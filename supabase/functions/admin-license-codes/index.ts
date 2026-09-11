import {corsHeaders} from '../_shared/cors.ts';
import {requiredAdmin} from '../_shared/auth.ts';

const VERSION='24.4.49';
const MAX_REQUEST_BYTES=4096;
const MAX_QUANTITY=5000;
const ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const SAFE_LOG_CODES=new Set([
  'AUTH_REQUIRED','ADMIN_REQUIRED','MFA_REQUIRED','MFA_STATE_UNAVAILABLE',
  'REQUEST_TOO_LARGE','JSON_REQUIRED','INVALID_JSON',
  'LICENSE_CODES_INSERT_FAILED','LICENSE_BATCH_ROLLBACK_FAILED'
]);
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

function safeLogCode(error:unknown){
  const code=error instanceof Error?error.message:'';
  return SAFE_LOG_CODES.has(code)?code:'LICENSE_BATCH_FAILED';
}

async function readLimitedJson(req:Request){
  const rawLength=req.headers.get('content-length');
  if(rawLength){
    const declared=Number(rawLength);
    if(!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  }
  const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(contentType!=='application/json')throw new Error('JSON_REQUIRED');
  const raw=await req.text();
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  let body:any;
  try{body=JSON.parse(raw||'{}');}
  catch{throw new Error('INVALID_JSON');}
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body;
}

function randomPart(n=5){const a=new Uint8Array(n);crypto.getRandomValues(a);return [...a].map(x=>ALPHABET[x%ALPHABET.length]).join('')}
function makeCode(prefix='SJR'){return `${prefix}-${randomPart()}-${randomPart()}-${randomPart()}`}
async function digest(code:string,pepper:string){const raw=new TextEncoder().encode(`${pepper}:${code.toUpperCase().replace(/\s+/g,'')}`);const h=await crypto.subtle.digest('SHA-256',raw);return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,'0')).join('')}

async function licenseHealth(s:any){
  const {data,error}=await s.rpc('sinjira_license_health');
  if(error||!data?.ok)return {ok:false,error};
  return {ok:true,data};
}

Deno.serve(async req=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,service:s}=await requiredAdmin(req);
    const body=await readLimitedJson(req);

    const pepper=Deno.env.get('SINJIRA_LICENSE_PEPPER');
    if(!pepper)return privateJson({ok:false,error:'Service de licence indisponible.',code:'LICENSE_PEPPER_MISSING'},503);

    const health=await licenseHealth(s);
    if(!health.ok)return privateJson({ok:false,error:'Service de licence indisponible.',code:'LICENSE_SCHEMA_UNAVAILABLE'},503);

    if(body?.action==='health'){
      return privateJson({ok:true,service:'admin-license-codes',version:VERSION,pepper_configured:true,schema:health.data});
    }

    const productSlug=String(body.product_slug||'').trim();
    const batchCode=String(body.batch_code||'').trim().toUpperCase();
    const quantity=Math.min(MAX_QUANTITY,Math.max(1,Number(body.quantity||0)));
    if(!productSlug||!batchCode||!Number.isInteger(quantity))return privateJson({ok:false,error:'Paramètres invalides.'},400);

    const {data:product,error:productError}=await s.from('products').select('slug,name,active').eq('slug',productSlug).maybeSingle();
    if(productError)throw productError;
    if(!product?.active)return privateJson({ok:false,error:'Produit inexistant ou inactif.'},400);

    const {data:batch,error:be}=await s.from('license_batches').insert({product_slug:productSlug,batch_code:batchCode,quantity,created_by:user.id}).select('id,batch_code').single();
    if(be){
      if(String(be.code||'')==='23505')return privateJson({ok:false,error:'Ce code de lot existe déjà.'},409);
      throw be;
    }

    const codes:string[]=[];const rows=[];
    const prefix=`SJR-${productSlug.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,6)||'PROD'}`;
    for(let i=0;i<quantity;i++){
      const code=makeCode(prefix);
      codes.push(code);
      rows.push({batch_id:batch.id,code_hash:await digest(code,pepper),product_slug:productSlug});
    }
    const {error:ie}=await s.from('activation_codes').insert(rows);
    if(ie){
      const {error:rollbackError}=await s.from('license_batches').delete().eq('id',batch.id);
      if(rollbackError)throw new Error('LICENSE_BATCH_ROLLBACK_FAILED');
      throw new Error('LICENSE_CODES_INSERT_FAILED');
    }
    return privateJson({ok:true,batch,codes,warning:'Les codes bruts sont retournés une seule fois. Conservez cet export dans un endroit sécurisé avant impression.'});
  }catch(e){
    console.error('[admin-license-codes]',safeLogCode(e));
    if(e?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(e?.message==='ADMIN_REQUIRED')return privateJson({ok:false,error:'Administration requise.',code:'ADMIN_REQUIRED'},403);
    if(e?.message==='MFA_REQUIRED')return privateJson({ok:false,error:'MFA_REQUIRED',code:'MFA_REQUIRED'},403);
    if(e?.message==='MFA_STATE_UNAVAILABLE')return privateJson({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(e?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE'},413);
    if(e?.message==='JSON_REQUIRED')return privateJson({ok:false,error:'Corps JSON requis.',code:'JSON_REQUIRED'},415);
    if(e?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON'},400);
    if(e?.message==='LICENSE_BATCH_ROLLBACK_FAILED')return privateJson({ok:false,error:'Génération interrompue; vérification administrateur requise.',code:'LICENSE_BATCH_ROLLBACK_FAILED'},500);
    if(e?.message==='LICENSE_CODES_INSERT_FAILED')return privateJson({ok:false,error:'Génération des codes impossible.',code:'LICENSE_CODES_INSERT_FAILED'},500);
    return privateJson({ok:false,error:'Génération des codes impossible.',code:'LICENSE_BATCH_FAILED'},500);
  }
});
