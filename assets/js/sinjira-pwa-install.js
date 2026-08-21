(function(){
  'use strict';
  var w=window,d=document;
  var deferredPrompt=null;
  var dismissedKey='sinjira-pwa-install-dismissed-v24-4-93';

  function standalone(){
    return !!(w.navigator.standalone || (w.matchMedia && (w.matchMedia('(display-mode: standalone)').matches || w.matchMedia('(display-mode: fullscreen)').matches || w.matchMedia('(display-mode: minimal-ui)').matches)));
  }
  function eligibleRoute(){
    var p=location.pathname.toLowerCase();
    return p==='/' || p==='/projets/sinjira/' || p==='/compte/' || p==='/compte/index.html';
  }
  function isIos(){return /iphone|ipad|ipod/i.test(navigator.userAgent||'') && !w.MSStream;}
  function dismissed(){try{return sessionStorage.getItem(dismissedKey)==='1';}catch(e){return false;}}
  function rememberDismiss(){try{sessionStorage.setItem(dismissedKey,'1');}catch(e){}}

  function ensureHeadLinks(){
    if(!d.querySelector('link[rel="manifest"]')){
      var manifest=d.createElement('link');manifest.rel='manifest';manifest.href='/manifest.webmanifest';d.head.appendChild(manifest);
    }
    if(!d.querySelector('link[rel="apple-touch-icon"]')){
      var icon=d.createElement('link');icon.rel='apple-touch-icon';icon.href='/android-chrome-192x192.png';d.head.appendChild(icon);
    }
  }

  function registerWorker(){
    if(!('serviceWorker' in navigator))return;
    navigator.serviceWorker.register('/sw.js',{scope:'/'}).catch(function(){});
  }

  function loadMobileAccountShell(){
    var p=location.pathname.toLowerCase();
    if(p.indexOf('/compte/')!==0)return;
    var excluded=['/compte/connexion.html','/compte/inscription.html','/compte/mot-de-passe-oublie.html','/compte/reinitialiser-mot-de-passe.html','/compte/mfa.html'];
    if(excluded.indexOf(p)!==-1)return;
    if(!d.querySelector('link[data-sinjira-mobile-account-shell]')){
      var style=d.createElement('link');style.rel='stylesheet';style.href='/assets/css/sinjira-mobile-account-shell-v24-4-95.css?v=24.4.95';style.setAttribute('data-sinjira-mobile-account-shell','');d.head.appendChild(style);
    }
    if(!d.querySelector('script[data-sinjira-mobile-account-shell]')){
      var script=d.createElement('script');script.src='/assets/js/sinjira-mobile-account-shell-v24-4-95.js?v=24.4.95';script.defer=true;script.setAttribute('data-sinjira-mobile-account-shell','');d.head.appendChild(script);
    }
  }

  function addStyle(){
    if(d.querySelector('[data-sinjira-pwa-style]'))return;
    var s=d.createElement('style');s.setAttribute('data-sinjira-pwa-style','');
    s.textContent='.sinjira-pwa-install{position:fixed;right:max(14px,env(safe-area-inset-right));bottom:max(14px,env(safe-area-inset-bottom));z-index:9997;width:min(390px,calc(100vw - 28px));padding:16px;border:1px solid rgba(255,255,255,.16);border-radius:18px;background:rgba(10,12,22,.96);box-shadow:0 18px 50px rgba(0,0,0,.38);backdrop-filter:blur(14px);color:#fff}.sinjira-pwa-install[hidden]{display:none}.sinjira-pwa-install__top{display:flex;gap:12px;align-items:flex-start}.sinjira-pwa-install__top img{width:44px;height:44px;border-radius:12px}.sinjira-pwa-install h2{font-size:1rem;margin:0 0 5px}.sinjira-pwa-install p{font-size:.88rem;line-height:1.45;margin:0;color:rgba(255,255,255,.78)}.sinjira-pwa-install__actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:13px}.sinjira-pwa-install__actions button{min-height:42px}.sinjira-pwa-install__close{position:absolute;right:8px;top:7px;border:0;background:transparent;color:#fff;font-size:1.25rem;padding:6px 9px;cursor:pointer}.sinjira-pwa-install__ios{margin-top:10px!important;color:rgba(255,255,255,.9)!important}@media(max-width:600px){.sinjira-pwa-install{left:14px;right:14px;bottom:max(12px,env(safe-area-inset-bottom));width:auto}}';
    d.head.appendChild(s);
  }

  function ensureCard(mode){
    if(standalone()||!eligibleRoute()||dismissed())return null;
    var old=d.querySelector('[data-sinjira-pwa-install]');if(old)return old;
    addStyle();
    var card=d.createElement('aside');card.className='sinjira-pwa-install';card.setAttribute('data-sinjira-pwa-install','');card.setAttribute('aria-label','Installer l’application SINJIRA™');
    card.innerHTML='<button class="sinjira-pwa-install__close" type="button" aria-label="Masquer cette proposition">×</button><div class="sinjira-pwa-install__top"><img src="/android-chrome-192x192.png" alt=""><div><h2>Installer SINJIRA™</h2><p>Ajoutez SINJIRA™ à votre téléphone comme une application. Aucun magasin d’applications ni service payant n’est nécessaire.</p></div></div><div class="sinjira-pwa-install__actions"><button class="btn btn-primary btn-small" type="button" data-pwa-install-action>Installer</button></div>';
    if(mode==='ios'){
      var note=d.createElement('p');note.className='sinjira-pwa-install__ios';note.setAttribute('data-pwa-ios-help','');note.textContent='Sur iPhone/iPad : touchez Partager, puis « Sur l’écran d’accueil ».';card.appendChild(note);
    }
    card.querySelector('.sinjira-pwa-install__close').addEventListener('click',function(){rememberDismiss();card.remove();});
    card.querySelector('[data-pwa-install-action]').addEventListener('click',install);
    d.body.appendChild(card);return card;
  }

  async function install(){
    if(deferredPrompt){
      var p=deferredPrompt;deferredPrompt=null;
      try{await p.prompt();var choice=await p.userChoice;if(choice&&choice.outcome==='accepted'){var c=d.querySelector('[data-sinjira-pwa-install]');if(c)c.remove();}}catch(e){}
      return;
    }
    if(isIos()){
      var note=d.querySelector('[data-pwa-ios-help]');if(note)note.textContent='Dans Safari : bouton Partager → « Sur l’écran d’accueil » → Ajouter.';
    }
  }

  w.addEventListener('beforeinstallprompt',function(event){
    event.preventDefault();deferredPrompt=event;ensureCard('prompt');
  });
  w.addEventListener('appinstalled',function(){deferredPrompt=null;var c=d.querySelector('[data-sinjira-pwa-install]');if(c)c.remove();});

  ensureHeadLinks();
  registerWorker();
  loadMobileAccountShell();
  if(isIos()&&!standalone()){
    if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',function(){ensureCard('ios');},{once:true});
    else ensureCard('ios');
  }
}());
