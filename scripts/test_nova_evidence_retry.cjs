#!/usr/bin/env node
"use strict";
// Exécuter le vrai explorateur documentaire deux fois : les anciens
// gestionnaires ne doivent pas survivre au rechargement des preuves.
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const assert=require("node:assert/strict");
const source=fs.readFileSync(path.resolve(__dirname,
  "../projets/projet-nova/assets/boussole-electorale.js"),"utf8");
const fn=source.match(/  function renderEvidenceExplorer\([^)]*\)\{[\s\S]*?\n  }\n\s*(?=  function renderDocumentaryStatus\()/);
assert.ok(fn,"Explorateur documentaire introuvable");
const listeners=new Map(),els=new Map();
let writes=0;
function element(id){
  if(els.has(id))return els.get(id);
  const el={value:"",checked:false,hidden:false,innerHTML:"",onchange:null,onclick:null,
    addEventListener(type,cb){if(!listeners.has(id+":"+type))listeners.set(id+":"+type,[]);
      listeners.get(id+":"+type).push(cb);},
    contains(){return true;},focus(){}};
  if(id==="#compass-evidence-question-status"){
    let value="";
    Object.defineProperty(el,"textContent",{get(){return value;},set(v){value=v;writes++;}});
  }
  els.set(id,el);return el;
}
function emit(id,type,target){
  const el=element(id);
  const event={target:target||el};
  if(typeof el["on"+type]==="function")el["on"+type](event);
  for(const cb of listeners.get(id+":"+type)||[])cb(event);
}
const ctx={
  $:element,
  esc:x=>String(x??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;"),
  safeSourceUrl:x=>String(x||""),
  DOCUMENTARY_STATUS_LABELS:{ambiguous:"Position indéterminée"},
  CONFIDENCE_LABELS:{low:"Faible"},
  console
};
vm.runInNewContext(fn[0]+"\nglobalThis.renderTest=renderEvidenceExplorer;",ctx,{timeout:2000});
const q={id:"q01",axis:"axis1",text:"Question du test"};
const qs={axes:[{id:"axis1",title:"Justice et libertés"}],questions:[q]};
const parties={parties:[{id:"p1",name:"Formation du test"}]};
const records=[{questionId:"q01",partyId:"p1",finalizable:true,
  secondIndependentReview:{status:"completed",reviewedAt:"2026-11-05"},
  proposedStatus:"ambiguous",sourceUrl:"https://example.org/preuve",
  evidenceSummary:"Source ambiguë",rationale:"Aucune extrapolation",confidence:"low"}];
const corpus={evidenceRecords:records,questions:[{questionId:"q01",statuses:{p1:"ambiguous"}}]};
ctx.renderTest(qs,parties,corpus);
ctx.renderTest(qs,parties,corpus);
const select="#compass-evidence-question";
const filter="#compass-evidence-only-documented";
const priority="#compass-evidence-priority-links";
for(const id of [select,filter]){
  const before=writes;
  emit(id,"change");
  assert.equal(writes-before,1,id+": un seul rendu après deux chargements");
}
const target={dataset:{compassPriority:"q01"},closest(){return this;}};
let before=writes;
emit(priority,"click",target);
assert.equal(writes-before,1,"Un seul rendu après le raccourci Q01");
for(const [id,type] of [[select,"change"],[filter,"change"],[priority,"click"]]){
  assert.ok((listeners.get(id+":"+type)||[]).length<=1,
    "Listeners empilés pour "+id+"/"+type);
}
console.log("OK NOVA : explorateur des preuves rechargé deux fois, un seul événement par action.");
