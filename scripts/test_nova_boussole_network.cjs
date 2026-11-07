#!/usr/bin/env node
"use strict";
// Contrôle isolé du repli JSON de la boussole et du questionnaire 64/16.
// Aucun appel au site réel, aucun vote, aucune sauvegarde de réponses.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const base=path.resolve(__dirname,"../projets/projet-nova");
const source=fs.readFileSync(path.join(base,"assets/boussole-electorale.js"),"utf8");
const corpus=JSON.parse(fs.readFileSync(path.join(base,"data/boussole-electorale-v2.json"),"utf8"));
assert.match(source,/const FALLBACK_TIMEOUT_MS = 10000;/);
assert.match(source,/fetchJsonWithTimeout\(DATA_URL\)/);
for(const url of ["PARTY_DATA_URL","PARTY_SOURCE_DATA_URL","EVIDENCE_DATA_URL"]){
  assert.ok(source.includes("fetchJsonWithTimeout("+url+")"),"Repli documentaire borné : "+url);
}
const offsets=[],cleared=[],requests=[];
let id=0;
const context={
  AbortController,
  document:{addEventListener(){}},
  window:{},
  navigator:{},
  console,
  setTimeout(fn,ms){const n=++id;offsets.push({id:n,fn,ms});return n;},
  clearTimeout(n){cleared.push(n);},
  fetch:async(url,opts)=>{requests.push({url,opts});return {ok:true,json:async()=>({value:42})};}
};
context.globalThis=context;
// La boussole publique exige le même validateur d'intégrité que le sondage.
const integrity=fs.readFileSync(path.join(base,"assets/nova-civic-integrity.js"),"utf8");
vm.runInNewContext(integrity,context,{timeout:2500});
assert.equal(typeof context.window.__NOVA_CIVIC_INTEGRITY?.inspectCompass,"function");
const end=source.lastIndexOf("})();");
assert.ok(end>0);
vm.runInNewContext(source.slice(0,end)+";globalThis.__novaTest={fetchJsonWithTimeout,validateQuestionnaireCorpus};"+source.slice(end),
  context,{timeout:2500});
const {fetchJsonWithTimeout,validateQuestionnaireCorpus}=context.__novaTest;
assert.doesNotThrow(()=>validateQuestionnaireCorpus(corpus),"64 propositions et 16 dimensions valides");
const corrupted=()=>JSON.parse(JSON.stringify(corpus));
let x=corrupted();x.questions[1].id=x.questions[0].id;
assert.throws(()=>validateQuestionnaireCorpus(x),/dupliquée/,"Identifiants répétés interdits");
x=corrupted();x.questions[1].axis="inconnue";
assert.throws(()=>validateQuestionnaireCorpus(x),/sans dimension/,"Dimensions inconnues interdites");
x=corrupted();x.questions[1].axis=x.axes[1].id;
assert.throws(()=>validateQuestionnaireCorpus(x),/Répartition/,"Quatre propositions exactes par dimension");
x=corrupted();x.questions[0].text=" ";
assert.throws(()=>validateQuestionnaireCorpus(x),/Proposition invalide/,"Texte vide interdit");
x=corrupted();x.axes[1].id=x.axes[0].id;
assert.throws(()=>validateQuestionnaireCorpus(x),/Dimensions invalides/,"Dimensions répétées interdites");

(async()=>{
  const answer=await fetchJsonWithTimeout("/corpus");
  assert.equal(answer.value,42);
  assert.equal(requests.at(-1).opts.cache,"no-store");
  assert.equal(offsets.at(-1).ms,10000);
  assert.equal(cleared.at(-1),offsets.at(-1).id,"Nettoyage après succès");

  context.fetch=async(url,opts)=>{requests.push({url,opts});return {ok:false,status:404};};
  await assert.rejects(fetchJsonWithTimeout("/absent"),/HTTP 404/);
  assert.equal(cleared.at(-1),offsets.at(-1).id,"Nettoyage après erreur HTTP");

  context.fetch=(url,opts)=>{
    requests.push({url,opts});
    return new Promise((resolve,reject)=>{
      opts.signal.addEventListener("abort",()=>reject(new Error("abort")), {once:true});
    });
  };
  const pending=fetchJsonWithTimeout("/bloque");
  const wait=offsets.at(-1);
  assert.equal(wait.ms,10000);
  wait.fn();
  await assert.rejects(pending,/abort/);
  assert.equal(requests.at(-1).opts.signal.aborted,true,"La requête suspendue est annulée");
  assert.equal(cleared.at(-1),wait.id,"Nettoyage après expiration");
  console.log("OK NOVA : boussole 64/16 validée, repli JSON borné, absence réseau et reprise possibles.");
})().catch(error=>{console.error(error);process.exitCode=1;});
