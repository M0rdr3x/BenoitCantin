/* Charger le module de commentaires uniquement à proximité de la rubrique.
 * Le lien de connexion et les contrôles de sécurité serveur restent inchangés. */
(function(){
  'use strict';
  const section=document.getElementById('commentaires');
  if(!section)return;
  const list=section.querySelector('[data-novel-comments]');
  if(!list)return;
  let started=false;
  let observer;
  function load(){
    if(started)return;
    started=true;
    observer?.disconnect();
    window.removeEventListener('hashchange',onHash);
    section.removeEventListener('focusin',load);
    section.dataset.commentsLoading='true';
    list.textContent='Chargement des commentaires…';
    import('./sinjira-reader.js?v=25.1.3').catch(()=>{
      section.dataset.commentsLoading='error';
      list.textContent='Les commentaires sont temporairement indisponibles. Rechargez la page pour réessayer.';
    });
  }
  function onHash(){
    if(location.hash==='#commentaires'||location.hash==='#sinjira-commentaire-texte')load();
  }
  section.addEventListener('focusin',load);
  window.addEventListener('hashchange',onHash);
  onHash();
  if(started)return;
  if('IntersectionObserver' in window){
    observer=new IntersectionObserver(entries=>{
      if(entries.some(entry=>entry.isIntersecting))load();
    },{rootMargin:'600px 0px'});
    observer.observe(section);
  }else{
    load();
  }
})();
