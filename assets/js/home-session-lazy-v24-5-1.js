(function(){
  'use strict';
  var loaded=false;
  var timer=null;
  var events=['pointerdown','touchstart','keydown'];
  function loadSession(){
    if(loaded)return;
    loaded=true;
    if(timer!==null)window.clearTimeout(timer);
    window.removeEventListener('load',arm);
    events.forEach(function(type){window.removeEventListener(type,loadSession);});
    import('./v19-session.js?v=24.5.1').catch(function(){});
  }
  function arm(){
    if(loaded)return;
    timer=window.setTimeout(loadSession,60000);
  }
  // Une interaction clavier ou tactile peut arriver avant window.load.
  // Installer les écouteurs immédiatement, mais conserver le délai de
  // repli après le chargement et ne jamais importer deux fois la session.
  events.forEach(function(type){
    window.addEventListener(type,loadSession,{once:true,passive:type!=='keydown'});
  });
  if(document.readyState==='complete')arm();
  else window.addEventListener('load',arm,{once:true});
}());
