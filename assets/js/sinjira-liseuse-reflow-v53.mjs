/**
 * SINJIRA V53 — livre à pages d'écran, texte adaptable au mobile.
 * Superposé à la V52 sans toucher au code d'authentification ni au schéma V51.
 * Un "écran" = un déplacement vertical d'un nombre entier de lignes du texte
 * du PDF courant ; une fois le texte terminé, tourner la vraie page du livre.
 * L'enregistrement d'emplacement reste le scroll_ratio historique de la V31.
 */
import {classifyReaderSwipe} from './sinjira-liseuse-touch-v52.mjs?v=52.11.10.1';

const PREF_KEY='sinjira:liseuse:lecture-par-ecrans:v53';
const INTERACTIVE='a,button,input,select,textarea,summary,[contenteditable],[role="button"],[role="link"],[data-reader-no-swipe]';

/** Empêche un saut de ligne masquée au bord de l'écran.
 * Le padding réduit la hauteur utile et une ligne reste visible à la jonction. */
export function measureReaderScreen({
  clientHeight,lineHeight,paddingTop=0,paddingBottom=0
}){
  if(!Number.isFinite(clientHeight)||clientHeight<=0)return 1;
  const line=Number.isFinite(lineHeight)&&lineHeight>0?lineHeight:30;
  const top=Number.isFinite(paddingTop)?Math.max(0,paddingTop):0;
  const bottom=Number.isFinite(paddingBottom)?Math.max(0,paddingBottom):0;
  const available=Math.max(1,clientHeight-top-bottom);
  const lines=Math.max(1,Math.floor((available-8)/line));
  const overlap=top+bottom>0&&lines>1?1:0;
  const safeStep=Math.min(available,(lines-overlap)*line);
  return Math.max(1,Math.min(clientHeight,Math.round(safeStep)));
}
export function readerScreenState({scrollTop=0,scrollHeight=0,clientHeight=0,lineHeight=30,paddingTop=0,paddingBottom=0}={}){
  const max=Math.max(0,scrollHeight-clientHeight);
  const top=Math.max(0,Math.min(max,Number.isFinite(scrollTop)?scrollTop:0));
  const step=measureReaderScreen({clientHeight,lineHeight,paddingTop,paddingBottom});
  const screens=Math.max(1,Math.ceil(max/step)+1);
  const screen=top>=max-2?screens:Math.max(1,Math.min(screens,Math.floor((top+2)/step)+1));
  return {top,max,step,screens,screen,ratio:max>0?top/max:0,
    hasPreviousScreen:top>2,hasNextScreen:top<max-2};
}
export function planReaderScreenTurn({direction,scrollTop,scrollHeight,clientHeight,lineHeight,paddingTop=0,paddingBottom=0}){
  if(!['next','previous'].includes(direction))return null;
  const s=readerScreenState({scrollTop,scrollHeight,clientHeight,lineHeight,paddingTop,paddingBottom});
  if(direction==='next'){
    if(!s.hasNextScreen)return {type:'document',direction};
    const next=(Math.floor((s.top+2)/s.step)+1)*s.step;
    return {type:'screen',direction,top:Math.min(s.max,next)};
  }
  if(!s.hasPreviousScreen)return {type:'document',direction};
  const prevIndex=Math.max(0,Math.ceil((s.top-2)/s.step)-1);
  return {type:'screen',direction,top:Math.max(0,prevIndex*s.step)};
}

