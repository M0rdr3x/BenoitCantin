import {getSupabase,getCurrentUser,isSinjiraOwner} from './sinjira-supabase.js';

const path=location.pathname.replace(/\/+$/,'')||'/';

function ensureCss(){
  if(document.querySelector('link[data-v2433-fixes]'))return;
  const link=document.createElement('link');
  link.rel='stylesheet';
  link.href='/assets/css/v24-3-3-fixes.css?v=24.3.3';
  link.dataset.v2433Fixes='';
  document.head.appendChild(link);
}

function normalizeAdminLinks(){
  document.querySelectorAll('a[href="/admin/sinjira/"],a[href="/Admin/sinjira/"],a[href="/Admin/sinjira/index.html"]').forEach(a=>{
    a.setAttribute('href','/admin/sinjira/index.html');
  });
}

function friendlyServerText(text){
  const t=String(text||'').trim();
  if(!t)return null;
  if(/migration V24.*profil privé|coffre privé.*migration|table privée V24/i.test(t)){
    return 'Le coffre privé attend la synchronisation du serveur SINJIRA™. Les renseignements déjà liés à votre compte restent conservés; cette section deviendra modifiable dès que le serveur sera à jour.';
  }
  if(/migration V24.*Relations|family_relationships|migration.*Relations/i.test(t)){
    return 'Les relations privées attendent la synchronisation du serveur SINJIRA™. Aucune relation n’est publiée pendant cette attente.';
  }
  if(/migration V24.*Marché|market_listings|migration.*Marché/i.test(t)){
    return 'Le module personnel du Marché est encore en préparation côté serveur. Les transactions et paiements restent désactivés.';
  }
  if(/Migration V24 requise|grand livre n’est pas encore installé|token_ledger/i.test(t)){
    return 'Le grand livre des Jetons SINJIRA™ attend la synchronisation du serveur. Aucun achat réel de jetons n’est actif pour le moment.';
  }
  if(/correctif Supabase V24\.?\d*.*Fracture|party_code.*ambiguous|Fracture Online doit être appliqué/i.test(t)){
    return 'Fracture Online attend la synchronisation de son serveur. Vous pouvez consulter les règles et votre compte, mais la création et la jonction de parties restent temporairement indisponibles.';
  }
  if(/correctif Supabase V24\.?\d*.*AbyssTime|synchronisation AbyssTime requise/i.test(t)){
    return 'AbyssTime est reconnu par votre compte. La fiche sociale persistante attend encore la synchronisation du serveur SINJIRA™.';
  }
  return null;
}

function replaceTechnicalMessages(root=document){
  const selectors='[data-private-profile-status],[data-social-status],[data-fracture-status],[data-fracture-access-status],[data-character-network-lock],[data-relation-status],[data-market-account-status],[data-token-ledger],[data-token-balance],.v24-empty,.account-status';
  const nodes=root.querySelectorAll?.(selectors)||[];
  for(const node of nodes){
    const replacement=friendlyServerText(node.textContent);
    if(!replacement)continue;
    if(node.matches('[data-token-balance]')) node.textContent='—';
    else if(node.matches('[data-token-ledger],.v24-empty')) node.innerHTML=`<div class="v2433-server-note"><strong>Synchronisation serveur requise</strong><br>${replacement}</div>`;
    else node.textContent=replacement;
    node.hidden=false;
    node.dataset.statusType='info';
    node.dataset.type='info';
  }
}

async function ownerState(){
  try{
    const user=await getCurrentUser();
    if(!isSinjiraOwner(user))return {user:null,owner:false};
    return {user,owner:true};
  }catch{return {user:null,owner:false}}
}

async function improveOwnerCharacterState(){
  if(!path.startsWith('/compte/'))return;
  const {user,owner}=await ownerState();
  if(!owner)return;
  const identity=document.querySelector('[data-character-identity]');
  const lock=document.querySelector('[data-character-network-lock]');
  if(identity&&/Vérification de votre personnage/i.test(identity.textContent||'')){
    identity.innerHTML='<strong>Mode personnage — AbyssTime</strong><p>Votre personnage officiel est reconnu par le Compte SINJIRA™. Vérification de la fiche sociale persistante en cours.</p>';
  }
  try{
    const s=getSupabase();
    const {data:existing}=await s.from('character_social_profiles').select('character_id,public_name').eq('user_id',user.id).maybeSingle();
    if(existing?.character_id){
      if(identity)identity.innerHTML=`<strong>Mode personnage — ${existing.public_name||'AbyssTime'}</strong><p>Identité fictive active. Les échanges de ce réseau restent du rôle-play et ne modifient pas le canon.</p>`;
      return;
    }
    const {data,error}=await s.rpc('ensure_sinjira_owner_character');
    if(!error&&data?.ok){
      const key='sinjira-v2433-owner-character-reloaded';
      if(!sessionStorage.getItem(key)){
        sessionStorage.setItem(key,'1');
        location.reload();
        return;
      }
    }
  }catch(_){/* le message utilisateur ci-dessous suffit */}
  if(identity)identity.innerHTML='<strong>Mode personnage — AbyssTime</strong><p>Votre personnage est reconnu. La synchronisation de sa fiche sociale côté serveur reste à terminer.</p>';
  if(lock&&!lock.hidden&&/V24|migration|synchronisation/i.test(lock.textContent||'')){
    lock.innerHTML='<div class="v20-character-lock"><h2>AbyssTime reconnu</h2><p>Votre personnage officiel est bien associé au compte. La publication dans le Réseau personnage sera activée dès que la fiche sociale persistante sera synchronisée côté serveur.</p><a class="btn btn-primary" href="mon-personnage.html">Voir AbyssTime</a></div>';
  }
}

async function improveOwnerFractureState(){
  if(!path.includes('/fracture-du-reseau-mere/'))return;
  const {owner}=await ownerState();
  if(!owner)return;
  const access=document.querySelector('[data-fracture-access-status]');
  if(access&&/Vérification|migration|correctif/i.test(access.textContent||'')){
    access.textContent='Accès propriétaire AbyssTime reconnu. Si la création ou la jonction de partie échoue, seule la synchronisation du serveur Fracture reste à terminer.';
    access.classList.add('v2433-server-note');
  }
}

function observe(){
  replaceTechnicalMessages();
  const observer=new MutationObserver(()=>replaceTechnicalMessages());
  observer.observe(document.documentElement,{subtree:true,childList:true,characterData:true});
}

ensureCss();
const start=()=>{
  normalizeAdminLinks();
  observe();
  window.setTimeout(improveOwnerCharacterState,500);
  window.setTimeout(improveOwnerFractureState,800);
};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
