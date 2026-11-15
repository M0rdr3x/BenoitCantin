#!/usr/bin/env node
"use strict";
// Exécuter le vrai gestionnaire GET dans une VM sans réseau ni vote.
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const src=fs.readFileSync(path.resolve(__dirname,"../projets/projet-nova/assets/sondage-citoyen.js"),"utf8");
const match=src.match(/  async function refreshResults\(\)\{[\s\S]*?\n  }\n(?=  function loadTurnstile\()/);
assert.ok(match,"Gestionnaire des résultats absent");

async function scenario({initialOpen,response,error,valid=true}){
  const statuses=[],rendered=[],buttons=[];
  const context={
    API:"https://example.invalid/consultation",
    fetchJson:async()=>{if(error)throw new Error("GET indisponible");return response;},
    validatedPublicResponse:()=>valid,
    renderResults:data=>rendered.push(data),
    setStatus:text=>statuses.push(text),
    updateButton:()=>buttons.push(true),
  };
  vm.runInNewContext(
    'let open='+JSON.stringify(initialOpen)+',captchaToken="jeton";\n'+
    match[0]+'\nglobalThis.testRefresh=refreshResults;\n'+
    'globalThis.testState=()=>({open,captchaToken});',context,{timeout:2000}
  );
  const result=await context.testRefresh();
  return {statuses,rendered,buttons,result,state:context.testState()};
}

(async()=>{
  let r=await scenario({initialOpen:true,error:true});
  assert.equal(r.result,null);
  assert.equal(r.state.open,false,"Une panne ferme la session de vote");
  assert.equal(r.state.captchaToken,"","Le jeton CAPTCHA doit être purgé");
  assert.match(r.statuses.at(-1),/indisponible/);
  assert.match(r.statuses.at(-1),/Aucun vote/);
  assert.equal(r.rendered.at(-1),null,"Les anciens chiffres doivent disparaître");
  assert.equal(r.buttons.length,1,"Le bouton est recalculé en état fermé");

  r=await scenario({initialOpen:true,response:{open:false}});
  assert.equal(r.state.open,false);
  assert.match(r.statuses.at(-1),/vient de fermer/);
  assert.equal(r.buttons.length,1);

  r=await scenario({initialOpen:false,response:{open:false}});
  assert.match(r.statuses.at(-1),/en préparation/);
  assert.equal(r.state.open,false);

  r=await scenario({initialOpen:false,response:{open:true}});
  assert.equal(r.state.open,false,"Un simple GET n'ouvre pas une session fermée");
  assert.match(r.statuses.at(-1),/session de vote reste fermée/);

  r=await scenario({initialOpen:true,response:{open:true}});
  assert.equal(r.state.open,true);
  assert.equal(r.statuses.length,0,"Aucune annonce fausse de fermeture");

  r=await scenario({initialOpen:true,response:{open:true},valid:false});
  assert.equal(r.state.open,false,"Un instantané malformé ferme la session");
  assert.match(r.statuses.at(-1),/données publiques incohérentes/);
  assert.equal(r.rendered.at(-1),null);

  console.log("OK NOVA : résultat GET, panne, lot invalide, fermeture serveur, absence de réouverture implicite ; aucun POST.");
})().catch(err=>{console.error(err);process.exitCode=1;});
