from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

js_path=ROOT/'assets/js/sinjira-admin-v18.js'
js=js_path.read_text('utf-8')
needle="""async function auditLog(){const d=await call('audit_log'),box=document.querySelector('[data-admin-audit-list]');if(!box)return;box.innerHTML=(d.rows||[]).map(r=>`<div class=\"v19-audit-row\"><strong>${escapeHtml(r.action)}</strong><p>${escapeHtml(r.summary||'')}</p><code>${escapeHtml(r.entity_type||'')} ${escapeHtml(r.entity_id||'')}</code><div class=\"v19-muted\">${escapeHtml(new Date(r.created_at).toLocaleString('fr-CA'))}</div></div>`).join('')||'<p>Aucune action V19 enregistrée.</p>'}

"""
if needle not in js: raise SystemExit('auditLog needle absent')
insert=needle+"""function openAdminTab(name){
 document.querySelectorAll('[data-admin-tab]').forEach(b=>{if(b.dataset.adminTab===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
 document.querySelectorAll('[data-admin-panel]').forEach(p=>{p.hidden=p.dataset.adminPanel!==name});
}
function notificationTarget(n){
 const type=String(n?.notification_type||'').toLowerCase(),entity=String(n?.related_entity_type||'').toLowerCase();
 if(type.includes('character')||entity.includes('character_submission'))return 'fan-characters';
 if(type.includes('tester')||type.includes('access')||entity.includes('access'))return 'access';
 if(type.includes('report')||entity.includes('fracture')||entity.includes('report'))return 'reports';
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

"""
js=js.replace(needle,insert)
old="""(async()=>{try{editor();await Promise.all([dashboard(),comments(),submissions(),characters(),canonOverview(),auditLog()])}catch(e){console.error('[SINJIRA admin V18]',e)}})();"""
new="""(async()=>{try{editor();ensureNotificationsUi();await Promise.all([dashboard(),comments(),submissions(),characters(),canonOverview(),auditLog(),notifications()])}catch(e){console.error('[SINJIRA admin V18]',e)}})();"""
if old not in js: raise SystemExit('init needle absent')
js=js.replace(old,new)
js_path.write_text(js,'utf-8')

ts_path=ROOT/'supabase/functions/admin-sinjira-v18/index.ts'
ts=ts_path.read_text('utf-8')
needle=""" if(a==='audit_log'){const {data,error}=await s.from('admin_audit_log').select('*').order('created_at',{ascending:false}).limit(200);if(error)throw error;return json({ok:true,rows:data||[]})}
"""
if needle not in ts: raise SystemExit('admin audit action needle absent')
insert=""" if(a==='list_notifications'){const {data,error}=await s.from('admin_notifications').select('id,notification_type,title,body,related_user_id,related_entity_type,related_entity_id,read_at,created_at').order('created_at',{ascending:false}).limit(200);if(error)throw error;const rows=data||[];return json({ok:true,notifications:rows,unread:rows.filter((n:any)=>!n.read_at).length})}
 if(a==='mark_notification_read'){const id=String(b.notification_id||'');if(!id)throw new Error('NOTIFICATION_ID_REQUIRED');const {error}=await s.from('admin_notifications').update({read_at:new Date().toISOString()}).eq('id',id);if(error)throw error;await audit(s,user.id,'mark_notification_read','admin_notification',id,'Notification marquée comme lue');return json({ok:true})}
 if(a==='mark_all_notifications_read'){const {error}=await s.from('admin_notifications').update({read_at:new Date().toISOString()}).is('read_at',null);if(error)throw error;await audit(s,user.id,'mark_all_notifications_read','admin_notification','','Toutes les notifications ont été marquées comme lues');return json({ok:true})}
"""+needle

ts=ts.replace(needle,insert)
ts=ts.replace("if(e?.message==='ROMAN1_LOCKED')", "if(e?.message==='NOTIFICATION_ID_REQUIRED')return json({ok:false,error:'Identifiant de notification requis.'},400);if(e?.message==='ROMAN1_LOCKED')")
ts_path.write_text(ts,'utf-8')

html_path=ROOT/'admin/sinjira/index.html'
html=html_path.read_text('utf-8')
if 'sinjira-admin-v18.js?v=18.0' not in html: raise SystemExit('admin cache-buster needle absent')
html=html.replace('sinjira-admin-v18.js?v=18.0','sinjira-admin-v18.js?v=18.51')
html_path.write_text(html,'utf-8')

val_path=ROOT/'scripts/validate_admin_action_contract.py'
val=val_path.read_text('utf-8')
old="""extra_required={'dashboard','list_comments','moderate_comment','list_submissions','create_manual_character','generate_character','audit_log','purge_submission_source','list_characters','canon_overview','save_character'}"""
new="""extra_required={'dashboard','list_comments','moderate_comment','list_submissions','create_manual_character','generate_character','audit_log','purge_submission_source','list_characters','canon_overview','save_character','list_notifications','mark_notification_read','mark_all_notifications_read'}"""
if old not in val: raise SystemExit('validator required-set needle absent')
val=val.replace(old,new)
val=val.replace("need(\"s.from('character_status_events')\" in server,'historique des statuts personnage non branché')", "need(\"s.from('character_status_events')\" in server,'historique des statuts personnage non branché')\nneed(\"s.from('admin_notifications')\" in server,'centre de notifications administrateur non branché')\nneed(\"data-admin-notification-badge\" in client and \"data-admin-notification-list\" in client,'interface de notifications administrateur absente')")
val_path.write_text(val,'utf-8')

print('V24.4.51 patch applied')
