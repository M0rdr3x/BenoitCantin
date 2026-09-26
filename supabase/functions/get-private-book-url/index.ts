import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';
import {
  LIVRE_I_PRODUCT_SLUG,
  LIVRE_I_SIGNED_URL_SECONDS,
  privateBookStorageConfig,
  requirePrivateBookAccess
} from '../_shared/privateBook.ts';

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

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:{...corsHeaders,'Cache-Control':'private, no-store, max-age=0'}});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);

  try{
    const user=await requiredUser(req);
    const service=serviceClient();
    const {data:ageBand,error:ageError}=await service.rpc('sinjira_age_band',{p_user_id:user.id});
    if(ageError)throw new Error('BOOK_AGE_STATE_UNAVAILABLE');
    const normalizedAgeBand=String(ageBand||'unverified');
    if(normalizedAgeBand==='child')throw new Error('BOOK_NOT_AVAILABLE_11_12');
    if(!['adult','youth'].includes(normalizedAgeBand))throw new Error('BOOK_ACCOUNT_RESTRICTED');
    await requirePrivateBookAccess(service,user.id);

    // Ne révèle l'état d'activation ou de configuration du stockage qu'après
    // authentification ET autorisation du compte pour ce Livre I.
    const storage=privateBookStorageConfig();
    if(!storage.enabled){
      return privateJson({ok:false,available:false,error:'La diffusion privée du Livre I n’est pas activée.'},503);
    }

    const {data:signed,error:signedError}=await service.storage
      .from(storage.bucket)
      .createSignedUrl(storage.storagePath,LIVRE_I_SIGNED_URL_SECONDS,{download:'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf'});
    if(signedError||!signed?.signedUrl){
      console.error('[get-private-book-url]',{code:'BOOK_SIGNED_URL_FAILED'});
      return privateJson({ok:false,error:'Impossible de préparer le téléchargement sécurisé.'},500);
    }

    return privateJson({
      ok:true,
      protected:true,
      url:signed.signedUrl,
      expires_in:LIVRE_I_SIGNED_URL_SECONDS,
      product_slug:LIVRE_I_PRODUCT_SLUG
    });
  }catch(error){
    const message=error instanceof Error?error.message:'';
    if(message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.'},401);
    if(message==='BOOK_NOT_AVAILABLE_11_12')return privateJson({ok:false,error:'Ce contenu privé n’est pas encore classé pour les comptes de 11–12 ans.'},403);
    if(message==='BOOK_ACCOUNT_RESTRICTED')return privateJson({ok:false,error:'Ce contenu privé n’est pas disponible pour ce compte tant que son état de sécurité n’est pas standard.'},403);
    if(message==='BOOK_AGE_STATE_UNAVAILABLE')return privateJson({ok:false,error:'La vérification d’âge du compte est temporairement indisponible.'},503);
    if(message==='BOOK_ACCESS_DENIED')return privateJson({ok:false,error:'Votre compte ne possède pas ce livre.'},403);
    if(message==='BOOK_UNAVAILABLE')return privateJson({ok:false,error:'Livre indisponible.'},503);
    if(message==='BOOK_ACCESS_CHECK_FAILED'){
      console.error('[get-private-book-url]',{code:'BOOK_ACCESS_CHECK_FAILED'});
      return privateJson({ok:false,error:'Impossible de vérifier votre droit d’accès.'},500);
    }
    if(message==='PRIVATE_STORAGE_NOT_CONFIGURED'){
      console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_STORAGE_NOT_CONFIGURED'});
      return privateJson({ok:false,error:'Diffusion privée non configurée.'},503);
    }
    console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_DELIVERY_FAILED'});
    return privateJson({ok:false,error:'Erreur lors de la préparation du téléchargement.'},500);
  }
});
