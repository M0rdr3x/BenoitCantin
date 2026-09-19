import {corsHeaders} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';

const VERSION='24.4.49';
const MAX_REQUEST_BYTES=4096;
const MIN_CODE_LENGTH=12;
const MAX_CODE_LENGTH=80;
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

async function readLimitedJson(req:Request):Promise<{body?:any;response?:Response}>{
  const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(contentType!=='application/json'){
    return {response:privateJson({ok:false,error:'Corps JSON requis.'},415)};
  }

  const rawLength=req.headers.get('content-length');
  if(rawLength!==null){
    const normalizedLength=rawLength.trim();
    if(!/^\d+$/.test(normalizedLength)){
      return {response:privateJson({ok:false,error:'Requête invalide.'},400)};
    }
    const declaredLength=Number(normalizedLength);
    if(!Number.isSafeInteger(declaredLength)){
      return {response:privateJson({ok:false,error:'Requête invalide.'},400)};
    }
    if(declaredLength>MAX_REQUEST_BYTES){
      return {response:privateJson({ok:false,error:'Requête trop volumineuse.'},413)};
    }
  }

  const reader=req.body?.getReader();
  if(!reader)return {body:{}};
  const chunks:Uint8Array[]=[];
  let total=0;
  while(true){
    const {done,value}=await reader.read();
    if(done)break;
    if(!value)continue;
    total+=value.byteLength;
    if(total>MAX_REQUEST_BYTES){
      try{await reader.cancel()}catch{/* Le rejet 413 reste prioritaire. */}
      return {response:privateJson({ok:false,error:'Requête trop volumineuse.'},413)};
    }
    chunks.push(value);
  }

  const bytes=new Uint8Array(total);
  let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength}
  let raw:string;
  try{raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes)}catch{
    return {response:privateJson({ok:false,error:'Corps JSON invalide.'},400)};
  }
  try{return {body:JSON.parse(raw||'{}')}}catch{return {response:privateJson({ok:false,error:'Corps JSON invalide.'},400)}}
}

async function digest(code:string,pepper:string){
  const normalized=code.toUpperCase().replace(/\s+/g,'').trim();
  const raw=new TextEncoder().encode(`${pepper}:${normalized}`);
  const h=await crypto.subtle.digest('SHA-256',raw);
  return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,'0')).join('');
}

async function licenseHealth(s:any){
  const {data,error}=await s.rpc('sinjira_license_health');
  if(error||!data?.ok)return {ok:false,error};
  return {ok:true,data};
}

Deno.serve(async req=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req);
    const ageService=serviceClient();
    const {data:ageBand,error:ageError}=await ageService.rpc('sinjira_age_band',{p_user_id:user.id});
    if(ageError)return privateJson({ok:false,error:'La vérification de sécurité du compte est temporairement indisponible.',code:'AGE_STATE_UNAVAILABLE'},503);
    const normalizedAgeBand=String(ageBand||'unverified');
    if(normalizedAgeBand==='child')return privateJson({ok:false,error:'L’activation de licences n’est pas disponible pour les comptes de 11–12 ans.',code:'CHILD_ACTION_NOT_AVAILABLE_11_12'},403);
    if(!['adult','youth'].includes(normalizedAgeBand))return privateJson({ok:false,error:'L’activation de licences n’est pas disponible pour ce compte tant que son état de sécurité n’est pas standard.',code:'ACCOUNT_ACTION_NOT_AVAILABLE_RESTRICTED'},403);
    const parsed=await readLimitedJson(req);
    if(parsed.response)return parsed.response;
    const body=parsed.body||{};

    const pepper=Deno.env.get('SINJIRA_LICENSE_PEPPER');
    if(!pepper)return privateJson({ok:false,error:'Service de licence indisponible.',code:'LICENSE_PEPPER_MISSING'},503);
    const s=ageService;
    const health=await licenseHealth(s);
    if(!health.ok)return privateJson({ok:false,error:'Service de licence indisponible.',code:'LICENSE_SCHEMA_UNAVAILABLE'},503);

    if(body?.action==='health'){
      return privateJson({ok:true,service:'redeem-license-code',version:VERSION,pepper_configured:true,schema:health.data});
    }

    const value=String(body?.code||'').trim();
    if(value.length<MIN_CODE_LENGTH||value.length>MAX_CODE_LENGTH){
      return privateJson({ok:false,error:'Code invalide.'},400);
    }
    const hash=await digest(value,pepper);
    const {data,error}=await s.rpc('redeem_sinjira_activation',{p_code_hash:hash,p_user_id:user.id});
    if(error){
      const msg=String(error.message||'');
      if(msg.includes('CODE_INVALID_OR_USED'))return privateJson({ok:false,error:'Ce code ne peut pas être activé. Vérifiez le code ou contactez le support.'},409);
      if(msg.includes('PRODUCT_NOT_ACTIVE'))return privateJson({ok:false,error:'Ce produit n’est pas disponible pour activation.'},409);
      console.error('[redeem-license-code]',{code:'LICENSE_REDEEM_FAILED'});
      return privateJson({ok:false,error:'Activation impossible.',code:'LICENSE_REDEEM_FAILED'},500);
    }
    return privateJson({ok:true,entitlement:data?.[0]||null});
  }catch(e){
    const code=e instanceof Error?e.message:'';
    if(code==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.'},401);
    console.error('[redeem-license-code]',{code:'LICENSE_UNEXPECTED_ERROR'});
    return privateJson({ok:false,error:'Activation impossible.',code:'LICENSE_UNEXPECTED_ERROR'},500);
  }
});
