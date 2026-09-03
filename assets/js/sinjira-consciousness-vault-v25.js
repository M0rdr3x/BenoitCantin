import { getSupabase, requireUser, escapeHtml, formatDate, setStatus } from './sinjira-supabase.js';

const DEVICE_KEY_STORAGE='sinjira.security.device_key.v1';
const VAULT_TTL_SECONDS=300;
const MAX_CONTENT_BYTES=1024*1024;
const HIDDEN_LOCK_DELAY_MS=60_000;

let vaultSessionId=null;
let vaultExpiresAt=0;
let entries=[];
let countdownTimer=null;
let expiryTimer=null;
let hiddenLockTimer=null;
let busy=false;

const q=(selector)=>document.querySelector(selector);

function randomDeviceKey(){
  if(globalThis.crypto?.randomUUID)return globalThis.crypto.randomUUID();
  const bytes=new Uint8Array(24);
  globalThis.crypto?.getRandomValues?.(bytes);
  return `sinjira-${Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')}-${Date.now().toString(36)}`;
}

function deviceKey(){
  try{
    let value=localStorage.getItem(DEVICE_KEY_STORAGE);
    if(!value){value=randomDeviceKey();localStorage.setItem(DEVICE_KEY_STORAGE,value)}
    return value;
  }catch{
    try{
      let value=sessionStorage.getItem(DEVICE_KEY_STORAGE);
      if(!value){value=randomDeviceKey();sessionStorage.setItem(DEVICE_KEY_STORAGE,value)}
      return value;
    }catch{return randomDeviceKey()}
  }
}

function deviceMetadata(){
  const ua=navigator.userAgent||'';
  const platform=String(navigator.userAgentData?.platform||navigator.platform||'').slice(0,120);
  let type='browser';
  if(/iPad|Tablet/i.test(ua))type='tablet';
  else if(/iPhone|iPod/i.test(ua))type='ios';
  else if(/Android/i.test(ua))type='android';
  const browser=/Firefox/i.test(ua)?'Firefox':/Edg\//i.test(ua)?'Edge':/Chrome|CriOS/i.test(ua)?'Chrome':/Safari/i.test(ua)?'Safari':'Navigateur';
  return {
    device_key:deviceKey(),
    display_name:`${browser}${platform?` — ${platform}`:''}`.slice(0,120),
    device_type:type,
    platform
  };
}

function textBytes(value){return new TextEncoder().encode(String(value||'')).byteLength}

function status(message,type='info'){
  setStatus(q('[data-vault-status]'),message,type);
}

function setBusy(value){
  busy=Boolean(value);
  document.querySelectorAll('[data-vault-action]').forEach(node=>{node.disabled=busy});
}

async function errorPayload(error,data){
  if(data&&typeof data==='object')return data;
  const response=error?.context;
  if(response&&typeof response.clone==='function'){
    try{return await response.clone().json()}catch{}
  }
  return null;
}

async function invokeVault(body){
  const {data,error}=await getSupabase().functions.invoke('conscience-vault',{body});
  if(error){
    const payload=await errorPayload(error,data);
    const wrapped=new Error(String(payload?.error||error.message||'Opération du coffre refusée.'));
    wrapped.code=String(payload?.code||'VAULT_OPERATION_REFUSED');
    wrapped.security=payload?.security||null;
    throw wrapped;
  }
  if(!data?.ok){
    const wrapped=new Error(String(data?.error||'Opération du coffre refusée.'));
    wrapped.code=String(data?.code||'VAULT_OPERATION_REFUSED');
    wrapped.security=data?.security||null;
    throw wrapped;
  }
  return data;
}

function resetChallenge(){
  const box=q('[data-vault-challenge]');
  if(box)box.hidden=true;
  const code=q('[data-vault-challenge-code]');
  if(code)code.textContent='—';
}

function showChallenge(error){
  const box=q('[data-vault-challenge]');
  if(!box)return;
  const code=q('[data-vault-challenge-code]');
  const retry=q('[data-vault-retry]');
  const displayCode=String(error?.security?.display_code||'').trim();
  if(code){
    code.textContent=displayCode||'—';
    code.closest('[data-vault-code-row]')?.toggleAttribute('hidden',!displayCode);
  }
  if(retry)retry.disabled=false;
  box.hidden=false;
}

