#!/usr/bin/env node
// Test fonctionnel du menu Nova sans navigateur ou service distant.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync('projets/projet-nova/script.js','utf8');
const html=readFileSync('projets/projet-nova/index.html','utf8');
assert.match(html,/script\.js\?v=26\.2\.0/);
assert.match(html,/boussole-electorale\.html/);
assert.match(html,/href="\/transparence-ia\.html"/);
const callbacks=new Map();
const bind=(target,name,fn)=>{
  if(!target.listeners)target.listeners=new Map();
  const old=target.listeners.get(name)||[];
  target.listeners.set(name,[...old,fn]);
};
const emit=(target,name,event={})=>(target.listeners?.get(name)||[]).forEach(fn=>fn(event));
const makeElement=()=>{
  const attrs=new Map();
  const classes=new Set();
  return {
    listeners:new Map(),
    classList:{
      toggle(name,on){
        if(on===undefined){on=!classes.has(name);}
        if(on)classes.add(name);else classes.delete(name);
      },
      contains(name){return classes.has(name);},
      add(name){classes.add(name);},
    },
    setAttribute(k,v){attrs.set(k,String(v));},
    getAttribute(k){return attrs.get(k)||null;},
    hasAttribute(k){return attrs.has(k);},
    contains(target){return target===this;},
    focus(){this.focusCount=(this.focusCount||0)+1;},
    querySelectorAll(){return [];},
    get textContent(){return this._textContent||'';},
    set textContent(v){this._textContent=v;},
    innerHTML:'',
    id:'',
  };
};
const nav=makeElement(),toggle=makeElement(),footer=makeElement(),list=makeElement(),heading=makeElement();
heading.textContent='Navigation';
footer.querySelector=(q)=>q==='h3'?heading:q==='ul'?list:null;
const window={innerWidth:500,location:{hostname:'www.benoitcantin.com',pathname:'/projets/projet-nova/'},listeners:new Map(),addEventListener(name,fn){bind(this,name,fn);}};
const head={appendChild(){}};
const document={
  readyState:'complete',head,body:{getAttribute:()=> 'index.html'},
  documentElement:{getAttribute:()=>null},
  listeners:new Map(),
  createElement:makeElement,
  addEventListener(name,fn){bind(this,name,fn);},
  querySelector(selector){
    if(selector==='[data-main-nav]')return nav;
    if(selector==='[data-menu-toggle]')return toggle;
    return null;
  },
  querySelectorAll(selector){return selector==='.footer section'?[footer]:[];},
};
const context={window,document,console};
vm.runInNewContext(source,context,{filename:'projets/projet-nova/script.js',timeout:2500});
assert.equal(nav.id,'navigation-nova');
assert.equal(toggle.getAttribute('aria-controls'),'navigation-nova');
assert.equal(toggle.getAttribute('aria-expanded'),'false');
assert.ok(nav.innerHTML.includes('boussole-electorale.html'));
assert.ok(list.innerHTML.includes('boussole-electorale.html'),'Le menu de pied de page dynamique doit contenir la Boussole');
assert.ok((document.listeners.get('pointerdown')||[]).length>0,'Fermeture tactile manquante');
assert.ok((window.listeners.get('resize')||[]).length>0,'Fermeture au redimensionnement manquante');
emit(toggle,'click');
assert.equal(toggle.getAttribute('aria-expanded'),'true');
assert.ok(nav.classList.contains('open'));
emit(document,'keydown',{key:'Escape'});
assert.equal(toggle.getAttribute('aria-expanded'),'false');
assert.equal(toggle.focusCount,1,'Échap doit restaurer le focus');
emit(toggle,'click');
emit(document,'pointerdown',{target:{}});
assert.equal(toggle.getAttribute('aria-expanded'),'false','Pointerdown en dehors doit fermer');
emit(toggle,'click');
emit(document,'click',{target:{}});
assert.equal(toggle.getAttribute('aria-expanded'),'false','Click clavier en dehors doit fermer');
emit(toggle,'click');
window.innerWidth=1201;
emit(window,'resize');
assert.equal(toggle.getAttribute('aria-expanded'),'false','Le redimensionnement desktop doit fermer');
assert.equal(toggle.getAttribute('aria-label'),'Ouvrir le menu');
assert.match(source,/if\(isOfficialHost&&!isNoindexSurface\)return;/,
  'La limitation de chargement automatique de l’assistant doit rester active');
assert.match(source,/data-ai-transparency-script/);
assert.match(source,/portal-global-nav/);
console.log('OK Projet Nova: Échap/focus, tactile, clic extérieur, resize, aria-controls, Boussole et IA.');
