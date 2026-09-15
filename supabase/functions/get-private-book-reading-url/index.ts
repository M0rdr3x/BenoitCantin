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
    const storage=privateBookStorageConfig();
    if(!storage.enabled){
      return privateJson({ok:false,available:false,error:'La lecture privée du Livre I n’est pas activée.'},503);
    }

    const service=serviceClient();
    await requirePrivateBookAccess(service,user.id);

    const {data:signed,error:signedError}=await service.storage
      .from(storage.bucket)
      .createSignedUrl(storage.storagePath,LIVRE_I_SIGNED_URL_SECONDS);
    if(signedError||!signed?.signedUrl){
      console.error('[get-private-book-reading-url]',{code:'BOOK_READER_SIGNED_URL_FAILED'});
      return privateJson({ok:false,error:'Impossible de préparer la lecture sécurisée.'},500);
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
    if(message==='BOOK_ACCESS_DENIED')return privateJson({ok:false,error:'Votre compte ne possède pas ce livre.'},403);
    if(message==='BOOK_UNAVAILABLE')return privateJson({ok:false,error:'Livre indisponible.'},503);
    if(message==='BOOK_ACCESS_CHECK_FAILED'){
      console.error('[get-private-book-reading-url]',{code:'BOOK_READER_ACCESS_CHECK_FAILED'});
      return privateJson({ok:false,error:'Impossible de vérifier votre droit d’accès.'},500);
    }
    if(message==='PRIVATE_STORAGE_NOT_CONFIGURED'){
      console.error('[get-private-book-reading-url]',{code:'BOOK_READER_STORAGE_NOT_CONFIGURED'});
      return privateJson({ok:false,error:'Lecture privée non configurée.'},503);
    }
    console.error('[get-private-book-reading-url]',{code:'BOOK_READER_FAILED'});
    return privateJson({ok:false,error:'Erreur lors de la préparation de la lecture.'},500);
  }
});
