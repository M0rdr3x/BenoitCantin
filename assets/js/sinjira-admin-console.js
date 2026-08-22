import './sinjira-admin-console-core.js';

function projectSlug(value){
  return String(value||'projet')
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .toLowerCase().replace(/[^a-z0-9]+/g,'-')
    .replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,96)||'projet';
}

function relabelProjectRows(){
  const list=document.querySelector('[data-admin-project-list]');
  if(!list)return;
  list.querySelectorAll('.admin-management-row span').forEach(span=>{
    const text=String(span.textContent||'').trim();
    if(!text||text.startsWith('Identifiant de projet ·'))return;
    const parts=text.split(' · ');
    if(parts.length>1)span.textContent='Identifiant de projet · '+parts.slice(1).join(' · ');
  });
}

function configureProjectIdentifier(){
  const form=document.querySelector('[data-project-form]');
  if(!form)return;
  const name=form.elements.name,slug=form.elements.slug;
  if(!name||!slug)return;

  const nameField=name.closest('.field');
  const slugField=slug.closest('.field');
  const label=nameField?.querySelector('label');
  if(label)label.textContent='Identifiant de projet';
  name.placeholder='Ex. Fracture du Réseau-Mère';

  if(nameField&&!nameField.querySelector('[data-project-identifier-help]')){
    const help=document.createElement('small');
    help.dataset.projectIdentifierHelp='';
    help.textContent='Nom lisible du projet. L’identifiant technique des URL est généré automatiquement et reste stable.';
    help.style.display='block';
    help.style.marginTop='6px';
    help.style.color='var(--muted)';
    nameField.appendChild(help);
  }
  if(slugField)slugField.hidden=true;

  form.addEventListener('submit',()=>{
    if(!String(slug.value||'').trim())slug.value=projectSlug(name.value);
  },true);

  const list=document.querySelector('[data-admin-project-list]');
  if(list){
    relabelProjectRows();
    new MutationObserver(relabelProjectRows).observe(list,{childList:true,subtree:true});
  }
}

function adminActions(){
  return document.querySelector('.hero-actions')||document.querySelector('.admin-console-layout section');
}
function installHeritageLink(){
  if(document.querySelector('[data-admin-heritage-link]'))return;
  const actions=adminActions();
  if(!actions)return;
  const link=document.createElement('a');
  link.href='/admin/sinjira/heritage.html';
  link.className='btn btn-secondary';
  link.dataset.adminHeritageLink='';
  link.textContent='Héritage numérique';
  actions.appendChild(link);
}
function installPreorderLink(){
  if(document.querySelector('[data-admin-preorders-link]'))return;
  const actions=adminActions();
  if(!actions)return;
  const link=document.createElement('a');
  link.href='/admin/sinjira/precommandes.html';
  link.className='btn btn-secondary';
  link.dataset.adminPreordersLink='';
  link.textContent='Précommandes du Livre I';
  actions.appendChild(link);
}

configureProjectIdentifier();
installHeritageLink();
installPreorderLink();
