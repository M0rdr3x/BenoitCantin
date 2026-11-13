import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
  measureReaderScreen,readerScreenState,planReaderScreenTurn,bindReaderScreenMode,parseReaderLineHeight,
  captureReaderTextAnchor,restoreReaderTextAnchor
} from '../assets/js/sinjira-liseuse-reflow-v53.mjs';

const setup={scrollHeight:1050,clientHeight:350,lineHeight:35};
const turn=(direction,scrollTop)=>planReaderScreenTurn({direction,scrollTop,...setup});

test('CSS line-height sans unité se convertit en hauteur réelle',()=>{
  assert.equal(parseReaderLineHeight({lineHeight:'1.75',fontSize:'20px'}),35);
  assert.ok(Math.abs(parseReaderLineHeight({lineHeight:'2.1',fontSize:'24px'})-50.4)<1e-9);
});
test('CSS line-height en px ne doit pas être multiplié',()=>{
  assert.equal(parseReaderLineHeight({lineHeight:'35px',fontSize:'20px'}),35);
});
test('interligne inconnu retombe sur 1,75 sans valeur NaN',()=>{
  assert.equal(parseReaderLineHeight({lineHeight:'normal',fontSize:'20px'}),35);
});
test('la page-écran avance par lignes complètes',()=>{
  assert.equal(measureReaderScreen({clientHeight:350,lineHeight:35}),315);
  assert.equal(measureReaderScreen({clientHeight:200,lineHeight:20}),180);
});
test('V55 : marge intérieure de 22 px laisse une ligne de chevauchement entre deux écrans',()=>{
  const step=measureReaderScreen({
    clientHeight:350,lineHeight:35,paddingTop:22,paddingBottom:22
  });
  assert.equal(step,245);
  assert.ok(step<=350-44-35);
});
test('V55 : navigation écran par écran ne saute aucune portion au changement de page source',()=>{
  const sample={scrollHeight:1050,clientHeight:350,lineHeight:35,
    paddingTop:22,paddingBottom:22};
  assert.equal(planReaderScreenTurn({direction:'next',scrollTop:0,...sample}).top,245);
  assert.equal(planReaderScreenTurn({direction:'next',scrollTop:245,...sample}).top,490);
  assert.equal(planReaderScreenTurn({direction:'next',scrollTop:490,...sample}).top,700);
  assert.equal(planReaderScreenTurn({direction:'next',scrollTop:700,...sample}).type,'document');
  assert.equal(planReaderScreenTurn({direction:'previous',scrollTop:700,...sample}).top,490);
  assert.equal(planReaderScreenTurn({direction:'previous',scrollTop:490,...sample}).top,245);
  assert.equal(planReaderScreenTurn({direction:'previous',scrollTop:245,...sample}).top,0);
});
test('V55 : les marges invalides et un écran extrêmement petit restent bornés',()=>{
  assert.equal(measureReaderScreen({
    clientHeight:20,lineHeight:35,paddingTop:40,paddingBottom:40
  }),1);
  assert.equal(measureReaderScreen({
    clientHeight:350,lineHeight:35,paddingTop:NaN,paddingBottom:-12
  }),315);
});
test('un petit écran reste navigable sans division par zéro',()=>{
  assert.equal(measureReaderScreen({clientHeight:0,lineHeight:32}),1);
  assert.equal(measureReaderScreen({clientHeight:20,lineHeight:32}),20);
});
test('pagination initiale et fin du texte sont mesurées',()=>{
  const s=readerScreenState({...setup,scrollTop:0});
  assert.equal(s.screens,4);
  assert.equal(s.screen,1);
  assert.equal(s.max,700);
  assert.equal(s.ratio,0);
});
test('trois gestes à gauche lisent les écrans puis atteignent la page PDF suivante',()=>{
  assert.deepEqual(turn('next',0),{type:'screen',direction:'next',top:315});
  assert.deepEqual(turn('next',315),{type:'screen',direction:'next',top:630});
  assert.deepEqual(turn('next',630),{type:'screen',direction:'next',top:700});
  assert.deepEqual(turn('next',700),{type:'document',direction:'next'});
});
test('un geste à droite recule écran par écran avant la page PDF précédente',()=>{
  assert.deepEqual(turn('previous',700),{type:'screen',direction:'previous',top:630});
  assert.deepEqual(turn('previous',630),{type:'screen',direction:'previous',top:315});
  assert.deepEqual(turn('previous',315),{type:'screen',direction:'previous',top:0});
  assert.deepEqual(turn('previous',0),{type:'document',direction:'previous'});
});
test('V60 : aucun micro-écran de dix pixels à la fin d’une page source',()=>{
  const p={scrollHeight:850,clientHeight:350,lineHeight:35,
    paddingTop:22,paddingBottom:22};
  const at=top=>readerScreenState({...p,scrollTop:top});
  const turn= (direction,top)=>planReaderScreenTurn({...p,direction,scrollTop:top});
  assert.equal(at(0).screens,3);
  assert.equal(at(0).screen,1);
  assert.equal(turn('next',0).top,245);
  assert.equal(turn('next',245).top,500);
  assert.equal(at(500).screen,3);
  assert.equal(turn('next',500).type,'document');
  assert.equal(turn('previous',500).top,245);
  assert.equal(turn('previous',245).top,0);
  assert.equal(turn('previous',0).type,'document');
});
test('V60 : aucun saut de contenu lorsqu’il reste plus d’une ligne',()=>{
  const p={scrollHeight:950,clientHeight:350,lineHeight:35,
    paddingTop:22,paddingBottom:22};
  const f=(direction,top)=>planReaderScreenTurn({...p,scrollTop:top,direction});
  assert.equal(readerScreenState({...p,scrollTop:0}).screens,4);
  assert.equal(f('next',0).top,245);
  assert.equal(f('next',245).top,490);
  assert.equal(f('next',490).top,600);
  assert.equal(f('previous',600).top,490);
  assert.equal(f('next',600).type,'document');
});
test('V60 : un reliquat nul reste réversible sans doublon',()=>{
  const p={scrollHeight:840,clientHeight:350,lineHeight:35,
    paddingTop:22,paddingBottom:22};
  assert.equal(readerScreenState({...p}).screens,3);
  assert.equal(planReaderScreenTurn({...p,scrollTop:245,direction:'next'}).top,490);
  assert.equal(planReaderScreenTurn({...p,scrollTop:490,direction:'previous'}).top,245);
});
test('V60 : un marque-page restauré près de la fin rejoint la vraie fin',()=>{
  const p={scrollHeight:850,clientHeight:350,lineHeight:35,
    paddingTop:22,paddingBottom:22};
  assert.equal(readerScreenState({...p,scrollTop:490}).screen,3);
  assert.equal(planReaderScreenTurn({...p,scrollTop:490,direction:'next'}).top,500);
  assert.equal(planReaderScreenTurn({...p,scrollTop:490,direction:'previous'}).top,245);
});
test('un PDF dont le texte tient sur un écran tourne directement la page',()=>{
  const args={scrollTop:0,scrollHeight:350,clientHeight:350,lineHeight:35};
  assert.equal(planReaderScreenTurn({direction:'next',...args}).type,'document');
  assert.equal(planReaderScreenTurn({direction:'previous',...args}).type,'document');
});
test('la proportion est bornée et réutilisable après un changement de taille',()=>{
  const s=readerScreenState({...setup,scrollTop:350});
  assert.equal(s.ratio,.5);
  assert.equal(readerScreenState({...setup,scrollTop:1400}).ratio,1);
  assert.equal(readerScreenState({...setup,scrollTop:-30}).ratio,0);
});
test('écran final numéroté même avec une dernière portion courte',()=>{
  const s=readerScreenState({...setup,scrollTop:700});
  assert.equal(s.screens,4);
  assert.equal(s.screen,4);
});
test('direction inconnue ne provoque aucune action',()=>{
  assert.equal(turn('down',350),null);
});
test('un grand texte peut être divisé en plusieurs écrans, jamais en zéro',()=>{
  assert.ok(readerScreenState({scrollTop:0,scrollHeight:30000,clientHeight:400,lineHeight:40}).screens>70);
  assert.equal(readerScreenState({scrollTop:0,scrollHeight:0,clientHeight:0}).screens,1);
});

