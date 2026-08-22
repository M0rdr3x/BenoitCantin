import {getSupabase,requireUser,escapeHtml,setStatus,formatDate} from './sinjira-supabase.js';

const s=getSupabase();
const PAGE_PATH='/compte/histoire-de-vie.html';
const state={user:null,settings:null,entries:[],versions:[],mappings:[],recipients:[]};

const typeLabels={childhood:'Enfance',memory:'Souvenir',relationship:'Relation',milestone:'Étape importante',travel:'Voyage',passion:'Passion',choice:'Choix',value:'Valeur',person:'Personne importante',event:'Événement',anecdote:'Anecdote',reflection:'Réflexion',other:'Autre'};
const knowledgeLabels={declared_fact:'Fait déclaré',reflection:'Réflexion',reconstruction:'Reconstruction'};
const audienceLabels={family:'Famille',personal:'Personnelle',general:'Générale'};
const defaultVersions={
  family:{name:'Famille',title:'Mon histoire — version famille'},
  personal:{name:'Personnelle',title:'Mon histoire — version personnelle'},
  general:{name:'Générale',title:'Mon histoire — version générale'}
};

function qs(sel){return document.querySelector(sel)}
function qsa(sel){return [...document.querySelectorAll(sel)]}
function report(message,type='info'){setStatus(qs('[data-life-story-status]'),message,type)}
function pill(text,kind=''){return `<span class="life-story-pill ${kind}">${escapeHtml(text)}</span>`}
function empty(text){return `<p class="life-story-empty">${escapeHtml(text)}</p>`}

async function ensureAal2(){
  const {data,error}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if(error)throw error;
  if(data?.nextLevel==='aal2'&&data?.currentLevel!=='aal2'){
    location.replace(`/compte/mfa.html?security=1&next=${encodeURIComponent(PAGE_PATH)}`);
    return false;
  }
  return true;
}

async function ensureWorkspace(userId){
  const {error:settingsError}=await s.from('life_story_legacy_settings').upsert({user_id:userId},{onConflict:'user_id',ignoreDuplicates:true});
  if(settingsError)throw settingsError;
  const {data:versions,error:versionsError}=await s.from('life_story_versions').select('audience').eq('user_id',userId);
  if(versionsError)throw versionsError;
  const existing=new Set((versions||[]).map(v=>v.audience));
  const missing=Object.entries(defaultVersions).filter(([audience])=>!existing.has(audience)).map(([audience,defaults])=>({user_id:userId,audience,...defaults,status:'draft'}));
  if(missing.length){
    const {error}=await s.from('life_story_versions').upsert(missing,{onConflict:'user_id,audience',ignoreDuplicates:true});
    if(error)throw error;
  }
}

async function loadState(){
  const userId=state.user.id;
  const [settingsResult,entriesResult,versionsResult,mappingsResult,recipientsResult]=await Promise.all([
    s.from('life_story_legacy_settings').select('*').eq('user_id',userId).maybeSingle(),
    s.from('life_story_entries').select('*').eq('user_id',userId).order('updated_at',{ascending:false}),
    s.from('life_story_versions').select('*').eq('user_id',userId).order('audience',{ascending:true}),
    s.from('life_story_version_entries').select('*').eq('user_id',userId).order('sort_order',{ascending:true}),
    s.from('life_story_recipients').select('*').eq('user_id',userId).eq('status','active').order('created_at',{ascending:true})
  ]);
  for(const result of [settingsResult,entriesResult,versionsResult,mappingsResult,recipientsResult])if(result.error)throw result.error;
  state.settings=settingsResult.data;
  state.entries=entriesResult.data||[];
  state.versions=versionsResult.data||[];
  state.mappings=mappingsResult.data||[];
  state.recipients=recipientsResult.data||[];
  renderAll();
}

function renderSummary(){
  const node=qs('[data-life-story-summary]');if(!node)return;
  const authorized=state.entries.filter(e=>e.posthumous_disclosure==='selected_versions'&&e.approval_status==='approved').length;
  const mapped=new Set(state.mappings.map(m=>m.entry_id)).size;
  node.innerHTML=`<div class="life-story-count"><strong>${state.entries.length}</strong><span>élément${state.entries.length===1?'':'s'} privé${state.entries.length===1?'':'s'}</span></div><div class="life-story-count"><strong>${authorized}</strong><span>autorisé${authorized===1?'':'s'} pour l’œuvre</span></div><div class="life-story-count"><strong>${mapped}</strong><span>inclus dans une version</span></div>`;
  const directive=qs('[data-life-story-directive-state]');
  if(directive)directive.textContent=state.settings?.delivery_enabled?'Directive posthume enregistrée':'Aucune transmission posthume activée';
}

