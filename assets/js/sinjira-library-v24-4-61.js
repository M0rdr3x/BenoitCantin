import {getSupabase,requireUser,escapeHtml,setStatus,projectStatusLabel} from './sinjira-supabase.js';

const status=document.querySelector('[data-library-status]');
const rows=value=>Array.isArray(value)?value:[];
const BOOK_ONE_SLUG='sinjira-livre-01-la-cendre-du-jugement';
const PRIVATE_READER_PATH='/projets/sinjira/romans/lire-integral.html';
const PRIVATE_DOWNLOAD_FUNCTION='get-private-book-url';

function cover(project){
  if(project.cover_url)return project.cover_url;
  if(project.slug==='fracture-du-reseau-mere')return '/assets/media/sinjira-fracture-du-reseau-mere-officiel.webp';
  if(project.slug==='reseau-mere-resistance')return '/assets/media/sinjira-reseau-mere-resistance-officiel.webp';
  return '/assets/media/sinjira-emblem.webp';
}

function setCount(selector,value){const node=document.querySelector(selector);if(node)node.textContent=String(value)}

function accessLabel(project,access,isOwner,isAdmin){
  if(isOwner)return 'Propriétaire';
  if(isAdmin)return 'Administration';
  if(access?.access_level)return `Accès privé · ${access.access_level}`;
  if(project.visibility==='account')return 'Inclus avec le compte';
  if(project.visibility==='public')return 'Public';
  return 'Accès autorisé';
}

function renderProjects(projects,documents,accessRows,pendingRows,isOwner,isAdmin,childMode=false){
  const box=document.querySelector('[data-project-library]');if(!box)return;
  const access=new Map(accessRows.map(row=>[row.project_id,row]));
  const pending=new Map(pendingRows.map(row=>[row.project_id,row]));
  const now=Date.now();
  const activeAccess=new Map([...access.entries()].filter(([,row])=>!row.expires_at||new Date(row.expires_at).getTime()>now));
  box.innerHTML=projects.map(project=>{
    const right=activeAccess.get(project.id),docCount=documents.filter(document=>document.project_id===project.id).length,waiting=pending.has(project.id);
    const tester=!childMode&&(isOwner||isAdmin||right?.access_level==='tester');
    const canRequest=!childMode&&!isOwner&&!isAdmin&&!tester&&project.allow_tester_requests;
    const role=childMode?'Approuvé 11–12 ans':accessLabel(project,right,isOwner,isAdmin);
    const visibility=childMode?'Contenu vérifié pour cette tranche d’âge':project.visibility==='restricted'?'Accès restreint':project.visibility==='account'?'Compte requis':'Page publique';
    return `<article class="library-project-card"><div class="library-project-art"><img src="${escapeHtml(cover(project))}" alt=""></div><div class="library-project-body"><div class="library-project-meta"><span class="status-badge">${escapeHtml(projectStatusLabel(project.status))}</span><span class="role-chip">${escapeHtml(role)}</span></div><h2>${escapeHtml(project.name)}</h2><p>${escapeHtml(project.description||'')}</p><div class="library-project-stats"><span>${docCount} document${docCount===1?'':'s'} accessible${docCount===1?'':'s'}</span><span>${escapeHtml(visibility)}</span></div><div class="hero-actions"><a class="btn btn-primary" href="/compte/projet.html?slug=${encodeURIComponent(project.slug)}">Ouvrir l’espace</a>${!childMode&&project.play_path?`<a class="btn btn-secondary" href="${escapeHtml(project.play_path)}">Jouer</a>`:''}${canRequest?`<button class="btn btn-secondary" type="button" data-v2461-request-tester="${project.id}" ${waiting?'disabled':''}>${waiting?'Demande testeur en attente':'Demander accès testeur'}</button>`:''}</div></div></article>`;
  }).join('')||(childMode?'<div class="notice"><strong>Aucun contenu n’a encore été approuvé pour les comptes de 11–12 ans.</strong><p>Les projets apparaîtront ici seulement après une révision humaine explicite.</p></div>':'<div class="notice"><strong>Aucun espace disponible pour ce compte.</strong></div>');
}

