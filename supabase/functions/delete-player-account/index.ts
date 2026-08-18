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

    // Un compte administrateur/propriétaire ne peut jamais s’autodétruire depuis
    // une page utilisateur. Il doit d’abord être retiré explicitement de l’administration.
    const {data:isAdmin,error:adminError}=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
    if(adminError)throw new Error('ADMIN_CHECK_FAILED');
    if(isAdmin)return json({ok:false,error:'Suppression self-service interdite pour un compte propriétaire ou administrateur.',code:'OWNER_OR_ADMIN_DELETE_BLOCKED'},403);

    // Si ce compte a activé un second facteur, une session aal2 est obligatoire
    // pour l’action irréversible. Sans facteur vérifié, Supabase retourne aal1/aal1.
    const token=bearerToken(req);
    const {data:aal,error:aalError}=await service.auth.mfa.getAuthenticatorAssuranceLevel(token);
    if(aalError||!aal)return json({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(aal.nextLevel==='aal2'&&aal.currentLevel!=='aal2')return json({ok:false,error:'Authentification renforcée requise.',code:'MFA_REQUIRED'},403);

    const body = await req.json().catch(()=>({}));
    if (body?.confirm !== CONFIRM_PHRASE) return json({ ok: false, error: 'Confirmation invalide.',code:'CONFIRMATION_REQUIRED' }, 400);

    // Lire les chemins avant la suppression des lignes. Les objets Storage ne
    // suivent pas automatiquement les cascades de auth.users.
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
    if(error?.message==='STORAGE_DELETE_FAILED'||error?.message==='STORAGE_PATH_LOOKUP_FAILED')return json({ok:false,error:'Les fichiers personnels n’ont pas pu être préparés pour suppression. Le compte n’a pas été supprimé.',code:error.message},503);
    if(error?.message==='CONTRIBUTION_REVOKE_FAILED')return json({ok:false,error:'Les contributions liées au compte n’ont pas pu être révoquées. Le compte n’a pas été supprimé.',code:'CONTRIBUTION_REVOKE_FAILED'},503);
    return json({ok:false,error:'Suppression impossible.',code:'DELETE_FAILED'},500);
  }
});
