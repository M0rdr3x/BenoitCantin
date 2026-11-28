/* Accueil public : la lecture et la navigation ne déclenchent pas
 * inutilement la personnalisation de session. Le lien Compte reste natif. */
(function(){
  'use strict';
  var root=document.documentElement;
  var selector='[data-sinjira-session-nav]';
  var loaded=false;
  var timer=null;
  var events=['pointerdown','focusin'];
  function syncOffline(){
    root.classList.toggle('offline',!navigator.onLine);
  }
  syncOffline();
  window.addEventListener('online',syncOffline);
  window.addEventListener('offline',syncOffline);
  function loadSession(){
    if(loaded)return;
    loaded=true;
    if(timer!==null)window.clearTimeout(timer);
    events.forEach(function(type){
      document.removeEventListener(type,onIntent,true);
    });
    window.removeEventListener('load',arm);
    import('./v19-session.js?v=24.5.1').catch(function(){});
  }
  function isAccountTarget(target){
    return target instanceof Element && !!target.closest(selector);
  }
  function onIntent(event){
    if(isAccountTarget(event.target))loadSession();
  }
  function arm(){
    if(!loaded&&timer===null)timer=window.setTimeout(loadSession,60000);
  }
  events.forEach(function(type){
    document.addEventListener(type,onIntent,{capture:true,passive:true});
  });
  if(isAccountTarget(document.activeElement))loadSession();
  if(!loaded){
    if(document.readyState==='complete')arm();
    else window.addEventListener('load',arm,{once:true});
  }
}());
