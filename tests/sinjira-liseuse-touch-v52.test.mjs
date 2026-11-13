import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {classifyReaderSwipe,bindReaderTouchNavigation,isReaderSystemEdgeGesture,isReaderViewportZoomed,captureReaderSwipeGeometry,isReaderSwipeGeometryStable,hasReaderNestedHorizontalOverflow,readerCanPanHorizontally,readerCanPanVertically,hasReaderNestedVerticalOverflow,captureReaderNestedVerticalScroll,readerNestedVerticalScrollMoved} from '../assets/js/sinjira-liseuse-touch-v52.mjs';

const gesture=(overrides={})=>classifyReaderSwipe({
  dx:-92,dy:8,durationMs:240,viewerWidth:375,...overrides
});
test('balayage de droite à gauche = page suivante',()=>{
  assert.equal(gesture(),'next');
});
test('balayage de gauche à droite = page précédente',()=>{
  assert.equal(gesture({dx:95}),'previous');
});
test('défilement vertical ne déclenche pas le changement de page',()=>{
  assert.equal(gesture({dx:-12,dy:110}),null);
});
test('déplacement diagonal reste une navigation libre',()=>{
  assert.equal(gesture({dx:-92,dy:75}),null);
});
test('petit déplacement, tap et longue pression sont ignorés',()=>{
  assert.equal(gesture({dx:-20}),null);
  assert.equal(gesture({dx:0,dy:0}),null);
  assert.equal(gesture({durationMs:860}),null);
});
test('seuil s’adapte à la largeur du téléphone ou tablette',()=>{
  assert.equal(gesture({dx:-57,viewerWidth:320}),'next');
  assert.equal(gesture({dx:-57,viewerWidth:800}),null);
  assert.equal(gesture({dx:-110,viewerWidth:800}),'next');
});
test('sélection de texte conservée, y compris marques et annotations',()=>{
  assert.equal(gesture({hasSelection:true}),null);
});
test('zoom PDF avec déplacement horizontal : pas de changement de page',()=>{
  assert.equal(gesture({horizontalOverflow:true}),null);
});
test('valeurs erronées ou durée impossible sont rejetées',()=>{
  assert.equal(gesture({dx:NaN}),null);
  assert.equal(gesture({viewerWidth:0}),null);
  assert.equal(gesture({durationMs:-5}),null);
  assert.equal(gesture({durationMs:Infinity}),null);
});
function target(){
  const events=new Map();
  return {
    disabled:false,clicks:0,clientWidth:375,scrollWidth:375,dataset:{},
    addEventListener(name,callback){events.set(name,callback)},
    removeEventListener(name,callback){if(events.get(name)===callback)events.delete(name)},
    emit(name,event={}){events.get(name)?.(event)},
    click(){if(!this.disabled){this.clicks++;this.emit('click',{target:this})}},
    events
  };
}
function fixture({selected=false}={}){
  const viewer=target(),previous=target(),next=target(),
        mobilePrevious=target(),mobileNext=target();
  let time=0,selection=selected?'Sélection de citation':'';
  const release=bindReaderTouchNavigation({
    viewer,previous,next,mobilePrevious,mobileNext,
    getSelectedText:()=>selection,clock:()=>time,Observer:null
  });
  const swipe=(dx,dy=5,options={})=>{
    const x=options.startX??170;
    const touch={identifier:7,clientX:x,clientY:190};
    viewer.emit('touchstart',{touches:options.multiple?[touch,{identifier:8,clientX:200,clientY:220}]:[touch],target:options.target||(options.interactive?{closest:()=>({})}:{closest:()=>null})});
    time+=options.elapsed??200;
    for(const [mx,my] of options.moves||[]){
      viewer.emit('touchmove',{touches:[{
        identifier:7,clientX:x+mx,clientY:190+my
      }]});
    }
    if(options.scrollDuring){
      viewer.scrollTop=(viewer.scrollTop||0)+options.scrollDuring;
      viewer.emit('touchmove',{touches:[touch]});
      viewer.scrollTop=0; // même si le scroll revient au départ, refuser
    }
    if(options.nestedScrollDuring){
      const {node,delta}=options.nestedScrollDuring;
      const before=node.scrollTop||0;
      node.scrollTop=before+delta;
      viewer.emit('touchmove',{touches:[{identifier:7,clientX:x-16,clientY:190}]});
      node.scrollTop=before;
    }
    if(options.cancel)viewer.emit('touchcancel',{touches:[]});
    if(options.moveMultiple)viewer.emit('touchmove',{touches:[touch,{identifier:8}]});
    viewer.emit('touchend',{touches:[],changedTouches:[{
      identifier:options.wrongId?9:7,
      clientX:x+dx,clientY:190+dy
    }],defaultPrevented:Boolean(options.prevented)});
  };
  return {viewer,previous,next,mobilePrevious,mobileNext,release,swipe,setSelected:v=>{selection=v}};
}
test('V76 : une note verticale immobile autorise gauche et droite sur le PDF',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={getComputedStyle:el=>({overflowY:el.cssOverflowY||'visible'})};
  const f=fixture();
  try{
    const panel={clientHeight:150,scrollHeight:500,scrollTop:25,cssOverflowY:'auto',parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.swipe(-130,2,{target:child});
    f.swipe(130,2,{target:child});
    assert.equal(f.next.clicks,1);
    assert.equal(f.previous.clicks,1);
  }finally{f.release();globalThis.window=oldWindow}
});
test('V76 : détecter le scroll d’une note revenue à son point de départ',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={getComputedStyle:el=>({overflowY:el.cssOverflowY||'visible'})};
  try{
    const viewer={clientHeight:400,scrollHeight:1200};
    const panel={clientHeight:140,scrollHeight:400,scrollTop:15,cssOverflowY:'auto',parentElement:viewer};
    const child={parentElement:panel};
    const captured=captureReaderNestedVerticalScroll(child,viewer);
    assert.equal(captured.length,1);
    assert.equal(readerNestedVerticalScrollMoved(captured),false);
    panel.scrollTop=18;
    assert.equal(readerNestedVerticalScrollMoved(captured),false);
    panel.scrollTop=20;
    assert.equal(readerNestedVerticalScrollMoved(captured),true);
    assert.equal(captureReaderNestedVerticalScroll({scrollTop:90},viewer).length,0);
    assert.equal(readerNestedVerticalScrollMoved(captured,NaN),false);
  }finally{globalThis.window=oldWindow}
});
test('V75 : un panneau vertical est défilable seulement si overflow-y le permet',()=>{
  const panel={clientHeight:210,scrollHeight:440};
  for(const overflowY of ['hidden','clip','visible'])
    assert.equal(readerCanPanVertically(panel,4,()=>({overflowY})),false);
  for(const overflowY of ['auto','scroll','overlay'])
    assert.equal(readerCanPanVertically(panel,4,()=>({overflowY})),true);
  assert.equal(readerCanPanVertically(panel,4,()=>undefined),true);
  panel.scrollHeight=214;
  assert.equal(readerCanPanVertically(panel,4,()=>({overflowY:'auto'})),false);
  assert.equal(readerCanPanVertically(panel,NaN,()=>({overflowY:'auto'})),false);
});
test('V75 : la détection verticale s’arrête au lecteur, sans capturer ses parents',()=>{
  const viewer={clientHeight:350,scrollHeight:1000,cssOverflowY:'auto'};
  const panel={clientHeight:180,scrollHeight:360,cssOverflowY:'auto',parentElement:viewer};
  const leaf={parentElement:panel};
  const original=globalThis.window;
  globalThis.window={getComputedStyle:el=>({overflowY:el.cssOverflowY})};
  try{
    assert.equal(hasReaderNestedVerticalOverflow(leaf,viewer),true);
    panel.cssOverflowY='hidden';
    assert.equal(hasReaderNestedVerticalOverflow(leaf,viewer),false);
    assert.equal(hasReaderNestedVerticalOverflow({parentElement:null},viewer),false);
    assert.equal(hasReaderNestedVerticalOverflow(leaf,viewer,-1),false);
  }finally{globalThis.window=original}
});
test('V75 : glisser sur une note PDF verticalement défilante ne tourne pas le livre',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={getComputedStyle:el=>({overflowY:el.cssOverflowY||'visible'})};
  const f=fixture();
  try{
    const panel={clientHeight:120,scrollHeight:550,cssOverflowY:'auto',parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.swipe(-130,2,{target:child,nestedScrollDuring:{node:panel,delta:55}});
    f.swipe(130,2,{target:child,nestedScrollDuring:{node:panel,delta:70}});
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
    f.swipe(-130,2);
    assert.equal(f.next.clicks,1);
  }finally{f.release();globalThis.window=oldWindow}
});
test('V75 : débordement vertical masqué PDF laisse tourner la page',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={getComputedStyle:el=>({overflowY:el.cssOverflowY||'visible'})};
  const f=fixture();
  try{
    const panel={clientHeight:100,scrollHeight:500,cssOverflowY:'hidden',parentElement:f.viewer};
    f.swipe(-130,2,{target:{parentElement:panel,closest:()=>null}});
    assert.equal(f.next.clicks,1);
  }finally{f.release();globalThis.window=oldWindow}
});
test('V74 : seulement un overflow-x véritablement défilable réserve le glissement',()=>{
  const element={clientWidth:300,scrollWidth:440};
  const style=overflowX=>()=>({overflowX});
  for(const overflowX of ['hidden','clip','visible'])
    assert.equal(readerCanPanHorizontally(element,4,style(overflowX)),false);
  for(const overflowX of ['auto','scroll','overlay'])
    assert.equal(readerCanPanHorizontally(element,4,style(overflowX)),true);
  assert.equal(readerCanPanHorizontally(element,4,()=>undefined),true);
  element.scrollWidth=304;
  assert.equal(readerCanPanHorizontally(element,4,style('auto')),false);
  assert.equal(readerCanPanHorizontally(element,NaN,style('auto')),false);
});
test('V74 : un tableau coupé par overflow hidden ne bloque pas le swipe PDF',()=>{
  const previousWindow=globalThis.window;
  globalThis.window={getComputedStyle:node=>({overflowX:node.cssOverflowX})};
  const f=fixture();
  try{
    const panel={clientWidth:210,scrollWidth:420,cssOverflowX:'hidden',parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.swipe(-130,2,{target:child});
    assert.equal(f.next.clicks,1);
    panel.cssOverflowX='auto';
    f.swipe(-130,2,{target:child});
    assert.equal(f.next.clicks,1);
  }finally{f.release();globalThis.window=previousWindow}
});
test('V74 : PDF avec zone principale non défilable ne bloque pas un geste',()=>{
  const previousWindow=globalThis.window;
  globalThis.window={getComputedStyle:node=>({overflowX:node.cssOverflowX})};
  const f=fixture();
  try{
    f.viewer.scrollWidth=600;
    f.viewer.cssOverflowX='hidden';
    f.swipe(-130,2);
    assert.equal(f.next.clicks,1);
    f.viewer.cssOverflowX='auto';
    f.swipe(-130,2);
    assert.equal(f.next.clicks,1);
  }finally{f.release();globalThis.window=previousWindow}
});
test('V73 : conteneur imbriqué débordant, faux débordement et nœud extérieur',()=>{
  const viewer={clientWidth:375,scrollWidth:375};
  const panel={clientWidth:300,scrollWidth:480,parentElement:viewer};
  const note={parentElement:panel,closest:()=>null};
  assert.equal(hasReaderNestedHorizontalOverflow(note,viewer),true);
  panel.scrollWidth=304;
  assert.equal(hasReaderNestedHorizontalOverflow(note,viewer),false);
  panel.scrollWidth=305;
  assert.equal(hasReaderNestedHorizontalOverflow(note,viewer),true);
  assert.equal(hasReaderNestedHorizontalOverflow({clientWidth:100,scrollWidth:900},viewer),false);
  assert.equal(hasReaderNestedHorizontalOverflow(note,viewer,NaN),false);
});
test('V73 : un geste sur un panneau PDF défilant ne tourne pas le roman',()=>{
  const f=fixture();
  try{
    const panel={clientWidth:210,scrollWidth:410,parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.swipe(-125,2,{target:child});
    assert.equal(f.next.clicks,0);
    f.swipe(125,2,{target:child});
    assert.equal(f.previous.clicks,0);
    f.swipe(-125,2);
    assert.equal(f.next.clicks,1);
    f.mobilePrevious.click();
    assert.equal(f.previous.clicks,1);
  }finally{f.release()}
});
test('V72 : géométrie stable ou fluctuation sous quatre pixels ne bloque pas le livre',()=>{
  const before={readerWidth:375,readerHeight:600,viewportWidth:390,viewportHeight:850};
  assert.equal(isReaderSwipeGeometryStable(before,{...before,readerHeight:604}),true);
  assert.equal(isReaderSwipeGeometryStable(before,{...before,readerWidth:320}),false);
  assert.equal(isReaderSwipeGeometryStable(before,{...before,viewportWidth:844}),false);
  assert.equal(isReaderSwipeGeometryStable(before,{...before,viewportHeight:750}),false);
  assert.equal(isReaderSwipeGeometryStable(before,{...before,readerHeight:undefined}),false);
  assert.equal(isReaderSwipeGeometryStable(null,before),false);
  assert.equal(isReaderSwipeGeometryStable(before,before,NaN),false);
  assert.equal(captureReaderSwipeGeometry({clientWidth:375,clientHeight:600},
    {innerWidth:390,innerHeight:850}).readerWidth,375);
});
test('V72 : une rotation pendant le balayage ne tourne pas la page PDF',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={innerWidth:390,innerHeight:850};
  const f=fixture();
  try{
    const touch={identifier:7,clientX:250,clientY:190};
    f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
    globalThis.window.innerWidth=844;
    f.viewer.clientWidth=800;
    f.viewer.emit('touchend',{touches:[],changedTouches:[
      {...touch,clientX:100,clientY:192}
    ],defaultPrevented:false});
    assert.equal(f.next.clicks,0);
    globalThis.window.innerWidth=390;
    f.viewer.clientWidth=375;
    f.swipe(-130);
    assert.equal(f.next.clicks,1);
  }finally{f.release();globalThis.window=oldWindow}
});
test('V72 : une variation transitoire de taille durant touchmove annule le geste PDF',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={innerWidth:390,innerHeight:850};
  const f=fixture();
  try{
    const touch={identifier:7,clientX:250,clientY:190};
    f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
    globalThis.window.innerHeight=720;
    f.viewer.emit('touchmove',{touches:[{...touch,clientX:220,clientY:191}]});
    globalThis.window.innerHeight=850;
    f.viewer.emit('touchend',{touches:[],changedTouches:[
      {...touch,clientX:100,clientY:192}
    ],defaultPrevented:false});
    assert.equal(f.next.clicks,0);
  }finally{f.release();globalThis.window=oldWindow}
});
test('V71 : le zoom visuel est détecté sans fausses alertes à échelle normale',()=>{
  assert.equal(isReaderViewportZoomed({scale:1}),false);
  assert.equal(isReaderViewportZoomed({scale:1.005}),false);
  assert.equal(isReaderViewportZoomed({scale:1.1}),true);
  assert.equal(isReaderViewportZoomed({scale:2}),true);
  assert.equal(isReaderViewportZoomed({scale:undefined}),false);
});
test('V71 : en zoom natif, glisser le PDF ne tourne jamais le livre',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={innerWidth:390,visualViewport:{scale:1.8}};
  const f=fixture();
  try{
    f.swipe(-125);f.swipe(125);
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
    // Revenir à l'échelle 1 restaure la lecture au doigt.
    globalThis.window.visualViewport.scale=1;
    f.swipe(-125);
    assert.equal(f.next.clicks,1);
  }finally{f.release();globalThis.window=oldWindow}
});
test('V71 : si le pincement démarre pendant le geste, le PDF ne tourne pas',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={innerWidth:390,visualViewport:{scale:1}};
  const f=fixture();
  try{
    const touch={identifier:7,clientX:200,clientY:190};
    f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
    globalThis.window.visualViewport.scale=1.7;
    f.viewer.emit('touchend',{touches:[],changedTouches:[
      {...touch,clientX:70,clientY:191}
    ],defaultPrevented:false});
    assert.equal(f.next.clicks,0);
  }finally{f.release();globalThis.window=oldWindow}
});
test('V67 : réserver 24 px de chaque bord pour le retour du navigateur',()=>{
  assert.equal(isReaderSystemEdgeGesture({clientX:0,viewportWidth:390}),true);
  assert.equal(isReaderSystemEdgeGesture({clientX:24,viewportWidth:390}),true);
  assert.equal(isReaderSystemEdgeGesture({clientX:366,viewportWidth:390}),true);
  assert.equal(isReaderSystemEdgeGesture({clientX:12,viewportWidth:390}),true);
  assert.equal(isReaderSystemEdgeGesture({clientX:25,viewportWidth:390}),false);
  assert.equal(isReaderSystemEdgeGesture({clientX:365,viewportWidth:390}),false);
  assert.equal(isReaderSystemEdgeGesture({clientX:220,viewportWidth:390}),false);
});
test('V67 : largeur absente ou invalide ne bloque pas le mouvement au doigt',()=>{
  assert.equal(isReaderSystemEdgeGesture({clientX:8,viewportWidth:undefined}),false);
  assert.equal(isReaderSystemEdgeGesture({clientX:8,viewportWidth:0}),false);
  assert.equal(isReaderSystemEdgeGesture({clientX:8,viewportWidth:70}),false);
  assert.equal(isReaderSystemEdgeGesture({clientX:NaN,viewportWidth:390}),false);
});
test('V67 : départ au bord gauche/droit ne tourne pas le PDF, centre reste actif',()=>{
  const oldWindow=globalThis.window;
  globalThis.window={innerWidth:390};
  const x=fixture();
  try{
    x.swipe(130,3,{startX:9});
    x.swipe(-130,3,{startX:381});
    assert.equal(x.previous.clicks,0);
    assert.equal(x.next.clicks,0);
    x.swipe(-130,3,{startX:250});
    x.swipe(130,3,{startX:120});
    assert.equal(x.previous.clicks,1);
    assert.equal(x.next.clicks,1);
  }finally{
    x.release();
    globalThis.window=oldWindow;
  }
});
test('intégration : les gestes cliquent uniquement les commandes officielles',()=>{
  const x=fixture();x.swipe(-90);x.swipe(90);
  assert.equal(x.next.clicks,1);
  assert.equal(x.previous.clicks,1);
  x.release();
});
test('V57 : mode pages écran V53 bloque totalement le double changement PDF par V52',()=>{
  const x=fixture();
  x.viewer.dataset={readerLayout:'screens'};
  x.swipe(-110);x.swipe(110);
  x.mobileNext.click();x.mobilePrevious.click();
  assert.equal(x.next.clicks,0);
  assert.equal(x.previous.clicks,0);
  x.viewer.dataset.readerLayout='scroll';
  x.swipe(-110);x.mobilePrevious.click();
  assert.equal(x.next.clicks,1);
  assert.equal(x.previous.clicks,1);
  x.release();
});
test('V57 : le module V52 annonce son statut au compagnon historique puis libère le marqueur',()=>{
  const x=fixture();
  assert.equal(x.viewer.dataset.readerTouchManaged,'v52');
  x.release();
  assert.equal(x.viewer.dataset.readerTouchManaged,undefined);
});
test('V57 : le compagnon V28 refuse le double geste quand V52 contrôle la lecture',()=>{
  const source=readFileSync(new URL('../assets/js/sinjira-liseuse-companion-v28.mjs',import.meta.url),'utf8');
  assert.match(source,/readerTouchManaged==='v52'/);
  assert.match(source,/readerLayout==='screens'/);
  assert.match(source,/event\.defaultPrevented/);
});
test('intégration : commandes de navigation en bas de l’écran',()=>{
  const x=fixture();
  x.mobileNext.click();x.mobilePrevious.click();
  assert.equal(x.next.clicks,1);
  assert.equal(x.previous.clicks,1);
  x.release();
});
test('intégration : sélection, champ interactif et événement annulé',()=>{
  const x=fixture({selected:true});
  x.swipe(-110);
  x.setSelected('');x.swipe(-110,0,{interactive:true});
  x.swipe(-110,0,{prevented:true});
  assert.equal(x.next.clicks,0);
  x.release();
});
test('V66 : le classificateur rejette une verticale intermédiaire même si le doigt termine droit',()=>{
  assert.equal(gesture({dx:-125,dy:3,maxVerticalTravel:112}),null);
  assert.equal(gesture({dx:-125,dy:3,maxVerticalTravel:14}),'next');
  assert.equal(gesture({dx:125,dy:4,maxVerticalTravel:120}),null);
});
test('V66 : un défilement natif pendant le geste interdit la commande PDF',()=>{
  assert.equal(gesture({scrolledDuringGesture:true}),null);
  assert.equal(gesture({maxVerticalTravel:NaN}),null);
  assert.equal(gesture({maxVerticalTravel:-5}),null);
});
test('V66 : trajet vertical puis horizontal de retour ne tourne pas le livre PDF',()=>{
  const x=fixture();
  x.swipe(-130,2,{moves:[[-5,110],[-60,12]]});
  assert.equal(x.next.clicks,0);
  x.swipe(130,2,{moves:[[5,-120],[65,-10]]});
  assert.equal(x.previous.clicks,0);
  x.swipe(-130,2,{moves:[[-70,8]]});
  assert.equal(x.next.clicks,1); // un véritable balayage reste disponible
  x.release();
});
test('V66 : scroll pendant toucher puis retour en place ne tourne pas le livre PDF',()=>{
  const x=fixture();
  x.swipe(-130,3,{scrollDuring:40});
  assert.equal(x.next.clicks,0);
  x.swipe(-130,3);
  assert.equal(x.next.clicks,1);
  x.release();
});
test('intégration : pas de swipe si un pincement ou une annulation a commencé',()=>{
  const x=fixture();
  x.swipe(-110,0,{multiple:true});
  x.swipe(-110,0,{moveMultiple:true});
  x.swipe(-110,0,{cancel:true});
  x.swipe(-110,0,{wrongId:true});
  assert.equal(x.next.clicks,0);
  x.release();
});
test('intégration : un bouton désactivé bloque le passage hors livre',()=>{
  const x=fixture();
  x.next.disabled=true;x.swipe(-110);
  x.previous.disabled=true;x.swipe(110);
  x.mobileNext.emit('click');x.mobilePrevious.emit('click');
  assert.equal(x.next.clicks,0);
  assert.equal(x.previous.clicks,0);
  x.release();
});
test('intégration : glissement vertical conserve la page et le scroll',()=>{
  const x=fixture();x.swipe(-20,115);
  assert.equal(x.next.clicks,0);
  assert.equal(x.previous.clicks,0);
  x.release();
});
test('intégration : PDF large en zoom conserve le défilement horizontal',()=>{
  const x=fixture();x.viewer.scrollWidth=550;x.swipe(-110);
  assert.equal(x.next.clicks,0);
  x.release();
});
test('intégration : débrancher les commandes supprime les écouteurs',()=>{
  const x=fixture();x.release();
  assert.equal(x.viewer.events.size,0);
  x.swipe(-110);
  assert.equal(x.next.clicks,0);
});
test('intégration : les boutons mobiles reflètent le statut initial des boutons de livre',()=>{
  const viewer=target(),previous=target(),next=target(),mobilePrevious=target(),mobileNext=target();
  previous.disabled=true;
  const release=bindReaderTouchNavigation({
    viewer,previous,next,mobilePrevious,mobileNext,
    getSelectedText:()=>'',clock:()=>0,Observer:null
  });
  assert.equal(mobilePrevious.disabled,true);
  assert.equal(mobileNext.disabled,false);
  release();
});
test('contrat HTML/CSS : module autonome et gestes expliqués',()=>{
  const html=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  const css=readFileSync(new URL('../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  assert.match(html,/sinjira-liseuse-touch-v52\.mjs\?v=52\.11\.10\.1/);
  assert.match(html,/id="reader-touch-prev"/);
  assert.match(html,/id="reader-touch-next"/);
  assert.match(html,/aria-describedby="reader-swipe-help"/);
  assert.match(css,/touch-action:auto/);
  assert.match(css,/min-height:48px/);
  assert.match(css,/env\(safe-area-inset-bottom/);
});
test('aucun changement des droits privés, du moteur CAS ou de la progression cloud',()=>{
  const module=readFileSync(new URL('../assets/js/sinjira-liseuse-touch-v52.mjs',import.meta.url),'utf8');
  assert.doesNotMatch(module,/supabase|upsert|localStorage|sessionStorage|fetch\(|createSignedUrl/i);
});
