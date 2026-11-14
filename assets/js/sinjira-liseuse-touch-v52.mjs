/**
 * SINJIRA V52 — navigation tactile dans le roman (démo et édition intégrale).
 *
 * Module indépendant du moteur de progression : une page est changée par le
 * même bouton natif que la navigation au clavier. Aucune donnée de roman,
 * authentification, stockage privé ou synchronisation cloud n'est manipulée.
 * Supports iOS Safari / Android / tablette via événements TouchEvent.
 */
const INTERACTIVE='a, button, input, select, textarea, summary, [contenteditable], [role="button"], [role="link"], [data-reader-no-swipe]';

export function classifyReaderSwipe({
  dx,dy,durationMs,viewerWidth=360,hasSelection=false,horizontalOverflow=false,
  maxVerticalTravel=0,scrolledDuringGesture=false
}={}){
  if(hasSelection||horizontalOverflow||scrolledDuringGesture||
     ![dx,dy,durationMs,viewerWidth,maxVerticalTravel].every(Number.isFinite)||
     maxVerticalTravel<0||durationMs<0||durationMs>1800||viewerWidth<=0)return null;
  const distance=Math.abs(dx),vertical=Math.max(Math.abs(dy),maxVerticalTravel);
  // V79 : conserver les gestes lents volontaires. Exiger un mouvement plus
  // ample et plus horizontal après 850 ms pour refuser les longues pressions.
  const threshold=Math.max(56,Math.min(100,viewerWidth*0.14));
  const slow=durationMs>850;
  const requiredDistance=slow?Math.max(112,threshold*1.5):threshold;
  const requiredDirection=slow?2.2:1.65;
  if(distance<requiredDistance||distance<vertical*requiredDirection)return null;
  return dx<0?'next':'previous';
}

/**
 * V71 : le zoom par pincement agrandit le viewport visuel sans toujours
 * modifier scrollWidth. Pendant ce zoom, un doigt doit déplacer la page
 * normalement plutôt que déclencher un changement de page PDF/texte.
 */
export function isReaderViewportZoomed({scale=globalThis.window?.visualViewport?.scale}={}){
  return Number.isFinite(scale)&&scale>1.01;
}
/** V72 : un changement d'orientation ou de taille pendant un contact
 * invalide le balayage pour éviter un faux passage de page. Les dimensions
 * absentes dans les moteurs anciens sont ignorées, pas extrapolées. */
export function captureReaderSwipeGeometry(viewer,win=globalThis.window){
  return {
    readerWidth:viewer?.clientWidth,readerHeight:viewer?.clientHeight,
    viewportWidth:win?.innerWidth,viewportHeight:win?.innerHeight
  };
}
/** V74 : la largeur de contenu ne signifie pas un pan tactile possible.
 * En mode « pages d'écran », le lecteur utilise overflow-x:hidden; certains
 * mots, tableaux et ornements restent plus larges que leur boîte sans être
 * parcourables horizontalement. Ne réservez le swipe au navigateur que si
 * un conteneur réellement défilable peut recevoir ce geste.
 * Style indisponible : prudence, ne pas voler un éventuel défilement. */
export function readerCanPanHorizontally(element,tolerancePx=4,
  getStyle=globalThis.window?.getComputedStyle?.bind(globalThis.window)){
  if(!element||!Number.isFinite(tolerancePx)||tolerancePx<0||
    !Number.isFinite(element.scrollWidth)||!Number.isFinite(element.clientWidth)||
    element.scrollWidth<=element.clientWidth+tolerancePx)return false;
  let overflowX;
  try{overflowX=getStyle?.(element)?.overflowX}catch{/* style inaccessible */}
  return !['hidden','clip','visible'].includes(String(overflowX||'').toLowerCase());
}
/** V77 : mémoriser les véritables déplacements latéraux des tableaux et
 * encadrés imbriqués sans bloquer les pages sur un panneau immobile.
 * Ne jamais inspecter hors de la zone de lecture. */