function friendlyVaultError(error){
  const code=String(error?.code||'');
  if(code==='MFA_SETUP_REQUIRED')return 'Configurez d’abord l’authentification renforcée dans Ma sécurité. Le Registre personnel ne peut jamais être ouvert avec un simple mot de passe.';
  if(code==='MFA_REQUIRED')return 'Une vérification MFA récente est requise avant d’ouvrir le Registre personnel.';
  if(code==='SECURITY_CHALLENGE_REQUIRED')return 'Cet appareil doit être confirmé depuis un autre appareil déjà fiable avant l’ouverture du coffre.';
  if(code==='SECURITY_BLOCKED')return 'La protection du compte bloque temporairement l’accès au coffre. Consultez Ma sécurité avant de réessayer.';
  if(code==='VAULT_SESSION_REQUIRED'||code==='VAULT_SESSION_INVALID')return 'La session privée du Registre a expiré. Ouvrez de nouveau le coffre.';
  if(code==='REQUEST_TOO_LARGE'||code==='VAULT_ENTRY_CONTENT_INVALID')return 'Cette entrée est trop volumineuse. Le contenu d’une entrée est limité à 1 Mio.';
  if(code==='AUTH_REQUIRED')return 'Reconnectez-vous avant d’ouvrir le Registre personnel.';
  if(code==='SECURITY_DECISION_INVALID'||code==='MFA_STATE_UNAVAILABLE')return 'La protection du Registre ne peut pas être vérifiée pour le moment. Aucun accès n’a été accordé.';
  return String(error?.message||'Opération du coffre refusée.');
}

function clearTimers(){
  if(countdownTimer)clearInterval(countdownTimer);
  if(expiryTimer)clearTimeout(expiryTimer);
  if(hiddenLockTimer)clearTimeout(hiddenLockTimer);
  countdownTimer=null;
  expiryTimer=null;
  hiddenLockTimer=null;
}

function clearSensitiveDom(){
  entries=[];
  const list=q('[data-vault-entries]');
  if(list)list.innerHTML='<div class="conscience-empty">Le contenu privé est masqué tant que le coffre est verrouillé.</div>';
  const form=q('[data-vault-entry-form]');
  if(form)form.reset();
  const id=q('[data-vault-entry-id]');
  if(id)id.value='';
  const title=q('[data-vault-form-title]');
  if(title)title.textContent='Nouvelle entrée privée';
  const submit=q('[data-vault-submit]');
  if(submit)submit.textContent='Enregistrer dans mon coffre';
  const cancel=q('[data-vault-edit-cancel]');
  if(cancel)cancel.hidden=true;
}

function localLock(message='Registre verrouillé.',announce=true){
  vaultSessionId=null;
  vaultExpiresAt=0;
  clearTimers();
  clearSensitiveDom();
  resetChallenge();
  const locked=q('[data-vault-locked]');
  const workspace=q('[data-vault-workspace]');
  if(locked)locked.hidden=false;
  if(workspace)workspace.hidden=true;
  const countdown=q('[data-vault-countdown]');
  if(countdown)countdown.textContent='Verrouillé';
  if(announce)status(message,'info');
}

function updateCountdown(){
  const node=q('[data-vault-countdown]');
  if(!node||!vaultSessionId)return;
  const remaining=Math.max(0,Math.ceil((vaultExpiresAt-Date.now())/1000));
  const minutes=Math.floor(remaining/60);
  const seconds=String(remaining%60).padStart(2,'0');
  node.textContent=`Verrouillage dans ${minutes}:${seconds}`;
}

function armVaultSession(sessionId,expiresInSeconds){
  vaultSessionId=sessionId;
  vaultExpiresAt=Date.now()+Math.max(1,Number(expiresInSeconds)||VAULT_TTL_SECONDS)*1000;
  clearTimers();
  updateCountdown();
  countdownTimer=setInterval(updateCountdown,1000);
  expiryTimer=setTimeout(()=>localLock('La session privée a expiré. Le contenu a été masqué.',true),Math.max(1,vaultExpiresAt-Date.now()));
}

