import { getSupabase, requireUser, escapeHtml, formatDate, setStatus } from './sinjira-supabase.js';

const DEVICE_KEY_STORAGE = 'sinjira.security.device_key.v1';
const MAX_RECENT = 25;

function qs(sel){return document.querySelector(sel)}
function qsa(sel){return [...document.querySelectorAll(sel)]}
function status(message,type='info'){setStatus(qs('[data-security-center-status]'),message,type)}

function randomDeviceKey(){
  if(globalThis.crypto?.randomUUID)return globalThis.crypto.randomUUID();
  const bytes=new Uint8Array(24);globalThis.crypto?.getRandomValues?.(bytes);
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

function pill(label,kind=''){return `<span class="security-pill ${kind}">${escapeHtml(label)}</span>`}
function empty(text){return `<p class="security-empty">${escapeHtml(text)}</p>`}

async function rpc(name,args={}){
  const {data,error}=await getSupabase().rpc(name,args);
  if(error)throw error;
  return data;
}

async function registerContext(meta){
  const registered=await rpc('security_register_device',{
    p_device_key:meta.device_key,p_display_name:meta.display_name,p_device_type:meta.device_type,p_platform:meta.platform
  });
  try{
    const {data,error}=await getSupabase().functions.invoke('security-context',{body:{...meta,action:'security_center'}});
    if(error)throw error;
    return {registered,context:data};
  }catch(error){
    console.warn('[SINJIRA security-context]',error?.message||error);
    return {registered,context:null};
  }
}

function renderOverview({devices=[],connections=[],travel=[],challenges=[],settings=null,context=null}){
  const trusted=devices.filter(d=>d.is_trusted&&!d.revoked_at).length;
  const pending=challenges.filter(c=>c.status==='pending'&&new Date(c.expires_at)>new Date()).length;
  const activeTravel=travel.filter(t=>t.status==='active'&&new Date(t.starts_at)<=new Date()&&new Date(t.ends_at)>=new Date()).length;
  const node=qs('[data-security-overview]');if(!node)return;
  node.innerHTML=`
    <div class="security-kpi"><strong>${trusted} appareil${trusted===1?'':'s'} fiable${trusted===1?'':'s'}</strong><span>${devices.length} appareil${devices.length===1?'':'s'} enregistré${devices.length===1?'':'s'}</span></div>
    <div class="security-kpi"><strong>${pending} confirmation${pending===1?'':'s'} en attente</strong><span>${connections.length} événement${connections.length===1?'':'s'} récent${connections.length===1?'':'s'} affiché${connections.length===1?'':'s'}</span></div>
    <div class="security-kpi"><strong>${activeTravel?'Mode Voyage actif':'Mode Voyage inactif'}</strong><span>${settings?.sensitive_step_up?'Protection renforcée active':'Protection renforcée désactivée'}</span></div>`;
  const privacy=qs('[data-security-privacy-runtime]');
  if(privacy){
    const geo=context?.geo_mode==='trusted_coarse'?'Région approximative disponible via infrastructure de confiance.':'Localisation de sécurité désactivée pour ce contexte.';
    privacy.textContent=`${geo} Aucune IP brute ni donnée GPS n’est stockée par le Centre de sécurité.`;
  }
}

function renderDevices(devices,meta){
  const node=qs('[data-security-devices]');if(!node)return;
  if(!devices.length){node.innerHTML=empty('Aucun appareil enregistré.');return}
  node.innerHTML=devices.map(d=>{
    const current=d.device_key===meta.device_key;
    const badges=[current&&pill('Cet appareil','good'),d.is_primary&&pill('Principal','good'),d.is_trusted&&pill('Fiable','good'),d.revoked_at&&pill('Révoqué','danger')].filter(Boolean).join(' ');
    return `<article class="security-item" data-device-id="${d.id}"><div class="security-item-head"><div><h3>${escapeHtml(d.display_name||'Appareil SINJIRA')}</h3><div>${badges}</div></div><small>Dernière activité : ${escapeHtml(formatDate(d.last_seen_at))}</small></div><p><small>${escapeHtml(d.device_type||'appareil')} · ${escapeHtml(d.platform||'plateforme non précisée')}</small></p>${d.last_country_code?`<p><small>Dernière région de sécurité : ${escapeHtml(d.last_country_code)}${d.last_region_code?` · ${escapeHtml(d.last_region_code)}`:''}</small></p>`:''}<div class="security-actions">${!d.revoked_at&&!d.is_trusted?`<button class="btn btn-secondary" type="button" data-device-trust="${d.id}">Marquer fiable</button>`:''}${!d.revoked_at&&d.is_trusted&&!d.is_primary?`<button class="btn btn-secondary" type="button" data-device-primary="${d.id}">Définir principal</button>`:''}${!d.revoked_at&&d.is_trusted?`<button class="btn btn-secondary" type="button" data-device-untrust="${d.id}">Retirer la confiance</button>`:''}${!d.revoked_at&&!current?`<button class="btn btn-secondary" type="button" data-device-revoke="${d.id}">Révoquer</button>`:''}</div></article>`;
  }).join('');
}

function renderSessions(sessions){
  const node=qs('[data-security-sessions]');if(!node)return;
  if(!sessions?.length){node.innerHTML=empty('Aucune session active trouvée.');return}
  node.innerHTML=sessions.map(s=>`<article class="security-item"><div class="security-item-head"><div><h3>${s.is_current?'Session actuelle':'Session SINJIRA'}</h3>${s.is_current?pill('Cet appareil','good'):''} ${pill(String(s.aal||'aal1').toUpperCase(),s.aal==='aal2'?'good':'')}</div><small>Mise à jour : ${escapeHtml(formatDate(s.updated_at))}</small></div><p><small>${escapeHtml(s.user_agent||'Agent utilisateur non disponible')}</small></p></article>`).join('');
}

function renderConnections(rows){
  const node=qs('[data-security-connections]');if(!node)return;
  if(!rows.length){node.innerHTML=empty('Aucun événement de connexion récent.');return}
  node.innerHTML=rows.map(r=>{
    const kind=r.outcome==='block'||r.outcome==='denied'?'danger':r.outcome==='challenge'?'warn':'good';
    const region=r.country_code?`${r.country_code}${r.region_code?` · ${r.region_code}`:''}`:'Région non enregistrée';
    const reasons=(r.risk_reasons||[]).map(x=>String(x).replaceAll('_',' ')).join(', ')||'aucun signal particulier';
    return `<article class="security-item"><div class="security-item-head"><div><h3>${escapeHtml(r.action_name||'session')}</h3>${pill(r.outcome||'allow',kind)} ${pill(`Risque ${r.risk_score||0}/100`,kind)}</div><small>${escapeHtml(formatDate(r.occurred_at))}</small></div><p><small>${escapeHtml(region)} · ${escapeHtml(r.client_type||'client')} · ${escapeHtml(r.platform||'')}</small></p><p><small>Signaux : ${escapeHtml(reasons)}</small></p></article>`;
  }).join('');
}

function renderSecurityEvents(rows){
  const node=qs('[data-security-events]');if(!node)return;
  if(!rows.length){node.innerHTML=empty('Aucun changement de sécurité récent.');return}
  node.innerHTML=rows.map(r=>`<article class="security-item"><div class="security-item-head"><div><h3>${escapeHtml(String(r.event_type||'sécurité').replaceAll('_',' '))}</h3>${pill(r.severity||'info',r.severity==='critical'?'danger':r.severity==='warning'?'warn':'good')}</div><small>${escapeHtml(formatDate(r.created_at))}</small></div><p>${escapeHtml(r.summary||'')}</p></article>`).join('');
}

function renderTravel(rows){
  const node=qs('[data-security-travel-list]');if(!node)return;
  if(!rows.length){node.innerHTML=empty('Aucun voyage enregistré.');return}
  node.innerHTML=rows.map(r=>`<article class="security-item"><div class="security-item-head"><div><h3>${escapeHtml((r.destinations||[]).join(' → '))}</h3>${pill(r.status,r.status==='active'?'good':'')}</div><small>${escapeHtml(formatDate(r.starts_at))} → ${escapeHtml(formatDate(r.ends_at))}</small></div><p><small>Suppression prévue : ${escapeHtml(formatDate(r.delete_after))}</small></p>${r.status==='active'?`<div class="security-actions"><button class="btn btn-secondary" type="button" data-travel-cancel="${r.id}">Annuler ce voyage</button></div>`:''}</article>`).join('');
}

function renderChallenges(rows,devices,meta){
  const node=qs('[data-security-challenges]');if(!node)return;
  const pending=rows.filter(r=>r.status==='pending'&&new Date(r.expires_at)>new Date());
  if(!pending.length){node.innerHTML=empty('Aucune connexion ne demande votre confirmation.');return}
  const currentDevice=devices.find(d=>d.device_key===meta.device_key&&!d.revoked_at)||null;
  node.innerHTML=pending.map(r=>{
    const sameRequestDevice=Boolean(currentDevice&&currentDevice.id===r.request_device_id);
    const canResolve=Boolean(currentDevice&&currentDevice.is_trusted&&!sameRequestDevice);
    const controls=canResolve
      ? `<div class="security-actions"><button class="btn btn-primary" type="button" data-challenge-approve="${r.id}">Autoriser</button><button class="btn btn-secondary" type="button" data-challenge-deny="${r.id}">Refuser</button></div>`
      : sameRequestDevice
        ? '<p><small>Cette tentative provient de cet appareil. Elle doit être confirmée par votre MFA pendant la connexion ou depuis un autre appareil déjà fiable.</small></p>'
        : '<p><small>Pour autoriser ou refuser cette tentative, utilisez un autre appareil déjà marqué comme fiable.</small></p>';
    return `<article class="security-item"><div class="security-item-head"><div><h3>Nouvelle connexion à confirmer</h3>${pill('En attente','warn')}</div><small>Expire : ${escapeHtml(formatDate(r.expires_at))}</small></div><p>Code de vérification : <span class="security-code">${escapeHtml(r.display_code)}</span></p>${controls}</article>`;
  }).join('');
}

function fillSettings(settings){
  qsa('[data-security-setting]').forEach(input=>{const key=input.name;if(key in settings)input.checked=Boolean(settings[key])});
}

async function loadState(meta,context=null){
  const [settings,devices,sessions,travel,connections,events,challenges]=await Promise.all([
    rpc('security_get_settings'),
    getSupabase().from('security_devices').select('*').order('last_seen_at',{ascending:false}).then(({data,error})=>{if(error)throw error;return data||[]}),
    rpc('security_list_sessions'),
    getSupabase().from('security_travel_plans').select('*').order('starts_at',{ascending:false}).limit(20).then(({data,error})=>{if(error)throw error;return data||[]}),
    getSupabase().from('security_connection_events').select('*').order('occurred_at',{ascending:false}).limit(MAX_RECENT).then(({data,error})=>{if(error)throw error;return data||[]}),
    getSupabase().from('security_events').select('*').order('created_at',{ascending:false}).limit(MAX_RECENT).then(({data,error})=>{if(error)throw error;return data||[]}),
    getSupabase().from('security_connection_challenges').select('*').order('created_at',{ascending:false}).limit(MAX_RECENT).then(({data,error})=>{if(error)throw error;return data||[]})
  ]);
  fillSettings(settings);renderDevices(devices,meta);renderSessions(sessions);renderTravel(travel);renderConnections(connections);renderSecurityEvents(events);renderChallenges(challenges,devices,meta);renderOverview({devices,connections,travel,challenges,settings,context});
  return {settings,devices,sessions,travel,connections,events,challenges};
}

async function saveSettings(){
  const values={};qsa('[data-security-setting]').forEach(input=>values[`p_${input.name}`]=Boolean(input.checked));
  await rpc('security_update_settings',values);status('Préférences de sécurité enregistrées.','success');
}

async function createTravel(form){
  const data=new FormData(form);const start=String(data.get('starts_at')||'');const end=String(data.get('ends_at')||'');
  const destinations=String(data.get('destinations')||'').split(',').map(x=>x.trim()).filter(Boolean);
  if(!start||!end||!destinations.length)throw new Error('Indiquez une période et au moins une destination approximative.');
  await rpc('security_create_travel_plan',{p_starts_at:new Date(start).toISOString(),p_ends_at:new Date(end).toISOString(),p_destinations:destinations,p_multi_country:data.get('multi_country')==='on'});
  form.reset();status('Mode Voyage enregistré. Les données seront supprimées après la période de sécurité prévue.','success');
}

function confirmAction(message){return globalThis.confirm(message)}

async function boot(){
  const meta=deviceMetadata();
  try{
    await requireUser();
    status('Initialisation du Centre de sécurité…');
    const contextResult=await registerContext(meta);
    let state=await loadState(meta,contextResult.context);

    qs('[data-security-settings-save]')?.addEventListener('click',async()=>{try{await saveSettings();state=await loadState(meta,contextResult.context)}catch(e){status(e.message||String(e),'error')}});
    qs('[data-security-travel-form]')?.addEventListener('submit',async e=>{e.preventDefault();try{await createTravel(e.currentTarget);state=await loadState(meta,contextResult.context)}catch(err){status(err.message||String(err),'error')}});
    qs('[data-security-refresh]')?.addEventListener('click',async()=>{try{state=await loadState(meta,contextResult.context);status('État de sécurité actualisé.','success')}catch(e){status(e.message||String(e),'error')}});
    qs('[data-security-compromised]')?.addEventListener('click',async()=>{
      if(!confirmAction('Révoquer les autres appareils SINJIRA et fermer leurs sessions ?'))return;
      try{await rpc('security_compromise_account',{p_current_device_key:meta.device_key});await getSupabase().auth.signOut({scope:'others'});state=await loadState(meta,contextResult.context);status('Mesures d’urgence appliquées : autres appareils révoqués et autres sessions fermées.','success')}catch(e){status(e.message||String(e),'error')}
    });

    document.addEventListener('click',async e=>{
      const target=e.target.closest('button');if(!target)return;
      try{
        if(target.dataset.deviceTrust){await rpc('security_set_device_trust',{p_device_id:target.dataset.deviceTrust,p_trusted:true,p_primary:false});status('Appareil marqué comme fiable.','success')}
        else if(target.dataset.devicePrimary){await rpc('security_set_device_trust',{p_device_id:target.dataset.devicePrimary,p_trusted:true,p_primary:true});status('Appareil principal mis à jour.','success')}
        else if(target.dataset.deviceUntrust){if(!confirmAction('Retirer la confiance à cet appareil ?'))return;await rpc('security_set_device_trust',{p_device_id:target.dataset.deviceUntrust,p_trusted:false,p_primary:false});status('Confiance retirée.','success')}
        else if(target.dataset.deviceRevoke){if(!confirmAction('Révoquer cet appareil ? Il devra être réautorisé pour être réutilisé.'))return;await rpc('security_revoke_device',{p_device_id:target.dataset.deviceRevoke});status('Appareil révoqué.','success')}
        else if(target.dataset.travelCancel){if(!confirmAction('Annuler ce Mode Voyage ?'))return;await rpc('security_cancel_travel_plan',{p_plan_id:target.dataset.travelCancel});status('Mode Voyage annulé.','success')}
        else if(target.dataset.challengeApprove){await rpc('security_resolve_connection_challenge',{p_challenge_id:target.dataset.challengeApprove,p_device_key:meta.device_key,p_decision:'approved'});status('Connexion autorisée.','success')}
        else if(target.dataset.challengeDeny){await rpc('security_resolve_connection_challenge',{p_challenge_id:target.dataset.challengeDeny,p_device_key:meta.device_key,p_decision:'denied'});status('Connexion refusée. Vérifiez vos appareils si vous ne reconnaissez pas cette tentative.','success')}
        else return;
        state=await loadState(meta,contextResult.context);
      }catch(err){status(err.message||String(err),'error')}
    });

    status('Centre de sécurité prêt.','success');
  }catch(error){console.error('[SINJIRA security center]',error);status(error.message||String(error),'error')}
}

boot();
