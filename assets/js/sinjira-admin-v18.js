import {getSupabase,escapeHtml} from './sinjira-supabase.js';
import './v24-admin-health.js';

async function call(action,extra={}){const {data,error}=await getSupabase().functions.invoke('admin-sinjira-v18',{body:{action,...extra}});if(error||!data?.ok){const err=new Error(data?.error||error?.message||'Erreur administration V18');err.data=data||null;throw err}return data}
function setText(sel,v){const n=document.querySelector(sel);if(n)n.textContent=String(v??0)}
async function dashboard(){const d=(await call('dashboard')).dashboard||{};setText('[data-admin-reader-comments]',d.pending_comments);setText('[data-admin-character-submissions]',d.character_submissions);setText('[data-admin-character-review]',d.characters_in_review)}

async function canonOverview(){
  const d=await call('canon_overview'),box=document.querySelector('[data-admin-canon-list]');
  if(!box)return;
  box.innerHTML=(d.contexts||[]).map(c=>`<article class="admin-v18-row"><strong>${escapeHtml(c.title||c.context_key)}</strong><p><b>Statut :</b> ${escapeHtml(c.classification)} · <b>Source :</b> ${escapeHtml(c.source_name||'')} · <b>Version :</b> ${escapeHtml(c.source_version||'')}</p><details><summary>Afficher le contexte privé</summary><pre style="white-space:pre-wrap;overflow:auto">${escapeHtml(JSON.stringify(c.content||{},null,2))}</pre></details></article>`).join('')||'<p>Aucun contexte canonique privé.</p>';
}

async function auditLog(){const d=await call('audit_log'),box=document.querySelector('[data-admin-audit-list]');if(!box)return;box.innerHTML=(d.rows||[]).map(r=>`<div class="v19-audit-row"><strong>${escapeHtml(r.action)}</strong><p>${escapeHtml(r.summary||'')}</p><code>${escapeHtml(r.entity_type||'')} ${escapeHtml(r.entity_id||'')}</code><div class="v19-muted">${escapeHtml(new Date(r.created_at).toLocaleString('fr-CA'))}</div></div>`).join('')||'<p>Aucune action V19 enregistrée.</p>'}

