import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';
import {
  PRIVATE_NOVEL_SIGNED_URL_SECONDS,
  getPrivateNovelAsset,
  requirePrivateNovelAccess,
  resolvePrivateNovelStorage
} from '../_shared/privateNovel.ts';

const MAX_REQUEST_BYTES = 2048;

const PRIVATE_HEADERS={
  ...corsHeaders,
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  'Pragma':'no-cache',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer'
};

function privateJson(data:unknown,status=200){
  return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS});
}

async function readBoundedJson(req:Request){
  const type=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(type!=='application/json')throw new Error('JSON_REQUIRED');
  const rawLength=req.headers.get('content-length');
  if(rawLength!==null){
    const normalizedLength=rawLength.trim();
    if(!/^\d+$/.test(normalizedLength))throw new Error('REQUEST_TOO_LARGE');
    const declared=Number(normalizedLength);
    if(!Number.isSafeInteger(declared)||declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  }
  if(!req.body)throw new Error('INVALID_JSON');
  const reader=req.body.getReader();
  const chunks:Uint8Array[]=[];
  let total=0;
  try{
    while(true){
      const {value,done}=await reader.read();
      if(done)break;
      if(!value)continue;
      total+=value.byteLength;
      if(total>MAX_REQUEST_BYTES){
        await reader.cancel('REQUEST_TOO_LARGE').catch(()=>undefined);
        throw new Error('REQUEST_TOO_LARGE');
      }
      chunks.push(value);
    }
  }finally{reader.releaseLock();}
  const bytes=new Uint8Array(total);
  let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
  let raw:string;
  try{raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);}
  catch{throw new Error('INVALID_JSON');}
  try{
    const parsed=JSON.parse(raw);
    if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))throw new Error();
    return parsed as Record<string,unknown>;
  }catch{throw new Error('INVALID_JSON');}
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:{...corsHeaders,'Cache-Control':'private, no-store, max-age=0'}});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);

  try{
    const user=await requiredUser(req);
    const body=await readBoundedJson(req);
    const novelSlug=String(body.novel_slug||'').trim();
    const mode=body?.mode==='download'?'download':'read';

    const service=serviceClient();
    const {data:ageBand,error:ageError}=await service.rpc('sinjira_age_band',{p_user_id:user.id});
    if(ageError)throw new Error('NOVEL_AGE_STATE_UNAVAILABLE');
    const normalizedAgeBand=String(ageBand||'unverified');
    if(normalizedAgeBand==='child')throw new Error('NOVEL_NOT_AVAILABLE_11_12');
    if(!['adult','youth'].includes(normalizedAgeBand))throw new Error('NOVEL_ACCOUNT_RESTRICTED');

    const asset=await getPrivateNovelAsset(service,novelSlug);
    const access=await requirePrivateNovelAccess(service,user.id,asset);
    const storage=resolvePrivateNovelStorage(asset);

    const options=mode==='download'&&asset.download_name
      ? {download:String(asset.download_name)}
      : undefined;
    const {data:signed,error:signedError}=await service.storage
      .from(storage.bucket)
      .createSignedUrl(storage.storagePath,PRIVATE_NOVEL_SIGNED_URL_SECONDS,options);

    if(signedError||!signed?.signedUrl){
      console.error('[get-private-novel-url]',{code:'NOVEL_SIGNED_URL_FAILED',novel_slug:asset.novel_slug});
      return privateJson({ok:false,error:'Impossible de préparer cet accès privé.'},500);
    }

    return privateJson({
      ok:true,
      protected:true,
      mode,
      access,
      novel_slug:asset.novel_slug,
      title:asset.title,
      total_pages:asset.total_pages,
      url:signed.signedUrl,
      expires_in:PRIVATE_NOVEL_SIGNED_URL_SECONDS
    });
  }catch(error){
    const message=error instanceof Error?error.message:'';
    if(message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.'},401);
    if(message==='JSON_REQUIRED')return privateJson({ok:false,error:'Corps JSON requis.'},415);
    if(message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.'},413);
    if(message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.'},400);
    if(message==='NOVEL_SLUG_INVALID')return privateJson({ok:false,error:'Roman invalide.'},400);
    if(message==='NOVEL_NOT_AVAILABLE_11_12')return privateJson({ok:false,error:'Ce contenu privé n’est pas encore classé pour les comptes de 11–12 ans.'},403);
    if(message==='NOVEL_ACCOUNT_RESTRICTED')return privateJson({ok:false,error:'Ce contenu privé n’est pas disponible pour ce compte tant que son état de sécurité n’est pas standard.'},403);
    if(message==='NOVEL_AGE_STATE_UNAVAILABLE')return privateJson({ok:false,error:'La vérification d’âge du compte est temporairement indisponible.'},503);
    if(message==='NOVEL_ACCESS_DENIED')return privateJson({ok:false,error:'Votre compte ne possède pas ce roman.'},403);
    if(message==='NOVEL_UNAVAILABLE'||message==='NOVEL_PRIVATE_ASSET_NOT_FOUND')return privateJson({ok:false,available:false,error:'L’intégrale privée de ce roman n’est pas encore disponible.'},404);
    if(message==='NOVEL_PRIVATE_DELIVERY_DISABLED'||message==='NOVEL_PRIVATE_STORAGE_NOT_CONFIGURED')return privateJson({ok:false,available:false,error:'La diffusion privée de ce roman n’est pas encore configurée.'},503);
    if(message==='NOVEL_ACCESS_CHECK_FAILED'){
      console.error('[get-private-novel-url]',{code:'NOVEL_ACCESS_CHECK_FAILED'});
      return privateJson({ok:false,error:'Impossible de vérifier votre droit d’accès.'},500);
    }
    console.error('[get-private-novel-url]',{code:'NOVEL_PRIVATE_DELIVERY_FAILED'});
    return privateJson({ok:false,error:'Erreur lors de la préparation de l’accès privé.'},500);
  }
});
