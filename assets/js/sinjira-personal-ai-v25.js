import { getSupabase, setStatus } from './sinjira-supabase.js';

const DEVICE_KEY_STORAGE='sinjira.security.device_key.v1';
let busy=false;
let state=null;

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
  return {device_key:deviceKey(),display_name:`${browser}${platform?` — ${platform}`:''}`.slice(0,120),device_type:type,platform};
}

function status(message,type='info'){setStatus(q('[data-personal-ai-status]'),message,type)}
function setBusy(value){
  busy=Boolean(value);
  document.querySelectorAll('button,input,select').forEach(node=>{if(node.dataset?.logout===undefined)node.disabled=busy});
}

async function errorPayload(error,data){
  if(data&&typeof data==='object')return data;
  const response=error?.context;
  if(response&&typeof response.clone==='function'){
    try{return await response.clone().json()}catch{}
  }
  return null;
}

async function invokePersonalAi(body){
  const {data,error}=await getSupabase().functions.invoke('personal-ai',{body:{...deviceMetadata(),...body}});
  if(error){
    const payload=await errorPayload(error,data);
    const wrapped=new Error(String(payload?.error||error.message||'Opération Mon IA refusée.'));
    wrapped.code=String(payload?.code||'PERSONAL_AI_OPERATION_REFUSED');
    wrapped.security=payload?.security||null;
    throw wrapped;
  }
  if(!data?.ok){
    const wrapped=new Error(String(data?.error||'Opération Mon IA refusée.'));
    wrapped.code=String(data?.code||'PERSONAL_AI_OPERATION_REFUSED');
    wrapped.security=data?.security||null;
    throw wrapped;
  }
  return data;
}

function friendlyError(error){
  const code=String(error?.code||'');
  if(code==='MFA_SETUP_REQUIRED')return 'Configurez d’abord l’authentification renforcée dans Ma sécurité. Mon IA privée exige toujours AAL2.';
  if(code==='MFA_REQUIRED')return 'Une vérification MFA récente est requise avant d’ouvrir ou modifier Mon IA.';
  if(code==='SECURITY_CHALLENGE_REQUIRED'){
    const display=String(error?.security?.display_code||'').trim();
    return `Cet appareil doit être confirmé depuis un autre appareil fiable.${display?` Code de confirmation : ${display}.`:''}`;
  }
  if(code==='SECURITY_BLOCKED')return 'La protection du compte bloque temporairement Mon IA. Consultez Ma sécurité avant de réessayer.';
  if(code==='AUTH_REQUIRED')return 'Reconnectez-vous à votre compte SINJIRA.';
  if(code==='MFA_STATE_UNAVAILABLE'||code==='SECURITY_DECISION_INVALID')return 'La protection de Mon IA ne peut pas être vérifiée pour le moment. Aucun accès n’a été accordé.';
  return String(error?.message||'Opération Mon IA refusée.');
}

function permissionGranted(source){
  const rows=Array.isArray(state?.source_permissions)?state.source_permissions:[];
  return rows.some(row=>row?.source_type===source&&row?.granted===true);
}

function renderState(){
  const settings=state?.settings||{};
  const form=q('[data-personal-ai-settings-form]');
  if(form){
    form.elements.namedItem('enabled').checked=settings.enabled===true;
    form.elements.namedItem('ai_display_name').value=settings.display_name||'';
    const language=form.elements.namedItem('language_code');
    if(language&&settings.language_code)language.value=settings.language_code;
  }
  document.querySelectorAll('[data-personal-ai-source]').forEach(node=>{
    node.checked=permissionGranted(node.dataset.personalAiSource);
  });
  const runtime=q('[data-personal-ai-runtime]');
  if(runtime)runtime.textContent='Runtime : non configuré — aucun chat, aucune mémoire et aucune récupération de source.';
}

async function loadState(){
  const result=await invokePersonalAi({action:'get_state'});
  state=result.state||{};
  renderState();
  document.querySelectorAll('[data-personal-ai-workspace]').forEach(node=>{node.hidden=false});
  status('Réglages privés ouverts. Aucun moteur IA n’est actif dans cette version.','success');
}

async function openWorkspace(){
  if(busy)return;
  setBusy(true);
  try{await loadState()}catch(error){status(friendlyError(error),'error')}
  finally{setBusy(false)}
}

async function saveSettings(event){
  event.preventDefault();
  if(busy)return;
  const form=event.currentTarget;
  setBusy(true);
  try{
    const result=await invokePersonalAi({
      action:'update_settings',
      enabled:form.elements.namedItem('enabled').checked===true,
      ai_display_name:String(form.elements.namedItem('ai_display_name').value||'').trim().slice(0,80),
      language_code:String(form.elements.namedItem('language_code').value||'fr-CA').slice(0,16)
    });
    state={...(state||{}),settings:result.settings};
    renderState();
    status('Vos réglages Mon IA sont enregistrés. Aucun modèle n’a été lancé.','success');
  }catch(error){status(friendlyError(error),'error')}
  finally{setBusy(false)}
}

async function setSourcePermission(event){
  if(busy)return;
  const input=event.currentTarget;
  const source=input.dataset.personalAiSource;
  const desired=input.checked===true;
  input.checked=!desired;
  setBusy(true);
  try{
    await invokePersonalAi({action:'set_source_permission',source_type:source,granted:desired});
    await loadState();
    status(desired?'Consentement enregistré. La récupération de cette source reste désactivée dans V25.':'Consentement retiré. Aucune donnée source n’est conservée par Mon IA.','success');
  }catch(error){status(friendlyError(error),'error')}
  finally{setBusy(false)}
}

async function deleteData(){
  if(busy)return;
  if(!window.confirm('Supprimer tous vos réglages et consentements Mon IA ? Vos autres espaces SINJIRA ne seront pas touchés.'))return;
  setBusy(true);
  try{
    await invokePersonalAi({action:'delete_personal_ai_data'});
    state=null;
    document.querySelectorAll('[data-personal-ai-workspace]').forEach(node=>{node.hidden=true});
    status('Vos données de fondation Mon IA ont été supprimées.','success');
  }catch(error){status(friendlyError(error),'error')}
  finally{setBusy(false)}
}

async function init(){
  const supabase=getSupabase();
  const {data:{user},error}=await supabase.auth.getUser();
  if(error||!user){status('Connectez-vous à votre compte SINJIRA pour accéder à Mon IA.','error');return}
  q('[data-personal-ai-open]')?.addEventListener('click',openWorkspace);
  q('[data-personal-ai-settings-form]')?.addEventListener('submit',saveSettings);
  document.querySelectorAll('[data-personal-ai-source]').forEach(node=>node.addEventListener('change',setSourcePermission));
  q('[data-personal-ai-delete]')?.addEventListener('click',deleteData);
}

init().catch(()=>status('Mon IA n’est pas disponible pour le moment.','error'));
