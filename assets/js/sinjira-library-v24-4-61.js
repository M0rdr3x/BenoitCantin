import {getSupabase,requireUser,escapeHtml,setStatus,projectStatusLabel} from './sinjira-supabase.js';

const status=document.querySelector('[data-library-status]');
const rows=value=>Array.isArray(value)?value:[];

function cover(project){
  if(project.cover_url)return project.cover_url;
  if(project.slug==='fracture-du-reseau-mere')return '/assets/media/sinjira-fracture-du-reseau-mere-officiel.webp';
  if(project.slug==='reseau-mere-resistance')return '/assets/media/sinjira-reseau-mere-resistance-officiel.webp';
  return '/assets/media/sinjira-emblem.webp';
}

function setCount(selector,value){
  const node=document.querySelector(selector);
  if(node)node.textContent=String(value);
}

function accessLabel(project,access,isOwner,isAdmin){
  if(isOwner)return 'Propriétaire';
  if(isAdmin)return 'Administration';
  if(access?.access_level)return `Accès privé · ${access.access_level}`;
  if(project.visibility==='account')return 'Inclus avec le compte';
  if(project.visibility==='public')return 'Public';
  return 'Accès autorisé';
}

function renderProjects(projects,documents,accessRows,pendingRows,isOwner,isAdmin){
  const box=document.querySelector('[data-project-library]');
  if(!box)return;
  const access=new Map(accessRows.map(row=>[row.project_id,row]));
  const pending=new Map(pendingRows.map(row=>[row.project_id,row]));
  const now=Date.now();
  const activeAccess=new Map([...access.entries()].filter(([,row])=>!row.expires_at||new Date(row.expires_at).getTime()>now));

  box.innerHTML=projects.map(project=>{
    const right=activeAccess.get(project.id);
    const docCount=documents.filter(document=>document.project_id===project.id).length;
    const waiting=pending.has(project.id);
    const tester=isOwner||isAdmin||right?.access_level==='tester';
    const canRequest=!isOwner&&!isAdmin&&!tester&&project.allow_tester_requests;
    return `<article class="library-project-card">
      <div class="library-project-art"><img src="${escapeHtml(cover(project))}" alt=""></div>
      <div class="library-project-body">
        <div class="library-project-meta"><span class="status-badge">${escapeHtml(projectStatusLabel(project.status))}</span><span class="role-chip">${escapeHtml(accessLabel(project,right,isOwner,isAdmin))}</span></div>
        <h2>${escapeHtml(project.name)}</h2>
        <p>${escapeHtml(project.description||'')}</p>
        <div class="library-project-stats"><span>${docCount} document${docCount===1?'':'s'} accessible${docCount===1?'':'s'}</span><span>${escapeHtml(project.visibility==='restricted'?'Accès restreint':project.visibility==='account'?'Compte requis':'Page publique')}</span></div>
        <div class="hero-actions"><a class="btn btn-primary" href="/compte/projet.html?slug=${encodeURIComponent(project.slug)}">Ouvrir l’espace</a>${project.play_path?`<a class="btn btn-secondary" href="${escapeHtml(project.play_path)}">Jouer</a>`:''}${canRequest?`<button class="btn btn-secondary" type="button" data-v2461-request-tester="${project.id}" ${waiting?'disabled':''}>${waiting?'Demande testeur en attente':'Demander accès testeur'}</button>`:''}</div>
      </div>
    </article>`;
  }).join('')||'<div class="notice"><strong>Aucun espace disponible pour ce compte.</strong></div>';
}

function renderReads(libraryRows){
  const box=document.querySelector('[data-library-reads]');
  if(!box)return;
  box.innerHTML=libraryRows.map(row=>{
    const novel=row.sinjira_novels;
    if(!novel)return '';
    const progress=Math.max(0,Math.min(100,Number(row.progress_percent||0)));
    return `<article class="reader-book-card">
      <span class="eyebrow">Lecture suivie</span>
      <h2>${escapeHtml(novel.title||'Roman SINJIRA™')}</h2>
      <p>${escapeHtml(novel.description||'')}</p>
      <div class="v19-progress-track"><span style="width:${progress}%"></span></div>
      <p>Progression : ${progress}%${row.last_page?` · page ${Number(row.last_page)}`:''}</p>
      <div class="hero-actions">${novel.demo_path?`<a class="btn btn-primary" href="${escapeHtml(novel.demo_path)}">${progress>0?'Continuer la lecture':'Lire la démo'}</a>`:''}<a class="btn btn-secondary" href="${escapeHtml(novel.public_path||'/projets/sinjira/romans/')}">Page du roman</a></div>
    </article>`;
  }).join('')||'<div class="notice"><strong>Aucun roman suivi.</strong><p>Les romans ajoutés à votre bibliothèque apparaîtront ici avec leur progression.</p></div>';
}

