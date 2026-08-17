import {getSupabase,requireUser,escapeHtml,formatDate,SINJIRA_CONFIG} from './sinjira-supabase.js';

export const RULES_VERSION='sinjira-community-rules-v1-2026-08-12';
export const SOCIAL_RUNTIME_VERSION='24.4.42';
export {getSupabase,requireUser,escapeHtml,formatDate};

export function avatarUrl(path){
  if(!path)return '/assets/media/sinjira-emblem.webp';
  const {data}=getSupabase().storage.from(SINJIRA_CONFIG.avatarBucket||'sinjira-avatars').getPublicUrl(path);
  return data?.publicUrl||'/assets/media/sinjira-emblem.webp';
}

export async function rulesAccepted(user){
  const {data,error}=await getSupabase()
    .from('community_rule_acceptances')
    .select('rules_version')
    .eq('user_id',user.id)
    .eq('rules_version',RULES_VERSION)
    .maybeSingle();
  if(error)throw error;
  return !!data;
}

export async function requireCommunityUser(next=location.pathname+location.search){
  const user=await requireUser('/compte/connexion.html');
  if(!await rulesAccepted(user)){
    location.href=`/compte/regles-communaute.html?next=${encodeURIComponent(next)}`;
    throw new Error('RULES_REQUIRED');
  }
  return user;
}

export async function realProfile(userId){
  const {data,error}=await getSupabase().from('social_profiles').select('*').eq('user_id',userId).maybeSingle();
  if(error)throw error;
  return data||null;
}

export async function characterProfileByUser(userId){
  const {data,error}=await getSupabase().from('character_social_profiles').select('*').eq('user_id',userId).maybeSingle();
  if(error)throw error;
  return data||null;
}

export async function reportContent({network,target_type,target_id,reason,snapshot={}}){
  const user=await requireCommunityUser();
  const {error}=await getSupabase().from('social_reports').insert({
    reporter_user_id:user.id,
    network,
    target_type,
    target_id,
    reason:String(reason||'Autre').slice(0,120),
    snapshot
  });
  if(error)throw error;
  return true;
}

export function socialStatus(node,msg,type='info'){
  if(!node)return;
  node.textContent=msg;
  node.dataset.statusType=type;
  node.hidden=false;
}

export function socialErrorMessage(error,fallback='Action impossible pour le moment. Réessayez dans quelques instants.'){
  const code=String(error?.code||'').toUpperCase();
  const message=String(error?.message||error||'').toLowerCase();

  if(code==='42501'||message.includes('row-level security')||message.includes('permission denied')){
    return 'Cette action n’est pas autorisée avec l’état actuel de votre compte. Rechargez la page; si le problème persiste, consultez Sécurité ou utilisez la page Contact.';
  }
  if(code==='23505'||message.includes('duplicate key')||message.includes('already exists')){
    return 'Cette action a déjà été enregistrée.';
  }
  if(code==='23503'||message.includes('foreign key')){
    return 'L’élément lié n’est plus disponible. Rechargez la page avant de réessayer.';
  }
  if(code==='PGRST301'||code==='PGRST302'||message.includes('jwt')||message.includes('not authenticated')){
    return 'Votre session doit être renouvelée. Reconnectez-vous au Compte SINJIRA™.';
  }
  if(message.includes('failed to fetch')||message.includes('network')||message.includes('offline')||message.includes('load failed')){
    return 'Connexion au service interrompue. Vérifiez votre connexion et réessayez.';
  }
  if(message.includes('timeout')||message.includes('timed out')){
    return 'Le service met trop de temps à répondre. Réessayez dans quelques instants.';
  }
  return fallback;
}

export function socialErrorStatus(node,error,fallback){
  console.error('[SINJIRA social]',error);
  socialStatus(node,socialErrorMessage(error,fallback),'error');
}
