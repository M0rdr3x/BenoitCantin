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
  const rawLength=req.headers.get('content-length');
  if(rawLength){
    const declared=Number(rawLength);
    if(!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES){
      return {response:privateJson({ok:false,error:'Requête trop volumineuse.'},413)};
    }
  }
  const raw=await req.text();
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES){
    return {response:privateJson({ok:false,error:'Requête trop volumineuse.'},413)};
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
    const parsed=await readLimitedJson(req);
    if(parsed.response)return parsed.response;
    const body=parsed.body||{};

    const pepper=Deno.env.get('SINJIRA_LICENSE_PEPPER');
    if(!pepper)return privateJson({ok:false,error:'Service de licence indisponible.',code:'LICENSE_PEPPER_MISSING'},503);
    const s=serviceClient();
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
      console.error('[redeem-license-code]',error);
      return privateJson({ok:false,error:'Activation impossible.',code:'LICENSE_REDEEM_FAILED'},500);
    }
    return privateJson({ok:true,entitlement:data?.[0]||null});
  }catch(e){
    console.error('[redeem-license-code]',e);
    if(e?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.'},401);
    return privateJson({ok:false,error:'Activation impossible.',code:'LICENSE_UNEXPECTED_ERROR'},500);
  }
});
