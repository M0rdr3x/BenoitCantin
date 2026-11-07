#!/usr/bin/env node
"use strict";
// Exécute la vraie primitive de requête JSON du sondage avec un réseau simulé.
// Aucun appel externe et aucun bulletin réel.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const src=fs.readFileSync(path.resolve(__dirname,"../projets/projet-nova/assets/sondage-citoyen.js"),"utf8");
const match=src.match(/  async function boundedJsonRequest\(url,opts=\{\}\) \{[\s\S]*?\n  \}/);
assert.ok(match,"Protection complète des délais HTTP/JSON manquante");
assert.match(src,/const REQUEST_TIMEOUT_MS = 10000;/,"Délai maximum explicite requis");
assert.match(src,/const \{response,result\}=await boundedJsonRequest\(url,\{cache:"no-store",\.\.\.opts\}\)/,
  "Les lectures GET doivent conserver le délai pendant le décodage JSON");
assert.match(src,/const \{response,result\}=await boundedJsonRequest\(API,\{\s*method:"POST"/,
  "Les écritures POST doivent conserver le délai pendant le décodage JSON");
assert.match(src,/ballotToken:randomToken\(\)/,
  "Le POST doit conserver son jeton anti-rejeu stable pour les nouvelles tentatives");

const timeouts=[],cleared=[],requests=[];
let nextId=0;
const context={
  AbortController,
  setTimeout(fn,ms){const id=++nextId;timeouts.push({id,fn,ms});return id;},
  clearTimeout(id){cleared.push(id);},
  fetch:async(url,opts)=>{requests.push({url,opts});return {ok:true,status:200,json:async()=>({status:"ok"})};}
};
context.globalThis=context;
vm.runInNewContext("const REQUEST_TIMEOUT_MS=10000;\n"+match[0]+
  "\nglobalThis.testRequest=boundedJsonRequest;",context,{timeout:2000});

(async()=>{
  // Succès GET : le résultat JSON est décodé avant de libérer le délai.
  const get=await context.testRequest("/resultats",{method:"GET"});
  assert.equal(get.response.status,200);
  assert.equal(get.result.status,"ok");
  assert.equal(requests[0].opts.method,"GET");
  assert.equal(requests[0].opts.signal.aborted,false);
  assert.equal(timeouts[0].ms,10000);
  assert.deepEqual(cleared,[timeouts[0].id],"Délai libéré après décodage GET");

  // Succès POST : même contrat pour la confirmation d'un bulletin.
  const post=await context.testRequest("/soumission",{method:"POST"});
  assert.equal(post.response.status,200);
  assert.equal(post.result.status,"ok");
  assert.equal(requests.at(-1).opts.method,"POST");
  assert.equal(cleared.at(-1),timeouts.at(-1).id,"Délai libéré après décodage POST");

  // Réponse HTTP 404 : l'appelant conserve le statut et le JSON d'erreur.
  context.fetch=async(url,opts)=>{
    requests.push({url,opts});
    return {ok:false,status:404,json:async()=>({error:"not_found"})};
  };
  const invalid=await context.testRequest("/absent",{method:"GET"});
  assert.equal(invalid.response.status,404);
  assert.equal(invalid.result.error,"not_found");
  assert.equal(cleared.at(-1),timeouts.at(-1).id,"Délai libéré après réponse HTTP d'erreur");

  // Le corps JSON peut se figer APRÈS un HTTP 200 : ce cas était non couvert.
  for(const method of ["GET","POST"]){
    context.fetch=async(url,opts)=>{
      requests.push({url,opts});
      return {ok:true,status:200,json:()=>new Promise((resolve,reject)=>{
        opts.signal.addEventListener("abort",()=>reject(new Error("aborted-body")), {once:true});
      })};
    };
    const pending=context.testRequest("/corps-bloque",{method});
    await Promise.resolve();
    await Promise.resolve();
    const timer=timeouts.at(-1);
    assert.equal(timer.ms,10000);
    assert.equal(cleared.includes(timer.id),false,"Le délai ne doit pas être libéré aux en-têtes");
    timer.fn();
    await assert.rejects(pending,/aborted-body/,
      method+": une lecture du corps suspendue doit être annulée");
    assert.equal(requests.at(-1).opts.signal.aborted,true);
    assert.equal(cleared.at(-1),timer.id);
  }

  // Le serveur peut ne jamais transmettre les en-têtes : borné également.
  context.fetch=(url,opts)=>{
    requests.push({url,opts});
    return new Promise((resolve,reject)=>{
      opts.signal.addEventListener("abort",()=>reject(new Error("aborted-headers")), {once:true});
    });
  };
  const pending=context.testRequest("/en-tetes-bloques",{method:"POST"});
  const last=timeouts.at(-1);
  last.fn();
  await assert.rejects(pending,/aborted-headers/);
  assert.equal(cleared.at(-1),last.id);

  // Une erreur de décodage nettoie aussi le temporisateur.
  context.fetch=async(url,opts)=>{
    requests.push({url,opts});
    return {ok:true,status:200,json:async()=>{throw new SyntaxError("JSON invalide");}};
  };
  await assert.rejects(context.testRequest("/json-invalide"),/JSON invalide/);
  assert.equal(cleared.at(-1),timeouts.at(-1).id);
  assert.equal(cleared.length,timeouts.length,"Aucun délai résiduel après les tests");

  console.log("OK NOVA : GET et POST bornés jusqu'au JSON, corps suspendus annulés, erreurs nettoyées, aucun vote.");
})().catch(error=>{console.error(error);process.exitCode=1;});
