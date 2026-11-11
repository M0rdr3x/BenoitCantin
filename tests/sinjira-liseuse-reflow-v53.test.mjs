import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
  measureReaderScreen,readerScreenState,planReaderScreenTurn,bindReaderScreenMode,parseReaderLineHeight
} from '../assets/js/sinjira-liseuse-reflow-v53.mjs';

const setup={scrollHeight:1050,clientHeight:350,lineHeight:35};
const turn=(direction,scrollTop)=>planReaderScreenTurn({direction,scrollTop,...setup});

test('CSS line-height sans unité se convertit en hauteur réelle',()=>{
  assert.equal(parseReaderLineHeight({lineHeight:'1.75',fontSize:'20px'}),35);
  assert.equal(parseReaderLineHeight({lineHeight:'2.1',fontSize:'24px'}),50.4);
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
    handlers
  };
}
function fixture({selected='',lastBookPage=false,firstBookPage=false}={}){
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
  const media=mockTarget();media.matches=true;
  let now=0;
  const teardown=bindReaderScreenMode({
    viewer,text,previous,next,mobilePrevious,mobileNext,toggle,status,
    pageField,media,getSelectionText:()=>selected,
    clock:()=>now,raf:fn=>fn(),Observer:null
  });
  function restore(){
    teardown();
    globalThis.window=oldWindow;globalThis.document=oldDocument;
  }
  function swipe(dx,dy=3,options={}){
    const begin={identifier:1,clientX:175,clientY:140};
    const end={identifier:1,clientX:175+dx,clientY:140+dy};
    const started={touches:[begin],target:{closest:()=>null}};
    const finished={
      touches:[],changedTouches:[end],defaultPrevented:false,
      preventDefault(){this.defaultPrevented=true}
    };
    viewer.emit('touchstart',started);
    now+=options.elapsed??200;
    viewer.emit('touchend',finished);
    return finished;
  }
  return {viewer,text,previous,next,mobilePrevious,mobileNext,toggle,status,
    pageField,documentMock,windowMock,media,restore,swipe,
    setSelected:v=>{selected=v}};
}
test('intégration : le mode pages d’écran est activé par défaut sur mobile',()=>{
  const f=fixture();
  try{
    assert.equal(f.viewer.dataset.readerLayout,'screens');
    assert.match(f.status.textContent,/Écran 1 sur 4/);
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
test('la nouvelle fonction ne contient aucune écriture d’identité ou de roman',()=>{
  const module=readFileSync(new URL('../assets/js/sinjira-liseuse-reflow-v53.mjs',import.meta.url),'utf8');
  assert.doesNotMatch(module,/supabase|\.upsert\(|createSignedUrl|reader_library|localStorage\.setItem\([^,]+\+|serviceClient/);
  assert.match(module,/scrollTop/);
  assert.match(module,/PREF_KEY/);
});