function requireVaultSession(){
  if(!vaultSessionId||Date.now()>=vaultExpiresAt){
    localLock('La session privée a expiré. Ouvrez de nouveau le coffre.',true);
    const error=new Error('Session de coffre invalide.');
    error.code='VAULT_SESSION_INVALID';
    throw error;
  }
  return vaultSessionId;
}

function entryTypeLabel(value){
  const labels={reflection:'Réflexion privée',memory:'Souvenir privé',note:'Note personnelle',value:'Valeur personnelle',decision:'Décision personnelle',other:'Autre'};
  return labels[value]||String(value||'Entrée privée');
}

function renderEntries(){
  const list=q('[data-vault-entries]');
  const count=q('[data-vault-entry-count]');
  if(count)count.textContent=String(entries.length);
  if(!list)return;
  if(!entries.length){
    list.innerHTML='<div class="conscience-empty"><strong>Votre coffre est vide.</strong><br/>Ajoutez uniquement ce que vous souhaitez conserver ici, pour vous.</div>';
    return;
  }
  list.innerHTML=entries.map(entry=>`<article class="conscience-entry-card" data-entry-id="${escapeHtml(entry.id)}"><div class="conscience-entry-meta"><span class="conscience-entry-type">${escapeHtml(entryTypeLabel(entry.entry_type))}</span><span class="conscience-entry-dates">Mis à jour ${escapeHtml(formatDate(entry.updated_at||entry.created_at))}</span></div><p class="conscience-entry-content">${escapeHtml(entry.content_payload||'')}</p><div class="conscience-entry-actions"><button class="btn btn-secondary btn-small" type="button" data-vault-edit="${escapeHtml(entry.id)}" data-vault-action>Modifier</button><button class="btn btn-secondary btn-small" type="button" data-vault-delete="${escapeHtml(entry.id)}" data-vault-action>Supprimer définitivement</button></div></article>`).join('');
}

async function loadEntries(){
  const sessionId=requireVaultSession();
  const result=await invokeVault({action:'list_entries',vault_session_id:sessionId});
  entries=Array.isArray(result.entries)?result.entries:[];
  renderEntries();
}

async function openVault(){
  if(busy)return;
  setBusy(true);
  resetChallenge();
  status('Vérification des protections du coffre…','info');
  try{
    const meta=deviceMetadata();
    const result=await invokeVault({action:'open_session',...meta,ttl_seconds:VAULT_TTL_SECONDS});
    if(!result.vault_session_id)throw Object.assign(new Error('Session privée absente.'),{code:'VAULT_OPERATION_REFUSED'});
    armVaultSession(result.vault_session_id,result.expires_in_seconds);
    const locked=q('[data-vault-locked]');
    const workspace=q('[data-vault-workspace]');
    if(locked)locked.hidden=true;
    if(workspace)workspace.hidden=false;
    const risk=q('[data-vault-risk]');
    if(risk){
      const score=Number(result.security?.risk_score);
      risk.textContent=Number.isInteger(score)?`Protection V25 · risque ${score}/100`:'Protection V25 active';
    }
    await loadEntries();
    status('Registre personnel ouvert. La capacité reste uniquement en mémoire et expirera automatiquement.','success');
  }catch(error){
    localLock('',false);
    if(error?.code==='SECURITY_CHALLENGE_REQUIRED')showChallenge(error);
    status(friendlyVaultError(error),'error');
  }finally{setBusy(false)}
}

async function revokeAndLock(message='Registre verrouillé.'){
  const sessionId=vaultSessionId;
  localLock(message,false);
  if(sessionId){
    try{await invokeVault({action:'revoke_session',vault_session_id:sessionId})}catch{}
  }
  status(message,'success');
}

function startEdit(entryId){
  const entry=entries.find(item=>item.id===entryId);
  if(!entry)return;
  const id=q('[data-vault-entry-id]');
  const type=q('[data-vault-entry-type]');
  const content=q('[data-vault-entry-content]');
  if(id)id.value=entry.id;
  if(type)type.value=entry.entry_type||'reflection';
  if(content){content.value=entry.content_payload||'';content.focus()}
  const title=q('[data-vault-form-title]');
  if(title)title.textContent='Modifier cette entrée';
  const submit=q('[data-vault-submit]');
  if(submit)submit.textContent='Enregistrer les modifications';
  const cancel=q('[data-vault-edit-cancel]');
  if(cancel)cancel.hidden=false;
}

