import { corsHeaders, json } from '../_shared/cors.ts';
import { bearerToken, requiredUser, serviceClient } from '../_shared/auth.ts';

const CONFIRM_PHRASE='SUPPRIMER MON COMPTE';

async function removeStoragePaths(service:any,bucket:string,paths:(string|null|undefined)[]){
  const unique=[...new Set(paths.map(x=>String(x||'').trim()).filter(Boolean))];
  for(let i=0;i<unique.length;i+=100){
    const {error}=await service.storage.from(bucket).remove(unique.slice(i,i+100));
    if(error){
      console.error(`[SINJIRA delete] storage ${bucket}`,error);
      throw new Error('STORAGE_DELETE_FAILED');
    }
  }
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ok:false,error:'Méthode non autorisée.'},405);
  try {
    const user = await requiredUser(req);
    const service = serviceClient();

    const {data:isAdmin,error:adminError}=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
    if(adminError)throw new Error('ADMIN_CHECK_FAILED');
    if(isAdmin)return json({ok:false,error:'Suppression self-service interdite pour un compte propriétaire ou administrateur.',code:'OWNER_OR_ADMIN_DELETE_BLOCKED'},403);

    // Vérifier toute conservation légale AVANT de supprimer un fichier ou révoquer une contribution.
    // La RPC est service_role-only afin que le navigateur ne puisse pas sonder les holds d'autres comptes.
    const {data:canDelete,error:holdError}=await service.rpc('privacy_service_can_delete_user',{p_user_id:user.id});
    if(holdError)throw new Error('LEGAL_HOLD_CHECK_FAILED');
    if(canDelete!==true){
      return json({
        ok:false,
        error:'La suppression automatique ne peut pas être exécutée pour le moment en raison d’une obligation de conservation documentée. Vous pouvez suivre votre demande dans le Centre Vie privée.',
        code:'LEGAL_HOLD_ACTIVE'
      },409);
    }

    const token=bearerToken(req);
    const {data:aal,error:aalError}=await service.auth.mfa.getAuthenticatorAssuranceLevel(token);
    if(aalError||!aal)return json({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(aal.nextLevel==='aal2'&&aal.currentLevel!=='aal2')return json({ok:false,error:'Authentification renforcée requise.',code:'MFA_REQUIRED'},403);

    const body = await req.json().catch(()=>({}));
    if (body?.confirm !== CONFIRM_PHRASE) return json({ ok: false, error: 'Confirmation invalide.',code:'CONFIRMATION_REQUIRED' }, 400);

    const [profileRes,submissionRes,applicationRes]=await Promise.all([
      service.from('profiles').select('avatar_path').eq('user_id',user.id).maybeSingle(),
      service.from('character_submissions').select('photo_path').eq('user_id',user.id),
      service.from('sinjira_character_applications').select('photo_path').eq('user_id',user.id)
    ]);
    if(profileRes.error||submissionRes.error||applicationRes.error)throw new Error('STORAGE_PATH_LOOKUP_FAILED');

    await removeStoragePaths(service,'sinjira-avatars',[profileRes.data?.avatar_path]);
    await removeStoragePaths(service,'sinjira-character-sources',(submissionRes.data||[]).map((row:any)=>row.photo_path));
    await removeStoragePaths(service,'sinjira-character-submissions',(applicationRes.data||[]).map((row:any)=>row.photo_path));

    const {error:revokeError}=await service.rpc('revoke_sinjira_contributions', {
      p_user_id: user.id,
      p_session_id: null
    });
    if(revokeError)throw new Error('CONTRIBUTION_REVOKE_FAILED');

    const { error } = await service.auth.admin.deleteUser(user.id);
    if (error){
      console.error('[SINJIRA delete] auth delete',error);
      return json({ok:false,error:'Suppression du compte impossible après la préparation des données.',code:'AUTH_DELETE_FAILED'},500);
    }
    return json({ok:true,deleted:true,storage_cleaned:true,contributions_revoked:true});
  } catch (error) {
    console.error('[delete-player-account]',error);
    if(error?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(error?.message==='ADMIN_CHECK_FAILED')return json({ok:false,error:'Vérification du rôle impossible.',code:'ADMIN_CHECK_FAILED'},503);
    if(error?.message==='LEGAL_HOLD_CHECK_FAILED')return json({ok:false,error:'La vérification des obligations de conservation est temporairement indisponible. Aucune suppression n’a été effectuée.',code:'LEGAL_HOLD_CHECK_FAILED'},503);
    if(error?.message==='STORAGE_DELETE_FAILED'||error?.message==='STORAGE_PATH_LOOKUP_FAILED')return json({ok:false,error:'Les fichiers personnels n’ont pas pu être préparés pour suppression. Le compte n’a pas été supprimé.',code:error.message},503);
    if(error?.message==='CONTRIBUTION_REVOKE_FAILED')return json({ok:false,error:'Les contributions liées au compte n’ont pas pu être révoquées. Le compte n’a pas été supprimé.',code:'CONTRIBUTION_REVOKE_FAILED'},503);
    return json({ok:false,error:'Suppression impossible.',code:'DELETE_FAILED'},500);
  }
});
