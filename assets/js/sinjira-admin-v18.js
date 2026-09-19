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
let canonSourcesCache=[],storyClaimsCache=[];
function canonSourceLabel(src){if(!src)return '';const bits=[src.book_number?'Livre '+src.book_number:'',src.chapter_reference||'',src.passage_reference||''].filter(Boolean);return (src.title||src.source_key||'Source')+(bits.length?' — '+bits.join(' · '):'')+' · '+(src.source_kind||'source')+' · '+(src.verification_status||'PROVISOIRE')}
function isAuthoritativeCanonSource(src){return !!src&&['VERIFIED','SECRET_AUTEUR'].includes(src.verification_status)&&['roman','bible','author_decision','archive'].includes(src.source_kind)}
function canonSourceOptions(placeholder='À relier',excludeId='',scope='',includeRetired=false,allowSupersededId='',replacementKind='',replacementBook=0,authoritativeOnly=false,allowMetaScope=false){return `<option value="">${escapeHtml(placeholder)}</option>`+canonSourcesCache.filter(src=>src.id!==excludeId&&(!scope||src.scope===scope||(allowMetaScope&&src.scope==='META'))&&(includeRetired||src.verification_status!=='RETIRED')&&(!authoritativeOnly||isAuthoritativeCanonSource(src))&&(!includeRetired||Number(src.usage?.superseded_by||0)===0||src.id===allowSupersededId)&&(!(includeRetired&&replacementKind==='roman'&&src.source_kind==='roman')||Number(src.book_number||0)===Number(replacementBook||0))).map(src=>`<option value="${src.id}">${escapeHtml(canonSourceLabel(src))}</option>`).join('')}
function refreshCanonSourceSelects(excludeSupersedesId=''){
 for(const sel of document.querySelectorAll('[data-canon-source-select],[data-story-claim-source]')){
   const old=sel.value,form=sel.closest('form');
   let authoritativeOnly=false,sourceScope='',allowMetaScope=false;
   if(sel.hasAttribute('data-story-claim-source')){
     authoritativeOnly=form?.elements?.verification_status?.value==='VERIFIED';
     if(form?.elements?.claim_type?.value==='anchor'){
       const story=extendedStoriesCache.find(st=>st.id===form.elements.story_id?.value);
       if(story?.anchor_scope&& !['MULTI_PERIODE','UNASSIGNED'].includes(story.anchor_scope)){
         sourceScope=story.anchor_scope;allowMetaScope=true;
       }
     }
   }else if(form?.matches?.('[data-world-location-form],[data-travel-rule-form]'))authoritativeOnly=form.elements.canon_status?.value==='CANON';
   else if(form?.matches?.('[data-canon-event-form]')){
     authoritativeOnly=['CANON','SECRET_AUTEUR'].includes(form.elements.classification?.value||'');
     sourceScope=form.elements.source_scope?.value||'';allowMetaScope=!!sourceScope;
   }else if(form?.matches?.('[data-event-presence-form]')){
     const event=canonEventsCache.find(e=>e.id===form.elements.event_id?.value);
     authoritativeOnly=['CANON','SECRET_AUTEUR'].includes(event?.classification||'');
     sourceScope=event?.source_scope||'';allowMetaScope=!!sourceScope;
   }
   sel.innerHTML=canonSourceOptions(sel.hasAttribute('data-story-claim-source')?'Choisir une source':'À relier au Registre','',sourceScope,false,'','',0,authoritativeOnly,allowMetaScope);
   if(old&&Array.from(sel.options).some(o=>o.value===old))sel.value=old;
 }
 const form=document.querySelector('[data-canon-source-form]'),sup=document.querySelector('[data-canon-source-supersedes]');
 if(sup){const old=sup.value,scope=form?.elements?.scope?.value||'',kind=form?.elements?.source_kind?.value||'',book=Number(form?.elements?.book_number?.value||0);sup.innerHTML=canonSourceOptions('Aucune',excludeSupersedesId,scope,true,old,kind,book);if(old&&old!==excludeSupersedesId&&Array.from(sup.options).some(o=>o.value===old))sup.value=old}
}
function syncCanonSourceScope(){
 const f=document.querySelector('[data-canon-source-form]');if(!f)return;
 const isRoman=f.elements.source_kind.value==='roman',book=Number(f.elements.book_number.value||0);
 if(isRoman&&book>=1&&book<=14)f.elements.scope.value=book<=12?'LIVRES_1_12':'ORIGINES_13_14';
 if(!f.elements.scope.dataset.authorityLocked)f.elements.scope.disabled=isRoman;
 const sup=f.elements.supersedes_source_id;
 if(sup){
   const research=f.elements.source_kind.value==='research';
   const old=research?'':sup.value,excludeId=f.elements.id.value||'',scope=f.elements.scope.value||'';
   sup.innerHTML=research?'<option value="">Non disponible pour research</option>':canonSourceOptions('Aucune',excludeId,scope,true,old,f.elements.source_kind.value,book);
   if(!research&&old&&old!==excludeId&&Array.from(sup.options).some(o=>o.value===old))sup.value=old;
   sup.disabled=research||sup.dataset.authorityLocked==='1';
 }
}
function setCanonSourceAuthorityLock(src){
 const f=document.querySelector('[data-canon-source-form]');if(!f)return;
 const usage=src?.usage||{},authorityLocked=usage.authority_locked===true,keyLocked=usage.key_locked===true,retirementAllowed=usage.retirement_allowed===true,retirementBlocked=usage.retirement_blocked_references===true;
 if(f.elements.source_key)f.elements.source_key.disabled=keyLocked;
 for(const name of ['source_kind','book_number','chapter_reference','passage_reference','source_version','supersedes_source_id']){
   if(f.elements[name]){
     f.elements[name].disabled=authorityLocked;
     if(name==='supersedes_source_id')f.elements[name].dataset.authorityLocked=authorityLocked?'1':'';
   }
 }
 const verification=f.elements.verification_status;
 if(verification){
   const allStatuses=[['PROVISOIRE','PROVISOIRE'],['VERIFIED','VERIFIED'],['SECRET_AUTEUR','SECRET AUTEUR'],['A_ARBITRER','À ARBITRER'],['RETIRED','RETIRÉE']];
   if(!src){
     verification.innerHTML=allStatuses.filter(([v])=>v!=='RETIRED').map(([v,l])=>`<option value="${v}">${l}</option>`).join('');
     verification.value='PROVISOIRE';verification.disabled=false;
   }else if(authorityLocked){
     const current=src.verification_status||'PROVISOIRE';
     const currentLabel=allStatuses.find(x=>x[0]===current)?.[1]||current;
     verification.innerHTML=`<option value="${escapeHtml(current)}">${escapeHtml(currentLabel)}</option>`+(retirementAllowed&&current!=='RETIRED'?'<option value="RETIRED">RETIRÉE</option>':'');
     verification.value=current;verification.disabled=!retirementAllowed||current==='RETIRED';
   }else{
     const current=src.verification_status||'PROVISOIRE';
     verification.innerHTML=allStatuses.map(([v,l])=>`<option value="${v}">${l}</option>`).join('');
     verification.value=current;verification.disabled=false;
   }
 }
 if(f.elements.scope){f.elements.scope.dataset.authorityLocked=authorityLocked?'1':'';f.elements.scope.disabled=authorityLocked||f.elements.source_kind.value==='roman'}
 const box=document.querySelector('[data-canon-source-usage]');
 if(box){
   if(!src){box.innerHTML='<div class="account-status" data-status-type="info">Nouvelle source : aucune utilisation canonique.</div>';return}
   const refs=Array.isArray(usage.references)?usage.references:[];
   const state=authorityLocked?(retirementAllowed?'Autorité verrouillée · RETIRED disponible':retirementBlocked?'Autorité verrouillée · références à migrer':'Autorité verrouillée'):keyLocked?'Clé stable verrouillée':'Source encore modifiable';
   const retireMessage=retirementAllowed
     ?'<p>Le remplacement vérifié existe et aucune référence directe ne subsiste : RETIRED est maintenant autorisé.</p>'
     :retirementBlocked
       ?'<p>Le remplacement vérifié existe, mais '+escapeHtml(String(usage.direct_references||0))+' référence(s) directe(s) doivent encore être migrées avant RETIRED.</p>'
       :'';
   const migrateButton=retirementBlocked&&usage.retirement_replacement_id
     ?`<p><button type="button" class="btn btn-secondary btn-small" data-migrate-canon-source data-source-id="${escapeHtml(src.id)}" data-replacement-id="${escapeHtml(usage.retirement_replacement_id)}">Migrer toutes les références vers ${escapeHtml(usage.retirement_replacement_title||'le remplacement')}</button></p>`
     :'';
   box.innerHTML=`<div class="account-status" data-status-type="${authorityLocked?'info':'success'}"><strong>${escapeHtml(state)}</strong><p>${escapeHtml(String(usage.total||0))} utilisation(s), dont ${escapeHtml(String(usage.direct_references||0))} référence(s) directe(s) et ${escapeHtml(String(usage.canonical||0))} canonique(s).</p>${retireMessage}${migrateButton}${refs.length?'<p>'+refs.map(escapeHtml).join(' · ')+'</p>':''}</div>`;
   const migrate=box.querySelector('[data-migrate-canon-source]');
   migrate?.addEventListener('click',async()=>{
     const replacementTitle=usage.retirement_replacement_title||'la source de remplacement';
     if(!confirm(`Migrer atomiquement toutes les références de « ${src.title||src.source_key} » vers « ${replacementTitle} » ? Les Chroniques dépendantes seront retirées de publication et repasseront en PROVISOIRE pour être revalidées.`))return;
     migrate.disabled=true;
     try{
       const result=await call('migrate_canon_source_references',{source_id:src.id,replacement_source_id:usage.retirement_replacement_id});
       await canonProvenance();
       await worldContinuity();
       const updated=canonSourcesCache.find(x=>x.id===src.id);
       if(updated)fillCanonSource(updated);
       const m=result?.migrated||{};
       alert(`Migration terminée : ${Number(m.world_locations||0)} lieu(x), ${Number(m.travel_rules||0)} trajet(s), ${Number(m.events||0)} événement(s), ${Number(m.presences||0)} présence(s) et ${Number(m.claims||0)} fait(s) déplacés. L’ancienne source est maintenant RETIRED automatiquement.`);
     }catch(err){alert(err.message)}finally{migrate.disabled=false}
   });
 }
}
function fillCanonSource(src){
 const f=document.querySelector('[data-canon-source-form]');if(!src||!f)return;
 refreshCanonSourceSelects(src.id);
 for(const [k,v] of Object.entries(src)){if(f.elements[k]&&k!=='public_safe')f.elements[k].value=v??''}
 f.elements.public_safe.checked=src.public_safe===true;
 setCanonSourceAuthorityLock(src);syncCanonSourceScope();
 f.scrollIntoView({behavior:'smooth'});
}
function fillStoryClaim(claim){const f=document.querySelector('[data-story-claim-form]');if(!claim||!f)return;f.elements.id.value=claim.id||'';f.elements.story_id.value=claim.story_id||'';f.elements.claim_key.value=claim.claim_key||'';f.elements.claim_type.value=claim.claim_type||'other';f.elements.verification_status.value=claim.verification_status||'PROVISOIRE';f.elements.statement.value=claim.statement||'';f.elements.author_note.value=claim.author_note||'';refreshCanonSourceSelects();if(claim.source_id&&Array.from(f.elements.source_id.options).some(o=>o.value===claim.source_id))f.elements.source_id.value=claim.source_id;f.scrollIntoView({behavior:'smooth'})}
function renderStoryClaims(storyId){
 const box=document.querySelector('[data-story-claim-list]'),f=document.querySelector('[data-story-claim-form]');if(f){f.elements.story_id.value=storyId||'';refreshCanonSourceSelects()}if(!box)return;
 const st=extendedStoriesCache.find(x=>x.id===storyId),locked=st?.status==='published',rows=storyClaimsCache.filter(x=>x.story_id===storyId);
 box.innerHTML=rows.map(cl=>{const src=cl.sinjira_canon_sources||canonSourcesCache.find(x=>x.id===cl.source_id);const sourceValid=src&&['VERIFIED','SECRET_AUTEUR'].includes(src.verification_status)&&['roman','bible','author_decision','archive'].includes(src.source_kind);const claimState=cl.verification_status==='VERIFIED'&&!sourceValid?'VERIFIED · SOURCE À REVALIDER':cl.verification_status;return `<article class="admin-v18-row"><strong>${escapeHtml(cl.claim_key)} · ${escapeHtml(cl.claim_type)}</strong><p>${escapeHtml(cl.statement)}</p><small>${escapeHtml(claimState)} · ${escapeHtml(src?canonSourceLabel(src):'Source non reliée')}</small>${locked?'<p><em>Chronique publiée — provenance verrouillée.</em></p>':`<div class="admin-v18-actions"><button class="btn btn-secondary btn-small" data-edit-story-claim="${cl.id}">Modifier</button><button class="btn btn-secondary btn-small" data-remove-story-claim="${cl.id}">Retirer</button></div>`}</article>`}).join('')||'<p>Aucun fait de provenance pour cette Chronique.</p>';
 if(locked)return;
 box.querySelectorAll('[data-edit-story-claim]').forEach(b=>b.addEventListener('click',()=>fillStoryClaim(rows.find(x=>x.id===b.dataset.editStoryClaim))));
 box.querySelectorAll('[data-remove-story-claim]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('Retirer ce fait de provenance?'))return;const wasCanon=extendedStoriesCache.find(x=>x.id===storyId)?.canon_status==='CANON_ETENDU';try{await call('remove_story_claim',{claim_id:b.dataset.removeStoryClaim});await canonProvenance();await extendedStories();syncStoryStateAfterChildEdit(storyId,wasCanon);renderStoryClaims(storyId)}catch(e){alert(e.message)}}));
}
async function canonProvenance(){
 const d=await call('list_canon_provenance');canonSourcesCache=d.sources||[];storyClaimsCache=d.claims||[];refreshCanonSourceSelects();
 const box=document.querySelector('[data-canon-source-list]');if(box){box.innerHTML=canonSourcesCache.map(src=>{const u=src.usage||{};const lock=u.authority_locked?' · autorité verrouillée':u.key_locked?' · clé verrouillée':'';return `<article class="admin-v18-row"><strong>${escapeHtml(src.title||src.source_key)}</strong><p>${escapeHtml(src.source_kind)} · ${escapeHtml(src.scope)} · ${escapeHtml(src.verification_status)}${escapeHtml(lock)}</p><small>${escapeHtml(canonSourceLabel(src))}</small><p>Utilisations : ${escapeHtml(String(u.total||0))} · canoniques : ${escapeHtml(String(u.canonical||0))}</p><button class="btn btn-secondary btn-small" data-edit-canon-source="${src.id}">Modifier</button></article>`}).join('')||'<p>Aucune source canonique enregistrée.</p>';box.querySelectorAll('[data-edit-canon-source]').forEach(b=>b.addEventListener('click',()=>fillCanonSource(canonSourcesCache.find(x=>x.id===b.dataset.editCanonSource))))}
 const storyId=document.querySelector('[data-extended-story-editor]')?.elements?.id?.value||'';if(storyId)renderStoryClaims(storyId);
}
function renderContinuityResult(result){
 const box=document.querySelector('[data-story-continuity-result]');if(!box)return;
 if(!result){box.innerHTML='';return}
 const validation=result.validation||result;
 const metadata=validation.metadata||null;
 const provenance=validation.provenance||null;
 const continuity=validation.continuity||(validation.blocking_conflicts!==undefined||validation.warnings!==undefined?validation:null);
 const conflicts=Number(continuity?.blocking_conflicts||0),warnings=Number(continuity?.warnings||0);
 const unresolved=Number(provenance?.unresolved_claims||0),anchors=Number(provenance?.matching_anchor_claims||0),verified=Number(provenance?.verified_claims||0);
 const ready=validation.ready===true||(!metadata&&!provenance&&conflicts===0&&warnings===0);
 const type=ready?'success':(conflicts>0?'error':'info');
 const title=ready?'Prêt pour la canonisation':'Validation à compléter';
 const metadataText=metadata?`Métadonnées : ancrage ${metadata.anchor_assigned?'OK':'MANQUANT'}, période ${metadata.time_complete?'OK':'INCOMPLÈTE'}, lieu ${metadata.location_assigned?(metadata.location_canon?'CANON':'NON CANON'):'MANQUANT'}, contenu ${metadata.content_present?'OK':'MANQUANT'}.`:'Métadonnées : non incluses dans cet ancien rapport.';
 const provenanceText=provenance?`Provenance : ${verified} fait(s) vérifié(s), ${anchors} ancrage(s) compatible(s), ${unresolved} non résolu(s).`:'Provenance : non incluse dans cet ancien rapport.';
 const continuityText=`Continuité : ${conflicts} conflit(s) bloquant(s), ${warnings} avertissement(s).`;
 box.innerHTML=`<div class="account-status" data-status-type="${type}"><strong>${title}</strong><p>${escapeHtml(metadataText)}</p><p>${escapeHtml(provenanceText)}</p><p>${escapeHtml(continuityText)}</p>${ready?'<p>Métadonnées, provenance et continuité satisfont la prévalidation actuelle.</p>':'<p>Corrigez les éléments signalés avant de demander CANON ÉTENDU.</p>'}</div>`;
}
function resetExtendedStoryEditor(){
 const f=document.querySelector('[data-extended-story-editor]');if(!f)return;
 f.reset();f.elements.id.value='';f.elements.published_at.value='';f.elements.story_type.value='character_chronicle';f.elements.anchor_scope.value='UNASSIGNED';f.elements.canon_status.value='PROVISOIRE';f.elements.status.value='draft';f.elements.audience.value='private';f.elements.location_id.value='';f.elements.continuity_json.value='{}';f.elements.visible_to_character_owner.checked=true;f.elements.author_confirmed_extended_canon.checked=false;f.elements.author_confirmed_publication.checked=false;renderContinuityResult(null);renderStoryPublicationState(null);setStoryPublishedLock(null);const sf=document.querySelector('[data-story-segment-form]');if(sf){sf.reset();sf.elements.id.value='';sf.elements.story_id.value=''}const sb=document.querySelector('[data-story-segment-list]');if(sb)sb.innerHTML='<p>Sélectionnez d’abord une Chronique.</p>';const cf=document.querySelector('[data-story-claim-form]');if(cf){cf.reset();cf.elements.id.value='';cf.elements.story_id.value=''}const cb=document.querySelector('[data-story-claim-list]');if(cb)cb.innerHTML='<p>Sélectionnez d’abord une Chronique.</p>';
}
function renderStoryPublicationState(st){
 const box=document.querySelector('[data-story-publication-state]');if(!box)return;
 if(!st){box.innerHTML='<div class="account-status" data-status-type="info">La publication est une étape distincte de la canonisation.</div>';return}
 if(st.status==='published'){const when=st.published_at?new Date(st.published_at).toLocaleString('fr-CA'):'date inconnue';box.innerHTML='<div class="account-status" data-status-type="success"><strong>Chronique publiée</strong><p>'+escapeHtml(st.audience||'public')+' · '+escapeHtml(when)+'. Retirez-la de publication avant toute modification.</p></div>';return}
 if(st.canon_status==='CANON_ETENDU'){box.innerHTML='<div class="account-status" data-status-type="info"><strong>Canon étendu validé</strong><p>La Chronique peut être publiée après confirmation et nouvelle vérification de provenance + continuité.</p></div>';return}
 box.innerHTML='<div class="account-status" data-status-type="info">La Chronique doit être CANON ÉTENDU avant publication.</div>';
}
function setStoryPublishedLock(st){
 const f=document.querySelector('[data-extended-story-editor]');if(!f)return;
 const locked=st?.status==='published';
 for(const el of f.querySelectorAll('input[name],textarea[name],select[name]')){if(['id','published_at'].includes(el.name))continue;el.disabled=locked}
 const submit=f.querySelector('button[type="submit"]');if(submit)submit.disabled=locked;
 const publish=f.querySelector('[data-story-publish]');if(publish)publish.disabled=locked||!st?.id||st?.canon_status!=='CANON_ETENDU';
 const unpublish=f.querySelector('[data-story-unpublish]');if(unpublish)unpublish.disabled=!locked;
 const check=f.querySelector('[data-story-check]');if(check)check.disabled=!st?.id;
 const sf=document.querySelector('[data-story-segment-form]');if(sf)sf.querySelectorAll('input,textarea,select,button').forEach(el=>el.disabled=locked);const cf=document.querySelector('[data-story-claim-form]');if(cf)cf.querySelectorAll('input,textarea,select,button').forEach(el=>el.disabled=locked);
}
let extendedStoriesCache=[];
async function extendedStories(){
 const d=await call('list_extended_stories');
 extendedStoriesCache=d.stories||[];
 const box=document.querySelector('[data-admin-extended-story-list]');
 const charSelect=document.querySelector('[data-admin-story-character-select]');
 if(charSelect)charSelect.innerHTML='<option value="">Aucune</option>'+charactersCache.map(c=>`<option value="${c.id}">${escapeHtml(c.public_name||'Personnage sans nom')}</option>`).join('');
 const locSelect=document.querySelector('[data-admin-story-location-select]');
 if(locSelect){const old=locSelect.value;locSelect.innerHTML='<option value="">À relier à l’Atlas</option>'+worldLocationsCache.map(l=>`<option value="${l.id}">${escapeHtml(l.name)} · ${escapeHtml(l.location_type)} · ${escapeHtml(l.canon_status||'PROVISOIRE')}</option>`).join('');if(old)locSelect.value=old}
 if(!box)return;
 const labels={character_chronicle:'Chronique de personnage',world_chronicle:'Chronique du Monde',quebec_chronicle:'Chronique de Québec',archive:'Archive',fragment:'Fragment',novella:'Novella'};
 box.innerHTML=extendedStoriesCache.map(st=>`<article class="admin-v18-row"><strong>${escapeHtml(st.title||'Chronique sans titre')}</strong><p>${escapeHtml(labels[st.story_type]||st.story_type)} · ${escapeHtml(st.canon_status||'PROVISOIRE')} · ${escapeHtml(st.status||'draft')}</p><p>${st.character_name?`Conscience : ${escapeHtml(st.character_name)} · `:''}${st.region_name?`Région : ${escapeHtml(st.region_name)} · `:''}Ancrage : ${escapeHtml(st.anchor_scope||'UNASSIGNED')}</p><button class="btn btn-secondary btn-small" data-edit-extended-story="${st.id}">Modifier</button></article>`).join('')||'<p>Aucune Chronique du Canon étendu.</p>';
 box.querySelectorAll('[data-edit-extended-story]').forEach(b=>b.addEventListener('click',()=>fillExtendedStoryEditor(extendedStoriesCache.find(x=>x.id===b.dataset.editExtendedStory))));
}
function renderStorySegments(storyId){
 const box=document.querySelector('[data-story-segment-list]'),sf=document.querySelector('[data-story-segment-form]');
 if(sf)sf.elements.story_id.value=storyId||'';
 if(!box)return;
 const st=extendedStoriesCache.find(x=>x.id===storyId),locked=st?.status==='published',rows=Array.isArray(st?.sinjira_story_character_presence)?st.sinjira_story_character_presence:[];
 box.innerHTML=rows.map(seg=>`<article class="admin-v18-row"><strong>${escapeHtml(seg.characters?.public_name||'Personnage')} · ${escapeHtml(seg.segment_key||'segment')}</strong><p>${escapeHtml(seg.presence_kind||'scene')} · ${escapeHtml(seg.sinjira_world_locations?.name||seg.location_name||'Lieu non normalisé')} · ${escapeHtml(seg.certainty||'confirmed')}</p><small>${seg.starts_at?escapeHtml(new Date(seg.starts_at).toLocaleString('fr-CA')):'Début à compléter'} → ${seg.ends_at?escapeHtml(new Date(seg.ends_at).toLocaleString('fr-CA')):'Fin à compléter'}</small>${seg.segment_key==='primary'?'<p><em>Segment principal — géré par la fiche de Chronique.</em></p>':locked?'<p><em>Chronique publiée — retirez-la de publication pour modifier ce segment.</em></p>':`<div class="admin-v18-actions"><button class="btn btn-secondary btn-small" data-edit-story-segment="${seg.id}">Modifier</button><button class="btn btn-secondary btn-small" data-remove-story-segment="${seg.id}">Retirer</button></div>`}</article>`).join('')||'<p>Aucun segment. La fiche principale créera automatiquement le segment primary pour une Chronique liée à un personnage.</p>';
 if(locked)return;
 box.querySelectorAll('[data-edit-story-segment]').forEach(b=>b.addEventListener('click',()=>fillStorySegment(rows.find(x=>x.id===b.dataset.editStorySegment))));
 box.querySelectorAll('[data-remove-story-segment]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('Retirer ce segment de continuité?'))return;const wasCanon=extendedStoriesCache.find(x=>x.id===storyId)?.canon_status==='CANON_ETENDU';try{await call('remove_extended_story_segment',{segment_id:b.dataset.removeStorySegment});await extendedStories();syncStoryStateAfterChildEdit(storyId,wasCanon);renderStorySegments(storyId)}catch(e){alert(e.message)}}));
}
function fillStorySegment(seg){const f=document.querySelector('[data-story-segment-form]');if(!seg||!f)return;f.elements.id.value=seg.id||'';f.elements.story_id.value=seg.story_id||'';f.elements.character_id.value=seg.character_id||'';f.elements.segment_key.value=seg.segment_key||'';f.elements.presence_kind.value=seg.presence_kind==='story_span'?'scene':seg.presence_kind||'scene';f.elements.location_id.value=seg.location_id||'';const zone=zoneForLocation(seg.location_id||'');f.elements.starts_at.value=toLocalInput(seg.starts_at,zone);f.elements.ends_at.value=toLocalInput(seg.ends_at,zone);f.elements.certainty.value=seg.certainty||'confirmed';f.elements.source_note.value=seg.source_note||'';f.scrollIntoView({behavior:'smooth'})}
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
 f.elements.author_confirmed_publication.checked=false;
 renderStoryPublicationState(st);
 setStoryPublishedLock(st);
 renderStorySegments(st.id);renderStoryClaims(st.id);
 f.scrollIntoView({behavior:'smooth'});
}
function extendedStoryEditor(){
 const f=document.querySelector('[data-extended-story-editor]');if(!f)return;
 f.querySelector('[data-story-reset]')?.addEventListener('click',resetExtendedStoryEditor);
 f.querySelector('[data-story-check]')?.addEventListener('click',async()=>{
   const storyId=f.elements.id.value;if(!storyId)return alert('Enregistrez d’abord la Chronique.');
   try{const d=await call('check_extended_story_validation',{story_id:storyId});renderContinuityResult(d.validation||d)}catch(err){alert(err.message)}
 });
 f.querySelector('[data-story-publish]')?.addEventListener('click',async()=>{
   const storyId=f.elements.id.value;if(!storyId)return alert('Enregistrez d’abord la Chronique.');
   if(!f.elements.author_confirmed_publication.checked)return alert('Confirmez personnellement la publication avant de continuer.');
   if(!['members','public'].includes(f.elements.audience.value))return alert('Choisissez une audience Membres ou Public avant publication.');
   try{
     const d=await call('publish_extended_story',{story_id:storyId,audience:f.elements.audience.value,author_confirmed_publication:true});
     await extendedStories();const current=extendedStoriesCache.find(x=>x.id===storyId)||d.story;if(current)fillExtendedStoryEditor(current);
     alert('Chronique publiée après nouvelle vérification de provenance et de continuité.');
   }catch(err){if(err.data?.continuity)renderContinuityResult(err.data.continuity);alert(err.message)}
 });
 f.querySelector('[data-story-unpublish]')?.addEventListener('click',async()=>{
   const storyId=f.elements.id.value;if(!storyId)return;
   if(!confirm('Retirer cette Chronique de publication afin de pouvoir la modifier?'))return;
   try{
     const d=await call('unpublish_extended_story',{story_id:storyId,author_confirmed_unpublish:true});
     await extendedStories();const current=extendedStoriesCache.find(x=>x.id===storyId)||d.story;if(current)fillExtendedStoryEditor(current);
     alert('Chronique retirée de publication. Vous pouvez maintenant la modifier.');
   }catch(err){alert(err.message)}
 });
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
     f.elements.id.value=saved.story?.id||story.id||'';
     f.elements.published_at.value=saved.story?.published_at||'';
     f.elements.author_confirmed_extended_canon.checked=false;f.elements.author_confirmed_publication.checked=false;
     await extendedStories();const current=extendedStoriesCache.find(x=>x.id===f.elements.id.value);if(current)fillExtendedStoryEditor(current);
     alert('Chronique enregistrée. La publication reste une étape distincte.');
   }catch(err){
     if(err.data?.story?.id){f.elements.id.value=err.data.story.id;f.elements.published_at.value=err.data.story.published_at||'';await extendedStories();const current=extendedStoriesCache.find(x=>x.id===f.elements.id.value);if(current)fillExtendedStoryEditor(current)}
     if(err.data?.validation)renderContinuityResult(err.data.validation);else if(err.data?.continuity)renderContinuityResult(err.data.continuity);
     alert(err.message);
   }
 });
}

