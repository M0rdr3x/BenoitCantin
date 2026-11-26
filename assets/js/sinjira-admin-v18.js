import {createAdminSaveGuard} from './sinjira-admin-save-guard.mjs?v=1.0.1';
import {prepareAdminNavigation,openAdminPanel} from './sinjira-admin-panel-nav.mjs?v=1.0.0';
import {getSupabase,escapeHtml} from './sinjira-supabase.js';
import './v24-admin-health.js';

async function call(action,extra={}){const {data,error}=await getSupabase().functions.invoke('admin-sinjira-v18',{body:{action,...extra}});if(error!==null||data?.ok!==true)throw new Error('Réponse administrative V18 non confirmée');return data}
function setText(sel,v){const n=document.querySelector(sel);if(n)n.textContent=String(v??0)}
async function dashboard(){const d=(await call('dashboard')).dashboard||{};setText('[data-admin-reader-comments]',d.pending_comments);setText('[data-admin-character-submissions]',d.character_submissions);setText('[data-admin-character-review]',d.characters_in_review)}

async function canonOverview(){
  const d=await call('canon_overview'),box=document.querySelector('[data-admin-canon-list]');
  if(!box)return;
  box.innerHTML=(d.contexts||[]).map(c=>`<article class="admin-v18-row"><strong>${escapeHtml(c.title||c.context_key)}</strong><p><b>Statut :</b> ${escapeHtml(c.classification)} · <b>Source :</b> ${escapeHtml(c.source_name||'')} · <b>Version :</b> ${escapeHtml(c.source_version||'')}</p><details><summary>Afficher le contexte privé</summary><pre style="white-space:pre-wrap;overflow:auto">${escapeHtml(JSON.stringify(c.content||{},null,2))}</pre></details></article>`).join('')||'<p>Aucun contexte canonique privé.</p>';
}

async function auditLog(){const d=await call('audit_log'),box=document.querySelector('[data-admin-audit-list]');if(!box)return;box.innerHTML=(d.rows||[]).map(r=>`<div class="v19-audit-row"><strong>${escapeHtml(r.action)}</strong><p>${escapeHtml(r.summary||'')}</p><code>${escapeHtml(r.entity_type||'')} ${escapeHtml(r.entity_id||'')}</code><div class="v19-muted">${escapeHtml(new Date(r.created_at).toLocaleString('fr-CA'))}</div></div>`).join('')||'<p>Aucune action V19 enregistrée.</p>'}

function openAdminTab(name){return openAdminPanel(name);}
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
 prepareAdminNavigation();
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

