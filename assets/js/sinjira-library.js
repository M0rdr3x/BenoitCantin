import {getSupabase,requireUser,escapeHtml,setStatus,roleLabel,projectStatusLabel} from './sinjira-supabase.js';

const page=document.body.dataset.libraryPage||'',status=document.querySelector('[data-library-status]');
let user=null;
function cover(p){if(p.cover_url)return p.cover_url;if(p.slug==='fracture-du-reseau-mere')return '/assets/media/sinjira-fracture-du-reseau-mere-officiel.png';if(p.slug==='reseau-mere-resistance')return '/assets/media/sinjira-reseau-mere-resistance-officiel.png';return '/assets/media/sinjira-emblem.webp'}
async function openDoc(id){
  setStatus(status,'Préparation du document sécurisé…','info');
  const {data,error}=await getSupabase().functions.invoke('get-document-url',{body:{document_id:id}});
  if(error||!data?.ok||!data?.url){setStatus(status,data?.error||error?.message||'Accès impossible.','error');return}
  window.open(data.url,'_blank','noopener');setStatus(status,data.protected?'Document ouvert avec un lien temporaire sécurisé.':'Document ouvert.','success');
}
function bindDocs(root=document){root.querySelectorAll('[data-open-document]').forEach(b=>b.addEventListener('click',()=>openDoc(b.dataset.openDocument)))}
async function accessMap(){
  const {data=[]}=await getSupabase().from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id);
  return new Map(data.map(x=>[x.project_id,x]));
}
async function library(){
  const s=getSupabase(),[pr,dr,rr,access]=await Promise.all([
    s.from('projects').select('*').order('sort_order'),
    s.from('documents').select('id,project_id,title,version,document_type,access_level').eq('status','approved'),
    s.from('access_requests').select('project_id,requested_level,status').eq('user_id',user.id).eq('status','pending'),
    accessMap()
  ]);
  const projects=pr.data||[],docs=dr.data||[],pending=new Map((rr.data||[]).map(x=>[x.project_id,x])),box=document.querySelector('[data-project-library]');
  box.innerHTML=projects.map(p=>{
    const a=access.get(p.id),tester=a?.access_level==='tester',pd=docs.filter(d=>d.project_id===p.id),waiting=pending.has(p.id);
    return `<article class="library-project-card"><div class="library-project-art"><img src="${escapeHtml(cover(p))}" alt=""></div><div class="library-project-body"><div class="library-project-meta"><span class="status-badge">${escapeHtml(projectStatusLabel(p.status))}</span>${tester?'<span class="role-chip role-chip--tester">Testeur</span>':''}</div><h2>${escapeHtml(p.name)}</h2><p>${escapeHtml(p.description||'')}</p><div class="library-project-stats"><span>${pd.length} document${pd.length===1?'':'s'} accessible${pd.length===1?'':'s'}</span><span>${p.visibility==='restricted'?'Accès restreint':'Inclus avec le compte'}</span></div><div class="hero-actions"><a class="btn btn-primary" href="/compte/projet.html?slug=${encodeURIComponent(p.slug)}">Ouvrir l’espace</a>${p.play_path?`<a class="btn btn-secondary" href="${escapeHtml(p.play_path)}">Jouer</a>`:''}${!tester&&p.allow_tester_requests?`<button class="btn btn-secondary" type="button" data-request-tester="${p.id}" ${waiting?'disabled':''}>${waiting?'Demande testeur en attente':'Demander accès testeur'}</button>`:''}</div></div></article>`;
  }).join('')||'<div class="notice"><strong>Aucun projet disponible.</strong></div>';
  box.querySelectorAll('[data-request-tester]').forEach(b=>b.addEventListener('click',async()=>{
    const message=prompt('Court message pour votre demande (facultatif).')||'';
    const {error}=await s.from('access_requests').insert({user_id:user.id,project_id:b.dataset.requestTester,requested_level:'tester',message:message.slice(0,1500)});
    if(error){setStatus(status,error.message,'error');return}b.disabled=true;b.textContent='Demande testeur en attente';setStatus(status,'Demande transmise à SINJIRA.','success');
  }));
}
async function documents(){
  const s=getSupabase(),{data=[],error}=await s.from('documents').select('id,title,description,version,document_type,access_level,approved_at,projects(name,slug)').eq('status','approved').order('approved_at',{ascending:false});
  if(error){setStatus(status,error.message,'error');return}
  const filter=document.querySelector('[data-document-filter]'),names=[...new Set(data.map(x=>x.projects?.name).filter(Boolean))];
  filter.innerHTML='<option value="">Tous les projets</option>'+names.map(n=>`<option>${escapeHtml(n)}</option>`).join('');
  const list=document.querySelector('[data-documents-list]'),render=()=>{
    const rows=filter.value?data.filter(x=>x.projects?.name===filter.value):data;
    list.innerHTML=rows.map(d=>`<article class="document-card"><div><span class="eyebrow">${escapeHtml(d.projects?.name||'SINJIRA')}</span><h2>${escapeHtml(d.title)}</h2><p>${escapeHtml(d.description||'')}</p></div><div class="document-meta"><span>Version ${escapeHtml(d.version||'—')}</span><span>${escapeHtml(roleLabel(d.access_level))}</span><span>${escapeHtml(d.document_type||'Document')}</span></div><button class="btn btn-primary" type="button" data-open-document="${d.id}">Ouvrir le document</button></article>`).join('')||'<div class="notice"><strong>Aucun document approuvé pour ce filtre.</strong></div>';bindDocs(list);
  };filter.addEventListener('change',render);render();
}
async function project(){
  const slug=new URLSearchParams(location.search).get('slug');if(!slug){location.href='/compte/bibliotheque.html';return}
  const s=getSupabase(),[{data:p,error},{data:access=[]}]=await Promise.all([s.from('projects').select('*').eq('slug',slug).maybeSingle(),s.from('project_access').select('*').eq('user_id',user.id)]);
  if(error||!p){setStatus(status,'Projet introuvable ou non accessible.','error');return}
  document.querySelector('[data-project-name]').textContent=p.name;document.querySelector('[data-project-description]').textContent=p.description||'';document.querySelector('[data-project-status]').textContent=projectStatusLabel(p.status);
  const img=document.querySelector('[data-project-cover]');img.src=cover(p);img.alt=`Visuel de ${p.name}`;
  const a=access.find(x=>x.project_id===p.id);document.querySelector('[data-project-role]').textContent=a?.access_level==='tester'?'Testeur approuvé':p.visibility==='restricted'?'Joueur approuvé':'Compte joueur';
  document.querySelector('[data-project-actions]').innerHTML=`${p.public_path?`<a class="btn btn-secondary" href="${escapeHtml(p.public_path)}">Page publique</a>`:''}${p.play_path?`<a class="btn btn-primary" href="${escapeHtml(p.play_path)}">Jouer</a>`:''}`;
  const {data:docs=[]}=await s.from('documents').select('id,title,description,version,document_type,access_level').eq('project_id',p.id).eq('status','approved').order('sort_order');
  const dl=document.querySelector('[data-project-documents]');dl.innerHTML=docs.map(d=>`<article class="document-row"><div><strong>${escapeHtml(d.title)}</strong><span>${escapeHtml(d.description||'')}</span></div><div class="document-row-meta"><small>v${escapeHtml(d.version||'—')}</small><small>${escapeHtml(roleLabel(d.access_level))}</small><button class="btn btn-secondary btn-small" type="button" data-open-document="${d.id}">Ouvrir</button></div></article>`).join('')||'<p>Aucun document approuvé accessible.</p>';bindDocs(dl);
  const {data:pts=[]}=await s.from('playtests').select('id,title,description,status,starts_at,ends_at,max_participants').eq('project_id',p.id).in('status',['open','active']).order('starts_at');
  document.querySelector('[data-project-playtests]').innerHTML=pts.map(x=>`<article class="playtest-card"><span class="status-badge">${x.status==='active'?'En cours':'Ouvert'}</span><h3>${escapeHtml(x.title)}</h3><p>${escapeHtml(x.description||'')}</p><a class="btn btn-secondary" href="/compte/playtests.html#${encodeURIComponent(x.id)}">Voir le playtest</a></article>`).join('')||'<p>Aucun playtest ouvert.</p>';
}
async function playtests(){
  const s=getSupabase(),[{data:pts=[]},{data:mine=[]}]=await Promise.all([
    s.from('playtests').select('id,title,description,status,starts_at,ends_at,max_participants,required_access,projects(name,slug)').in('status',['open','active']).order('starts_at'),
    s.from('playtest_participants').select('playtest_id,status').eq('user_id',user.id)
  ]),map=new Map(mine.map(x=>[x.playtest_id,x.status])),list=document.querySelector('[data-playtests-list]');
  list.innerHTML=pts.map(x=>{const m=map.get(x.id);return `<article class="account-game-card" id="${x.id}"><div class="account-game-card-top"><span class="status-badge">${x.status==='active'?'En cours':'Candidatures ouvertes'}</span><span>${escapeHtml(x.projects?.name||'')}</span></div><h2>${escapeHtml(x.title)}</h2><p>${escapeHtml(x.description||'')}</p><p><strong>Accès requis :</strong> ${escapeHtml(roleLabel(x.required_access||'tester'))}</p><div class="hero-actions">${m?`<span class="role-chip">${escapeHtml({applied:'Candidature envoyée',approved:'Approuvé',refused:'Refusé',completed:'Complété'}[m]||m)}</span>`:`<button class="btn btn-primary" type="button" data-apply-playtest="${x.id}">Poser ma candidature</button>`}</div></article>`}).join('')||'<div class="notice"><strong>Aucun playtest ouvert.</strong></div>';
  list.querySelectorAll('[data-apply-playtest]').forEach(b=>b.addEventListener('click',async()=>{const msg=prompt('Message de candidature (facultatif).')||'';const {error}=await s.from('playtest_participants').insert({playtest_id:b.dataset.applyPlaytest,user_id:user.id,status:'applied',application_message:msg.slice(0,1500)});if(error){setStatus(status,error.message,'error');return}b.outerHTML='<span class="role-chip">Candidature envoyée</span>';setStatus(status,'Candidature transmise.','success')}));
}
(async()=>{user=await requireUser();try{if(page==='library')await library();else if(page==='documents')await documents();else if(page==='project')await project();else if(page==='playtests')await playtests()}catch(e){setStatus(status,e?.message||'Une erreur est survenue.','error')}})();
