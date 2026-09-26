import {getSupabase,requireUser,escapeHtml,setStatus,projectStatusLabel} from './sinjira-supabase.js';

const status=document.querySelector('[data-library-status]');
const rows=value=>Array.isArray(value)?value:[];
const BOOK_ONE_SLUG='sinjira-livre-01-la-cendre-du-jugement';
const PRIVATE_READER_PATH='/projets/sinjira/romans/lire-integral.html';

function cover(project){
  if(project.cover_url)return project.cover_url;
  if(project.slug==='fracture-du-reseau-mere')return '/assets/media/sinjira-fracture-du-reseau-mere-officiel.webp';
  if(project.slug==='reseau-mere-resistance')return '/assets/media/sinjira-reseau-mere-resistance-officiel.webp';
  return '/assets/media/sinjira-emblem.webp';
}

function setCount(selector,value){const node=document.querySelector(selector);if(node)node.textContent=String(value)}
function renderUnavailable(selector,title,message){
  const box=document.querySelector(selector);if(!box)return;
  box.innerHTML=`<div class="notice"><strong>${escapeHtml(title)}</strong><p>${escapeHtml(message)}</p></div>`;
}

function accessLabel(project,access,isOwner,isAdmin){
  if(isOwner)return 'Propriétaire';
  if(isAdmin)return 'Administration';
  if(access?.access_level)return `Accès privé · ${access.access_level}`;
  if(project.visibility==='account')return 'Inclus avec le compte';
  if(project.visibility==='public')return 'Public';
  return 'Accès autorisé';
}

function renderProjects(projects,documents,accessRows,pendingRows,isOwner,isAdmin,childMode=false,selector='[data-library-games]',familyCatalog=false){
  const box=document.querySelector(selector);if(!box)return;
  const access=new Map(accessRows.map(row=>[row.project_id,row]));
  const pending=new Map(pendingRows.map(row=>[row.project_id,row]));
  const now=Date.now();
  const activeAccess=new Map([...access.entries()].filter(([,row])=>!row.expires_at||new Date(row.expires_at).getTime()>now));
  box.innerHTML=projects.map(project=>{
    const right=activeAccess.get(project.id),docCount=documents.filter(document=>document.project_id===project.id).length,waiting=pending.has(project.id);
    const tester=!childMode&&(isOwner||isAdmin||right?.access_level==='tester');
    const canRequest=!childMode&&!isOwner&&!isAdmin&&!tester&&project.allow_tester_requests;
    const childApproved=!childMode||project.content_available!==false;
    const source=String(project.access_source||'free');
    const role=childMode
      ?(childApproved?'Approuvé 11–12 ans':'Catalogue familial · accès protégé')
      :isOwner
        ?'Propriétaire'
        :familyCatalog||source==='family'
          ?'Famille créateur · catalogue complet'
          :source==='product'
            ?'Acheté / droit numérique'
            :accessLabel(project,right,isOwner,isAdmin);
    const visibility=childMode
      ?(childApproved?'Contenu vérifié pour cette tranche d’âge':'Visible dans le catalogue familial · contenu protégé selon l’âge')
      :project.product_slug&&source==='product'
        ?'Droit numérique actif'
        :project.visibility==='restricted'?'Accès restreint':project.visibility==='account'?'Inclus avec le compte':'Page publique';
    const openAction=childApproved
      ?`<a class="btn btn-primary" href="/compte/projet.html?slug=${encodeURIComponent(project.slug)}">Ouvrir l’espace</a>`
      :'';
    return `<article class="library-project-card"><div class="library-project-art"><img src="${escapeHtml(cover(project))}" alt=""></div><div class="library-project-body"><div class="library-project-meta"><span class="status-badge">${escapeHtml(projectStatusLabel(project.status))}</span><span class="role-chip">${escapeHtml(role)}</span></div><h2>${escapeHtml(project.name)}</h2><p>${escapeHtml(project.description||'')}</p><div class="library-project-stats"><span>${docCount} document${docCount===1?'':'s'} accessible${docCount===1?'':'s'}</span><span>${escapeHtml(visibility)}</span></div><div class="hero-actions">${openAction}${!childMode&&project.play_path&&childApproved?`<a class="btn btn-secondary" href="${escapeHtml(project.play_path)}">Jouer</a>`:''}${canRequest?`<button class="btn btn-secondary" type="button" data-v2461-request-tester="${project.id}" ${waiting?'disabled':''}>${waiting?'Demande testeur en attente':'Demander accès testeur'}</button>`:''}</div></div></article>`;
  }).join('')||(childMode?'<div class="notice"><strong>Aucun contenu n’a encore été approuvé pour les comptes de 11–12 ans.</strong><p>Les projets apparaîtront ici seulement après une révision humaine explicite.</p></div>':'<div class="notice"><strong>Aucun espace disponible pour ce compte.</strong></div>');
}

