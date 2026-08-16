import {getSupabase,getCurrentUser,isSinjiraOwner} from './sinjira-supabase.js';

const path=location.pathname.replace(/\/+$/,'')||'/';

function ensureCss(){
  if(document.querySelector('link[data-v2432-fixes]'))return;
  const link=document.createElement('link');
  link.rel='stylesheet';
  link.href='/assets/css/v24-3-2-fixes.css?v=24.4.11';
  link.dataset.v2432Fixes='';
  document.head.appendChild(link);
}

function repairAdminRouting(){
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
    if(/migration V24 du profil privé doit être appliquée|migrations V24.*V24\.3\.1/i.test(text)){
      node.textContent='Supabase production n’est pas encore synchronisé avec SINJIRA™ V24.4.11. Ouvrez Administration → État du système après avoir appliqué le workflow de production.';
      node.hidden=false;
      node.dataset.statusType='error';
    }
    if(/correctif Supabase V24\.1 de Fracture Online doit être appliqué|correctif V24\.3\.1 est prêt/i.test(text)){
      node.textContent='Fracture Online attend la synchronisation Supabase production. Le moteur V24.4.6 est déjà dans GitHub; le workflow Supabase doit être lancé manuellement avec apply=true.';
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
    const key='sinjira-v24411-owner-character-reloaded';
    if(!sessionStorage.getItem(key)){
      sessionStorage.setItem(key,'1');
      location.reload();
    }
  }catch(_){
    // Si la RPC n'existe pas encore en production, la page conserve son état explicite.
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
