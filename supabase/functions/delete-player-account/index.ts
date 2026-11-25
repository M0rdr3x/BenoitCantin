import { corsHeaders } from '../_shared/cors.ts';
import { bearerToken, requiredUser, serviceClient } from '../_shared/auth.ts';
import { readLimitedUtf8Body } from '../_shared/limited-body.mjs';

const CONFIRM_PHRASE='SUPPRIMER MON COMPTE';
const MAX_REQUEST_BYTES=1024;
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

async function readBoundedJson(req:Request){
  const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(contentType!=='application/json')throw new Error('JSON_REQUIRED');

  const limited=await readLimitedUtf8Body(req,MAX_REQUEST_BYTES);
  if(!limited.ok)throw new Error('REQUEST_TOO_LARGE');
  const raw=limited.raw;

  let body:unknown;
  try{ body=JSON.parse(raw); }
  catch{ throw new Error('INVALID_JSON'); }
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body as Record<string,unknown>;
}

// Les références issues de la base ne sont pas une preuve de propriété.
// Valider tous les chemins des trois compartiments avant la première mutation.
function ownedStoragePaths(paths:unknown[],userId:string):string[]{
  const unique=new Set<string>();
  for(const value of paths){
    if(value===null||value===undefined||value==='')continue;
    if(typeof value!=='string'||value!==value.trim()||value.length>1024||
       !value.startsWith(userId+'/')||/[%\\\u0000-\u001f\u007f]/.test(value)||
       value.split('/').some(part=>!part||part==='.'||part==='..')){
      throw new Error('STORAGE_PATH_OWNERSHIP_INVALID');
    }
    unique.add(value);
  }
  return [...unique];
}

async function removeStoragePaths(service:any,bucket:string,paths:string[]){
  const unique=paths;
  for(let i=0;i<unique.length;i+=100){
    const {error}=await service.storage.from(bucket).remove(unique.slice(i,i+100));
    if(error){
      console.error('[SINJIRA delete]',{code:'STORAGE_DELETE_FAILED'});
      throw new Error('STORAGE_DELETE_FAILED');
    }
  }
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return privateJson({ok:false,error:'Méthode non autorisée.'},405);
  try {
    const user = await requiredUser(req);
    const body=await readBoundedJson(req);
    if (body.confirm !== CONFIRM_PHRASE) return privateJson({ ok: false, error: 'Confirmation invalide.',code:'CONFIRMATION_REQUIRED' }, 400);

    const service = serviceClient();

    const {data:isAdmin,error:adminError}=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
    if(adminError||typeof isAdmin!=='boolean')throw new Error('ADMIN_CHECK_FAILED');
    if(isAdmin===true)return privateJson({ok:false,error:'Suppression self-service interdite pour un compte propriétaire ou administrateur.',code:'OWNER_OR_ADMIN_DELETE_BLOCKED'},403);

    // Vérifier toute conservation légale AVANT de supprimer un fichier ou révoquer une contribution.
    // La RPC est service_role-only afin que le navigateur ne puisse pas sonder les holds d'autres comptes.
    const {data:canDelete,error:holdError}=await service.rpc('privacy_service_can_delete_user',{p_user_id:user.id});
    if(holdError)throw new Error('LEGAL_HOLD_CHECK_FAILED');
    if(canDelete!==true){
      return privateJson({
        ok:false,
        error:'La suppression automatique ne peut pas être exécutée pour le moment en raison d’une obligation de conservation documentée. Vous pouvez suivre votre demande dans le Centre Vie privée.',
        code:'LEGAL_HOLD_ACTIVE'
      },409);
    }

    const token=bearerToken(req);
    const {data:aal,error:aalError}=await service.auth.mfa.getAuthenticatorAssuranceLevel(token);
    if(aalError||!aal||!['aal1','aal2'].includes(aal.currentLevel)||!['aal1','aal2'].includes(aal.nextLevel)||
       (aal.currentLevel==='aal2'&&aal.nextLevel!=='aal2'))return privateJson({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(aal.nextLevel==='aal2'&&aal.currentLevel!=='aal2')return privateJson({ok:false,error:'Authentification renforcée requise.',code:'MFA_REQUIRED'},403);

    const [profileRes,submissionRes,applicationRes]=await Promise.all([
      service.from('profiles').select('avatar_path').eq('user_id',user.id).maybeSingle(),
      service.from('character_submissions').select('photo_path').eq('user_id',user.id),
      service.from('sinjira_character_applications').select('photo_path').eq('user_id',user.id)
    ]);
    if(profileRes.error||submissionRes.error||applicationRes.error)throw new Error('STORAGE_PATH_LOOKUP_FAILED');

    if(!Array.isArray(submissionRes.data)||!Array.isArray(applicationRes.data))throw new Error('STORAGE_PATH_LOOKUP_FAILED');
    const avatarPaths=ownedStoragePaths([profileRes.data?.avatar_path],user.id);
    const sourcePaths=ownedStoragePaths(submissionRes.data.map((row:any)=>row.photo_path),user.id);
    const applicationPaths=ownedStoragePaths(applicationRes.data.map((row:any)=>row.photo_path),user.id);
    await removeStoragePaths(service,'sinjira-avatars',avatarPaths);
    await removeStoragePaths(service,'sinjira-character-sources',sourcePaths);
    await removeStoragePaths(service,'sinjira-character-submissions',applicationPaths);

    const {error:revokeError}=await service.rpc('revoke_sinjira_contributions', {
      p_user_id: user.id,
      p_session_id: null
    });
    if(revokeError)throw new Error('CONTRIBUTION_REVOKE_FAILED');

    const { error } = await service.auth.admin.deleteUser(user.id);
    if (error){
      console.error('[SINJIRA delete]',{code:'AUTH_DELETE_FAILED'});
      return privateJson({ok:false,error:'Suppression du compte impossible après la préparation des données.',code:'AUTH_DELETE_FAILED'},500);
    }
    return privateJson({ok:true,deleted:true,storage_cleaned:true,contributions_revoked:true});
  } catch (error) {
    console.error('[delete-player-account]',{code:'DELETE_FAILED'});
    if(error?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(error?.message==='JSON_REQUIRED')return privateJson({ok:false,error:'Corps JSON requis.',code:'JSON_REQUIRED'},415);
    if(error?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE'},413);
    if(error?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON'},400);
    if(error?.message==='ADMIN_CHECK_FAILED')return privateJson({ok:false,error:'Vérification du rôle impossible.',code:'ADMIN_CHECK_FAILED'},503);
    if(error?.message==='LEGAL_HOLD_CHECK_FAILED')return privateJson({ok:false,error:'La vérification des obligations de conservation est temporairement indisponible. Aucune suppression n’a été effectuée.',code:'LEGAL_HOLD_CHECK_FAILED'},503);
    if(error?.message==='STORAGE_DELETE_FAILED'||error?.message==='STORAGE_PATH_LOOKUP_FAILED'||error?.message==='STORAGE_PATH_OWNERSHIP_INVALID')return privateJson({ok:false,error:'Les fichiers personnels n’ont pas pu être préparés pour suppression. Le compte n’a pas été supprimé.',code:error.message},503);
    if(error?.message==='CONTRIBUTION_REVOKE_FAILED')return privateJson({ok:false,error:'Les contributions liées au compte n’ont pas pu être révoquées. Le compte n’a pas été supprimé.',code:'CONTRIBUTION_REVOKE_FAILED'},503);
    return privateJson({ok:false,error:'Suppression impossible.',code:'DELETE_FAILED'},500);
  }
});