export function captureReaderNestedHorizontalScroll(target,viewer,tolerancePx=4){
  if(!target||!viewer||!Number.isFinite(tolerancePx)||tolerancePx<0)return [];
  const seen=new Set(),captured=[];
  let node=target;
  while(node&&!seen.has(node)){
    if(node===viewer)return captured;
    seen.add(node);
    if(readerCanPanHorizontally(node,tolerancePx))
      captured.push({node,scrollLeft:Number.isFinite(node.scrollLeft)?node.scrollLeft:0});
    node=node.parentElement||node.parentNode;
  }
  return [];
}
export function readerNestedHorizontalScrollMoved(captured,tolerancePx=4){
  if(!Array.isArray(captured)||!Number.isFinite(tolerancePx)||tolerancePx<0)return false;
  return captured.some(({node,scrollLeft})=>
    Number.isFinite(node?.scrollLeft)&&Math.abs(node.scrollLeft-scrollLeft)>tolerancePx
  );
}
/** V75 : un panneau vertical à l'intérieur d'une page ne doit pas
 * provoquer un changement de page quand on le fait défiler au doigt.
 * Les débordements CSS masqués n'ont pas de défilement tactile natif. */
export function readerCanPanVertically(element,tolerancePx=4,
  getStyle=globalThis.window?.getComputedStyle?.bind(globalThis.window)){
  if(!element||!Number.isFinite(tolerancePx)||tolerancePx<0||
    !Number.isFinite(element.scrollHeight)||!Number.isFinite(element.clientHeight)||
    element.scrollHeight<=element.clientHeight+tolerancePx)return false;
  let overflowY;
  try{overflowY=getStyle?.(element)?.overflowY}catch{/* API CSS inaccessible */}
  return !['hidden','clip','visible'].includes(String(overflowY||'').toLowerCase());
}
/** Limiter la détection aux descendants véritables de la zone de lecture. */
export function hasReaderNestedVerticalOverflow(target,viewer,tolerancePx=4){
  if(!target||!viewer||!Number.isFinite(tolerancePx)||tolerancePx<0)return false;
  const visited=new Set();
  let found=false,node=target;
  while(node&&!visited.has(node)){
    if(node===viewer)return found;
    visited.add(node);
    if(readerCanPanVertically(node,tolerancePx))found=true;
    node=node.parentElement||node.parentNode;
  }
  return false;
}
/** V76 : relever les positions de défilement *des notes seulement*.
 * Une note verticalement défilable qui n'a pas bougé ne doit pas empêcher
 * un geste horizontal volontaire de changer de page. */
export function captureReaderNestedVerticalScroll(target,viewer,tolerancePx=4){
  if(!target||!viewer||!Number.isFinite(tolerancePx)||tolerancePx<0)return [];
  const visited=new Set();
  const captured=[];
  let node=target;
  while(node&&!visited.has(node)){
    if(node===viewer)return captured;
    visited.add(node);
    if(readerCanPanVertically(node,tolerancePx))
      captured.push({node,scrollTop:Number.isFinite(node.scrollTop)?node.scrollTop:0});
    node=node.parentElement||node.parentNode;
  }
  return [];
}
export function readerNestedVerticalScrollMoved(captured,tolerancePx=4){
  if(!Array.isArray(captured)||!Number.isFinite(tolerancePx)||tolerancePx<0)return false;
  return captured.some(({node,scrollTop})=>
    Number.isFinite(node?.scrollTop)&&Math.abs(node.scrollTop-scrollTop)>tolerancePx
  );
}
/** V73 : le texte peut contenir un tableau ou une annotation défilant
 * horizontalement dans son propre conteneur, sans agrandir le lecteur.
 * Un tel geste doit rester au conteneur, pas tourner une page du roman.
 * N'inspecter que les ancêtres appartenant effectivement au lecteur. */
