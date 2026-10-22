import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

const HEADERS={...corsHeaders,'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'};
const MAX_REQUEST_BYTES=2048;
function json(data:unknown,status=200){return new Response(JSON.stringify(data),{status,headers:HEADERS});}

async function readBoundedJson(req:Request){
  if(!req.body)return {};
  const reader=req.body.getReader();
  const chunks:Uint8Array[]=[];
  let total=0;
  while(true){
    const {done,value}=await reader.read();
    if(done)break;
    if(value){
      total+=value.byteLength;
      if(total>MAX_REQUEST_BYTES){
        try{await reader.cancel();}catch{}
        throw new Error('REQUEST_TOO_LARGE');
      }
      chunks.push(value);
    }
  }
  const bytes=new Uint8Array(total);
  let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
  if(!bytes.length)return {};
  try{return JSON.parse(new TextDecoder().decode(bytes));}
  catch{throw new Error('INVALID_JSON');}
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req);
    const body=await readBoundedJson(req);
    const slug=String(body?.slug||'').trim();
    if(!slug||slug.length>120)return json({ok:false,error:'Roman invalide.'},400);
    const service=serviceClient();
    const {data:novel,error:novelError}=await service.from('sinjira_novels').select('id,slug,title,status,product_id,private_storage_bucket,private_storage_path,page_count,file_version,file_sha256,file_size_bytes,file_ready').eq('slug',slug).maybeSingle();
    if(novelError||!novel||novel.status!=='published')return json({ok:false,error:'Roman introuvable.'},404);
    const [{data:isOwner},{data:isAdmin}]=await Promise.all([service.rpc('is_sinjira_owner',{p_user_id:user.id}),service.rpc('is_sinjira_admin',{p_user_id:user.id})]);
    let entitled=Boolean(isOwner||isAdmin);
    if(!entitled&&novel.product_id){
      const {data:entitlement}=await service.from('user_entitlements').select('product_id').eq('user_id',user.id).eq('product_id',novel.product_id).maybeSingle();
      if(entitlement){const {data:product}=await service.from('products').select('active').eq('id',novel.product_id).maybeSingle();entitled=product?.active===true;}
    }
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
    if(message==='INVALID_JSON')return json({ok:false,error:'Corps JSON invalide.'},400);
    console.error(error);
    return json({ok:false,error:'Erreur lors de l’accès au roman.'},500);
  }
});