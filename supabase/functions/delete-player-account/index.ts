import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

const OWNER_EMAIL='kingtyrano@gmail.com';

async function removePaths(service:any,bucket:string,paths:string[]){
  const unique=[...new Set(paths.map(x=>String(x||'').trim()).filter(Boolean))];
  if(!unique.length)return;
  const {error}=await service.storage.from(bucket).remove(unique);
  if(error)throw new Error(`STORAGE_DELETE_FAILED:${bucket}`);
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ok:false,error:'Méthode non autorisée.'},405);
  try {
    const user = await requiredUser(req);
    const body = await req.json().catch(()=>({}));
    if (body?.confirm !== 'SUPPRIMER') return json({ ok: false, error: 'Confirmation invalide.' }, 400);
    if(String(user.email||'').trim().toLowerCase()===OWNER_EMAIL){
      return json({ok:false,error:'Le compte propriétaire unique ne peut pas être supprimé depuis l’interface publique. Utilisez une procédure administrative de transfert/récupération.'},409);
    }

    const service = serviceClient();
    const [{data:profile,error:profileError},{data:submissions,error:submissionError}]=await Promise.all([
      service.from('profiles').select('avatar_path').eq('user_id',user.id).maybeSingle(),
      service.from('character_submissions').select('photo_path').eq('user_id',user.id)
    ]);
    if(profileError||submissionError)throw profileError||submissionError;

    const { error: revokeError } = await service.rpc('revoke_sinjira_contributions', {
      p_user_id: user.id,
      p_session_id: null
    });
    if(revokeError)throw new Error('CONTRIBUTION_REVOKE_FAILED');

    // Les objets Storage ne sont pas supprimés automatiquement par les cascades SQL.
    // On efface d'abord les chemins privés connus; si cette étape échoue, le compte reste
    // intact afin d'éviter de perdre les pointeurs vers des fichiers personnels orphelins.
    await removePaths(service,'sinjira-avatars',[profile?.avatar_path]);
    await removePaths(service,'sinjira-character-sources',(submissions||[]).map((x:any)=>x.photo_path));

    const { error } = await service.auth.admin.deleteUser(user.id);
    if (error) throw error;
    return json({ ok: true });
  } catch (error) {
    console.error('[SINJIRA delete account]',error);
    if (error?.message === 'AUTH_REQUIRED') return json({ ok: false, error: 'Connexion requise.' }, 401);
    if (error?.message === 'CONTRIBUTION_REVOKE_FAILED') return json({ok:false,error:'La révocation des contributions n’a pas pu être confirmée. Le compte n’a pas été supprimé.'},502);
    if (String(error?.message||'').startsWith('STORAGE_DELETE_FAILED:')) return json({ok:false,error:'Un fichier personnel n’a pas pu être supprimé du stockage. Le compte n’a pas été supprimé.'},502);
    return json({ ok: false, error: 'Suppression impossible.' }, 500);
  }
});
