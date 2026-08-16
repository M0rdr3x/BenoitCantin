import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
import { SINJIRA_CONFIG, isSinjiraBackendConfigured } from './sinjira-supabase-config.js';

let client = null;
export function getSupabase() {
  if (!isSinjiraBackendConfigured()) throw new Error('Configuration Supabase requise.');
  if (!client) client = createClient(SINJIRA_CONFIG.supabaseUrl, SINJIRA_CONFIG.supabasePublishableKey, {auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
  return client;
}
export async function getCurrentUser() {if (!isSinjiraBackendConfigured()) return null;const {data,error}=await getSupabase().auth.getUser();return error ? null : (data.user || null)}
export async function requireUser(redirect='/compte/connexion.html') {const user=await getCurrentUser();if (!user) {const next=encodeURIComponent(location.pathname+location.search+location.hash);location.href=`${redirect}?next=${next}`;throw new Error('Connexion requise')}return user}
export function isSinjiraOwner(user){return String(user?.email||'').trim().toLowerCase()==='kingtyrano@gmail.com'}
export async function signOut(){ if(isSinjiraBackendConfigured()) await getSupabase().auth.signOut(); location.href='/compte/connexion.html'; }
export function escapeHtml(v=''){return String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;')}
export function formatDate(v){if(!v)return '—';return new Intl.DateTimeFormat('fr-CA',{dateStyle:'medium',timeStyle:'short'}).format(new Date(v))}
export function friendlyBackendMessage(message,fallback='Une opération serveur n’a pas pu être terminée.'){
  const raw=String(message||'').trim();if(!raw)return fallback;
  if(/PGRST20[25]|Could not find the (?:table|function)|relation .* does not exist|schema cache/i.test(raw))return 'Le serveur SINJIRA™ doit encore être synchronisé pour cette fonction.';
  if(/JWT|token.*expired|session.*expired|invalid claim/i.test(raw))return 'Votre session a expiré. Reconnectez-vous puis réessayez.';
  if(/Failed to fetch|NetworkError|FunctionsFetchError|Load failed/i.test(raw))return 'Communication avec le serveur SINJIRA™ impossible pour le moment.';
  if(/row-level security|permission denied|42501|not authorized|forbidden/i.test(raw))return 'Votre compte n’a pas l’autorisation nécessaire pour cette opération.';
  if(/FRACTURE_(?:ACCESS|ENTITLEMENT)_REQUIRED/i.test(raw))return 'Un droit d’accès Fracture du Réseau-Mère est requis pour ce compte.';
  if(/WAITING_FOR_PLAYERS/i.test(raw))return 'La partie attend encore les autres joueurs humains.';
  if(/GAME_ALREADY_STARTED/i.test(raw))return 'Cette partie a déjà commencé.';
  if(/PARTY_FULL/i.test(raw))return 'Tous les sièges humains de cette partie sont occupés.';
  if(/PARTY_NOT_FOUND/i.test(raw))return 'Cette partie Fracture est introuvable.';
  if(/SEAT_(?:TAKEN|ALREADY_TAKEN)/i.test(raw))return 'Ce siège est déjà occupé.';
  if(/INVALID_SEAT/i.test(raw))return 'Ce numéro de siège n’est pas valide pour cette partie.';
  if(/SOLO_PARTY_CANNOT_BE_JOINED/i.test(raw))return 'Une partie Solo ne peut pas être rejointe par un deuxième compte.';
  if(/INVALID_PLAYER_COUNT/i.test(raw))return 'Le nombre de joueurs humains doit être compris entre 1 et 20.';
  if(/NOT_A_MEMBER/i.test(raw))return 'Votre compte ne fait pas partie de cette partie.';
  if(/NOT_YOUR_TURN/i.test(raw))return 'Ce n’est pas encore votre tour.';
  if(/WRONG_PHASE/i.test(raw))return 'Cette action n’est pas disponible à cette étape de la ronde.';
  if(/CHOOSE_EXACTLY_TWO/i.test(raw))return 'Choisissez exactement deux cartes.';
  if(/INVALID_CARDS|CARD_NOT_AVAILABLE/i.test(raw))return 'Une des cartes choisies n’est plus disponible. Rechargez l’état de la partie.';
  if(/INVALID_REPORT/i.test(raw))return 'Le rapport doit être Résistance, Réseau-Mère ou Équilibré.';
  if(/INVALID_SUSPECT/i.test(raw))return 'Choisissez un autre siège valide comme soupçon.';
  if(/INVALID_PROOF/i.test(raw))return 'Cette carte ne peut pas être utilisée comme Preuve.';
  if(/PROOF_ALREADY_USED/i.test(raw))return 'Votre Preuve a déjà été utilisée dans cette partie.';
  if(/INVALID_ACCUSATION_COUNT/i.test(raw))return 'Le nombre d’accusations finales ne correspond pas au nombre d’agents à identifier.';
  if(/ACCUSATIONS_MUST_BE_DISTINCT/i.test(raw))return 'Chaque siège accusé doit être différent.';
  if(/INVALID_ACCUSED_SEAT/i.test(raw))return 'Une accusation finale vise un siège invalide ou votre propre siège.';
  if(/ALREADY_SUBMITTED/i.test(raw))return 'Cette décision a déjà été enregistrée.';
  if(/OWNER_ONLY/i.test(raw))return 'Seul le créateur de la partie peut effectuer cette action.';
  if(/AUTH_REQUIRED/i.test(raw))return 'Connexion requise pour cette opération.';
  if(/duplicate key|23505/i.test(raw))return 'Cette information existe déjà dans votre compte.';
  if(/foreign key|23503/i.test(raw))return 'Cette opération dépend d’un élément qui n’est plus disponible.';
  if(/null value|23502|check constraint|23514|syntax error|SQLSTATE|column .* does not exist/i.test(raw))return 'Le serveur a refusé cette opération. Le diagnostic administrateur permet d’identifier le composant à synchroniser.';
  return raw.length>240?fallback:raw;
}
export function setStatus(node,msg,type='info'){if(!node)return;const raw=String(msg||'');const friendly=friendlyBackendMessage(raw,raw||'Une opération n’a pas pu être terminée.');if(friendly!==raw&&raw)console.warn('[SINJIRA backend]',raw);node.textContent=friendly;node.dataset.statusType=type;node.hidden=false}
export function roleLabel(v){return ({public:'Public',account:'Compte joueur',player:'Joueur approuvé',tester:'Testeur approuvé',admin:'Administration'})[v]||v||'—'}
export function projectStatusLabel(v){return ({draft:'Brouillon',development:'En développement',testing:'En test',active:'Disponible',archived:'Archivé'})[v]||v||'—'}
export { SINJIRA_CONFIG, isSinjiraBackendConfigured };
if(typeof location!=='undefined'&&/^\/admin\/sinjira(?:\/|$)/i.test(location.pathname)){queueMicrotask(()=>import('./v24-admin-health.js?v=24.4.6').catch(err=>console.warn('[SINJIRA admin health loader]',err)))}
