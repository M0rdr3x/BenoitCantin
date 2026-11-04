#!/usr/bin/env node
"use strict";
// Test du véritable gestionnaire de chargement NOVA, sans HTTP ni vote.
// Vérifie qu'un premier GET transitoire 503 ne laisse pas un faux état d'erreur.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const src=fs.readFileSync(path.resolve(__dirname,
  "../projets/projet-nova/assets/sondage-citoyen.js"),"utf8");
const match=src.match(/  async function loadPoll\(\)\{[\s\S]*?\n  }\n(?=  async function submit\()/);
assert.ok(match,"Handler de chargement de l'interface introuvable");
const corpus=JSON.parse(fs.readFileSync(path.resolve(__dirname,
  "../projets/projet-nova/data/sondage-citoyen-v1.json"),"utf8"));
assert.equal(corpus.published,false,"Le sondage public n'est pas approuvé");
const sample={version:corpus.version,open:false,siteKey:null,resultsVisible:false,
  ballots:null,publishedAt:null,questions:corpus.questions};

async function verify(mode,remote=sample){
  const statuses=[];
  let firstCalls=0,retries=0,forms=0,robots=0;
  const ctx={
    window:{__NOVA_POLL_PUBLIC_CORPUS:corpus},
    fetchJson:async()=>{firstCalls++;if(mode==="ok")return remote;
      throw new Error(mode==="invalid"?"public_snapshot_invalid":"HTTP 503");},
    validatedPublicResponse:()=>mode!=="invalid",
    refreshResults:async()=>{retries++;return mode==="down"?null:remote;},
    setStatus:x=>statuses.push(x),
    renderResults:()=>{},
    renderForm:()=>forms++,
    loadTurnstile:()=>robots++
  };
  vm.runInNewContext(
    'let open=false,questions=[],localCorpus=null,siteKey="";\n'+match[0]+
    '\nglobalThis.__load=loadPoll;\nglobalThis.__state=()=>({open,siteKey,questions});',
    ctx,{timeout:2000}
  );
  await ctx.__load();
  return {status:statuses.at(-1),firstCalls,retries,forms,robots,state:ctx.__state()};
}
(async()=>{
  let result=await verify("ok");
  assert.match(result.status,/consultation est en préparation/);
  assert.equal(result.retries,0);
  assert.equal(result.state.open,false);
  result=await verify("transient");
  assert.match(result.status,/consultation est en préparation/);
  assert.equal(result.firstCalls,1);
  assert.equal(result.retries,1);
  assert.equal(result.forms,1);
  assert.equal(result.robots,0);
  assert.equal(result.state.open,false);
  result=await verify("down");
  assert.match(result.status,/service de vote indisponible/);
  assert.equal(result.state.open,false);
  assert.equal(result.retries,1);
  result=await verify("transient",{...sample,open:true,siteKey:"cle-exemple"});
  assert.match(result.status,/consultation est en préparation/);
  assert.equal(result.state.open,false,"Ne pas ouvrir sur un corpus provisoire");
  assert.equal(result.robots,0,"Aucun CAPTCHA de vote lorsque fermé");
  console.log("OK NOVA : succès initial, 503 puis rétablissement, panne durable, ouverture impossible sur corpus provisoire.");
})().catch(error=>{console.error(error);process.exitCode=1;});
