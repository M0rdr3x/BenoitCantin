import {getSupabase,requireUser,escapeHtml,formatDate,SINJIRA_CONFIG} from './sinjira-supabase.js';
export const RULES_VERSION='sinjira-community-rules-v1-2026-08-12';
export {getSupabase,requireUser,escapeHtml,formatDate};
export function avatarUrl(path){if(!path)return '/assets/media/sinjira-emblem.webp';const {data}=getSupabase().storage.from(SINJIRA_CONFIG.avatarBucket||'sinjira-avatars').getPublicUrl(path);return data?.publicUrl||'/assets/media/sinjira-emblem.webp'}
export async function rulesAccepted(user){const {data}=await getSupabase().from('community_rule_acceptances').select('rules_version').eq('user_id',user.id).eq('rules_version',RULES_VERSION).maybeSingle();return !!data}
export async function requireCommunityUser(next=location.pathname+location.search){const user=await requireUser('/compte/connexion.html');if(!await rulesAccepted(user)){location.href=`/compte/regles-communaute.html?next=${encodeURIComponent(next)}`;throw new Error('RULES_REQUIRED')}return user}
export async function realProfile(userId){const {data}=await getSupabase().from('social_profiles').select('*').eq('user_id',userId).maybeSingle();return data||null}
export async function characterProfileByUser(userId){const {data}=await getSupabase().from('character_social_profiles').select('*').eq('user_id',userId).maybeSingle();return data||null}
export async function reportContent({network,target_type,target_id,reason,snapshot={}}){const user=await requireCommunityUser();const {error}=await getSupabase().from('social_reports').insert({reporter_user_id:user.id,network,target_type,target_id,reason:String(reason||'Autre').slice(0,120),snapshot});if(error)throw error;return true}
export function socialStatus(node,msg,type='info'){if(!node)return;node.textContent=msg;node.dataset.statusType=type;node.hidden=false}