function mappingSet(entryId){return new Set(state.mappings.filter(m=>m.entry_id===entryId).map(m=>m.version_id))}
function renderEntries(){
  const node=qs('[data-life-story-entries]');if(!node)return;
  if(!state.entries.length){node.innerHTML=empty('Aucun élément. Tout ce que vous ajouterez ici restera privé par défaut.');return}
  node.innerHTML=state.entries.map(entry=>{
    const authorized=entry.approval_status==='approved'&&entry.posthumous_disclosure==='selected_versions';
    const mapped=mappingSet(entry.id);
    const versionChecks=authorized?`<div class="life-story-version-checks">${state.versions.map(version=>`<label><input type="checkbox" data-life-entry-version="${entry.id}" data-version-id="${version.id}" ${mapped.has(version.id)?'checked':''}/> ${escapeHtml(audienceLabels[version.audience]||version.name)}</label>`).join('')}</div>`:'';
    return `<article class="life-story-item" data-entry-id="${entry.id}"><div class="life-story-item-head"><div><span class="eyebrow">${escapeHtml(typeLabels[entry.entry_type]||entry.entry_type)}</span><h3>${escapeHtml(entry.title)}</h3></div><small>${entry.occurred_on?escapeHtml(entry.occurred_on):'Date non précisée'}</small></div><div class="life-story-meta">${pill(knowledgeLabels[entry.knowledge_status]||entry.knowledge_status,entry.knowledge_status==='reconstruction'?'warn':'')}${authorized?pill('Autorisé pour l’œuvre','good'):pill('Privé','private')}${entry.source_kind==='ai_assisted_draft'?pill('Aide IA / reconstruction','warn'):''}</div><div class="life-story-body">${escapeHtml(entry.body)}</div>${authorized?`<p><small>Choisissez explicitement les versions où cet élément peut apparaître.</small></p>${versionChecks}`:'<p><small>Enregistrer un souvenir ne l’autorise jamais automatiquement pour une transmission posthume.</small></p>'}<div class="life-story-actions">${authorized?`<button class="btn btn-secondary" type="button" data-entry-private="${entry.id}">Retirer de l’œuvre et garder privé</button>`:`<button class="btn btn-primary" type="button" data-entry-authorize="${entry.id}">Autoriser pour l’œuvre</button>`}<button class="btn btn-secondary" type="button" data-entry-delete="${entry.id}">Supprimer</button></div></article>`;
  }).join('');
}

function renderVersions(){
  const node=qs('[data-life-story-versions]');if(!node)return;
  node.innerHTML=state.versions.map(version=>{
    const entryCount=state.mappings.filter(m=>m.version_id===version.id).length;
    const recipientCount=state.recipients.filter(r=>r.version_id===version.id).length;
    return `<form class="life-story-version" data-version-form="${version.id}"><span class="eyebrow">Version ${escapeHtml(audienceLabels[version.audience]||version.audience)}</span><h3>${escapeHtml(version.name)}</h3><p><small>${entryCount} élément${entryCount===1?'':'s'} · ${recipientCount} destinataire${recipientCount===1?'':'s'}</small></p><div class="field"><label>Titre de l’œuvre</label><input name="title" maxlength="200" value="${escapeHtml(version.title||'')}"/></div><div class="field"><label>Instructions de ton ou de contenu</label><textarea name="instructions" maxlength="5000" rows="3">${escapeHtml(version.instructions||'')}</textarea></div><label><input type="checkbox" name="ready" ${version.status==='ready'?'checked':''}/> Cette version est prête selon moi</label><div class="life-story-actions"><button class="btn btn-secondary" type="submit">Enregistrer cette version</button></div></form>`;
  }).join('');
  const selects=qsa('[data-life-story-version-select]');
  for(const select of selects){
    const current=select.value;
    select.innerHTML=state.versions.map(v=>`<option value="${v.id}">${escapeHtml(audienceLabels[v.audience]||v.name)}</option>`).join('');
    if(current&&state.versions.some(v=>v.id===current))select.value=current;
  }
}

function renderRecipients(){
  const node=qs('[data-life-story-recipients]');if(!node)return;
  if(!state.recipients.length){node.innerHTML=empty('Aucun destinataire choisi. Vous pouvez aussi volontairement ne désigner personne.');return}
  node.innerHTML=state.recipients.map(recipient=>{
    const version=state.versions.find(v=>v.id===recipient.version_id);
    return `<article class="life-story-item"><div class="life-story-item-head"><div><h3>${escapeHtml(recipient.recipient_label)}</h3><div class="life-story-meta">${pill(version?audienceLabels[version.audience]||version.name:'Version inconnue')}${recipient.recipient_email?pill('Coordonnée enregistrée','private'):pill('Contact nommé','private')}</div></div></div>${recipient.recipient_email?`<p><small>${escapeHtml(recipient.recipient_email)}</small></p>`:''}<div class="life-story-actions"><button class="btn btn-secondary" type="button" data-recipient-delete="${recipient.id}">Retirer ce destinataire</button></div></article>`;
  }).join('');
}