function renderExtensions(extensions,childMode=false,familyCatalog=false){
  const box=document.querySelector('[data-library-extensions]');if(!box)return;
  if(childMode&&!familyCatalog){
    box.innerHTML='<div class="notice"><strong>Extensions fermées par défaut pour les comptes 11–12 ans.</strong><p>Une extension interne n’apparaît ici que dans le catalogue familial protégé.</p></div>';
    return;
  }
  box.innerHTML=extensions.map(extension=>{
    const available=extension.content_available!==false;
    const source=String(extension.access_source||'catalogue');
    const role=childMode
      ?'Catalogue familial · accès protégé'
      :extension.creator_mode
        ?'Créateur · catalogue complet'
        :extension.family_mode
          ?'Famille créateur · catalogue complet'
          :source==='product'
            ?'Acheté / droit numérique'
            :extension.is_public?'Public':'Accès autorisé';
    const statusLabel=childMode?'Protégé':String(extension.status||'—');
    const projectLabel=extension.project_slug?'Projet : '+escapeHtml(extension.project_slug):'Projet SINJIRA™';
    return '<article class="library-project-card"><div class="library-project-body"><div class="library-project-meta"><span class="status-badge">'+escapeHtml(statusLabel)+'</span><span class="role-chip">'+escapeHtml(role)+'</span></div><h2>'+escapeHtml(extension.title||'Extension SINJIRA™')+'</h2><p>'+escapeHtml(extension.description||'')+'</p><div class="library-project-stats"><span>'+projectLabel+'</span><span>'+(available?'Contenu disponible':'Contenu protégé selon l’âge')+'</span></div></div></article>';
  }).join('')||'<div class="notice"><strong>Aucune extension disponible pour ce compte.</strong></div>';
}

function renderNovels(novels,libraryRows,isOwner,childMode=false,familyCatalog=false){
  const box=document.querySelector('[data-library-novels]');if(!box)return;
  if(childMode&&!familyCatalog){
    box.innerHTML='<div class="notice"><strong>Romans fermés par défaut pour les comptes 11–12 ans.</strong><p>Un roman apparaît ici seulement après une classification et une autorisation adaptées.</p></div>';
    return;
  }
  const progressByNovel=new Map(libraryRows.map(row=>[row.novel_id,row]));
  box.innerHTML=novels.map(novel=>{
    const progress=progressByNovel.get(novel.id);
    const fullAccess=Boolean(novel.full_access);
    const source=String(novel.access_source||'catalogue');
    const access=childMode&&familyCatalog
      ?'Catalogue familial · lecture protégée'
      :isOwner
        ?(fullAccess?'Créateur · intégrale privée':'Créateur · catalogue complet')
        :(source==='family'||source==='family_catalog')
          ?(fullAccess?'Famille créateur · intégrale privée':'Famille créateur · catalogue complet')
          :fullAccess&&(source==='entitlement'||source==='product')?'Acheté / droit numérique':novel.status==='published'?'Disponible':'Annoncé';
    const statusLabel=novel.status==='draft'?'Brouillon créateur':novel.status==='published'?'Publié':novel.status==='announced'?'Annoncé':novel.status||'—';
    const actions=childMode?'':[
      novel.demo_path?`<a class="btn btn-secondary" href="${escapeHtml(novel.demo_path)}">Lire la démo</a>`:'',
      fullAccess?`<a class="btn btn-primary" href="${PRIVATE_READER_PATH}?novel=${encodeURIComponent(novel.slug)}">Lire l’intégrale</a>`:'',
      novel.public_path?`<a class="btn btn-secondary" href="${escapeHtml(novel.public_path)}">Voir le roman</a>`:''
    ].join('');
    const privateState=isOwner&&!fullAccess?'<p><small>Manuscrit intégral privé non chargé dans le coffre SINJIRA™.</small></p>':'';
    return `<article class="reader-book-card"><div class="library-project-meta"><span class="status-badge">${escapeHtml(statusLabel)}</span><span class="role-chip">${escapeHtml(access)}</span></div><h2>${escapeHtml(novel.title||'Roman SINJIRA™')}</h2><p>${escapeHtml(novel.description||'')}</p>${privateState}${progress?`<p>Progression privée : ${Math.max(0,Math.min(100,Number(progress.progress_percent||0)))} %${progress.last_page?` · page ${Number(progress.last_page)}`:''}</p>`:''}<div class="hero-actions">${actions}</div></article>`;
  }).join('')||'<div class="notice"><strong>Aucun roman disponible pour ce compte.</strong></div>';
}
function renderReads(libraryRows){
  const box=document.querySelector('[data-library-reads]');if(!box)return;
  box.innerHTML=libraryRows.map(row=>{const novel=row.sinjira_novels;if(!novel)return '';const progress=Math.max(0,Math.min(100,Number(row.progress_percent||0)));return `<article class="reader-book-card"><span class="eyebrow">Lecture suivie</span><h2>${escapeHtml(novel.title||'Roman SINJIRA™')}</h2><p>${escapeHtml(novel.description||'')}</p><div class="v19-progress-track"><span style="width:${progress}%"></span></div><p>Progression : ${progress}%${row.last_page?` · page ${Number(row.last_page)}`:''}</p><div class="hero-actions">${novel.demo_path?`<a class="btn btn-primary" href="${escapeHtml(novel.demo_path)}">${progress>0?'Continuer la démo':'Lire la démo'}</a>`:''}<a class="btn btn-secondary" href="${escapeHtml(novel.public_path||'/projets/sinjira/romans/')}">Page du roman</a></div></article>`}).join('')||'<div class="notice"><strong>Aucun roman suivi.</strong><p>Les romans ajoutés à votre bibliothèque apparaîtront ici avec leur progression.</p></div>';
}

