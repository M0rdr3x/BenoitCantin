(function(){
  'use strict';
  var loaded=false;
  var timer=null;
  function loadSession(){
    if(loaded)return;
    loaded=true;
    if(timer)window.clearTimeout(timer);
    import('./v19-session.js?v=24.5.1').catch(function(){});
  }
  function arm(){
    ['pointerdown','touchstart','keydown'].forEach(function(type){
      window.addEventListener(type,loadSession,{once:true,passive:type!=='keydown'});
    });
    timer=window.setTimeout(loadSession,8000);
  }
  if(document.readyState==='complete')arm();
  else window.addEventListener('load',arm,{once:true});
}());