function renderReads(libraryRows){
  const box=document.querySelector('[data-library-reads]');if(!box)return;
  box.innerHTML=libraryRows.map(row=>{const novel=row.sinjira_novels;if(!novel)return '';const progress=Math.max(0,Math.min(100,Number(row.progress_percent||0)));return `<article class="reader-book-card"><span class="eyebrow">Lecture suivie</span><h2>${escapeHtml(novel.title||'Roman SINJIRA™')}</h2><p>${escapeHtml(novel.description||'')}</p><div class="v19-progress-track"><span style="width:${progress}%"></span></div><p>Progression : ${progress}%${row.last_page?` · page ${Number(row.last_page)}`:''}</p><div class="hero-actions">${novel.demo_path?`<a class="btn btn-primary" href="${escapeHtml(novel.demo_path)}">${progress>0?'Continuer la démo':'Lire la démo'}</a>`:''}<a class="btn btn-secondary" href="${escapeHtml(novel.public_path||'/projets/sinjira/romans/')}">Page du roman</a></div></article>`}).join('')||'<div class="notice"><strong>Aucun roman suivi.</strong><p>Les romans ajoutés à votre bibliothèque apparaîtront ici avec leur progression.</p></div>';
}

function bookActions(){
  return `<div class="hero-actions"><a class="btn btn-primary" href="${PRIVATE_READER_PATH}">Lire le livre intégral</a><button class="btn btn-secondary" type="button" data-private-book-download>Télécharger mon PDF</button><a class="btn btn-secondary" href="/projets/sinjira/romans/lire-demo.html">Lire la démo</a></div>`;
}

function entitlementCard(row){
  const product=row.products;if(!product)return '';
  const name=escapeHtml(product.name||product.slug||'Produit SINJIRA™'),source=escapeHtml(row.source||'compte');
  if(product.slug===BOOK_ONE_SLUG){
    return `<article class="account-card"><span class="eyebrow">Droit numérique reconnu</span><h2>${name}</h2><p>${escapeHtml(product.product_type||'Accès')} · source ${source}</p><p>Ce droit est réellement associé au compte. L’intégrale reste derrière la diffusion privée : le lecteur et le téléchargement demandent une autorisation serveur à chaque ouverture.</p>${bookActions()}<div class="hero-actions"><a class="btn btn-secondary" href="licences.html">Voir mes licences</a><a class="btn btn-secondary" href="/projets/sinjira/romans/">Page du roman</a></div></article>`;
  }
  return `<article class="account-card"><span class="eyebrow">Droit numérique</span><h2>${name}</h2><p>${escapeHtml(product.product_type||'Accès')} · source ${source}</p><div class="hero-actions"><a class="btn btn-secondary" href="licences.html">Voir mes licences</a></div></article>`;
}

function renderEntitlements(entitlements,isOwner){
  const box=document.querySelector('[data-library-entitlements]');if(!box)return;
  const hasBook=entitlements.some(row=>row.products?.slug===BOOK_ONE_SLUG);
  const cards=entitlements.map(entitlementCard).join('');
  const authorCard=isOwner&&!hasBook?`<article class="account-card"><span class="eyebrow">Accès auteur</span><h2>SINJIRA™ — Livre I : La Cendre du Jugement</h2><p>Ton rôle propriétaire reste distinct d’un achat ou d’une licence produit. Pour ce Livre I seulement, le serveur peut reconnaître le rôle auteur/propriétaire et autoriser gratuitement la lecture ou le téléchargement sans fabriquer de droit acheté.</p>${bookActions()}<p><small>Le bouton visible dans le navigateur ne suffit jamais : l’autorisation est revérifiée côté serveur.</small></p></article>`:'';
  box.innerHTML=cards+authorCard||`<article class="account-card"><span class="eyebrow">Droits numériques</span><h2>${isOwner?'Rôle propriétaire actif · aucun droit produit explicite':'Aucune licence numérique explicite'}</h2><p>${isOwner?'Le rôle propriétaire reste distinct des droits numériques. Aucun produit n’est marqué comme possédé sans entitlement réellement attribué au compte.':'Les produits activés ou attribués à votre compte apparaîtront ici.'}</p><div class="hero-actions"><a class="btn btn-secondary" href="licences.html">Gérer mes licences</a></div></article>`;
}

async function downloadPrivateBook(button){
  button.disabled=true;const label=button.textContent;button.textContent='Préparation…';
  try{
    const {data,error}=await getSupabase().functions.invoke(PRIVATE_DOWNLOAD_FUNCTION);
    if(error||!data?.ok||!data?.url)throw new Error(data?.error||'Téléchargement indisponible.');
    location.assign(String(data.url));
  }catch(error){setStatus(status,error?.message||'Téléchargement indisponible.','error')}
  finally{button.disabled=false;button.textContent=label}
}