function entitlementCard(row){
  const product=row||{};
  const name=escapeHtml(product.name||product.slug||'Produit SINJIRA™');
  const source=escapeHtml(product.source==='paid_order'?'achat payé':product.source||'compte');
  if(product.slug===BOOK_ONE_SLUG){
    return `<article class="account-card"><span class="eyebrow">Droit numérique reconnu</span><h2>${name}</h2><p>${escapeHtml(product.product_type||'Accès')} · source ${source}</p><p>Ce droit est réellement associé au compte. La disponibilité de l’intégrale privée est vérifiée séparément dans la section Romans : le bouton de lecture n’apparaît que lorsqu’un actif privé est configuré et que le serveur confirme l’accès.</p><div class="hero-actions"><a class="btn btn-secondary" href="licences.html">Voir mes licences</a><a class="btn btn-secondary" href="/projets/sinjira/romans/">Page du roman</a></div></article>`;
  }
  return `<article class="account-card"><span class="eyebrow">Droit numérique</span><h2>${name}</h2><p>${escapeHtml(product.product_type||'Accès')} · source ${source}</p><div class="hero-actions"><a class="btn btn-secondary" href="licences.html">Voir mes licences</a></div></article>`;
}

function renderEntitlements(entitlements,isOwner){
  const box=document.querySelector('[data-library-entitlements]');if(!box)return;
  const cards=entitlements.map(entitlementCard).join('');
  box.innerHTML=cards||`<article class="account-card"><span class="eyebrow">Droits numériques</span><h2>${isOwner?'Rôle propriétaire actif · aucun droit produit explicite':'Aucune licence numérique explicite'}</h2><p>${isOwner?'Le rôle propriétaire donne la visibilité de gestion sur les créations, mais ne fabrique ni achat ni entitlement. Les intégrales privées disponibles apparaissent uniquement dans la section Romans lorsque leur actif est configuré.':'Les produits activés ou attribués à votre compte apparaîtront ici.'}</p><div class="hero-actions"><a class="btn btn-secondary" href="licences.html">Gérer mes licences</a></div></article>`;
}

