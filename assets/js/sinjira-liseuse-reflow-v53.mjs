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
/**
 * V60 : quand il reste moins d'un interligne à lire au-delà du dernier pas
 * complet, ne pas générer un « écran final » qui n'avance que de 2 à 30 px.
 * Le saut supplémentaire est borné par la hauteur d'une ligne, et préserve
 * donc le recouvrement utile de V55 sans masquer un passage entier.
 */
function readerShortTail({max,step,lineHeight}){
  if(!Number.isFinite(max)||!Number.isFinite(step)||max<=0||step<=0)return null;
  const fullSteps=Math.floor(max/step);
  if(fullSteps<1)return null;
  const tail=max-fullSteps*step;
  const limit=Math.min(step*0.18,Number.isFinite(lineHeight)&&lineHeight>0?lineHeight:30);
  return tail>0&&tail<=limit
    ?{omitted:fullSteps*step,previous:(fullSteps-1)*step}:null;
}
export function readerScreenState({scrollTop=0,scrollHeight=0,clientHeight=0,lineHeight=30,paddingTop=0,paddingBottom=0}={}){
  const max=Math.max(0,scrollHeight-clientHeight);
  const top=Math.max(0,Math.min(max,Number.isFinite(scrollTop)?scrollTop:0));
  const step=measureReaderScreen({clientHeight,lineHeight,paddingTop,paddingBottom});
  const shortTail=readerShortTail({max,step,lineHeight});
  const screens=Math.max(1,Math.ceil(max/step)+1-(shortTail?1:0));
  const screen=top>=max-2?screens:Math.max(1,Math.min(screens,Math.floor((top+2)/step)+1));
  return {top,max,step,screens,screen,shortTail,ratio:max>0?top/max:0,
    hasPreviousScreen:top>2,hasNextScreen:top<max-2};
}
export function planReaderScreenTurn({direction,scrollTop,scrollHeight,clientHeight,lineHeight,paddingTop=0,paddingBottom=0}){
  if(!['next','previous'].includes(direction))return null;
  const s=readerScreenState({scrollTop,scrollHeight,clientHeight,lineHeight,paddingTop,paddingBottom});
  if(direction==='next'){
    if(!s.hasNextScreen)return {type:'document',direction};
    const next=(Math.floor((s.top+2)/s.step)+1)*s.step;
    if(s.shortTail&&next>=s.shortTail.omitted-2)
      return {type:'screen',direction,top:s.max};
    return {type:'screen',direction,top:Math.min(s.max,next)};
  }
  if(!s.hasPreviousScreen)return {type:'document',direction};
  if(s.shortTail&&s.top>=s.max-2)
    return {type:'screen',direction,top:s.shortTail.previous};
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
/** V63 : ancre éphémère de caractère du roman, jamais enregistrée. */
export function captureReaderTextAnchor({viewer,text,doc=globalThis.document}={}){
  if(!viewer?.getBoundingClientRect||!text?.getBoundingClientRect||!doc?.createRange||
    (!doc.caretPositionFromPoint&&!doc.caretRangeFromPoint))return null;
  const box=viewer.getBoundingClientRect(),page=text.getBoundingClientRect();
  if(box.width<=0||box.height<=0||page.width<=0||text.hidden)return null;
  const style=globalThis.window?.getComputedStyle?.(text);
  const padLeft=Math.max(0,Number.parseFloat(style?.paddingLeft)||0);
  const x=Math.min(page.right-8,Math.max(page.left+8,page.left+padLeft+18));
  if(x<box.left||x>box.right)return null;
  // V63 : sur un petit cellulaire, la barre supérieure « sticky » peut
  // recouvrir les premières lignes visibles de la zone de lecture. Ne pas
  // prendre un caractère du logo/titre comme ancre du livre.
  for(const fraction of [.14,.27,.40,.56,.72,.87]){
    const y=Math.min(box.bottom-12,box.top+Math.max(24,box.height*fraction));
    if(y<=box.top||y>=box.bottom)continue;
    const layer=doc.elementFromPoint?.(x,y);
    if(layer&&!text.contains?.(layer))continue;
    let node=null,offset=0;
    if(doc.caretPositionFromPoint){
      const pos=doc.caretPositionFromPoint(x,y);
      if(pos){node=pos.offsetNode;offset=pos.offset}
    }
    if((node?.nodeType!==3||!text.contains?.(node))&&doc.caretRangeFromPoint){
      const pos=doc.caretRangeFromPoint(x,y);
      if(pos){node=pos.startContainer;offset=pos.startOffset}
    }
    if(node?.nodeType!==3||!text.contains?.(node)||!node.length)continue;
    const index=Math.max(0,Math.min(node.length-1,Number(offset)||0));
    try{
      const range=doc.createRange();
      range.setStart(node,index);range.setEnd(node,index+1);
      const rect=Array.from(range.getClientRects()).find(r=>r.height>0);
      if(!rect||!Number.isFinite(rect.top))continue;
      if(rect.top<box.top-box.height||rect.top>box.bottom+box.height)continue;
      return {node,offset:index,relativeY:rect.top-box.top};
    }catch{/* autre portion visible ou repli ratio */}
  }
  return null;
}
/** Replace un caractère visible dans l'écran sans persister son texte. */
export function restoreReaderTextAnchor({viewer,text,anchor,doc=globalThis.document}={}){
  if(!viewer?.scrollTo||!viewer?.getBoundingClientRect||!doc?.createRange||
    !anchor?.node||!text?.contains?.(anchor.node)||text.hidden)return false;
  const node=anchor.node,index=anchor.offset;
  if(node.nodeType!==3||!Number.isInteger(index)||index<0||index>=node.length||
    !Number.isFinite(anchor.relativeY))return false;
  try{
    const range=doc.createRange();
    range.setStart(node,index);range.setEnd(node,index+1);
    const rect=Array.from(range.getClientRects()).find(r=>r.height>0);
    if(!rect||!Number.isFinite(rect.top))return false;
    const top=viewer.scrollTop+rect.top-viewer.getBoundingClientRect().top-anchor.relativeY;
    if(!Number.isFinite(top))return false;
    const max=Math.max(0,viewer.scrollHeight-viewer.clientHeight);
    viewer.scrollTo({top:Math.max(0,Math.min(max,top)),left:0,behavior:'auto'});
    return true;
  }catch{return false}
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
  let lastAnchor=null,pendingLayoutAnchor=null; // V63 : ancre locale non persistée
  toggle.checked=localPreference();
  const isPaged=()=>!closed&&media.matches&&toggle.checked&&!text.hidden;
  const metric=()=>readerScreenState({
    scrollTop:viewer.scrollTop,scrollHeight:viewer.scrollHeight,
    clientHeight:viewer.clientHeight,...textMetrics(text)
  });
  const sync=()=>{
    const active=isPaged();
    viewer.dataset.readerLayout=active?'screens':'scroll';
    // V61 : les mêmes boutons contrôlent soit les portions de texte, soit
    // les pages PDF. Un libellé statique tromperait un lecteur d'écran.
    const backLabel=active
      ?'Écran précédent, ou page du livre précédente au début'
      :'Page du livre précédente';
    const forwardLabel=active
      ?'Écran suivant, ou page du livre suivante à la fin'
      :'Page du livre suivante';
    const describe=(button,label)=>{
      if(button?.getAttribute?.('aria-label')!==label)
        button?.setAttribute?.('aria-label',label);
    };
    for(const button of [previous,mobilePrevious])describe(button,backLabel);
    for(const button of [next,mobileNext])describe(button,forwardLabel);
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
    if(!restoring&&pendingLayoutRatio===null){
      lastRatio=s.ratio;
      lastAnchor=active?captureReaderTextAnchor({viewer,text}):null;
    }
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
    // V61 : les flèches sont des raccourcis de la LISEUSE, pas du site.
    // Hors du focus du livre, conserver les raccourcis du navigateur,
    // les zones de réglage et la navigation des technologies d'assistance.
    const focused=document.activeElement;
    if(!focused||(focused!==viewer&&!viewer.contains?.(focused)))return;
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
  const scheduleLayoutRestore=(ratio,anchor=lastAnchor)=>{
    if(pendingLayoutRatio!==null)return;
    pendingLayoutRatio=Math.max(0,Math.min(1,Number.isFinite(ratio)?ratio:0));
    pendingLayoutAnchor=anchor;
    raf(()=>raf(()=>{
      if(closed)return;
      const target=pendingLayoutRatio,anchored=pendingLayoutAnchor;
      pendingLayoutRatio=null;pendingLayoutAnchor=null;
      if(!isPaged()){sync();return}
      restoring=true;
      const found=restoreReaderTextAnchor({viewer,text,anchor:anchored});
      restoring=false;
      if(found)sync();
      else scrollToScreen(target*Math.max(0,viewer.scrollHeight-viewer.clientHeight));
    }));
  };
  const onToggle=()=>{
    // Un mode continu peut avoir une proportion différente de lastRatio.
    const previousRatio=metric().ratio;
    savePreference(toggle.checked);
    sync();
    scheduleLayoutRestore(previousRatio);
  };
  const onResize=()=>scheduleLayoutRestore(lastRatio,lastAnchor);
  const onPreferences=event=>{
    if(!isPaged()||!['reader-size','reader-font','reader-line-height',
      'reader-letter-spacing','reader-text-width'].includes(event.target?.id))return;
    // Phase capture du formulaire : avant le changement CSS de V26.
    scheduleLayoutRestore(lastRatio,
      captureReaderTextAnchor({viewer,text})||lastAnchor);
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
