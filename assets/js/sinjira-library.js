import {getSupabase,requireUser,escapeHtml,setStatus,roleLabel,projectStatusLabel} from './sinjira-supabase.js';

const page=document.body.dataset.libraryPage||'',status=document.querySelector('[data-library-status]');
let user=null,owner=false,ownerResolved=true,familyCatalog=false,childMode=false;
const rows=v=>Array.isArray(v)?v:[];
function cover(p){if(p.cover_url)return p.cover_url;if(p.slug==='fracture-du-reseau-mere')return '/assets/media/sinjira-fracture-du-reseau-mere-officiel.webp';if(p.slug==='reseau-mere-resistance')return '/assets/media/sinjira-reseau-mere-resistance-officiel.webp';return '/assets/media/sinjira-emblem.webp'}
async function openDoc(id){
  setStatus(status,'Préparation du document sécurisé…','info');
  const {data,error}=await getSupabase().functions.invoke('get-document-url',{body:{document_id:id}});
  if(error||!data?.ok||!data?.url){setStatus(status,data?.error||error?.message||'Accès impossible.','error');return}
  window.open(data.url,'_blank','noopener');setStatus(status,data.protected?'Document ouvert avec un lien temporaire sécurisé.':'Document ouvert.','success');
}
function bindDocs(root=document){root.querySelectorAll('[data-open-document]').forEach(b=>b.addEventListener('click',()=>openDoc(b.dataset.openDocument)))}
async function accessMap(){
  const {data,error}=await getSupabase().from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id);
  if(error)throw error;
  return new Map(rows(data).map(x=>[x.project_id,x]));
}
async function resolveFractureRight(projects,s){
  const familyProductAccess=familyCatalog&&!childMode;
  const needsCheck=!owner&&!familyProductAccess&&!childMode&&projects.some(p=>p.slug==='fracture-du-reseau-mere');
  if(!needsCheck)return {active:owner||familyProductAccess,verified:true};
  const result=await s.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'});
  return {active:!result.error&&result.data===true,verified:!result.error};
}
async function library(){
  const s=getSupabase(),[pr,dr,rr,access]=await Promise.all([
    s.from('projects').select('*').order('sort_order'),
    s.from('documents').select('id,project_id,title,version,document_type,access_level').eq('status','approved'),
    s.from('access_requests').select('project_id,requested_level,status').eq('user_id',user.id).eq('status','pending'),
    accessMap()
  ]);
  const box=document.querySelector('[data-project-library]');
  if(pr.error||dr.error||rr.error){
    if(box)box.innerHTML='<div class="notice"><strong>Bibliothèque temporairement indisponible.</strong><p>Les accès n’ont pas pu être vérifiés; aucun contenu supplémentaire n’est supposé.</p></div>';
    setStatus(status,'Impossible de vérifier complètement les projets, documents ou demandes. Aucun accès supplémentaire n’a été accordé.','error');
    return;
  }
  const projects=rows(pr.data),docs=rows(dr.data),pending=new Map(rows(rr.data).map(x=>[x.project_id,x]));
  const fractureRight=await resolveFractureRight(projects,s);
  box.innerHTML=projects.map(p=>{
    const a=access.get(p.id),tester=owner||a?.access_level==='tester',pd=docs.filter(d=>d.project_id===p.id).length,waiting=pending.has(p.id);
    const licensedGame=p.slug==='fracture-du-reseau-mere';
    const canPlay=!licensedGame||owner||(fractureRight.verified&&fractureRight.active);
    const licenseAction=licensedGame&&!owner&&!fractureRight.active
      ?`<a class="btn btn-secondary" href="licences.html">${fractureRight.verified?'Activer une licence':'Vérifier mes licences'}</a>`
      :'';
    const roleChip=owner?'Propriétaire':a?.access_level==='tester'?'Testeur':'';
    const visibility=licensedGame&&!owner
      ?(!fractureRight.verified?'Droit de jeu non vérifié':fractureRight.active?'Droit numérique actif':'Droit de jeu requis')
      :p.visibility==='restricted'?'Accès restreint':p.visibility==='account'?'Inclus avec le compte':'Page publique';
    return `<article class="library-project-card"><div class="library-project-art"><img src="${escapeHtml(cover(p))}" alt=""></div><div class="library-project-body"><div class="library-project-meta"><span class="status-badge">${escapeHtml(projectStatusLabel(p.status))}</span>${roleChip?`<span class="role-chip">${escapeHtml(roleChip)}</span>`:''}</div><h2>${escapeHtml(p.name)}</h2><p>${escapeHtml(p.description||'')}</p><div class="library-project-stats"><span>${pd} document${pd===1?'':'s'} accessible${pd===1?'':'s'}</span><span>${escapeHtml(visibility)}</span></div><div class="hero-actions"><a class="btn btn-primary" href="/compte/projet.html?slug=${encodeURIComponent(p.slug)}">Ouvrir l’espace</a>${p.play_path&&canPlay?`<a class="btn btn-secondary" href="${escapeHtml(p.play_path)}">Jouer</a>`:''}${licenseAction}${!tester&&p.allow_tester_requests?`<button class="btn btn-secondary" type="button" data-request-tester="${p.id}" ${waiting?'disabled':''}>${waiting?'Demande testeur en attente':'Demander accès testeur'}</button>`:''}</div></div></article>`;
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
    list.innerHTML=filtered.map(d=>`<article class="document-card"><div><span class="eyebrow">${escapeHtml(d.projects?.name||'SINJIRA')}</span><h2>${escapeHtml(d.title)}</h2><p>${escapeHtml(d.description||'')}</p></div><div class="document-meta"><span>Version ${escapeHtml(d.version||'—')}</span><span>${childMode?'Approuvé 11–12 ans':escapeHtml(roleLabel(d.access_level))}</span><span>${escapeHtml(d.document_type||'Document')}</span></div><button class="btn btn-primary" type="button" data-open-document="${d.id}">Ouvrir le document</button></article>`).join('')||`<div class="notice"><strong>${childMode?'Aucun document approuvé 11–12 ans pour ce filtre.':'Aucun document approuvé pour ce filtre.'}</strong></div>`;bindDocs(list);
  };filter.addEventListener('change',render);render();
}
async function project(){
  const slug=new URLSearchParams(location.search).get('slug');if(!slug){location.href='/compte/bibliotheque.html';return}
  const s=getSupabase(),projectRequest=s.from('projects').select('*').eq('slug',slug).maybeSingle();
  const accessRequest=childMode?Promise.resolve({data:[],error:null}):s.from('project_access').select('*').eq('user_id',user.id);
  const [{data:p,error},{data:access,error:accessError}]=await Promise.all([projectRequest,accessRequest]);
  if(error||!p){setStatus(status,childMode?'Ce projet n’est pas approuvé pour les comptes de 11–12 ans.':'Projet introuvable ou non accessible.','error');return}
  if(accessError&&!childMode)setStatus(status,'Le niveau d’accès au projet n’a pas pu être vérifié. Aucun rôle supplémentaire n’est supposé.','error');
  document.querySelector('[data-project-name]').textContent=p.name;document.querySelector('[data-project-description]').textContent=p.description||'';document.querySelector('[data-project-status]').textContent=projectStatusLabel(p.status);
  const img=document.querySelector('[data-project-cover]');img.src=cover(p);img.alt=`Visuel de ${p.name}`;
  const licensedGame=p.slug==='fracture-du-reseau-mere';
  let productRight=owner,productRightVerified=owner;
  if(licensedGame&&!owner&&!childMode){
    const productResult=await s.rpc('has_sinjira_product',{p_product_slug:p.slug});
    productRightVerified=!productResult.error;
    productRight=productRightVerified&&productResult.data===true;
  }
  const a=rows(access).find(x=>x.project_id===p.id);
  document.querySelector('[data-project-role]').textContent=childMode
    ?'Approuvé 11–12 ans'
    :licensedGame&&!owner
      ?(!productRightVerified?'Droit de jeu non vérifié':productRight?'Droit numérique actif':'Droit de jeu requis')
      :owner?'Propriétaire · catalogue complet':a?.access_level==='tester'?'Testeur approuvé':p.visibility==='restricted'?'Accès privé autorisé':p.visibility==='account'?'Inclus avec le compte':'Page publique';
  const canPlay=!licensedGame||owner||productRight;
  const licenseAction=!childMode&&licensedGame&&!owner&&!productRight
    ?`<a class="btn btn-secondary" href="licences.html">${productRightVerified?'Activer une licence':'Vérifier mes licences'}</a>`
    :'';
  document.querySelector('[data-project-actions]').innerHTML=`${p.public_path?`<a class="btn btn-secondary" href="${escapeHtml(p.public_path)}">Page publique</a>`:''}${!childMode&&p.play_path&&canPlay?`<a class="btn btn-primary" href="${escapeHtml(p.play_path)}">Jouer</a>`:''}${licenseAction}`;
  const {data:docs,error:docsError}=await s.from('documents').select('id,title,description,version,document_type,access_level').eq('project_id',p.id).eq('status','approved').order('sort_order');
  const dl=document.querySelector('[data-project-documents]');
  if(docsError){
    if(dl)dl.innerHTML='<p>Documents temporairement indisponibles : les droits n’ont pas pu être vérifiés.</p>';
    setStatus(status,'Impossible de vérifier les documents du projet.','error');
  }else if(dl)dl.innerHTML=rows(docs).map(d=>`<article class="document-row"><div><strong>${escapeHtml(d.title)}</strong><span>${escapeHtml(d.description||'')}</span></div><div class="document-row-meta"><small>v${escapeHtml(d.version||'—')}</small><small>${childMode?'Approuvé 11–12 ans':escapeHtml(roleLabel(d.access_level))}</small><button class="btn btn-secondary btn-small" type="button" data-open-document="${d.id}">Ouvrir</button></div></article>`).join('')||'<p>Aucun document approuvé accessible.</p>';bindDocs(dl);
  const playtests=document.querySelector('[data-project-playtests]');
  if(childMode){
    if(playtests)playtests.innerHTML='<p>Les playtests ne sont pas disponibles pour les comptes de 11–12 ans.</p>';
    return;
  }
  const {data:pts,error:playtestError}=await s.from('playtests').select('id,title,description,status,starts_at,ends_at,max_participants').eq('project_id',p.id).in('status',['open','active']).order('starts_at');
  if(playtestError){
    if(playtests)playtests.innerHTML='<p>Playtests temporairement indisponibles : leur visibilité n’a pas pu être vérifiée.</p>';
    setStatus(status,'Impossible de vérifier les playtests du projet.','error');
  }else if(playtests)playtests.innerHTML=rows(pts).map(x=>`<article class="playtest-card"><span class="status-badge">${x.status==='active'?'En cours':'Ouvert'}</span><h3>${escapeHtml(x.title)}</h3><p>${escapeHtml(x.description||'')}</p><a class="btn btn-secondary" href="/compte/playtests.html#${encodeURIComponent(x.id)}">Voir le playtest</a></article>`).join('')||'<p>Aucun playtest ouvert.</p>';
}
async function playtests(){
  const s=getSupabase(),[pr,mr]=await Promise.all([
    s.from('playtests').select('id,title,description,status,starts_at,ends_at,max_participants,required_access,projects(name,slug)').in('status',['open','active']).order('starts_at'),
    s.from('playtest_participants').select('playtest_id,status').eq('user_id',user.id)
  ]),list=document.querySelector('[data-playtests-list]');
  if(pr.error||mr.error){
    if(list)list.innerHTML='<div class="notice"><strong>Playtests temporairement indisponibles.</strong><p>Les candidatures et tests ouverts n’ont pas pu être vérifiés; aucune nouvelle action n’est proposée.</p></div>';
    setStatus(status,'Impossible de vérifier les playtests ou vos candidatures.','error');
    return;
  }
  const pts=rows(pr.data),mine=rows(mr.data),map=new Map(mine.map(x=>[x.playtest_id,x.status]));
  list.innerHTML=pts.map(x=>{const m=map.get(x.id);return `<article class="account-game-card" id="${x.id}"><div class="account-game-card-top"><span class="status-badge">${x.status==='active'?'En cours':'Candidatures ouvertes'}</span><span>${escapeHtml(x.projects?.name||'')}</span></div><h2>${escapeHtml(x.title)}</h2><p>${escapeHtml(x.description||'')}</p><p><strong>Accès requis :</strong> ${escapeHtml(roleLabel(x.required_access||'tester'))}</p><div class="hero-actions">${m?`<span class="role-chip">${escapeHtml({applied:'Candidature envoyée',approved:'Approuvé',refused:'Refusé',completed:'Complété'}[m]||m)}</span>`:`<button class="btn btn-primary" type="button" data-apply-playtest="${x.id}">Poser ma candidature</button>`}</div></article>`}).join('')||'<div class="notice"><strong>Aucun playtest ouvert.</strong></div>';
  list.querySelectorAll('[data-apply-playtest]').forEach(b=>b.addEventListener('click',async()=>{const msg=prompt('Message de candidature (facultatif).')||'';const {error}=await s.from('playtest_participants').insert({playtest_id:b.dataset.applyPlaytest,user_id:user.id,status:'applied',application_message:msg.slice(0,1500)});if(error){setStatus(status,error.message,'error');return}b.outerHTML='<span class="role-chip">Candidature envoyée</span>';setStatus(status,'Candidature transmise.','success')}));
}
(async()=>{
  user=await requireUser();
  const s=getSupabase();
  const [capabilityResult,ownerResult,catalogAccessResult]=await Promise.all([
    s.rpc('sinjira_my_account_capabilities'),
    s.rpc('is_sinjira_owner',{p_user_id:user.id}),
    s.rpc('sinjira_my_catalog_access_mode')
  ]);
  const {data:capabilities,error:capabilityError}=capabilityResult;
  if(capabilityError||!capabilities){setStatus(status,'Impossible de vérifier les capacités du compte.','error');return}
  ownerResolved=!ownerResult.error;
  owner=ownerResolved&&ownerResult.data===true;
  familyCatalog=!catalogAccessResult.error&&String(catalogAccessResult.data||'member')==='family';
  if(!ownerResolved||catalogAccessResult.error)setStatus(status,'Le rôle propriétaire ou famille n’a pas pu être confirmé. Aucun accès supplémentaire n’est supposé.','error');
  childMode=capabilities.library_mode==='reviewed_11_12';
  try{
    if(page==='library')await library();
    else if(page==='documents')await documents();
    else if(page==='project')await project();
    else if(page==='playtests'){
      if(childMode)return;
      await playtests();
    }
  }catch(e){setStatus(status,e?.message||'Une erreur est survenue.','error')}
})();
