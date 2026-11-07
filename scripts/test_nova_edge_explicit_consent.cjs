#!/usr/bin/env node
"use strict";
// Vérifie le vrai validateur d'entrée Edge sans API, secret ni vote réel.
// Le consentement politique et l'âge déclaré sont deux conditions distinctes.
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const assert=require("node:assert/strict");
const root=path.resolve(__dirname,"..");
const edge=fs.readFileSync(path.join(root,"supabase/functions/nova-civic-poll/index.ts"),"utf8");
const client=fs.readFileSync(path.join(root,"projets/projet-nova/assets/sondage-citoyen.js"),"utf8");
const html=fs.readFileSync(path.join(root,"projets/projet-nova/sondage-citoyen.html"),"utf8");
const match=edge.match(/function validBallotEnvelope\(payload: unknown\): boolean \{[\s\S]*?\n\}\n(?=async function confirmCaptcha)/);
assert.ok(match,"Le validateur serveur de consentement est absent");
let js=match[0]
  .replace("payload: unknown","payload")
  .replace("const ballot=payload as Record<string,unknown>;","const ballot=payload;")
  .replace("const answers=ballot.answers as Record<string,unknown>;","const answers=ballot.answers;");
assert.ok(!js.includes(" as Record<"),"TypeScript de test non transformé");
const context={};
vm.runInNewContext(
  'const VERSION="nova-consultation-v1";const OPTIONS=new Set([-2,-1,0,1,2,9]);\n'+
  js+"\nglobalThis.validate=validBallotEnvelope;",context,{timeout:2000});
const validate=context.validate;
const qids=["q02","q09","q17","q22","q29","q33","q47","q61"];
const make=()=>({
  version:"nova-consultation-v1",ageConfirmed:true,consentConfirmed:true,
  ballotToken:"f".repeat(48),captchaToken:"captcha-fictif",
  answers:Object.fromEntries(qids.map(id=>[id,9]))
});
assert.equal(validate(make()),true,"Tous les consentements explicites valides");
for(const status of [false,undefined,null,"true",1,0,"",{}]){
  const copy=make();
  if(status===undefined)delete copy.consentConfirmed;
  else copy.consentConfirmed=status;
  assert.equal(validate(copy),false,"La confirmation du consentement doit être le booléen true");
}
for(const status of [false,undefined,null,"true",1]){
  const copy=make();
  if(status===undefined)delete copy.ageConfirmed;
  else copy.ageConfirmed=status;
  assert.equal(validate(copy),false,"Age autodéclaré vrai requis, indépendamment du consentement");
}
const mutations=[
  null,[],{},false,
  {...make(),version:"ancienne"},
  {...make(),ballotToken:"a"},
  {...make(),ballotToken:"z".repeat(48)},
  {...make(),captchaToken:"trop-court"},
  {...make(),captchaToken:"x".repeat(4097)},
  {...make(),answers:{}},
  {...make(),answers:null},
  {...make(),answers:[]},
  {...make(),answers:Object.fromEntries(qids.slice(0,7).map(id=>[id,9]))},
  {...make(),answers:Object.fromEntries(qids.map(id=>[id,"9"]))},
  {...make(),answers:{...make().answers,q02:7}},
  {...make(),answers:{...make().answers,q02:NaN}}
];
for(const payload of mutations)assert.equal(validate(payload),false,
  "Aucun bulletin invalide ne doit parvenir au CAPTCHA ou au RPC");

assert.match(html,/id="poll-adult"[^>]*type="checkbox"/,"Case d'âge distincte");
assert.match(html,/id="poll-agree"[^>]*type="checkbox"/,"Case de consentement distincte");
assert.match(html,/Je consens expressément/,"Texte explicite du consentement");
assert.match(client,/!\$\("poll-adult"\)\.checked \|\| !\$\("poll-agree"\)\.checked/,
  "Le navigateur refuse un envoi sans âge et consentement");
assert.match(client,/ageConfirmed:true,consentConfirmed:true,ballotToken:randomToken\(\)/,
  "Les deux déclarations doivent être transmises dans l'enveloppe POST");

const post=edge.slice(edge.indexOf('if(req.method!=="POST")'));
const validation=post.indexOf("if(!validBallotEnvelope(payload))");
const captcha=post.indexOf("if(!await confirmCaptcha(payload.captchaToken))");
const sql=post.indexOf('db("rpc/nova_poll_submit"');
assert.ok(validation>=0 && captcha>validation && sql>captcha,
  "Refuser un consentement absent avant CAPTCHA et tout accès privilégié SQL");
assert.match(edge,/NOVA_POLL_APPROVED_VERSION/,"Verrou éditorial serveur conservé");
assert.match(edge,/matchesApprovedQuestions\(questions\)/,
  "Vérification du questionnaire canonique conservée");
console.log("OK NOVA: 2 déclarations indépendantes et 29+ mutations refusées avant CAPTCHA/RPC, aucune donnée politique transmise.");
