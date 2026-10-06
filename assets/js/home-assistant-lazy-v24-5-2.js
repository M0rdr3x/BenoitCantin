(function(){
  'use strict';
  var d=document,w=window,loaded=false,timer=null;
  var VERSION='24.4.48';

  function loadAssistant(){
    if(loaded)return;
    loaded=true;
    if(timer)w.clearTimeout(timer);
    if(!d.querySelector('link[data-sinjira-assistant-style]')){
      var style=d.createElement('link');
      style.rel='stylesheet';
      style.href='/assets/css/sinjira-assistant.css?v='+VERSION;
      style.setAttribute('data-sinjira-assistant-style','');
      d.head.appendChild(style);
    }
    if(!d.querySelector('script[data-sinjira-assistant-script]')){
      var script=d.createElement('script');
      script.src='/assets/js/sinjira-assistant.js?v='+VERSION;
      script.defer=true;
      script.setAttribute('data-sinjira-assistant-script','');
      d.head.appendChild(script);
    }
  }

  function arm(){
    var events=['pointerdown','touchstart','keydown','scroll'];
    for(var i=0;i<events.length;i+=1){
      w.addEventListener(events[i],loadAssistant,{once:true,passive:events[i]!=='keydown'});
    }
    timer=w.setTimeout(loadAssistant,12000);
  }

  if(d.readyState==='complete')arm();
  else w.addEventListener('load',arm,{once:true});
}());
