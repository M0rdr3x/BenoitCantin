import {getSupabase,requireUser,escapeHtml,setStatus,roleLabel,projectStatusLabel,prepareDocumentWindow,closeDocumentWindow,navigateDocumentWindow,safeLibraryRoute,safeLibraryCover} from './sinjira-supabase.js';

const page=document.body.dataset.libraryPage||'',status=document.querySelector('[data-library-status]');
let user=null,owner=false,admin=false;
const rows=v=>Array.isArray(v)?v:[];
// Les seuls niveaux autorisés par le schéma SQL project_access.
function verifiedProjectAccess(grants,now=Date.now()){
  return new Map(rows(grants).filter(g=>{
    if(!g?.project_id||!['player','tester'].includes(g.access_level))return false;
    if(!g.expires_at)return true;
    const end=Date.parse(g.expires_at);
    return Number.isFinite(end)&&end>now;
  }).map(g=>[g.project_id,g]));
}
function projectIsOpen(project,access,isOwner=owner,isAdmin=admin){
  return Boolean(isOwner||isAdmin||project?.visibility==='public'
    ||project?.visibility==='account'||access.get(project?.id));
}
function internalProjectPath(raw){
  return safeLibraryRoute(raw);
}
function cover(p){
  const fallback=p.slug==='fracture-du-reseau-mere'
    ?'/assets/media/sinjira-fracture-du-reseau-mere-officiel.webp'
    :p.slug==='reseau-mere-resistance'
      ?'/assets/media/sinjira-reseau-mere-resistance-officiel.webp'
      :'/assets/media/sinjira-emblem.webp';
  return safeLibraryCover(p.cover_url,fallback);
}
async function openDoc(id,button){
  if(button?.disabled)return;
  if(button)button.disabled=true;
  // Réserver l'onglet synchroniquement lors du clic : après await, les
  // bloqueurs de fenêtres peuvent empêcher l'ouverture du document.
  const tab=prepareDocumentWindow();
  setStatus(status,'Vérification de vos droits et préparation du document…','info');
  try{
    const {data,error}=await getSupabase().functions.invoke('get-document-url',{body:{document_id:id}});
    if(error||!data?.ok||!data?.url){
      closeDocumentWindow(tab);
      setStatus(status,data?.error||error?.message||'Accès impossible.','error');
      return;
    }
    if(!navigateDocumentWindow(tab,data.url)){
      setStatus(status,'Le serveur a fourni un lien de document invalide.','error');
      return;
    }
    setStatus(status,data.protected?'Document ouvert avec un lien temporaire sécurisé.':'Document ouvert.','success');
  }catch{
    closeDocumentWindow(tab);
    setStatus(status,'Le document ne peut pas être ouvert pour le moment.','error');
  }finally{
    if(button)button.disabled=false;
  }
}
function bindDocs(root=document){root.querySelectorAll('[data-open-document]').forEach(b=>b.addEventListener('click',()=>openDoc(b.dataset.openDocument,b)))}
async function accessMap(){
  const {data,error}=await getSupabase().from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id);
  if(error)throw new Error('Les droits du compte sont temporairement indisponibles.');
  return verifiedProjectAccess(data);
}
async function library(){
  const s=getSupabase(),[pr,dr,rr,access]=await Promise.all([
    s.from('projects').select('*').order('sort_order'),
    s.from('documents').select('id,project_id,title,version,document_type,access_level').eq('status','approved'),
    s.from('access_requests').select('project_id,requested_level,status').eq('user_id',user.id).eq('status','pending'),
    accessMap()
  ]);
  if(pr.error||dr.error||rr.error)throw new Error('Les ressources du compte ne sont pas vérifiables.');
  const projects=rows(pr.data),docs=rows(dr.data),pending=new Map(rows(rr.data).map(x=>[x.project_id,x])),box=document.querySelector('[data-project-library]');
  box.innerHTML=projects.map(p=>{
    const a=access.get(p.id),allowed=projectIsOpen(p,access),tester=owner||admin||a?.access_level==='tester',pd=allowed?docs.filter(d=>d.project_id===p.id):[],waiting=pending.has(p.id),play=allowed?internalProjectPath(p.play_path):'';
    return `<article class="library-project-card"><div class="library-project-art"><img src="${escapeHtml(cover(p))}" alt=""></div><div class="library-project-body"><div class="library-project-meta"><span class="status-badge">${escapeHtml(projectStatusLabel(p.status))}</span>${tester?'<span class="role-chip role-chip--tester">Testeur</span>':''}</div><h2>${escapeHtml(p.name)}</h2><p>${escapeHtml(p.description||'')}</p><div class="library-project-stats"><span>${allowed?`${pd.length} document${pd.length===1?'':'s'} accessible${pd.length===1?'':'s'}`:'Documents sur autorisation'}</span><span>${p.visibility==='restricted'?'Accès restreint':'Inclus avec le compte'}</span></div><div class="hero-actions">${allowed?`<a class="btn btn-primary" href="/compte/projet.html?slug=${encodeURIComponent(p.slug)}">Ouvrir l’espace</a>`:'<span class="role-chip">Projet soumis à autorisation</span>'}${play?`<a class="btn btn-secondary" href="${escapeHtml(play)}">Jouer</a>`:''}${!tester&&p.allow_tester_requests?`<button class="btn btn-secondary" type="button" data-request-tester="${p.id}" ${waiting?'disabled':''}>${waiting?'Demande testeur en attente':'Demander accès testeur'}</button>`:''}</div></div></article>`;
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
  const docRows=rows(data);const filter=document.querySelector('[data-document-filter]'),names=[...new Set(docRows.map(x=>x.projects?.name).filter(Boolean))];
  filter.innerHTML='<option value="">Tous les projets</option>'+names.map(n=>`<option>${escapeHtml(n)}</option>`).join('');
  const list=document.querySelector('[data-documents-list]'),render=()=>{
    const filtered=filter.value?docRows.filter(x=>x.projects?.name===filter.value):docRows;
    list.innerHTML=filtered.map(d=>`<article class="document-card"><div><span class="eyebrow">${escapeHtml(d.projects?.name||'SINJIRA')}</span><h2>${escapeHtml(d.title)}</h2><p>${escapeHtml(d.description||'')}</p></div><div class="document-meta"><span>Version ${escapeHtml(d.version||'—')}</span><span>${escapeHtml(roleLabel(d.access_level))}</span><span>${escapeHtml(d.document_type||'Document')}</span></div><button class="btn btn-primary" type="button" data-open-document="${d.id}">Ouvrir le document</button></article>`).join('')||'<div class="notice"><strong>Aucun document approuvé pour ce filtre.</strong></div>';bindDocs(list);
  };filter.addEventListener('change',render);render();
}
async function project(){
  const slug=new URLSearchParams(location.search).get('slug');
  if(!slug){location.href='/compte/bibliotheque.html';return}
  const s=getSupabase(),[{data:p,error},{data:access,error:accessError}]=await Promise.all([
    s.from('projects').select('*').eq('slug',slug).maybeSingle(),
    s.from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id)
  ]);
  if(error||!p){setStatus(status,'Projet introuvable ou non accessible.','error');return}
  document.querySelector('[data-project-name]').textContent=p.name;
  document.querySelector('[data-project-description]').textContent=p.description||'';
  document.querySelector('[data-project-status]').textContent=projectStatusLabel(p.status);
  const img=document.querySelector('[data-project-cover]');img.src=cover(p);img.alt=`Visuel de ${p.name}`;
  const accessMap=verifiedProjectAccess(accessError?[]:access);
  const grant=accessMap.get(p.id),allowed=projectIsOpen(p,accessMap);
  document.querySelector('[data-project-role]').textContent=owner?'Propriétaire confirmé'
    :admin?'Administrateur confirmé':grant?.access_level==='tester'?'Testeur approuvé'
    :grant?.access_level==='player'?'Joueur approuvé'
    :allowed?(p.visibility==='public'?'Projet public':'Inclus avec le compte')
    :'Accès restreint · non attribué';
  const publicPath=internalProjectPath(p.public_path);
  const playPath=allowed?internalProjectPath(p.play_path):'';
  document.querySelector('[data-project-actions]').innerHTML=
    `${publicPath?`<a class="btn btn-secondary" href="${escapeHtml(publicPath)}">Page publique</a>`:''}`
    +`${playPath?`<a class="btn btn-primary" href="${escapeHtml(playPath)}">Jouer</a>`:''}`;
  if(!allowed){
    document.querySelector('[data-project-documents]').innerHTML='<p>Documents sur autorisation. Aucun accès privé confirmé.</p>';
    document.querySelector('[data-project-playtests]').innerHTML='<p>Playtests non accessibles sans droit confirmé.</p>';
    setStatus(status,accessError?'Autorisation temporairement non vérifiable.':'Ce projet nécessite une autorisation.','info');
    return;
  }
  const {data:docs,error:documentsError}=await s.from('documents').select('id,title,description,version,document_type,access_level').eq('project_id',p.id).eq('status','approved').order('sort_order');
  const dl=document.querySelector('[data-project-documents]');
  dl.innerHTML=documentsError?'<p>Les documents ne sont pas vérifiables pour le moment.</p>'
    :rows(docs).map(d=>`<article class="document-row"><div><strong>${escapeHtml(d.title)}</strong><span>${escapeHtml(d.description||'')}</span></div><div class="document-row-meta"><small>v${escapeHtml(d.version||'—')}</small><small>${escapeHtml(roleLabel(d.access_level))}</small><button class="btn btn-secondary btn-small" type="button" data-open-document="${d.id}">Ouvrir</button></div></article>`).join('')||'<p>Aucun document approuvé accessible.</p>';
  if(!documentsError)bindDocs(dl);
  const {data:pts,error:playtestsError}=await s.from('playtests').select('id,title,description,status,starts_at,ends_at,max_participants').eq('project_id',p.id).in('status',['open','active']).order('starts_at');
  document.querySelector('[data-project-playtests]').innerHTML=playtestsError
    ?'<p>Les playtests sont temporairement indisponibles.</p>'
    :rows(pts).map(x=>`<article class="playtest-card"><span class="status-badge">${x.status==='active'?'En cours':'Ouvert'}</span><h3>${escapeHtml(x.title)}</h3><p>${escapeHtml(x.description||'')}</p><a class="btn btn-secondary" href="/compte/playtests.html#${encodeURIComponent(x.id)}">Voir le playtest</a></article>`).join('')||'<p>Aucun playtest ouvert.</p>';
}
async function playtests(){
  const s=getSupabase(),[pr,mr]=await Promise.all([
    s.from('playtests').select('id,title,description,status,starts_at,ends_at,max_participants,required_access,projects(name,slug)').in('status',['open','active']).order('starts_at'),
    s.from('playtest_participants').select('playtest_id,status').eq('user_id',user.id)
  ]),pts=rows(pr.data),mine=rows(mr.data),map=new Map(mine.map(x=>[x.playtest_id,x.status])),list=document.querySelector('[data-playtests-list]');
  list.innerHTML=pts.map(x=>{const m=map.get(x.id);return `<article class="account-game-card" id="${x.id}"><div class="account-game-card-top"><span class="status-badge">${x.status==='active'?'En cours':'Candidatures ouvertes'}</span><span>${escapeHtml(x.projects?.name||'')}</span></div><h2>${escapeHtml(x.title)}</h2><p>${escapeHtml(x.description||'')}</p><p><strong>Accès requis :</strong> ${escapeHtml(roleLabel(x.required_access||'tester'))}</p><div class="hero-actions">${m?`<span class="role-chip">${escapeHtml({applied:'Candidature envoyée',approved:'Approuvé',refused:'Refusé',completed:'Complété'}[m]||m)}</span>`:`<button class="btn btn-primary" type="button" data-apply-playtest="${x.id}">Poser ma candidature</button>`}</div></article>`}).join('')||'<div class="notice"><strong>Aucun playtest ouvert.</strong></div>';
  list.querySelectorAll('[data-apply-playtest]').forEach(b=>b.addEventListener('click',async()=>{const msg=prompt('Message de candidature (facultatif).')||'';const {error}=await s.from('playtest_participants').insert({playtest_id:b.dataset.applyPlaytest,user_id:user.id,status:'applied',application_message:msg.slice(0,1500)});if(error){setStatus(status,error.message,'error');return}b.outerHTML='<span class="role-chip">Candidature envoyée</span>';setStatus(status,'Candidature transmise.','success')}));
}
(async()=>{
  user=await requireUser();
  try{
    if(page==='library'||page==='project'){
      const s=getSupabase(),[ow,ad]=await Promise.all([
        s.rpc('is_sinjira_owner',{p_user_id:user.id}),
        s.rpc('is_sinjira_admin',{p_user_id:user.id})
      ]);
      owner=!ow.error&&ow.data===true;
      admin=!ad.error&&ad.data===true;
      if(ow.error||ad.error)setStatus(status,'Certains rôles ne peuvent pas être vérifiés. Les droits privés restent fermés sans confirmation.','info');
    }
    if(page==='library')await library();
    else if(page==='documents')await documents();
    else if(page==='project')await project();
    else if(page==='playtests')await playtests();
  }catch(e){setStatus(status,e?.message||'Une erreur est survenue.','error')}
})();