function cancelEdit(){
  const form=q('[data-vault-entry-form]');
  if(form)form.reset();
  const id=q('[data-vault-entry-id]');
  if(id)id.value='';
  const title=q('[data-vault-form-title]');
  if(title)title.textContent='Nouvelle entrée privée';
  const submit=q('[data-vault-submit]');
  if(submit)submit.textContent='Enregistrer dans mon coffre';
  const cancel=q('[data-vault-edit-cancel]');
  if(cancel)cancel.hidden=true;
}

async function saveEntry(form){
  const sessionId=requireVaultSession();
  const data=new FormData(form);
  const entryId=String(data.get('entry_id')||'').trim();
  const entryType=String(data.get('entry_type')||'reflection').trim().slice(0,64);
  const content=String(data.get('content_payload')||'');
  if(!content.trim())throw Object.assign(new Error('Ajoutez du contenu avant d’enregistrer.'),{code:'VAULT_ENTRY_CONTENT_INVALID'});
  if(textBytes(content)>MAX_CONTENT_BYTES)throw Object.assign(new Error('Entrée trop volumineuse.'),{code:'VAULT_ENTRY_CONTENT_INVALID'});

  if(entryId){
    await invokeVault({action:'update_entry',vault_session_id:sessionId,entry_id:entryId,entry_type:entryType,content_payload:content});
    status('Entrée mise à jour dans votre coffre privé.','success');
  }else{
    await invokeVault({action:'create_entry',vault_session_id:sessionId,entry_type:entryType,content_payload:content});
    status('Entrée enregistrée dans votre coffre privé.','success');
  }
  cancelEdit();
  await loadEntries();
}

async function deleteEntry(entryId){
  if(!globalThis.confirm('Supprimer définitivement cette entrée du Registre personnel ? Cette action ne crée pas de copie dans l’Histoire de vie.'))return;
  const sessionId=requireVaultSession();
  await invokeVault({action:'delete_entry',vault_session_id:sessionId,entry_id:entryId});
  entries=entries.filter(item=>item.id!==entryId);
  renderEntries();
  cancelEdit();
  status('Entrée supprimée définitivement du coffre.','success');
}

function handleVaultFailure(error){
  if(error?.code==='VAULT_SESSION_INVALID'||error?.code==='VAULT_SESSION_REQUIRED')localLock('',false);
  status(friendlyVaultError(error),'error');
}

function wireEvents(){
  q('[data-vault-open]')?.addEventListener('click',openVault);
  q('[data-vault-retry]')?.addEventListener('click',openVault);
  q('[data-vault-lock]')?.addEventListener('click',()=>revokeAndLock('Registre verrouillé. Le contenu affiché a été effacé de la page.'));
  q('[data-vault-edit-cancel]')?.addEventListener('click',cancelEdit);
  q('[data-vault-entry-form]')?.addEventListener('submit',async event=>{
    event.preventDefault();
    if(busy)return;
    setBusy(true);
    try{await saveEntry(event.currentTarget)}catch(error){handleVaultFailure(error)}finally{setBusy(false)}
  });
  q('[data-vault-entries]')?.addEventListener('click',async event=>{
    const button=event.target.closest('button');
    if(!button||busy)return;
    if(button.dataset.vaultEdit){startEdit(button.dataset.vaultEdit);return}
    if(button.dataset.vaultDelete){
      setBusy(true);
      try{await deleteEntry(button.dataset.vaultDelete)}catch(error){handleVaultFailure(error)}finally{setBusy(false)}
    }
  });

  document.addEventListener('visibilitychange',()=>{
    if(document.hidden){
      hiddenLockTimer=setTimeout(()=>localLock('Registre verrouillé après une minute hors de cette page.',true),HIDDEN_LOCK_DELAY_MS);
    }else if(hiddenLockTimer){
      clearTimeout(hiddenLockTimer);
      hiddenLockTimer=null;
    }
  });
  globalThis.addEventListener('pagehide',()=>localLock('',false));
}

async function boot(){
  wireEvents();
  localLock('',false);
  try{
    await requireUser();
    status('Coffre verrouillé. Ouvrez-le seulement lorsque vous souhaitez consulter ou écrire une entrée privée.','info');
  }catch{}
}

boot();
