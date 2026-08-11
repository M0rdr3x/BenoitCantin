import {getSupabase,requireUser,escapeHtml,setStatus} from './sinjira-supabase.js';

const status=document.querySelector('[data-admin-status]');
let projects=[];

async function requireSinjiraAdmin(){
  const s=getSupabase();
  const {data:{user},error:userError}=await s.auth.getUser();
  if(userError||!user){
    location.replace('/compte/connexion.html?next=/Admin/sinjira/');
    throw new Error('AUTH_REQUIRED');
  }
  const {data:isAdmin,error}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});
  if(error||!isAdmin){
    location.replace('/compte/index.html');
    throw new Error('ADMIN_REQUIRED');
  }
  return user;
}

function adminAvatarUrl(path){
  if(!path) return '/assets/media/sinjira-emblem.webp';
  const {data}=getSupabase().storage.from('sinjira-avatars').getPublicUrl(path);
  return data?.publicUrl||'/assets/media/sinjira-emblem.webp';
}

async function call(action,extra={}){
  const {data,error}=await getSupabase().functions.invoke('admin-console',{body:{action,...extra}});
  if(error||!data?.ok)throw new Error(data?.error||error?.message||'Erreur administration');
  return data;
}
async function callReports(action,extra={}){
  const {data,error}=await getSupabase().functions.invoke('admin-reports',{body:{action,...extra}});
  if(error||!data?.ok)throw new Error(data?.error||error?.message||'Erreur rapports administrateur');
  return data;
}
function tabs(){
  document.querySelectorAll('[data-admin-tab]').forEach(b=>b.addEventListener('click',()=>{
    document.querySelectorAll('[data-admin-tab]').forEach(x=>x.removeAttribute('aria-current'));b.setAttribute('aria-current','page');
    document.querySelectorAll('[data-admin-panel]').forEach(p=>p.hidden=p.dataset.adminPanel!==b.dataset.adminTab);
  }));
}
async function dashboard(){
  const [{dashboard:d},{dashboard:r}]=await Promise.all([call('dashboard'),callReports('dashboard')]);
  const map={
    '[data-admin-users]':d.users,
    '[data-admin-projects]':d.projects,
    '[data-admin-docs]':d.approved_documents,
    '[data-admin-requests]':d.pending_requests,
    '[data-admin-playtests]':d.open_playtests,
    '[data-admin-contributions]':d.contributions,
    '[data-admin-reports]':r.game_reports,
    '[data-admin-active-parties]':r.active_parties,
    '[data-admin-finished-parties]':r.finished_parties
  };
  Object.entries(map).forEach(([s,v])=>{const n=document.querySelector(s);if(n)n.textContent=String(v??0)});
}
async function loadProjects(){
  projects=(await call('list_projects')).projects||[];
  const list=document.querySelector('[data-admin-project-list]');
  list.innerHTML=projects.map(p=>`<article class="admin-management-row"><div><strong>${escapeHtml(p.name)}</strong><span>${escapeHtml(p.slug)} · ${escapeHtml(p.status)} · ${escapeHtml(p.visibility)}</span></div><button class="btn btn-secondary btn-small" data-edit-project="${p.id}">Modifier</button></article>`).join('');
  const opts=projects.map(p=>`<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
  document.querySelectorAll('[data-project-select]').forEach(s=>{const old=s.value;s.innerHTML=opts;if(old)s.value=old});
  list.querySelectorAll('[data-edit-project]').forEach(b=>b.addEventListener('click',()=>{
    const p=projects.find(x=>x.id===b.dataset.editProject),f=document.querySelector('[data-project-form]');if(!p)return;
    Object.entries(p).forEach(([k,v])=>{if(f.elements[k]){if(f.elements[k].type==='checkbox')f.elements[k].checked=!!v;else f.elements[k].value=v??''}});
    f.scrollIntoView({behavior:'smooth'});
  }));
}
function bindProject(){
  const f=document.querySelector('[data-project-form]');
  f.addEventListener('submit',async e=>{e.preventDefault();const fd=new FormData(f),obj=Object.fromEntries(fd.entries());obj.allow_tester_requests=f.elements.allow_tester_requests.checked;
    try{await call('save_project',{project:obj});setStatus(status,'Projet enregistré.','success');f.reset();await loadProjects();await dashboard()}catch(x){setStatus(status,x.message,'error')}})
}
async function loadDocs(){
  const rows=(await call('list_documents')).documents||[],box=document.querySelector('[data-admin-document-list]');
  box.innerHTML=rows.map(d=>`<article class="admin-management-row"><div><strong>${escapeHtml(d.title)}</strong><span>${escapeHtml(d.projects?.name||'')} · v${escapeHtml(d.version)} · ${escapeHtml(d.access_level)} · ${escapeHtml(d.status)}</span></div><div class="admin-row-actions">${d.status!=='approved'?`<button class="btn btn-secondary btn-small" data-doc="${d.id}" data-state="approved">Approuver</button>`:''}${d.status!=='archived'?`<button class="btn btn-secondary btn-small" data-doc="${d.id}" data-state="archived">Archiver</button>`:''}</div></article>`).join('')||'<p>Aucun document.</p>';
  box.querySelectorAll('[data-doc]').forEach(b=>b.addEventListener('click',async()=>{try{await call('set_document_status',{document_id:b.dataset.doc,status:b.dataset.state});await loadDocs();await dashboard()}catch(x){setStatus(status,x.message,'error')}}));
}
function bindUpload(){
  const f=document.querySelector('[data-document-upload-form]');
  f.addEventListener('submit',async e=>{e.preventDefault();const file=f.elements.file.files?.[0],project=projects.find(p=>p.id===f.elements.project_id.value);
    if(!file||!project){setStatus(status,'Choisissez un projet et un fichier.','error');return}
    try{
      setStatus(status,'Préparation du téléversement sécurisé…','info');
      const prep=await call('prepare_document_upload',{document:{project_id:project.id,project_slug:project.slug,title:f.elements.title.value,description:f.elements.description.value,document_type:f.elements.document_type.value,version:f.elements.version.value,access_level:f.elements.access_level.value,sort_order:f.elements.sort_order.value,filename:file.name,mime_type:file.type||'application/octet-stream',file_size_bytes:file.size}});
      const {error}=await getSupabase().storage.from(prep.upload.bucket).uploadToSignedUrl(prep.upload.path,prep.upload.token,file,{contentType:file.type||'application/octet-stream'});
      if(error)throw error;
      await call('finalize_document',{document_id:prep.document.id,status:f.elements.publish_status.value});
      setStatus(status,'Document téléversé.','success');f.reset();await loadDocs();await dashboard();
    }catch(x){setStatus(status,x.message,'error')}
  });
}
async function loadRequests(){
  const d=await call('list_access_requests'),emails=new Map((d.users||[]).map(u=>[u.id,u.email])),box=document.querySelector('[data-admin-request-list]');
  box.innerHTML=(d.requests||[]).map(r=>`<article class="admin-management-row"><div><strong>${escapeHtml(emails.get(r.user_id)||r.user_id)}</strong><span>${escapeHtml(r.projects?.name||'')} · ${escapeHtml(r.requested_level)} · ${escapeHtml(r.status)}</span><p>${escapeHtml(r.message||'')}</p></div>${r.status==='pending'?`<div class="admin-row-actions"><button class="btn btn-primary btn-small" data-request="${r.id}" data-decision="approved">Approuver</button><button class="btn btn-secondary btn-small" data-request="${r.id}" data-decision="refused">Refuser</button></div>`:''}</article>`).join('')||'<p>Aucune demande.</p>';
  box.querySelectorAll('[data-request]').forEach(b=>b.addEventListener('click',async()=>{try{await call('review_access_request',{request_id:b.dataset.request,decision:b.dataset.decision});await loadRequests();await dashboard()}catch(x){setStatus(status,x.message,'error')}}));
}
async function loadUsers(){
  const {data,error}=await getSupabase().functions.invoke('admin-users',{body:{action:'list_users'}});if(error||!data?.ok)throw new Error(data?.error||error?.message||'Impossible de charger les joueurs');const users=data.users||[],box=document.querySelector('[data-admin-user-list]');
  box.innerHTML=users.map(u=>`<article class="admin-user-card"><div class="admin-user-identity"><img class="admin-user-avatar" src="${escapeHtml(adminAvatarUrl(u.avatar_path))}" alt=""><div><strong>${escapeHtml(u.pseudo||u.display_name||u.email||'Joueur')}</strong><span>${escapeHtml(u.email||'')}</span>${u.is_admin?'<span class="role-chip role-chip--admin">Administrateur propriétaire</span>':''}</div></div><div class="role-stack">${(u.access||[]).map(a=>`<span class="role-chip">${escapeHtml(a.projects?.name||'Projet')}: ${escapeHtml(a.access_level)}</span>`).join('')}</div><div class="admin-access-form"><select data-user-project="${u.id}">${projects.map(p=>`<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('')}</select><select data-user-level="${u.id}"><option value="player">Joueur approuvé</option><option value="tester">Testeur</option></select><button class="btn btn-secondary btn-small" data-grant="${u.id}">Accorder</button></div></article>`).join('');
  box.querySelectorAll('[data-grant]').forEach(b=>b.addEventListener('click',async()=>{const id=b.dataset.grant;try{await call('grant_access',{user_id:id,project_id:box.querySelector(`[data-user-project="${id}"]`).value,access_level:box.querySelector(`[data-user-level="${id}"]`).value});setStatus(status,'Accès accordé.','success');await loadUsers()}catch(x){setStatus(status,x.message,'error')}}));
}
async function loadPlaytests(){
  const rows=(await call('list_playtests')).playtests||[],box=document.querySelector('[data-admin-playtest-list]');
  box.innerHTML=rows.map(p=>`<article class="admin-user-card"><div><strong>${escapeHtml(p.title)}</strong><span>${escapeHtml(p.projects?.name||'')} · ${escapeHtml(p.status)}</span></div><div>${(p.playtest_participants||[]).map(x=>`<div class="admin-participant-row"><span>${escapeHtml(x.user_id)} · ${escapeHtml(x.status)}</span>${x.status==='applied'?`<button class="btn btn-secondary btn-small" data-pt="${p.id}" data-user="${x.user_id}" data-state="approved">Approuver</button><button class="btn btn-secondary btn-small" data-pt="${p.id}" data-user="${x.user_id}" data-state="refused">Refuser</button>`:''}</div>`).join('')||'<small>Aucune candidature.</small>'}</div></article>`).join('')||'<p>Aucun playtest.</p>';
  box.querySelectorAll('[data-pt]').forEach(b=>b.addEventListener('click',async()=>{try{await call('review_playtest_participant',{playtest_id:b.dataset.pt,user_id:b.dataset.user,status:b.dataset.state});await loadPlaytests()}catch(x){setStatus(status,x.message,'error')}}));
}
function bindPlaytest(){
  const f=document.querySelector('[data-playtest-form]');f.addEventListener('submit',async e=>{e.preventDefault();try{await call('save_playtest',{playtest:Object.fromEntries(new FormData(f).entries())});setStatus(status,'Playtest enregistré.','success');f.reset();await loadPlaytests();await dashboard()}catch(x){setStatus(status,x.message,'error')}})
}
async function loadExtensions(){
  const d=await call('list_extensions'),box=document.querySelector('[data-admin-extension-list]'),signals=document.querySelector('[data-extension-signals]');
  box.innerHTML=(d.extensions||[]).map(e=>`<article class="admin-management-row"><div><strong>${escapeHtml(e.title)}</strong><span>${escapeHtml(e.projects?.name||'')} · ${escapeHtml(e.status)}</span><p>${escapeHtml(e.description||'')}</p></div></article>`).join('')||'<p>Aucune extension.</p>';
  signals.innerHTML=(d.signals||[]).slice(0,100).map(s=>`<article class="extension-signal"><strong>${escapeHtml(s.game_slug)}</strong>${s.idea?`<p><b>Extension :</b> ${escapeHtml(s.idea)}</p>`:''}${s.favorite?`<p><b>Mécanique appréciée :</b> ${escapeHtml(s.favorite)}</p>`:''}${s.unclear?`<p><b>À clarifier :</b> ${escapeHtml(s.unclear)}</p>`:''}</article>`).join('')||'<p>Aucun signal partagé.</p>';
}
function bindExtension(){
  const f=document.querySelector('[data-extension-form]');f.addEventListener('submit',async e=>{e.preventDefault();const o=Object.fromEntries(new FormData(f).entries());o.is_public=f.elements.is_public.checked;try{await call('save_extension',{extension:o});setStatus(status,'Extension enregistrée.','success');f.reset();await loadExtensions()}catch(x){setStatus(status,x.message,'error')}})
}
function reportModeLabel(v){return v==='solo'?'Solo':v==='duo'?'Duo':v==='multiplayer'?'Multijoueur':(v||'—')}
function reportDate(v){try{return new Date(v).toLocaleString('fr-CA',{dateStyle:'medium',timeStyle:'short'})}catch{return v||'—'}}
async function loadGameReports(){
  const d=await callReports('list_game_reports'),rows=d.reports||[],s=d.summary||{},box=document.querySelector('[data-admin-report-list]'),filter=document.querySelector('[data-report-filter]');
  const counts={
    '[data-report-total]':s.count||0,
    '[data-report-resistance]':s.resistance_wins||0,
    '[data-report-network]':s.network_wins||0,
    '[data-report-ties]':s.ties||0
  };
  Object.entries(counts).forEach(([sel,val])=>{const n=document.querySelector(sel);if(n)n.textContent=String(val)});
  const render=()=>{
    const visible=filter?.value?rows.filter(r=>r.play_mode===filter.value):rows;
    box.innerHTML=visible.map(r=>{
      const f=r.fields||{},who=r.owner?.pseudo||r.owner?.display_name||r.owner?.email||'Compte joueur';
      return `<article class="admin-management-row" style="align-items:flex-start">
        <div style="min-width:0">
          <strong>${escapeHtml(r.party_code||'Partie')}</strong>
          <span>${escapeHtml(reportDate(r.submitted_at))} · ${escapeHtml(reportModeLabel(r.play_mode))} · ${escapeHtml(String(r.human_player_count??'—'))} joueur(s) humain(s) · ${escapeHtml(String(r.round_count??'—'))} rondes</span>
          <p style="margin:.7rem 0 .2rem"><b>Gagnant :</b> ${escapeHtml(f.winner_final||'—')} · <b>Résistance :</b> ${escapeHtml(String(f.total_resistance??'—'))} · <b>Réseau-Mère :</b> ${escapeHtml(String(f.total_network??'—'))}</p>
          <p style="margin:.2rem 0;color:var(--muted)"><b>Rondes :</b> R ${escapeHtml(String(f.rounds_resistance??'—'))} · RM ${escapeHtml(String(f.rounds_network??'—'))} · égalités ${escapeHtml(String(f.rounds_tied??'—'))} · départage ${escapeHtml(f.tiebreak_required||'—')}</p>
          <p style="margin:.2rem 0;color:var(--muted)"><b>Transmis par :</b> ${escapeHtml(who)}${r.owner?.email&&who!==r.owner.email?` · ${escapeHtml(r.owner.email)}`:''}</p>
        </div>
      </article>`;
    }).join('')||'<p>Aucun rapport de fin de partie transmis pour ce filtre.</p>';
  };
  if(filter&&!filter.dataset.bound){filter.dataset.bound='1';filter.addEventListener('change',render)}
  render();
}

async function analytics(){
  const d=(await call('analytics')).analytics||{},box=document.querySelector('[data-admin-analytics]');
  box.innerHTML=Object.entries(d).map(([g,a])=>`<article class="admin-analytics-card"><h3>${escapeHtml(g)}</h3><dl><div><dt>Contributions</dt><dd>${a.count}</dd></div><div><dt>Joueurs moyens</dt><dd>${a.average_players??'—'}</dd></div><div><dt>Durée moyenne</dt><dd>${a.average_duration?`${a.average_duration} min`:'—'}</dd></div><div><dt>Note moyenne</dt><dd>${a.average_rating??'—'}</dd></div></dl></article>`).join('')||'<p>Aucune contribution.</p>';
}
(async()=>{try{await requireSinjiraAdmin();tabs();bindProject();bindUpload();bindPlaytest();bindExtension();await dashboard();await loadProjects();await Promise.all([loadDocs(),loadRequests(),loadUsers(),loadPlaytests(),loadExtensions(),loadGameReports(),analytics()]);setStatus(status,'Administration SINJIRA chargée.','success')}catch(x){if(x?.message!=='AUTH_REQUIRED'&&x?.message!=='ADMIN_REQUIRED')setStatus(status,x.message||'Erreur de chargement de l’administration.','error')}})();