function renderEntitlements(entitlements,isOwner){
  const box=document.querySelector('[data-library-entitlements]');
  if(!box)return;
  const cards=entitlements.map(row=>{
    const product=row.products;
    if(!product)return '';
    return `<article class="account-card"><span class="eyebrow">Droit numérique</span><h2>${escapeHtml(product.name||product.slug||'Produit SINJIRA™')}</h2><p>${escapeHtml(product.product_type||'Accès')} · source ${escapeHtml(row.source||'compte')}</p><div class="hero-actions"><a class="btn btn-secondary" href="licences.html">Voir mes licences</a></div></article>`;
  }).join('');
  box.innerHTML=cards||`<article class="account-card"><span class="eyebrow">Droits numériques</span><h2>${isOwner?'Accès propriétaire actif':'Aucune licence numérique explicite'}</h2><p>${isOwner?'Votre rôle propriétaire conserve l’accès universel côté serveur, indépendamment des licences individuelles.':'Les produits activés ou attribués à votre compte apparaîtront ici.'}</p><div class="hero-actions"><a class="btn btn-secondary" href="licences.html">Gérer mes licences</a></div></article>`;
}

async function init(){
  if(document.body.dataset.libraryPage!=='library-v24-4-61')return;
  const user=await requireUser('/compte/connexion.html');
  const s=getSupabase();
  const [adminResult,ownerResult,projectsResult,accessResult,documentsResult,pendingResult,readsResult,entitlementsResult]=await Promise.all([
    s.rpc('is_sinjira_admin',{p_user_id:user.id}),
    s.rpc('is_sinjira_owner',{p_user_id:user.id}),
    s.from('projects').select('id,slug,name,status,visibility,description,cover_url,public_path,play_path,allow_tester_requests,sort_order').order('sort_order'),
    s.from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id),
    s.from('documents').select('id,project_id').eq('status','approved'),
    s.from('access_requests').select('project_id,requested_level,status').eq('user_id',user.id).eq('status','pending'),
    s.from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent,sinjira_novels(id,title,description,status,cover_url,public_path,demo_path)').eq('user_id',user.id).order('updated_at',{ascending:false}),
    s.from('user_entitlements').select('product_id,source,granted_at,products(id,slug,name,product_type,active)').eq('user_id',user.id).order('granted_at',{ascending:false})
  ]);

  const isAdmin=!adminResult.error&&adminResult.data===true;
  const isOwner=!ownerResult.error&&ownerResult.data===true;
  const projects=rows(projectsResult.data);
  const accessRows=rows(accessResult.data);
  const documents=rows(documentsResult.data);
  const pendingRows=rows(pendingResult.data);
  const libraryRows=rows(readsResult.data);
  const entitlements=rows(entitlementsResult.data).filter(row=>row.products?.active!==false);

  setCount('[data-library-project-count]',projects.length);
  setCount('[data-library-read-count]',libraryRows.length);
  setCount('[data-library-entitlement-count]',entitlements.length);
  setCount('[data-library-request-count]',pendingRows.length);

  const role=document.querySelector('[data-library-role]');
  if(role)role.textContent=isOwner?'Propriétaire SINJIRA™':isAdmin?'Administrateur SINJIRA™':'Compte SINJIRA™';

  renderProjects(projects,documents,accessRows,pendingRows,isOwner,isAdmin);
  renderReads(libraryRows);
  renderEntitlements(entitlements,isOwner);

  const errors=[projectsResult,accessResult,documentsResult,pendingResult,readsResult,entitlementsResult].filter(result=>result.error);
  if(errors.length){
    setStatus(status,'Certaines sections privées n’ont pas pu être chargées. Les données disponibles restent protégées par les règles du compte.','error');
  }

  document.querySelectorAll('[data-v2461-request-tester]').forEach(button=>button.addEventListener('click',async()=>{
    const message=prompt('Court message pour votre demande (facultatif).')||'';
    const {error}=await s.from('access_requests').insert({user_id:user.id,project_id:button.dataset.v2461RequestTester,requested_level:'tester',message:message.slice(0,1500)});
    if(error){setStatus(status,'La demande n’a pas pu être transmise.','error');return;}
    button.disabled=true;
    button.textContent='Demande testeur en attente';
    setStatus(status,'Demande testeur transmise.','success');
  }));
}

init().catch(error=>{
  if(error?.message!=='Connexion requise')setStatus(status,'Impossible de charger la bibliothèque pour le moment.','error');
});
