/* Univers public : le lien Compte reste un lien natif.
 * La personnalisation de la navigation ne doit pas bloquer le premier affichage. */
(function(){
  'use strict';
  const root=document.documentElement;
  const syncOffline=()=>root.classList.toggle('offline',!navigator.onLine);
  syncOffline();
  window.addEventListener('online',syncOffline);
  window.addEventListener('offline',syncOffline);
  let started=false;
  let timer=null;
  const events=['pointerdown','focusin'];
  function load(){
    if(started)return;
    started=true;
    if(timer!==null)window.clearTimeout(timer);
    for(const type of events)document.removeEventListener(type,onIntent,true);
    window.removeEventListener('load',arm);
    root.dataset.universeSessionLoading='true';
    import('./v19-session.js?v=24.4.12').catch(()=>{
      root.dataset.universeSessionLoading='error';
    });
  }
  function onIntent(event){
    const target=event.target;
    if(target instanceof Element && target.closest('[data-sinjira-session-nav], [data-menu-toggle]'))load();
  }
  function arm(){
    if(!started&&timer===null)timer=window.setTimeout(load,60000);
  }
  for(const type of events)document.addEventListener(type,onIntent,{capture:true,passive:true});
  if(document.readyState==='complete')arm();
  else window.addEventListener('load',arm,{once:true});
})();
