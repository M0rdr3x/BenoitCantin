import { corsHeaders } from '../_shared/cors.ts';
import { optionalUser, serviceClient } from '../_shared/auth.ts';

const MAX_REQUEST_BYTES=512;
const REQUEST_BODY_TOO_LARGE='REQUEST_BODY_TOO_LARGE';
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

function externalUrlAllowed(value:string){
  if(value.startsWith('/')&&!value.startsWith('//'))return true;
  try{return new URL(value).protocol==='https:'}catch{return false}
}

function isRecord(value:unknown):value is Record<string,unknown>{
  return !!value&&typeof value==='object'&&!Array.isArray(value);
}

async function readRequestBody(req:Request){
  if(!req.body)return '';
  const reader=req.body.getReader();
  const decoder=new TextDecoder();
  let totalBytes=0,raw='';
  try{
    while(true){
      const {done,value}=await reader.read();
      if(done)break;
      if(!value)continue;
      totalBytes+=value.byteLength;
      if(totalBytes>MAX_REQUEST_BYTES){
        await reader.cancel();
        throw new Error(REQUEST_BODY_TOO_LARGE);
      }
      raw+=decoder.decode(value,{stream:true});
    }
    raw+=decoder.decode();
    return raw;
  }finally{
    reader.releaseLock();
  }
}

async function readLimitedJson(req:Request):Promise<{body?:Record<string,unknown>;response?:Response}>{
  const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(contentType!=='application/json'){
    return {response:privateJson({ok:false,error:'Type de contenu non autorisé.'},415)};
  }
  const rawLength=req.headers.get('content-length');
  if(rawLength!==null){
    const normalized=rawLength.trim();
    if(!/^\d+$/.test(normalized)){
      return {response:privateJson({ok:false,error:'Requête invalide.'},400)};
    }
    const declared=Number(normalized);
    if(!Number.isSafeInteger(declared)){
      return {response:privateJson({ok:false,error:'Requête invalide.'},400)};
    }
    if(declared>MAX_REQUEST_BYTES){
      return {response:privateJson({ok:false,error:'Requête trop volumineuse.'},413)};
    }
  }
  let raw:string;
  try{
    raw=await readRequestBody(req);
  }catch(error){
    if(error instanceof Error&&error.message===REQUEST_BODY_TOO_LARGE){
      return {response:privateJson({ok:false,error:'Requête trop volumineuse.'},413)};
    }
    throw error;
  }
  let parsed:unknown;
  try{parsed=JSON.parse(raw)}catch{return {response:privateJson({ok:false,error:'Corps JSON invalide.'},400)}}
  if(!isRecord(parsed)||Object.keys(parsed).length!==1||typeof parsed.document_id!=='string'){
    return {response:privateJson({ok:false,error:'Corps JSON invalide.'},400)};
  }
  return {body:parsed};
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const parsed=await readLimitedJson(req);
    if(parsed.response)return parsed.response;
    const documentIdValue=parsed.body?.document_id;
    const document_id=typeof documentIdValue==='string'?documentIdValue.trim():'';
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

    let userRank=0;
    if(user){
      const {data:isAdmin}=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
      if(isAdmin===true)userRank=100;
      else{
        const {data:accessRank}=await service.rpc('project_access_rank',{p_project_id:doc.project_id,p_user_id:user.id});
        const normalizedRank=Number(accessRank??0);
        if(!Number.isFinite(normalizedRank)||normalizedRank<0){
          console.error('[get-document-url]',{code:'INVALID_PROJECT_ACCESS_RANK',projectId:doc.project_id,userId:user.id});
          return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);
        }
        userRank=normalizedRank;
      }
    }else if(doc.projects?.visibility==='public')userRank=1;

    const requiredRank=typeof doc.access_level==='string'?(ranks[doc.access_level]??999):999;
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
