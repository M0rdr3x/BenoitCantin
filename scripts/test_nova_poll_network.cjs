#!/usr/bin/env node
"use strict";
// Exécute la vraie primitive HTTP du sondage avec un réseau simulé.
// Aucun appel externe et aucune collecte de vote.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const src=fs.readFileSync(path.resolve(__dirname,"../projets/projet-nova/assets/sondage-citoyen.js"),"utf8");
const match=src.match(/  async function boundedFetch\(url,opts=\{\}\) \{[\s\S]*?\n  \}/);
assert.ok(match,"Protection des délais HTTP manquante");
assert.match(src,/const REQUEST_TIMEOUT_MS = 10000;/,"Délai maximum explicite requis");
assert.match(src,/const response=await boundedFetch\(url,\{cache:"no-store",\.\.\.opts\}\)/,
  "Les lectures GET doivent utiliser une requête bornée");
assert.match(src,/const response=await boundedFetch\(API,\{\s*method:"POST"/,
  "Les écritures POST doivent également être bornées");

const timeouts=[],cleared=[],requests=[];
let nextId=0;
const context={
  AbortController,
  setTimeout(fn,ms){ const id=++nextId; timeouts.push({id,fn,ms});return id; },
  clearTimeout(id){cleared.push(id);},
  fetch:async(url,opts)=>{requests.push({url,opts});return {ok:true,status:200};}
};
context.globalThis=context;
vm.runInNewContext("const REQUEST_TIMEOUT_MS=10000;\n"+match[0]+"\nglobalThis.testFetch=boundedFetch;",context,{timeout:2000});

(async()=>{
  const response=await context.testFetch("/resultats",{method:"GET"});
  assert.equal(response.status,200);
  assert.equal(requests.length,1);
  assert.equal(requests[0].opts.method,"GET");
  assert.equal(requests[0].opts.signal.aborted,false);
  assert.equal(timeouts[0].ms,10000);
  assert.deepEqual(cleared,[timeouts[0].id],"Délai libéré après le succès");

  context.fetch=(url,opts)=>{
    requests.push({url,opts});
    return new Promise((resolve,reject)=>{
      opts.signal.addEventListener("abort",()=>reject(new Error("aborted")), {once:true});
    });
  };
  const pending=context.testFetch("/soumission",{method:"POST"});
  assert.equal(requests.at(-1).opts.method,"POST");
  assert.equal(timeouts.at(-1).ms,10000);
  timeouts.at(-1).fn();
  await assert.rejects(pending,/aborted/,"Une connexion bloquée doit être interrompue");
  assert.equal(requests.at(-1).opts.signal.aborted,true);
  assert.deepEqual(cleared,[timeouts[0].id,timeouts[1].id],
    "Délai libéré après interruption");
  console.log("OK NOVA : délais GET/POST bornés, annulation des requêtes suspendues et nettoyage des temporisateurs.");
})().catch(err=>{console.error(err);process.exitCode=1;});