function renderSettings(){
  const form=qs('[data-life-story-settings-form]');
  if(form&&state.settings){form.elements.delivery_enabled.checked=Boolean(state.settings.delivery_enabled)}
  const review=qs('[data-life-story-legacy-review]');
  if(review)review.hidden=!state.settings?.legacy_directive_review_required;
}

function renderPreview(){
  const select=qs('[data-life-story-preview-version]');
  const node=qs('[data-life-story-preview]');
  if(!select||!node)return;
  if(!select.options.length){node.innerHTML=empty('Aucune version disponible.');return}
  const versionId=select.value||state.versions[0]?.id;
  if(versionId&&!select.value)select.value=versionId;
  const version=state.versions.find(v=>v.id===versionId);
  const maps=state.mappings.filter(m=>m.version_id===versionId).sort((a,b)=>a.sort_order-b.sort_order);
  const entries=maps.map(m=>state.entries.find(e=>e.id===m.entry_id)).filter(Boolean);
  if(!version){node.innerHTML=empty('Version introuvable.');return}
  node.innerHTML=`<h3>${escapeHtml(version.title||version.name)}</h3><p><small>Aperçu privé. Ce n’est pas encore le PDF posthume final.</small></p>${entries.length?entries.map(entry=>`<article><div class="life-story-meta">${pill(knowledgeLabels[entry.knowledge_status]||entry.knowledge_status,entry.knowledge_status==='reconstruction'?'warn':'')}</div><h4>${escapeHtml(entry.title)}</h4><div class="life-story-body">${escapeHtml(entry.body)}</div></article>`).join(''):empty('Aucun élément autorisé n’est inclus dans cette version.')}`;
}

function renderAll(){renderSummary();renderEntries();renderVersions();renderRecipients();renderSettings();renderPreview()}

async function addEntry(form){
  const data=new FormData(form);
  const title=String(data.get('title')||'').trim();
  const body=String(data.get('body')||'').trim();
  const entryType=String(data.get('entry_type')||'memory');
  const knowledge=String(data.get('knowledge_status')||'declared_fact');
  const occurred=String(data.get('occurred_on')||'').trim();
  if(!title||!body)throw new Error('Ajoutez un titre et un contenu.');
  const sourceKind=knowledge==='reconstruction'?'ai_assisted_draft':'self_declared';
  const {error}=await s.from('life_story_entries').insert({user_id:state.user.id,entry_type:entryType,title,body,occurred_on:occurred||null,knowledge_status:knowledge,source_kind:sourceKind,approval_status:'draft',posthumous_disclosure:'never',user_approved_at:null});
  if(error)throw error;
  form.reset();
  report('Élément enregistré en privé. Il n’est dans aucune œuvre tant que vous ne l’autorisez pas explicitement.','success');
  await loadState();
}

async function authorizeEntry(id){
  if(!globalThis.confirm('Autoriser cet élément à pouvoir être inclus dans votre Histoire de vie posthume ? Vous devrez encore choisir les versions. Cette autorisation ne donne aucun accès au Registre des Consciences.'))return;
  const {error}=await s.from('life_story_entries').update({approval_status:'approved',posthumous_disclosure:'selected_versions',user_approved_at:new Date().toISOString()}).eq('id',id).eq('user_id',state.user.id);
  if(error)throw error;
  report('Élément autorisé. Choisissez maintenant les versions où il peut apparaître.','success');
  await loadState();
}

async function privatizeEntry(id){
  if(!globalThis.confirm('Retirer cet élément de toutes les versions et le garder privé ?'))return;
  const {error}=await s.from('life_story_entries').update({posthumous_disclosure:'never'}).eq('id',id).eq('user_id',state.user.id);
  if(error)throw error;
  report('Élément retiré de toutes les versions et conservé privé.','success');
  await loadState();
}

async function deleteEntry(id){
  if(!globalThis.confirm('Supprimer définitivement cet élément de votre Histoire de vie ?'))return;
  const {error}=await s.from('life_story_entries').delete().eq('id',id).eq('user_id',state.user.id);
  if(error)throw error;
  report('Élément supprimé.','success');
  await loadState();
}

async function toggleVersion(entryId,versionId,checked){
  if(checked){
    const sortOrder=state.mappings.filter(m=>m.version_id===versionId).length;
    const {error}=await s.from('life_story_version_entries').insert({user_id:state.user.id,entry_id:entryId,version_id:versionId,sort_order:sortOrder});
    if(error)throw error;
  }else{
    const {error}=await s.from('life_story_version_entries').delete().eq('user_id',state.user.id).eq('entry_id',entryId).eq('version_id',versionId);
    if(error)throw error;
  }
  await loadState();
  report('Sélection de version mise à jour.','success');
}