export function hasReaderNestedHorizontalOverflow(target,viewer,tolerancePx=4){
  if(!target||!viewer||!Number.isFinite(tolerancePx)||tolerancePx<0)return false;
  const visited=new Set();
  let overflow=false,node=target;
  while(node&&!visited.has(node)){
    if(node===viewer)return overflow;
    visited.add(node);
    if(readerCanPanHorizontally(node,tolerancePx))overflow=true;
    node=node.parentElement||node.parentNode;
  }
  return false;
}
export function isReaderSwipeGeometryStable(before,after,tolerancePx=4){
  if(!before||!after||!Number.isFinite(tolerancePx)||tolerancePx<0)return false;
  for(const key of ['readerWidth','readerHeight','viewportWidth','viewportHeight']){
    const first=before[key],last=after[key];
    const a=Number.isFinite(first),b=Number.isFinite(last);
    if(a!==b||a&&Math.abs(first-last)>tolerancePx)return false;
  }
  return true;
}
/**
 * V67 : préserver les gestes système aux 24 pixels des bords du viewport.
 */
export function isReaderSystemEdgeGesture({clientX,viewportWidth,edgePx=24}={}){
  if(![clientX,viewportWidth,edgePx].every(Number.isFinite)||
     edgePx<=0||viewportWidth<=edgePx*3)return false;
  return clientX>=0&&(clientX<=edgePx||clientX>=viewportWidth-edgePx);
}
function isInteractiveTarget(target){
  return Boolean(target&&typeof target.closest==='function'&&target.closest(INTERACTIVE));
}

