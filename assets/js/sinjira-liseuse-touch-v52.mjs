/**
 * SINJIRA V52 — navigation tactile dans le roman (démo et édition intégrale).
 *
 * Module indépendant du moteur de progression : une page est changée par le
 * même bouton natif que la navigation au clavier. Aucune donnée de roman,
 * authentification, stockage privé ou synchronisation cloud n'est manipulée.
 * Supports iOS Safari / Android / tablette via événements TouchEvent.
 */
const INTERACTIVE='a, button, input, select, textarea, summary, [contenteditable], [role="button"], [role="link"], [data-reader-no-swipe]';

// V120 : une seule indication de changement de page à la fois.
const activePageTurnFlashes=new WeakMap();
export function cancelReaderPageTurnFlash(viewer){
  if(!viewer)return false;
  const active=activePageTurnFlashes.get(viewer);
  if(!active)return false;
  activePageTurnFlashes.delete(viewer);
  try{active.cancel?.()}catch{/* annulation facultative, pas d'impact sur la lecture */}
  return true;
}
/** V119/V120 : retour visuel léger de page tournée, sans déplacer le roman.
 * Seuls les bords de la zone de lecture s'éclairent; aucun texte n'est lu,
 * aucune position n'est sauvegardée. Les préférences d'accessibilité
 * « réduire les animations » priment, aussi sur WebKit/iOS. */
export function flashReaderPageTurn(viewer,direction,{win=globalThis.window}={}){
  if((direction!=='next'&&direction!=='previous')||
     typeof viewer?.animate!=='function')return false;
  // V120 : annuler la précédente lumière avant toute nouvelle direction.
  // Si la préférence « réduire les animations » a changé entre-temps,
  // retirer aussi immédiatement l'effet précédent, sans en créer d'autre.
  cancelReaderPageTurnFlash(viewer);
  if(win?.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches)return false;
  const edge=direction==='next'?-26:26;
  try{
    const animation=viewer.animate([
      {boxShadow:`inset ${edge}px 0 0 rgba(108, 218, 204, .22)`},
      {boxShadow:'inset 0px 0 0 rgba(108, 218, 204, 0)'}
    ],{duration:180,easing:'ease-out'});
    if(animation&&typeof animation==='object'){
      activePageTurnFlashes.set(viewer,animation);
      const clear=()=>{
        if(activePageTurnFlashes.get(viewer)===animation)
          activePageTurnFlashes.delete(viewer);
      };
      animation.addEventListener?.('finish',clear,{once:true});
      animation.addEventListener?.('cancel',clear,{once:true});
    }
    return true;
  }catch{return false}
}

export function classifyReaderSwipe({
  dx,dy,durationMs,viewerWidth=360,hasSelection=false,horizontalOverflow=false,
  maxVerticalTravel=0,maxLeftTravel=0,maxRightTravel=0,scrolledDuringGesture=false
}={}){
  if(hasSelection||horizontalOverflow||scrolledDuringGesture||
     ![dx,dy,durationMs,viewerWidth,maxVerticalTravel,maxLeftTravel,maxRightTravel].every(Number.isFinite)||
     maxVerticalTravel<0||maxLeftTravel<0||maxRightTravel<0||durationMs<0||durationMs>1800||viewerWidth<=0)return null;
  const distance=Math.abs(dx),vertical=Math.max(Math.abs(dy),maxVerticalTravel);
  // V79 : conserver les gestes lents volontaires. Exiger un mouvement plus
  // ample et plus horizontal après 850 ms pour refuser les longues pressions.
  const threshold=Math.max(56,Math.min(100,viewerWidth*0.14));
  // V116 : un glissement d'abord franc dans le sens contraire de sa
  // direction finale n'est pas un changement de page volontaire.
  // Les micro-corrections sous le seuil tactile restent permises.
  if(dx<0&&maxRightTravel>=threshold||dx>0&&maxLeftTravel>=threshold)return null;
  const slow=durationMs>850;
  const requiredDistance=slow?Math.max(112,threshold*1.5):threshold;
  const requiredDirection=slow?2.2:1.65;
  if(distance<requiredDistance||distance<vertical*requiredDirection)return null;
  return dx<0?'next':'previous';
}

/** V97 — classificateur partagé des tapotements de marge pour texte et PDF.
 * Réserve le centre pour la sélection et les bords extérieurs aux gestes OS. */
