/* Navigation de présentation uniquement. Aucun accès réseau, aucune autorisation. */
function structure(){
  const main=document.querySelector('.admin-console-layout');
  const nav=main?.querySelector('.admin-console-tabs');
  if(!main||!nav)return null;
  const buttons=[...nav.querySelectorAll('button[data-admin-tab]')];
  const panels=[...main.querySelectorAll('[data-admin-panel]')];
  const pairs=buttons.flatMap(button=>{
    const name=button.dataset.adminTab;
    if(!/^[a-z][a-z0-9-]*$/.test(name||'')||buttons.filter(b=>b.dataset.adminTab===name).length!==1)return [];
    const matches=panels.filter(p=>p.dataset.adminPanel===name);
    return matches.length===1?[{name,button,panel:matches[0]}]:[];
  });
  return {nav,pairs,buttons,panels};
}
export function prepareAdminNavigation(){
  const state=structure();
  if(!state)return;
  for(const {name,button,panel} of state.pairs){
    if(!panel.id)panel.id='admin-panel-'+name;
    if(!button.id)button.id='admin-tab-'+name;
    button.setAttribute('aria-controls',panel.id);
    panel.setAttribute('aria-labelledby',button.id);
    const heading=panel.querySelector('h2,h3');
    if(heading)heading.tabIndex=-1;
    if(!panel.querySelector(':scope > .admin-panel-return')){
      const back=document.createElement('a');
      back.href='#admin-sections';
      back.className='btn btn-secondary admin-panel-return';
      back.textContent='Retour aux rubriques';
      back.addEventListener('click',event=>{
        event.preventDefault();
        if(button.isConnected&&!button.disabled){
          button.focus({preventScroll:true});
          button.scrollIntoView({block:'center',behavior:'instant'});
        }
      });
      panel.prepend(back);
    }
  }
}
export function openAdminPanel(name){
  prepareAdminNavigation();
  const state=structure();
  const target=state?.pairs.find(pair=>pair.name===name);
  if(!target||target.button.disabled)return false;
  for(const button of state.buttons){
    if(button===target.button)button.setAttribute('aria-current','page');
    else button.removeAttribute('aria-current');
  }
  for(const panel of state.panels)panel.hidden=panel!==target.panel;
  const heading=target.panel.querySelector('h2,h3')||target.panel;
  heading.tabIndex=-1;
  heading.focus({preventScroll:true});
  heading.scrollIntoView({block:'start',behavior:'instant'});
  return true;
}
