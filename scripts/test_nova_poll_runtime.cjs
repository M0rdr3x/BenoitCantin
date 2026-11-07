#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const assert=require("node:assert/strict");
const src=fs.readFileSync(path.join(__dirname,"../projets/projet-nova/assets/sondage-citoyen.js"),"utf8");
const html=fs.readFileSync(path.join(__dirname,"../projets/projet-nova/sondage-citoyen.html"),"utf8");
assert.match(html,/<button[^>]+id="poll-send"[^>]*\bdisabled\b/);
const elements=new Map();
const pollRadios=[{disabled:false},{disabled:false}];
const elem=id=>{if(!elements.has(id))elements.set(id,{
  disabled:false,checked:false,textContent:"",querySelectorAll:()=>pollRadios,replaceChildren:()=>{}
});return elements.get(id);};
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
// Le navigateur charge la validation partagée avant le gestionnaire de sondage.
const integrity=fs.readFileSync(path.join(__dirname,"../projets/projet-nova/assets/nova-civic-integrity.js"),"utf8");
vm.runInNewContext(integrity,context,{timeout:2000});
assert.equal(typeof context.window.__NOVA_CIVIC_INTEGRITY?.inspectPoll,"function");
const end=src.lastIndexOf("})();");
assert.ok(end>0);
vm.runInNewContext(src.slice(0,end)+';globalThis.__pollTest={updateButton,setOpen:v=>open=v,setCaptcha:v=>captchaToken=v,setSending:v=>sending=v,setQuestions:v=>questions=v,setLocal:v=>localCorpus=v,validatedPublicResponse,validLocalCorpus,loadPoll};'+src.slice(end),context,{timeout:2000});
const t=context.__pollTest;
elem("poll-adult").checked=true;elem("poll-agree").checked=true;
const corpus=JSON.parse(fs.readFileSync(path.join(__dirname,"../projets/projet-nova/data/sondage-citoyen-v1.json"),"utf8"));
t.setQuestions(corpus.questions);
for(const question of corpus.questions)selected.add(question.id);
t.setCaptcha("jeton-de-test");t.setOpen(false);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Consultation fermée");
assert.ok(pollRadios.every(input=>input.disabled),"Choix verrouillés dès la fermeture");
t.setOpen(true);t.updateButton();
assert.equal(elem("poll-send").disabled,false,"Huit questions répondues, ouvert et consentement complet");
assert.match(elem("poll-answer-progress").textContent,/8 sur 8/,"Compteur de huit questions");
assert.ok(pollRadios.every(input=>!input.disabled),"Choix utilisables uniquement si ouvert");
selected.clear();t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Aucune réponse");
selected.add("q02");t.setCaptcha("");t.updateButton();
assert.equal(elem("poll-send").disabled,true,"CAPTCHA absent");
t.setCaptcha("jeton-de-test");elem("poll-adult").checked=false;t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Âge non confirmé");
elem("poll-adult").checked=true;
for(const question of corpus.questions)selected.add(question.id);
elem("poll-agree").checked=false;t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Consentement politique non confirmé");
elem("poll-agree").checked=true;t.updateButton();
assert.equal(elem("poll-send").disabled,false,"Deux confirmations indépendantes exigées");
voted=true;t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Déjà participé");
assert.ok(pollRadios.every(input=>input.disabled),"Choix verrouillés après participation");
voted=false;t.setSending(true);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Envoi en cours");
assert.ok(pollRadios.every(input=>input.disabled),"Choix verrouillés pendant envoi");
t.setSending(false);t.setOpen(false);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Retour en mode fermé");
assert.ok(pollRadios.every(input=>input.disabled),"Les choix déjà rendus sont aussi verrouillés");
assert.equal(t.validLocalCorpus(corpus),true,"Corpus officiel de huit questions valide");
const clone=()=>JSON.parse(JSON.stringify(corpus));
assert.equal(t.validLocalCorpus(null),false);
assert.equal(t.validLocalCorpus({questions:{}}),false,"Structure défectueuse refusée");
assert.equal(t.validLocalCorpus([]),false);
let corrupt=clone();corrupt.questions=corrupt.questions.slice(0,7);
assert.equal(t.validLocalCorpus(corrupt),false,"Questionnaire tronqué refusé");
corrupt=clone();corrupt.questions[1].id=corrupt.questions[0].id;
assert.equal(t.validLocalCorpus(corrupt),false,"Id de question répété refusé");
corrupt=clone();corrupt.questions[2].ordinal=10;
assert.equal(t.validLocalCorpus(corrupt),false,"Ordre des questions altéré refusé");
corrupt=clone();corrupt.questions[0].text=" ";
assert.equal(t.validLocalCorpus(corrupt),false,"Texte de question vide refusé");
corrupt=clone();corrupt.options[0].value=99;
assert.equal(t.validLocalCorpus(corrupt),false,"Catégorie de réponse différente refusée");
corrupt=clone();corrupt.options[0].label="Position remplacée";
assert.equal(t.validLocalCorpus(corrupt),false,"Libellé de réponse modifié refusé");
corrupt=clone();corrupt.published="true";
assert.equal(t.validLocalCorpus(corrupt),false,"Activation non booléenne refusée");
corrupt=clone();corrupt.version="autre-version";
assert.equal(t.validLocalCorpus(corrupt),false,"Version incompatible refusée");
corrupt=clone();corrupt.format="sondage_representatif";
assert.equal(t.validLocalCorpus(corrupt),false,"Format politique différent refusé");
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
assert.equal(t.validatedPublicResponse({...publication,publishedAt:null}),false,
  "Une publication sans date doit être rejetée");
assert.equal(t.validatedPublicResponse({...publication,publishedAt:"date-invalide"}),false,
  "Une date de publication invalide ne doit pas être affichée");
// Le navigateur refuse aussi les petites catégories même si le total
// global d'une question est correct.
const change=row=>({...publication,questions:publicQuestions.map((q,i)=>i===3
  ? {...q,counts:row}:q)});
assert.equal(t.validatedPublicResponse(change({"-2":9,"-1":1,"0":0,"1":0,"2":0,"9":0})),false,
  "Une seule réponse dans une catégorie doit masquer tous les chiffres");
assert.equal(t.validatedPublicResponse(change({"-2":6,"-1":4,"0":0,"1":0,"2":0,"9":0})),false,
  "Une catégorie de quatre réponses doit rester privée");
assert.equal(t.validatedPublicResponse(change({"-2":5,"-1":5,"0":0,"1":0,"2":0,"9":0})),true,
  "Deux catégories de cinq réponses peuvent être affichées");

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


// Cas d'intégration : le chargement d'un corpus invalide doit verrouiller
// l'envoi, afficher une erreur claire et n'effectuer aucun GET ni POST.
(async()=>{
  let networkCalls=0;
  context.fetch=()=>{networkCalls++;throw new Error("Une source corrompue n'autorise pas de requête réseau");};
  context.window.__NOVA_POLL_PUBLIC_CORPUS={questions:"corrompues",published:true};
  await t.loadPoll();
  assert.equal(networkCalls,0,"Corpus invalide : aucun accès API");
  assert.match(elem("poll-live-status").textContent,/incomplet/);
  assert.equal(elem("poll-send").disabled,true,"Corpus invalide : envoi verrouillé");
  assert.match(elem("poll-results-status").textContent,/pas disponibles/);
  assert.match(elem("poll-questions").textContent,/indisponible/);
  console.log("OK sondage : corpus public tronqué/doublé refuse toute collecte et affiche un état clair.");
})().catch(error=>{console.error(error);process.exitCode=1;});
