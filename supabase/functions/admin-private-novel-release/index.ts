import { corsHeaders } from '../_shared/cors.ts';
import { requiredAdmin } from '../_shared/auth.ts';

const MAX_REQUEST_BYTES=4096;
const DEFAULT_NOVEL_SLUG='la-cendre-du-jugement';
const ENABLE_CONFIRMATION='ACTIVER_LA_DIFFUSION_PRIVEE';
const SHA256_RE=/^[0-9a-f]{64}$/;

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
    const normalized=rawLength.trim();
    if(!/^\d+$/.test(normalized))throw new Error('REQUEST_TOO_LARGE');
    const declared=Number(normalized);
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
  }finally{
    reader.releaseLock();
  }

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
  }catch{
    throw new Error('INVALID_JSON');
  }
}

function safeSlug(value:unknown){
  const slug=String(value||DEFAULT_NOVEL_SLUG).trim();
  if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)||slug.length>160){
    throw new Error('NOVEL_SLUG_INVALID');
  }
  return slug;
}

function safeAction(value:unknown){
  const action=String(value||'status').trim();
  if(!['status','record_integrity','enable','disable'].includes(action)){
    throw new Error('ACTION_INVALID');
  }
  return action;
}

function safeDigest(value:unknown){
  const digest=String(value||'').trim().toLowerCase();
  if(!SHA256_RE.test(digest))throw new Error('SHA256_INVALID');
  return digest;
}

function safeSize(value:unknown){
  const size=Number(value);
  if(!Number.isSafeInteger(size)||size<=0||size>100*1024*1024){
    throw new Error('SIZE_INVALID');
  }
  return size;
}

function statusCode(message:string){
  if(message==='AUTH_REQUIRED')return 401;
  if(message==='ADMIN_REQUIRED'||message==='MFA_REQUIRED'||message==='MFA_SETUP_REQUIRED')return 403;
  if(message==='JSON_REQUIRED')return 415;
  if(message==='REQUEST_TOO_LARGE')return 413;
  if(['INVALID_JSON','ACTION_INVALID','NOVEL_SLUG_INVALID','SHA256_INVALID','SIZE_INVALID','ENABLE_CONFIRMATION_REQUIRED'].includes(message))return 400;
  if(message==='NOVEL_PRIVATE_ASSET_NOT_FOUND')return 404;
  if([
    'NOVEL_PRIVATE_STORAGE_NOT_CONFIGURED',
    'NOVEL_PRIVATE_BUCKET_REQUIRED',
    'NOVEL_PRIVATE_OBJECT_NOT_FOUND',
    'NOVEL_PRIVATE_OBJECT_SIZE_MISMATCH',
    'NOVEL_PRIVATE_OBJECT_MIME_MISMATCH',
    'NOVEL_INTEGRITY_MISMATCH',
    'NOVEL_PRIVATE_RELEASE_NOT_READY'
  ].includes(message))return 409;
  return 500;
}

function publicError(message:string){
  const known:Record<string,string>={
    AUTH_REQUIRED:'Connexion requise.',
    ADMIN_REQUIRED:'Accès administrateur requis.',
    MFA_REQUIRED:'Validation MFA requise.',
    MFA_SETUP_REQUIRED:'Configuration MFA requise.',
    JSON_REQUIRED:'Content-Type application/json requis.',
    REQUEST_TOO_LARGE:'Requête trop volumineuse.',
    INVALID_JSON:'JSON invalide.',
    ACTION_INVALID:'Action inconnue.',
    NOVEL_SLUG_INVALID:'Roman invalide.',
    SHA256_INVALID:'Empreinte SHA-256 invalide.',
    SIZE_INVALID:'Taille de fichier invalide.',
    ENABLE_CONFIRMATION_REQUIRED:'Confirmation explicite requise pour activer la diffusion.',
    NOVEL_PRIVATE_ASSET_NOT_FOUND:'Actif roman privé introuvable.',
    NOVEL_PRIVATE_STORAGE_NOT_CONFIGURED:'Stockage privé non configuré.',
    NOVEL_PRIVATE_BUCKET_REQUIRED:'Le bucket doit rester privé.',
    NOVEL_PRIVATE_OBJECT_NOT_FOUND:'Fichier privé introuvable.',
    NOVEL_PRIVATE_OBJECT_SIZE_MISMATCH:'La taille du fichier privé ne correspond pas au maître.',
    NOVEL_PRIVATE_OBJECT_MIME_MISMATCH:'Le type du fichier privé ne correspond pas au maître.',
    NOVEL_INTEGRITY_MISMATCH:'La preuve d’intégrité ne correspond pas au maître attendu.',
    NOVEL_PRIVATE_RELEASE_NOT_READY:'La diffusion privée n’est pas prête.'
  };
  return known[message]||'Opération de diffusion privée refusée.';
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:{...corsHeaders,'Cache-Control':'private, no-store, max-age=0'}});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);

  try{
    const {service}=await requiredAdmin(req);
    const body=await readBoundedJson(req);
    const action=safeAction(body.action);
    const novelSlug=safeSlug(body.novel_slug);

    if(action==='status'){
      const {data,error}=await service.rpc('sinjira_private_novel_release_status',{p_novel_slug:novelSlug});
      if(error)throw new Error(error.message||'RELEASE_STATUS_FAILED');
      return privateJson({ok:true,status:data});
    }

    if(action==='record_integrity'){
      const sha256=safeDigest(body.sha256);
      const sizeBytes=safeSize(body.size_bytes);
      const {data,error}=await service.rpc('sinjira_record_private_novel_integrity',{
        p_novel_slug:novelSlug,
        p_sha256:sha256,
        p_size_bytes:sizeBytes
      });
      if(error)throw new Error(error.message||'INTEGRITY_RECORD_FAILED');
      return privateJson({ok:true,status:data});
    }

    if(action==='disable'){
      const {data,error}=await service.rpc('sinjira_set_private_novel_delivery',{
        p_novel_slug:novelSlug,
        p_enabled:false
      });
      if(error)throw new Error(error.message||'RELEASE_DISABLE_FAILED');
      return privateJson({ok:true,status:data});
    }

    const confirmation=String(body.confirmation||'').trim();
    if(confirmation!==ENABLE_CONFIRMATION)throw new Error('ENABLE_CONFIRMATION_REQUIRED');

    const sha256=safeDigest(body.sha256);
    const {data:before,error:statusError}=await service.rpc(
      'sinjira_private_novel_release_status',
      {p_novel_slug:novelSlug}
    );
    if(statusError)throw new Error(statusError.message||'RELEASE_STATUS_FAILED');

    if(!before?.can_enable)throw new Error('NOVEL_PRIVATE_RELEASE_NOT_READY');
    if(String(before?.expected_sha256||'').toLowerCase()!==sha256){
      throw new Error('NOVEL_INTEGRITY_MISMATCH');
    }

    const {data,error}=await service.rpc('sinjira_set_private_novel_delivery',{
      p_novel_slug:novelSlug,
      p_enabled:true
    });
    if(error)throw new Error(error.message||'RELEASE_ENABLE_FAILED');

    return privateJson({ok:true,status:data});
  }catch(error){
    const raw=error instanceof Error?error.message:'';
    const normalized=raw.split(':')[0].trim();
    const status=statusCode(normalized);
    console.error('[admin-private-novel-release]',{code:normalized||'PRIVATE_NOVEL_RELEASE_FAILED'});
    return privateJson({ok:false,error:publicError(normalized),code:normalized||'PRIVATE_NOVEL_RELEASE_FAILED'},status);
  }
});
