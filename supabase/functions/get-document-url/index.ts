import { corsHeaders } from '../_shared/cors.ts';
import { optionalUser, serviceClient } from '../_shared/auth.ts';

const MAX_REQUEST_BYTES=512;
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ranks:Record<string,number>={public:1,account:10,player:20,tester:30,admin:100};
const PRIVATE_JSON_HEADERS={
  ...corsHeaders,
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  'Pragma':'no-cache',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer'
};

function privateJson(data:unknown,status=200){
  return new Response(JSON.stringify(data),{status,headers:PRIVATE_JSON_HEADERS});
}

const OFFICIAL_ORIGIN='https://www.benoitcantin.com';
function externalUrlAllowed(value:string){
  // Les URL de documents proviennent du registre approuvé, mais doivent
  // rester non ambiguës au moment de leur ouverture par le navigateur.
  // Une URL commençant par /\\ peut sinon changer d'hôte silencieusement.
  if(!value||value.trim()!==value||/[\\\u0000-\u001f\u007f]/.test(value))return false;
  if(value.startsWith('/')&&!value.startsWith('//')){
    // Refuser aussi les séparateurs et caractères de contrôle encodés.
    if(/%(?:2f|5c|0[0-9a-f]|1[0-9a-f]|7f)/i.test(value))return false;
    try{
      const url=new URL(value,OFFICIAL_ORIGIN);
      return url.origin===OFFICIAL_ORIGIN&&!url.username&&!url.password;
    }catch{return false}
  }
  // Les fournisseurs HTTPS externes restent permis, mais sans
  // identifiants intégrés ni URL dont le schéma est écrit ambiguëment.
  if(!/^https:\/\/[^/]/i.test(value))return false;
  try{
    const url=new URL(value);
    return url.protocol==='https:'&&!!url.hostname&&!url.username&&!url.password;
  }catch{return false}
}

async function readLimitedJson(req:Request):Promise<{body?:any;response?:Response}>{
  // Lecture bornée pendant le flux, jamais en mémoire via req.text().
  const contentType=(req.headers.get('content-type')||'').toLowerCase().split(';',1)[0].trim();
  if(contentType!=='application/json'){
    return {response:privateJson({ok:false,error:'Type de contenu non autorisé.'},415)};
  }
  const rawLength=req.headers.get('content-length');
  if(rawLength!==null){
    const declared=Number(rawLength);
    if(!Number.isSafeInteger(declared)||declared<0||declared>MAX_REQUEST_BYTES){
      return {response:privateJson({ok:false,error:'Requête trop volumineuse.'},413)};
    }
  }
  if(!req.body)return {body:{}};
  const reader=req.body.getReader();
  const chunks:Uint8Array[]=[];
  let total=0;
  try{
    while(true){
      const {done,value}=await reader.read();
      if(done)break;
      if(value){
        total+=value.byteLength;
        if(total>MAX_REQUEST_BYTES){
          await reader.cancel().catch(()=>{});
          return {response:privateJson({ok:false,error:'Requête trop volumineuse.'},413)};
        }
        chunks.push(value);
      }
    }
  }finally{
    reader.releaseLock();
  }
  const bytes=new Uint8Array(total);
  let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
  try{
    const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
    return {body:JSON.parse(raw||'{}')};
  }catch{
    return {response:privateJson({ok:false,error:'Corps JSON invalide.'},400)};
  }
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const parsed=await readLimitedJson(req);
    if(parsed.response)return parsed.response;
    const document_id=typeof parsed.body?.document_id==='string'?parsed.body.document_id.trim():'';
    if(!UUID_RE.test(document_id))return privateJson({ok:false,error:'Document manquant ou invalide.'},400);

    const service=serviceClient(),user=await optionalUser(req);
    const {data:doc,error}=await service
      .from('documents')
      .select('project_id,status,access_level,external_url,storage_bucket,storage_path,projects(id,visibility,status)')
      .eq('id',document_id)
      .maybeSingle();
    if(error||!doc||doc.status!=='approved'||doc.projects?.status!=='active'){
      return privateJson({ok:false,error:'Document introuvable ou non approuvé.'},404);
    }

    // Le droit public appartient aussi aux membres connectés :
    // une connexion ne doit jamais réduire l'accès à un document public
    // d'un projet public approuvé. Aucun RPC privilégié n'est requis ici.
    const requiredRank=ranks[doc.access_level]||999;
    let userRank=doc.projects?.visibility==='public'?ranks.public:0;
    if(user&&userRank<requiredRank){
      // Le propriétaire SINJIRA et les administrateurs constituent deux
      // rôles distincts. Ne jamais déduire le rôle propriétaire du courriel.
      const [{data:isOwner,error:ownerError},{data:isAdmin,error:adminError}]=await Promise.all([
        service.rpc('is_sinjira_owner',{p_user_id:user.id}),
        service.rpc('is_sinjira_admin',{p_user_id:user.id})
      ]);
      if((!ownerError&&isOwner===true)||(!adminError&&isAdmin===true))userRank=100;
      else{
        const {data:accessRank,error:rankError}=await service.rpc('project_access_rank',{p_project_id:doc.project_id,p_user_id:user.id});
        if(rankError)return privateJson({ok:false,error:'Droits du compte temporairement indisponibles.'},503);
        const memberRank=Number.isFinite(Number(accessRank))?Number(accessRank):0;
        userRank=Math.max(userRank,memberRank);
      }
    }

    if(userRank<requiredRank){
      return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);
    }

    if(doc.external_url){
      const url=String(doc.external_url).trim();
      if(!externalUrlAllowed(url))return privateJson({ok:false,error:'URL de document non autorisée.'},500);
      return privateJson({ok:true,url,protected:false,expires_in:null});
    }
    if(!doc.storage_bucket||!doc.storage_path)return privateJson({ok:false,error:'Fichier non configuré.'},500);

    const {data:signed,error:signedError}=await service.storage.from(doc.storage_bucket).createSignedUrl(doc.storage_path,600);
    if(signedError||!signed?.signedUrl)return privateJson({ok:false,error:'Impossible de créer le lien sécurisé.'},500);
    return privateJson({ok:true,url:signed.signedUrl,protected:true,expires_in:600});
  }catch{
    console.error('[get-document-url]',{code:'GET_DOCUMENT_URL_FAILED'});
    return privateJson({ok:false,error:'Erreur lors de l’accès au document.'},500);
  }
});
