import { corsHeaders } from '../_shared/cors.ts';
import { readLimitedUtf8BodyWithDeadline } from '../_shared/read-chunk-deadline.mjs';
import { requiredUser, serviceClient } from '../_shared/auth.ts';
import { privateBookLocationValid, isVerifiedPrivateBucket } from '../_shared/private-book-storage-guard.mjs';

const HEADERS={...corsHeaders,'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'};
const MAX_REQUEST_BYTES=2048;
function json(data:unknown,status=200){return new Response(JSON.stringify(data),{status,headers:HEADERS});}

async function readBoundedJson(req:Request){
  // Une requête JSON n'autorise ni MIME alternatif ni flux indéfiniment lent.
  const contentType=req.headers.get('content-type')||'';
  if(!/^application\/json(?:\s*;|$)/i.test(contentType))throw new Error('JSON_REQUIRED');
  // Délai absolu : un client ne peut pas redémarrer le chronomètre par fragment.
  // readLimitedUtf8BodyWithDeadline refuse Content-Length trompeur, corps trop
  // gros, UTF-8 invalide et producteurs qui bloquent read()/cancel().
  const result=await readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,8000);
  if(!result.ok)throw new Error(
    result.reason==='REQUEST_TIMEOUT'?'REQUEST_TIMEOUT':
    result.reason==='REQUEST_TOO_LARGE'?'REQUEST_TOO_LARGE':'INVALID_JSON'
  );
  try{
    const body=JSON.parse(result.raw||'{}');
    if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
    return body;
  }catch{throw new Error('INVALID_JSON');}
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req);
    const body=await readBoundedJson(req);
    // Aucune coercition d'objet client dans une recherche de roman privilégiée.
    const slug=typeof body.slug==='string'?body.slug:'';
    if(slug.length>120||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug))
      return json({ok:false,error:'Roman invalide.'},400);
    const service=serviceClient();
    const {data:novel,error:novelError}=await service.from('sinjira_novels').select('id,slug,title,status,product_id,private_storage_bucket,private_storage_path,page_count,file_version,file_sha256,file_size_bytes,file_ready').eq('slug',slug).maybeSingle();
    if(novelError||!novel||novel.status!=='published')return json({ok:false,error:'Roman introuvable.'},404);
    const [ownerCheck,adminCheck]=await Promise.all([service.rpc('is_sinjira_owner',{p_user_id:user.id}),service.rpc('is_sinjira_admin',{p_user_id:user.id})]);
    // Un booléen SQL explicite, jamais une chaîne « false » ou un objet truthy.
    // Un diagnostic RPC non nul ne doit pas devenir une preuve de privilège.
    let entitled=(ownerCheck?.error==null&&ownerCheck?.data===true)||
      (adminCheck?.error==null&&adminCheck?.data===true);
    if(!entitled&&novel.product_id){
      const {data:entitlement}=await service.from('user_entitlements').select('product_id').eq('user_id',user.id).eq('product_id',novel.product_id).maybeSingle();
      if(entitlement){const {data:product}=await service.from('products').select('active').eq('id',novel.product_id).maybeSingle();entitled=product?.active===true;}
    }
    if(!entitled)return json({ok:false,error:'Votre compte ne possède pas le droit de lecture intégrale de ce roman.'},403);
    if(!novel.file_ready)return json({ok:false,error:'Le fichier intégral de cette édition n’est pas encore activé dans le stockage privé.',code:'FILE_NOT_READY',metadata:{page_count:novel.page_count,file_version:novel.file_version}},409);
    // Une URL signée ne suffit pas à protéger un PDF placé dans un bucket public.
    // Échec fermé si le chemin ou le statut réel du bucket est ambigu.
    if(!privateBookLocationValid(novel.private_storage_bucket,novel.private_storage_path)){
      return json({ok:false,error:'Fichier privé non configuré.'},503);
    }
    const {data:bucketMetadata,error:bucketMetadataError}=await service.storage.getBucket(novel.private_storage_bucket);
    if(bucketMetadataError||!isVerifiedPrivateBucket(bucketMetadata,novel.private_storage_bucket)){
      console.error('[get-novel-file-url]',{code:'NOVEL_PRIVATE_BUCKET_UNVERIFIED'});
      return json({ok:false,error:'Stockage privé indisponible.'},503);
    }
    const {data:signed,error:signedError}=await service.storage.from(novel.private_storage_bucket).createSignedUrl(novel.private_storage_path,600,{download:novel.slug+'.pdf'});
    if(signedError||!signed?.signedUrl)return json({ok:false,error:'Impossible de créer le lien sécurisé.'},500);
    return json({ok:true,url:signed.signedUrl,protected:true,expires_in:600,novel:{slug:novel.slug,title:novel.title,page_count:novel.page_count,file_version:novel.file_version,file_sha256:novel.file_sha256,file_size_bytes:novel.file_size_bytes}});
  }catch(error){
    const message=String(error?.message||'');
    if(message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(message==='REQUEST_TOO_LARGE')return json({ok:false,error:'Requête trop volumineuse.'},413);
    if(message==='REQUEST_TIMEOUT')return json({ok:false,error:'Délai de lecture de la requête dépassé.'},408);
    if(message==='JSON_REQUIRED')return json({ok:false,error:'Type de contenu JSON requis.'},415);
    if(message==='INVALID_JSON')return json({ok:false,error:'Corps JSON invalide.'},400);
    console.error('[get-novel-file-url]',{code:'NOVEL_ACCESS_FAILED'});
    return json({ok:false,error:'Erreur lors de l’accès au roman.'},500);
  }
});