import {getSupabase,setStatus,formatDate} from './sinjira-supabase.js';

const s=getSupabase();
const status=document.querySelector('[data-security-center-status]');
const devices=document.querySelector('[data-security-devices]');
const travelList=document.querySelector('[data-security-travel-list]');
let travelRefreshInProgress=false;
let travelRefreshQueued=false;

function report(message,type='info'){setStatus(status,message,type)}
function augmentLostDeviceActions(){
  if(!devices)return;
  devices.querySelectorAll('[data-device-revoke]').forEach(revokeButton=>{
    const id=String(revokeButton.getAttribute('data-device-revoke')||'');
    if(!id||devices.querySelector(`[data-device-lost="${CSS.escape(id)}"]`))return;
    const button=document.createElement('button');
    button.className='btn btn-secondary';
    button.type='button';
    button.dataset.deviceLost=id;
    button.textContent='Déclarer perdu';
    revokeButton.insertAdjacentElement('afterend',button);
  });
}
function addPasskeyReadiness(){
  const anchor=document.querySelector('[aria-labelledby="mfa-active-title"]');
  if(!anchor||document.querySelector('[data-passkey-readiness]'))return;
  const supported=typeof globalThis.PublicKeyCredential!=='undefined';
  const section=document.createElement('section');
  section.className='security-card security-section-card';
  section.setAttribute('data-passkey-readiness','');
  section.setAttribute('aria-labelledby','passkey-readiness-title');
  section.innerHTML=`<div class="security-card-head"><div><h2 id="passkey-readiness-title">Passkeys</h2><p>Préparation WebAuthn pour le futur domaine définitif de SINJIRA.</p></div><span class="security-state-chip">Préparé</span></div><p><strong>${supported?'Cet appareil prend en charge les passkeys.':'Compatibilité passkey non détectée sur ce navigateur.'}</strong></p><p class="v24-feature-note">État : préparé, non activé. Aucun identifiant WebAuthn n’est créé tant que le RP ID définitif n’est pas <strong>sinjira.com</strong>.</p>`;
  anchor.insertAdjacentElement('afterend',section);
}

