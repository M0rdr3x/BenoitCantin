(function(){
  'use strict';
  var path=String(location.pathname||'').toLowerCase();
  if(path.indexOf('/compte/')!==0||!document.body||!document.body.classList.contains('account-page'))return;
  var excluded=['/compte/connexion.html','/compte/inscription.html','/compte/mot-de-passe-oublie.html','/compte/reinitialiser-mot-de-passe.html','/compte/mfa.html'];
  if(excluded.indexOf(path)!==-1)return;
  if(document.querySelector('[data-sinjira-account-mobile-nav]'))return;

  document.body.classList.add('sinjira-mobile-account-shell');
  var nav=document.createElement('nav');
  nav.className='sinjira-account-mobile-nav';
  nav.setAttribute('aria-label','Navigation principale mobile SINJIRA');
  nav.setAttribute('data-sinjira-account-mobile-nav','');

  var items=[
    {key:'feed',href:'/app/',label:'Fil',icon:'<path d="M3 11.5 12 4l9 7.5V21h-6v-6H9v6H3v-9.5Z"/>'},
    {key:'world',href:'/compte/monde-parallele.html',label:'Monde',icon:'<circle cx="12" cy="12" r="8"/><path d="M4.5 9h15M4.5 15h15M12 4c2.2 2.2 3.2 4.9 3.2 8S14.2 17.8 12 20M12 4C9.8 6.2 8.8 8.9 8.8 12s1 5.8 3.2 8"/>'},
    {key:'messages',href:'/compte/messages.html',label:'Messages',icon:'<path d="M4 5.5h16v11H8l-4 3v-14Z"/>'},
    {key:'alerts',href:'/compte/notifications.html',label:'Alertes',icon:'<path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 8.5h18C21 16 18 16 18 9ZM9.5 20h5"/>'},
    {key:'profile',href:'/compte/profil.html',label:'Profil',icon:'<circle cx="12" cy="8" r="4"/><path d="M4.5 21c.7-4.2 3.2-6.5 7.5-6.5s6.8 2.3 7.5 6.5"/>'}
  ];

  function activeKey(){
    if(path.indexOf('/compte/monde-parallele')===0)return 'world';
    if(path.indexOf('/compte/messages')===0)return 'messages';
    if(path.indexOf('/compte/notifications')===0)return 'alerts';
    if(path.indexOf('/compte/profil')===0||path.indexOf('/compte/parametres')===0||path.indexOf('/compte/securite')===0)return 'profile';
    if(path.indexOf('/compte/communaute')===0)return 'feed';
    return '';
  }
  var active=activeKey();
  for(var i=0;i<items.length;i+=1){
    var item=items[i],a=document.createElement('a');
    a.href=item.href;
    a.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true">'+item.icon+'</svg><span>'+item.label+'</span>';
    // aria-current=page seulement si ce lien pointe vers la page exacte.
    // Une page liée (p. ex. Sécurité > Profil) conserve l'accent visuel
    // sans être annoncée à tort comme la page courante.
    if(item.key===active){
      if(path===item.href || (item.href==='/app/' && path==='/app/index.html')){
        a.setAttribute('aria-current','page');
      }else{
        a.setAttribute('data-current-section','');
      }
    }
    nav.appendChild(a);
  }
  document.body.appendChild(nav);

  // Sur 240 px et en zoom fort, le dock est défilant. Ne jamais laisser
  // la rubrique en cours hors de vue au chargement ou après une rotation.
  // On n'intervient pas lors d'un balayage manuel (aucun listener scroll).
  var activeLink=nav.querySelector('a[aria-current="page"],a[data-current-section]');
  function revealActiveLink(){
    if(!activeLink||!window.matchMedia('(max-width:270px)').matches)return;
    if(getComputedStyle(nav).display==='none'||nav.scrollWidth<=nav.clientWidth+2)return;
    var area=nav.getBoundingClientRect();
    var link=activeLink.getBoundingClientRect();
    if(link.left>=area.left+2&&link.right<=area.right-2)return;
    var max=Math.max(0,nav.scrollWidth-nav.clientWidth);
    var target=nav.scrollLeft+link.left-area.left-
      Math.max(0,Math.round((nav.clientWidth-link.width)/2));
    nav.scrollLeft=Math.max(0,Math.min(max,target));
  }
  function syncAfterLayout(){
    syncNavHeight();
    revealActiveLink();
  }

  // Le dock peut grandir lorsque la police est agrandie : réserver sa
  // hauteur réelle au contenu et au bandeau d'installation PWA.
  var lastHeight=0;
  function syncNavHeight(){
    var height=Math.ceil(nav.getBoundingClientRect().height);
    if(!height || height===lastHeight)return;
    lastHeight=height;
    document.body.style.setProperty('--sinjira-account-mobile-nav-height',height+'px');
  }
  syncNavHeight();
  window.requestAnimationFrame(revealActiveLink);
  window.addEventListener('resize',function(){
    window.requestAnimationFrame(syncAfterLayout);
  });
  if('ResizeObserver' in window){
    var navObserver=new ResizeObserver(syncAfterLayout);
    navObserver.observe(nav);
  }
}());
