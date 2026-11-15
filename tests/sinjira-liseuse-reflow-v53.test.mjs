import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
  measureReaderScreen,readerScreenState,planReaderScreenTurn,bindReaderScreenMode,parseReaderLineHeight,
  captureReaderTextAnchor,restoreReaderTextAnchor,classifyReaderEdgeTap,
  prepareReaderPreferencePanels,bindReaderResponsivePanels,bindReaderQuickAccess,
  formatReaderMobileLocation,formatReaderAccessibleLocation
} from '../assets/js/sinjira-liseuse-reflow-v53.mjs';

const setup={scrollHeight:1050,clientHeight:350,lineHeight:35};

test('V115 : accès au livre donne le focus pour tourner au clavier sans contourner V26',()=>{
  const handlers=new Map(),link={
    hidden:true,
    addEventListener(name,fn){handlers.set(name,fn)},
    removeEventListener(name,fn){if(handlers.get(name)===fn)handlers.delete(name)}
  };
  const content={hidden:true};
  let notification=null,disconnected=false,focusCount=0,options=null;
  const viewer={focus(opts){focusCount++;options=opts}};
  class Observer{
    constructor(fn){notification=fn}
    observe(node,opts){assert.equal(node,content);assert.deepEqual(opts,{
      attributes:true,attributeFilter:['hidden']
    })}
    disconnect(){disconnected=true}
  }
  const release=bindReaderQuickAccess({link,content,viewer,Observer});
  function click(){
    let prevented=false;
    handlers.get('click')?.({preventDefault(){prevented=true}});
    return prevented;
  }
  try{
    assert.equal(link.hidden,true);
    assert.equal(click(),true,'un clic programmatique ne doit pas ouvrir une édition masquée');
    assert.equal(focusCount,0);
    content.hidden=false;notification();
    assert.equal(link.hidden,false);
    assert.equal(click(),false,'conserver le lien natif et son fragment');
    assert.equal(focusCount,1);
    assert.deepEqual(options,{preventScroll:true});
    content.hidden=true;notification();
    assert.equal(link.hidden,true);
    assert.equal(click(),true,'le lien redevient inactif lors de la suspension');
    assert.equal(focusCount,1);
    content.hidden=false;notification();
    assert.equal(click(),false);
    assert.equal(focusCount,2);
  }finally{release()}
  assert.equal(handlers.size,0,'retirer l écouteur après destruction');
  assert.equal(disconnected,true);
});
test('V114 : le guide tactile concerne aussi les tablettes de 768 et 820 px',()=>{
  const css=readFileSync(new URL('../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  const html=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  const tabletIndex=css.indexOf('/* V114 :');
  const desktopIndex=css.indexOf('/* V110',tabletIndex);
  assert.ok(tabletIndex>0&&desktopIndex>tabletIndex);
  const responsive=css.slice(tabletIndex,desktopIndex);
  assert.match(responsive,/@media\(max-width:980px\)\{/);
  assert.match(responsive,/\.reader-swipe-help summary\{[\s\S]*?min-height:44px/);
  assert.match(responsive,/\.reader-swipe-help summary:focus-visible\{/);
  assert.match(responsive,/\.reader-swipe-help p\{[\s\S]*?text-align:left/);
  assert.match(html,/sinjira-liseuse-v26\.css\?v=53\.11\.14\.114/);
  assert.match(html,/aria-describedby="reader-swipe-help"/);
});
test('V113 : aide tactile compacte, repliable et annoncée au lecteur',()=>{
  const html=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  const css=readFileSync(new URL('../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  assert.match(html,/aria-describedby="reader-swipe-help"/);
  assert.match(html,/<details class="reader-swipe-help">\s*<summary id="reader-swipe-help">/);
  assert.doesNotMatch(html,/<details class="reader-swipe-help" open>/);
  assert.match(html,/Glissez à gauche pour avancer, à droite pour revenir/);
  assert.match(html,/<\/summary>\s*<p>Sur téléphone ou tablette/);
  assert.match(html,/Les déplacements intermédiaires n’entraînent pas de sauvegarde/);
  assert.match(css,/\.reader-swipe-help summary\{[\s\S]*?min-height:44px/);
  assert.match(css,/\.reader-swipe-help summary:focus-visible\{/);
});
test('V112 : lien de lecture mobile masqué tant que V26 masque le livre',()=>{
  const html=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  const css=readFileSync(new URL('../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  assert.match(html,/id="reader-mobile-read-link" href="#reader-viewer" hidden/);
  assert.match(css,/\.reader-mobile-read-link\[hidden\]\{display:none!important\}/);
  const link={hidden:false},content={hidden:true};
  let callback=null,disconnected=false,observed=null;
  class FakeObserver{
    constructor(fn){callback=fn}
    observe(node,options){observed={node,options}}
    disconnect(){disconnected=true}
  }
  const release=bindReaderQuickAccess({link,content,Observer:FakeObserver});
  try{
    assert.equal(link.hidden,true);
    assert.equal(observed.node,content);
    assert.deepEqual(observed.options,{attributes:true,attributeFilter:['hidden']});
    content.hidden=false;callback();
    assert.equal(link.hidden,false);
    content.hidden=true;callback();
    assert.equal(link.hidden,true);
    content.hidden=false;callback();
    assert.equal(link.hidden,false);
  }finally{release()}
  assert.equal(disconnected,true);
  assert.equal(typeof bindReaderQuickAccess({}), 'function');
});
test('V111 : bascule ordinateur-tablette protège les choix de réglages volontaires',()=>{
  function fakeTarget(){
    const hooks=new Map();
    return {
      addEventListener(type,fn){hooks.set(type,fn)},
      removeEventListener(type,fn){if(hooks.get(type)===fn)hooks.delete(type)},
      emit(type){hooks.get(type)?.()},
      count(){return hooks.size}
    };
  }
  const media=fakeTarget();media.matches=false;
  const settingsSummary=fakeTarget(),voiceSummary=fakeTarget();
  const settings={open:false,querySelector:()=>settingsSummary};
  const voice={open:false,querySelector:()=>voiceSummary};
  const cleanup=bindReaderResponsivePanels({media,panels:[settings,voice]});
  try{
    assert.equal(settings.open,true);
    assert.equal(voice.open,true);
    media.matches=true;media.emit('change');
    assert.equal(settings.open,false);
    assert.equal(voice.open,false);
    settingsSummary.emit('click'); // l'utilisateur choisit ses réglages
    settings.open=true;
    media.matches=false;media.emit('change');
    assert.equal(settings.open,true);
    assert.equal(voice.open,true);
    media.matches=true;media.emit('change');
    assert.equal(settings.open,true); // ne pas refermer un réglage demandé
    assert.equal(voice.open,false);
    settingsSummary.emit('click');settings.open=false;
    media.matches=false;media.emit('change');
    assert.equal(settings.open,false); // respecter aussi sa fermeture
    assert.equal(voice.open,true);
    assert.equal(media.count(),1);
  }finally{cleanup()}
  assert.equal(media.count(),0);
  assert.equal(settingsSummary.count(),0);
  assert.equal(voiceSummary.count(),0);
  media.matches=true;media.emit('change');
  assert.equal(voice.open,true); // plus de mutation après cleanup
});
test('V110 : les réglages mobiles sont repliés au premier rendu, jamais verrouillés',()=>{
  const html=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  const css=readFileSync(new URL('../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  assert.match(html,/<details class="reader-settings">/);
  assert.match(html,/<details class="reader-audio-settings">/);
  assert.doesNotMatch(html,/<details class="reader-(?:settings|audio-settings)" open>/);
  assert.match(html,/class="reader-mobile-read-link" id="reader-mobile-read-link" href="#reader-viewer"/);
  assert.match(css,/\.reader-mobile-read-link:focus-visible/);
  assert.match(css,/\.reader-mobile-read-link\{[\s\S]*?min-height:48px/);
  const font={open:false},voice={open:false};
  assert.equal(prepareReaderPreferencePanels({media:{matches:true},panels:[font,voice]}),0);
  assert.deepEqual([font.open,voice.open],[false,false]);
  font.open=true; // l'utilisateur ouvre ses réglages volontairement
  assert.equal(prepareReaderPreferencePanels({media:{matches:true},panels:[font,voice]}),0);
  assert.deepEqual([font.open,voice.open],[true,false]);
  assert.equal(prepareReaderPreferencePanels({media:{matches:false},panels:[font,voice]}),1);
  assert.deepEqual([font.open,voice.open],[true,true]);
  assert.equal(prepareReaderPreferencePanels({media:{matches:false},panels:[font,voice]}),0);
});
test('V103 : libellé de la zone de lecture sans contenu privé',()=>{
  assert.equal(formatReaderAccessibleLocation({
    mode:'screens',screen:3,screens:8,page:4,total:20
  }),'Lecture du roman, texte adapté : écran 3 sur 8, page 4 sur 20.');
  assert.equal(formatReaderAccessibleLocation({
    mode:'pdf',page:5,total:20
  }),'Lecture du roman en PDF : page 5 sur 20. Pour une lecture accessible, choisissez le texte adaptable.');
  assert.equal(formatReaderAccessibleLocation({
    mode:'continuous',page:4,total:20
  }),'Lecture du roman, texte adaptable en défilement continu : page 4 sur 20.');
  assert.equal(formatReaderAccessibleLocation({
    mode:'screens',screen:99,screens:3,page:'',total:undefined
  }),'Lecture du roman, texte adapté : écran 3 sur 3, page inconnue.');
});
test('V102 : progression compacte lisible selon écrans, texte et PDF',()=>{
  assert.equal(formatReaderMobileLocation({
    mode:'screens',screen:3,screens:8,page:4,total:20
  }),'Écr. 3/8 · p. 4 / 20');
  assert.equal(formatReaderMobileLocation({
    mode:'continuous',page:4,total:20
  }),'Continu · p. 4 / 20');
  assert.equal(formatReaderMobileLocation({mode:'pdf',page:5,total:20}),
    'PDF · p. 5 / 20');
  assert.equal(formatReaderMobileLocation({
    mode:'screens',screen:20,screens:3,page:1,total:3
  }),'Écr. 3/3 · p. 1 / 3');
  assert.equal(formatReaderMobileLocation({
    mode:'screens',screen:0,screens:-2,page:'invalid'
  }),'Écr. 1/1 · page inconnue');
  assert.equal(formatReaderMobileLocation({mode:'pdf',page:3,total:undefined}),
    'PDF · p. 3');
});
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
    getBoundingClientRect(){return {left:0,width:this.clientWidth}},
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
  windowMock.visualViewport=mockTarget();
  windowMock.visualViewport.scale=1;
  globalThis.window=windowMock;
  const documentMock=mockTarget();
  documentMock.activeElement=null;
  globalThis.document=documentMock;
  const viewer=mockTarget(),text=mockTarget(),
    previous=mockTarget({disabled:firstBookPage}),
    next=mockTarget({disabled:lastBookPage}),
    mobilePrevious=mockTarget(),mobileNext=mockTarget(),
    toggle=mockTarget(),status=mockTarget(),pageField=mockTarget(),
    mobileHint=mockTarget(),totalPages=mockTarget(),
    screenJump=mockTarget(),screenJumpLabel=mockTarget(),
    pageAnnouncement=mockTarget();
  totalPages.textContent='20';
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
    pageField,mobileHint,totalPages,screenJump,screenJumpLabel,pageAnnouncement,media,getSelectionText:()=>selected,
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
    const started={touches:[begin],target:options.target||{closest:()=>null}};
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
    if(options.nestedHorizontalScrollDuring){
      const {node,delta}=options.nestedHorizontalScrollDuring;
      const before=node.scrollLeft||0;
      node.scrollLeft=before+delta;
      viewer.emit('touchmove',{touches:[{identifier:1,clientX:startX-16,clientY:140}]});
      node.scrollLeft=before;
    }
    if(options.nestedScrollDuring){
      const {node,delta}=options.nestedScrollDuring;
      const before=node.scrollTop||0;
      node.scrollTop=before+delta;
      viewer.emit('touchmove',{touches:[{identifier:1,clientX:startX-16,clientY:140}]});
      node.scrollTop=before;
    }
    now+=options.elapsed??200;
    viewer.emit('touchend',finished);
    return finished;
  }
  return {viewer,text,previous,next,mobilePrevious,mobileNext,toggle,status,
    pageField,mobileHint,totalPages,screenJump,screenJumpLabel,pageAnnouncement,
    documentMock,windowMock,media,restore,swipe,
    notifyText:()=>observed.find(x=>x.target===text)?.emit([{type:'childList'}]),
    flushFrames,getStatusWrites:()=>statusWrites,
    setSelected:v=>{selected=v}};
}
test('V119 : repère visible lors d un écran réel, pas sur un geste ignoré',()=>{
  const f=fixture(),animation=[];
  f.viewer.animate=(frames)=>{animation.push(frames[0].boxShadow)};
  try{
    const first=f.swipe(-130,3);
    assert.equal(first.defaultPrevented,true);
    assert.equal(animation.length,1);
    assert.match(animation[0],/inset -26px/);
    const second=f.swipe(130,3);
    assert.equal(second.defaultPrevented,true);
    assert.equal(animation.length,2);
    assert.match(animation[1],/inset 26px/);
    f.swipe(-10,100);
    assert.equal(animation.length,2);
    assert.equal(f.viewer.scrollTop,0);
  }finally{f.restore()}
});
test('V118 : signal canonique de page annule le geste même si le numéro reste stable',()=>{
  const f=fixture();
  try{
    const begin={identifier:118,clientX:250,clientY:160};
    f.viewer.emit('touchstart',{touches:[begin],target:{closest:()=>null}});
    const before=f.pageField.value;
    f.viewer.emit('sinjira:reader-page-change');
    let prevented=false;
    f.viewer.emit('touchend',{
      touches:[],changedTouches:[{...begin,clientX:120,clientY:164}],
      defaultPrevented:false,preventDefault(){prevented=true}
    });
    assert.equal(f.pageField.value,before);
    assert.equal(prevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    const valid=f.swipe(-130,3);
    assert.equal(valid.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V117 : changer la page pendant un swipe ne tourne pas le nouveau roman',()=>{
  const f=fixture();
  try{
    const start={identifier:19,clientX:255,clientY:160};
    f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
    f.pageField.value='5';
    let prevented=false;
    f.viewer.emit('touchend',{
      touches:[],changedTouches:[{...start,clientX:110,clientY:163}],
      defaultPrevented:false,preventDefault(){prevented=true}
    });
    assert.equal(prevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
    const fresh=f.swipe(-130,3);
    assert.equal(fresh.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V116 : un doigt qui revient sur sa trajectoire ne tourne pas l écran',()=>{
  const f=fixture();
  try{
    const initial=f.viewer.scrollTop;
    const left=f.swipe(-130,3,{moves:[[75,3],[-45,3]]});
    const right=f.swipe(130,3,{moves:[[-75,3],[45,3]]});
    assert.equal(left.defaultPrevented,false);
    assert.equal(right.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,initial);
    assert.equal(f.next.clicks,0);
    assert.equal(f.previous.clicks,0);
    const valid=f.swipe(-130,3,{moves:[[-60,3],[-90,3]]});
    assert.equal(valid.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>initial);
    const back=f.swipe(130,3,{moves:[[60,3],[90,3]]});
    assert.equal(back.defaultPrevented,true);
    assert.equal(f.viewer.scrollTop,initial);
  }finally{f.restore()}
});
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
test('V91 : un swipe texte est annulé si la liseuse perd le focus ou devient cachée',()=>{
  const f=fixture();
  try{
    const touch={identifier:1,clientX:250,clientY:140};
    const begin=()=>f.viewer.emit('touchstart',{
      touches:[touch],target:{closest:()=>null}
    });
    const finish=()=>f.viewer.emit('touchend',{
      touches:[],changedTouches:[{...touch,clientX:120,clientY:142}],
      defaultPrevented:false,preventDefault(){this.defaultPrevented=true}
    });
    begin();f.windowMock.emit('blur',{});finish();
    begin();f.windowMock.emit('pagehide',{});finish();
    begin();f.documentMock.hidden=true;
    f.documentMock.emit('visibilitychange',{});finish();
    assert.equal(f.viewer.scrollTop,0,'aucune navigation après interruption du geste');
    f.documentMock.hidden=false;
    begin();f.documentMock.emit('visibilitychange',{});finish();
    assert.ok(f.viewer.scrollTop>0,'navigation active dans un onglet visible');
  }finally{
    const w=f.windowMock,d=f.documentMock;
    f.restore();
    assert.equal((w.handlers.get('blur')||[]).length,0);
    assert.equal((w.handlers.get('pagehide')||[]).length,0);
    assert.equal((d.handlers.get('visibilitychange')||[]).length,0);
  }
});
test('V96 : livre privé masqué, aucun tap, swipe, clavier ou bouton ne tourne un écran',()=>{
  const f=fixture();
  try{
    // La visibilité de l'ancêtre est vérifiée au moment de chaque commande.
    let hidden=true;
    f.viewer.closest=selector=>selector==='[hidden]'&&hidden?{hidden:true}:null;
    const before=f.viewer.scrollTop;
    const tap=f.swipe(0,0,{startX:315,elapsed:100});
    const swipe=f.swipe(-125,3);
    assert.equal(tap.defaultPrevented,false);
    assert.equal(swipe.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,before);
    const e={key:'ArrowRight',defaultPrevented:false,altKey:false,ctrlKey:false,
      metaKey:false,shiftKey:false,preventDefault(){this.defaultPrevented=true},
      stopImmediatePropagation(){}};
    f.documentMock.emit('keydown',e);
    assert.equal(e.defaultPrevented,false);
    const click={defaultPrevented:false,preventDefault(){this.defaultPrevented=true},
      stopImmediatePropagation(){}};
    f.next.emit('click',click);
    f.mobileNext.emit('click',click);
    assert.equal(click.defaultPrevented,true,
      'le bouton canonique est intercepté avant son gestionnaire historique');
    assert.equal(f.viewer.scrollTop,before);
    assert.equal(f.next.clicks,0);
    // Le texte reste mesuré : un retour n'exige ni changement de mode,
    // ni téléchargement du livre, ni écriture de progression fantôme.
    assert.equal(f.viewer.dataset.readerLayout,'screens');
    hidden=false;
    assert.equal(f.swipe(-125,3).defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
    assert.equal(f.next.clicks,0);
  }finally{f.restore()}
});
test('V96 : onglet masqué, refus de tout nouveau geste même sans touchcancel',()=>{
  const f=fixture();
  try{
    f.documentMock.hidden=true;
    assert.equal(f.swipe(-125).defaultPrevented,false);
    assert.equal(f.swipe(0,0,{startX:315,elapsed:100}).defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    f.documentMock.hidden=false;
    assert.equal(f.swipe(-125).defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V89 : désactiver puis réactiver les écrans invalide une ancienne restitution',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    f.toggle.checked=false;
    f.toggle.emit('change',{});
    assert.equal(f.viewer.dataset.readerLayout,'scroll');
    // L'utilisateur continue en mode libre avant la fin des deux frames.
    f.viewer.scrollTo({top:560});
    f.toggle.checked=true;
    f.toggle.emit('change',{});
    f.flushFrames();
    assert.equal(f.viewer.dataset.readerLayout,'screens');
    assert.equal(f.viewer.scrollTop,560,
      'un ancien ratio de pagination ne doit pas effacer la lecture en continu');
  }finally{f.restore()}
});
test('V89 : retour au mode pages après lecture continue conserve le ratio actuel',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    f.toggle.checked=false;f.toggle.emit('change',{});
    f.flushFrames();
    f.viewer.scrollTo({top:560});
    f.toggle.checked=true;f.toggle.emit('change',{});
    f.flushFrames();
    assert.equal(f.viewer.dataset.readerLayout,'screens');
    assert.equal(f.viewer.scrollTop,560);
  }finally{f.restore()}
});
test('V90 : barre du navigateur mobile réajuste les écrans sans window.resize',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    // Le CSS 100dvh a changé la hauteur et le nombre de lignes visibles ;
    // seul visualViewport a notifié le changement.
    f.viewer.clientHeight=300;
    f.viewer.scrollHeight=1100;
    f.windowMock.visualViewport.emit('resize',{});
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,400);
    assert.match(f.status.textContent,/Écran/);
  }finally{f.restore()}
});
test('V90 : le pinch-zoom ne repositionne pas le roman et libère son listener',()=>{
  const f=fixture({deferredRaf:true});
  const visual=f.windowMock.visualViewport;
  try{
    f.viewer.scrollTo({top:350});
    visual.scale=1.6;
    f.viewer.clientHeight=300;
    f.viewer.scrollHeight=1100;
    visual.emit('resize',{});
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,350,
      'le redimensionnement du viewport en zoom ne doit pas modifier le scroll');
    visual.scale=1;
    visual.emit('resize',{});
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,400);
  }finally{
    f.restore();
    assert.equal((visual.handlers.get('resize')||[]).length,0,
      'pas de listener visualViewport orphelin après fermeture du lecteur');
  }
});
test('V90 : un vrai swipe prime sur un redimensionnement visualViewport',()=>{
  const f=fixture({deferredRaf:true});
  try{
    f.viewer.scrollTo({top:350});
    f.windowMock.visualViewport.emit('resize',{});
    f.viewer.scrollHeight=1750;
    const gesture=f.swipe(-130,2);
    assert.equal(gesture.defaultPrevented,true);
    const location=f.viewer.scrollTop;
    assert.ok(location>350,location);
    f.flushFrames();
    assert.equal(f.viewer.scrollTop,location);
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
test('V79 : la lecture paginée accepte un swipe lent et net puis un retour lent',()=>{
  const f=fixture();
  try{
    const forward=f.swipe(-135,3,{elapsed:1400});
    assert.equal(forward.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
    const reverse=f.swipe(135,3,{elapsed:1600});
    assert.equal(reverse.defaultPrevented,true);
    assert.equal(f.viewer.scrollTop,0);
    const hold=f.swipe(-135,3,{elapsed:1900});
    assert.equal(hold.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
  }finally{f.restore()}
});
test('V78 : bascule texte/continu pendant contact puis retour annule le swipe périmé',()=>{
  const f=fixture();
  try{
    const start={identifier:1,clientX:230,clientY:140};
    f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
    f.toggle.checked=false;
    f.toggle.emit('change',{});
    f.toggle.checked=true;
    f.toggle.emit('change',{});
    const ended={touches:[],changedTouches:[{...start,clientX:90,clientY:142}],
      defaultPrevented:false,preventDefault(){this.defaultPrevented=true}};
    f.viewer.emit('touchend',ended);
    assert.equal(ended.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    const resumed=f.swipe(-130,2);
    assert.equal(resumed.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V78 : disparition du mode écrans pendant touchmove annule définitivement le contact',()=>{
  const f=fixture();
  try{
    const start={identifier:1,clientX:230,clientY:140};
    f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
    f.viewer.dataset.readerLayout='scroll';
    f.viewer.emit('touchmove',{touches:[{...start,clientX:205,clientY:141}]});
    f.viewer.dataset.readerLayout='screens';
    const ended={touches:[],changedTouches:[{...start,clientX:90,clientY:143}],
      defaultPrevented:false,preventDefault(){this.defaultPrevented=true}};
    f.viewer.emit('touchend',ended);
    assert.equal(ended.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.swipe(-130,2).defaultPrevented,true);
  }finally{f.restore()}
});
test('V77 : texte paginé tourne la page sur un tableau horizontal immobile',()=>{
  const f=fixture();
  try{
    const table={clientWidth:190,scrollWidth:460,scrollLeft:70,parentElement:f.viewer};
    const child={parentElement:table,closest:()=>null};
    const evt=f.swipe(-130,2,{target:child});
    assert.equal(evt.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V77 : un tableau de texte défilé puis revenu ne provoque pas de fausse page',()=>{
  const f=fixture();
  try{
    const table={clientWidth:180,scrollWidth:460,scrollLeft:60,parentElement:f.viewer};
    const child={parentElement:table,closest:()=>null};
    const ignored=f.swipe(-130,2,{target:child,nestedHorizontalScrollDuring:{node:table,delta:70}});
    assert.equal(ignored.defaultPrevented,false);
    assert.equal(table.scrollLeft,60);
    assert.equal(f.viewer.scrollTop,0);
    const resumed=f.swipe(-130,2,{target:child});
    assert.equal(resumed.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V76 : balayage horizontal à travers une note immobile tourne l’écran texte',()=>{
  const f=fixture();
  try{
    const panel={clientHeight:120,scrollHeight:480,scrollTop:50,cssOverflowY:'auto',parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.windowMock.getComputedStyle=el=>({lineHeight:'35px',fontSize:'20px',overflowY:el.cssOverflowY||'visible'});
    const evt=f.swipe(-130,2,{target:child});
    assert.equal(evt.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V76 : une note qui bouge puis revient ne vole pas la lecture horizontale',()=>{
  const f=fixture();
  try{
    const panel={clientHeight:120,scrollHeight:480,scrollTop:50,cssOverflowY:'auto',parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.windowMock.getComputedStyle=el=>({lineHeight:'35px',fontSize:'20px',overflowY:el.cssOverflowY||'visible'});
    const evt=f.swipe(-130,2,{target:child,nestedScrollDuring:{node:panel,delta:45}});
    assert.equal(evt.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(panel.scrollTop,50);
  }finally{f.restore()}
});
test('V75 : faire défiler une note verticale ne tourne pas un écran de texte',()=>{
  const f=fixture();
  try{
    const panel={clientHeight:150,scrollHeight:450,cssOverflowY:'auto',parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.windowMock.getComputedStyle=el=>({lineHeight:'35px',fontSize:'20px',overflowY:el.cssOverflowY||'visible'});
    const stop=f.swipe(-130,2,{target:child,nestedScrollDuring:{node:panel,delta:65}});
    assert.equal(stop.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    const normal=f.swipe(-130,2);
    assert.equal(normal.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V75 : une note verticalement masquée ne désactive pas les pages écran',()=>{
  const f=fixture();
  try{
    const panel={clientHeight:150,scrollHeight:450,cssOverflowY:'hidden',parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.windowMock.getComputedStyle=el=>({lineHeight:'35px',fontSize:'20px',overflowY:el.cssOverflowY||'visible'});
    const go=f.swipe(-130,2,{target:child});
    assert.equal(go.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V74 : mode pages écran conserve le swipe malgré débordement masqué du texte',()=>{
  const f=fixture();
  try{
    f.viewer.scrollWidth=f.viewer.clientWidth+130;
    f.text.scrollWidth=f.text.clientWidth+220;
    f.windowMock.getComputedStyle=element=>({
      lineHeight:'35px',fontSize:'20px',
      overflowX:element===f.viewer?'hidden':element===f.text?'visible':'auto'
    });
    const evt=f.swipe(-130,2);
    assert.equal(evt.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V74 : sous-conteneur masqué est ignoré, mais auto-scroll empêche le tournage',()=>{
  const f=fixture();
  try{
    const panel={clientWidth:240,scrollWidth:390,cssOverflowX:'hidden',parentElement:f.viewer};
    const child={parentElement:panel,closest:()=>null};
    f.windowMock.getComputedStyle=element=>({
      lineHeight:'35px',fontSize:'20px',overflowX:element.cssOverflowX||'visible'
    });
    let evt=f.swipe(-130,2,{target:child});
    assert.equal(evt.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
    const previous=f.viewer.scrollTop;
    panel.cssOverflowX='auto';
    evt=f.swipe(-130,2,{target:child,nestedHorizontalScrollDuring:{node:panel,delta:70}});
    assert.equal(evt.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,previous);
  }finally{f.restore()}
});
test('V73 : un panneau de notes défilant conserve le geste horizontal en texte paginé',()=>{
  const f=fixture();
  try{
    const scroller={clientWidth:200,scrollWidth:420,parentElement:f.text};
    f.text.parentElement=f.viewer;
    const child={parentElement:scroller,closest:()=>null};
    const ignored=f.swipe(-130,2,{target:child,nestedHorizontalScrollDuring:{node:scroller,delta:65}});
    assert.equal(ignored.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    // Hors de ce panneau, la même distance avance d'un écran.
    const page=f.swipe(-130,2);
    assert.equal(page.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V73 : un petit dépassement interne ne désactive pas la pagination texte',()=>{
  const f=fixture();
  try{
    const scroller={clientWidth:200,scrollWidth:204,parentElement:f.viewer};
    const target={parentElement:scroller,closest:()=>null};
    const page=f.swipe(-130,2,{target});
    assert.equal(page.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V72 : rotation du cellulaire pendant un geste ne tourne pas l’écran texte',()=>{
  const f=fixture();
  try{
    f.windowMock.innerWidth=390;
    f.windowMock.innerHeight=840;
    const touch={identifier:1,clientX:230,clientY:140};
    f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
    f.viewer.clientWidth=560;
    f.windowMock.innerWidth=568;
    const end={touches:[],changedTouches:[{...touch,clientX:90,clientY:143}],
      defaultPrevented:false,preventDefault(){this.defaultPrevented=true}};
    f.viewer.emit('touchend',end);
    assert.equal(end.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    f.viewer.clientWidth=375;
    f.windowMock.innerWidth=390;
    const next=f.swipe(-130);
    assert.equal(next.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V72 : changement transitoire de hauteur pendant touchmove invalide le swipe texte',()=>{
  const f=fixture();
  try{
    f.windowMock.innerHeight=840;
    const touch={identifier:1,clientX:230,clientY:140};
    f.viewer.emit('touchstart',{touches:[touch],target:{closest:()=>null}});
    f.windowMock.innerHeight=700;
    f.viewer.emit('touchmove',{touches:[{...touch,clientX:190,clientY:143}]});
    f.windowMock.innerHeight=840;
    const end={touches:[],changedTouches:[{...touch,clientX:80,clientY:143}],
      defaultPrevented:false,preventDefault(){this.defaultPrevented=true}};
    f.viewer.emit('touchend',end);
    assert.equal(end.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
  }finally{f.restore()}
});
test('V71 : zoom par pincement sur mobile conserve le défilement natif du texte',()=>{
  const f=fixture();
  try{
    f.windowMock.visualViewport={scale:2};
    const start=f.swipe(-130,2);
    assert.equal(start.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    f.windowMock.visualViewport.scale=1;
    const page=f.swipe(-130,2);
    assert.equal(page.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V71 : zoom pendant un geste n’interrompt pas la page en cours',()=>{
  const f=fixture();
  try{
    f.windowMock.visualViewport={scale:1};
    const start={identifier:1,clientX:210,clientY:140};
    f.viewer.emit('touchstart',{touches:[start],target:{closest:()=>null}});
    f.windowMock.visualViewport.scale=1.5;
    const end={touches:[],changedTouches:[
      {...start,clientX:60,clientY:142}
    ],defaultPrevented:false,preventDefault(){this.defaultPrevented=true}};
    f.viewer.emit('touchend',end);
    assert.equal(end.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
  }finally{f.restore()}
});
test('V70 : le défilement horizontal de la liseuse ne tourne pas une page par balayage',()=>{
  const f=fixture();
  try{
    f.viewer.scrollWidth=f.viewer.clientWidth+160;
    const swipe=f.swipe(-130,3);
    assert.equal(swipe.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.next.clicks,0);
    // Les boutons accessibles restent disponibles si le texte est élargi.
    f.mobileNext.click();
    assert.ok(f.viewer.scrollTop>0);
  }finally{f.restore()}
});
test('V70 : un contenu texte plus large que son cadre ne vole pas le retour tactile',()=>{
  const f=fixture();
  try{
    f.text.scrollWidth=f.text.clientWidth+120;
    f.viewer.scrollTop=300;
    const back=f.swipe(130,2);
    assert.equal(back.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,300);
    assert.equal(f.previous.clicks,0);
  }finally{f.restore()}
});
test('V70 : quatre pixels de tolérance ne suppriment pas la pagination tactile normale',()=>{
  const f=fixture();
  try{
    f.viewer.scrollWidth=f.viewer.clientWidth+4;
    f.text.scrollWidth=f.text.clientWidth+4;
    const next=f.swipe(-130,2);
    assert.equal(next.defaultPrevented,true);
    assert.ok(f.viewer.scrollTop>0);
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
test('V95 : zones de tapotement : gauche revient, droite avance, centre ne tourne pas',()=>{
  const c={viewerWidth:375,durationMs:150};
  assert.equal(classifyReaderEdgeTap({...c,x:62}),'previous');
  assert.equal(classifyReaderEdgeTap({...c,x:320}),'next');
  assert.equal(classifyReaderEdgeTap({...c,x:185}),null);
  assert.equal(classifyReaderEdgeTap({...c,x:9}),null,'bord système réservé');
  assert.equal(classifyReaderEdgeTap({...c,x:369}),null,'bord système réservé');
  assert.equal(classifyReaderEdgeTap({...c,x:60,viewerWidth:200}),null,'écran trop étroit');
  assert.equal(classifyReaderEdgeTap({...c,x:NaN}),null);
});
test('V95 : pression longue, mouvement, sélection et scroll annulent les taps',()=>{
  const c={x:65,viewerWidth:375,durationMs:150};
  assert.equal(classifyReaderEdgeTap({...c,durationMs:400}),null);
  assert.equal(classifyReaderEdgeTap({...c,dx:20}),null);
  assert.equal(classifyReaderEdgeTap({...c,dy:15}),null);
  assert.equal(classifyReaderEdgeTap({...c,maxTravel:55}),null);
  assert.equal(classifyReaderEdgeTap({...c,hasSelection:true}),null);
  assert.equal(classifyReaderEdgeTap({...c,scrolled:true}),null);
});
test('V95 : tapotement mobile tourne les écrans sans double changement PDF',()=>{
  const f=fixture();
  try{
    const forward=f.swipe(0,0,{startX:315,elapsed:100});
    assert.equal(forward.defaultPrevented,true);
    assert.equal(f.viewer.scrollTop,315);
    assert.equal(f.next.clicks,0);
    const back=f.swipe(0,0,{startX:65,elapsed:100});
    assert.equal(back.defaultPrevented,true);
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.previous.clicks,0);
    const center=f.swipe(0,0,{startX:180,elapsed:100});
    assert.equal(center.defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
  }finally{f.restore()}
});
test('V95 : tapotement annulé après glissement, sélection, zoom ou mode continu',()=>{
  const f=fixture();
  try{
    assert.equal(f.swipe(0,0,{startX:65,elapsed:500}).defaultPrevented,false);
    assert.equal(f.swipe(0,0,{startX:65,moves:[[90,0]],elapsed:120}).defaultPrevented,false);
    f.setSelected('Texte sélectionné');
    assert.equal(f.swipe(0,0,{startX:315}).defaultPrevented,false);
    f.setSelected('');
    f.windowMock.visualViewport.scale=1.6;
    assert.equal(f.swipe(0,0,{startX:315}).defaultPrevented,false);
    f.windowMock.visualViewport.scale=1;
    f.toggle.checked=false;f.toggle.emit('change',{});
    assert.equal(f.swipe(0,0,{startX:315}).defaultPrevented,false);
    assert.equal(f.viewer.scrollTop,0);
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
test('V105 : le curseur et son libellé disparaissent ensemble selon le mode et la longueur',()=>{
  const f=fixture();
  try{
    assert.equal(f.screenJump.hidden,false);
    assert.equal(f.screenJumpLabel.hidden,false);
    f.text.hidden=true;
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(f.screenJump.hidden,true);
    assert.equal(f.screenJumpLabel.hidden,true);
    f.text.hidden=false;
    f.toggle.checked=false;
    f.toggle.emit('change',{});
    assert.equal(f.screenJump.hidden,true);
    assert.equal(f.screenJumpLabel.hidden,true);
    f.toggle.checked=true;
    f.toggle.emit('change',{});
    assert.equal(f.screenJump.hidden,false);
    assert.equal(f.screenJumpLabel.hidden,false);
    // Une courte page de texte tient en entier dans la zone visible.
    f.viewer.scrollHeight=f.viewer.clientHeight;
    f.viewer.scrollTop=0;
    f.viewer.emit('scroll',{});
    assert.equal(f.screenJump.hidden,true);
    assert.equal(f.screenJumpLabel.hidden,true);
    const source=f.pageField.value;
    f.screenJump.value='2';
    f.screenJump.emit('input',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.pageField.value,source);
    assert.equal(f.previous.clicks,0);
    assert.equal(f.next.clicks,0);
    // Un nouveau passage plus long restaure correctement la commande.
    f.viewer.scrollHeight=1050;
    f.viewer.emit('scroll',{});
    assert.equal(f.screenJump.hidden,false);
    assert.equal(f.screenJumpLabel.hidden,false);
    assert.equal(f.screenJump.max,'4');
  }finally{f.restore()}
});
test('V106 : glissement du curseur prévisualise sans déplacer le texte ni multiplier la sauvegarde',()=>{
  const f=fixture();
  try{
    let turns=0;
    f.viewer.dispatchEvent=event=>{
      if(event.type==='sinjira:reader-screen-turn')turns++;
      return true;
    };
    const source=f.pageField.value,initialStatus=f.status.textContent;
    for(const screen of ['2','3','2','3']){
      f.screenJump.value=screen;
      f.screenJump.emit('input',{target:f.screenJump});
      assert.equal(f.viewer.scrollTop,0);
      assert.equal(f.pageField.value,source);
      assert.equal(turns,0);
      assert.equal(f.status.textContent,initialStatus);
      assert.match(f.screenJump.getAttribute('aria-valuetext'),
        new RegExp('Écran '+screen+' sur 4.*relâcher pour lire cet écran'));
    }
    f.screenJump.emit('change',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,630);
    assert.equal(turns,1);
    assert.equal(f.screenJump.value,'3');
    assert.match(f.screenJump.getAttribute('aria-valuetext'),/Écran 3 sur 4/);
    assert.doesNotMatch(f.screenJump.getAttribute('aria-valuetext'),/relâcher/);
    assert.equal(f.pageField.value,source);
    // Confirmer une deuxième fois l'écran courant ne produit aucune écriture.
    f.screenJump.emit('change',{target:f.screenJump});
    assert.equal(turns,1);
    // Une nouvelle interaction abandonnée à la suite d'un swipe revient
    // à l'écran effectivement lu, sans effacer une position valide.
    f.screenJump.value='4';
    f.screenJump.emit('input',{target:f.screenJump});
    f.swipe(95);
    assert.equal(turns,2);
    assert.equal(f.screenJump.value,'2');
  }finally{f.restore()}
});
test('V107 : un change tardif du curseur ne réactive pas une navigation annulée',()=>{
  const f=fixture();
  try{
    let turns=0;
    f.viewer.dispatchEvent=event=>{
      if(event.type==='sinjira:reader-screen-turn')turns++;
      return true;
    };
    const preview=value=>{
      f.screenJump.value=String(value);
      f.screenJump.emit('input',{target:f.screenJump});
    };
    const commit=()=>f.screenJump.emit('change',{target:f.screenJump});
    preview(3);
    f.windowMock.emit('resize',{});
    f.screenJump.value='3'; // relâchement natif retardé après rotation
    commit();
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(turns,0);
    assert.equal(f.screenJump.value,'1');
    preview(3);commit();
    assert.equal(f.viewer.scrollTop,630);
    assert.equal(turns,1);
    preview(4);
    f.viewer.emit('sinjira:reader-page-change',{});
    f.screenJump.value='4'; // ancienne sélection réémise par le navigateur
    commit();
    assert.equal(f.viewer.scrollTop,630);
    assert.equal(turns,1);
    preview(4);
    f.swipe(95); // un geste plus récent prime sur le curseur
    const afterSwipe=f.viewer.scrollTop;
    assert.notEqual(afterSwipe,630);
    f.screenJump.value='4';commit();
    assert.equal(f.viewer.scrollTop,afterSwipe);
    assert.equal(turns,2);
    preview(4);commit(); // nouvelle action volontaire toujours possible
    assert.equal(f.viewer.scrollTop,700);
    assert.equal(turns,3);
  }finally{f.restore()}
});
test('V109 : le curseur revient immédiatement à l’écran réellement lu',()=>{
  const f=fixture();
  try{
    let turns=0;
    f.viewer.dispatchEvent=event=>{
      if(event.type==='sinjira:reader-screen-turn')turns++;
      return true;
    };
    const interruptions=[
      ()=>f.windowMock.emit('blur',{}),
      ()=>{f.documentMock.hidden=true;f.documentMock.emit('visibilitychange',{});f.documentMock.hidden=false},
      ()=>f.windowMock.emit('pagehide',{}),
      ()=>f.viewer.emit('touchcancel',{})
    ];
    for(const interrupt of interruptions){
      f.screenJump.value='3';
      f.screenJump.emit('input',{target:f.screenJump});
      assert.equal(f.screenJump.value,'3');
      assert.match(f.screenJump.getAttribute('aria-valuetext'),/relâcher pour lire/);
      interrupt();
      // Le navigateur peut ne JAMAIS produire de change à la reprise.
      assert.equal(f.screenJump.value,'1');
      assert.match(f.screenJump.getAttribute('aria-valuetext'),/^Écran 1 sur 4/);
      assert.doesNotMatch(f.screenJump.getAttribute('aria-valuetext'),/relâcher/);
      assert.equal(f.viewer.scrollTop,0);
      assert.equal(turns,0);
      f.screenJump.emit('change',{target:f.screenJump});
      assert.equal(f.viewer.scrollTop,0);
      assert.equal(turns,0);
    }
    f.screenJump.value='2';
    f.screenJump.emit('input',{target:f.screenJump});
    f.screenJump.emit('change',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,315);
    assert.equal(turns,1);
  }finally{f.restore()}
});
test('V108 : changer d’application annule une sélection de curseur inachevée',()=>{
  const f=fixture();
  try{
    let turns=0;
    f.viewer.dispatchEvent=event=>{
      if(event.type==='sinjira:reader-screen-turn')turns++;
      return true;
    };
    const preview=screen=>{
      f.screenJump.value=String(screen);
      f.screenJump.emit('input',{target:f.screenJump});
    };
    const commit=()=>f.screenJump.emit('change',{target:f.screenJump});
    preview(3);
    f.windowMock.emit('blur',{});
    f.screenJump.value='3';
    commit(); // change natif différé après avoir changé de fenêtre
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.screenJump.value,'1');
    assert.equal(turns,0);
    preview(2);commit(); // nouvelle interaction volontaire
    assert.equal(f.viewer.scrollTop,315);
    assert.equal(turns,1);
    preview(4);
    f.documentMock.hidden=true;
    f.documentMock.emit('visibilitychange',{});
    f.documentMock.hidden=false;
    f.screenJump.value='4';commit();
    assert.equal(f.viewer.scrollTop,315);
    assert.equal(turns,1);
    preview(4);
    f.windowMock.emit('pagehide',{});
    f.screenJump.value='4';commit();
    assert.equal(f.viewer.scrollTop,315);
    assert.equal(turns,1);
    preview(3);commit(); // la lecture reste utilisable après le retour
    assert.equal(f.viewer.scrollTop,630);
    assert.equal(turns,2);
  }finally{f.restore()}
});
test('V104 : curseur tactile navigue entre écrans sans changer le PDF',()=>{
  const f=fixture();
  try{
    assert.equal(f.screenJump.hidden,false);
    assert.equal(f.screenJump.max,'4');
    assert.equal(f.screenJump.value,'1');
    assert.match(f.screenJump.getAttribute('aria-valuetext'),/Écran 1 sur 4 · page 4/);
    f.screenJump.value='3';
    f.screenJump.emit('input',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,0);
    f.screenJump.emit('change',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,630);
    assert.equal(f.screenJump.value,'3');
    assert.match(f.mobileHint.textContent,/Écr. 3\/4/);
    assert.match(f.screenJump.getAttribute('aria-valuetext'),/Écran 3 sur 4 · page 4/);
    assert.equal(f.previous.clicks,0);
    assert.equal(f.next.clicks,0);
    f.screenJump.value='4';
    f.screenJump.emit('input',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,630);
    f.screenJump.emit('change',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,700); // fin réelle d'une page source
    assert.equal(f.screenJump.value,'4');
    f.screenJump.value='1';
    f.screenJump.emit('input',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,700);
    f.screenJump.emit('change',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,0);
    assert.equal(f.pageField.value,'4');
    for(const invalid of ['0','7','NaN','2.2']){
      f.screenJump.value=invalid;
      f.screenJump.emit('input',{target:f.screenJump});
      assert.equal(f.viewer.scrollTop,0);
    }
  }finally{f.restore()}
});
test('V104 : le curseur est désactivé en PDF ou en texte continu',()=>{
  const f=fixture();
  try{
    f.text.hidden=true;
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(f.screenJump.hidden,true);
    f.screenJump.value='3';
    f.screenJump.emit('input',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,0);
    f.text.hidden=false;
    f.toggle.checked=false;
    f.toggle.emit('change',{});
    assert.equal(f.screenJump.hidden,true);
    f.screenJump.value='3';
    f.screenJump.emit('input',{target:f.screenJump});
    assert.equal(f.viewer.scrollTop,0);
    f.toggle.checked=true;
    f.toggle.emit('change',{});
    assert.equal(f.screenJump.hidden,false);
  }finally{f.restore()}
});
test('V121 : PDF annonce seulement une vraie nouvelle page en mode visible',()=>{
  const f=fixture();
  try{
    assert.equal(f.pageAnnouncement.textContent,'');
    f.text.hidden=true;
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(f.pageAnnouncement.textContent,'');
    f.pageField.value='5';
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(f.pageAnnouncement.textContent,'Page 5 sur 20 du livre.');
    let writes=0,value=f.pageAnnouncement.textContent;
    Object.defineProperty(f.pageAnnouncement,'textContent',{
      configurable:true,get:()=>value,set:v=>{writes++;value=v}
    });
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(writes,0,'signal redondant sans nouvelle annonce');
    f.text.hidden=false;f.toggle.checked=true;f.pageField.value='6';
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(writes,0,'les écrans texte annoncent via leur propre statut');
    assert.match(f.status.textContent,/page 6 du livre/);
    f.text.hidden=true;
    f.pageField.value='7';f.documentMock.hidden=true;
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(writes,0,'onglet masqué');
    f.documentMock.hidden=false;
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(writes,0,'pas de rattrapage rétroactif');
    f.pageField.value='8';f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(writes,1);
    assert.equal(value,'Page 8 sur 20 du livre.');
    f.viewer.closest=()=>({hidden:true});
    f.pageField.value='9';f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(writes,1,'contenu de livre masqué');
    f.viewer.closest=()=>null;
    f.pageField.value='NaN';f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(writes,1,'numéro invalide');
  }finally{f.restore()}
});
test('V121 : annonce PDF accessible mais visuellement dissimulée',()=>{
  const html=readFileSync(new URL('../compte/liseuse.html',import.meta.url),'utf8');
  const css=readFileSync(new URL('../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  assert.match(html,/id="reader-page-announcement"[^>]*role="status" aria-live="polite"/);
  assert.match(css,/\.reader-screen-reader-status\{[\s\S]*?clip-path:inset\(50%\)/);
  assert.doesNotMatch(html,/id="reader-page-announcement"[^>]*aria-hidden="true"/);
});
test('V102 : barre mobile reflète écran, PDF, texte continu et page source',()=>{
  const f=fixture();
  try{
    assert.equal(f.mobileHint.textContent,'Écr. 1/4 · p. 4 / 20');
    assert.equal(f.viewer.getAttribute('aria-label'),
      'Lecture du roman, texte adapté : écran 1 sur 4, page 4 sur 20.');
    const before=f.status.textContent;
    f.swipe(-100);
    assert.equal(f.mobileHint.textContent,'Écr. 2/4 · p. 4 / 20');
    assert.match(f.viewer.getAttribute('aria-label'),/écran 2 sur 4, page 4 sur 20/);
    assert.notEqual(f.status.textContent,before);
    f.text.hidden=true;
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(f.mobileHint.textContent,'PDF · p. 4 / 20');
    assert.match(f.viewer.getAttribute('aria-label'),/en PDF : page 4 sur 20/);
    f.pageField.value='5';
    f.viewer.emit('sinjira:reader-page-change',{});
    assert.equal(f.mobileHint.textContent,'PDF · p. 5 / 20');
    assert.match(f.viewer.getAttribute('aria-label'),/en PDF : page 5 sur 20/);
    f.text.hidden=false;
    f.toggle.checked=false;
    f.toggle.emit('change',{});
    assert.equal(f.mobileHint.textContent,'Continu · p. 5 / 20');
    assert.match(f.viewer.getAttribute('aria-label'),/défilement continu : page 5 sur 20/);
    f.toggle.checked=true;
    f.toggle.emit('change',{});
    assert.match(f.mobileHint.textContent,/^Écr\. \d+\/4 · p\. 5 \/ 20$/);
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
  assert.match(h,/sinjira-liseuse-reflow-v53\.mjs\?v=53\.11\.15\.120/);
  assert.match(h,/sinjira-liseuse-v26\.js\?v=34\.11\.14\.102/);
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
  const htmlUrl='/assets/js/sinjira-liseuse-touch-v52.mjs?v=52.11.15.120';
  const importedUrl='./sinjira-liseuse-touch-v52.mjs?v=52.11.15.120';
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