export function parseReaderLineHeight({lineHeight,fontSize}={}){
  const font=Number.parseFloat(fontSize)||20;
  const raw=String(lineHeight??'').trim();
  const number=Number.parseFloat(raw);
  if(!Number.isFinite(number)||number<=0)return font*1.75;
  if(raw.endsWith('px'))return number;
  // CSS line-height sans unité: ex. 1.75 signifie 1.75 × font-size,
  // et non 1.75 px. Important pour ne pas couper une ligne sur Safari.
  if(Number.isFinite(Number(raw)))return number*font;
  return font*1.75;
}
function textMetrics(element){
  const style=window.getComputedStyle(element);
  const value=raw=>Number.parseFloat(raw)||0;
  return {
    lineHeight:parseReaderLineHeight({lineHeight:style.lineHeight,fontSize:style.fontSize}),
    paddingTop:Math.max(0,value(style.paddingTop)),
    paddingBottom:Math.max(0,value(style.paddingBottom))
  };
}
function isInteractive(element){
  return Boolean(element?.closest?.(INTERACTIVE));
}
function localPreference(){
  try{const value=localStorage.getItem(PREF_KEY);return value!=='off'}
  catch{return true}
}
function savePreference(on){
  try{localStorage.setItem(PREF_KEY,on?'on':'off')}catch{/* préférence facultative */}
}

/**
 * N'envoie pas de texte ni de position hors du navigateur.
 * previous/next restent les contrôles canoniques du moteur PDF (et V51 CAS).
 * Un événement touchend est capturé avant le gestionnaire V52 ; preventDefault
 * indique à la V52 de ne PAS doubler le mouvement.
 */