let worldLocationsCache=[],canonEventsCache=[],travelRulesCache=[];
function locationOptions(placeholder='Aucun'){return `<option value="">${escapeHtml(placeholder)}</option>`+worldLocationsCache.map(l=>`<option value="${l.id}">${escapeHtml(l.name)} · ${escapeHtml(l.location_type)} · ${escapeHtml(l.canon_status||'PROVISOIRE')}</option>`).join('')}
function refreshWorldSelects(){
 const parent=document.querySelector('[data-world-parent-select]');if(parent){const old=parent.value;parent.innerHTML=locationOptions('Aucun parent');if(old)parent.value=old}
 for(const sel of document.querySelectorAll('[data-event-location-select],[data-event-presence-location]')){const old=sel.value;sel.innerHTML=locationOptions(sel.hasAttribute('data-event-presence-location')?'Lieu de l’événement':'Non normalisé');if(old)sel.value=old}
 const story=document.querySelector('[data-admin-story-location-select]');if(story){const old=story.value;story.innerHTML=locationOptions('À relier à l’Atlas');if(old)story.value=old}
 const segmentLoc=document.querySelector('[data-story-segment-location]');if(segmentLoc){const old=segmentLoc.value;segmentLoc.innerHTML=locationOptions('À relier à l’Atlas');if(old)segmentLoc.value=old}
 const segmentChar=document.querySelector('[data-story-segment-character]');if(segmentChar){const old=segmentChar.value;segmentChar.innerHTML=charactersCache.map(c=>`<option value="${c.id}">${escapeHtml(c.public_name||'Personnage sans nom')}</option>`).join('');if(old)segmentChar.value=old}
 for(const sel of document.querySelectorAll('[data-travel-from],[data-travel-to]')){const old=sel.value;sel.innerHTML=worldLocationsCache.map(l=>`<option value="${l.id}">${escapeHtml(l.name)} · ${escapeHtml(l.location_type)}</option>`).join('');if(old)sel.value=old}
 const eventSel=document.querySelector('[data-event-presence-event]');if(eventSel){const old=eventSel.value;eventSel.innerHTML=canonEventsCache.map(e=>`<option value="${e.id}">${escapeHtml(e.title)}</option>`).join('');if(old)eventSel.value=old}
 const charSel=document.querySelector('[data-event-presence-character]');if(charSel){const old=charSel.value;charSel.innerHTML=charactersCache.map(c=>`<option value="${c.id}">${escapeHtml(c.public_name||'Personnage sans nom')}</option>`).join('');if(old)charSel.value=old}
}
function setExtendedV25Unavailable(message='Le backend V25 du Canon étendu n’est pas encore déployé. Les fonctions existantes de l’administration restent disponibles.'){
 for(const panel of document.querySelectorAll('[data-admin-panel="extended-stories"],[data-admin-panel="world-continuity"]')){
   panel.querySelectorAll('input,textarea,select,button').forEach(el=>el.disabled=true);
 }
 const sourceForm=document.querySelector('[data-canon-source-form]');if(sourceForm)sourceForm.querySelectorAll('input,textarea,select,button').forEach(el=>el.disabled=true);
 for(const sel of ['[data-admin-extended-story-list]','[data-world-location-list]','[data-canon-event-list]','[data-event-presence-list]','[data-travel-rule-list]','[data-story-segment-list]','[data-story-claim-list]','[data-canon-source-list]']){
   const box=document.querySelector(sel);if(box)box.innerHTML=`<div class="account-status" data-status-type="info">${escapeHtml(message)}</div>`;
 }
}
async function loadExtendedV25Safely(){
 try{await canonProvenance();await worldContinuity();return true}
 catch(error){
   console.info('[SINJIRA admin V25]',error?.message||error);
   setExtendedV25Unavailable();
   return false;
 }
}
async function worldContinuity(){
 const editor=document.querySelector('[data-extended-story-editor]'),currentStoryId=editor?.elements?.id?.value||'',wasCanon=extendedStoriesCache.find(x=>x.id===currentStoryId)?.canon_status==='CANON_ETENDU';
 const d=await call('list_world_continuity');worldLocationsCache=d.locations||[];canonEventsCache=d.events||[];travelRulesCache=d.travel_rules||[];refreshWorldSelects();refreshCanonSourceSelects();
 const lbox=document.querySelector('[data-world-location-list]');if(lbox){lbox.innerHTML=worldLocationsCache.map(l=>`<article class="admin-v18-row"><strong>${escapeHtml(l.name)}</strong><p>${escapeHtml(l.location_type)} · ${escapeHtml(l.canon_status)}${l.timezone_name?` · ${escapeHtml(l.timezone_name)}`:''}</p><button class="btn btn-secondary btn-small" data-edit-world-location="${l.id}">Modifier</button></article>`).join('')||'<p>Aucun lieu dans l’Atlas.</p>';lbox.querySelectorAll('[data-edit-world-location]').forEach(b=>b.addEventListener('click',()=>fillWorldLocation(worldLocationsCache.find(x=>x.id===b.dataset.editWorldLocation))))}
 const ebox=document.querySelector('[data-canon-event-list]');if(ebox){ebox.innerHTML=canonEventsCache.map(e=>`<article class="admin-v18-row"><strong>${escapeHtml(e.title)}</strong><p>${escapeHtml(e.classification)} · ${escapeHtml(e.source_scope)} · ${escapeHtml(e.sinjira_world_locations?.name||e.location_name_snapshot||'Lieu non normalisé')}</p><small>${escapeHtml(e.source_reference||'')}</small><button class="btn btn-secondary btn-small" data-edit-canon-event="${e.id}">Modifier</button></article>`).join('')||'<p>Aucun événement canonique.</p>';ebox.querySelectorAll('[data-edit-canon-event]').forEach(b=>b.addEventListener('click',()=>fillCanonEvent(canonEventsCache.find(x=>x.id===b.dataset.editCanonEvent))))}
 const pbox=document.querySelector('[data-event-presence-list]');if(pbox){const rows=canonEventsCache.flatMap(e=>(e.sinjira_canon_event_characters||[]).map(p=>({...p,event_title:e.title})));pbox.innerHTML=rows.map(p=>`<article class="admin-v18-row"><strong>${escapeHtml(p.characters?.public_name||'Personnage')} · ${escapeHtml(p.event_title)}</strong><p>${escapeHtml(p.certainty||'confirmed')} · ${escapeHtml(p.location_name_snapshot||'Lieu hérité / Atlas')}</p><button class="btn btn-secondary btn-small" data-remove-event-presence="${p.event_id}" data-character="${p.character_id}">Retirer</button></article>`).join('')||'<p>Aucune présence canonique enregistrée.</p>';pbox.querySelectorAll('[data-remove-event-presence]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('Retirer cette présence du Calendrier-Monde?'))return;try{await call('remove_canon_event_character',{event_id:b.dataset.removeEventPresence,character_id:b.dataset.character});await worldContinuity()}catch(e){alert(e.message)}}))}
 const tbox=document.querySelector('[data-travel-rule-list]');if(tbox){tbox.innerHTML=travelRulesCache.map(r=>`<article class="admin-v18-row"><strong>${escapeHtml(r.from?.name||'Lieu')} ${r.bidirectional?'↔':'→'} ${escapeHtml(r.to?.name||'Lieu')}</strong><p>${escapeHtml(String(r.minimum_minutes))} min · ${escapeHtml(r.travel_mode||'unspecified')} · ${escapeHtml(r.canon_status||'PROVISOIRE')}</p><small>${escapeHtml(r.source_reference||'Source à compléter')}</small><button class="btn btn-secondary btn-small" data-edit-travel-rule="${r.id}">Modifier</button></article>`).join('')||'<p>Aucune règle de déplacement.</p>';tbox.querySelectorAll('[data-edit-travel-rule]').forEach(b=>b.addEventListener('click',()=>fillTravelRule(travelRulesCache.find(x=>x.id===b.dataset.editTravelRule))))}
 await extendedStories();
 if(currentStoryId)syncStoryStateAfterChildEdit(currentStoryId,wasCanon);
}
function fillWorldLocation(l){const f=document.querySelector('[data-world-location-form]');if(!l||!f)return;for(const [k,v] of Object.entries(l)){if(f.elements[k])f.elements[k].value=v??''}refreshCanonSourceSelects();if(f.elements.source_id&&l.source_id&&Array.from(f.elements.source_id.options).some(o=>o.value===l.source_id))f.elements.source_id.value=l.source_id;f.scrollIntoView({behavior:'smooth'})}
function fillTravelRule(r){const f=document.querySelector('[data-travel-rule-form]');if(!r||!f)return;f.elements.id.value=r.id||'';f.elements.from_location_id.value=r.from_location_id||'';f.elements.to_location_id.value=r.to_location_id||'';f.elements.minimum_minutes.value=r.minimum_minutes??'';f.elements.travel_mode.value=r.travel_mode||'';f.elements.bidirectional.checked=r.bidirectional!==false;f.elements.canon_status.value=r.canon_status||'PROVISOIRE';const zone=zoneForLocation(r.from_location_id||'');f.elements.valid_from.value=toLocalInput(r.valid_from,zone);f.elements.valid_until.value=toLocalInput(r.valid_until,zone);f.elements.source_reference.value=r.source_reference||'';f.elements.notes.value=r.notes||'';refreshCanonSourceSelects();if(f.elements.source_id&&r.source_id&&Array.from(f.elements.source_id.options).some(o=>o.value===r.source_id))f.elements.source_id.value=r.source_id;f.scrollIntoView({behavior:'smooth'})}
function fillCanonEvent(e){const f=document.querySelector('[data-canon-event-form]');if(!e||!f)return;f.elements.id.value=e.id||'';f.elements.title.value=e.title||'';f.elements.event_key.value=e.event_key||'';f.elements.source_scope.value=e.source_scope||'LIVRES_1_12';f.elements.classification.value=e.classification||'PROVISOIRE';f.elements.location_id.value=e.location_id||'';f.elements.timezone_name.value=e.timezone_name||zoneForLocation(e.location_id||'');const eventZone=f.elements.timezone_name.value;f.elements.starts_at.value=toLocalInput(e.starts_at,eventZone);f.elements.ends_at.value=toLocalInput(e.ends_at,eventZone);f.elements.source_reference.value=e.source_reference||'';f.elements.summary.value=e.summary||'';f.elements.public_safe.checked=e.public_safe===true;refreshCanonSourceSelects();if(f.elements.source_id&&e.source_id&&Array.from(f.elements.source_id.options).some(o=>o.value===e.source_id))f.elements.source_id.value=e.source_id;f.scrollIntoView({behavior:'smooth'})}
function syncStoryStateAfterChildEdit(storyId,wasCanon=false){
 const current=extendedStoriesCache.find(x=>x.id===storyId),editor=document.querySelector('[data-extended-story-editor]');
 if(current&&editor&&editor.elements.id.value===storyId){
   editor.elements.canon_status.value=current.canon_status||'PROVISOIRE';
   editor.elements.status.value=current.status||'author_review';
   editor.elements.audience.value=current.audience||'private';
   editor.elements.published_at.value=current.published_at||'';
   renderStoryPublicationState(current);setStoryPublishedLock(current);
 }
 if(wasCanon&&current?.canon_status!=='CANON_ETENDU')alert('Cette modification touche la continuité ou la provenance : la Chronique est repassée en PROVISOIRE / author_review et doit être prévalidée de nouveau.');
}
function bindStorySegments(){
 const f=document.querySelector('[data-story-segment-form]');if(!f)return;
 f.querySelector('[data-story-segment-reset]')?.addEventListener('click',()=>{const storyId=f.elements.story_id.value;f.reset();f.elements.id.value='';f.elements.story_id.value=storyId});
 f.addEventListener('submit',async e=>{e.preventDefault();const storyId=f.elements.story_id.value;if(!storyId)return alert('Sélectionnez d’abord une Chronique.');const wasCanon=extendedStoriesCache.find(x=>x.id===storyId)?.canon_status==='CANON_ETENDU';const zone=zoneForLocation(f.elements.location_id.value||'');const startsAt=toIso(f.elements.starts_at.value,zone),endsAt=toIso(f.elements.ends_at.value,zone);if(f.elements.starts_at.value&&!startsAt)return alert('Début du segment invalide pour le fuseau du lieu.');if(f.elements.ends_at.value&&!endsAt)return alert('Fin du segment invalide pour le fuseau du lieu.');const segment={id:f.elements.id.value||null,story_id:storyId,character_id:f.elements.character_id.value,segment_key:f.elements.segment_key.value,presence_kind:f.elements.presence_kind.value,location_id:f.elements.location_id.value||null,location_name:worldLocationsCache.find(x=>x.id===f.elements.location_id.value)?.name||'',starts_at:startsAt,ends_at:endsAt,certainty:f.elements.certainty.value,source_note:f.elements.source_note.value};try{await call('save_extended_story_segment',{segment});f.reset();f.elements.id.value='';f.elements.story_id.value=storyId;await extendedStories();syncStoryStateAfterChildEdit(storyId,wasCanon);renderStorySegments(storyId)}catch(err){alert(err.message)}});
}
function bindCanonProvenance(){
 const sf=document.querySelector('[data-canon-source-form]');
 if(sf){setCanonSourceAuthorityLock(null);syncCanonSourceScope()}
 sf?.elements.source_kind?.addEventListener('change',syncCanonSourceScope);
 sf?.elements.book_number?.addEventListener('input',syncCanonSourceScope);
 sf?.querySelector('[data-canon-source-reset]')?.addEventListener('click',()=>{sf.reset();sf.elements.id.value='';for(const el of sf.querySelectorAll('input,textarea,select,button'))el.disabled=false;sf.elements.scope.dataset.authorityLocked='';refreshCanonSourceSelects();setCanonSourceAuthorityLock(null);syncCanonSourceScope()});
 sf?.addEventListener('submit',async e=>{e.preventDefault();const source={id:sf.elements.id.value||null,source_key:sf.elements.source_key.value,source_kind:sf.elements.source_kind.value,scope:sf.elements.scope.value,verification_status:sf.elements.verification_status.value,title:sf.elements.title.value,book_number:sf.elements.book_number.value,chapter_reference:sf.elements.chapter_reference.value,passage_reference:sf.elements.passage_reference.value,source_version:sf.elements.source_version.value,supersedes_source_id:sf.elements.supersedes_source_id.value||null,public_safe:sf.elements.public_safe.checked,notes:sf.elements.notes.value};try{await call('save_canon_source',{source});sf.reset();sf.elements.id.value='';for(const el of sf.querySelectorAll('input,textarea,select,button'))el.disabled=false;sf.elements.scope.dataset.authorityLocked='';await canonProvenance();setCanonSourceAuthorityLock(null);syncCanonSourceScope();await worldContinuity()}catch(err){alert(err.message)}});
 const cf=document.querySelector('[data-story-claim-form]');
 cf?.elements.verification_status?.addEventListener('change',refreshCanonSourceSelects);
 cf?.elements.claim_type?.addEventListener('change',refreshCanonSourceSelects);
 cf?.querySelector('[data-story-claim-reset]')?.addEventListener('click',()=>{const storyId=cf.elements.story_id.value;cf.reset();cf.elements.id.value='';cf.elements.story_id.value=storyId;refreshCanonSourceSelects()});
 cf?.addEventListener('submit',async e=>{e.preventDefault();const storyId=cf.elements.story_id.value;if(!storyId)return alert('Sélectionnez d’abord une Chronique.');const wasCanon=extendedStoriesCache.find(x=>x.id===storyId)?.canon_status==='CANON_ETENDU';const claim={id:cf.elements.id.value||null,story_id:storyId,claim_key:cf.elements.claim_key.value,claim_type:cf.elements.claim_type.value,source_id:cf.elements.source_id.value||null,verification_status:cf.elements.verification_status.value,statement:cf.elements.statement.value,author_note:cf.elements.author_note.value};try{await call('save_story_claim',{claim});cf.reset();cf.elements.id.value='';cf.elements.story_id.value=storyId;await canonProvenance();await extendedStories();syncStoryStateAfterChildEdit(storyId,wasCanon);renderStoryClaims(storyId)}catch(err){alert(err.message)}});
}
function bindWorldContinuity(){
 const lf=document.querySelector('[data-world-location-form]');
 lf?.elements.canon_status?.addEventListener('change',refreshCanonSourceSelects);lf?.querySelector('[data-world-location-reset]')?.addEventListener('click',()=>{lf.reset();lf.elements.id.value=''});lf?.addEventListener('submit',async e=>{e.preventDefault();const location={id:lf.elements.id.value||null,name:lf.elements.name.value,slug:lf.elements.slug.value,location_type:lf.elements.location_type.value,parent_id:lf.elements.parent_id.value||null,timezone_name:lf.elements.timezone_name.value,canon_status:lf.elements.canon_status.value,latitude:lf.elements.latitude.value,longitude:lf.elements.longitude.value,source_id:lf.elements.source_id.value||null,source_reference:lf.elements.source_reference.value,notes:lf.elements.notes.value};try{await call('save_world_location',{location});lf.reset();lf.elements.id.value='';await worldContinuity()}catch(err){alert(err.message)}});
 const ef=document.querySelector('[data-canon-event-form]');
 ef?.elements.classification?.addEventListener('change',refreshCanonSourceSelects);
 ef?.elements.source_scope?.addEventListener('change',refreshCanonSourceSelects);ef?.querySelector('[data-canon-event-reset]')?.addEventListener('click',()=>{ef.reset();ef.elements.id.value=''});ef?.elements.location_id?.addEventListener('change',()=>{const z=zoneForLocation(ef.elements.location_id.value);if(z)ef.elements.timezone_name.value=z});ef?.addEventListener('submit',async e=>{e.preventDefault();const eventZone=String(ef.elements.timezone_name.value||zoneForLocation(ef.elements.location_id.value)||'').trim();const eventStart=toIso(ef.elements.starts_at.value,eventZone),eventEnd=toIso(ef.elements.ends_at.value,eventZone);if(ef.elements.starts_at.value&&!eventStart)return alert('Début invalide pour le fuseau de cet événement.');if(ef.elements.ends_at.value&&!eventEnd)return alert('Fin invalide pour le fuseau de cet événement.');const event={id:ef.elements.id.value||null,title:ef.elements.title.value,event_key:ef.elements.event_key.value,source_scope:ef.elements.source_scope.value,classification:ef.elements.classification.value,location_id:ef.elements.location_id.value||null,timezone_name:eventZone,starts_at:eventStart,ends_at:eventEnd,source_id:ef.elements.source_id.value||null,source_reference:ef.elements.source_reference.value,summary:ef.elements.summary.value,public_safe:ef.elements.public_safe.checked};try{await call('save_canon_event',{event});ef.reset();ef.elements.id.value='';await worldContinuity()}catch(err){alert(err.message)}});
 const pf=document.querySelector('[data-event-presence-form]');
 pf?.elements.event_id?.addEventListener('change',refreshCanonSourceSelects);pf?.addEventListener('submit',async e=>{e.preventDefault();const event=canonEventsCache.find(x=>x.id===pf.elements.event_id.value);const locationId=pf.elements.location_id.value||event?.location_id||null;const presenceZone=zoneForLocation(locationId)||event?.timezone_name||'';const presenceStart=toIso(pf.elements.starts_at.value,presenceZone)||event?.starts_at||null,presenceEnd=toIso(pf.elements.ends_at.value,presenceZone)||event?.ends_at||null;if(pf.elements.starts_at.value&&!toIso(pf.elements.starts_at.value,presenceZone))return alert('Début de présence invalide pour le fuseau du lieu.');if(pf.elements.ends_at.value&&!toIso(pf.elements.ends_at.value,presenceZone))return alert('Fin de présence invalide pour le fuseau du lieu.');const presence={event_id:pf.elements.event_id.value,character_id:pf.elements.character_id.value,location_id:locationId,location_name_snapshot:worldLocationsCache.find(x=>x.id===locationId)?.name||event?.location_name_snapshot||'',certainty:pf.elements.certainty.value,starts_at:presenceStart,ends_at:presenceEnd,role:pf.elements.role.value,source_id:pf.elements.source_id.value||event?.source_id||null,source_reference:pf.elements.source_reference.value||event?.source_reference||''};try{await call('save_canon_event_character',{presence});pf.reset();await worldContinuity()}catch(err){alert(err.message)}});
 const tf=document.querySelector('[data-travel-rule-form]');
 tf?.elements.canon_status?.addEventListener('change',refreshCanonSourceSelects);tf?.querySelector('[data-travel-rule-reset]')?.addEventListener('click',()=>{tf.reset();tf.elements.id.value='';tf.elements.bidirectional.checked=true});tf?.addEventListener('submit',async e=>{e.preventDefault();const zone=zoneForLocation(tf.elements.from_location_id.value);const validFrom=toIso(tf.elements.valid_from.value,zone),validUntil=toIso(tf.elements.valid_until.value,zone);if(tf.elements.valid_from.value&&!validFrom)return alert('Début de validité invalide pour le fuseau du lieu de départ.');if(tf.elements.valid_until.value&&!validUntil)return alert('Fin de validité invalide pour le fuseau du lieu de départ.');const rule={id:tf.elements.id.value||null,from_location_id:tf.elements.from_location_id.value,to_location_id:tf.elements.to_location_id.value,minimum_minutes:tf.elements.minimum_minutes.value,travel_mode:tf.elements.travel_mode.value,bidirectional:tf.elements.bidirectional.checked,canon_status:tf.elements.canon_status.value,valid_from:validFrom,valid_until:validUntil,source_id:tf.elements.source_id.value||null,source_reference:tf.elements.source_reference.value,notes:tf.elements.notes.value};try{await call('save_world_travel_rule',{rule});tf.reset();tf.elements.id.value='';await worldContinuity()}catch(err){alert(err.message)}});
}

(async()=>{try{editor();extendedStoryEditor();bindStorySegments();bindCanonProvenance();bindWorldContinuity();ensureNotificationsUi();await Promise.all([dashboard(),comments(),submissions(),canonOverview(),auditLog(),notifications()]);await characters();await loadExtendedV25Safely()}catch(e){console.error('[SINJIRA admin V18]',e)}})();
