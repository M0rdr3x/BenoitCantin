import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {classifyReaderSwipe,bindReaderTouchNavigation} from '../assets/js/sinjira-liseuse-touch-v52.mjs';

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
    disabled:false,clicks:0,clientWidth:375,scrollWidth:375,
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
    const touch={identifier:7,clientX:170,clientY:190};
    viewer.emit('touchstart',{touches:options.multiple?[touch,{identifier:8,clientX:200,clientY:220}]:[touch],target:options.interactive?{closest:()=>({})}:{closest:()=>null}});
    time+=options.elapsed??200;
    if(options.cancel)viewer.emit('touchcancel',{touches:[]});
    if(options.moveMultiple)viewer.emit('touchmove',{touches:[touch,{identifier:8}]});
    viewer.emit('touchend',{touches:[],changedTouches:[{
      identifier:options.wrongId?9:7,
      clientX:170+dx,clientY:190+dy
    }],defaultPrevented:Boolean(options.prevented)});
  };
  return {viewer,previous,next,mobilePrevious,mobileNext,release,swipe,setSelected:v=>{selection=v}};
}
test('intégration : les gestes cliquent uniquement les commandes officielles',()=>{
  const x=fixture();x.swipe(-90);x.swipe(90);
  assert.equal(x.next.clicks,1);
  assert.equal(x.previous.clicks,1);
  x.release();
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
