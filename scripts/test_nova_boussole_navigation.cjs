#!/usr/bin/env node
"use strict";
// Simulation du vrai moteur NOVA : 64 interactions, clavier/navigation,
 // aucune dépendance, aucun navigateur réel, aucune requête ni stockage.
const assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const json=JSON.parse(fs.readFileSync(path.join(root,"projets/projet-nova/data/boussole-electorale-v2.json"),"utf8"));
const source=fs.readFileSync(path.join(root,"projets/projet-nova/assets/boussole-electorale.js"),"utf8");
assert.equal(json.questions.length,64);
assert.equal(json.axes.length,16);

const nodes=new Map();
let focusCount=0,scrollCount=0,networkCalls=0,storageCalls=0;
function el(id){
  if(nodes.has(id))return nodes.get(id);
  const item={
    id,hidden:false,disabled:false,innerHTML:"",textContent:"",value:"",style:{},
    attrs:{},href:"",
    setAttribute(k,v){this.attrs[k]=String(v);},
    getAttribute(k){return k==="href"?this.href:this.attrs[k]??null;},
    focus(){focusCount++;},
    scrollIntoView(){scrollCount++;},
    replaceChildren(child){this.current=child;this.innerHTML=child?.innerHTML||"";},
    querySelector(sel){return sel==="[data-compass-question-focus]"?{focus(){focusCount++;}}:null;}
  };
  if(id==="compass-share-facebook")item.href="https://www.facebook.com/sharer/sharer.php";
  if(id==="compass-share-x")item.href="https://x.com/intent/post";
  if(id==="compass-share-linkedin")item.href="https://www.linkedin.com/sharing/share-offsite/";
  nodes.set(id,item);return item;
}
function fieldset(){
  return {
    dataset:{},className:"",innerHTML:"",handlers:{},
    addEventListener(event,fn){this.handlers[event]=fn;},
    querySelector(sel){return sel==="[data-importance]"?{value:"normal"}:null;}
  };
}
const fakeDocument={
  querySelector:selector=>selector.startsWith("#")?el(selector.slice(1)):null,
  createElement:tag=>tag==="fieldset"?fieldset():{style:{},setAttribute(){},remove(){},select(){}},
  addEventListener(){}
};
const ctx={
  document:fakeDocument,
  window:{matchMedia:()=>({matches:true}),location:{href:"https://www.benoitcantin.com/projets/projet-nova/boussole-electorale.html"}},
  navigator:{},
  localStorage:{getItem(){storageCalls++;throw Error("localStorage interdit");},setItem(){storageCalls++;throw Error("localStorage interdit");}},
  fetch(){networkCalls++;throw Error("Aucune requête attendue");},console
};
ctx.globalThis=ctx;
const marker="})();",at=source.lastIndexOf(marker);
assert.ok(at>=0);
const expose=";globalThis.__test={state,startQuestionnaire,goPrevious,goNext,reset,calculate,updateStepControls};";
vm.runInNewContext(source.slice(0,at)+expose+source.slice(at),ctx,{timeout:2500});
const engine=ctx.__test;
engine.state.data=json;

function choose(value){
  const stage=el("compass-question-stage");
  const fn=stage.current?.handlers.change;
  assert.equal(typeof fn,"function","Événement de réponse non connecté");
  fn({target:{
    value:value===null?"skip":String(value),
    matches:selector=>selector==='input[type="radio"]'
  }});
  assert.equal(el("compass-next").disabled,false,"Une réponse ou « Sans opinion » autorise la suite");
}
function run(answers){
  assert.equal(answers.length,64);
  engine.reset();
  assert.equal(engine.state.answers.size,0);
  engine.startQuestionnaire();
  assert.equal(el("compass-start-panel").hidden,true);
  assert.equal(el("compass-stepper").hidden,false);
  assert.equal(el("compass-next").disabled,true,"La première question n'est pas préremplie");
  engine.goNext();
  assert.equal(engine.state.currentIndex,0,"Ne pas sauter une question sans choix");
  for(let i=0;i<64;i++){
    assert.equal(engine.state.currentIndex,i);
    assert.equal(el("compass-question-stage").current.dataset.questionId,json.questions[i].id);
    choose(answers[i]);
    const answer=engine.state.answers.get(json.questions[i].id);
    assert.equal(answer.value,answers[i]);
    assert.equal(el("compass-progress-track").attrs["aria-valuenow"],String(i+1));
    if(i===0){
      engine.goNext();
      assert.equal(engine.state.currentIndex,1);
      engine.goPrevious();
      assert.equal(engine.state.currentIndex,0);
      assert.match(el("compass-question-stage").innerHTML,answers[0]===null?/value="skip" checked/:new RegExp('value="'+answers[0]+'" checked'));
      assert.equal(el("compass-next").disabled,false,"Réponse retenue après retour");
    }
    if(i===63)assert.equal(el("compass-next").textContent,"Consulter mes résultats");
    engine.goNext();
    if(i<63)assert.equal(engine.state.currentIndex,i+1);
  }
  assert.equal(el("compass-results").hidden,false,"Le parcours doit toujours pouvoir se terminer");
  assert.equal(engine.state.answers.size,64);
  assert.equal((el("compass-results-grid").innerHTML.match(/class="compass-result-card"/g)||[]).length,16);
  assert.equal(el("compass-progress-track").attrs["aria-valuenow"],"64");
  assert.equal(el("compass-progress-track").attrs["aria-valuemax"],"64");
  assert.ok(focusCount>0,"La progression doit annoncer les nouvelles questions");
  assert.ok(scrollCount>0,"Les sections doivent rester accessibles à la navigation");
  return engine.calculate().filter(r=>r.score!==null).length;
}

const complete=Array.from({length:64},(_,i)=>i%5===0?null:((i%7)-3));
assert.equal(run(complete),16,"Le profil complet doit couvrir seize axes");
assert.match(el("compass-summary").textContent,/16 dimensions/);
assert.match(el("compass-radar").innerHTML,/<polygon points=/);

assert.equal(run(Array(64).fill(null)),0,"Aucun score pour 64 réponses sans opinion");
assert.match(el("compass-summary").textContent,/Aucune dimension calculable/);
assert.match(el("compass-summary").textContent,/0 proposition/);
assert.doesNotMatch(el("compass-radar").innerHTML,/<polygon points=/);

assert.equal(run([2,...Array(63).fill(null)]),0,"Un seul item ne suffit pas");
assert.match(el("compass-summary").textContent,/au moins deux propositions principales/);
assert.doesNotMatch(el("compass-radar").innerHTML,/<polygon points=/);

engine.reset();
assert.equal(engine.state.answers.size,0);
assert.equal(el("compass-start-panel").hidden,false);
assert.equal(el("compass-stepper").hidden,true);
assert.equal(el("compass-results").hidden,true);
assert.equal(networkCalls,0,"La boussole ne transmet aucun résultat");
assert.equal(storageCalls,0,"La boussole ne persiste aucune réponse");
console.log("OK : navigation 64 étapes, réponse/retour, 16 axes, zéro opinion, une opinion, résultats, reset, confidentialité.");
