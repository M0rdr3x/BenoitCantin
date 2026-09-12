import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

const PRODUCT_SLUG='sinjira-livre-01-la-cendre-du-jugement';
const SIGNED_URL_SECONDS=300;
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

function privateStorageConfig(){
  const enabled=Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED')==='true';
  const bucket=(Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_BUCKET')||'').trim();
  const storagePath=(Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_PATH')||'').trim();
  if(!enabled)return {enabled:false,bucket:'',storagePath:''};
  if(!bucket||!storagePath||storagePath.startsWith('/')||storagePath.includes('://')){
    throw new Error('PRIVATE_STORAGE_NOT_CONFIGURED');
  }
  return {enabled:true,bucket,storagePath};
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);

  try{
    // La fonction privée ne révèle jamais son état d’activation ou de stockage
    // avant d’avoir validé l’identité du compte.
    const user=await requiredUser(req);
    const storage=privateStorageConfig();
    if(!storage.enabled){
      return privateJson({ok:false,available:false,error:'La diffusion privée du Livre I n’est pas activée.'},503);
    }

    const service=serviceClient();

    const {data:product,error:productError}=await service
      .from('products')
      .select('id,slug,active')
      .eq('slug',PRODUCT_SLUG)
      .eq('active',true)
      .maybeSingle();
    if(productError||!product){
      return privateJson({ok:false,error:'Livre indisponible.'},503);
    }

    const {data:entitlement,error:entitlementError}=await service
      .from('user_entitlements')
      .select('product_id')
      .eq('user_id',user.id)
      .eq('product_id',product.id)
      .maybeSingle();
    if(entitlementError){
      console.error('[get-private-book-url]',{code:'BOOK_ENTITLEMENT_CHECK_FAILED'});
      return privateJson({ok:false,error:'Impossible de vérifier votre droit d’accès.'},500);
    }
    if(!entitlement){
      return privateJson({ok:false,error:'Votre compte ne possède pas ce livre.'},403);
    }

    const {data:signed,error:signedError}=await service.storage
      .from(storage.bucket)
      .createSignedUrl(storage.storagePath,SIGNED_URL_SECONDS,{download:'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf'});
    if(signedError||!signed?.signedUrl){
      console.error('[get-private-book-url]',{code:'BOOK_SIGNED_URL_FAILED'});
      return privateJson({ok:false,error:'Impossible de préparer le téléchargement sécurisé.'},500);
    }

    return privateJson({
      ok:true,
      protected:true,
      url:signed.signedUrl,
      expires_in:SIGNED_URL_SECONDS,
      product_slug:PRODUCT_SLUG
    });
  }catch(error){
    const message=error instanceof Error?error.message:'';
    if(message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.'},401);
    if(message==='PRIVATE_STORAGE_NOT_CONFIGURED'){
      console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_STORAGE_NOT_CONFIGURED'});
      return privateJson({ok:false,error:'Diffusion privée non configurée.'},503);
    }
    console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_DELIVERY_FAILED'});
    return privateJson({ok:false,error:'Erreur lors de la préparation du téléchargement.'},500);
  }
});
