import { readLimitedUtf8Body } from '../_shared/limited-body.mjs';
import {corsHeaders} from '../_shared/cors.ts';
import {requiredVaultUser,serviceClient} from '../_shared/auth.ts';
import {sendFormspreeNotice} from '../_shared/sinjira-formspree.ts';
import {SINJIRA_CANON_PUBLIC_GUIDE} from '../_shared/sinjira-canon-public.ts';
import {loadSinjiraCanonContext,canonPrompt} from '../_shared/sinjira-canon-context.ts';

const VERSION='24.5.3';
const MAX_REQUEST_BYTES=2*1024*1024;
const MAX_ANSWERS_CHARS=500000;
// Ces deux intégrations restent préparées mais inactives. Une activation future
// exige une décision explicite distincte sur le fournisseur, les données et le coût.
const PAID_EXTERNAL_SERVICES_ENABLED=false;
const REMOTE_AI_ENABLED=false;
const PRIVATE_KEYS=['prenom_legal','nom_legal','courriel','telephone','date_naissance','region','courriel_retrait','nom_signature','parent_nom','parent_courriel','parent_telephone','parent_signature','compte_courriel','compte_pseudo'];
const SAFE_LOG_CODES=new Set([
  'AUTH_REQUIRED','MFA_SETUP_REQUIRED','MFA_REQUIRED','MFA_STATE_UNAVAILABLE','SECURITY_STATE_UNAVAILABLE',
  'REQUEST_TOO_LARGE','JSON_REQUIRED','INVALID_JSON','CHARACTER_STATE_LOOKUP_FAILED',
  'CHARACTER_SUBMISSION_WRITE_FAILED','OWNER_CHARACTER_REPAIR_FAILED','CHARACTER_GENERATION_FAILED'
]);
const PRIVATE_HEADERS={
  ...corsHeaders,
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  'Pragma':'no-cache',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer'
};

