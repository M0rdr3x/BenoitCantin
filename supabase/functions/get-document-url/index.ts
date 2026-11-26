import { readLimitedUtf8Body } from '../_shared/limited-body.mjs';
import { corsHeaders } from '../_shared/cors.ts';
import { optionalUser, serviceClient } from '../_shared/auth.ts';
import { privateDocumentLocationValid, isVerifiedPrivateDocumentBucket, privateSignedDownloadUrlValid } from '../_shared/private-document-storage.mjs';

const MAX_REQUEST_BYTES=512;
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ranks:Record<string,number>={public:1,account:10,player:20,tester:30,admin:100};
const CANONICAL_PROJECT_RANKS=new Set([0,1,10,20,30]);
// Les propriétés héritées de Object.prototype ne sont pas des niveaux d'accès.
// Même un rang RPC inattendu (NaN/Infinity) ne doit jamais autoriser de lien.
function documentAccessAllowed(accessLevel:unknown,userRank:number){
  return typeof accessLevel==='string'
    && Object.prototype.hasOwnProperty.call(ranks,accessLevel)
    && Number.isFinite(userRank)
    && userRank>=ranks[accessLevel];
}
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

const DOCUMENT_URL_BASE='https://www.benoitcantin.com';
function externalUrlAllowed(value:string){
  // Les navigateurs interprètent parfois /\ comme // (origine externe).
  // Contrôler la destination après parsing et refuser les caractères ambigus.
  if(!value||value.length>2048||/[\u0000-\u0020\u007f\\]/.test(value))return false;
  try{
    const relative=value.startsWith('/');
    if(relative&&value.startsWith('//'))return false;
    const parsed=relative?new URL(value,DOCUMENT_URL_BASE):new URL(value);
    if(parsed.protocol!=='https:'||parsed.username||parsed.password)return false;
    // Interdire tout renvoi de document public vers un domaine tiers.
    if(parsed.origin!==DOCUMENT_URL_BASE)return false;
    return true;
  }catch{return false}
}

async function readLimitedJson(req:Request):Promise<{body?:any;response?:Response}>{
  const contentType=(req.headers.get('content-type')||'').toLowerCase();
  if(!contentType.startsWith('application/json')){
    return {response:privateJson({ok:false,error:'Type de contenu non autorisé.'},415)};
  }
  const limited=await readLimitedUtf8Body(req,MAX_REQUEST_BYTES);
  if(!limited.ok)return {response:privateJson({ok:false,error:'Requête trop volumineuse ou invalide.'},413)};
  const raw=limited.raw;
  try{return {body:JSON.parse(raw||'{}')}}catch{return {response:privateJson({ok:false,error:'Corps JSON invalide.'},400)}}
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const parsed=await readLimitedJson(req);
    if(parsed.response)return parsed.response;
    const document_id=typeof parsed.body?.document_id==='string'?parsed.body.document_id.trim():'';
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
      const adminCheck=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
      // Une RPC en erreur ou un résultat non booléen ne confère jamais
      // des privilèges, même lorsque sa valeur est truthy.
      if(!adminCheck||adminCheck.error!==null||typeof adminCheck.data!=='boolean'){
        return privateJson({ok:false,error:'Vérification des droits indisponible.'},503);
      }
      if(adminCheck.data===true)userRank=100;
      else{
        const rankCheck=await service.rpc('project_access_rank',{p_project_id:doc.project_id,p_user_id:user.id});
        // Ce SQL retourne un entier 0,1,10,20,30 pour les non-admins.
        // Le niveau 100 exigerait une confirmation admin déjà obtenue.
        if(!rankCheck||rankCheck.error!==null||typeof rankCheck.data!=='number'||
          !Number.isSafeInteger(rankCheck.data)||!CANONICAL_PROJECT_RANKS.has(rankCheck.data)){
          return privateJson({ok:false,error:'Vérification des droits indisponible.'},503);
        }
        userRank=rankCheck.data;
      }
    }else if(doc.projects?.visibility==='public')userRank=1;

    if(!documentAccessAllowed(doc.access_level,userRank)){
      return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);
    }

    if(doc.external_url){
      // Une autorisation API ne peut pas rendre confidentielle une URL statique.
      // Les fichiers restreints exigent un bucket privé et une URL signée.
      if(doc.access_level!=='public'||doc.projects?.visibility!=='public'){
        return privateJson({ok:false,error:'Document privé sans stockage sécurisé.'},500);
      }
      const url=String(doc.external_url).trim();
      if(!externalUrlAllowed(url))return privateJson({ok:false,error:'URL de document non autorisée.'},500);
      return privateJson({ok:true,url,protected:false,expires_in:null});
    }
    // Ne jamais signer un chemin douteux ni un objet situé dans un bucket public.
    // La vérification Storage suit la décision d'autorisation, sans repli permissif.
    if(!privateDocumentLocationValid(doc.storage_bucket,doc.storage_path)){
      return privateJson({ok:false,error:'Stockage privé indisponible.'},503);
    }
    const {data:bucketMetadata,error:bucketMetadataError}=await service.storage.getBucket(doc.storage_bucket);
    if(bucketMetadataError!==null||!isVerifiedPrivateDocumentBucket(bucketMetadata,doc.storage_bucket)){
      console.error('[get-document-url]',{code:'DOCUMENT_PRIVATE_BUCKET_UNVERIFIED'});
      return privateJson({ok:false,error:'Stockage privé indisponible.'},503);
    }

    const {data:signed,error:signedError}=await service.storage.from(doc.storage_bucket).createSignedUrl(doc.storage_path,600);
    if(signedError!==null||typeof signed?.signedUrl!=='string'||!privateSignedDownloadUrlValid(signed.signedUrl,Deno.env.get('SUPABASE_URL'),doc.storage_bucket,doc.storage_path))return privateJson({ok:false,error:'Impossible de créer le lien sécurisé.'},500);
    return privateJson({ok:true,url:signed.signedUrl,protected:true,expires_in:600});
  }catch{
    console.error('[get-document-url]',{code:'GET_DOCUMENT_URL_FAILED'});
    return privateJson({ok:false,error:'Erreur lors de l’accès au document.'},500);
  }
});
