import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {flashReaderPageTurn,cancelReaderPageTurnFlash,classifyReaderSwipe,classifyReaderEdgeTap,bindReaderTouchNavigation,isReaderSystemEdgeGesture,isReaderViewportZoomed,captureReaderSwipeGeometry,isReaderSwipeGeometryStable,hasReaderNestedHorizontalOverflow,readerCanPanHorizontally,readerCanPanVertically,hasReaderNestedVerticalOverflow,captureReaderNestedVerticalScroll,readerNestedVerticalScrollMoved,captureReaderNestedHorizontalScroll,readerNestedHorizontalScrollMoved} from '../assets/js/sinjira-liseuse-touch-v52.mjs';

const gesture=(overrides={})=>classifyReaderSwipe({
  dx:-92,dy:8,durationMs:240,viewerWidth:375,...overrides
});
test('V120 : gestes rapides annulent l ancien effet et respectent reduce en direct',()=>{
  const effects=[];
  const viewer={animate(){
    const listeners=new Map();
    const effect={cancels:0,addEventListener:(event,cb)=>listeners.set(event,cb),
      cancel(){this.cancels++;listeners.get('cancel')?.()},
      finish(){listeners.get('finish')?.()}};
    effects.push(effect);
    return effect;
  }};
  let reduce=false;
  const win={matchMedia:()=>({matches:reduce})};
  assert.equal(flashReaderPageTurn(viewer,'next',{win}),true);
  assert.equal(flashReaderPageTurn(viewer,'previous',{win}),true);
  assert.equal(effects.length,2);
  assert.equal(effects[0].cancels,1,'le geste suivant annule le liseré précédent');
  assert.equal(effects[1].cancels,0);
  reduce=true;
  assert.equal(flashReaderPageTurn(viewer,'next',{win}),false);
  assert.equal(effects.length,2,'ne plus lancer d animation quand reduce est demandé');
  assert.equal(effects[1].cancels,1,'arrêter aussi le liseré déjà visible');
  assert.equal(cancelReaderPageTurnFlash(viewer),false,'aucune animation orpheline');
  reduce=false;
  assert.equal(flashReaderPageTurn(viewer,'next',{win}),true);
  effects[2].finish();
  assert.equal(cancelReaderPageTurnFlash(viewer),false,'effet terminé libéré');
  assert.equal(flashReaderPageTurn(viewer,'previous',{win}),true);
  assert.equal(cancelReaderPageTurnFlash(viewer),true);
  assert.equal(effects[3].cancels,1);
  assert.equal(cancelReaderPageTurnFlash(viewer),false);
});
test('V119 : effet discret, directionnel et annulé si animation réduite',()=>{
  const shots=[];
  const viewer={animate(keyframes,options){shots.push({keyframes,options})}};
  const normal={matchMedia:()=>({matches:false})};
  const reduce={matchMedia:()=>({matches:true})};
  assert.equal(flashReaderPageTurn(viewer,'next',{win:normal}),true);
  assert.equal(flashReaderPageTurn(viewer,'previous',{win:normal}),true);
  assert.equal(shots.length,2);
  assert.match(shots[0].keyframes[0].boxShadow,/inset -26px/);
  assert.match(shots[1].keyframes[0].boxShadow,/inset 26px/);
  assert.equal(shots[0].options.duration,180);
  assert.equal(flashReaderPageTurn(viewer,'next',{win:reduce}),false);
  assert.equal(flashReaderPageTurn(viewer,'invalid',{win:normal}),false);
  assert.equal(flashReaderPageTurn({},'next',{win:normal}),false);
  assert.equal(shots.length,2);
  const broken={animate(){throw Error('API unavailable')}};
  assert.equal(flashReaderPageTurn(broken,'next',{win:normal}),false);
});
test('V119 : une navigation PDF montre un repère, jamais un swipe refusé',()=>{
  const f=fixture(),animation=[];
  f.viewer.animate=(frames)=>{animation.push(frames[0].boxShadow)};
  try{
    f.setPdfMode(true);
    f.swipe(-130,3);
    f.swipe(130,3);
    assert.equal(animation.length,2);
    assert.match(animation[0],/inset -26px/);
    assert.match(animation[1],/inset 26px/);
    f.swipe(-12,80);
    assert.equal(animation.length,2);
  }finally{f.release()}
  assert.equal(f.next.events.has('click'),false);
  assert.equal(f.previous.events.has('click'),false);
});
test('V133 : BFCache invalide le vieux doigt PDF mais pas le pageshow normal',()=>{
  const win=target(),f=fixture({win});
  const touch={identifier:133,clientX:250,clientY:190};
  const begin=()=>f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
  const end=()=>f.viewer.emit('touchend',{touches:[],
    changedTouches:[{...touch,clientX:95,clientY:193}],defaultPrevented:false});
  try{
    f.setPdfMode(true);
    begin();win.emit('pageshow',{persisted:false});f.advance(200);end();
    assert.equal(f.next.clicks,1,'reprise normale conserve le geste');
    begin();win.emit('pageshow',{persisted:true});f.advance(200);end();
    assert.equal(f.next.clicks,1,'un ancien geste ne tourne pas le PDF');
    f.swipe(130,3);assert.equal(f.previous.clicks,1,'nouveau geste droit disponible');
  }finally{f.release()}
  assert.equal(win.events.size,0,'pageshow est détaché');
});
test('V132 : sélection modifiée annule un toucher PDF et un drag souris',()=>{
  const doc=target(),f=fixture({doc});
  const start={identifier:132,clientX:250,clientY:190};
  const begin=()=>f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
  const end=()=>f.viewer.emit('touchend',{touches:[],
    changedTouches:[{...start,clientX:95,clientY:193}],defaultPrevented:false});
  const pointer=(kind,x)=>f.viewer.emit(kind,{
    pointerType:'mouse',pointerId:132,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    begin();doc.emit('selectionchange');f.advance(200);end();
    assert.equal(f.next.clicks,0,'sélection mobile : aucune page fantôme');
    pointer('pointerdown',250);doc.emit('selectionchange');
    f.advance(200);pointer('pointerup',95);
    assert.equal(f.next.clicks,0,'sélection souris : aucun ancien drag');
    doc.emit('selectionchange'); // aucune origine active
    f.swipe(-130,3);f.swipe(130,3);
    assert.equal(f.next.clicks,1,'gauche avance après la sélection');
    assert.equal(f.previous.clicks,1,'droite revient après la sélection');
  }finally{f.release()}
  assert.equal(doc.events.size,0,'écouteur selectionchange retiré');
});
test('V131 : menu contextuel annule ancien toucher et drag PDF sans bloquer menu',()=>{
  const f=fixture(),start={identifier:131,clientX:250,clientY:190};
  const begin=()=>f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
  const end=()=>f.viewer.emit('touchend',{touches:[],
    changedTouches:[{...start,clientX:95,clientY:192}],defaultPrevented:false});
  const pointer=(kind,x)=>f.viewer.emit(kind,{
    pointerType:'mouse',pointerId:131,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  const menu={defaultPrevented:false,preventDefault(){this.defaultPrevented=true}};
  try{
    f.setPdfMode(true);
    begin();f.viewer.emit('contextmenu',menu);f.advance(200);end();
    assert.equal(f.next.clicks,0,'pas de page fantôme après appui long');
    assert.equal(menu.defaultPrevented,false,'menu natif disponible');
    pointer('pointerdown',250);f.viewer.emit('contextmenu',menu);
    f.advance(200);pointer('pointerup',95);
    assert.equal(f.next.clicks,0,'drag souris périmé annulé');
    f.swipe(-130,3);f.swipe(130,3);
    assert.equal(f.next.clicks,1);assert.equal(f.previous.clicks,1);
  }finally{f.release()}
  assert.equal(f.viewer.events.has('contextmenu'),false);
});
test('V130 : plein écran annule les anciennes trajectoires PDF',()=>{
  const win=target(),f=fixture({win});
  const start={identifier:130,clientX:250,clientY:190};
  const begin=()=>f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
  const finish=()=>f.viewer.emit('touchend',{touches:[],
    changedTouches:[{...start,clientX:95,clientY:192}],defaultPrevented:false});
  const pointer=(type,x)=>f.viewer.emit(type,{
    pointerType:'mouse',pointerId:130,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    begin();win.emit('sinjira:reader-layout-will-change');
    f.advance(200);finish();
    assert.equal(f.next.clicks,0);
    pointer('pointerdown',250);win.emit('sinjira:reader-layout-will-change');
    f.advance(200);pointer('pointerup',95);
    assert.equal(f.next.clicks,0);
    f.swipe(-130,3);f.swipe(130,3);
    assert.equal(f.next.clicks,1);assert.equal(f.previous.clicks,1);
  }finally{f.release()}
  assert.equal(win.events.size,0,'nettoyage de l événement plein écran');
});
test('V129 : changement typographique annule le PDF et le drag, pas les nouveaux swipes',()=>{
  const doc=target();
  const f=fixture({doc});
  const start={identifier:7,clientX:250,clientY:190};
  const touchStart=()=>f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
  const touchEnd=()=>f.viewer.emit('touchend',{
    touches:[],changedTouches:[{...start,clientX:95,clientY:193}],
    defaultPrevented:false
  });
  const pointer=(type,x)=>f.viewer.emit(type,{
    pointerType:'mouse',pointerId:129,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    for(const id of ['reader-size','reader-font','reader-line-height',
      'reader-letter-spacing','reader-text-width']){
      touchStart();
      doc.emit('input',{target:{id}});
      f.advance(190);touchEnd();
      assert.equal(f.next.clicks,0,id+' ne doit pas tourner un ancien PDF');
    }
    pointer('pointerdown',250);
    doc.emit('change',{target:{id:'reader-font'}});
    f.advance(200);pointer('pointerup',90);
    assert.equal(f.next.clicks,0,'choix police interrompt le drag PDF');
    touchStart();
    doc.emit('input',{target:{id:'unrelated-search'}});
    f.advance(200);touchEnd();
    assert.equal(f.next.clicks,1,'contrôle étranger ne bloque pas le geste');
    f.swipe(-130,3);f.swipe(130,3);
    assert.equal(f.next.clicks,2,'gauche avance normalement après réglage');
    assert.equal(f.previous.clicks,1,'droite revient normalement après réglage');
  }finally{f.release()}
  assert.equal(doc.events.size,0,'input et change libérés au démontage');
});
test('V128 : rotation et viewport transitoires annulent le PDF et la souris',()=>{
  const win=target(),viewport=target();win.visualViewport=viewport;
  const f=fixture({win});
  const start={identifier:7,clientX:250,clientY:190};
  const touchStart=()=>f.viewer.emit('touchstart',{
    touches:[start],target:{closest:()=>null}});
  const touchEnd=()=>f.viewer.emit('touchend',{
    touches:[],changedTouches:[{...start,clientX:90,clientY:192}],
    defaultPrevented:false
  });
  const pointer=(kind,x)=>f.viewer.emit(kind,{
    pointerType:'mouse',pointerId:128,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    for(const name of ['resize','orientationchange']){
      touchStart();win.emit(name);f.advance(200);touchEnd();
      assert.equal(f.next.clicks,0,name+' : pas de saut de page');
    }
    touchStart();viewport.emit('resize');f.advance(200);touchEnd();
    assert.equal(f.next.clicks,0,'visualViewport annule aussi');
    pointer('pointerdown',250);
    win.emit('orientationchange');
    f.advance(200);pointer('pointerup',95);
    assert.equal(f.next.clicks,0,'rotation annule le drag souris PDF');
    f.swipe(-130,3);f.swipe(130,3);
    assert.equal(f.next.clicks,1,'gauche avance après rotation');
    assert.equal(f.previous.clicks,1,'droite revient après rotation');
    pointer('pointerdown',250);f.advance(200);pointer('pointerup',95);
    assert.equal(f.next.clicks,2,'nouveau drag PDF utilisable');
  }finally{f.release()}
  assert.equal(win.events.size,0,'écouteurs fenêtre libérés');
  assert.equal(viewport.events.size,0,'écouteurs visualViewport libérés');
});
test('V125 : mutations synchrones PDF texte PDF sont détectées avant touchend',()=>{
  const observers=[];
  class FakeObserver{
    constructor(fn){this.fn=fn;this.targets=[];this.pending=[];this.closed=false;observers.push(this)}
    observe(node,options){this.targets.push({node,options})}
    takeRecords(){return this.pending.splice(0)}
    disconnect(){this.closed=true}
  }
  const f=fixture({Observer:FakeObserver});
  const watcher=observers.find(o=>o.targets.some(x=>x.node===f.readingText));
  assert.ok(watcher);
  const start={identifier:7,clientX:250,clientY:190};
  const end={...start,clientX:100,clientY:192};
  const fireStart=()=>f.viewer.emit('touchstart',{
    touches:[start],target:{closest:()=>null}});
  const fireEnd=()=>f.viewer.emit('touchend',{
    touches:[],changedTouches:[end],defaultPrevented:false});
  try{
    f.setPdfMode(true);
    fireStart();
    f.setPdfMode(false);f.setPdfMode(true);
    watcher.pending.push(
      {type:'attributes',attributeName:'hidden',target:f.readingText},
      {type:'attributes',attributeName:'hidden',target:f.readingText});
    f.advance(180);
    fireEnd();
    assert.equal(f.next.clicks,0,'une vraie tâche synchrone ne change pas de page');
    assert.equal(watcher.pending.length,0,'mutations consommées avant le callback');
    fireStart();
    f.readingContent.hidden=true;f.readingContent.hidden=false;
    watcher.pending.push(
      {type:'attributes',attributeName:'hidden',target:f.readingContent});
    f.advance(180);
    fireEnd();
    assert.equal(f.next.clicks,0,'masquage synchrone du livre annule le toucher');
    // Les événements avant le nouveau contact ne doivent pas annuler
    // un vrai nouveau swipe vers la gauche, ou vers la droite.
    watcher.pending.push(
      {type:'attributes',attributeName:'hidden',target:f.readingText});
    f.swipe(-130,3);
    f.swipe(130,3);
    assert.equal(f.next.clicks,1,'gauche avance après purge initiale');
    assert.equal(f.previous.clicks,1,'droite revient après purge initiale');
    // Une mutation sans rapport (classe) ne modifie pas la navigation.
    fireStart();
    watcher.pending.push({type:'attributes',attributeName:'class'});
    f.advance(180);
    fireEnd();
    assert.equal(f.next.clicks,2,'un changement class ne bloque pas le PDF');
    // Le drag souris doit avoir la même protection que le toucher.
    const pointer=(type,x)=>f.viewer.emit(type,{
      pointerType:'mouse',pointerId:125,button:0,buttons:1,isPrimary:true,
      clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
      preventDefault(){this.defaultPrevented=true}
    });
    pointer('pointerdown',250);
    watcher.pending.push({type:'attributes',attributeName:'hidden'});
    f.advance(200);pointer('pointerup',95);
    assert.equal(f.next.clicks,2,'pas de saut de page après drag souris interrompu');
    pointer('pointerdown',250);f.advance(200);pointer('pointerup',95);
    assert.equal(f.next.clicks,3,'nouveau drag souris PDF utilisable');
  }finally{f.release()}
  assert.equal(watcher.closed,true,'l observateur est déconnecté');
});
test('V123 : mutation cachée PDF vers texte puis PDF annule un geste tactile',()=>{
  const observers=[];
  class FakeObserver{
    constructor(fn){this.fn=fn;this.watched=[];this.closed=false;this.pending=[];observers.push(this)}
    observe(node,options){this.watched.push({node,options})}
    disconnect(){this.closed=true}
    takeRecords(){return this.pending.splice(0)}
    queue(records){this.pending.push(...records)}
    notify(records){if(!this.closed)this.fn(records)}
  }
  const f=fixture({Observer:FakeObserver});
  const modeWatcher=observers.find(o=>o.watched.some(x=>x.node===f.readingText));
  assert.ok(modeWatcher,'surveiller le mode du texte réel');
  assert.deepEqual(modeWatcher.watched.map(x=>x.options.attributeFilter),[['hidden'],['hidden']]);
  assert.ok(modeWatcher.watched.some(x=>x.node===f.readingContent),
    'surveiller aussi le masquage du roman intégral');
  const start={identifier:7,clientX:245,clientY:190};
  const end={...start,clientX:95,clientY:193};
  try{
    f.setPdfMode(true);
    f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
    f.setPdfMode(false);f.setPdfMode(true);
    modeWatcher.notify([{type:'attributes',attributeName:'hidden',target:f.readingText}]);
    f.advance(190);
    f.viewer.emit('touchend',{touches:[],changedTouches:[end],defaultPrevented:false});
    assert.equal(f.next.clicks,0,'le mode revenu à PDF ne réactive pas le vieux doigt');
    f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
    f.readingContent.hidden=true;f.readingContent.hidden=false;
    modeWatcher.notify([{type:'attributes',attributeName:'hidden',target:f.readingContent}]);
    f.advance(190);
    f.viewer.emit('touchend',{touches:[],changedTouches:[end],defaultPrevented:false});
    assert.equal(f.next.clicks,0,'masquer puis révéler un nouveau livre annule le contact');
    modeWatcher.notify([{type:'attributes',attributeName:'class',target:f.readingText}]);
    f.swipe(-130,3);f.swipe(130,3);
    assert.equal(f.next.clicks,1,'le nouveau geste gauche fonctionne');
    assert.equal(f.previous.clicks,1,'le nouveau geste droit fonctionne');
  }finally{f.release()}
  assert.equal(modeWatcher.closed,true,'libérer les observers au démontage');
  assert.ok(observers.every(x=>x.closed),'aucun observateur résiduel');
});
test('V122 : changement PDF texte pendant un swipe sans page fantome',()=>{
  const f=fixture();
  try{
    f.setPdfMode(true);
    f.swipe(-130,3,{switchPdfMode:false});
    assert.equal(f.next.clicks,0,'PDF vers texte continu ne tourne pas');
    f.swipe(130,3,{switchPdfMode:true});
    assert.equal(f.previous.clicks,0,'texte continu vers PDF ne tourne pas');
    assert.equal(f.pageField.value,'3');
    f.swipe(-130,3);
    f.swipe(130,3);
    assert.equal(f.next.clicks,1,'gauche sur PDF avance toujours');
    assert.equal(f.previous.clicks,1,'droite sur PDF revient toujours');
  }finally{f.release()}
});
test('V122 : PDF vers texte puis PDF pendant touchmove invalide le swipe',()=>{
  const f=fixture();
  const start={identifier:7,clientX:245,clientY:190};
  try{
    f.setPdfMode(true);
    f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
    f.setPdfMode(false);
    f.viewer.emit('touchmove',{touches:[{...start,clientX:160,clientY:192}]});
    f.setPdfMode(true);
    f.advance(180);
    f.viewer.emit('touchend',{touches:[],changedTouches:[
      {...start,clientX:90,clientY:193}],defaultPrevented:false});
    assert.equal(f.next.clicks,0);
    f.swipe(-130,3);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V118 : notification de changement sans nouveau numéro annule un toucher PDF',()=>{
  const f=fixture();
  try{
    f.setPdfMode(true);
    f.swipe(-130,3,{emitPageChange:true});
    f.swipe(130,3,{emitPageChange:true});
    assert.equal(f.pageField.value,'3');
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
    f.swipe(-130,3);
    assert.equal(f.next.clicks,1,'la lecture reste possible sur la page remplacée');
  }finally{f.release()}
  assert.equal(f.viewer.events.has('sinjira:reader-page-change'),false,
    'la destruction libère aussi l écouteur de changement de page');
});
test('V118 : notification de nouvelle page annule le drag souris PDF',()=>{
  const f=fixture();
  const pointer=(kind,x)=>f.viewer.emit(kind,{
    pointerType:'mouse',pointerId:118,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    pointer('pointerdown',260);pointer('pointermove',180);
    f.viewer.emit('sinjira:reader-page-change');
    f.advance(200);pointer('pointerup',100);
    assert.equal(f.next.clicks,0);
    pointer('pointerdown',260);pointer('pointermove',180);
    f.advance(200);pointer('pointerup',100);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V117 : changement de page pendant un swipe PDF interdit le tournage',()=>{
  const f=fixture();
  try{
    f.setPdfMode(true);
    f.swipe(-130,2,{changePage:'4'});
    f.swipe(130,2,{changePage:'5'});
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
    f.swipe(-130,2);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V117 : changement de page pendant un drag souris PDF annule le geste',()=>{
  const f=fixture();
  const pointer=(name,x)=>f.viewer.emit(name,{
    pointerType:'mouse',pointerId:145,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    pointer('pointerdown',260);pointer('pointermove',170);
    f.pageField.value='4';f.advance(180);pointer('pointerup',80);
    assert.equal(f.next.clicks,0);
    pointer('pointerdown',260);pointer('pointermove',180);
    f.advance(180);pointer('pointerup',100);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V116 : une trajectoire contradictoire ne tourne pas le PDF',()=>{
  assert.equal(gesture({dx:-130,maxRightTravel:80}),null);
  assert.equal(gesture({dx:130,maxLeftTravel:80}),null);
  assert.equal(gesture({dx:-130,maxRightTravel:15}),'next');
  assert.equal(gesture({dx:130,maxLeftTravel:15}),'previous');
  assert.equal(gesture({dx:-130,maxRightTravel:NaN}),null);
  const f=fixture();
  try{
    f.swipe(-130,3,{moves:[[75,3],[-45,3]]});
    f.swipe(130,3,{moves:[[-75,3],[45,3]]});
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
    f.swipe(-130,3,{moves:[[-60,3],[-90,3]]});
    f.swipe(130,3,{moves:[[60,3],[90,3]]});
    assert.equal(f.next.clicks,1);
    assert.equal(f.previous.clicks,1);
  }finally{f.release()}
});
test('V116 : souris PDF inversée ne tourne pas le livre',()=>{
  const f=fixture();
  const emit=(type,x)=>f.viewer.emit(type,{
    pointerType:'mouse',pointerId:211,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,
    defaultPrevented:false,preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    emit('pointerdown',175);emit('pointermove',260);f.advance(160);emit('pointerup',40);
    emit('pointerdown',175);emit('pointermove',90);f.advance(160);emit('pointerup',310);
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
    emit('pointerdown',260);emit('pointermove',180);f.advance(160);emit('pointerup',110);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
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
test('petit déplacement, tap et longue pression sans glissement net sont ignorés',()=>{
  assert.equal(gesture({dx:-20}),null);
  assert.equal(gesture({dx:0,dy:0}),null);
  assert.equal(gesture({durationMs:860}),null);
});
test('V79 : glissement plus lent et volontaire reste utilisable sur téléphone',()=>{
  assert.equal(gesture({dx:-130,dy:3,durationMs:1200}),'next');
  assert.equal(gesture({dx:130,dy:3,durationMs:1500}),'previous');
  assert.equal(gesture({dx:-130,dy:3,durationMs:1800}),'next');
});
test('V79 : pression longue, déplacement court et diagonale lente sont refusés',()=>{
  assert.equal(gesture({dx:-92,durationMs:900}),null);
  assert.equal(gesture({dx:-105,durationMs:1500}),null);
  assert.equal(gesture({dx:-160,dy:90,durationMs:1250}),null);
  assert.equal(gesture({dx:-150,dy:3,durationMs:1801}),null);
  assert.equal(gesture({dx:-145,durationMs:1400,hasSelection:true}),null);
  assert.equal(gesture({dx:-145,durationMs:1400,horizontalOverflow:true}),null);
  assert.equal(gesture({dx:-145,durationMs:1400,scrolledDuringGesture:true}),null);
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
    getBoundingClientRect(){return {left:0,width:this.clientWidth}},
    addEventListener(name,callback){events.set(name,callback)},
    removeEventListener(name,callback){if(events.get(name)===callback)events.delete(name)},
    emit(name,event={}){events.get(name)?.(event)},
    click(){if(!this.disabled){this.clicks++;this.emit('click',{target:this})}},
    events
  };
}
function fixture({selected=false,Observer=null,win=globalThis.window,doc=globalThis.document}={}){
  const viewer=target(),previous=target(),next=target(),
        mobilePrevious=target(),mobileNext=target(),canvas=target(),
        readingContent=target();
  const pageField={value:'3'};
  canvas.id='reader-canvas';
  let time=0,selection=selected?'Sélection de citation':'',pdfMode=false;
  const readingText={get hidden(){return pdfMode}};
  viewer.querySelector=sel=>sel==='#reader-text'?readingText:
    sel==='#reader-canvas'?canvas:null;
  viewer.closest=selector=>selector==='#reader-content'?readingContent:
    selector==='[hidden]'&&readingContent.hidden?readingContent:null;
  const release=bindReaderTouchNavigation({
    viewer,previous,next,mobilePrevious,mobileNext,pageField,
    getSelectedText:()=>selection,clock:()=>time,Observer,win,doc
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
    if(options.nestedHorizontalScrollDuring){
      const {node,delta}=options.nestedHorizontalScrollDuring;
      const before=node.scrollLeft||0;
      node.scrollLeft=before+delta;
      viewer.emit('touchmove',{touches:[{identifier:7,clientX:x-16,clientY:190}]});
      node.scrollLeft=before;
    }
    if(options.nestedScrollDuring){
      const {node,delta}=options.nestedScrollDuring;
      const before=node.scrollTop||0;
      node.scrollTop=before+delta;
      viewer.emit('touchmove',{touches:[{identifier:7,clientX:x-16,clientY:190}]});
      node.scrollTop=before;
    }
    if(options.switchPdfMode!==undefined)pdfMode=Boolean(options.switchPdfMode);
    if(options.changePage)pageField.value=String(options.changePage);
    if(options.emitPageChange)viewer.emit('sinjira:reader-page-change');
    if(options.cancel)viewer.emit('touchcancel',{touches:[]});
    if(options.moveMultiple)viewer.emit('touchmove',{touches:[touch,{identifier:8}]});
    viewer.emit('touchend',{touches:[],changedTouches:[{
      identifier:options.wrongId?9:7,
      clientX:x+dx,clientY:190+dy
    }],defaultPrevented:Boolean(options.prevented)});
  };
  return {viewer,canvas,previous,next,mobilePrevious,mobileNext,pageField,release,swipe,
    readingText,readingContent,
    advance:ms=>{time+=ms},
    setSelected:v=>{selection=v},setPdfMode:v=>{pdfMode=v}};
}
test('V101 : glisser le PDF à la souris avance et revient exactement une fois',()=>{
  const f=fixture();
  const pointer=(kind,x,y=190,extra={})=>f.viewer.emit(kind,{
    pointerType:'mouse',pointerId:101,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:y,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true},...extra
  });
  try{
    f.setPdfMode(true);
    pointer('pointerdown',260);
    pointer('pointermove',180);
    f.advance(210);
    pointer('pointerup',95);
    assert.equal(f.next.clicks,1);
    pointer('pointerdown',95);
    pointer('pointermove',175);
    f.advance(210);
    pointer('pointerup',260);
    assert.equal(f.previous.clicks,1);
  }finally{f.release()}
});
test('V101 : la sélection du texte, les taps, le PDF masqué et le scroll restent sûrs',()=>{
  const f=fixture();
  const event=(kind,x,extra={})=>f.viewer.emit(kind,{
    pointerType:'mouse',pointerId:102,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true},...extra
  });
  try{
    // Un clic sans mouvement et une glissade en TEXTE ne font rien.
    f.setPdfMode(true);
    event('pointerdown',240);f.advance(120);event('pointerup',240);
    f.setPdfMode(false);
    event('pointerdown',250);f.advance(130);event('pointerup',90);
    // Le fallback tactile/stylet PDF est vérifié isolément en V158.
    f.setPdfMode(true);
    // La sélection ne doit jamais être écrasée.
    f.setSelected('Texte sélectionné');
    event('pointerdown',250);f.advance(120);event('pointerup',90);
    f.setSelected('');
    // Un vrai défilement intermédiaire annule le changement.
    event('pointerdown',250);
    f.viewer.scrollTop=28;event('pointermove',180);
    f.viewer.scrollTop=0;f.advance(120);event('pointerup',90);
    // La fermeture du livre durant le glissement annule le geste.
    event('pointerdown',250);f.setPdfMode(false);
    f.advance(120);event('pointerup',90);
    // Les gestes diagonaux et les longues pressions sont refusés.
    f.setPdfMode(true);
    event('pointerdown',250);f.advance(100);event('pointerup',90,{clientY:315});
    event('pointerdown',250);f.advance(2000);event('pointerup',90);
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
  }finally{f.release()}
});
test('V158 : pointeur tactile sans TouchEvents tourne le PDF une seule fois',()=>{
  const f=fixture();
  const pointer=(kind,x,y=190,extra={})=>f.viewer.emit(kind,{
    pointerType:'touch',pointerId:158,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:y,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true},...extra
  });
  try{
    f.setPdfMode(true);
    pointer('pointerdown',260);
    pointer('pointermove',180);
    f.advance(180);
    pointer('pointerup',95);
    assert.equal(f.next.clicks,1);
    pointer('pointerdown',95);
    pointer('pointermove',175);
    f.advance(180);
    pointer('pointerup',260);
    assert.equal(f.previous.clicks,1);
    // Ni appui court ni geste dont le navigateur a fait défiler le PDF.
    pointer('pointerdown',260);
    f.advance(80);
    pointer('pointerup',260);
    pointer('pointerdown',260);
    f.viewer.scrollTop=35;
    pointer('pointermove',180);
    f.viewer.scrollTop=0;
    f.advance(150);
    pointer('pointerup',90);
    assert.equal(f.next.clicks,1);
    f.setSelected('Extrait annoté');
    pointer('pointerdown',260);
    f.advance(150);
    pointer('pointerup',95);
    assert.equal(f.next.clicks,1);
    f.setSelected('');
    // Le fallback ne touche jamais le mode texte ni le pointeur secondaire.
    f.setPdfMode(false);
    pointer('pointerdown',260);
    f.advance(150);
    pointer('pointerup',95);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V158 : stylet sans TouchEvents et séquence couplée ne doublent pas le PDF',()=>{
  const f=fixture();
  const pointer=(kind,x,y=190,extra={})=>f.viewer.emit(kind,{
    pointerType:'pen',pointerId:159,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:y,target:f.canvas,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true},...extra
  });
  try{
    f.setPdfMode(true);
    pointer('pointerdown',260);
    pointer('pointermove',180);
    f.advance(190);
    pointer('pointerup',95);
    assert.equal(f.next.clicks,1,'stylet seul = une page');
    // Le navigateur émet ensuite les TouchEvents d'un même contact :
    // le flux tactile prime, pointerup ne doit pas cliquer une seconde fois.
    pointer('pointerdown',260);
    const touch={identifier:7,clientX:260,clientY:190};
    f.viewer.emit('touchstart',{touches:[touch],target:f.canvas});
    f.advance(180);
    f.viewer.emit('touchmove',{touches:[{identifier:7,clientX:180,clientY:192}]});
    f.viewer.emit('touchend',{touches:[],changedTouches:[{
      identifier:7,clientX:95,clientY:194
    }],defaultPrevented:false});
    pointer('pointerup',95);
    assert.equal(f.next.clicks,2,'couplage TouchEvent + PointerEvent = une page');
    pointer('pointerdown',260,190,{isPrimary:false});
    f.advance(150);
    pointer('pointerup',95);
    assert.equal(f.next.clicks,2,'pointeur secondaire sans effet');
  }finally{f.release()}
});
test('V101 : ancien touch PDF et souris PDF coexistent sans double déclenchement',()=>{
  const f=fixture();
  try{
    f.setPdfMode(true);
    f.viewer.emit('pointerdown',{
      pointerType:'touch',pointerId:9,button:0,clientX:260,clientY:190,
      target:f.canvas
    });
    f.swipe(-130,4,{startX:240,elapsed:100});
    f.viewer.emit('pointerup',{
      pointerType:'touch',pointerId:9,button:0,clientX:100,clientY:194,
      target:f.canvas
    });
    assert.equal(f.next.clicks,1);
    assert.equal(f.previous.clicks,0);
  }finally{f.release()}
});
test('V161 : toucher la gouttière vide du PDF peut avancer et revenir au doigt',()=>{
  const f=fixture();
  const pointer=(name,x,extra={})=>f.viewer.emit(name,{
    pointerType:'touch',pointerId:161,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.viewer,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true},...extra
  });
  try{
    f.setPdfMode(true);
    pointer('pointerdown',260);pointer('pointermove',175);
    f.advance(170);pointer('pointerup',90);
    assert.equal(f.next.clicks,1,'glisser à gauche depuis la marge avance');
    pointer('pointerdown',95);pointer('pointermove',185);
    f.advance(170);pointer('pointerup',260);
    assert.equal(f.previous.clicks,1,'glisser à droite depuis la marge revient');
    // Un tap sans déplacement ne tourne pas le PDF par PointerEvent.
    pointer('pointerdown',260);f.advance(80);pointer('pointerup',260);
    assert.equal(f.next.clicks,1);
    // Le texte paginé/continu reste géré uniquement par V53.
    f.setPdfMode(false);
    pointer('pointerdown',260);f.advance(150);pointer('pointerup',90);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V161 : stylet sur gouttière PDF fonctionne sans doubler les TouchEvents',()=>{
  const f=fixture();
  const pointer=(name,x)=>f.viewer.emit(name,{
    pointerType:'pen',pointerId:162,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target:f.viewer,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    pointer('pointerdown',260);pointer('pointermove',175);
    f.advance(190);pointer('pointerup',95);
    assert.equal(f.next.clicks,1);
    // Lors d'une séquence jumelée, le vrai TouchEvent conserve la priorité.
    pointer('pointerdown',260);
    const touch={identifier:22,clientX:260,clientY:190};
    f.viewer.emit('touchstart',{touches:[touch],target:f.viewer});
    f.advance(190);
    f.viewer.emit('touchend',{touches:[],changedTouches:[
      {identifier:22,clientX:95,clientY:190}
    ],defaultPrevented:false});
    pointer('pointerup',95);
    assert.equal(f.next.clicks,2,'une seule page par séquence couplée');
  }finally{f.release()}
});
test('V161 : ni souris en marge ni enfant interactif ne volent la navigation PDF',()=>{
  const f=fixture();
  const pointer=(name,x,target,pointerType='touch')=>f.viewer.emit(name,{
    pointerType,pointerId:163,button:0,buttons:1,isPrimary:true,
    clientX:x,clientY:190,target,defaultPrevented:false,
    preventDefault(){this.defaultPrevented=true}
  });
  try{
    f.setPdfMode(true);
    pointer('pointerdown',260,f.viewer,'mouse');
    f.advance(180);pointer('pointerup',95,f.viewer,'mouse');
    assert.equal(f.next.clicks,0,'la souris ne tourne que depuis le canvas');
    const button={closest:()=>({nodeName:'BUTTON'})};
    pointer('pointerdown',260,button);
    f.advance(180);pointer('pointerup',95,button);
    assert.equal(f.next.clicks,0,'bouton/zone interne non capturé');
    const child={closest:()=>null};
    pointer('pointerdown',260,child);
    f.advance(180);pointer('pointerup',95,child);
    assert.equal(f.next.clicks,0,'autre contenu interne non capturé');
    pointer('pointerdown',260,f.viewer);
    f.viewer.emit('pointercancel',{pointerId:163});
    f.advance(180);pointer('pointerup',95,f.viewer);
    assert.equal(f.next.clicks,0,'pointercancel retire le geste en cours');
    f.setSelected('citation sélectionnée');
    pointer('pointerdown',260,f.viewer);
    f.advance(180);pointer('pointerup',95,f.viewer);
    assert.equal(f.next.clicks,0,'la sélection du roman reste intacte');
    f.setSelected('');
    f.canvas.hidden=true;
    pointer('pointerdown',260,f.viewer);
    f.advance(180);pointer('pointerup',95,f.viewer);
    assert.equal(f.next.clicks,0,'canvas PDF masqué : marges non interactives');
  }finally{f.release()}
});

test('V97 : marges PDF et texte partagent les mêmes limites',()=>{
  const p={x:318,viewerWidth:375,durationMs:160};
  assert.equal(classifyReaderEdgeTap(p),'next');
  assert.equal(classifyReaderEdgeTap({...p,x:62}),'previous');
  assert.equal(classifyReaderEdgeTap({...p,x:188}),null);
  assert.equal(classifyReaderEdgeTap({...p,x:10}),null);
  assert.equal(classifyReaderEdgeTap({...p,x:370}),null);
  assert.equal(classifyReaderEdgeTap({...p,durationMs:400}),null);
  assert.equal(classifyReaderEdgeTap({...p,maxTravel:40}),null);
  assert.equal(classifyReaderEdgeTap({...p,hasSelection:true}),null);
  assert.equal(classifyReaderEdgeTap({...p,scrolled:true}),null);
});
test('V97 : en PDF, tap marge droite puis gauche = une page chacune',()=>{
  const f=fixture();
  try{
    f.setPdfMode(true);
    f.swipe(0,0,{startX:315,elapsed:120});
    f.swipe(0,0,{startX:65,elapsed:120});
    assert.equal(f.next.clicks,1);
    assert.equal(f.previous.clicks,1);
    // Le milieu et les bordures réservées au système ne tournent rien.
    f.swipe(0,0,{startX:185,elapsed:120});
    f.swipe(0,0,{startX:9,elapsed:120});
    assert.equal(f.next.clicks,1);
    assert.equal(f.previous.clicks,1);
  }finally{f.release()}
});
test('V97 : seul le PDF autorise les taps, jamais le texte continu',()=>{
  const f=fixture();
  try{
    f.swipe(0,0,{startX:315,elapsed:100});
    assert.equal(f.next.clicks,0);
    f.setPdfMode(true);
    f.swipe(0,0,{startX:315,elapsed:100});
    assert.equal(f.next.clicks,1);
    f.setPdfMode(false);
    f.swipe(0,0,{startX:315,elapsed:100});
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V97 : protéger le PDF contre appui long, retour du doigt et zoom',()=>{
  const f=fixture();
  const oldWindow=globalThis.window;
  try{
    f.setPdfMode(true);
    f.swipe(0,0,{startX:315,elapsed:450});
    f.swipe(0,0,{startX:315,elapsed:100,moves:[[60,0]]});
    f.swipe(0,0,{startX:315,elapsed:100,scrollDuring:45});
    f.setSelected('Citation PDF');
    f.swipe(0,0,{startX:315,elapsed:100});
    f.setSelected('');
    globalThis.window={visualViewport:{scale:1.5}};
    f.swipe(0,0,{startX:315,elapsed:100});
    assert.equal(f.next.clicks,0);
    globalThis.window=oldWindow;
    f.swipe(0,0,{startX:315,elapsed:100});
    assert.equal(f.next.clicks,1);
  }finally{globalThis.window=oldWindow;f.release()}
});
test('V97 : un contact commençant en texte et finissant en PDF ne tourne pas',()=>{
  const f=fixture();
  try{
    f.setPdfMode(false);
    const touch={identifier:7,clientX:315,clientY:190};
    f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
    f.setPdfMode(true);
    f.viewer.emit('touchend',{touches:[],changedTouches:[touch],defaultPrevented:false});
    assert.equal(f.next.clicks,0);
  }finally{f.release()}
});
test('V79 : un mouvement lent mais clairement horizontal tourne les pages PDF',()=>{
  const f=fixture();
  try{
    f.swipe(-135,3,{elapsed:1300});
    f.swipe(135,3,{elapsed:1500});
    assert.equal(f.next.clicks,1);
    assert.equal(f.previous.clicks,1);
    f.swipe(-95,3,{elapsed:1000});
    f.swipe(-150,3,{elapsed:1900});
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V78 : passer de texte paginé à PDF pendant un geste ne tourne pas le PDF',()=>{
  const f=fixture();
  try{
    const touch={identifier:7,clientX:245,clientY:190};
    f.viewer.dataset.readerLayout='screens';
    f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
    f.viewer.dataset.readerLayout='scroll';
    f.viewer.emit('touchend',{touches:[],changedTouches:[
      {...touch,clientX:105,clientY:192}
    ],defaultPrevented:false});
    assert.equal(f.next.clicks,0);
    f.swipe(-130,2);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V78 : changer de mode puis revenir durant touchmove annule le geste PDF',()=>{
  const f=fixture();
  try{
    const touch={identifier:7,clientX:245,clientY:190};
    f.viewer.dataset.readerLayout='scroll';
    f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
    f.viewer.dataset.readerLayout='screens';
    f.viewer.emit('touchmove',{touches:[{...touch,clientX:220,clientY:191}]});
    f.viewer.dataset.readerLayout='scroll';
    f.viewer.emit('touchend',{touches:[],changedTouches:[
      {...touch,clientX:95,clientY:192}
    ],defaultPrevented:false});
    assert.equal(f.next.clicks,0);
    f.swipe(-130,2);
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V77 : un tableau horizontal immobile autorise gauche et droite en PDF',()=>{
  const f=fixture();
  try{
    const table={clientWidth:185,scrollWidth:480,scrollLeft:85,parentElement:f.viewer};
    const child={parentElement:table,closest:()=>null};
    f.swipe(-130,2,{target:child});
    f.swipe(130,2,{target:child});
    assert.equal(f.next.clicks,1);
    assert.equal(f.previous.clicks,1);
  }finally{f.release()}
});
test('V77 : déplacement horizontal transitoire du tableau PDF annule le swipe',()=>{
  const f=fixture();
  try{
    const table={clientWidth:195,scrollWidth:430,scrollLeft:55,parentElement:f.viewer};
    const child={parentElement:table,closest:()=>null};
    f.swipe(-130,2,{target:child,nestedHorizontalScrollDuring:{node:table,delta:60}});
    assert.equal(table.scrollLeft,55);
    assert.equal(f.next.clicks,0);
    f.swipe(-130,2,{target:child});
    assert.equal(f.next.clicks,1);
  }finally{f.release()}
});
test('V77 : capture horizontale limitée aux éléments imbriqués défilables',()=>{
  const root={clientWidth:360,scrollWidth:700,scrollLeft:33};
  const outer={clientWidth:240,scrollWidth:450,scrollLeft:21,parentElement:root};
  const inner={clientWidth:140,scrollWidth:270,scrollLeft:5,parentElement:outer};
  const node={parentElement:inner};
  const history=captureReaderNestedHorizontalScroll(node,root);
  assert.equal(history.length,2);
  assert.equal(readerNestedHorizontalScrollMoved(history),false);
  inner.scrollLeft=9;
  assert.equal(readerNestedHorizontalScrollMoved(history),false);
  inner.scrollLeft=10;
  assert.equal(readerNestedHorizontalScrollMoved(history),true);
  assert.equal(captureReaderNestedHorizontalScroll({scrollLeft:90},root).length,0);
  assert.equal(readerNestedHorizontalScrollMoved(history,NaN),false);
});
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
    f.swipe(-130,2,{target:child,nestedHorizontalScrollDuring:{node:panel,delta:60}});
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
    f.swipe(-125,2,{target:child,nestedHorizontalScrollDuring:{node:panel,delta:75}});
    assert.equal(f.next.clicks,0);
    f.swipe(125,2,{target:child,nestedHorizontalScrollDuring:{node:panel,delta:65}});
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
test('V91 : un balayage PDF interrompu par blur, pagehide ou onglet masqué est annulé',()=>{
  const oldWindow=globalThis.window,oldDocument=globalThis.document;
  const win=target(),doc=target();
  win.innerWidth=390;win.innerHeight=844;doc.hidden=false;
  globalThis.window=win;globalThis.document=doc;
  const f=fixture();
  try{
    const start={identifier:7,clientX:250,clientY:190};
    const finish=()=>{
      f.viewer.emit('touchend',{touches:[],changedTouches:[{
        ...start,clientX:110,clientY:192
      }],defaultPrevented:false});
    };
    const begin=()=>f.viewer.emit('touchstart',{
      touches:[start],target:{closest:()=>null}
    });
    begin();win.emit('blur',{});finish();
    begin();win.emit('pagehide',{});finish();
    begin();doc.hidden=true;doc.emit('visibilitychange',{});finish();
    assert.equal(f.next.clicks,0,'aucune page ne doit être tournée après interruption');
    doc.hidden=false;
    begin();doc.emit('visibilitychange',{});finish();
    assert.equal(f.next.clicks,1,'un onglet visible conserve les gestes normaux');
  }finally{
    f.release();
    assert.equal(win.events.size,0,'listeners de fenêtre nettoyés');
    assert.equal(doc.events.size,0,'listener de visibilité nettoyé');
    globalThis.window=oldWindow;globalThis.document=oldDocument;
  }
});
test('V96 : aucune page PDF ni bouton mobile actif sous un livre masqué',()=>{
  const oldDocument=globalThis.document;
  const doc=target();
  doc.hidden=false;
  globalThis.document=doc;
  const f=fixture();
  try{
    let hidden=true;
    f.viewer.closest=selector=>selector==='[hidden]'&&hidden?{hidden:true}:null;
    f.swipe(-130,3);
    f.mobileNext.emit('click');
    assert.equal(f.next.clicks,0);
    doc.hidden=true;hidden=false;
    f.swipe(-130,3);
    f.mobileNext.emit('click');
    assert.equal(f.next.clicks,0,'onglet caché sans ancêtre masqué');
    doc.hidden=false;
    f.swipe(-130,3);
    f.mobileNext.emit('click');
    assert.equal(f.next.clicks,2,'une reprise visible rétablit les gestes');
  }finally{
    f.release();
    globalThis.document=oldDocument;
  }
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
  assert.match(html,/sinjira-liseuse-touch-v52\.mjs\?v=52\.11\.18\.158/);
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