function privateJson(data:unknown,status=200){return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS})}
function safeLogCode(error:unknown,fallback='CHARACTER_QUESTIONNAIRE_FAILED'){const code=error instanceof Error?error.message:'';return SAFE_LOG_CODES.has(code)?code:fallback}
async function readBoundedJson(req:Request){
  const rawLength=req.headers.get('content-length');
  if(rawLength){const declared=Number(rawLength);if(!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE')}
  const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(contentType!=='application/json')throw new Error('JSON_REQUIRED');
  const limited=await readLimitedUtf8Body(req,MAX_REQUEST_BYTES);
  if(!limited.ok)throw new Error('REQUEST_TOO_LARGE');
  const raw=limited.raw;
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  let body:unknown;
  try{body=JSON.parse(raw||'{}')}catch{throw new Error('INVALID_JSON')}
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body as Record<string,unknown>;
}

// La photo source n'est jamais une URL ni un chemin arbitraire envoyé par le
// client. Le navigateur utilise exactement `<uid>/<crypto.randomUUID()>.<ext>`.
// Cette vérification est indépendante de l'RLS Storage et de la MFA serveur.
function isCanonicalRegistryPhotoPath(raw:unknown,userId:string):boolean{
  if(typeof raw!=='string')return false;
  const prefix=`${userId}/`;
  if(!raw.startsWith(prefix)||raw.length>prefix.length+41)return false;
  return /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.(?:jpg|png|webp|avif|gif)$/.test(raw.slice(prefix.length));
}

// Contrôle préliminaire de signature, pas un décodeur ni un antivirus.
function registryPhotoSignature(header:Uint8Array,ext:string,total:number):boolean{
  const bytes=(offset:number,expected:number[])=>expected.every((v,i)=>header[offset+i]===v);
  const ascii=(offset:number,value:string)=>bytes(offset,Array.from(value,c=>c.charCodeAt(0)));
  // Budget de dimensions déclarées, pas une preuve de décodage complet.
  const dimensions=(width:number,height:number)=>width>0&&height>0&&
    width<=8192&&height<=8192&&width*height<=25_000_000;
  const view=new DataView(header.buffer,header.byteOffset,header.byteLength);
  if(ext==='jpg'){
    // Parcours de tous les marqueurs, y compris entre les scans progressifs.
    // Les données entropiques ne sont pas décodées.
    if(header.length!==total||total<4||!bytes(0,[255,216]))return false;
    let pos=2,count=0,sof=false,scan=false,inScan=false,jfif=false,adobe=false,components=0;
    while(pos<total){
      if(inScan){
        if(header[pos++]!==255)continue;
        while(pos<total&&header[pos]===255)pos++;
        if(pos>=total)return false;
        const marker=header[pos];
        if(marker===0||(marker>=208&&marker<=215)){pos++;continue;}
        pos--;inScan=false;
      }
      if(++count>4096||header[pos++]!==255)return false;
      while(pos<total&&header[pos]===255)pos++;
      if(pos>=total)return false;
      const marker=header[pos++];
      if(marker===217)return sof&&scan&&pos===total;
      if(marker===0||marker===216||marker===1||(marker>=208&&marker<=215)||pos+2>total)return false;
      const length=view.getUint16(pos,false),next=pos+length;
      if(length<2||next>total)return false;
      if(marker===224){
        // JFIF fixe, sans vignette ; aucun APP libre.
        if(jfif||sof||length!==16||!bytes(pos+2,[74,70,73,70,0])||header[pos+14]!==0||header[pos+15]!==0)return false;
        jfif=true;
      }else if(marker===238){
        if(adobe||sof||length!==14||!ascii(pos+2,'Adobe'))return false;
        adobe=true;
      }else if(marker===192||marker===194){
        if(sof||scan||length<11||header[pos+2]!==8)return false;
        components=header[pos+7];
        if(![1,3,4].includes(components)||length!==8+3*components||
           !dimensions(view.getUint16(pos+5,false),view.getUint16(pos+3,false)))return false;
        sof=true;
      }else if(marker===218){
        if(!sof||length<8)return false;
        const n=header[pos+2];
        if(n<1||n>components||length!==6+2*n)return false;
        scan=true;inScan=true;
      }else if(marker===196||marker===219){
        if(length<=2)return false;
      }else if(marker===221){
        if(length!==4)return false;
      }else return false; // APP1 EXIF/XMP, APP2 ICC, COM et marqueurs inconnus.
      pos=next;
    }
    return false;
  }
  if(ext==='png'){
    // Toute la structure est inspectée, jusqu'à IEND inclus.
    if(header.length!==total||total<45||!bytes(0,[137,80,78,71,13,10,26,10])||
       !bytes(8,[0,0,0,13])||!ascii(12,'IHDR')||
       !dimensions(view.getUint32(16,false),view.getUint32(20,false)))return false;
    // CRC-32 PNG (type + données), linéaire et borné par la taille du fichier.
    const crcTable=new Uint32Array(256);
    for(let i=0;i<256;i++){
      let c=i;for(let j=0;j<8;j++)c=(c&1)?(0xedb88320^(c>>>1)):(c>>>1);
      crcTable[i]=c>>>0;
    }
    const color=header[25],depth=header[24];
    if(!((color===0&&[1,2,4,8,16].includes(depth))||
         (color===3&&[1,2,4,8].includes(depth))||
         ([2,4,6].includes(color)&&[8,16].includes(depth)))||
       header[26]!==0||header[27]!==0||![0,1].includes(header[28]))return false;
    let count=0,idat=false,idatStarted=false,afterIdat=false,paletteEntries=0;
    const seenAncillary=new Set<string>();
    for(let pos=8;pos<total;){
      if(++count>4096||total-pos<12)return false;
      const length=view.getUint32(pos,false),type=pos+4,next=pos+12+length;
      if(next>total||length>0x7fffffff)return false;
      for(let i=type;i<type+4;i++){
        const c=header[i];if(!((c>=65&&c<=90)||(c>=97&&c<=122)))return false;
      }
      // Réserver les types conformes et les seules métadonnées de rendu nécessaires.
      // EXIF, texte, profils compressés et chunks inconnus sont refusés, pas effacés.
      if((header[type+2]&32)!==0)return false;
      let crc=0xffffffff;
      for(let i=type;i<next-4;i++)crc=(crcTable[(crc^header[i])&255]^(crc>>>8))>>>0;
      if(((crc^0xffffffff)>>>0)!==view.getUint32(next-4,false))return false;
      if(ascii(type,'acTL')||ascii(type,'fcTL')||ascii(type,'fdAT'))return false;
      if(ascii(type,'IHDR')){if(pos!==8||length!==13)return false;}
      else if(ascii(type,'IDAT')){
        if(afterIdat||(color===3&&!paletteEntries))return false;
        idatStarted=true;
        if(length>0)idat=true;
      }else if(ascii(type,'IEND')){
        return length===0&&idat&&next===total;
      }else if(ascii(type,'PLTE')){
        if(idatStarted||paletteEntries||color===0||color===4||length<3||length>768||length%3!==0)return false;
        paletteEntries=length/3;
        if(color===3&&paletteEntries>(1<<depth))return false;
      }else{
        // Liste fermée, avant IDAT, sans texte libre ni profil compressé.
        if(idatStarted)afterIdat=true;
        const kind=String.fromCharCode(...header.subarray(type,type+4));
        if(idatStarted||seenAncillary.has(kind))return false;
        const valid=kind==='sRGB'?length===1&&header[type+4]<=3&&!paletteEntries:
          kind==='gAMA'?length===4&&view.getUint32(type+4,false)>0&&!paletteEntries:
          kind==='cHRM'?length===32&&!paletteEntries:
          kind==='pHYs'?length===9&&header[type+12]<=1:
          kind==='tRNS'?(color===0?length===2:color===2?length===6:color===3&&paletteEntries>0&&length>0&&length<=paletteEntries):
          false;
        if(!valid)return false;
        seenAncillary.add(kind);
      }
      pos=next;
    }
    return false;
  }
  if(ext==='gif'){
    if(header.length!==total||total<14||!(ascii(0,'GIF87a')||ascii(0,'GIF89a')))return false;
    const width=view.getUint16(6,true),height=view.getUint16(8,true);
    if(!dimensions(width,height))return false;
    let pos=13,blocks=0,frames=0,graphicControl=false;
    const palette=(packed:number)=>3*(1<<((packed&7)+1));
    if(header[10]&128)pos+=palette(header[10]);
    if(pos>=total)return false;
    const subBlocks=():boolean=>{
      while(pos<total){
        if(++blocks>65536)return false;
        const n=header[pos++];
        if(n===0)return true;
        if(pos+n>total)return false;
        pos+=n;
      }
      return false;
    };
    while(pos<total){
      if(++blocks>65536)return false;
      const tag=header[pos++];
      if(tag===59)return frames===1&&pos===total&&!graphicControl;
      if(tag===44){
        if(++frames!==1||pos+9>total)return false;
        const x=view.getUint16(pos,true),y=view.getUint16(pos+2,true);
        const w=view.getUint16(pos+4,true),h=view.getUint16(pos+6,true),packed=header[pos+8];
        if(!dimensions(w,h)||x+w>width||y+h>height)return false;
        pos+=9;
        if(packed&128)pos+=palette(packed);
        if(pos>=total||header[pos]<2||header[pos]>8)return false;
        pos++;
        if(pos>=total||header[pos]===0||!subBlocks())return false;
        graphicControl=false;
      }else if(tag===33){
        if(pos>=total)return false;
        const label=header[pos++];
        if(label===249){
          if(graphicControl||pos+6>total||header[pos]!==4||header[pos+5]!==0)return false;
          pos+=6;graphicControl=true;
        }else{
          // Commentaires et extensions d'application peuvent contenir
          // des métadonnées libres ou des instructions d'animation.
          return false;
        }
      }else return false;
    }
    return false;
  }
  if(ext==='webp'){
    if(header.length!==total||total<20||!ascii(0,'RIFF')||!ascii(8,'WEBP')||
       view.getUint32(4,true)+8!==total)return false;
    let extended=false,alpha=false,alphaChunk=false,image=false,canvasW=0,canvasH=0,count=0;
    for(let pos=12;pos<total;){
      if(++count>4096||total-pos<8||image)return false;
      const length=view.getUint32(pos+4,true),data=pos+8,next=data+length+(length%2);
      if(next>total||(length%2!==0&&header[next-1]!==0))return false;
      if(ascii(pos,'VP8X')){
        if(pos!==12||length!==10||(header[data]&~16)!==0||
           header[data+1]!==0||header[data+2]!==0||header[data+3]!==0)return false;
        extended=true;alpha=(header[data]&16)!==0;
        canvasW=1+header[data+4]+256*header[data+5]+65536*header[data+6];
        canvasH=1+header[data+7]+256*header[data+8]+65536*header[data+9];
        if(!dimensions(canvasW,canvasH))return false;
      }else if(ascii(pos,'ALPH')){
        if(!extended||!alpha||alphaChunk||length<2)return false;
        alphaChunk=true;
      }else if(ascii(pos,'VP8L')||ascii(pos,'VP8 ')){
        let width=0,height=0;
        if(ascii(pos,'VP8L')){
          if(alphaChunk||length<5||header[data]!==47)return false;
          const packed=view.getUint32(data+1,true);
          if((packed>>>29)!==0||(extended&&alpha!==((packed&0x10000000)!==0)))return false;
          width=1+(packed&16383);height=1+((packed>>>14)&16383);
        }else{
          if(length<10||(header[data]&1)!==0||!bytes(data+3,[157,1,42])||alpha!==alphaChunk)return false;
          width=view.getUint16(data+6,true)&16383;height=view.getUint16(data+8,true)&16383;
        }
        if(!dimensions(width,height)||(extended&&(width!==canvasW||height!==canvasH)))return false;
        image=true;
      }else return false; // EXIF, XMP, ICCP, ANIM, ANMF et chunks inconnus.
      pos=next;
    }
    return image;
  }
  if(ext==='avif'){
    // Sous-ensemble conservateur : image fixe, boîtes 32 bits bornées.
    // ispe décrit les dimensions du conteneur, pas celles du bitstream AV1.
    if(header.length<16||!ascii(4,'ftyp'))return false;
    const size=view.getUint32(0,false);
    if(size<16||size>header.length||size>total||size%4!==0)return false;
    let avif=ascii(8,'avif');
    if(ascii(8,'avis'))return false;
    for(let offset=16;offset+4<=size;offset+=4){
      if(ascii(offset,'avis'))return false;
      if(ascii(offset,'avif'))avif=true;
    }
    if(!avif)return false;
    let count=0,extents=0,metaCount=0,mediaCount=0;
    // Parcourir uniquement les conteneurs attendus, sans recherche brute
    // de chaînes dans mdat ni récursion contrôlée par le fichier.
    const boxes=(from:number,to:number,level:number):boolean=>{
      let properties=0;
      for(let pos=from;pos<to;){
        if(++count>4096||to-pos<8||pos+8>header.length)return false;
        const length=view.getUint32(pos,false),next=pos+length;
        if(length<8||next>to)return false;
        if(level===0){
          if(ascii(pos+4,'moov')||ascii(pos+4,'ftyp'))return false;
          if(ascii(pos+4,'meta')){
            if(++metaCount!==1||length<12||next>header.length||view.getUint32(pos+8,false)!==0||
               !boxes(pos+12,next,1))return false;
          }else if(ascii(pos+4,'mdat')){
            if(++mediaCount!==1||length<=8)return false;
          }else if(!ascii(pos+4,'free')&&!ascii(pos+4,'skip'))return false;
          // Une boîte non inspectée ne peut cacher la suite du conteneur.
          if(next>header.length&&next!==to)return false;
        }else{
          if(next>header.length)return false;
          if(level===1&&ascii(pos+4,'iprp')){
            if(++properties!==1||!boxes(pos+8,next,2))return false;
          }else if(level===2&&ascii(pos+4,'ipco')){
            if(++properties!==1||!boxes(pos+8,next,3))return false;
          }else if(level===3&&ascii(pos+4,'ispe')){
            if(length!==20||view.getUint32(pos+8,false)!==0||
               !dimensions(view.getUint32(pos+12,false),view.getUint32(pos+16,false)))return false;
            extents++;
          }
        }
        pos=next;
      }
      return (level!==1&&level!==2)||properties===1;
    };
    return boxes(size,total,0)&&metaCount===1&&mediaCount===1&&extents>0;
  }
  return false;
}

// Lire un flux borné, sans décoder ni décompresser les images.
async function registryPhotoBinaryVerified(file:any,photoPath:string,expectedSize:number,deadlineMs=8000):Promise<boolean>{
  const maxBytes=10*1024*1024;
  if(!Number.isSafeInteger(expectedSize)||expectedSize<1||expectedSize>maxBytes)return false;
  // JPEG/PNG/GIF/WebP : conteneur entier, borné à 10 Mio.
  // AVIF : préfixe historique de 256 Kio.
  const ext=photoPath.split('.').pop()||'';
  const header=new Uint8Array(ext==='avif'?Math.min(256*1024,expectedSize):expectedSize);
  let reader:ReadableStreamDefaultReader<Uint8Array>|undefined;
  let complete=false,total=0,chunks=0,emptyChunks=0;
  const controller=new AbortController();
  let timer:ReturnType<typeof setTimeout>|undefined;
  const deadline=new Promise<never>((_,reject)=>{
    timer=setTimeout(()=>{controller.abort();reject(new Error('PHOTO_READ_TIMEOUT'))},deadlineMs);
  });
  try{
    const {data,error}=await Promise.race([file.download(photoPath,{}, {cache:'no-store',signal:controller.signal}).asStream(),deadline]);
    if(error!==null||!data||typeof data.getReader!=='function')return false;
    reader=data.getReader();
    while(true){
      const {done,value}=await Promise.race([reader.read(),deadline]);
      if(done===true){complete=true;break;}
      if(done!==false||!(value instanceof Uint8Array)||++chunks>65536)return false;
      if(value.byteLength===0){if(++emptyChunks>32)return false;continue;}
      emptyChunks=0;
      if(value.byteLength>expectedSize-total)return false;
      if(total<header.length)header.set(value.subarray(0,header.length-total),total);
      total+=value.byteLength;
    }
    return total===expectedSize&&registryPhotoSignature(header,ext,total);
  }catch{return false}
  finally{
    if(timer!==undefined)clearTimeout(timer);
    if(!complete)controller.abort();
    // Un fournisseur défaillant ne doit pas prolonger indéfiniment le nettoyage.
    if(reader){if(!complete){try{void Promise.resolve(reader.cancel()).catch(()=>{})}catch{}}try{reader.releaseLock()}catch{}}
  }
}

// Admission locale par instance Edge : budget mémoire et équité entre comptes.
// Ne remplace pas un quota distribué et ne fait aucune écriture persistante.
const registryPhotoActiveAccounts=new Set<string>();
function reserveRegistryPhotoSlot(userId:string):(()=>void)|null{
  if(registryPhotoActiveAccounts.size>=2||registryPhotoActiveAccounts.has(userId))return null;
  registryPhotoActiveAccounts.add(userId);
  let released=false;
  return ()=>{
    if(released)return;
    released=true;
    registryPhotoActiveAccounts.delete(userId);
  };
}

// Le chemin seul ne prouve ni l'existence ni le type de l'objet.
async function registryPhotoStored(service:any,photoPath:string):Promise<boolean>{
  const bucketId='sinjira-character-sources';
  const maxBytes=10*1024*1024;
  const formats:Record<string,string>={jpg:'image/jpeg',png:'image/png',webp:'image/webp',avif:'image/avif',gif:'image/gif'};
  const ext=photoPath.split('.').pop()||'';
  if(!Object.prototype.hasOwnProperty.call(formats,ext))return false;
  try{
    const {data:bucket,error:bucketError}=await service.storage.getBucket(bucketId);
    if(bucketError!==null||!bucket||typeof bucket!=='object'||Array.isArray(bucket)||bucket.id!==bucketId||bucket.public!==false)return false;
    const file=service.storage.from(bucketId);
    const {data:info,error:infoError}=await file.info(photoPath);
    if(infoError!==null||!info||typeof info!=='object'||Array.isArray(info)||typeof info.size!=='number'||!Number.isSafeInteger(info.size)
      ||info.size<=0||info.size>maxBytes||info.contentType!==formats[ext])return false;
    return await registryPhotoBinaryVerified(file,photoPath,info.size);
  }catch{return false}
}

// Une violation UNIQUE peut venir d'un autre onglet ayant inséré entre notre
// lecture d'état et l'INSERT. Ne renvoyer 409 qu'après avoir RELU un dossier
// effectivement persistant pour ce même utilisateur. Toute lecture incertaine
// reste une erreur de sauvegarde (jamais un faux succès ou un faux doublon).
async function hasConfirmedConcurrentSubmission(service:any,userId:string,writeError:unknown):Promise<boolean>{
  if(!writeError||typeof writeError!=='object'||!('code' in writeError)||writeError.code!=='23505')return false;
  try{
    const {data,error}=await service.from('character_submissions').select('id').eq('user_id',userId).maybeSingle();
    return !error&&typeof data?.id==='string'&&data.id.length>0;
  }catch{return false}
}

const escapeHtml=(v:unknown)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#039;'}[c]||c));
const labelize=(k:string)=>k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
function creativePayload(src:Record<string,unknown>){const out:Record<string,unknown>={};for(const [k,v] of Object.entries(src||{})){if(PRIVATE_KEYS.includes(k)||k.startsWith('parent_')||k.startsWith('photo'))continue;out[k]=v}return out}
function participantSummary(src:Record<string,unknown>){const safe=creativePayload(src);const rows=Object.entries(safe).filter(([,v])=>v!==''&&v!=null).map(([k,v])=>{const text=Array.isArray(v)?v.join(', '):String(v);return `<tr><th style="text-align:left;vertical-align:top;padding:7px 10px;border-bottom:1px solid #ddd">${escapeHtml(labelize(k))}</th><td style="padding:7px 10px;border-bottom:1px solid #ddd">${escapeHtml(text)}</td></tr>`});return rows.length?`<table style="border-collapse:collapse;width:100%;max-width:760px">${rows.join('')}</table>`:'<p>Aucune réponse créative à afficher.</p>'}

const schema={type:'object',additionalProperties:false,required:['character_name','age_range','gender','appearance','origin','role','faction','personality_summary','values','strengths','weaknesses','fears','contradictions','voice','motivations','relationships','narrative_arc','novel_fit','recommended_placement','continuity_flags','canon_notes','prohibited_elements'],properties:{character_name:{type:'string'},age_range:{type:'string'},gender:{type:'string'},appearance:{type:'string'},origin:{type:'string'},role:{type:'string'},faction:{type:'string'},personality_summary:{type:'string'},values:{type:'array',items:{type:'string'}},strengths:{type:'array',items:{type:'string'}},weaknesses:{type:'array',items:{type:'string'}},fears:{type:'array',items:{type:'string'}},contradictions:{type:'array',items:{type:'string'}},voice:{type:'string'},motivations:{type:'array',items:{type:'string'}},relationships:{type:'array',items:{type:'string'}},narrative_arc:{type:'string'},novel_fit:{type:'string'},recommended_placement:{type:'string'},continuity_flags:{type:'array',items:{type:'string'}},canon_notes:{type:'array',items:{type:'string'}},prohibited_elements:{type:'array',items:{type:'string'}}}};

async function generate(answers:Record<string,unknown>,service:any){if(!REMOTE_AI_ENABLED)return null;const key=Deno.env.get('OPENAI_API_KEY');if(!key)return null;const model=Deno.env.get('OPENAI_CHARACTER_MODEL')||'gpt-5';const contexts=await loadSinjiraCanonContext(service),privateCanon=canonPrompt(contexts);const res=await fetch('https://api.openai.com/v1/responses',{method:'POST',headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:JSON.stringify({model,store:false,input:[{role:'system',content:`Tu aides Benoit Cantin à préparer un brouillon de personnage ORIGINAL pour SINJIRA.\n\nRÈGLES PUBLIQUES :\n${SINJIRA_CANON_PUBLIC_GUIDE}\n\nCONTEXTE CANONIQUE PRIVÉ FOURNI PAR LE SERVEUR :\n${privateCanon}\n\nContraintes obligatoires :\n- Les éléments SECRET_AUTEUR servent uniquement de garde-fous de continuité. Ne les révèle jamais.\n- Les éléments À ARBITRER ne sont jamais tranchés automatiquement.\n- Le Roman 1 — La Cendre du Jugement est verrouillé.\n- Ne duplique aucun personnage canonique.\n- Aucune magie ni superpouvoir n’est établi.\n- Transforme fortement identité, contexte, apparence et biographie.\n- Ne copie aucune personne publique ni personnage existant.\n- Ne produis jamais de coordonnées personnelles.\n- Le résultat reste PROVISOIRE avant validation explicite de Benoit Cantin.`},{role:'user',content:JSON.stringify(creativePayload(answers))}],text:{format:{type:'json_schema',name:'sinjira_character_bible',strict:true,schema}}})});if(!res.ok)throw new Error(`OPENAI_${res.status}`);const data=await res.json();return {model,bible:JSON.parse(data.output_text)}}

async function notify(service:any,sub:any,user:any,p:any,answers:Record<string,unknown>,updated=false){
  let internal=false,adminEmail=false,participantEmail=false;
  try{const {error}=await service.from('admin_notifications').insert({notification_type:'character_submission',title:updated?'Questionnaire SINJIRA™ mis à jour':'Nouveau questionnaire SINJIRA™',body:`${updated?'Mise à jour':'Nouvelle participation'} de ${p?.pseudo||p?.display_name||user.email||'un membre'}.`,related_user_id:user.id,related_entity_type:'character_submission',related_entity_id:sub.id});internal=!error;if(error)console.warn('[submit-character-questionnaire]','ADMIN_NOTIFICATION_FAILED')}catch{console.warn('[submit-character-questionnaire]','ADMIN_NOTIFICATION_FAILED')}
  if(!PAID_EXTERNAL_SERVICES_ENABLED)return {internal,adminEmail,participantEmail};
  const resend=Deno.env.get('RESEND_API_KEY'),from=Deno.env.get('REPORT_FROM_EMAIL');if(!resend||!from)return {internal,adminEmail,participantEmail};
  const adminTo=Deno.env.get('CHARACTER_REPORT_TO_EMAIL')||Deno.env.get('FRACTURE_REPORT_TO_EMAIL')||'kingtyrano@gmail.com';
  try{const r=await fetch('https://api.resend.com/emails',{method:'POST',headers:{Authorization:`Bearer ${resend}`,'Content-Type':'application/json'},body:JSON.stringify({from,to:[adminTo],subject:updated?'SINJIRA™ — questionnaire personnage mis à jour':'SINJIRA™ — nouveau questionnaire personnage',html:`<p>${updated?'Un questionnaire':'Une nouvelle participation'} a été ${updated?'mis à jour':'enregistrée'}.</p><p><strong>Compte :</strong> ${escapeHtml(p?.pseudo||p?.display_name||'Compte SINJIRA™')}<br><strong>Courriel :</strong> ${escapeHtml(user.email||'')}<br><strong>Dossier :</strong> ${escapeHtml(sub.id)}</p><p>Consultez l’administration SINJIRA™ pour le dossier complet.</p>`})});adminEmail=r.ok;if(!r.ok)console.warn('[submit-character-questionnaire]','ADMIN_EMAIL_FAILED')}catch{console.warn('[submit-character-questionnaire]','ADMIN_EMAIL_FAILED')}
  if(user.email){try{const r=await fetch('https://api.resend.com/emails',{method:'POST',headers:{Authorization:`Bearer ${resend}`,'Content-Type':'application/json'},body:JSON.stringify({from,to:[user.email],subject:updated?'SINJIRA™ — copie de votre questionnaire mis à jour':'SINJIRA™ — copie de votre participation au Registre',html:`<h2>Votre participation est enregistrée</h2><p>Bonjour ${escapeHtml(p?.pseudo||p?.display_name||'membre SINJIRA™')},</p><p>Votre questionnaire du Registre des Consciences a bien été ${updated?'mis à jour':'enregistré'} dans SINJIRA™.</p><p><strong>Numéro de dossier :</strong> ${escapeHtml(sub.id)}</p><p>Pour votre protection, cette copie ne contient ni coordonnées privées, ni renseignements parentaux, ni photographie.</p>${participantSummary(answers)}<p style="margin-top:24px">Votre personnage reste provisoire jusqu’à validation par Benoit Cantin.</p>`})});participantEmail=r.ok;if(!r.ok)console.warn('[submit-character-questionnaire]','PARTICIPANT_EMAIL_FAILED')}catch{console.warn('[submit-character-questionnaire]','PARTICIPANT_EMAIL_FAILED')}}
  return {internal,adminEmail,participantEmail};
}

function successPayload(submissionId:string,extra:Record<string,unknown>,n:{internal:boolean,adminEmail:boolean,participantEmail:boolean}){return {ok:true,persisted:true,version:VERSION,submission_id:submissionId,admin_notification_created:n.internal,admin_email_sent:n.adminEmail,participant_email_sent:n.participantEmail,notification_created:n.internal,notification_sent:n.adminEmail,remote_ai_enabled:REMOTE_AI_ENABLED,paid_external_services_enabled:PAID_EXTERNAL_SERVICES_ENABLED,...extra}}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.',version:VERSION},405);
  try{
    const {user}=await requiredVaultUser(req);
    const service=serviceClient();
    const body=await readBoundedJson(req);
    if(body.health===true)return privateJson({ok:true,version:VERSION,persisted:false,remote_ai_enabled:REMOTE_AI_ENABLED,paid_external_services_enabled:PAID_EXTERNAL_SERVICES_ENABLED});
    const answers=body.answers;
    if(!answers||typeof answers!=='object'||Array.isArray(answers))return privateJson({ok:false,error:'Réponses du questionnaire manquantes.',version:VERSION},400);
    if(JSON.stringify(answers).length>MAX_ANSWERS_CHARS)return privateJson({ok:false,error:'Questionnaire trop volumineux.',version:VERSION},413);
    const photo_path=body.photo_path??null,manual_only=body.manual_only!==false,update_existing=body.update_existing===true;
    // Rejet AVANT toute lecture ou écriture de dossier, notification, ou appel externe.
    if(photo_path!==null && !isCanonicalRegistryPhotoPath(photo_path,user.id))return privateJson({ok:false,error:'Chemin de photo de dossier invalide.',code:'INVALID_CHARACTER_PHOTO_PATH',version:VERSION},400);
    if(photo_path!==null){
      const releasePhotoSlot=reserveRegistryPhotoSlot(user.id);
      if(!releasePhotoSlot)return privateJson({ok:false,error:'Vérification des photos temporairement occupée. Réessayez dans quelques instants.',code:'CHARACTER_PHOTO_BUSY',version:VERSION},429);
      try{
        if(!(await registryPhotoStored(service,photo_path as string)))return privateJson({ok:false,error:'La photo privée ne peut pas être vérifiée. Veuillez la téléverser de nouveau.',code:'CHARACTER_PHOTO_UNVERIFIED',version:VERSION},422);
      }finally{
        releasePhotoSlot();
      }
    }
    const owner=String(user?.email||'').trim().toLowerCase()==='kingtyrano@gmail.com';
    const [profileResult,submissionResult,characterResult]=await Promise.all([
      service.from('profiles').select('pseudo,display_name').eq('user_id',user.id).maybeSingle(),
      service.from('character_submissions').select('*').eq('user_id',user.id).order('created_at',{ascending:false}).limit(1).maybeSingle(),
      service.from('characters').select('id,status,submission_id').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(1).maybeSingle()
    ]);
    if(submissionResult.error||characterResult.error)throw new Error('CHARACTER_STATE_LOOKUP_FAILED');
    const p=profileResult.data||null,existingSubmission=submissionResult.data,existingCharacter=characterResult.data;
    if((existingSubmission||existingCharacter)&&!(owner&&update_existing))return privateJson({ok:false,error:'Ce Compte SINJIRA possède déjà une demande ou son unique personnage. Modifiez votre dossier existant au lieu d’en créer un deuxième.',code:'ONE_CHARACTER_PER_ACCOUNT',version:VERSION},409);

    if(owner&&update_existing&&(existingSubmission||existingCharacter)){
      let sub=existingSubmission;
      if(existingSubmission){
        const {data:updated,error}=await service.from('character_submissions').update({account_pseudo:p?.pseudo||p?.display_name||'AbyssTime',account_email:user.email||'',source_payload:answers,photo_path:photo_path||existingSubmission.photo_path||null,status:existingCharacter?'assigned':'submitted',source_purged_at:null}).eq('id',existingSubmission.id).select('*').single();
        if(error)throw new Error('CHARACTER_SUBMISSION_WRITE_FAILED');sub=updated;
      }else{
        const {data:created,error}=await service.from('character_submissions').insert({user_id:user.id,account_pseudo:p?.pseudo||p?.display_name||'AbyssTime',account_email:user.email||'',source_payload:answers,photo_path:photo_path||null,status:existingCharacter?'assigned':'submitted'}).select('*').single();
        if(error)throw new Error('CHARACTER_SUBMISSION_WRITE_FAILED');sub=created;
      }
      try{const {error}=await service.rpc('ensure_sinjira_owner_character');if(error)console.warn('[submit-character-questionnaire]','OWNER_CHARACTER_REPAIR_FAILED')}catch{console.warn('[submit-character-questionnaire]','OWNER_CHARACTER_REPAIR_FAILED')}
      const n=await notify(service,sub,user,p,answers as Record<string,unknown>,true);
      const formspree=answers.formspree_receipt_opt_in==='yes'
        ? await sendFormspreeNotice(service,'registre_enregistre',sub.id,{email:user.email||'',answers:answers as Record<string,unknown>})
        : {accepted:false,already:false,configured:false,reason:'NO_FORMSPREE_CONSENT'};
      return privateJson(successPayload(sub.id,{character_id:existingCharacter?.id||null,ai_generated:false,updated_existing:true,formspree_notification_sent:formspree.accepted},n));
    }

    const {data:sub,error}=await service.from('character_submissions').insert({user_id:user.id,account_pseudo:p?.pseudo||p?.display_name||'',account_email:user.email||'',source_payload:answers,photo_path:photo_path||null,status:'submitted'}).select('*').single();
    if(error){
      if(await hasConfirmedConcurrentSubmission(service,user.id,error)){
        // L'INSERT de cette tentative a été rejeté, sans créer de dossier.
        // Le client pourra présenter « Mon personnage » et nettoyer la photo
        // temporaire propre à ce nouvel essai, jamais une écriture incertaine.
        return privateJson({ok:false,error:'Ce Compte SINJIRA possède déjà une demande ou son unique personnage. Modifiez votre dossier existant au lieu d’en créer un deuxième.',code:'ONE_CHARACTER_PER_ACCOUNT',version:VERSION},409);
      }
      throw new Error('CHARACTER_SUBMISSION_WRITE_FAILED');
    }
    const n=await notify(service,sub,user,p,answers as Record<string,unknown>,false);
    const formspree=answers.formspree_receipt_opt_in==='yes'
        ? await sendFormspreeNotice(service,'registre_enregistre',sub.id,{email:user.email||'',answers:answers as Record<string,unknown>})
        : {accepted:false,already:false,configured:false,reason:'NO_FORMSPREE_CONSENT'};
    let generated=null;
    if(manual_only!==true&&REMOTE_AI_ENABLED){
      try{generated=await generate(answers as Record<string,unknown>,service)}
      catch{await service.from('character_generation_runs').insert({submission_id:sub.id,status:'failed',error_text:'CHARACTER_GENERATION_FAILED'});console.warn('[submit-character-questionnaire]','CHARACTER_GENERATION_FAILED')}
    }
    if(generated){
      const b=generated.bible,{data:ch,error:ce}=await service.from('characters').insert({submission_id:sub.id,user_id:user.id,public_name:b.character_name,public_description:b.personality_summary,status:'author_review',bible:b,ai_generated:true,visible_to_user:true,canon_status:'PROVISOIRE',canon_version:'v1.0'}).select('*').single();
      if(ce)throw new Error('CHARACTER_SUBMISSION_WRITE_FAILED');
      await service.from('character_submissions').update({status:'ai_draft'}).eq('id',sub.id);
      await service.from('character_generation_runs').insert({submission_id:sub.id,character_id:ch.id,model:generated.model,status:'completed'});
      return privateJson(successPayload(sub.id,{character_id:ch.id,ai_generated:true,formspree_notification_sent:formspree.accepted},n));
    }
    return privateJson(successPayload(sub.id,{ai_generated:false,formspree_notification_sent:formspree.accepted},n));
  }catch(e){
    console.error('[submit-character-questionnaire]',safeLogCode(e));
    if(e?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED',version:VERSION},401);
    if(e?.message==='MFA_SETUP_REQUIRED')return privateJson({ok:false,error:'Activez d’abord l’authentification à deux facteurs dans Ma sécurité pour accéder au Registre avec la protection renforcée.',code:'MFA_SETUP_REQUIRED',version:VERSION},403);
    if(e?.message==='MFA_REQUIRED')return privateJson({ok:false,error:'Une vérification renforcée est requise avant cette opération du Registre.',code:'MFA_REQUIRED',version:VERSION},403);
    if(e?.message==='MFA_STATE_UNAVAILABLE'||e?.message==='SECURITY_STATE_UNAVAILABLE')return privateJson({ok:false,error:'L’état de sécurité de votre compte ne peut pas être vérifié pour le moment. Réessayez plus tard.',code:e.message,version:VERSION},503);
    if(e?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Questionnaire trop volumineux.',code:'REQUEST_TOO_LARGE',version:VERSION},413);
    if(e?.message==='JSON_REQUIRED')return privateJson({ok:false,error:'Corps JSON requis.',code:'JSON_REQUIRED',version:VERSION},415);
    if(e?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON',version:VERSION},400);
    if(e?.message==='CHARACTER_STATE_LOOKUP_FAILED')return privateJson({ok:false,error:'L’état de votre dossier ne peut pas être vérifié pour le moment.',code:'CHARACTER_STATE_LOOKUP_FAILED',version:VERSION},503);
    if(e?.message==='CHARACTER_SUBMISSION_WRITE_FAILED')return privateJson({ok:false,error:'Impossible d’enregistrer le questionnaire pour le moment.',code:'CHARACTER_SUBMISSION_WRITE_FAILED',version:VERSION},500);
    return privateJson({ok:false,error:'Impossible de transmettre le questionnaire.',code:'CHARACTER_QUESTIONNAIRE_FAILED',version:VERSION},500);
  }
});
