import {getSupabase, escapeHtml} from './sinjira-supabase.js';

const s=getSupabase();

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

function renderAccess(projects,isOwner,isAdmin){
  const count=projects.length;
  setText('[data-stat-projects]',count);
  setText('[data-project-access-summary]',isOwner
    ? `Accès propriétaire : ${count} projet${count===1?'':'s'} disponible${count===1?'':'s'}.`
    : isAdmin
      ? `Accès administrateur : ${count} projet${count===1?'':'s'} disponible${count===1?'':'s'}.`
      : count
        ? `${count} accès projet actif${count===1?'':'s'} sur votre compte.`
        : 'Aucun accès privé supplémentaire. Les contenus publics restent disponibles.');

  const box=document.querySelector('[data-dashboard-projects]');
  if(!box)return;
  if(!projects.length){
    box.innerHTML='<p>Aucun accès privé supplémentaire pour le moment.</p>';
    return;
  }
  box.innerHTML=projects.slice(0,4).map(project=>{
    const p=project.projects||project;
    if(!p?.slug)return '';
    return `<a class="account-mini-project" href="/compte/projet.html?slug=${encodeURIComponent(p.slug)}"><span>${escapeHtml(p.name||p.slug)}</span><small>${escapeHtml(isOwner?'Propriétaire':isAdmin?'Administration':project.access_level||'Accès')}</small></a>`;
  }).join('');
}

function renderLibrary(rows){
  const count=rows.length;
  setText('[data-stat-reader]',count);
  const progressed=rows.filter(row=>Number(row.progress_percent||0)>0);
  const max=progressed.length?Math.max(...progressed.map(row=>Number(row.progress_percent||0))):0;
  setText('[data-reader-library-summary]',count
    ? `${count} roman${count===1?'':'s'} dans votre bibliothèque${max?` · progression maximale ${max}%`:''}.`
    : 'Votre bibliothèque de lecture est prête. Ajoutez un roman depuis la section Romans.');
}

function renderCharacter(character,application){
  const name=document.querySelector('[data-character-name]');
  const summary=document.querySelector('[data-character-summary]');
  const register=document.querySelector('[data-registre-summary]');
  if(character){
    if(name)name.textContent=character.canonical_name||'Personnage SINJIRA™';
    if(summary)summary.textContent=`${characterStatusLabel(character.status)}${character.narrative_role?` · ${character.narrative_role}`:''}`;
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

  const [adminResult,ownerResult,accessResult,libraryResult,characterResult,applicationResult]=await Promise.all([
    s.rpc('is_sinjira_admin',{p_user_id:user.id}),
    s.rpc('is_sinjira_owner',{p_user_id:user.id}),
    s.from('project_access').select('project_id,access_level,expires_at,projects(id,slug,name,status)').eq('user_id',user.id),
    s.from('sinjira_reader_library').select('novel_id,last_opened_at,progress_percent').eq('user_id',user.id),
    s.from('sinjira_characters').select('id,status,canonical_name,narrative_role,future_novel_note,updated_at').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(1),
    s.from('sinjira_character_applications').select('id,status,submitted_at,updated_at').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(1)
  ]);

  const isAdmin=!adminResult.error&&adminResult.data===true;
  const isOwner=!ownerResult.error&&ownerResult.data===true;
  setText('[data-account-role]',isOwner?'Propriétaire SINJIRA™':isAdmin?'Administrateur SINJIRA™':'Membre SINJIRA™');

  let projects=(accessResult.data||[]).filter(row=>!row.expires_at||new Date(row.expires_at)>new Date());
  if(isAdmin){
    const all=await s.from('projects').select('id,slug,name,status').order('sort_order');
    if(!all.error)projects=all.data||[];
  }

  renderAccess(projects,isOwner,isAdmin);
  renderLibrary(libraryResult.data||[]);
  renderCharacter(characterResult.data?.[0]||null,applicationResult.data?.[0]||null);

  const state=document.querySelector('[data-dashboard-private-state]');
  if(state){
    const hadError=[accessResult,libraryResult,characterResult,applicationResult].some(result=>result.error);
    state.hidden=!hadError;
    if(hadError)state.textContent='Certaines informations privées n’ont pas pu être chargées. Vos données restent protégées; réessayez après avoir rechargé la page.';
  }
}

loadPrivateDashboard().catch(()=>{
  const state=document.querySelector('[data-dashboard-private-state]');
  if(state){state.hidden=false;state.textContent='Le résumé privé du compte est temporairement indisponible.';}
});