export function bindReaderScreenMode({
  viewer,text,previous,next,mobilePrevious,mobileNext,toggle,status,pageField,
  media=window.matchMedia('(max-width: 980px)'),
  getSelectionText=()=>String(window.getSelection?.()?.toString()||''),
  clock=()=>performance.now(),
  raf=callback=>requestAnimationFrame(callback),
  Observer=MutationObserver
}={}){
  if(!viewer||!text||!previous||!next||!toggle||!status||!pageField)
    throw new Error('SINJIRA V53 : contrôles nécessaires absents');
  let gesture=null,pendingPreviousPdf=null,lastRatio=0,restoring=false,closed=false;
  let pendingLayoutRatio=null; // V56 : une seule position de référence par réagencement
  toggle.checked=localPreference();
  const isPaged=()=>!closed&&media.matches&&toggle.checked&&!text.hidden;
  const metric=()=>readerScreenState({
    scrollTop:viewer.scrollTop,scrollHeight:viewer.scrollHeight,
    clientHeight:viewer.clientHeight,...textMetrics(text)
  });
  const sync=()=>{
    const active=isPaged();
    viewer.dataset.readerLayout=active?'screens':'scroll';
    status.hidden=!active;
    if(!active){
      if(mobilePrevious)mobilePrevious.disabled=previous.disabled;
      if(mobileNext)mobileNext.disabled=next.disabled;
      return;
    }
    const s=metric();
    const announced='Écran '+s.screen+' sur '+s.screens+' · page '+pageField.value+' du livre';
    // Une zone aria-live ne doit pas annoncer la même phrase à chaque scroll.
    if(status.textContent!==announced)status.textContent=announced;
    if(mobilePrevious)mobilePrevious.disabled=!s.hasPreviousScreen&&previous.disabled;
    if(mobileNext)mobileNext.disabled=!s.hasNextScreen&&next.disabled;
    if(!restoring&&pendingLayoutRatio===null)lastRatio=s.ratio;
  };
  const scrollToScreen=top=>{
    restoring=true;
    viewer.scrollTo({top,left:0,behavior:'auto'});
    restoring=false;
    sync();
    // Le gestionnaire V31/V51 de scroll sauvegarde le ratio de progression
    // de la même page PDF, sans nouveau format ni identifiant de lecteur.
  };
  const turn=direction=>{
    if(!isPaged())return false;
    const p=planReaderScreenTurn({
      direction,scrollTop:viewer.scrollTop,scrollHeight:viewer.scrollHeight,
      clientHeight:viewer.clientHeight,...textMetrics(text)
    });
    if(p?.type==='screen'){
      scrollToScreen(p.top);
      return true;
    }
    if(p?.type==='document'){
      if(direction==='previous'){
        if(previous.disabled)return true; // début du livre
        pendingPreviousPdf=Number(pageField.value)-1;
        previous.click();
      }else if(!next.disabled){
        pendingPreviousPdf=null;
        next.click();
      }
      return true;
    }
    return false;
  };
  const isTouchTargetAllowed=event=>!isInteractive(event.target);
  const onTouchStart=event=>{
    gesture=null;
    if(!isPaged()||event.touches?.length!==1||!isTouchTargetAllowed(event))return;
    const touch=event.touches[0];
    gesture={id:touch.identifier,x:touch.clientX,y:touch.clientY,start:clock()};
  };
  const onTouchMove=event=>{if(event.touches?.length!==1)gesture=null};
  const onTouchCancel=()=>{gesture=null};
  const onTouchEnd=event=>{
    const start=gesture;gesture=null;
    if(!start||!isPaged()||event.defaultPrevented||
      event.touches?.length!==0||event.changedTouches?.length!==1)return;
    const touch=event.changedTouches[0];
    if(touch.identifier!==start.id)return;
    const direction=classifyReaderSwipe({
      dx:touch.clientX-start.x,dy:touch.clientY-start.y,
      durationMs:clock()-start.start,viewerWidth:viewer.clientWidth,
      hasSelection:Boolean(getSelectionText().trim()),horizontalOverflow:false
    });
    if(direction){
      // Intercepte uniquement un vrai mouvement horizontal; la sélection et
      // les gestes verticaux restent accessibles au navigateur.
      event.preventDefault();
      turn(direction);
    }
  };
  const handleNav=(direction,event)=>{
    if(!isPaged())return;
    const state=metric();
    if(direction==='next'&&state.hasNextScreen||
       direction==='previous'&&state.hasPreviousScreen){
      event.preventDefault();
      event.stopImmediatePropagation();
      turn(direction);
    }else if(direction==='previous'&&!previous.disabled){
      pendingPreviousPdf=Number(pageField.value)-1;
    }
  };
  const onPrev=event=>handleNav('previous',event);
  const onNext=event=>handleNav('next',event);
  const onMobilePrev=event=>{
    if(!isPaged())return;
    event.preventDefault();event.stopImmediatePropagation();turn('previous');
  };
  const onMobileNext=event=>{
    if(!isPaged())return;
    event.preventDefault();event.stopImmediatePropagation();turn('next');
  };
  const onKeyboard=event=>{
    if(!isPaged()||event.defaultPrevented||event.altKey||event.ctrlKey||
      event.metaKey||event.shiftKey||isInteractive(document.activeElement))return;
    const direction=event.key==='ArrowLeft'||event.key==='PageUp'?'previous'
      :event.key==='ArrowRight'||event.key==='PageDown'?'next':null;
    if(!direction)return;
    event.preventDefault();event.stopImmediatePropagation();turn(direction);
  };
  const afterTextChanged=()=>{
    if(!isPaged()){sync();return}
    const expected=pendingPreviousPdf;
    raf(()=>raf(()=>{
      if(closed)return;
      if(expected!==null&&Number(pageField.value)===expected){
        pendingPreviousPdf=null;
        scrollToScreen(Math.max(0,viewer.scrollHeight-viewer.clientHeight));
      }else if(expected===null){
        // Le moteur natif restoreScrollAfterRender replace scrollTop selon
        // le scroll_ratio. Ici on ne l'écrase pas après son propre rappel.
        sync();
      }
    }));
  };
  const observer=Observer?new Observer(mutations=>{
    if(mutations.some(m=>m.attributeName==='hidden'||m.type==='childList'||m.type==='characterData')){
      afterTextChanged();
    }else sync();
  }):null;
  observer?.observe(text,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['hidden']});
  const buttonsObserver=Observer?new Observer(()=>sync()):null;
  buttonsObserver?.observe(previous,{attributes:true,attributeFilter:['disabled']});
  buttonsObserver?.observe(next,{attributes:true,attributeFilter:['disabled']});
  const onScroll=()=>{if(!closed)sync()};
  /**
   * V56 : un changement de police déclenche souvent input puis change; et une
   * rotation provoque resize puis media.change. Capturer une SEULE position
   * proportionnelle évite qu'un événement post-reflow remplace l'ancre.
   * Cette ancre est une fraction du PDF courant, pas un identifiant EPUB.
   */
  const scheduleLayoutRestore=ratio=>{
    if(pendingLayoutRatio!==null)return;
    pendingLayoutRatio=Math.max(0,Math.min(1,Number.isFinite(ratio)?ratio:0));
    raf(()=>raf(()=>{
      if(closed)return;
      const target=pendingLayoutRatio;
      pendingLayoutRatio=null;
      if(isPaged())scrollToScreen(target*Math.max(0,viewer.scrollHeight-viewer.clientHeight));
      else sync();
    }));
  };
  const onToggle=()=>{
    // Un mode continu peut avoir une proportion différente de lastRatio.
    const previousRatio=metric().ratio;
    savePreference(toggle.checked);
    sync();
    scheduleLayoutRestore(previousRatio);
  };
  const onResize=()=>scheduleLayoutRestore(lastRatio);
  const onPreferences=event=>{
    if(!isPaged()||!['reader-size','reader-font','reader-line-height',
      'reader-letter-spacing','reader-text-width'].includes(event.target?.id))return;
    scheduleLayoutRestore(lastRatio);
  };
  viewer.addEventListener('touchstart',onTouchStart,{capture:true,passive:true});
  viewer.addEventListener('touchmove',onTouchMove,{capture:true,passive:true});
  viewer.addEventListener('touchcancel',onTouchCancel,{capture:true,passive:true});
  viewer.addEventListener('touchend',onTouchEnd,{capture:true,passive:false});
  viewer.addEventListener('scroll',onScroll,{passive:true});
  previous.addEventListener('click',onPrev,true);
  next.addEventListener('click',onNext,true);
  mobilePrevious?.addEventListener('click',onMobilePrev,true);
  mobileNext?.addEventListener('click',onMobileNext,true);
  document.addEventListener('keydown',onKeyboard,true);
  document.addEventListener('input',onPreferences,true);
  document.addEventListener('change',onPreferences,true);
  toggle.addEventListener('change',onToggle);
  window.addEventListener('resize',onResize,{passive:true});
  media.addEventListener?.('change',onResize);
  sync();
  return ()=>{
    closed=true;gesture=null;
    viewer.removeEventListener('touchstart',onTouchStart,true);
    viewer.removeEventListener('touchmove',onTouchMove,true);
    viewer.removeEventListener('touchcancel',onTouchCancel,true);
    viewer.removeEventListener('touchend',onTouchEnd,true);
    viewer.removeEventListener('scroll',onScroll);
    previous.removeEventListener('click',onPrev,true);
    next.removeEventListener('click',onNext,true);
    mobilePrevious?.removeEventListener('click',onMobilePrev,true);
    mobileNext?.removeEventListener('click',onMobileNext,true);
    document.removeEventListener('keydown',onKeyboard,true);
    document.removeEventListener('input',onPreferences,true);
    document.removeEventListener('change',onPreferences,true);
    toggle.removeEventListener('change',onToggle);
    window.removeEventListener('resize',onResize);
    media.removeEventListener?.('change',onResize);
    observer?.disconnect();buttonsObserver?.disconnect();
  };
}
function initReaderScreens(){
  const id=name=>document.getElementById(name);
  const required=['reader-viewer','reader-text','reader-previous','reader-next',
    'reader-screens-enabled','reader-screen-count','reader-page'];
  if(required.some(name=>!id(name)))return;
  bindReaderScreenMode({
    viewer:id('reader-viewer'),text:id('reader-text'),
    previous:id('reader-previous'),next:id('reader-next'),
    mobilePrevious:id('reader-touch-prev'),mobileNext:id('reader-touch-next'),
    toggle:id('reader-screens-enabled'),status:id('reader-screen-count'),pageField:id('reader-page')
  });
}
if(typeof document!=='undefined'){
  if(document.readyState==='loading')
    document.addEventListener('DOMContentLoaded',initReaderScreens,{once:true});
  else initReaderScreens();
}
