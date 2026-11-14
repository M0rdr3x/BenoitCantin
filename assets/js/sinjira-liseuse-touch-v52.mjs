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
  dx,dy,durationMs,viewerWidth=360,hasSelection=false,horizontalOverflow=false
}={}){
  if(hasSelection||horizontalOverflow||
     ![dx,dy,durationMs,viewerWidth].every(Number.isFinite)||
     durationMs<0||durationMs>850||viewerWidth<=0)return null;
  const distance=Math.abs(dx),vertical=Math.abs(dy);
  // Résiste aux gestes accidentels, au défilement vertical et aux diagonales.
  const threshold=Math.max(56,Math.min(100,viewerWidth*0.14));
  if(distance<threshold||distance<vertical*1.65)return null;
  return dx<0?'next':'previous';
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
  let origin=null;
  const start=event=>{
    origin=null;
    if(event.touches?.length!==1||isInteractiveTarget(event.target))return;
    const touch=event.touches[0];
    if(!Number.isFinite(touch.clientX)||!Number.isFinite(touch.clientY))return;
    origin={id:touch.identifier,x:touch.clientX,y:touch.clientY,time:clock(),
      scrollTop:viewer.scrollTop||0,scrollLeft:viewer.scrollLeft||0};
  };
  const viewportMoved=initial=>
    Math.abs((viewer.scrollTop||0)-initial.scrollTop)>3||
    Math.abs((viewer.scrollLeft||0)-initial.scrollLeft)>3;
  const move=event=>{
    // Un scroll vertical déjà engagé ne doit jamais se transformer en page,
    // même si le doigt revient ensuite sur son axe Y initial.
    if(!origin)return;
    if(event.touches?.length!==1){origin=null;return;}
    const touch=event.touches[0];
    if(touch.identifier!==origin.id){origin=null;return;}
    const dx=touch.clientX-origin.x,dy=touch.clientY-origin.y;
    if(!Number.isFinite(dx)||!Number.isFinite(dy)||viewportMoved(origin)||
      (Math.abs(dy)>22&&Math.abs(dy)>Math.abs(dx)*1.25))origin=null;
  };
  const cancel=()=>{origin=null};
  const end=event=>{
    const initial=origin;
    origin=null;
    if(!initial||event.touches?.length!==0||event.changedTouches?.length!==1||
      viewportMoved(initial))return;
    const touch=event.changedTouches[0];
    if(touch.identifier!==initial.id||event.defaultPrevented)return;
    const direction=classifyReaderSwipe({
      dx:touch.clientX-initial.x,dy:touch.clientY-initial.y,
      durationMs:clock()-initial.time,viewerWidth:viewer.clientWidth,
      hasSelection:Boolean(getSelectedText()?.trim()),
      horizontalOverflow:viewer.scrollWidth>viewer.clientWidth+4
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

  const mobileBack=()=>{if(!previous.disabled)previous.click()};
  const mobileForward=()=>{if(!next.disabled)next.click()};
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
