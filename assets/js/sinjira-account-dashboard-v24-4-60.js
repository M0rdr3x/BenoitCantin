import {getSupabase, escapeHtml} from './sinjira-supabase.js';

const s=getSupabase();
let dashboardFamily=false;

const setText=(selector,value)=>{
  document.querySelectorAll(selector).forEach(node=>{node.textContent=String(value??'—')});
};

const characterStatusLabel=status=>({
  approved:'Approuvé',
  assigned:'Assigné',
  future:'Prévu dans le canon',
  published:'Publié'
}[status]||'En préparation');

const applicationStatusLabel=status=>({
  submitted:'Questionnaire reçu',
  pending:'En attente',
  reviewing:'En révision',
  processing:'En préparation',
  approved:'Approuvé',
  rejected:'À revoir'
}[status]||'Aucune demande active');

async function waitForLegacyDashboard(){
  const marker=document.querySelector('[data-contribution-status]');
  if(!marker)return;
  const started=Date.now();
  while(marker.textContent.trim()==='—'&&Date.now()-started<2500){
    await new Promise(resolve=>setTimeout(resolve,60));
  }
}

function renderAccess(projects,isOwner,isAdmin,roleResolved=true,catalogResolved=true,accessResolved=true){
  const count=projects.length;
  setText('[data-stat-projects]',accessResolved||catalogResolved?count:'—');
  setText('[data-project-access-summary]',!accessResolved&&!catalogResolved
    ? 'Accès projets temporairement indisponibles; aucun accès supplémentaire n’est supposé.'
    : !roleResolved
      ? `${count} accès projet visible${count===1?'':'s'}; rôle du compte non confirmé.`
      : (isOwner||isAdmin||dashboardFamily)&&!catalogResolved
        ? `Catalogue complet temporairement indisponible · ${count} accès confirmé${count===1?'':'s'} affiché${count===1?'':'s'}.`
        : isOwner
          ? `Catalogue propriétaire : ${count} création${count===1?'':'s'} visible${count===1?'':'s'}.`
          : dashboardFamily
            ? `Catalogue famille créateur : ${count} création${count===1?'':'s'} visible${count===1?'':'s'}.`
          : isAdmin
            ? `Accès administrateur : ${count} projet${count===1?'':'s'} disponible${count===1?'':'s'}.`
            : count
              ? `${count} accès projet actif${count===1?'':'s'} sur votre compte.`
              : 'Aucun accès privé supplémentaire. Les contenus publics restent disponibles.');

  const box=document.querySelector('[data-dashboard-projects]');
  if(!box)return;
  if(!accessResolved&&!catalogResolved){
    box.innerHTML='<p>Les accès projets n’ont pas pu être vérifiés. Aucun accès supplémentaire n’est supposé.</p>';
    return;
  }
  if(!projects.length){
    box.innerHTML='<p>Aucun accès privé supplémentaire pour le moment.</p>';
    return;
  }
  box.innerHTML=projects.slice(0,4).map(project=>{
    const p=project.projects||project;
    if(!p?.slug)return '';
    const label=isOwner?'Propriétaire':dashboardFamily?'Famille créateur':isAdmin?'Administration':project.access_level||'Accès';
    if(dashboardFamily&&p.content_available===false){
      return `<div class="account-mini-project"><span>${escapeHtml(p.name||p.slug)}</span><small>Catalogue famille · contenu protégé</small></div>`;
    }
    return `<a class="account-mini-project" href="/compte/projet.html?slug=${encodeURIComponent(p.slug)}"><span>${escapeHtml(p.name||p.slug)}</span><small>${escapeHtml(label)}</small></a>`;
  }).join('');
}

function renderLibrary(rows,resolved=true){
  if(!resolved){
    setText('[data-stat-reader]','—');
    setText('[data-reader-library-summary]','Bibliothèque de lecture temporairement indisponible; aucune progression n’est supposée.');
    return;
  }
  const count=rows.length;
  setText('[data-stat-reader]',count);
  const progressed=rows.filter(row=>Number(row.progress_percent||0)>0);
  const max=progressed.length?Math.max(...progressed.map(row=>Number(row.progress_percent||0))):0;
  setText('[data-reader-library-summary]',count
    ? `${count} roman${count===1?'':'s'} dans votre bibliothèque${max?` · progression maximale ${max}%`:''}.`
    : 'Votre bibliothèque de lecture est prête. Ajoutez un roman depuis la section Romans.');
}

function normalizeCharacter(primary,legacy){
  if(primary){
    return {
      name:primary.public_name||'Personnage SINJIRA™',
      status:primary.status,
      detail:primary.canon_status&&primary.canon_status!=='PROVISOIRE'?primary.canon_status:''
    };
  }
  if(legacy){
    return {
      name:legacy.canonical_name||'Personnage SINJIRA™',
      status:legacy.status,
      detail:legacy.narrative_role||''
    };
  }
  return null;
}