function mockTarget(opts={}){
  const handlers=new Map();
  const attributes=new Map();
  return {
    disabled:opts.disabled??false,hidden:opts.hidden??false,checked:opts.checked??true,
    dataset:{},clientWidth:opts.clientWidth??375,clientHeight:opts.clientHeight??350,
    scrollTop:opts.scrollTop??0,scrollHeight:opts.scrollHeight??1050,
    value:opts.value??'4',textContent:'',clicks:0,
    addEventListener(name,handler){const arr=handlers.get(name)||[];arr.push(handler);handlers.set(name,arr)},
    removeEventListener(name,handler){const arr=handlers.get(name)||[];handlers.set(name,arr.filter(x=>x!==handler));},
    emit(name,event={}){for(const fn of handlers.get(name)||[])fn(event)},
    click(){if(this.disabled)return;this.clicks++;this.emit('click',{preventDefault(){},stopImmediatePropagation(){}})},
    scrollTo({top}){this.scrollTop=top;this.emit('scroll',{})},
    getAttribute(name){return attributes.get(name)??null},
    setAttribute(name,value){attributes.set(name,String(value))},
    contains(node){return node===this},
    handlers
  };
}
function fixture({selected='',lastBookPage=false,firstBookPage=false,observe=false,deferredRaf=false}={}){
  const observed=[];
  class FakeObserver{
    constructor(callback){this.callback=callback;observed.push(this)}
    observe(target){this.target=target}
    disconnect(){}
    emit(mutations){this.callback(mutations)}
  }
  const oldWindow=globalThis.window,oldDocument=globalThis.document;
  const windowMock=mockTarget();
  windowMock.getComputedStyle=()=>({lineHeight:'35px',fontSize:'20px'});
  globalThis.window=windowMock;
  const documentMock=mockTarget();
  documentMock.activeElement=null;
  globalThis.document=documentMock;
  const viewer=mockTarget(),text=mockTarget(),
    previous=mockTarget({disabled:firstBookPage}),
    next=mockTarget({disabled:lastBookPage}),
    mobilePrevious=mockTarget(),mobileNext=mockTarget(),
    toggle=mockTarget(),status=mockTarget(),pageField=mockTarget();
  documentMock.activeElement=viewer; // le clavier du test possède le focus du livre
  const media=mockTarget();media.matches=true;
  let now=0;
  const frameQueue=[];
  const raf=fn=>deferredRaf?frameQueue.push(fn):fn();
  const flushFrames=()=>{
    let count=0;
    // Les appels placés dans la nouvelle trame ne sont exécutés qu'au
    // prochain passage, comme requestAnimationFrame dans le navigateur.
    while(frameQueue.length){
      if(++count>15)throw new Error('V56 : boucle de restitution');
      const frame=frameQueue.splice(0);
      frame.forEach(fn=>fn());
    }
  };
  let statusWrites=0;
  let statusValue=status.textContent;
  Object.defineProperty(status,'textContent',{
    get:()=>statusValue,set:value=>{statusWrites++;statusValue=value},
    configurable:true
  });
  const teardown=bindReaderScreenMode({
    viewer,text,previous,next,mobilePrevious,mobileNext,toggle,status,
    pageField,media,getSelectionText:()=>selected,
    clock:()=>now,raf,Observer:observe?FakeObserver:null
  });
  function restore(){
    teardown();
    globalThis.window=oldWindow;globalThis.document=oldDocument;
  }
  function swipe(dx,dy=3,options={}){
    const startX=options.startX??175;
    const begin={identifier:1,clientX:startX,clientY:140};
    const end={identifier:1,clientX:startX+dx,clientY:140+dy};
    const started={touches:[begin],target:{closest:()=>null}};
    const finished={
      touches:[],changedTouches:[end],defaultPrevented:false,
      preventDefault(){this.defaultPrevented=true}
    };
    viewer.emit('touchstart',started);
    for(const [mx,my] of options.moves||[]){
      viewer.emit('touchmove',{touches:[{
        identifier:1,clientX:startX+mx,clientY:140+my
      }]});
    }
    if(options.scrollDuring){
      const original=viewer.scrollTop;
      viewer.scrollTop=original+options.scrollDuring;
      viewer.emit('touchmove',{touches:[begin]});
      viewer.scrollTop=original;
    }
    now+=options.elapsed??200;
    viewer.emit('touchend',finished);
    return finished;
  }
  return {viewer,text,previous,next,mobilePrevious,mobileNext,toggle,status,
    pageField,documentMock,windowMock,media,restore,swipe,
    notifyText:()=>observed.find(x=>x.target===text)?.emit([{type:'childList'}]),
    flushFrames,getStatusWrites:()=>statusWrites,
    setSelected:v=>{selected=v}};
}
test('V67 : une amorce au bord du téléphone laisse le geste au système en mode écran',()=>{
  const f=fixture();
  try{
    f.windowMock.innerWidth=390;
    const initial=f.viewer.scrollTop;
    const back=f.swipe(130,3,{startX:10});
    const ahead=f.swipe(-130,3,{startX:380});
    assert.equal(back.defaultPrevented,false);
    assert.equal(ahead.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,initial);
    assert.equal(f.previous.clicks,0);
    assert.equal(f.next.clicks,0);
    const inside=f.swipe(-130,3,{startX:230});
    assert.equal(inside.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V67 : la zone système est bornée par la largeur actuelle après rotation',()=>{
  const f=fixture();
  try{
    f.windowMock.innerWidth=568;
    const edge=f.swipe(-130,2,{startX:557});
    assert.equal(edge.defaultPrevented,false);
    const content=f.swipe(-130,2,{startX:400});
    assert.equal(content.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V66 : trajet texte vertical puis gauche ne provoque aucun changement écran',()=>{
  const f=fixture();
  try{
    const evt=f.swipe(-140,3,{moves:[[-10,110],[-75,10]]});
    assert.equal(evt.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    const valid=f.swipe(-140,3,{moves:[[-80,8]]});
    assert.equal(valid.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V66 : trajet texte vertical puis droite ne revient pas à une autre page',()=>{
  const f=fixture();
  try{
    const evt=f.swipe(140,2,{moves:[[10,-130],[90,-8]]});
    assert.equal(evt.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.previous.clicks,0);
  }finally{f.restore()}
});
test('V66 : scroll natif transitoire annule un faux balayage de texte',()=>{
  const f=fixture();
  try{
    const evt=f.swipe(-140,2,{scrollDuring:50});
    assert.equal(evt.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    const valid=f.swipe(-140,2);
    assert.equal(valid.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V63 : capture d’un caractère local visible, sans stocker le texte',()=>{
  const node={nodeType:3,length:100};
  let glyphTop=80,scrollTop=220;
  const doc={
    caretPositionFromPoint:()=>({offsetNode:node,offset:27}),
    createRange:()=>({
      setStart(n,o){assert.equal(n,node);assert.equal(o,27)},
      setEnd(n,o){assert.equal(n,node);assert.equal(o,28)},
      getClientRects:()=>[{top:glyphTop,height:20}]
    })
  };
  const viewer={
    scrollTop,scrollHeight:1800,clientHeight:350,
    getBoundingClientRect:()=>({left:0,right:320,width:320,top:0,bottom:350,height:350}),
    scrollTo({top}){this.scrollTop=top}
  };
  const text={
    hidden:false,contains:n=>n===node,
    getBoundingClientRect:()=>({left:0,right:320,width:320})
  };
  const anchor=captureReaderTextAnchor({viewer,text,doc});
  assert.deepEqual(anchor,{node,offset:27,relativeY:80});
  glyphTop=190;
  assert.equal(restoreReaderTextAnchor({viewer,text,anchor,doc}),true);
  assert.equal(viewer.scrollTop,330);
  assert.equal(anchor.text,undefined); // zéro extrait de roman persistant
});
test('V63 : ancre devenue périmée après changement de page PDF est rejetée',()=>{
  const oldNode={nodeType:3,length:80};
  const viewer={
    scrollTop:70,scrollHeight:1500,clientHeight:350,
    getBoundingClientRect:()=>({top:0}),scrollTo(){throw Error('ne pas scroller')}
  };
  const text={hidden:false,contains:()=>false};
  const doc={createRange(){throw Error('ne jamais évaluer une ancienne page')}};
  assert.equal(restoreReaderTextAnchor({
    viewer,text,doc,anchor:{node:oldNode,offset:23,relativeY:80}
  }),false);
  assert.equal(viewer.scrollTop,70);
});
test('V63 : absence API caret et page cachée -> conservation du repli ratio',()=>{
  const viewer={getBoundingClientRect:()=>({width:300,height:350,top:0,bottom:350,left:0,right:300})};
  const text={hidden:false,getBoundingClientRect:()=>({width:300,left:0,right:300})};
  assert.equal(captureReaderTextAnchor({viewer,text,doc:{createRange(){}}}),null);
  text.hidden=true;
  assert.equal(captureReaderTextAnchor({
    viewer,text,doc:{createRange(){},caretPositionFromPoint(){}}
  }),null);
});
test('V63 : aucun dépassement même si la nouvelle mise en page raccourcit le livre',()=>{
  const node={nodeType:3,length:12};
  const viewer={
    scrollTop:400,scrollHeight:420,clientHeight:350,
    getBoundingClientRect:()=>({top:0}),scrollTo({top}){this.scrollTop=top}
  };
  const doc={createRange:()=>({
    setStart(){},setEnd(){},getClientRects:()=>[{top:500,height:20}]
  })};
  assert.equal(restoreReaderTextAnchor({
    viewer,text:{hidden:false,contains:n=>n===node},doc,
    anchor:{node,offset:4,relativeY:80}
  }),true);
  assert.equal(viewer.scrollTop,70);
});
test('intégration : le mode pages d’écran est activé par défaut sur mobile',()=>{
  const f=fixture();
  try{
    assert.equal(f.viewer.dataset.readerLayout,'screens');
    assert.match(f.status.textContent,/Écran 1 sur 4/);
  }finally{f.restore()}
});
test('V56 : l’annonce accessible ne se répète pas à chaque scroll de la même portion',()=>{
  const f=fixture();
  try{
    const startingWrites=f.getStatusWrites();
    f.viewer.scrollTo({top:10});
    f.viewer.scrollTo({top:20});
    assert.equal(f.getStatusWrites(),startingWrites);
    f.viewer.scrollTo({top:320});
    assert.equal(f.getStatusWrites(),startingWrites+1);
    f.viewer.scrollTo({top:321});
    assert.equal(f.getStatusWrites(),startingWrites+1);
  }finally{f.restore()}
});
test('V69 : un swipe pendant les deux frames du resize gagne sur le ratio ancien',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    f.windowMock.emit('resize',{});
    f.viewer.scrollHeight=1750;
    const swipe=f.swipe(-130,2);
    assert.equal(swipe.defaultPrevented,true);
    const next=f.viewer.scrollTop;
    assert.ok(next>350,next);
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,next,
      'une restauration obsolète ne doit pas ramener le lecteur en arrière');
  }finally{f.restore()}
});
test('V69 : le bouton suivant gagne aussi pendant un réagencement',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    f.windowMock.emit('resize',{});
    f.viewer.scrollHeight=1750;
    f.mobileNext.click();
    const target=f.viewer.scrollTop;
    assert.ok(target>350,target);
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,target);
  }finally{f.restore()}
});
test('V69 : toucher la zone du livre annule une restauration différée',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    f.windowMock.emit('resize',{});
    f.viewer.scrollHeight=1750;
    f.viewer.emit('touchstart',{
      touches:[{identifier:1,clientX:175,clientY:140}],
      target:{closest:()=>null}
    });
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,350);
  }finally{f.restore()}
});
test('V56 : rotation mobile conserve la même proportion malgré événements en double',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    assert.equal(f.viewer.scrollTop,350);
    f.windowMock.emit('resize',{});
    f.viewer.scrollHeight=1750; // mise en page plus longue après rotation
    f.viewer.emit('scroll',{}); // ratio temporairement modifié pendant le layout
    f.media.emit('change',{});
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,700);
    assert.match(f.status.textContent,/Écran/);
  }finally{f.restore()}
});
test('V56 : input puis change de taille de police ne créent pas deux déplacements',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    f.documentMock.emit('input',{target:{id:'reader-size'}});
    f.viewer.scrollHeight=2100;
    f.documentMock.emit('change',{target:{id:'reader-size'}});
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,875); // 50 % de la nouvelle hauteur scrollable
  }finally{f.restore()}
});
test('intégration : glisser gauche/droite navigue par écran sans changer page PDF',()=>{
  const f=fixture();
  try{
    const left=f.swipe(-100);
    assert.equal(left.defaultPrevented,true);
    assert.equal(f.viewer.scrollTop,315);
    assert.equal(f.next.clicks,0);
    const right=f.swipe(100);
    assert.equal(right.defaultPrevented,true);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.previous.clicks,0);
  }finally{f.restore()}
});
test('intégration : les boutons mobiles parcourent les écrans',()=>{
  const f=fixture();
  try{
    f.mobileNext.emit('click',{preventDefault(){},stopImmediatePropagation(){}});
    assert.equal(f.viewer.scrollTop,315);
    f.mobilePrevious.emit('click',{preventDefault(){},stopImmediatePropagation(){}});
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
  }finally{f.restore()}
});
test('intégration : bouton PDF désactivé n’interdit pas les écrans internes',()=>{
  const f=fixture({lastBookPage:true});
  try{
    assert.equal(f.next.disabled,true);
    assert.equal(f.mobileNext.disabled,false);
    f.swipe(-100);
    assert.equal(f.viewer.scrollTop,315);
    f.viewer.scrollTop=700;f.viewer.emit('scroll',{});
    assert.equal(f.mobileNext.disabled,true);
  }finally{f.restore()}
});
test('intégration : touch vertical et sélection ne tournent jamais les pages',()=>{
  const f=fixture({selected:'Extrait choisi'});
  try{
    assert.equal(f.swipe(-100).defaultPrevented,false);
    f.setSelected('');
    assert.equal(f.swipe(-10,130).defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
  }finally{f.restore()}
});
test('intégration : une page PDF reste le repli lorsqu’il n’existe plus d’écran',()=>{
  const f=fixture();
  try{
    f.viewer.scrollTop=700;f.viewer.emit('scroll',{});
    f.swipe(-100);
    assert.equal(f.next.clicks,1);
  }finally{f.restore()}
});
test('intégration : retour à la page PDF précédente ouvre sa dernière portion',()=>{
  const f=fixture({observe:true});
  try{
    f.previous.addEventListener('click',()=>{
      f.pageField.value='3';
      f.viewer.scrollTop=0;
      f.viewer.emit('scroll',{});
    });
    f.swipe(105);
    assert.equal(f.previous.clicks,1);
    f.notifyText();
    assert.equal(f.viewer.scrollTop,700);
    assert.match(f.status.textContent,/Écran 4 sur 4 · page 3/);
  }finally{f.restore()}
});
test('intégration : mode PDF laisse les gestes au module V52',()=>{
  const f=fixture();
  try{
    f.text.hidden=true;
    f.toggle.emit('change',{});
    assert.equal(f.viewer.dataset.readerLayout,'scroll');
    assert.equal(f.swipe(-100).defaultPrevented,false);
  }finally{f.restore()}
});
test('intégration : défilement libre désactivant la pagination mobile',()=>{
  const f=fixture();
  try{
    f.toggle.checked=false;
    f.toggle.emit('change',{});
    assert.equal(f.viewer.dataset.readerLayout,'scroll');
    assert.equal(f.swipe(-100).defaultPrevented,false);
  }finally{f.restore()}
});
test('intégration : clavier flèche droite pagine sans double passage PDF',()=>{
  const f=fixture();
  try{
    const e={key:'ArrowRight',altKey:false,ctrlKey:false,metaKey:false,shiftKey:false,
      defaultPrevented:false,preventDefault(){this.defaultPrevented=true},
      stopImmediatePropagation(){}};
    f.documentMock.emit('keydown',e);
    assert.equal(e.defaultPrevented,true);
    assert.equal(f.viewer.scrollTop,315);
    assert.equal(f.next.clicks,0);
  }finally{f.restore()}
});
test('V61 : les raccourcis de lecture n’interceptent pas les flèches hors du livre',()=>{
  const f=fixture();
  const key=key=>({key,defaultPrevented:false,altKey:false,ctrlKey:false,
    metaKey:false,shiftKey:false,preventDefault(){this.defaultPrevented=true},
    stopImmediatePropagation(){}});
  try{
    f.documentMock.activeElement=f.documentMock;
    const elsewhere=key('ArrowRight');
    f.documentMock.emit('keydown',elsewhere);
    assert.equal(elsewhere.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    f.documentMock.activeElement=f.previous;
    const controls=key('PageDown');
    f.documentMock.emit('keydown',controls);
    assert.equal(controls.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    f.documentMock.activeElement=null;
    const noFocus=key('PageUp');
    f.documentMock.emit('keydown',noFocus);
    assert.equal(noFocus.defaultPrevented,false);
    f.documentMock.activeElement=f.viewer;
    const active=key('ArrowRight');
    f.documentMock.emit('keydown',active);
    assert.equal(active.defaultPrevented,true);
    assert.equal(f.viewer.scrollTop,315);
  }finally{f.restore()}
});
test('V61 : boutons de lecture annoncent écran ou page du livre selon le mode',()=>{
  const f=fixture();
  try{
    for(const control of [f.previous,f.mobilePrevious])
      assert.match(control.getAttribute('aria-label'),/Écran précédent/);
    for(const control of [f.next,f.mobileNext])
      assert.match(control.getAttribute('aria-label'),/Écran suivant/);
    f.text.hidden=true;
    f.toggle.emit('change',{});
    for(const control of [f.previous,f.mobilePrevious])
      assert.equal(control.getAttribute('aria-label'),'Page du livre précédente');
    for(const control of [f.next,f.mobileNext])
      assert.equal(control.getAttribute('aria-label'),'Page du livre suivante');
  }finally{f.restore()}
});
test('V61 : indications des raccourcis et focus visible existent dans la vraie page',()=>{
  const html=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  const css=readFileSync(new URL('../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  assert.match(html,/aria-keyshortcuts="ArrowLeft ArrowRight PageUp PageDown"/);
  assert.match(html,/placez d’abord le focus dans la zone du livre/);
  assert.match(css,/\.reader-viewer:focus-visible\{outline:3px solid/);
});
test('V61 : le moteur historique V26 ne doit pas doubler les flèches clavier V53',()=>{
  const source=readFileSync(new URL('../assets/js/sinjira-liseuse-v26.js',import.meta.url),'utf8');
  assert.match(source,/event\.defaultPrevented/);
  assert.match(source,/focused!==viewer/);
  assert.match(source,/viewer\.dataset\.readerLayout==='screens'/);
  assert.match(source,/viewer\.contains\(focused\)/);
});
test('contrat du HTML : le choix paginé et le mode PDF restent distincts',()=>{
  const h=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  assert.match(h,/id="reader-screens-enabled"/);
  assert.match(h,/id="reader-screen-count"/);
  assert.match(h,/sinjira-liseuse-reflow-v53\.mjs\?v=53\.11\.10\.1/);
  assert.match(h,/sinjira-liseuse-v26\.js\?v=34\.11\.07\.1/);
});
test('contrat CSS : texte responsive, mode continu, grands boutons tablette',()=>{
  const css=readFileSync(new URL('../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  assert.match(css,/reader-layout="screens"/);
  assert.match(css,/touch-action:pan-y pinch-zoom/);
  assert.match(css,/min-height:48px/);
  assert.match(css,/reader-layout="scroll"/);
});
test('V52 singleton: import V53 et script HTML ont exactement la même URL cache-bustée',()=>{
  const html=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  const module=readFileSync(new URL('../assets/js/sinjira-liseuse-reflow-v53.mjs',import.meta.url),'utf8');
  const htmlUrl='/assets/js/sinjira-liseuse-touch-v52.mjs?v=52.11.10.1';
  const importedUrl='./sinjira-liseuse-touch-v52.mjs?v=52.11.10.1';
  assert.ok(html.includes('src="'+htmlUrl+'"'));
  assert.ok(module.includes("'"+importedUrl+"'"));
  assert.equal(html.split('sinjira-liseuse-touch-v52.mjs').length-1,1);
});
test('la nouvelle fonction ne contient aucune écriture d’identité ou de roman',()=>{
  const module=readFileSync(new URL('../assets/js/sinjira-liseuse-reflow-v53.mjs',import.meta.url),'utf8');
  assert.doesNotMatch(module,/supabase|\.upsert\(|createSignedUrl|reader_library|localStorage\.setItem\([^,]+\+|serviceClient/);
  assert.match(module,/scrollTop/);
  assert.match(module,/PREF_KEY/);
});
