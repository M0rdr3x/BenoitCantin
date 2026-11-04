#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const assert=require("node:assert/strict");
const src=fs.readFileSync(path.join(__dirname,"../projets/projet-nova/assets/sondage-citoyen.js"),"utf8");
const html=fs.readFileSync(path.join(__dirname,"../projets/projet-nova/sondage-citoyen.html"),"utf8");
assert.match(html,/<button[^>]+id="poll-send"[^>]*\bdisabled\b/);
const elements=new Map();
const elem=id=>{if(!elements.has(id))elements.set(id,{disabled:false,checked:false,textContent:""});return elements.get(id);};
const selected=new Set();
let voted=false;
const context={
  document:{getElementById:elem,querySelector:selector=>{
    const m=selector.match(/input\[name="([^"]+)"\]:checked/);
    return m&&selected.has(m[1])?{value:"0"}:null;
  },addEventListener:()=>{}},
  localStorage:{getItem:key=>key==="nova_poll_sent_v1"&&voted?"yes":null,setItem:()=>{}},
  window:{},crypto:{getRandomValues:()=>{throw new Error("pas de jeton en test");}},console
};
context.globalThis=context;
const end=src.lastIndexOf("})();");
assert.ok(end>0);
vm.runInNewContext(src.slice(0,end)+';globalThis.__pollTest={updateButton,setOpen:v=>open=v,setCaptcha:v=>captchaToken=v,setSending:v=>sending=v,setQuestions:v=>questions=v,setLocal:v=>localCorpus=v,validatedPublicResponse};'+src.slice(end),context,{timeout:2000});
const t=context.__pollTest;
elem("poll-adult").checked=true;elem("poll-agree").checked=true;
t.setQuestions([{id:"q02"}]);selected.add("q02");
t.setCaptcha("jeton-de-test");t.setOpen(false);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Consultation fermée");
t.setOpen(true);t.updateButton();
assert.equal(elem("poll-send").disabled,false,"Ouvert et consentement complet");
selected.clear();t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Aucune réponse");
selected.add("q02");t.setCaptcha("");t.updateButton();
assert.equal(elem("poll-send").disabled,true,"CAPTCHA absent");
t.setCaptcha("jeton-de-test");elem("poll-adult").checked=false;t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Âge non confirmé");
elem("poll-adult").checked=true;voted=true;t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Déjà participé");
voted=false;t.setSending(true);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Envoi en cours");
t.setSending(false);t.setOpen(false);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Retour en mode fermé");
const corpus=JSON.parse(fs.readFileSync(path.join(__dirname,"../projets/projet-nova/data/sondage-citoyen-v1.json"),"utf8"));
t.setQuestions(corpus.questions);t.setLocal(corpus);
const baseQuestions=corpus.questions.map(q=>({id:q.id,ordinal:q.ordinal,text:q.text,counts:null}));
const hidden={version:corpus.version,open:false,siteKey:null,minPublicBallots:10,
  questions:baseQuestions,resultsVisible:false,ballots:null,publishedAt:null};
assert.equal(t.validatedPublicResponse(hidden),true,"Réponse fermée valide");
assert.equal(t.validatedPublicResponse({...hidden,open:true}),false,"Ouverture contradictoire refusée");
assert.equal(t.validatedPublicResponse({...hidden,version:"mauvaise-version"}),false);
assert.equal(t.validatedPublicResponse({...hidden,ballots:1}),false,"Petits effectifs masqués");
assert.equal(t.validatedPublicResponse({...hidden,questions:baseQuestions.map((q,i)=>i? q:{...q,counts:{"2":1}})}),false);
assert.equal(t.validatedPublicResponse({...hidden,questions:baseQuestions.slice(1)}),false);
const acceptedCounts=Object.fromEntries([-2,-1,0,1,2,9].map(v=>[String(v),v===9?10:0]));
const publicQuestions=baseQuestions.map(q=>({...q,counts:{...acceptedCounts}}));
const publication={...hidden,resultsVisible:true,ballots:10,publishedAt:"2026-11-03T20:00:00Z",
  questions:publicQuestions};
assert.equal(t.validatedPublicResponse(publication),true,"Lot de 10 bulletins cohérent");
const tamper=(make)=>({...publication,questions:publicQuestions.map((q,i)=>i? q:{...q,counts:make({...q.counts})})});
assert.equal(t.validatedPublicResponse({...publication,ballots:20}),false,"Transition de lots incohérente");
assert.equal(t.validatedPublicResponse(tamper(c=>({...c,"9":9}))),false,"Total incorrect");
assert.equal(t.validatedPublicResponse(tamper(c=>({...c,"9":-1}))),false,"Nombre négatif");
assert.equal(t.validatedPublicResponse(tamper(c=>({...c,"9":Number.POSITIVE_INFINITY}))),false,"Nombre infini");
assert.equal(t.validatedPublicResponse(tamper(c=>({...c,"9":1.5}))),false,"Nombre fractionnaire");
assert.equal(t.validatedPublicResponse(tamper(c=>({...c,"99":1}))),false,"Catégorie inconnue");
assert.equal(t.validatedPublicResponse(tamper(c=>({...c,"9":"10"}))),false,"Nombre sous forme de texte");
console.log("OK sondage : serveur et navigateur concordants, aucun petit effectif, aucun pourcentage issu de données invalides.");
console.log("OK sondage : désactivé hors ouverture, âge, anti-robot, choix et doublon.");
