import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';

const VERSION='24.4.49';

async function digest(code:string,pepper:string){const normalized=code.toUpperCase().replace(/\s+/g,'').trim();const raw=new TextEncoder().encode(`${pepper}:${normalized}`);const h=await crypto.subtle.digest('SHA-256',raw);return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,'0')).join('')}

async function licenseHealth(s:any){
  const {data,error}=await s.rpc('sinjira_license_health');
  if(error||!data?.ok)return {ok:false,error};
  return {ok:true,data};
}

Deno.serve(async req=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req);
    const pepper=Deno.env.get('SINJIRA_LICENSE_PEPPER');
    if(!pepper)return json({ok:false,error:'Service de licence indisponible.',code:'LICENSE_PEPPER_MISSING'},503);
    const body=await req.json().catch(()=>({}));
    const s=serviceClient();
    const health=await licenseHealth(s);
    if(!health.ok)return json({ok:false,error:'Service de licence indisponible.',code:'LICENSE_SCHEMA_UNAVAILABLE'},503);

    if(body?.action==='health'){
      return json({ok:true,service:'redeem-license-code',version:VERSION,pepper_configured:true,schema:health.data});
    }

    const value=String(body?.code||'').trim();
    if(value.length<12)return json({ok:false,error:'Code invalide.'},400);
    const hash=await digest(value,pepper);
    const {data,error}=await s.rpc('redeem_sinjira_activation',{p_code_hash:hash,p_user_id:user.id});
    if(error){
      const msg=String(error.message||'');
      if(msg.includes('CODE_INVALID_OR_USED'))return json({ok:false,error:'Ce code ne peut pas être activé. Vérifiez le code ou contactez le support.'},409);
      if(msg.includes('PRODUCT_NOT_ACTIVE'))return json({ok:false,error:'Ce produit n’est pas disponible pour activation.'},409);
      console.error('[redeem-license-code]',error);
      return json({ok:false,error:'Activation impossible.',code:'LICENSE_REDEEM_FAILED'},500);
    }
    return json({ok:true,entitlement:data?.[0]||null});
  }catch(e){
    console.error('[redeem-license-code]',e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    return json({ok:false,error:'Activation impossible.',code:'LICENSE_UNEXPECTED_ERROR'},500);
  }
});
