/* SINJIRA — initialisation très précoce du menu responsive.
 * Empêche le décalage visuel avant chargement de site.js.
 * En cas de JS désactivé, de script bloqué ou de panne, la navigation
 * HTML native reste disponible grâce à la feuille CSS de secours. */
(function(){
  'use strict';
  var root=document.documentElement;
  root.setAttribute('data-sinjira-nav-ready','true');
  function restore(){
    if(root.getAttribute('data-sinjira-nav-initialized')==='true')return;
    root.removeAttribute('data-sinjira-nav-ready');
  }
  window.addEventListener('error',function(event){
    var node=event.target;
    if(node&&node.tagName==='SCRIPT'&&/\/assets\/js\/site\.js(?:\?|#|$)/.test(node.src||'')){
      restore();
    }
  },true);
  document.addEventListener('DOMContentLoaded',restore,{once:true});
})();