export function bindReaderTouchNavigation({
  viewer,previous,next,mobilePrevious=null,mobileNext=null,
  getSelectedText=()=>typeof window==='undefined'?'':String(window.getSelection?.()?.toString()||''),
  clock=()=>typeof performance!=='undefined'?performance.now():Date.now(),
  Observer=typeof MutationObserver!=='undefined'?MutationObserver:null
}={}){
  if(!viewer||!previous||!next)throw new Error('V52: zone ou boutons de lecture absents');
  // Marqueur partagé avec le module historique V28 : V52 devient l'unique
  // propriétaire du geste, que le lecteur soit en mode PDF ou écran texte.
  if(viewer.dataset)viewer.dataset.readerTouchManaged='v52';
  let origin=null;
  const start=event=>{
    origin=null;
    if(event.touches?.length!==1||isInteractiveTarget(event.target)||
      isReaderViewportZoomed())return;
    const touch=event.touches[0];
    if(!Number.isFinite(touch.clientX)||!Number.isFinite(touch.clientY))return;
    // Ne pas intercepter un geste de navigation système démarrant sur le bord.
    if(isReaderSystemEdgeGesture({
      clientX:touch.clientX,viewportWidth:globalThis.window?.innerWidth
    }))return;
    origin={
      id:touch.identifier,x:touch.clientX,y:touch.clientY,time:clock(),
      scrollTop:viewer.scrollTop||0,maxVerticalTravel:0,scrolled:false,
      readerLayout:viewer.dataset?.readerLayout||'scroll',
      geometry:captureReaderSwipeGeometry(viewer),
      nestedHorizontalScroll:captureReaderNestedHorizontalScroll(event.target,viewer),
      nestedHorizontalScrolled:false,
      nestedVerticalScroll:captureReaderNestedVerticalScroll(event.target,viewer),
      nestedScrolled:false
    };
  };
  const move=event=>{
    // V66 : un défilement vertical intermédiaire puis un retour au point de
    // départ ne doit jamais être interprété comme une page tournée.
    if(!origin)return;
    if(event.touches?.length!==1||isReaderViewportZoomed()||
      origin.readerLayout!==(viewer.dataset?.readerLayout||'scroll')||
      !isReaderSwipeGeometryStable(origin.geometry,captureReaderSwipeGeometry(viewer))){
      origin=null;return;
    }
    const touch=event.touches[0];
    if(touch.identifier!==origin.id||!Number.isFinite(touch.clientY)){
      origin=null;return;
    }
    origin.maxVerticalTravel=Math.max(
      origin.maxVerticalTravel,Math.abs(touch.clientY-origin.y)
    );
    if(Math.abs((viewer.scrollTop||0)-origin.scrollTop)>8)origin.scrolled=true;
    if(readerNestedVerticalScrollMoved(origin.nestedVerticalScroll))origin.nestedScrolled=true;
    if(readerNestedHorizontalScrollMoved(origin.nestedHorizontalScroll))
      origin.nestedHorizontalScrolled=true;
  };
  const cancel=()=>{origin=null};
  const end=event=>{
    const initial=origin;
    origin=null;
    // Le mode V53 « pages d'écran » possède son propre gestionnaire tactile.
    // Ne JAMAIS déclencher ici le changement de page PDF quand V53 est actif,
    // même si preventDefault() n'a pas été honoré sur un appareil tactile.
    if(viewer.dataset?.readerLayout==='screens')return;
    if(!initial||isReaderViewportZoomed()||
      initial.readerLayout!==(viewer.dataset?.readerLayout||'scroll')||
      !isReaderSwipeGeometryStable(initial.geometry,captureReaderSwipeGeometry(viewer))||
      event.touches?.length!==0||event.changedTouches?.length!==1)return;
    const touch=event.changedTouches[0];
    if(touch.identifier!==initial.id||event.defaultPrevented)return;
    const direction=classifyReaderSwipe({
      dx:touch.clientX-initial.x,dy:touch.clientY-initial.y,
      durationMs:clock()-initial.time,viewerWidth:viewer.clientWidth,
      hasSelection:Boolean(getSelectedText()?.trim()),
      horizontalOverflow:readerCanPanHorizontally(viewer)||
        initial.nestedHorizontalScrolled||
        readerNestedHorizontalScrollMoved(initial.nestedHorizontalScroll),
      maxVerticalTravel:initial.maxVerticalTravel,
      scrolledDuringGesture:initial.nestedScrolled||
        readerNestedVerticalScrollMoved(initial.nestedVerticalScroll)||
        initial.scrolled||Math.abs((viewer.scrollTop||0)-initial.scrollTop)>8
    });
    const button=direction==='next'?next:direction==='previous'?previous:null;
    if(button&&!button.disabled)button.click();
  };
  // Listeners passifs : conserver le scroll vertical, le pinch-to-zoom,
  // le menu de sélection et les gestes des technologies d'assistance.
  viewer.addEventListener('touchstart',start,{passive:true});
  viewer.addEventListener('touchmove',move,{passive:true});
  viewer.addEventListener('touchcancel',cancel,{passive:true});
  viewer.addEventListener('touchend',end,{passive:true});

  const mobileBack=()=>{
    if(viewer.dataset?.readerLayout!=='screens'&&!previous.disabled)previous.click();
  };
  const mobileForward=()=>{
    if(viewer.dataset?.readerLayout!=='screens'&&!next.disabled)next.click();
  };
  mobilePrevious?.addEventListener('click',mobileBack);
  mobileNext?.addEventListener('click',mobileForward);

  const reflectDisabled=()=>{
    if(mobilePrevious)mobilePrevious.disabled=previous.disabled;
    if(mobileNext)mobileNext.disabled=next.disabled;
  };
  const observer=Observer?new Observer(reflectDisabled):null;
  observer?.observe(previous,{attributes:true,attributeFilter:['disabled']});
  observer?.observe(next,{attributes:true,attributeFilter:['disabled']});
  reflectDisabled();
  return ()=>{
    origin=null;
    if(viewer.dataset?.readerTouchManaged==='v52')delete viewer.dataset.readerTouchManaged;
    viewer.removeEventListener('touchstart',start);
    viewer.removeEventListener('touchmove',move);
    viewer.removeEventListener('touchcancel',cancel);
    viewer.removeEventListener('touchend',end);
    mobilePrevious?.removeEventListener('click',mobileBack);
    mobileNext?.removeEventListener('click',mobileForward);
    observer?.disconnect();
  };
}
function initTouchReader(){
  const viewer=document.getElementById('reader-viewer');
  const previous=document.getElementById('reader-previous');
  const next=document.getElementById('reader-next');
  if(!viewer||!previous||!next)return;
  bindReaderTouchNavigation({
    viewer,previous,next,
    mobilePrevious:document.getElementById('reader-touch-prev'),
    mobileNext:document.getElementById('reader-touch-next')
  });
}
if(typeof document!=='undefined'){
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initTouchReader,{once:true});
  else initTouchReader();
}