async function init(){
  if(document.body.dataset.libraryPage!=='library-v24-4-61')return;
  const user=await requireUser('/compte/connexion.html');const s=getSupabase();
  const {data:capabilities,error:capabilityError}=await s.rpc('sinjira_my_account_capabilities');
  if(capabilityError||!capabilities){setStatus(status,'Impossible de vérifier les capacités du compte.','error');return}
  const childMode=capabilities.library_mode==='reviewed_11_12';
  const catalogAccessResult=await s.rpc('sinjira_my_catalog_access_mode');
  const catalogAccessResolved=!catalogAccessResult.error;
  const catalogAccessMode=catalogAccessResolved?String(catalogAccessResult.data||'member'):'member';
  const familyCatalog=catalogAccessMode==='family';

  if(childMode){
    const projectQuery=s.rpc('sinjira_my_project_catalog');
    const novelQuery=familyCatalog?s.rpc('sinjira_my_novel_catalog'):Promise.resolve({data:[],error:null});
    const extensionQuery=familyCatalog?s.rpc('sinjira_my_extension_catalog'):Promise.resolve({data:[],error:null});
    const [projectsResult,documentsResult,novelsResult,extensionsResult]=await Promise.all([
      projectQuery,
      s.from('documents').select('id,project_id,child_access_status').eq('status','approved'),
      novelQuery,
      extensionQuery
    ]);
    const projects=rows(projectsResult.data),documents=rows(documentsResult.data),juniorResolved=!projectsResult.error&&!documentsResult.error&&(!familyCatalog||(!novelsResult.error&&!extensionsResult.error));
    const juniorNovels=familyCatalog?rows(novelsResult.data):[],juniorExtensions=familyCatalog?rows(extensionsResult.data):[];
    setCount('[data-library-project-count]',juniorResolved?projects.length:'—');setCount('[data-library-novel-count]',juniorResolved?juniorNovels.length:'—');setCount('[data-library-extension-count]',juniorResolved?juniorExtensions.length:'—');setCount('[data-library-entitlement-count]',0);setCount('[data-library-request-count]',0);
    const role=document.querySelector('[data-library-role]');if(role)role.textContent=familyCatalog?'Compte famille créateur · Junior 11–12 ans':'Compte Junior 11–12 ans';
    if(juniorResolved){
      renderProjects(projects.filter(project=>project.type==='game'),documents,[],[],false,false,true,'[data-library-games]');
      renderProjects(projects.filter(project=>project.type!=='game'),documents,[],[],false,false,true,'[data-library-other]');
    }else{
      renderUnavailable('[data-library-games]','Bibliothèque Junior temporairement indisponible','Les contenus approuvés 11–12 ans n’ont pas pu être vérifiés. Aucun contenu supplémentaire n’est affiché.');
      renderUnavailable('[data-library-other]','Bibliothèque Junior temporairement indisponible','Les contenus approuvés 11–12 ans n’ont pas pu être vérifiés. Aucun contenu supplémentaire n’est affiché.');
    }
    renderNovels(juniorResolved?juniorNovels:[],[],false,true,familyCatalog);
    renderExtensions(juniorResolved?juniorExtensions:[],true,familyCatalog);
    const reads=document.querySelector('[data-library-reads]');if(reads)reads.innerHTML='<div class="notice"><strong>Lectures privées non classées.</strong><p>Elles resteront fermées jusqu’à une révision adaptée aux 11–12 ans.</p></div>';
    const entitlements=document.querySelector('[data-library-entitlements]');if(entitlements)entitlements.innerHTML='<div class="notice"><strong>Licences et achats indisponibles à 11–12 ans.</strong><p>Cette section ne s’active pas automatiquement avec un compte supervisé.</p></div>';
    if(!juniorResolved)setStatus(status,'La bibliothèque Junior n’a pas pu terminer sa vérification. Aucun contenu supplémentaire n’est affiché.','error');
    else if(familyCatalog)setStatus(status,'Catalogue familial chargé · toutes les créations sont visibles, mais seuls les contenus approuvés 11–12 ans peuvent être ouverts.','success');
    else setStatus(status,'Bibliothèque Junior chargée · seuls les contenus approuvés 11–12 ans sont affichés.','success');
    return;
  }

  const [adminResult,ownerResult,projectsResult,accessResult,documentsResult,pendingResult,readsResult,entitlementsResult,novelsResult,extensionsResult]=await Promise.all([
    s.rpc('is_sinjira_admin',{p_user_id:user.id}),s.rpc('is_sinjira_owner',{p_user_id:user.id}),s.rpc('sinjira_my_project_catalog'),s.from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id),s.from('documents').select('id,project_id').eq('status','approved'),s.from('access_requests').select('project_id,requested_level,status').eq('user_id',user.id).eq('status','pending'),s.from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent,sinjira_novels(id,title,description,status,cover_url,public_path,demo_path)').eq('user_id',user.id).order('updated_at',{ascending:false}),s.rpc('sinjira_my_product_rights'),s.rpc('sinjira_my_novel_catalog'),s.rpc('sinjira_my_extension_catalog')
  ]);
  const ownerResolved=!ownerResult.error,adminResolved=!adminResult.error;
  const isAdmin=adminResolved&&adminResult.data===true,isOwner=ownerResolved&&ownerResult.data===true;
  const roleResolved=ownerResolved&&(isOwner||adminResolved);
  const projectResolved=!projectsResult.error&&!accessResult.error&&!documentsResult.error&&!pendingResult.error;
  const readsResolved=!readsResult.error,entitlementsResolved=!entitlementsResult.error,novelsResolved=!novelsResult.error,extensionsResolved=!extensionsResult.error;
  const projects=rows(projectsResult.data),accessRows=rows(accessResult.data),documents=rows(documentsResult.data),pendingRows=rows(pendingResult.data),libraryRows=rows(readsResult.data),entitlements=rows(entitlementsResult.data),novels=rows(novelsResult.data),extensions=rows(extensionsResult.data);
  setCount('[data-library-project-count]',projectResolved?projects.length:'—');setCount('[data-library-novel-count]',novelsResolved?novels.length:'—');setCount('[data-library-extension-count]',extensionsResolved?extensions.length:'—');setCount('[data-library-entitlement-count]',entitlementsResolved?entitlements.length:'—');setCount('[data-library-request-count]',!pendingResult.error?pendingRows.length:'—');
  const role=document.querySelector('[data-library-role]');if(role)role.textContent=!roleResolved&&!catalogAccessResolved?'Rôle du compte non confirmé':isOwner?'Propriétaire SINJIRA™':familyCatalog?'Famille créateur SINJIRA™':isAdmin?'Administrateur SINJIRA™':'Compte SINJIRA™';
  if(projectResolved){
    renderProjects(projects.filter(project=>project.type==='game'),documents,accessRows,pendingRows,isOwner,isAdmin,false,'[data-library-games]',familyCatalog);
    renderProjects(projects.filter(project=>project.type!=='game'),documents,accessRows,pendingRows,isOwner,isAdmin,false,'[data-library-other]',familyCatalog);
  }else{
    renderUnavailable('[data-library-games]','Projets temporairement indisponibles','Les accès projets n’ont pas pu être vérifiés. Aucun accès ou bouton de jeu supplémentaire n’est supposé.');
    renderUnavailable('[data-library-other]','Créations temporairement indisponibles','Les accès projets n’ont pas pu être vérifiés. Aucun accès supplémentaire n’est supposé.');
  }
  if(novelsResolved)renderNovels(novels,readsResolved?libraryRows:[],isOwner,false);
  else renderUnavailable('[data-library-novels]','Romans temporairement indisponibles','Le catalogue de romans n’a pas pu être vérifié.');
  if(extensionsResolved)renderExtensions(extensions,false,familyCatalog);
  else renderUnavailable('[data-library-extensions]','Extensions temporairement indisponibles','Le catalogue des extensions n’a pas pu être vérifié.');
  if(readsResolved)renderReads(libraryRows);
  else renderUnavailable('[data-library-reads]','Progression temporairement indisponible','Votre progression de lecture n’a pas pu être vérifiée.');
  if(entitlementsResolved)renderEntitlements(entitlements,isOwner);
  else renderUnavailable('[data-library-entitlements]','Droits numériques temporairement indisponibles','Les droits numériques du compte n’ont pas pu être vérifiés; aucun accès supplémentaire n’est supposé.');
  const errors=[ownerResult,adminResult,projectsResult,accessResult,documentsResult,pendingResult,readsResult,entitlementsResult,novelsResult,extensionsResult].filter(result=>result.error);if(catalogAccessResult.error)errors.push(catalogAccessResult);if(errors.length)setStatus(status,'Certaines sections privées ou le rôle du compte n’ont pas pu être vérifiés. Aucun accès supplémentaire n’a été accordé.','error');
  document.querySelectorAll('[data-v2461-request-tester]').forEach(button=>button.addEventListener('click',async()=>{const message=prompt('Court message pour votre demande (facultatif).')||'';const {error}=await s.from('access_requests').insert({user_id:user.id,project_id:button.dataset.v2461RequestTester,requested_level:'tester',message:message.slice(0,1500)});if(error){setStatus(status,'La demande n’a pas pu être transmise.','error');return}button.disabled=true;button.textContent='Demande testeur en attente';setStatus(status,'Demande testeur transmise.','success')}));
}

init().catch(error=>{if(error?.message!=='Connexion requise')setStatus(status,'Impossible de charger la bibliothèque pour le moment.','error')});