let charactersCache=[],novelsCache=[],characterGuard,characterRead=0;
async function characters(){
 const request=++characterRead,d=await call('list_characters');
 if(request!==characterRead)return;
 if(!Array.isArray(d.characters)||!Array.isArray(d.novels))throw new Error('Liste des personnages non confirmée');
 charactersCache=d.characters;novelsCache=d.novels;
 const box=document.querySelector('[data-admin-character-list]'),nov=document.querySelector('[data-admin-novel-select]');
 if(nov){
   const previous=nov.value,label=nov.selectedOptions[0]?.textContent;
   nov.replaceChildren(new Option('À attribuer',''));
   for(const n of novelsCache)if(typeof n.id==='string'&&n.id)nov.add(new Option(String(n.title||'Roman'),n.id));
   if(previous&&!novelsCache.some(n=>n.id===previous)){
     const missing=new Option((label||'Roman')+' — indisponible',previous);
     missing.disabled=true;nov.add(missing);
   }
   nov.value=previous;
 }
 if(!box)return;
 box.innerHTML=charactersCache.map(c=>`<article class="admin-v18-row"><strong>${escapeHtml(c.public_name||'Personnage sans nom')}</strong><p>${escapeHtml(c.status)} · ${escapeHtml(c.novel_title||c.novel_note||'Aucun roman attribué')}</p><button class="btn btn-secondary btn-small" type="button" data-edit-character="${escapeHtml(c.id)}">Modifier</button></article>`).join('')||'<p>Aucun personnage.</p>';
 box.querySelectorAll('[data-edit-character]').forEach(b=>b.addEventListener('click',()=>fillEditor(charactersCache.find(c=>c.id===b.dataset.editCharacter))));
}
function enableCharacterFields(f,enabled){
 for(const control of f.elements)if('disabled' in control)control.disabled=!enabled;
}
function fillEditor(c){
 const f=document.querySelector('[data-character-editor]');
 if(!c||!f||!characterGuard?.canReplace())return;
 enableCharacterFields(f,true);
 f.elements.id.value=c.id;f.elements.public_name.value=c.public_name||'';f.elements.status.value=c.status||'author_review';f.elements.canon_status.value=c.canon_status||'PROVISOIRE';f.elements.canon_version.value=c.canon_version||'v1.0';f.elements.public_description.value=c.public_description||'';
 const novel=f.elements.novel_id;
 if(c.novel_id&&!Array.from(novel.options).some(o=>o.value===c.novel_id)){
   const missing=new Option(String(c.novel_title||'Roman')+' — indisponible',c.novel_id);missing.disabled=true;novel.add(missing);
 }
 novel.value=c.novel_id||'';f.elements.novel_note.value=c.novel_note||'';f.elements.visible_to_user.checked=c.visible_to_user!==false;f.elements.bible_json.value=JSON.stringify(c.bible||{},null,2);
 if(f.elements.author_confirmed_canon)f.elements.author_confirmed_canon.checked=false;
 if(f.elements.author_confirmed_retcon)f.elements.author_confirmed_retcon.checked=false;
 f.elements.bible_json.removeAttribute('aria-invalid');
 characterGuard.markClean();
 characterGuard.notice('Personnage sélectionné. Vérifiez les confirmations avant enregistrement.','info');
 f.elements.public_name.focus({preventScroll:true});f.scrollIntoView({behavior:'instant',block:'start'});
}
function editor(){
 const f=document.querySelector('[data-character-editor]');if(!f)return;
 characterGuard=createAdminSaveGuard(f);
 enableCharacterFields(f,false);
 f.addEventListener('submit',async e=>{
   e.preventDefault();
   if(!characterGuard.canStart()||!f.elements.id.value)return;
   let bible;
   const field=f.elements.bible_json;
   field.removeAttribute('aria-invalid');
   try{
     bible=JSON.parse(field.value||'{}');
     if(!bible||typeof bible!=='object'||Array.isArray(bible))throw new Error('INVALID_BIBLE');
   }catch{
     field.setAttribute('aria-invalid','true');
     characterGuard.notice('La Bible doit contenir un objet JSON valide. Corrigez le texte avant d’enregistrer.','error');field.focus();return;
   }
   if(f.elements.canon_status.value==='CANON'&&!f.elements.author_confirmed_canon.checked){
     characterGuard.notice('Confirmez le manuscrit officiel finalisé avant de passer le personnage CANON.','error');f.elements.author_confirmed_canon.focus();return;
   }
   const character={id:f.elements.id.value,public_name:f.elements.public_name.value,status:f.elements.status.value,public_description:f.elements.public_description.value,novel_id:f.elements.novel_id.value||null,novel_note:f.elements.novel_note.value,visible_to_user:f.elements.visible_to_user.checked,canon_status:f.elements.canon_status.value,canon_version:f.elements.canon_version.value,author_confirmed_canon:Boolean(f.elements.author_confirmed_canon?.checked),author_confirmed_retcon:Boolean(f.elements.author_confirmed_retcon?.checked),bible};
   for(const [name,limit] of [['public_name',160],['public_description',8000],['novel_note',500],['canon_version',30]]){
     if(character[name].length>limit){
       characterGuard.notice('Un champ dépasse la longueur autorisée. Réduisez son contenu avant enregistrement.','error');
       f.elements[name].focus();return;
     }
   }
   if(character.novel_id&&!novelsCache.some(n=>n.id===character.novel_id)){
     characterGuard.notice('Le roman sélectionné est indisponible. Choisissez un roman disponible ou À attribuer.','error');f.elements.novel_id.focus();return;
   }
   if(new TextEncoder().encode(JSON.stringify({action:'save_character',character})).byteLength>262144){
     characterGuard.notice('La Bible et les informations dépassent la taille maximale de 256 Kio. Réduisez le contenu avant l’enregistrement.','error');field.focus();return;
   }
   const confirmed=await characterGuard.run(async()=>{const result=await call('save_character',{character});return result.character},
     characters,'Personnage enregistré. Sélectionnez une fiche pour poursuivre.',character.id);
   if(confirmed)enableCharacterFields(f,false);
 });
 f.elements.bible_json.addEventListener('input',()=>f.elements.bible_json.removeAttribute('aria-invalid'));
}

(async()=>{try{editor();ensureNotificationsUi();await Promise.all([dashboard(),comments(),submissions(),characters(),canonOverview(),auditLog(),notifications()])}catch(e){console.error('[SINJIRA admin V18]',e)}})();