function openAdminTab(name){
 document.querySelectorAll('[data-admin-tab]').forEach(b=>{if(b.dataset.adminTab===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
 document.querySelectorAll('[data-admin-panel]').forEach(p=>{p.hidden=p.dataset.adminPanel!==name});
}
function notificationTarget(n){
 const type=String(n?.notification_type||'').toLowerCase(),entity=String(n?.related_entity_type||'').toLowerCase();
 if(type.includes('character')||entity.includes('character_submission'))return 'fan-characters';
 if(type.includes('tester')||type.includes('access')||entity.includes('access'))return 'access';
 if(type.includes('report')||entity.includes('fracture')||entity.includes('report'))return 'reports';
 if(type.includes('novel_comment')||entity.includes('novel_comment'))return 'reader-comments';
 if(type.includes('social')||entity.includes('social'))return 'social-moderation';
 return 'notifications';
}
function ensureNotificationsUi(){
 const tabs=document.querySelector('.admin-console-tabs'),main=document.querySelector('.admin-console-layout');
 if(!tabs||!main)return;
 if(!tabs.querySelector('[data-admin-tab="notifications"]')){
   const button=document.createElement('button');button.type='button';button.dataset.adminTab='notifications';button.innerHTML='Notifications <span data-admin-notification-badge style="font-weight:800"></span>';
   button.addEventListener('click',()=>openAdminTab('notifications'));tabs.prepend(button);
 }
 if(!main.querySelector('[data-admin-panel="notifications"]')){
   const panel=document.createElement('section');panel.className='admin-panel';panel.dataset.adminPanel='notifications';panel.hidden=true;
   panel.innerHTML='<article class="account-card"><span class="eyebrow">Centre administrateur</span><h2>Notifications</h2><p>Demandes, questionnaires et événements internes qui requièrent votre attention.</p><div class="admin-row-actions" style="margin-bottom:14px"><button class="btn btn-secondary btn-small" type="button" data-admin-notification-read-all>Tout marquer comme lu</button><button class="btn btn-secondary btn-small" type="button" data-admin-notification-refresh>Actualiser</button></div><div class="admin-management-list" data-admin-notification-list></div></article>';
   main.appendChild(panel);
   panel.querySelector('[data-admin-notification-read-all]').addEventListener('click',async()=>{try{await call('mark_all_notifications_read');await notifications()}catch(e){alert(e.message)}});
   panel.querySelector('[data-admin-notification-refresh]').addEventListener('click',()=>notifications().catch(e=>console.error(e)));
 }
}
async function notifications(){
 ensureNotificationsUi();
 const d=await call('list_notifications'),rows=d.notifications||[],unread=Number(d.unread||0),box=document.querySelector('[data-admin-notification-list]'),badge=document.querySelector('[data-admin-notification-badge]');
 if(badge)badge.textContent=unread?`(${unread})`:'';
 if(!box)return;
 box.innerHTML=rows.map(n=>{const isUnread=!n.read_at,target=notificationTarget(n);return `<article class="admin-management-row" style="align-items:flex-start;${isUnread?'border-left:3px solid currentColor;padding-left:12px':''}"><div><strong>${isUnread?'● ':''}${escapeHtml(n.title||n.notification_type||'Notification')}</strong><span>${escapeHtml(n.notification_type||'')} · ${escapeHtml(new Date(n.created_at).toLocaleString('fr-CA'))}</span>${n.body?`<p>${escapeHtml(n.body)}</p>`:''}</div><div class="admin-row-actions">${isUnread?`<button class="btn btn-secondary btn-small" type="button" data-notification-read="${n.id}">Marquer lu</button>`:''}${target!=='notifications'?`<button class="btn btn-primary btn-small" type="button" data-notification-open="${n.id}" data-target="${target}">Ouvrir</button>`:''}</div></article>`}).join('')||'<p>Aucune notification.</p>';
 box.querySelectorAll('[data-notification-read]').forEach(b=>b.addEventListener('click',async()=>{try{await call('mark_notification_read',{notification_id:b.dataset.notificationRead});await notifications()}catch(e){alert(e.message)}}));
 box.querySelectorAll('[data-notification-open]').forEach(b=>b.addEventListener('click',async()=>{try{await call('mark_notification_read',{notification_id:b.dataset.notificationOpen});openAdminTab(b.dataset.target);await notifications()}catch(e){alert(e.message)}}));
}

async function comments(){const d=await call('list_comments'),box=document.querySelector('[data-admin-reader-comment-list]');if(!box)return;box.innerHTML=(d.comments||[]).map(c=>`<article class="admin-v18-row"><strong>${escapeHtml(c.novel_title||'Roman')} · ${escapeHtml(c.display_name_snapshot||'Lecteur')}</strong><p>${escapeHtml(c.body)}</p>${c.contains_spoilers?'<small>⚠ Contient des divulgâcheurs</small>':''}<div class="admin-v18-actions"><button class="btn btn-primary btn-small" data-comment="${c.id}" data-decision="approved">Approuver</button><button class="btn btn-secondary btn-small" data-comment="${c.id}" data-decision="refused">Refuser</button></div></article>`).join('')||'<p>Aucun commentaire en attente.</p>';box.querySelectorAll('[data-comment]').forEach(b=>b.addEventListener('click',async()=>{await call('moderate_comment',{comment_id:b.dataset.comment,decision:b.dataset.decision});await comments();await dashboard()}))}

async function submissions(){const d=await call('list_submissions'),box=document.querySelector('[data-admin-submission-list]');if(!box)return;box.innerHTML=(d.submissions||[]).map(s=>`<article class="admin-v18-row"><strong>${escapeHtml(s.account_pseudo||s.account_email||'Compte SINJIRA')}</strong><p>Statut : ${escapeHtml(s.status)} · ${escapeHtml(new Date(s.created_at).toLocaleString('fr-CA'))}</p>${s.photo_url?`<img src="${escapeHtml(s.photo_url)}" alt="Photo source confidentielle" style="width:min(220px,100%);aspect-ratio:1;object-fit:cover;border-radius:16px;margin:10px 0">`:''}${s.source_payload?`<details><summary>Afficher les réponses du questionnaire</summary><pre style="white-space:pre-wrap;overflow:auto;max-height:520px">${escapeHtml(JSON.stringify(s.source_payload,null,2))}</pre></details>`:'<p><em>Les données sources ont été supprimées ou ne sont plus disponibles.</em></p>'}<div class="admin-v18-actions"><button class="btn btn-primary btn-small" data-manual="${s.id}">Préparer le personnage manuellement</button><button class="btn btn-secondary btn-small" data-ai="${s.id}" ${s.source_payload?'':'disabled'}>Préparer un brouillon avec IA</button><button class="btn btn-secondary btn-small" data-purge="${s.id}" ${s.source_payload?'':'disabled'}>Supprimer les données sources personnelles</button></div></article>`).join('')||'<p>Aucun questionnaire reçu.</p>';
 box.querySelectorAll('[data-manual]').forEach(b=>b.addEventListener('click',async()=>{b.disabled=true;try{await call('create_manual_character',{submission_id:b.dataset.manual});alert('Fiche de personnage créée. Ouvrez « Bible personnages » pour la compléter.');await Promise.all([submissions(),characters(),dashboard()])}catch(e){alert(e.message)}finally{b.disabled=false}}));
 box.querySelectorAll('[data-ai]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('Préparer un brouillon IA provisoire à partir des réponses créatives de ce dossier? Benoit Cantin devra le réviser et l’approuver.'))return;b.disabled=true;try{await call('generate_character',{submission_id:b.dataset.ai});alert('Brouillon IA créé. Ouvrez « Bible personnages » pour le réviser.');await Promise.all([submissions(),characters(),dashboard()])}catch(e){alert(e.message)}finally{b.disabled=false}}));
 box.querySelectorAll('[data-purge]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('Supprimer définitivement les réponses sources personnelles de ce dossier? Le personnage créé et sa Bible seront conservés.'))return;await call('purge_submission_source',{submission_id:b.dataset.purge,author_confirmed_source_purge:true});await submissions()}));
}

let charactersCache=[];
async function characters(){const d=await call('list_characters');charactersCache=d.characters||[];const box=document.querySelector('[data-admin-character-list]'),nov=document.querySelector('[data-admin-novel-select]');if(nov)nov.innerHTML='<option value="">Aucune liaison directe</option>'+(d.novels||[]).map(n=>`<option value="${n.id}">${escapeHtml(n.title)}</option>`).join('');if(!box)return;box.innerHTML=charactersCache.map(c=>`<article class="admin-v18-row"><strong>${escapeHtml(c.public_name||'Personnage sans nom')}</strong><p>${escapeHtml(c.status)} · ${escapeHtml(c.novel_title||c.novel_note||'Aucun roman attribué')}</p><button class="btn btn-secondary btn-small" data-edit-character="${c.id}">Modifier</button></article>`).join('')||'<p>Aucun personnage.</p>';box.querySelectorAll('[data-edit-character]').forEach(b=>b.addEventListener('click',()=>fillEditor(charactersCache.find(c=>c.id===b.dataset.editCharacter))))}
function fillEditor(c){const f=document.querySelector('[data-character-editor]');if(!c||!f)return;f.elements.id.value=c.id;f.elements.public_name.value=c.public_name||'';f.elements.status.value=c.status||'author_review';f.elements.canon_status.value=c.canon_status||'PROVISOIRE';f.elements.canon_version.value=c.canon_version||'v1.0';f.elements.public_description.value=c.public_description||'';f.elements.novel_id.value=c.novel_id||'';f.elements.novel_note.value=c.novel_note||'';f.elements.visible_to_user.checked=c.visible_to_user!==false;f.elements.bible_json.value=JSON.stringify(c.bible||{},null,2);if(f.elements.author_confirmed_canon)f.elements.author_confirmed_canon.checked=false;if(f.elements.author_confirmed_retcon)f.elements.author_confirmed_retcon.checked=false;f.scrollIntoView({behavior:'smooth'})}
function editor(){const f=document.querySelector('[data-character-editor]');if(!f)return;f.addEventListener('submit',async e=>{e.preventDefault();let bible={};try{bible=JSON.parse(f.elements.bible_json.value||'{}')}catch{return alert('Le JSON de la Bible est invalide.')};await call('save_character',{character:{id:f.elements.id.value,public_name:f.elements.public_name.value,status:f.elements.status.value,public_description:f.elements.public_description.value,novel_id:f.elements.novel_id.value||null,novel_note:f.elements.novel_note.value,visible_to_user:f.elements.visible_to_user.checked,canon_status:f.elements.canon_status.value,canon_version:f.elements.canon_version.value,author_confirmed_canon:Boolean(f.elements.author_confirmed_canon?.checked),author_confirmed_retcon:Boolean(f.elements.author_confirmed_retcon?.checked),bible}});alert('Personnage enregistré.');await characters()})}

function zoneForLocation(id){return worldLocationsCache.find(x=>x.id===id)?.timezone_name||''}
function zonedParts(date,zone){
 if(!zone)return null;
 try{
   const parts=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(date);
   return Object.fromEntries(parts.filter(x=>x.type!=='literal').map(x=>[x.type,x.value]));
 }catch{return null}
}
function toLocalInput(value,zone=''){
 if(!value)return '';
 const d=new Date(value);if(Number.isNaN(d.getTime()))return '';
 const pad=n=>String(n).padStart(2,'0');
 const p=zonedParts(d,zone);
 if(p)return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
 return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function toIso(value,zone=''){
 if(!value)return null;
 if(!zone){const d=new Date(value);return Number.isNaN(d.getTime())?null:d.toISOString()}
 const m=String(value).match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/);if(!m)return null;
 const target=Date.UTC(Number(m[1]),Number(m[2])-1,Number(m[3]),Number(m[4]),Number(m[5]),0);
 let guess=target;
 for(let i=0;i<4;i++){const p=zonedParts(new Date(guess),zone);if(!p)return null;const represented=Date.UTC(Number(p.year),Number(p.month)-1,Number(p.day),Number(p.hour),Number(p.minute),Number(p.second||0));const delta=target-represented;guess+=delta;if(Math.abs(delta)<1000)break}
 const result=new Date(guess);if(Number.isNaN(result.getTime()))return null;
 const roundTrip=toLocalInput(result.toISOString(),zone);return roundTrip===String(value)?result.toISOString():null;
}
function resetExtendedStoryEditor(){
 const f=document.querySelector('[data-extended-story-editor]');if(!f)return;
 f.reset();f.elements.id.value='';f.elements.published_at.value='';f.elements.story_type.value='character_chronicle';f.elements.anchor_scope.value='UNASSIGNED';f.elements.canon_status.value='PROVISOIRE';f.elements.status.value='draft';f.elements.audience.value='private';f.elements.location_id.value='';f.elements.continuity_json.value='{}';f.elements.visible_to_character_owner.checked=true;f.elements.author_confirmed_extended_canon.checked=false;renderContinuityResult(null);
}
let extendedStoriesCache=[];
async function extendedStories(){
 const d=await call('list_extended_stories');
 extendedStoriesCache=d.stories||[];
 const box=document.querySelector('[data-admin-extended-story-list]');
 const charSelect=document.querySelector('[data-admin-story-character-select]');
 if(charSelect)charSelect.innerHTML='<option value="">Aucune</option>'+charactersCache.map(c=>`<option value="${c.id}">${escapeHtml(c.public_name||'Personnage sans nom')}</option>`).join('');
 const locSelect=document.querySelector('[data-admin-story-location-select]');
 if(locSelect){const old=locSelect.value;locSelect.innerHTML='<option value="">À relier à l’Atlas</option>'+worldLocationsCache.map(l=>`<option value="${l.id}">${escapeHtml(l.name)} · ${escapeHtml(l.location_type)}</option>`).join('');if(old)locSelect.value=old}
 if(!box)return;
 const labels={character_chronicle:'Chronique de personnage',world_chronicle:'Chronique du Monde',quebec_chronicle:'Chronique de Québec',archive:'Archive',fragment:'Fragment',novella:'Novella'};
 box.innerHTML=extendedStoriesCache.map(st=>`<article class="admin-v18-row"><strong>${escapeHtml(st.title||'Chronique sans titre')}</strong><p>${escapeHtml(labels[st.story_type]||st.story_type)} · ${escapeHtml(st.canon_status||'PROVISOIRE')} · ${escapeHtml(st.status||'draft')}</p><p>${st.character_name?`Conscience : ${escapeHtml(st.character_name)} · `:''}${st.region_name?`Région : ${escapeHtml(st.region_name)} · `:''}Ancrage : ${escapeHtml(st.anchor_scope||'UNASSIGNED')}</p><button class="btn btn-secondary btn-small" data-edit-extended-story="${st.id}">Modifier</button></article>`).join('')||'<p>Aucune Chronique du Canon étendu.</p>';
 box.querySelectorAll('[data-edit-extended-story]').forEach(b=>b.addEventListener('click',()=>fillExtendedStoryEditor(extendedStoriesCache.find(x=>x.id===b.dataset.editExtendedStory))));
}
function fillExtendedStoryEditor(st){
 const f=document.querySelector('[data-extended-story-editor]');if(!st||!f)return;
 f.elements.id.value=st.id||'';
 f.elements.published_at.value=st.published_at||'';
 f.elements.story_type.value=st.story_type||'character_chronicle';
 f.elements.character_id.value=st.character_id||'';
 f.elements.title.value=st.title||'';
 f.elements.region_name.value=st.region_name||'';
 f.elements.location_id.value=st.location_id||'';
 f.elements.anchor_scope.value=st.anchor_scope||'UNASSIGNED';
 f.elements.canon_status.value=st.canon_status||'PROVISOIRE';
 f.elements.status.value=st.status||'draft';
 f.elements.audience.value=st.audience||'private';
 const storyZone=zoneForLocation(st.location_id||'');
 f.elements.starts_at.value=toLocalInput(st.starts_at,storyZone);
 f.elements.ends_at.value=toLocalInput(st.ends_at,storyZone);
 f.elements.summary.value=st.summary||'';
 f.elements.content.value=st.content||'';
 f.elements.continuity_json.value=JSON.stringify(st.continuity_data||{},null,2);
 f.elements.visible_to_character_owner.checked=st.visible_to_character_owner!==false;
 f.elements.author_confirmed_extended_canon.checked=false;
 f.scrollIntoView({behavior:'smooth'});
}
function extendedStoryEditor(){
 const f=document.querySelector('[data-extended-story-editor]');if(!f)return;
 f.querySelector('[data-story-reset]')?.addEventListener('click',resetExtendedStoryEditor);
 f.addEventListener('submit',async e=>{
   e.preventDefault();
   let continuity={};try{continuity=JSON.parse(f.elements.continuity_json.value||'{}')}catch{return alert('Le JSON de continuité est invalide.')};
   const storyZone=zoneForLocation(f.elements.location_id.value||'');
   const storyStart=toIso(f.elements.starts_at.value,storyZone),storyEnd=toIso(f.elements.ends_at.value,storyZone);
   if(f.elements.starts_at.value&&!storyStart)return alert('Début invalide pour le fuseau horaire du lieu sélectionné.');
   if(f.elements.ends_at.value&&!storyEnd)return alert('Fin invalide pour le fuseau horaire du lieu sélectionné.');
   const story={
     id:f.elements.id.value||null,
     published_at:f.elements.published_at.value||null,
     story_type:f.elements.story_type.value,
     character_id:f.elements.character_id.value||null,
     title:f.elements.title.value,
     region_name:f.elements.region_name.value,
     location_id:f.elements.location_id.value||null,
     anchor_scope:f.elements.anchor_scope.value,
     canon_status:f.elements.canon_status.value,
     status:f.elements.status.value,
     audience:f.elements.audience.value,
     starts_at:storyStart,
     ends_at:storyEnd,
     summary:f.elements.summary.value,
     content:f.elements.content.value,
     continuity_data:continuity,
     visible_to_character_owner:f.elements.visible_to_character_owner.checked,
     author_confirmed_extended_canon:Boolean(f.elements.author_confirmed_extended_canon.checked)
   };
   try{
     const saved=await call('save_extended_story',{story});
     alert('Chronique enregistrée dans le Canon étendu.');
     f.elements.id.value=saved.story?.id||story.id||'';
     f.elements.published_at.value=saved.story?.published_at||story.published_at||'';
     f.elements.author_confirmed_extended_canon.checked=false;
     await extendedStories();
   }catch(err){if(err.data?.story?.id){f.elements.id.value=err.data.story.id;f.elements.published_at.value=err.data.story.published_at||''}if(err.data?.continuity)renderContinuityResult(err.data.continuity);alert(err.message)}
 });
}

let worldLocationsCache=[],canonEventsCache=[],travelRulesCache=[];
function locationOptions(placeholder='Aucun'){return `<option value="">${escapeHtml(placeholder)}</option>`+worldLocationsCache.map(l=>`<option value="${l.id}">${escapeHtml(l.name)} · ${escapeHtml(l.location_type)}</option>`).join('')}
function refreshWorldSelects(){
 const parent=document.querySelector('[data-world-parent-select]');if(parent){const old=parent.value;parent.innerHTML=locationOptions('Aucun parent');if(old)parent.value=old}
 for(const sel of document.querySelectorAll('[data-event-location-select],[data-event-presence-location]')){const old=sel.value;sel.innerHTML=locationOptions(sel.hasAttribute('data-event-presence-location')?'Lieu de l’événement':'Non normalisé');if(old)sel.value=old}
 const story=document.querySelector('[data-admin-story-location-select]');if(story){const old=story.value;story.innerHTML=locationOptions('À relier à l’Atlas');if(old)story.value=old}
 for(const sel of document.querySelectorAll('[data-travel-from],[data-travel-to]')){const old=sel.value;sel.innerHTML=worldLocationsCache.map(l=>`<option value="${l.id}">${escapeHtml(l.name)} · ${escapeHtml(l.location_type)}</option>`).join('');if(old)sel.value=old}
 const eventSel=document.querySelector('[data-event-presence-event]');if(eventSel){const old=eventSel.value;eventSel.innerHTML=canonEventsCache.map(e=>`<option value="${e.id}">${escapeHtml(e.title)}</option>`).join('');if(old)eventSel.value=old}
 const charSel=document.querySelector('[data-event-presence-character]');if(charSel){const old=charSel.value;charSel.innerHTML=charactersCache.map(c=>`<option value="${c.id}">${escapeHtml(c.public_name||'Personnage sans nom')}</option>`).join('');if(old)charSel.value=old}
}
async function worldContinuity(){
 const d=await call('list_world_continuity');worldLocationsCache=d.locations||[];canonEventsCache=d.events||[];travelRulesCache=d.travel_rules||[];refreshWorldSelects();
 const lbox=document.querySelector('[data-world-location-list]');if(lbox){lbox.innerHTML=worldLocationsCache.map(l=>`<article class="admin-v18-row"><strong>${escapeHtml(l.name)}</strong><p>${escapeHtml(l.location_type)} · ${escapeHtml(l.canon_status)}${l.timezone_name?` · ${escapeHtml(l.timezone_name)}`:''}</p><button class="btn btn-secondary btn-small" data-edit-world-location="${l.id}">Modifier</button></article>`).join('')||'<p>Aucun lieu dans l’Atlas.</p>';lbox.querySelectorAll('[data-edit-world-location]').forEach(b=>b.addEventListener('click',()=>fillWorldLocation(worldLocationsCache.find(x=>x.id===b.dataset.editWorldLocation))))}
 const ebox=document.querySelector('[data-canon-event-list]');if(ebox){ebox.innerHTML=canonEventsCache.map(e=>`<article class="admin-v18-row"><strong>${escapeHtml(e.title)}</strong><p>${escapeHtml(e.classification)} · ${escapeHtml(e.source_scope)} · ${escapeHtml(e.sinjira_world_locations?.name||e.location_name_snapshot||'Lieu non normalisé')}</p><small>${escapeHtml(e.source_reference||'')}</small><button class="btn btn-secondary btn-small" data-edit-canon-event="${e.id}">Modifier</button></article>`).join('')||'<p>Aucun événement canonique.</p>';ebox.querySelectorAll('[data-edit-canon-event]').forEach(b=>b.addEventListener('click',()=>fillCanonEvent(canonEventsCache.find(x=>x.id===b.dataset.editCanonEvent))))}
 const pbox=document.querySelector('[data-event-presence-list]');if(pbox){const rows=canonEventsCache.flatMap(e=>(e.sinjira_canon_event_characters||[]).map(p=>({...p,event_title:e.title})));pbox.innerHTML=rows.map(p=>`<article class="admin-v18-row"><strong>${escapeHtml(p.characters?.public_name||'Personnage')} · ${escapeHtml(p.event_title)}</strong><p>${escapeHtml(p.certainty||'confirmed')} · ${escapeHtml(p.location_name_snapshot||'Lieu hérité / Atlas')}</p><button class="btn btn-secondary btn-small" data-remove-event-presence="${p.event_id}" data-character="${p.character_id}">Retirer</button></article>`).join('')||'<p>Aucune présence canonique enregistrée.</p>';pbox.querySelectorAll('[data-remove-event-presence]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('Retirer cette présence du Calendrier-Monde?'))return;try{await call('remove_canon_event_character',{event_id:b.dataset.removeEventPresence,character_id:b.dataset.character});await worldContinuity()}catch(e){alert(e.message)}}))}
 const tbox=document.querySelector('[data-travel-rule-list]');if(tbox){tbox.innerHTML=travelRulesCache.map(r=>`<article class="admin-v18-row"><strong>${escapeHtml(r.from?.name||'Lieu')} → ${escapeHtml(r.to?.name||'Lieu')}</strong><p>${escapeHtml(String(r.minimum_minutes))} min · ${escapeHtml(r.travel_mode||'unspecified')} · ${escapeHtml(r.canon_status||'PROVISOIRE')}</p><small>${escapeHtml(r.source_reference||'Source à compléter')}</small><button class="btn btn-secondary btn-small" data-edit-travel-rule="${r.id}">Modifier</button></article>`).join('')||'<p>Aucune règle de déplacement.</p>';tbox.querySelectorAll('[data-edit-travel-rule]').forEach(b=>b.addEventListener('click',()=>fillTravelRule(travelRulesCache.find(x=>x.id===b.dataset.editTravelRule))))}
 await extendedStories();
}
function fillWorldLocation(l){const f=document.querySelector('[data-world-location-form]');if(!l||!f)return;for(const [k,v] of Object.entries(l)){if(f.elements[k])f.elements[k].value=v??''}f.scrollIntoView({behavior:'smooth'})}
function fillTravelRule(r){const f=document.querySelector('[data-travel-rule-form]');if(!r||!f)return;f.elements.id.value=r.id||'';f.elements.from_location_id.value=r.from_location_id||'';f.elements.to_location_id.value=r.to_location_id||'';f.elements.minimum_minutes.value=r.minimum_minutes??'';f.elements.travel_mode.value=r.travel_mode||'';f.elements.canon_status.value=r.canon_status||'PROVISOIRE';const zone=zoneForLocation(r.from_location_id||'');f.elements.valid_from.value=toLocalInput(r.valid_from,zone);f.elements.valid_until.value=toLocalInput(r.valid_until,zone);f.elements.source_reference.value=r.source_reference||'';f.elements.notes.value=r.notes||'';f.scrollIntoView({behavior:'smooth'})}
function fillCanonEvent(e){const f=document.querySelector('[data-canon-event-form]');if(!e||!f)return;f.elements.id.value=e.id||'';f.elements.title.value=e.title||'';f.elements.event_key.value=e.event_key||'';f.elements.source_scope.value=e.source_scope||'LIVRES_1_12';f.elements.classification.value=e.classification||'PROVISOIRE';f.elements.location_id.value=e.location_id||'';f.elements.timezone_name.value=e.timezone_name||zoneForLocation(e.location_id||'');const eventZone=f.elements.timezone_name.value;f.elements.starts_at.value=toLocalInput(e.starts_at,eventZone);f.elements.ends_at.value=toLocalInput(e.ends_at,eventZone);f.elements.source_reference.value=e.source_reference||'';f.elements.summary.value=e.summary||'';f.elements.public_safe.checked=e.public_safe===true;f.scrollIntoView({behavior:'smooth'})}
function bindWorldContinuity(){
 const lf=document.querySelector('[data-world-location-form]');lf?.querySelector('[data-world-location-reset]')?.addEventListener('click',()=>{lf.reset();lf.elements.id.value=''});lf?.addEventListener('submit',async e=>{e.preventDefault();const location={id:lf.elements.id.value||null,name:lf.elements.name.value,slug:lf.elements.slug.value,location_type:lf.elements.location_type.value,parent_id:lf.elements.parent_id.value||null,timezone_name:lf.elements.timezone_name.value,canon_status:lf.elements.canon_status.value,latitude:lf.elements.latitude.value,longitude:lf.elements.longitude.value,source_reference:lf.elements.source_reference.value,notes:lf.elements.notes.value};try{await call('save_world_location',{location});lf.reset();lf.elements.id.value='';await worldContinuity()}catch(err){alert(err.message)}});
 const ef=document.querySelector('[data-canon-event-form]');ef?.querySelector('[data-canon-event-reset]')?.addEventListener('click',()=>{ef.reset();ef.elements.id.value=''});ef?.elements.location_id?.addEventListener('change',()=>{const z=zoneForLocation(ef.elements.location_id.value);if(z)ef.elements.timezone_name.value=z});ef?.addEventListener('submit',async e=>{e.preventDefault();const eventZone=String(ef.elements.timezone_name.value||zoneForLocation(ef.elements.location_id.value)||'').trim();const eventStart=toIso(ef.elements.starts_at.value,eventZone),eventEnd=toIso(ef.elements.ends_at.value,eventZone);if(ef.elements.starts_at.value&&!eventStart)return alert('Début invalide pour le fuseau de cet événement.');if(ef.elements.ends_at.value&&!eventEnd)return alert('Fin invalide pour le fuseau de cet événement.');const event={id:ef.elements.id.value||null,title:ef.elements.title.value,event_key:ef.elements.event_key.value,source_scope:ef.elements.source_scope.value,classification:ef.elements.classification.value,location_id:ef.elements.location_id.value||null,timezone_name:eventZone,starts_at:eventStart,ends_at:eventEnd,source_reference:ef.elements.source_reference.value,summary:ef.elements.summary.value,public_safe:ef.elements.public_safe.checked};try{await call('save_canon_event',{event});ef.reset();ef.elements.id.value='';await worldContinuity()}catch(err){alert(err.message)}});
 const pf=document.querySelector('[data-event-presence-form]');pf?.addEventListener('submit',async e=>{e.preventDefault();const event=canonEventsCache.find(x=>x.id===pf.elements.event_id.value);const locationId=pf.elements.location_id.value||event?.location_id||null;const presenceZone=zoneForLocation(locationId)||event?.timezone_name||'';const presenceStart=toIso(pf.elements.starts_at.value,presenceZone)||event?.starts_at||null,presenceEnd=toIso(pf.elements.ends_at.value,presenceZone)||event?.ends_at||null;if(pf.elements.starts_at.value&&!toIso(pf.elements.starts_at.value,presenceZone))return alert('Début de présence invalide pour le fuseau du lieu.');if(pf.elements.ends_at.value&&!toIso(pf.elements.ends_at.value,presenceZone))return alert('Fin de présence invalide pour le fuseau du lieu.');const presence={event_id:pf.elements.event_id.value,character_id:pf.elements.character_id.value,location_id:locationId,location_name_snapshot:worldLocationsCache.find(x=>x.id===locationId)?.name||event?.location_name_snapshot||'',certainty:pf.elements.certainty.value,starts_at:presenceStart,ends_at:presenceEnd,role:pf.elements.role.value,source_reference:pf.elements.source_reference.value||event?.source_reference||''};try{await call('save_canon_event_character',{presence});pf.reset();await worldContinuity()}catch(err){alert(err.message)}});
 const tf=document.querySelector('[data-travel-rule-form]');tf?.querySelector('[data-travel-rule-reset]')?.addEventListener('click',()=>{tf.reset();tf.elements.id.value=''});tf?.addEventListener('submit',async e=>{e.preventDefault();const zone=zoneForLocation(tf.elements.from_location_id.value);const validFrom=toIso(tf.elements.valid_from.value,zone),validUntil=toIso(tf.elements.valid_until.value,zone);if(tf.elements.valid_from.value&&!validFrom)return alert('Début de validité invalide pour le fuseau du lieu de départ.');if(tf.elements.valid_until.value&&!validUntil)return alert('Fin de validité invalide pour le fuseau du lieu de départ.');const rule={id:tf.elements.id.value||null,from_location_id:tf.elements.from_location_id.value,to_location_id:tf.elements.to_location_id.value,minimum_minutes:tf.elements.minimum_minutes.value,travel_mode:tf.elements.travel_mode.value,canon_status:tf.elements.canon_status.value,valid_from:validFrom,valid_until:validUntil,source_reference:tf.elements.source_reference.value,notes:tf.elements.notes.value};try{await call('save_world_travel_rule',{rule});tf.reset();tf.elements.id.value='';await worldContinuity()}catch(err){alert(err.message)}});
}

(async()=>{try{editor();extendedStoryEditor();bindWorldContinuity();ensureNotificationsUi();await Promise.all([dashboard(),comments(),submissions(),canonOverview(),auditLog(),notifications()]);await characters();await worldContinuity()}catch(e){console.error('[SINJIRA admin V18]',e)}})();
