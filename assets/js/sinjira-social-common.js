import {getSupabase,requireUser,escapeHtml,formatDate,SINJIRA_CONFIG} from './sinjira-supabase.js';

export const RULES_VERSION='sinjira-community-rules-v2-2026-08-19';
export const SOCIAL_RUNTIME_VERSION='24.4.82';
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

export async function reportContent({network,target_type,target_id,reason='other',details=null,block=false}){
  await requireUser('/compte/connexion.html');
  const allowed=new Set([
    'minor_safety','grooming','sexual_exploitation','human_trafficking','paid_sexual_content','drugs_or_illicit_sales','off_platform_minor_contact',
    'harassment','sexual_content','pressure','scam','hate','threats','impersonation','spam','other'
  ]);
  const raw=String(reason||'other').trim();
  const normalized=allowed.has(raw)?raw:'other';
  const safeDetails=details??(normalized==='other'&&raw&&raw.toLowerCase()!=='other'?raw:null);
  const {data,error}=await getSupabase().rpc('social_report_content',{
    p_network:network,
    p_target_type:target_type,
    p_target_id:target_id,
    p_reason:normalized,
    p_details:safeDetails?String(safeDetails).slice(0,1200):null,
    p_block:!!block
  });
  if(error)throw error;
  return data||{ok:true};
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

  if(message.includes('sinjira_content_policy_minor_off_platform_contact'))return 'Pour protéger les mineurs, les coordonnées et déplacements vers une autre plateforme sont bloqués dans la messagerie jeunesse.';
  if(message.includes('sinjira_content_policy_minor_sexual_solicitation'))return 'Ce message est bloqué par la protection renforcée contre la sollicitation sexuelle des mineurs.';
  if(message.includes('sinjira_content_policy_minor_financial_solicitation'))return 'Ce message est bloqué par la protection renforcée contre les sollicitations financières visant les mineurs.';
  if(message.includes('sinjira_content_policy_paid_sexual_content'))return 'La promotion ou la vente de contenu sexuel payant est interdite sur SINJIRA™.';
  if(message.includes('sinjira_content_policy_sexual_exploitation'))return 'La prostitution, le proxénétisme et la vente de services sexuels sont interdits sur SINJIRA™.';
  if(message.includes('sinjira_content_policy_human_trafficking'))return 'La traite, la vente ou l’achat de personnes sont strictement interdits sur SINJIRA™.';
  if(message.includes('sinjira_content_policy_illicit_drug_sales'))return 'La vente ou la sollicitation commerciale de drogues est interdite sur SINJIRA™.';
  if(message.includes('social_report_already_open'))return 'Un signalement ouvert existe déjà pour ce contenu.';
  if(message.includes('social_report_rate_limit'))return 'Trop de signalements ont été envoyés récemment. Réessayez plus tard.';
  if(message.includes('social_report_target_unavailable'))return 'Ce contenu n’est plus disponible depuis votre compte.';
  if(code==='42501'||message.includes('row-level security')||message.includes('permission denied')){
    return 'Cette action n’est pas autorisée avec l’état actuel de votre compte. Rechargez la page; si le problème persiste, consultez Sécurité ou utilisez la page Contact.';
  }
  if(code==='23505'||message.includes('duplicate key')||message.includes('already exists'))return 'Cette action a déjà été enregistrée.';
  if(code==='23503'||message.includes('foreign key'))return 'L’élément lié n’est plus disponible. Rechargez la page avant de réessayer.';
  if(code==='PGRST301'||code==='PGRST302'||message.includes('jwt')||message.includes('not authenticated'))return 'Votre session doit être renouvelée. Reconnectez-vous au Compte SINJIRA™.';
  if(message.includes('failed to fetch')||message.includes('network')||message.includes('offline')||message.includes('load failed'))return 'Connexion au service interrompue. Vérifiez votre connexion et réessayez.';
  if(message.includes('timeout')||message.includes('timed out'))return 'Le service met trop de temps à répondre. Réessayez dans quelques instants.';
  return fallback;
}

export function socialErrorStatus(node,error,fallback){
  console.error('[SINJIRA social]',error);
  socialStatus(node,socialErrorMessage(error,fallback),'error');
}
