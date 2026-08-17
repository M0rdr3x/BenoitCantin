import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';

const VERSION='24.4.49';
const ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
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
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req),s=serviceClient();
    const {data:isAdmin,error:adminError}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});
    if(adminError)throw adminError;
    if(!isAdmin)return json({ok:false,error:'Administration requise.'},403);

    const pepper=Deno.env.get('SINJIRA_LICENSE_PEPPER');
    if(!pepper)return json({ok:false,error:'Service de licence indisponible.',code:'LICENSE_PEPPER_MISSING'},503);
    const body=await req.json().catch(()=>({}));
    const health=await licenseHealth(s);
    if(!health.ok)return json({ok:false,error:'Service de licence indisponible.',code:'LICENSE_SCHEMA_UNAVAILABLE'},503);

    if(body?.action==='health'){
      return json({ok:true,service:'admin-license-codes',version:VERSION,pepper_configured:true,schema:health.data});
    }

    const productSlug=String(body.product_slug||'').trim();
    const batchCode=String(body.batch_code||'').trim().toUpperCase();
    const quantity=Math.min(5000,Math.max(1,Number(body.quantity||0)));
    if(!productSlug||!batchCode||!Number.isInteger(quantity))return json({ok:false,error:'Paramètres invalides.'},400);

    const {data:product,error:productError}=await s.from('products').select('slug,name,active').eq('slug',productSlug).maybeSingle();
    if(productError)throw productError;
    if(!product?.active)return json({ok:false,error:'Produit inexistant ou inactif.'},400);

    const {data:batch,error:be}=await s.from('license_batches').insert({product_slug:productSlug,batch_code:batchCode,quantity,created_by:user.id}).select('id,batch_code').single();
    if(be){
      if(String(be.code||'')==='23505')return json({ok:false,error:'Ce code de lot existe déjà.'},409);
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
    if(ie)throw ie;
    return json({ok:true,batch,codes,warning:'Les codes bruts sont retournés une seule fois. Conservez cet export dans un endroit sécurisé avant impression.'});
  }catch(e){
    console.error('[admin-license-codes]',e);
    return json({ok:false,error:'Génération des codes impossible.',code:'LICENSE_BATCH_FAILED'},500);
  }
});