function safeTravelNode(tag,text,className=''){
  const node=document.createElement(tag);
  if(className)node.className=className;
  node.textContent=text;
  return node;
}
function travelItem(row,nowMs){
  const article=document.createElement('article');
  article.className='security-item';
  article.dataset.travelSafeItem='';

  const head=document.createElement('div');
  head.className='security-item-head';
  const titleBox=document.createElement('div');
  const destinations=Array.isArray(row.destinations)?row.destinations.map(x=>String(x).trim().toUpperCase()).filter(Boolean):[];
  titleBox.appendChild(safeTravelNode('h3',destinations.join(' → ')||'Destination prévue'));

  const startsMs=new Date(row.starts_at).getTime();
  const activeNow=Number.isFinite(startsMs)&&startsMs<=nowMs;
  const badge=safeTravelNode('span',activeNow?'Actif maintenant':'À venir','security-pill good');
  titleBox.appendChild(badge);
  head.appendChild(titleBox);
  head.appendChild(safeTravelNode('small',`${formatDate(row.starts_at)} → ${formatDate(row.ends_at)}`));
  article.appendChild(head);

  const actions=document.createElement('div');
  actions.className='security-actions';
  const cancel=document.createElement('button');
  cancel.className='btn btn-secondary';
  cancel.type='button';
  cancel.dataset.travelCancel=String(row.id||'');
  cancel.textContent='Annuler ce voyage';
  if(!cancel.dataset.travelCancel)cancel.disabled=true;
  actions.appendChild(cancel);
  article.appendChild(actions);
  return article;
}
function renderVisibleTravel(rows){
  if(!travelList)return;
  const nowMs=Date.now();
  const visible=(Array.isArray(rows)?rows:[]).filter(row=>{
    const endsMs=new Date(row?.ends_at).getTime();
    return row?.status==='active'&&Number.isFinite(endsMs)&&endsMs>=nowMs;
  });
  travelList.replaceChildren();
  if(!visible.length){
    const empty=safeTravelNode('p','Aucun Mode Voyage actif ou futur.','security-empty');
    empty.dataset.travelSafeItem='';
    travelList.appendChild(empty);
    return;
  }
  visible.forEach(row=>travelList.appendChild(travelItem(row,nowMs)));
}
async function refreshVisibleTravel(){
  if(!travelList)return;
  if(travelRefreshInProgress){travelRefreshQueued=true;travelList.hidden=true;return}
  travelRefreshInProgress=true;
  travelList.hidden=true;
  try{
    const nowIso=new Date().toISOString();
    const {data,error}=await s
      .from('security_travel_plans')
      .select('id,status,starts_at,ends_at,destinations')
      .eq('status','active')
      .gte('ends_at',nowIso)
      .order('starts_at',{ascending:true})
      .limit(20);
    if(error)throw error;
    renderVisibleTravel(data||[]);
  }catch(error){
    console.warn('[SINJIRA travel visibility]',error);
    travelList.replaceChildren();
    const unavailable=safeTravelNode('p','Impossible d’afficher les Modes Voyage actifs pour le moment.','security-empty');
    unavailable.dataset.travelSafeItem='';
    travelList.appendChild(unavailable);
  }finally{
    travelList.hidden=false;
    travelRefreshInProgress=false;
    if(travelRefreshQueued){
      travelRefreshQueued=false;
      queueMicrotask(refreshVisibleTravel);
    }
  }
}
function travelViewIsSafe(){
  if(!travelList)return true;
  return [...travelList.children].every(node=>node.hasAttribute('data-travel-safe-item'));
}
async function cancelTravel(button){
  const id=String(button?.dataset?.travelCancel||'');
  if(!id)return;
  if(!globalThis.confirm('Annuler ce Mode Voyage ? Après confirmation, il ne sera plus utilisé pour réduire les faux positifs géographiques.'))return;
  button.disabled=true;
  try{
    const {error}=await s.rpc('security_cancel_travel_plan',{p_plan_id:id});
    if(error)throw error;
    report('Mode Voyage annulé. Il n’est plus utilisé pour le signal géographique.','success');
    await refreshVisibleTravel();
  }catch(error){
    console.warn('[SINJIRA travel cancel]',error);
    const message=String(error?.message||error||'');
    report(message.includes('AAL2_REQUIRED')
      ? 'Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée.'
      : 'Impossible d’annuler ce Mode Voyage pour le moment. Aucune modification n’a été effectuée.','error');
    button.disabled=false;
  }
}

const observer=new MutationObserver(()=>augmentLostDeviceActions());
if(devices)observer.observe(devices,{childList:true,subtree:true});
augmentLostDeviceActions();
addPasskeyReadiness();

const travelObserver=new MutationObserver(()=>{
  if(!travelViewIsSafe()){
    travelList.hidden=true;
    void refreshVisibleTravel();
  }
});
if(travelList){
  travelList.hidden=true;
  travelObserver.observe(travelList,{childList:true});
  void refreshVisibleTravel();
}

document.addEventListener('click',event=>{
  const button=event.target.closest?.('[data-travel-cancel]');
  if(!button)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  void cancelTravel(button);
},true);

document.addEventListener('click',async event=>{
  const button=event.target.closest?.('[data-device-lost]');
  if(!button)return;
  const id=String(button.dataset.deviceLost||'');
  if(!id)return;
  if(!globalThis.confirm('Déclarer cet appareil perdu ? SINJIRA retirera sa confiance, désactivera ses notifications de sécurité et fermera les autres sessions du compte.'))return;
  button.disabled=true;
  try{
    const {error}=await s.rpc('security_report_lost_device',{p_device_id:id});
    if(error)throw error;
    await s.auth.signOut({scope:'others'});
    report('Appareil déclaré perdu. Sa confiance et ses notifications ont été révoquées; les autres sessions ont été fermées.','success');
    setTimeout(()=>location.reload(),900);
  }catch(error){
    console.warn('[SINJIRA lost device]',error);
    report(error?.message==='AAL2_REQUIRED'?'Vérification MFA requise avant de déclarer cet appareil perdu.':'Impossible de terminer la protection de cet appareil pour le moment.','error');
    button.disabled=false;
  }
});
