import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

const HEADERS={...corsHeaders,'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'};
const MAX_REQUEST_BYTES=2048;
const MAX_REQUEST_CHUNKS = 4096;
const REQUEST_READ_TIMEOUT_MS = 15000;
function json(data:unknown,status=200){return new Response(JSON.stringify(data),{status,headers:HEADERS});}

async function readBoundedJson(req:Request){
  const mime=(req.headers.get('content-type')||'').toLowerCase().split(';',1)[0].trim();
  if(mime!=='application/json')throw new Error('JSON_REQUIRED');
  const declaredRaw=req.headers.get('content-length');
  if(declaredRaw!==null && (!/^[0-9]+$/.test(declaredRaw) ||
      !Number.isSafeInteger(Number(declaredRaw)) || Number(declaredRaw)>MAX_REQUEST_BYTES))
    throw new Error('REQUEST_TOO_LARGE');
  if(!req.body||typeof req.body.getReader!=='function')throw new Error('INVALID_JSON');
  const reader=req.body.getReader();
  const chunks:Uint8Array[]=[];
  let total=0,count=0,timer;
  const deadline=new Promise((_,reject)=>{
    timer=setTimeout(()=>reject(new Error('REQUEST_TIMEOUT')),REQUEST_READ_TIMEOUT_MS);
  });
  try{
    for(;;){
      const {done,value}=await Promise.race([reader.read(),deadline]);
      if(done)break;
      if(!(value instanceof Uint8Array))throw new Error('INVALID_JSON');
      if(++count>MAX_REQUEST_CHUNKS)throw new Error('REQUEST_TOO_LARGE');
      total+=value.byteLength;
      if(total>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
      chunks.push(value);
    }
  }catch(error){
    try{Promise.resolve(reader.cancel()).catch(()=>{});}catch{}
    throw error;
  }finally{
    clearTimeout(timer);
    reader.releaseLock();
  }
  const bytes=new Uint8Array(total);
  let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
  if(!bytes.length)throw new Error('INVALID_JSON');
  try{
    const parsed=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
    if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))throw new Error('INVALID_JSON');
    return parsed;
  }catch{throw new Error('INVALID_JSON');}
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req);
    const body=await readBoundedJson(req);
    const slug=typeof body?.slug==='string'?body.slug.trim():'';
    if(!slug||slug.length>120||!/^[a-z0-9][a-z0-9_-]*$/i.test(slug))
      return json({ok:false,error:'Roman invalide.'},400);
    const service=serviceClient();
    const {data:novel,error:novelError}=await service.from('sinjira_novels').select('id,slug,title,status,product_id,private_storage_bucket,private_storage_path,page_count,file_version,file_sha256,file_size_bytes,file_ready').eq('slug',slug).maybeSingle();
    if(novelError||!novel||novel.status!=='published')return json({ok:false,error:'Roman introuvable.'},404);
    const [ownerResult,adminResult]=await Promise.all([
      service.rpc('is_sinjira_owner',{p_user_id:user.id}),
      service.rpc('is_sinjira_admin',{p_user_id:user.id})
    ]);
    let entitled=(!ownerResult.error&&ownerResult.data===true)
      ||(!adminResult.error&&adminResult.data===true);
    let rightsUnavailable=false;
    if(!entitled&&novel.product_id){
      const {data:entitlement,error:entitlementError}=await service.from('user_entitlements')
        .select('product_id').eq('user_id',user.id).eq('product_id',novel.product_id).maybeSingle();
      if(entitlementError)rightsUnavailable=true;
      else if(entitlement){
        const {data:product,error:productError}=await service.from('products')
          .select('active').eq('id',novel.product_id).maybeSingle();
        if(productError)rightsUnavailable=true;
        else entitled=product?.active===true;
      }
    }
    // Une erreur réseau/RPC ne prouve pas que le membre ne possède
    // aucun droit. Refuser la signature sans fabriquer un "zéro achat".
    if(!entitled&&(rightsUnavailable||ownerResult.error||adminResult.error))
      return json({ok:false,error:'Vérification des droits momentanément indisponible.'},503);
    if(!entitled)return json({ok:false,error:'Votre compte ne possède pas le droit de lecture intégrale de ce roman.'},403);
    if(!novel.file_ready)return json({ok:false,error:'Le fichier intégral de cette édition n’est pas encore activé dans le stockage privé.',code:'FILE_NOT_READY',metadata:{page_count:novel.page_count,file_version:novel.file_version}},409);
    if(!novel.private_storage_bucket||!novel.private_storage_path)return json({ok:false,error:'Fichier privé non configuré.'},500);
    const {data:signed,error:signedError}=await service.storage.from(novel.private_storage_bucket).createSignedUrl(novel.private_storage_path,600,{download:novel.slug+'.pdf'});
    if(signedError||!signed?.signedUrl)return json({ok:false,error:'Impossible de créer le lien sécurisé.'},500);
    return json({ok:true,url:signed.signedUrl,protected:true,expires_in:600,novel:{slug:novel.slug,title:novel.title,page_count:novel.page_count,file_version:novel.file_version,file_sha256:novel.file_sha256,file_size_bytes:novel.file_size_bytes}});
  }catch(error){
    const message=String(error?.message||'');
    if(message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(message==='REQUEST_TOO_LARGE')return json({ok:false,error:'Requête trop volumineuse.'},413);
    if(message==='REQUEST_TIMEOUT')return json({ok:false,error:'Lecture de requête expirée.'},408);
    if(message==='INVALID_JSON')return json({ok:false,error:'Corps JSON invalide.'},400);
    if(message==='JSON_REQUIRED')return json({ok:false,error:'Type de contenu non autorisé.'},415);
    console.error('[get-novel-file-url]',{code:'NOVEL_FILE_URL_FAILED'});
    return json({ok:false,error:'Erreur lors de l’accès au roman.'},500);
  }
});