function renderCharacter(character,application){
  const name=document.querySelector('[data-character-name]');
  const summary=document.querySelector('[data-character-summary]');
  const register=document.querySelector('[data-registre-summary]');
  if(character){
    if(name)name.textContent=character.name;
    if(summary)summary.textContent=`${characterStatusLabel(character.status)}${character.detail?` · ${character.detail}`:''}`;
    if(register)register.textContent='Votre personnage est déjà rattaché à votre compte. Le Registre reste consultable, sans créer de doublon.';
    return;
  }
  if(name)name.textContent='Aucun personnage assigné';
  if(summary)summary.textContent=application?applicationStatusLabel(application.status):'Vous pouvez commencer par le Registre des Consciences.';
  if(register)register.textContent=application
    ? `État du Registre : ${applicationStatusLabel(application.status)}.`
    : 'Aucun questionnaire envoyé. Vous pouvez remplir le Registre quand vous le souhaitez.';
}

async function loadPrivateDashboard(){
  if(document.body.dataset.accountPage!=='dashboard')return;
  const {data:{user},error:userError}=await s.auth.getUser();
  if(userError||!user)return;

  await waitForLegacyDashboard();

  const [adminResult,ownerResult,catalogAccessResult,accessResult,libraryResult,characterResult,legacyCharacterResult,applicationResult]=await Promise.all([
    s.rpc('is_sinjira_admin',{p_user_id:user.id}),
    s.rpc('is_sinjira_owner',{p_user_id:user.id}),
    s.rpc('sinjira_my_catalog_access_mode'),
    s.from('project_access').select('project_id,access_level,expires_at,projects(id,slug,name,status)').eq('user_id',user.id),
    s.from('sinjira_reader_library').select('novel_id,last_opened_at,progress_percent').eq('user_id',user.id),
    s.from('characters').select('id,status,public_name,canon_status,novel_note,updated_at').eq('user_id',user.id).eq('visible_to_user',true).order('updated_at',{ascending:false}).limit(1),
    s.from('sinjira_characters').select('id,status,canonical_name,narrative_role,future_novel_note,updated_at').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(1),
    s.from('sinjira_character_applications').select('id,status,submitted_at,updated_at').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(1)
  ]);

  const ownerResolved=!ownerResult.error,adminResolved=!adminResult.error;
  const isOwner=ownerResolved&&ownerResult.data===true;
  const isAdmin=adminResolved&&adminResult.data===true;
  const roleResolved=ownerResolved&&(isOwner||adminResolved);
  const catalogAccessResolved=!catalogAccessResult.error;
  const catalogAccessMode=catalogAccessResolved?String(catalogAccessResult.data||'member'):'member';
  dashboardFamily=catalogAccessMode==='family';
  setText('[data-account-role]',!roleResolved||!catalogAccessResolved?'Rôle du compte non confirmé':isOwner?'Propriétaire SINJIRA™':dashboardFamily?'Famille créateur SINJIRA™':isAdmin?'Administrateur SINJIRA™':'Membre SINJIRA™');

  const accessResolved=!accessResult.error;
  let projects=(accessResult.data||[]).filter(row=>!row.expires_at||new Date(row.expires_at)>new Date());
  let catalogResolved=false;
  if(roleResolved&&(isAdmin||isOwner)){
    const all=await s.from('projects').select('id,slug,name,status').order('sort_order');
    catalogResolved=!all.error;
    if(catalogResolved)projects=all.data||[];
  }
  if(catalogAccessResolved&&dashboardFamily){
    const all=await s.rpc('sinjira_my_project_catalog');
    catalogResolved=!all.error;
    if(catalogResolved)projects=Array.isArray(all.data)?all.data:[];
  }
  if(roleResolved&&!isOwner&&!isAdmin&&!dashboardFamily)catalogResolved=accessResolved;

  renderAccess(projects,isOwner,isAdmin,roleResolved,catalogResolved,accessResolved);
  renderLibrary(libraryResult.data||[],!libraryResult.error);
  renderCharacter(
    normalizeCharacter(characterResult.data?.[0]||null,legacyCharacterResult.data?.[0]||null),
    applicationResult.data?.[0]||null
  );

  const state=document.querySelector('[data-dashboard-private-state]');
  if(state){
    const characterUnavailable=characterResult.error&&legacyCharacterResult.error;
    const hadError=!catalogResolved||[adminResult,ownerResult,catalogAccessResult,accessResult,libraryResult,applicationResult].some(result=>result.error)||characterUnavailable;
    state.hidden=!hadError;
    if(hadError)state.textContent='Certaines informations privées n’ont pas pu être chargées. Vos données restent protégées; réessayez après avoir rechargé la page.';
  }
}

loadPrivateDashboard().catch(()=>{
  const state=document.querySelector('[data-dashboard-private-state]');
  if(state){state.hidden=false;state.textContent='Le résumé privé du compte est temporairement indisponible.';}
});
