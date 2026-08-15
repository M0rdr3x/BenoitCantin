import {getSupabase,getCurrentUser,isSinjiraOwner} from './sinjira-supabase.js';

const path=location.pathname.replace(/\/+$/,'')||'/';

function ensureCss(){
  if(document.querySelector('link[data-v2432-fixes]'))return;
  const link=document.createElement('link');
  link.rel='stylesheet';
  link.href='/assets/css/v24-3-2-fixes.css?v=24.3.2';
  link.dataset.v2432Fixes='';
  document.head.appendChild(link);
}

function repairAdminRouting(){
  // GitHub Pages peut remettre la page 404 sur l'URL de dossier. Dans ce cas,
  // on vise explicitement le fichier index au lieu de reboucler vers le dossier.
  if((path==='/admin/sinjira'||path==='/admin/sinjira/index.html')&&/Page introuvable/i.test(document.title||'')){
    location.replace('/admin/sinjira/index.html'+location.search+location.hash);
    return;
  }
  document.querySelectorAll('a[href="/admin/sinjira/"]').forEach(a=>a.setAttribute('href','/admin/sinjira/index.html'));
}

function replaceLegacyServerMessages(root=document){
  const nodes=root.querySelectorAll?.('[data-private-profile-status],[data-social-status],[data-fracture-status],[data-fracture-access-status],[data-character-network-lock]')||[];
  for(const node of nodes){
    const text=(node.textContent||'').trim();
    if(/migration V24 du profil privé doit être appliquée/i.test(text)){
      node.textContent='Mise à niveau serveur SINJIRA™ requise pour le coffre privé. Les migrations V24 → V24.1 → V24.3.1 sont prêtes dans GitHub, mais doivent encore être appliquées à Supabase.';
      node.hidden=false;
      node.dataset.statusType='error';
    }
    if(/correctif Supabase V24\.1 de Fracture Online doit être appliqué/i.test(text)){
      node.textContent='Mise à niveau serveur Fracture requise. Le correctif V24.3.1 est prêt dans GitHub; Supabase doit recevoir les migrations V24, V24.1 et V24.3.1 avant la création ou la jonction de parties.';
      node.hidden=false;
      node.dataset.statusType='error';
      node.dataset.type='error';
    }
  }
}

async function tryOwnerCharacterRepair(){
  if(!path.startsWith('/compte/reseau-personnage'))return;
  try{
    const user=await getCurrentUser();
    if(!isSinjiraOwner(user))return;
    const s=getSupabase();
    const {data:existing}=await s.from('character_social_profiles').select('character_id').eq('user_id',user.id).maybeSingle();
    if(existing?.character_id)return;
    const {data,error}=await s.rpc('ensure_sinjira_owner_character');
    if(error||!data?.ok)return;
    const key='sinjira-v2432-owner-character-reloaded';
    if(!sessionStorage.getItem(key)){
      sessionStorage.setItem(key,'1');
      location.reload();
    }
  }catch(_){
    // Si la RPC n'existe pas encore, le verrou explicite de la page reste affiché.
  }
}

function startObservers(){
  replaceLegacyServerMessages();
  const observer=new MutationObserver(()=>replaceLegacyServerMessages());
  observer.observe(document.documentElement,{subtree:true,childList:true,characterData:true});
}

ensureCss();
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',()=>{
    repairAdminRouting();
    startObservers();
    window.setTimeout(tryOwnerCharacterRepair,700);
  },{once:true});
}else{
  repairAdminRouting();
  startObservers();
  window.setTimeout(tryOwnerCharacterRepair,700);
}
