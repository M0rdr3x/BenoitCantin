import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

const OWNER_EMAIL='kingtyrano@gmail.com';
const MAX_STORAGE_OBJECTS_PER_BUCKET=10_000;

function ownedPath(userId:string,value:unknown){
  const path=String(value||'').trim(),prefix=`${userId}/`;
  if(!path||!path.startsWith(prefix)||path.includes('..')||/[\u0000-\u001f\\]/.test(path))return null;
  return path;
}
async function listOwnedObjects(service:any,bucket:string,userId:string){
  const files:string[]=[],queue=[userId];
  while(queue.length){
    const folder=queue.shift()!;let offset=0;
    while(true){
      const {data,error}=await service.storage.from(bucket).list(folder,{limit:100,offset,sortBy:{column:'name',order:'asc'}});
      if(error)throw new Error(`STORAGE_LIST_FAILED:${bucket}`);
      const rows=data||[];
      for(const item of rows){
        const full=`${folder}/${item.name}`;
        // Les dossiers virtuels n'ont pas d'id/metadata; les objets réels en ont.
        if(item?.id||item?.metadata)files.push(full);else queue.push(full);
        if(files.length>MAX_STORAGE_OBJECTS_PER_BUCKET)throw new Error(`STORAGE_TOO_MANY:${bucket}`);
      }
      if(rows.length<100)break;
      offset+=rows.length;
    }
  }
  return files;
}
async function removePaths(service:any,bucket:string,paths:string[]){
  const unique=[...new Set(paths.map(x=>String(x||'').trim()).filter(Boolean))];
  for(let i=0;i<unique.length;i+=100){
    const {error}=await service.storage.from(bucket).remove(unique.slice(i,i+100));
    if(error)throw new Error(`STORAGE_DELETE_FAILED:${bucket}`);
  }
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

    // Les références DB peuvent être anciennes ou volontairement falsifiées par un client.
    // Jamais une suppression service-role n'agit hors du dossier UUID du compte authentifié.
    const avatarReferenced=ownedPath(user.id,profile?.avatar_path);
    const sourceReferenced=(submissions||[]).map((x:any)=>ownedPath(user.id,x.photo_path)).filter(Boolean) as string[];

    // On balaie aussi récursivement les dossiers privés du compte afin de supprimer les
    // anciens objets orphelins qui ne seraient plus référencés dans les tables applicatives.
    const [avatarObjects,sourceObjects]=await Promise.all([
      listOwnedObjects(service,'sinjira-avatars',user.id),
      listOwnedObjects(service,'sinjira-character-sources',user.id)
    ]);
    await removePaths(service,'sinjira-avatars',[...avatarObjects,...(avatarReferenced?[avatarReferenced]:[])]);
    await removePaths(service,'sinjira-character-sources',[...sourceObjects,...sourceReferenced]);

    const { error } = await service.auth.admin.deleteUser(user.id);
    if (error) throw error;
    return json({ ok: true, removed_storage_objects: avatarObjects.length+sourceObjects.length });
  } catch (error) {
    console.error('[SINJIRA delete account]',error);
    if (error?.message === 'AUTH_REQUIRED') return json({ ok: false, error: 'Connexion requise.' }, 401);
    if (error?.message === 'CONTRIBUTION_REVOKE_FAILED') return json({ok:false,error:'La révocation des contributions n’a pas pu être confirmée. Le compte n’a pas été supprimé.'},502);
    if (String(error?.message||'').startsWith('STORAGE_LIST_FAILED:')) return json({ok:false,error:'Le stockage personnel n’a pas pu être inventorié. Le compte n’a pas été supprimé.'},502);
    if (String(error?.message||'').startsWith('STORAGE_DELETE_FAILED:')) return json({ok:false,error:'Un fichier personnel n’a pas pu être supprimé du stockage. Le compte n’a pas été supprimé.'},502);
    if (String(error?.message||'').startsWith('STORAGE_TOO_MANY:')) return json({ok:false,error:'Le volume de fichiers du compte exige une suppression administrative assistée.'},409);
    return json({ ok: false, error: 'Suppression impossible.' }, 500);
  }
});