async function init(){
  if(document.body.dataset.libraryPage!=='library-v24-4-61')return;
  const user=await requireUser('/compte/connexion.html');const s=getSupabase();
  const {data:ageBand,error:ageError}=await s.rpc('sinjira_my_age_band');
  if(ageError){setStatus(status,'Impossible de vérifier la tranche d’âge du compte.','error');return}
  const childMode=ageBand==='child';

  if(childMode){
    const [projectsResult,documentsResult]=await Promise.all([
      s.from('projects').select('id,slug,name,status,visibility,description,cover_url,public_path,play_path,allow_tester_requests,sort_order,child_access_status').order('sort_order'),
      s.from('documents').select('id,project_id,child_access_status').eq('status','approved')
    ]);
    const projects=rows(projectsResult.data),documents=rows(documentsResult.data);
    setCount('[data-library-project-count]',projects.length);setCount('[data-library-read-count]',0);setCount('[data-library-entitlement-count]',0);setCount('[data-library-request-count]',0);
    const role=document.querySelector('[data-library-role]');if(role)role.textContent='Compte Junior 11–12 ans';
    renderProjects(projects,documents,[],[],false,false,true);
    const reads=document.querySelector('[data-library-reads]');if(reads)reads.innerHTML='<div class="notice"><strong>Lectures privées non classées.</strong><p>Elles resteront fermées jusqu’à une révision adaptée aux 11–12 ans.</p></div>';
    const entitlements=document.querySelector('[data-library-entitlements]');if(entitlements)entitlements.innerHTML='<div class="notice"><strong>Licences et achats indisponibles à 11–12 ans.</strong><p>Cette section ne s’active pas automatiquement avec un compte supervisé.</p></div>';
    if(projectsResult.error||documentsResult.error)setStatus(status,'La bibliothèque Junior n’a pas pu terminer sa vérification.','error');
    else setStatus(status,'Bibliothèque Junior chargée · seuls les contenus approuvés 11–12 ans sont affichés.','success');
    return;
  }

  const [adminResult,ownerResult,projectsResult,accessResult,documentsResult,pendingResult,readsResult,entitlementsResult]=await Promise.all([
    s.rpc('is_sinjira_admin',{p_user_id:user.id}),s.rpc('is_sinjira_owner',{p_user_id:user.id}),s.from('projects').select('id,slug,name,status,visibility,description,cover_url,public_path,play_path,allow_tester_requests,sort_order').order('sort_order'),s.from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id),s.from('documents').select('id,project_id').eq('status','approved'),s.from('access_requests').select('project_id,requested_level,status').eq('user_id',user.id).eq('status','pending'),s.from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent,sinjira_novels(id,title,description,status,cover_url,public_path,demo_path)').eq('user_id',user.id).order('updated_at',{ascending:false}),s.from('user_entitlements').select('product_id,source,granted_at,products(id,slug,name,product_type,active)').eq('user_id',user.id).order('granted_at',{ascending:false})
  ]);
  const isAdmin=!adminResult.error&&adminResult.data===true,isOwner=!ownerResult.error&&ownerResult.data===true;
  const projects=rows(projectsResult.data),accessRows=rows(accessResult.data),documents=rows(documentsResult.data),pendingRows=rows(pendingResult.data),libraryRows=rows(readsResult.data),entitlements=rows(entitlementsResult.data).filter(row=>row.products?.active!==false);
  setCount('[data-library-project-count]',projects.length);setCount('[data-library-read-count]',libraryRows.length);setCount('[data-library-entitlement-count]',entitlements.length);setCount('[data-library-request-count]',pendingRows.length);
  const role=document.querySelector('[data-library-role]');if(role)role.textContent=isOwner?'Propriétaire SINJIRA™':isAdmin?'Administrateur SINJIRA™':'Compte SINJIRA™';
  renderProjects(projects,documents,accessRows,pendingRows,isOwner,isAdmin,false);renderReads(libraryRows);renderEntitlements(entitlements,isOwner);
  document.querySelectorAll('[data-private-book-download]').forEach(button=>button.addEventListener('click',()=>downloadPrivateBook(button)));
  const errors=[projectsResult,accessResult,documentsResult,pendingResult,readsResult,entitlementsResult].filter(result=>result.error);if(errors.length)setStatus(status,'Certaines sections privées n’ont pas pu être chargées. Les données disponibles restent protégées par les règles du compte.','error');
  document.querySelectorAll('[data-v2461-request-tester]').forEach(button=>button.addEventListener('click',async()=>{const message=prompt('Court message pour votre demande (facultatif).')||'';const {error}=await s.from('access_requests').insert({user_id:user.id,project_id:button.dataset.v2461RequestTester,requested_level:'tester',message:message.slice(0,1500)});if(error){setStatus(status,'La demande n’a pas pu être transmise.','error');return}button.disabled=true;button.textContent='Demande testeur en attente';setStatus(status,'Demande testeur transmise.','success')}));
}

init().catch(error=>{if(error?.message!=='Connexion requise')setStatus(status,'Impossible de charger la bibliothèque pour le moment.','error')});