export function classifyReaderEdgeTap({x,viewerWidth,durationMs,dx=0,dy=0,
  maxTravel=0,hasSelection=false,scrolled=false}={}){
  if(hasSelection||scrolled||![x,viewerWidth,durationMs,dx,dy,maxTravel]
    .every(Number.isFinite)||viewerWidth<240||durationMs<0||durationMs>300||
    Math.abs(dx)>12||Math.abs(dy)>12||maxTravel>12)return null;
  const margin=Math.max(28,viewerWidth*.07);
  const band=viewerWidth*.26;
  if(x>=margin&&x<=band)return 'previous';
  if(x>=viewerWidth-band&&x<=viewerWidth-margin)return 'next';
  return null;
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
  viewer,previous,next,mobilePrevious=null,mobileNext=null,pageField=null,
  getSelectedText=()=>typeof window==='undefined'?'':String(window.getSelection?.()?.toString()||''),
  clock=()=>typeof performance!=='undefined'?performance.now():Date.now(),
  Observer=typeof MutationObserver!=='undefined'?MutationObserver:null,
  win=globalThis.window,
  doc=globalThis.document
}={}){
  if(!viewer||!previous||!next)throw new Error('V52: zone ou boutons de lecture absents');
  // Marqueur partagé avec le module historique V28 : V52 devient l'unique
  // propriétaire du geste, que le lecteur soit en mode PDF ou écran texte.
  if(viewer.dataset)viewer.dataset.readerTouchManaged='v52';
  let origin=null,pointerOrigin=null;
  // V117 : une fin de geste sur la page source remplacée est périmée.
  // Valeur du champ de page, sans contenu de livre ou identité.
  const currentPage=()=>pageField?.value==null?null:String(pageField.value);
  // V122 : ne pas appliquer un toucher PDF à la vue texte, ni l'inverse,
  // si le mode a changé sans numéro de page ou événement canonique.
  const isPdfMode=()=>viewer.querySelector?.('#reader-text')?.hidden===true;
  // V96 : les PDF (édition intégrale incluse) ne doivent pas changer de page
  // tant que le contenu parent est masqué ou que l'onglet est suspendu.
  const canNavigate=()=>!globalThis.document?.hidden&&
    !viewer.closest?.('[hidden]');
  const start=event=>{
    origin=null;
    // V125 : ne pas reporter les mutations antérieures à un nouveau doigt.
    contentObserver?.takeRecords?.();
    if(!canNavigate()||event.touches?.length!==1||isInteractiveTarget(event.target)||
      isReaderViewportZoomed())return;
    const touch=event.touches[0];
    if(!Number.isFinite(touch.clientX)||!Number.isFinite(touch.clientY))return;
    // Ne pas intercepter un geste de navigation système démarrant sur le bord.
    if(isReaderSystemEdgeGesture({
      clientX:touch.clientX,viewportWidth:globalThis.window?.innerWidth
    }))return;
    origin={
      id:touch.identifier,x:touch.clientX,y:touch.clientY,time:clock(),
      bookPage:currentPage(),
      scrollTop:viewer.scrollTop||0,maxVerticalTravel:0,maxTravel:0,maxLeftTravel:0,maxRightTravel:0,scrolled:false,
      pdfMode:isPdfMode(),
      readerLayout:viewer.dataset?.readerLayout||'scroll',
      geometry:captureReaderSwipeGeometry(viewer),
      nestedHorizontalScroll:captureReaderNestedHorizontalScroll(event.target,viewer),
      nestedHorizontalScrolled:false,
      nestedVerticalScroll:captureReaderNestedVerticalScroll(event.target,viewer),
      nestedScrolled:false
    };
  };
  const move=event=>{
    // V125 : le callback MutationObserver est différé; une fin de geste
    // peut précéder la micro-tâche si l'affichage bascule deux fois de suite.
    if(cancelPendingContentChanges())return;
    // V66 : un défilement vertical intermédiaire puis un retour au point de
    // départ ne doit jamais être interprété comme une page tournée.
    if(!origin)return;
    if(event.touches?.length!==1||isReaderViewportZoomed()||
      origin.bookPage!==currentPage()||origin.pdfMode!==isPdfMode()||
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
    if(!Number.isFinite(touch.clientX)){origin=null;return}
    origin.maxLeftTravel=Math.max(origin.maxLeftTravel,origin.x-touch.clientX);
    origin.maxRightTravel=Math.max(origin.maxRightTravel,touch.clientX-origin.x);
    origin.maxTravel=Math.max(origin.maxTravel,
      Math.abs(touch.clientX-origin.x),Math.abs(touch.clientY-origin.y));
    if(Math.abs((viewer.scrollTop||0)-origin.scrollTop)>8)origin.scrolled=true;
    if(readerNestedVerticalScrollMoved(origin.nestedVerticalScroll))origin.nestedScrolled=true;
    if(readerNestedHorizontalScrollMoved(origin.nestedHorizontalScroll))
      origin.nestedHorizontalScrolled=true;
  };
  const cancel=()=>{origin=null};
  const end=event=>{
    // V125 : vider immédiatement les records avant d'utiliser une origine.
    if(cancelPendingContentChanges())return;
    const initial=origin;
    origin=null;
    // Le mode V53 « pages d'écran » possède son propre gestionnaire tactile.
    // Ne JAMAIS déclencher ici le changement de page PDF quand V53 est actif,
    // même si preventDefault() n'a pas été honoré sur un appareil tactile.
    if(viewer.dataset?.readerLayout==='screens')return;
    if(!initial||!canNavigate()||isReaderViewportZoomed()||
      initial.bookPage!==currentPage()||initial.pdfMode!==isPdfMode()||
      initial.readerLayout!==(viewer.dataset?.readerLayout||'scroll')||
      !isReaderSwipeGeometryStable(initial.geometry,captureReaderSwipeGeometry(viewer))||
      event.touches?.length!==0||event.changedTouches?.length!==1)return;
    const touch=event.changedTouches[0];
    if(touch.identifier!==initial.id||event.defaultPrevented)return;
    const selected=Boolean(getSelectedText()?.trim());
    const horizontalOverflow=readerCanPanHorizontally(viewer)||
      initial.nestedHorizontalScrolled||
      readerNestedHorizontalScrollMoved(initial.nestedHorizontalScroll);
    const scrolled=initial.nestedScrolled||
      readerNestedVerticalScrollMoved(initial.nestedVerticalScroll)||
      initial.scrolled||Math.abs((viewer.scrollTop||0)-initial.scrollTop)>8;
    const direction=classifyReaderSwipe({
      dx:touch.clientX-initial.x,dy:touch.clientY-initial.y,
      durationMs:clock()-initial.time,viewerWidth:viewer.clientWidth,
      hasSelection:selected,horizontalOverflow,
      maxVerticalTravel:initial.maxVerticalTravel,
      maxLeftTravel:initial.maxLeftTravel,maxRightTravel:initial.maxRightTravel,
      scrolledDuringGesture:scrolled
    });
    if(direction){
      const button=direction==='next'?next:previous;
      if(!button.disabled)button.click();
      return;
    }
    // V97 : en PDF uniquement, un tap de marge tourne la page comme en
    // texte paginé. En mode texte continu, le centre et les bords ne
    // deviennent jamais des zones de navigation par tapotement.
    if(!initial.pdfMode||!isPdfMode())
      return;
    const rect=viewer.getBoundingClientRect?.();
    if(!rect)return;
    const tap=classifyReaderEdgeTap({
      x:initial.x-rect.left,viewerWidth:rect.width,
      durationMs:clock()-initial.time,
      dx:touch.clientX-initial.x,dy:touch.clientY-initial.y,
      maxTravel:initial.maxTravel,hasSelection:selected,
      scrolled:scrolled||horizontalOverflow
    });
    const button=tap==='next'?next:tap==='previous'?previous:null;
    if(button&&!button.disabled)button.click();
  };
  // V101 : faire glisser à la SOURIS une page PDF sur ordinateur. Le
  // texte adaptable reste sélectionnable, et les pointeurs touch/pen sont
  // laissés aux gestionnaires tactiles existants (pas de double tournage).
  const isPdfCanvas=event=>event?.target===viewer.querySelector?.('#reader-canvas')&&
    viewer.querySelector?.('#reader-text')?.hidden===true;
  const pointerDown=event=>{
    pointerOrigin=null;
    contentObserver?.takeRecords?.();
    if(!canNavigate()||viewer.dataset?.readerLayout==='screens'||
      event?.pointerType!=='mouse'||event.button!==0||event.isPrimary===false||
      isReaderViewportZoomed()||!isPdfCanvas(event)||isInteractiveTarget(event.target))
      return;
    if(![event.clientX,event.clientY,event.pointerId].every(Number.isFinite))return;
    pointerOrigin={
      id:event.pointerId,x:event.clientX,y:event.clientY,time:clock(),
      bookPage:currentPage(),
      scrollTop:viewer.scrollTop||0,maxVerticalTravel:0,maxLeftTravel:0,maxRightTravel:0,scrolled:false,
      geometry:captureReaderSwipeGeometry(viewer),
      readerLayout:viewer.dataset?.readerLayout||'scroll'
    };
    try{viewer.setPointerCapture?.(event.pointerId)}
    catch{/* perte de capture possible; le pointerup local reste utilisable */}
  };
  const pointerMove=event=>{
    if(cancelPendingContentChanges())return;
    const initial=pointerOrigin;
    if(!initial)return;
    if(!canNavigate()||!isPdfCanvas({target:viewer.querySelector?.('#reader-canvas')})||
      initial.bookPage!==currentPage()||
      event.pointerId!==initial.id||event.pointerType!=='mouse'||
      event.buttons!==undefined&&event.buttons!==1||
      initial.readerLayout!==(viewer.dataset?.readerLayout||'scroll')||
      !isReaderSwipeGeometryStable(initial.geometry,captureReaderSwipeGeometry(viewer))){
      pointerOrigin=null;return;
    }
    if(![event.clientX,event.clientY].every(Number.isFinite)){
      pointerOrigin=null;return;
    }
    initial.maxVerticalTravel=Math.max(initial.maxVerticalTravel,
      Math.abs(event.clientY-initial.y));
    initial.maxLeftTravel=Math.max(initial.maxLeftTravel,initial.x-event.clientX);
    initial.maxRightTravel=Math.max(initial.maxRightTravel,event.clientX-initial.x);
    if(Math.abs((viewer.scrollTop||0)-initial.scrollTop)>8)initial.scrolled=true;
  };
  const pointerCancel=()=>{pointerOrigin=null};
  const pointerUp=event=>{
    if(cancelPendingContentChanges())return;
    const initial=pointerOrigin;
    pointerOrigin=null;
    if(!initial||!canNavigate()||event.pointerType!=='mouse'||
      initial.bookPage!==currentPage()||
      event.pointerId!==initial.id||event.button!==0||event.defaultPrevented||
      viewer.dataset?.readerLayout==='screens'||
      !viewer.querySelector?.('#reader-text')?.hidden||
      initial.readerLayout!==(viewer.dataset?.readerLayout||'scroll')||
      !isReaderSwipeGeometryStable(initial.geometry,captureReaderSwipeGeometry(viewer))||
      isReaderViewportZoomed()||
      ![event.clientX,event.clientY].every(Number.isFinite))return;
    const direction=classifyReaderSwipe({
      dx:event.clientX-initial.x,dy:event.clientY-initial.y,
      durationMs:clock()-initial.time,viewerWidth:viewer.clientWidth,
      hasSelection:Boolean(getSelectedText()?.trim()),
      horizontalOverflow:readerCanPanHorizontally(viewer),
      maxVerticalTravel:initial.maxVerticalTravel,
      maxLeftTravel:initial.maxLeftTravel,maxRightTravel:initial.maxRightTravel,
      scrolledDuringGesture:initial.scrolled||
        Math.abs((viewer.scrollTop||0)-initial.scrollTop)>8
    });
    const button=direction==='next'?next:direction==='previous'?previous:null;
    if(button&&!button.disabled){
      event.preventDefault?.();
      button.click();
    }
  };
  viewer.addEventListener('pointerdown',pointerDown);
  viewer.addEventListener('pointermove',pointerMove);
  viewer.addEventListener('pointerup',pointerUp);
  viewer.addEventListener('pointercancel',pointerCancel);
  viewer.addEventListener('lostpointercapture',pointerCancel);
  // Listeners passifs : conserver le scroll vertical, le pinch-to-zoom,
  // le menu de sélection et les gestes des technologies d'assistance.
  viewer.addEventListener('touchstart',start,{passive:true});
  viewer.addEventListener('touchmove',move,{passive:true});
  viewer.addEventListener('touchcancel',cancel,{passive:true});
  viewer.addEventListener('touchend',end,{passive:true});
  // V91 : iOS/Android peuvent suspendre une application ou perdre le focus
  // sans émettre touchcancel. Une reprise ne doit jamais tourner une page
  // depuis une ancienne position de doigt.
  const cancelAll=()=>{cancel();pointerCancel();cancelReaderPageTurnFlash(viewer)};
  // V131 : un menu de sélection peut s'ouvrir sans événement touchcancel.
  // Ne jamais réutiliser l'ancien doigt/drag, sans bloquer le menu natif.
  viewer.addEventListener('contextmenu',cancelAll,{passive:true});
  // V132 : la sélection peut changer sans ouvrir de menu (poignées iOS).
  // Un contact en cours devient périmé, sans lire la sélection ni bloquer
  // ses interactions natives. Les autres déplacements restent possibles.
  const onSelectionChange=()=>{if(origin||pointerOrigin){cancel();pointerCancel()}};
  doc?.addEventListener?.('selectionchange',onSelectionChange);
  // V118 : le moteur V26 peut charger une nouvelle page (ou réinitialiser
  // le roman) en conservant temporairement la même valeur #reader-page.
  // Un contact de l'ancienne page devient immédiatement invalide.
  const onBookPageChange=()=>cancelAll();
  viewer.addEventListener('sinjira:reader-page-change',onBookPageChange);
  // V123 : un passage PDF→texte→PDF (ou livre masqué puis réaffiché)
  // peut conserver le numéro ET le mode au touchend. MutationObserver
  // conserve la preuve du basculement, même s'il a déjà été rétabli.
  // N'annuler que les contacts en cours : aucun livre ou statut n'est lu.
  const readingText=viewer.querySelector?.('#reader-text');
  const readingContent=viewer.closest?.('#reader-content');
  const isContentHiddenChange=records=>records?.some(record=>
    record.type==='attributes'&&record.attributeName==='hidden');
  const contentObserver=Observer?new Observer(records=>{
    if(isContentHiddenChange(records)){
      cancel();pointerCancel();
    }
  }):null;
  // V125 : takeRecords capture des mutations déjà écrites dans la même
  // tâche JS, avant que le navigateur puisse appeler le callback différé.
  // Examen des seuls attributs hidden surveillés, jamais du roman lui-même.
  const cancelPendingContentChanges=()=>{
    const records=contentObserver?.takeRecords?.();
    if(!isContentHiddenChange(records))return false;
    cancel();pointerCancel();
    return true;
  };
  if(readingText)contentObserver?.observe(readingText,{
    attributes:true,attributeFilter:['hidden']
  });
  if(readingContent)contentObserver?.observe(readingContent,{
    attributes:true,attributeFilter:['hidden']
  });
  const onVisibilityChange=()=>{if(globalThis.document?.hidden)cancelAll()};
  globalThis.document?.addEventListener?.('visibilitychange',onVisibilityChange);
  globalThis.window?.addEventListener?.('blur',cancelAll);
  globalThis.window?.addEventListener?.('pagehide',cancelAll);
  // V133 : retour du cache avant/arrière du navigateur mobile.
  // Annuler les contacts d'une ancienne apparition de la page.
  const onPageShow=event=>{if(event?.persisted)cancelAll()};
  win?.addEventListener?.('pageshow',onPageShow);
  // V128 : une rotation ou un resize visuel peut revenir à la géométrie
  // initiale avant touchend. Annuler immédiatement les anciens contacts.
  const onViewportChange=()=>{cancel();pointerCancel()};
  win?.addEventListener?.('resize',onViewportChange,{passive:true});
  win?.addEventListener?.('orientationchange',onViewportChange,{passive:true});
  win?.visualViewport?.addEventListener?.('resize',onViewportChange,{passive:true});
  // V130 : le plein écran V28 peut changer les dimensions CSS sans resize.
  // Annuler les anciennes trajectoires tactiles et les drags souris PDF.
  win?.addEventListener?.('sinjira:reader-layout-will-change',onViewportChange);
  // V129 : changer la police/interligne peut réorganiser le roman sans
  // événement de scroll, de changement de mode ni de page source.
  // Un doigt/drag commencé avant cette modification doit être ignoré.
  const onReadingPreferenceChange=event=>{
    if(['reader-size','reader-font','reader-line-height',
      'reader-letter-spacing','reader-text-width'].includes(event.target?.id))
      onViewportChange();
  };
  doc?.addEventListener?.('input',onReadingPreferenceChange,true);
  doc?.addEventListener?.('change',onReadingPreferenceChange,true);

  const mobileBack=()=>{
    if(canNavigate()&&viewer.dataset?.readerLayout!=='screens'&&!previous.disabled)previous.click();
  };
  const mobileForward=()=>{
    if(canNavigate()&&viewer.dataset?.readerLayout!=='screens'&&!next.disabled)next.click();
  };
  mobilePrevious?.addEventListener('click',mobileBack);
  mobileNext?.addEventListener('click',mobileForward);

  const reflectDisabled=()=>{
    if(mobilePrevious)mobilePrevious.disabled=previous.disabled;
    if(mobileNext)mobileNext.disabled=next.disabled;
  };
  // V119 : observer les commandes canoniques plutôt que les gestes eux-mêmes :
  // un swipe PDF, un tap de marge ou un bouton n'anime qu'une seule fois.
  const onPageBackward=()=>{if(canNavigate()&&viewer.dataset?.readerLayout!=='screens')
    flashReaderPageTurn(viewer,'previous')};
  const onPageForward=()=>{if(canNavigate()&&viewer.dataset?.readerLayout!=='screens')
    flashReaderPageTurn(viewer,'next')};
  previous.addEventListener('click',onPageBackward);
  next.addEventListener('click',onPageForward);
  const observer=Observer?new Observer(reflectDisabled):null;
  observer?.observe(previous,{attributes:true,attributeFilter:['disabled']});
  observer?.observe(next,{attributes:true,attributeFilter:['disabled']});
  reflectDisabled();
  return ()=>{
    origin=null;pointerOrigin=null;
    cancelReaderPageTurnFlash(viewer);
    if(viewer.dataset?.readerTouchManaged==='v52')delete viewer.dataset.readerTouchManaged;
    viewer.removeEventListener('touchstart',start);
    viewer.removeEventListener('touchmove',move);
    viewer.removeEventListener('touchcancel',cancel);
    viewer.removeEventListener('touchend',end);
    viewer.removeEventListener('contextmenu',cancelAll);
    doc?.removeEventListener?.('selectionchange',onSelectionChange);
    viewer.removeEventListener('pointerdown',pointerDown);
    viewer.removeEventListener('pointermove',pointerMove);
    viewer.removeEventListener('pointerup',pointerUp);
    viewer.removeEventListener('pointercancel',pointerCancel);
    viewer.removeEventListener('lostpointercapture',pointerCancel);
    viewer.removeEventListener('sinjira:reader-page-change',onBookPageChange);
    globalThis.document?.removeEventListener?.('visibilitychange',onVisibilityChange);
    globalThis.window?.removeEventListener?.('blur',cancelAll);
    globalThis.window?.removeEventListener?.('pagehide',cancelAll);
    win?.removeEventListener?.('pageshow',onPageShow);
    win?.removeEventListener?.('resize',onViewportChange);
    win?.removeEventListener?.('orientationchange',onViewportChange);
    win?.visualViewport?.removeEventListener?.('resize',onViewportChange);
    win?.removeEventListener?.('sinjira:reader-layout-will-change',onViewportChange);
    doc?.removeEventListener?.('input',onReadingPreferenceChange,true);
    doc?.removeEventListener?.('change',onReadingPreferenceChange,true);
    mobilePrevious?.removeEventListener('click',mobileBack);
    mobileNext?.removeEventListener('click',mobileForward);
    previous.removeEventListener('click',onPageBackward);
    next.removeEventListener('click',onPageForward);
    contentObserver?.disconnect();
    observer?.disconnect();
  };
}
function initTouchReader(){
  const viewer=document.getElementById('reader-viewer');
  const previous=document.getElementById('reader-previous');
  const next=document.getElementById('reader-next');
  if(!viewer||!previous||!next)return;
  bindReaderTouchNavigation({
    viewer,previous,next,pageField:document.getElementById('reader-page'),
    mobilePrevious:document.getElementById('reader-touch-prev'),
    mobileNext:document.getElementById('reader-touch-next')
  });
}
if(typeof document!=='undefined'){
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initTouchReader,{once:true});
  else initTouchReader();
}
