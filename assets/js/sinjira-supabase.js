import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
import { SINJIRA_CONFIG, isSinjiraBackendConfigured } from './sinjira-supabase-config.js';

let client = null;
export function getSupabase() {
  if (!isSinjiraBackendConfigured()) throw new Error('Configuration Supabase requise.');
  if (!client) client = createClient(SINJIRA_CONFIG.supabaseUrl, SINJIRA_CONFIG.supabasePublishableKey, {auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
  return client;
}
export async function getCurrentUser() {if (!isSinjiraBackendConfigured()) return null;const {data,error}=await getSupabase().auth.getUser();return error ? null : (data.user || null)}

// BEGIN SINJIRA_DOCUMENT_WINDOW
// Ouvrir la fenêtre pendant le geste utilisateur, AVANT tout await Supabase.
// Une nouvelle fenêtre créée après une réponse réseau est souvent bloquée
// par les navigateurs, même pour un lecteur autorisé.
export function prepareDocumentWindow(){
  let tab=null;
  try{
    tab=window.open('about:blank','_blank');
    if(!tab)return null;
    // La fenêtre n'a pas le droit de piloter l'onglet de bibliothèque.
    tab.opener=null;
  }catch{
    try{tab?.close()}catch{}
    return null;
  }
  try{
    tab.document.title='SINJIRA™ — document sécurisé';
    tab.document.body.textContent='Vérification des droits de lecture en cours…';
  }catch{} // Certains navigateurs isolent le contexte après opener=null.
  return tab;
}
export function closeDocumentWindow(tab){
  try{tab?.close()}catch{}
}
export function navigateDocumentWindow(tab,raw){
  const url=typeof raw==='string'?raw:'';
  if(!url||url!==url.trim()||/[\\\u0000-\u001f\u007f]/.test(url)){
    closeDocumentWindow(tab);
    return false;
  }
  const local=url.startsWith('/')&&!url.startsWith('//');
  if(!local&&!/^https:\/\/[^/]/i.test(url)){
    closeDocumentWindow(tab);
    return false;
  }
  try{
    if(local&&/%(?:2f|5c|0[0-9a-f]|1[0-9a-f]|7f)/i.test(url)){
      closeDocumentWindow(tab);
      return false;
    }
    const destination=new URL(url,location.origin);
    if(destination.protocol!=='https:'||!destination.hostname
       ||destination.username||destination.password
       ||(local&&destination.origin!==location.origin)){
      closeDocumentWindow(tab);
      return false;
    }
    if(tab&&!tab.closed){
      try{
        tab.location.replace(url);
        return true;
      }catch{
        closeDocumentWindow(tab);
      }
    }
    // Popup bloquée : ouvrir dans l'onglet actuel plutôt que perdre
    // l'accès à un lien signé temporaire après l'authentification.
    location.assign(url);
    return true;
  }catch{
    closeDocumentWindow(tab);
    return false;
  }
}
// END SINJIRA_DOCUMENT_WINDOW

// BEGIN SINJIRA_LIBRARY_ROUTE
// Les champs de navigation issus du registre de projets/romans ne sont
// jamais des autorisations. Le client n'affiche que des routes locales
// non ambiguës : échapper le HTML ne valide pas un attribut href.
export function safeLibraryRoute(value){
  if(typeof value!=='string'||!value||value!==value.trim())return '';
  if(!value.startsWith('/')||value.startsWith('//')||/[\\\u0000-\u001f\u007f]/.test(value))return '';
  if(/%(?:2f|5c|2e|0[0-9a-f]|1[0-9a-f]|7f)/i.test(value))return '';
  if(/%(?![0-9a-f]{2})/i.test(value))return '';
  try{
    const url=new URL(value,location.origin);
    const pathname=value.split(/[?#]/,1)[0];
    if(url.origin!==location.origin||url.username||url.password||url.pathname!==pathname)return '';
    return value;
  }catch{return ''}
}
// END SINJIRA_LIBRARY_ROUTE

export function safeInternalDestination(value,fallback='/compte/index.html'){
  const raw=String(value||'').trim();
  if(!raw.startsWith('/')||raw.startsWith('//')||raw.includes('\\')||/[\u0000-\u001f\u007f]/.test(raw))return fallback;
  try{
    const url=new URL(raw,location.origin);
    if(url.origin!==location.origin||url.username||url.password)return fallback;
    return `${url.pathname}${url.search}${url.hash}`;
  }catch{return fallback}
}

export async function requireUser(redirect='/compte/connexion.html') {
  const user=await getCurrentUser();
  if (!user) {
    const next=encodeURIComponent(safeInternalDestination(location.pathname+location.search+location.hash,'/compte/index.html'));
    location.replace(`${redirect}?next=${next}`);
    throw new Error('Connexion requise');
  }
  if(!/^\/compte\/mfa\.html$/i.test(location.pathname)){
    const next=safeInternalDestination(location.pathname+location.search+location.hash,'/compte/index.html');
    try{
      const {data,error}=await getSupabase().auth.mfa.getAuthenticatorAssuranceLevel();
      if(error)throw error;
      if(data?.nextLevel==='aal2'&&data?.currentLevel!=='aal2'){
        location.replace(`/compte/mfa.html?next=${encodeURIComponent(next)}`);
        await new Promise(()=>{});
      }
    }catch(error){
      console.warn('[SINJIRA MFA gate]',error?.message||error);
      location.replace(`/compte/mfa.html?next=${encodeURIComponent(next)}&state=aal-check`);
      await new Promise(()=>{});
    }
  }
  return user;
}
export function isSinjiraOwner(user){return String(user?.email||'').trim().toLowerCase()==='kingtyrano@gmail.com'}
export async function signOut(){ if(isSinjiraBackendConfigured()) await getSupabase().auth.signOut({scope:'local'}); location.href='/compte/connexion.html'; }
export function escapeHtml(v=''){return String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;')}
export function formatDate(v){if(!v)return '—';return new Intl.DateTimeFormat('fr-CA',{dateStyle:'medium',timeStyle:'short'}).format(new Date(v))}
export function friendlyBackendMessage(message,fallback='Une opération serveur n’a pas pu être terminée.'){
  const raw=String(message||'').trim();if(!raw)return fallback;
  if(/PGRST20[25]|Could not find the (?:table|function)|relation .* does not exist|schema cache/i.test(raw))return 'Le serveur SINJIRA™ doit encore être synchronisé pour cette fonction.';
  if(/GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14/i.test(raw))return 'Un code d’autorisation parentale est obligatoire pour un compte de 12 ou 13 ans.';
  if(/INVALID_OR_EXPIRED_GUARDIAN_CODE/i.test(raw))return 'Le code d’autorisation parentale est invalide, expiré ou déjà utilisé.';
  if(/ADULT_GUARDIAN_REQUIRED/i.test(raw))return 'Le code doit provenir d’un parent ou tuteur possédant un compte adulte.';
  if(/MFA_REQUIRED/i.test(raw))return 'Une authentification renforcée est requise pour cette opération sensible.';
  if(/MFA_STATE_UNAVAILABLE/i.test(raw))return 'L’état de votre authentification renforcée ne peut pas être vérifié pour le moment.';
  if(/SINJIRA_MINIMUM_AGE_12/i.test(raw))return 'Les Comptes SINJIRA™ sont disponibles à partir de 12 ans.';
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
export function setStatus(node,msg,type='info'){
  if(!node)return;
  const raw=String(msg||'');
  const friendly=friendlyBackendMessage(raw,raw||'Une opération n’a pas pu être terminée.');
  if(friendly!==raw&&raw)console.warn('[SINJIRA backend]',raw);
  const isError=type==='error';
  node.setAttribute('role',isError?'alert':'status');
  node.setAttribute('aria-live',isError?'assertive':'polite');
  node.setAttribute('aria-atomic','true');
  node.textContent=friendly;
  node.dataset.statusType=type;
  node.hidden=false;
}
export function roleLabel(v){return ({public:'Public',account:'Compte joueur',player:'Joueur approuvé',tester:'Testeur approuvé',admin:'Administration'})[v]||v||'—'}
export function projectStatusLabel(v){return ({draft:'Brouillon',development:'En développement',testing:'En test',active:'Disponible',archived:'Archivé'})[v]||v||'—'}
export { SINJIRA_CONFIG, isSinjiraBackendConfigured };
if(typeof location!=='undefined'&&/^\/admin\/sinjira(?:\/|$)/i.test(location.pathname)){queueMicrotask(()=>import('./v24-admin-health.js?v=24.4.67').catch(err=>console.warn('[SINJIRA admin health loader]',err)))}