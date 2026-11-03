#!/usr/bin/env node
"use strict";
// Exécute le moteur public dans un contexte isolé, sans navigateur ni réseau.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname,"..");
const data = JSON.parse(fs.readFileSync(path.join(root,"projets/projet-nova/data/boussole-electorale-v2.json"),"utf8"));
const script = fs.readFileSync(path.join(root,"projets/projet-nova/assets/boussole-electorale.js"),"utf8");
assert.match(script,/axisMinimumAnswered/);
assert.equal(data.axes.length,16);
assert.equal(data.questions.length,64);
assert.equal(data.methodology.axisMinimumAnswered,2);
const htmlHost={innerHTML:""};
const fakeDocument = {
  addEventListener(){}, querySelector(sel){return sel==="#compass-radar"?htmlHost:null;}
};
const context = {document:fakeDocument,window:{},navigator:{},console};
context.globalThis=context;
const injection = ";globalThis.__novaRuntimeTest = {state,calculate,renderRadar,buildResultText,configureSharing};\n";
const marker="})();";
const offset=script.lastIndexOf(marker);
assert.ok(offset>=0);
vm.runInNewContext(script.slice(0,offset)+injection+script.slice(offset),context,{timeout:1500});
const {state,calculate,renderRadar,buildResultText}=context.__novaRuntimeTest;
state.data=data;
const byAxis=axis=>data.questions.filter(q=>q.axis===axis);
const economy=byAxis(data.axes[0].id);
const evaluate=()=>Array.from(calculate());
const result=axis=>evaluate().find(r=>r.id===axis);
const [a,b,c]=economy;
state.answers.clear();
assert.equal(evaluate().filter(r=>r.score!==null).length,0,"Profil vide: aucun score");
state.answers.set(a.id,{value:3,importance:"normal"});
assert.equal(result(a.axis).answered,1);
assert.equal(result(a.axis).score,null,"Un seul item principal ne suffit pas");
state.answers.set(b.id,{value:3,importance:"normal"});
assert.equal(result(a.axis).answered,2);
assert.notEqual(result(a.axis).score,null,"Seuil à deux réponses atteint");
state.answers.set(c.id,{value:null,importance:"forte"});
assert.equal(result(a.axis).answered,2,"Une proposition passée ne compte pas");
const secondary = data.questions.find(q=>q.loadings?.some(l=>l.axis!==q.axis && Number(l.weight)>0));
if(secondary){
  state.answers.clear();
  state.answers.set(secondary.id,{value:3,importance:"normal"});
  for(const loading of secondary.loadings.filter(l=>l.axis!==secondary.axis)){
    assert.equal(result(loading.axis).score,null,"Une contribution secondaire ne suffit pas");
  }
}
state.answers.clear();
for(const q of data.questions)state.answers.set(q.id,{value:0,importance:"normal"});
let all=evaluate();
assert.equal(all.length,16);
for(const r of all){assert.equal(r.coverage,100);assert.equal(r.score,0);}
renderRadar(all);
assert.match(htmlHost.innerHTML,/<polygon points=/,"Polygone complet");
assert.equal((htmlHost.innerHTML.match(/<line /g)||[]).length,16);
state.answers.clear();
state.answers.set(a.id,{value:3,importance:"normal"});
state.answers.set(b.id,{value:-3,importance:"normal"});
all=evaluate();
renderRadar(all);
assert.doesNotMatch(htmlHost.innerHTML,/<polygon points=/,"Pas de polygone artificiel partiel");
assert.equal((htmlHost.innerHTML.match(/<line /g)||[]).length,16,"Les axes restent stables");
assert.equal((htmlHost.innerHTML.match(/class="compass-radar-marker"/g)||[]).length,1);
assert.match(htmlHost.innerHTML,/>—</,"Axes inconnus signalés");
assert.match(buildResultText(all),/Couverture moyenne/);
state.answers.clear();
for(const q of data.questions)state.answers.set(q.id,{value:3,importance:"forte"});
all=evaluate();
for(const r of all) {
  assert.ok(Number.isInteger(r.score) && Math.abs(r.score)<=100);
  assert.equal(r.answered,4);
}
assert.ok(!script.includes('$("#compass-share-native")?.addEventListener("click"'),"Pas de listeners de partage empilés");
assert.ok(script.includes("shareNative.onclick"));
console.log("OK : boussole 64 questions / 16 dimensions, seuil principal 2, sans opinion, contributions croisées, graphique et partage.");