async function saveVersion(form){
  const id=form.dataset.versionForm;
  const data=new FormData(form);
  const title=String(data.get('title')||'').trim();
  const instructions=String(data.get('instructions')||'').trim();
  const statusValue=data.get('ready')==='on'?'ready':'draft';
  const {error}=await s.from('life_story_versions').update({title:title||null,instructions:instructions||null,status:statusValue}).eq('id',id).eq('user_id',state.user.id);
  if(error)throw error;
  report('Version enregistrée.','success');
  await loadState();
}

async function addRecipient(form){
  const data=new FormData(form);
  const versionId=String(data.get('version_id')||'');
  const label=String(data.get('recipient_label')||'').trim();
  const email=String(data.get('recipient_email')||'').trim();
  if(!versionId||!label)throw new Error('Choisissez une version et indiquez le nom du destinataire.');
  const payload={user_id:state.user.id,version_id:versionId,recipient_kind:email?'email':'named_contact',recipient_label:label,recipient_email:email||null,status:'active'};
  const {error}=await s.from('life_story_recipients').insert(payload);
  if(error)throw error;
  form.reset();
  report('Destinataire enregistré. Aucun message ni fichier n’est envoyé à cette étape.','success');
  await loadState();
}

async function deleteRecipient(id){
  if(!globalThis.confirm('Retirer ce destinataire de votre directive ?'))return;
  const {error}=await s.from('life_story_recipients').delete().eq('id',id).eq('user_id',state.user.id);
  if(error)throw error;
  report('Destinataire retiré.','success');
  await loadState();
}

async function saveSettings(form){
  const enabled=form.elements.delivery_enabled.checked;
  const {error}=await s.from('life_story_legacy_settings').update({delivery_enabled:enabled,legacy_directive_review_required:false}).eq('user_id',state.user.id);
  if(error)throw error;
  await loadState();
  if(enabled&&state.recipients.length===0)report('Directive enregistrée, mais aucun destinataire n’est choisi. Rien ne pourra être transmis tant que cette liste reste vide.','info');
  else report(enabled?'Directive posthume enregistrée. La vérification du décès restera obligatoire avant toute opération.':'Transmission posthume désactivée.','success');
}

function bindEvents(){
  qs('[data-life-story-entry-form]')?.addEventListener('submit',async event=>{event.preventDefault();try{await addEntry(event.currentTarget)}catch(error){report(error.message||String(error),'error')}});
  qs('[data-life-story-recipient-form]')?.addEventListener('submit',async event=>{event.preventDefault();try{await addRecipient(event.currentTarget)}catch(error){report(error.message||String(error),'error')}});
  qs('[data-life-story-settings-form]')?.addEventListener('submit',async event=>{event.preventDefault();try{await saveSettings(event.currentTarget)}catch(error){report(error.message||String(error),'error')}});
  qs('[data-life-story-preview-version]')?.addEventListener('change',()=>renderPreview());
  document.addEventListener('submit',async event=>{
    const form=event.target.closest?.('[data-version-form]');if(!form)return;
    event.preventDefault();try{await saveVersion(form)}catch(error){report(error.message||String(error),'error')}
  });
  document.addEventListener('click',async event=>{
    const authorize=event.target.closest?.('[data-entry-authorize]');
    const privateButton=event.target.closest?.('[data-entry-private]');
    const removeEntry=event.target.closest?.('[data-entry-delete]');
    const removeRecipient=event.target.closest?.('[data-recipient-delete]');
    try{
      if(authorize)await authorizeEntry(authorize.dataset.entryAuthorize);
      else if(privateButton)await privatizeEntry(privateButton.dataset.entryPrivate);
      else if(removeEntry)await deleteEntry(removeEntry.dataset.entryDelete);
      else if(removeRecipient)await deleteRecipient(removeRecipient.dataset.recipientDelete);
    }catch(error){report(error.message||String(error),'error')}
  });
  document.addEventListener('change',async event=>{
    const input=event.target.closest?.('[data-life-entry-version]');if(!input)return;
    input.disabled=true;
    try{await toggleVersion(input.dataset.lifeEntryVersion,input.dataset.versionId,input.checked)}catch(error){input.checked=!input.checked;report(error.message||String(error),'error')}finally{input.disabled=false}
  });
}

async function boot(){
  state.user=await requireUser();
  if(!state.user)return;
  if(!await ensureAal2())return;
  await ensureWorkspace(state.user.id);
  await loadState();
  bindEvents();
  report('Histoire de vie chargée. Tout nouvel élément reste privé tant que vous ne l’autorisez pas.','success');
}

boot().catch(error=>{
  console.warn('[SINJIRA life story]',error);
  report('Impossible de charger l’Histoire de vie de façon sécurisée pour le moment.','error');
});
