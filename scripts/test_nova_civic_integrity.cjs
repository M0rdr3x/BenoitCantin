#!/usr/bin/env node
"use strict";
// Exercer le véritable validateur public partagé (aucun réseau, aucun vote).
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const nova=path.resolve(__dirname,"../projets/projet-nova");
const script=fs.readFileSync(path.join(nova,"assets/nova-civic-integrity.js"),"utf8");
const poll=JSON.parse(fs.readFileSync(path.join(nova,"data/sondage-citoyen-v1.json"),"utf8"));
const compass=JSON.parse(fs.readFileSync(path.join(nova,"data/boussole-electorale-v2.json"),"utf8"));
const context={window:{}};
vm.runInNewContext(script,context,{timeout:3000});
const integrity=context.window.__NOVA_CIVIC_INTEGRITY;
assert.equal(typeof integrity.inspectPoll,"function");
assert.equal(typeof integrity.inspectCompass,"function");
assert.equal(typeof integrity.inspectPollCompassBinding,"function");
assert.equal(integrity.inspectPoll(poll).ok,true,"Huit questions publiques valides");
assert.equal(integrity.inspectCompass(compass).ok,true,"Boussole 64/16 et neutralité valides");
assert.equal(integrity.inspectPollCompassBinding(poll,compass).ok,true,
  "Le sondage officiel provient exactement des huit propositions du corpus de la boussole");
const clone=obj=>JSON.parse(JSON.stringify(obj));
const reject=(fn,modified,reason)=>assert.equal(fn(modified).ok,false,reason);
let p=clone(poll);p.questions[0].text+=" (question altérée)";
assert.equal(integrity.inspectPoll(p).ok,false,"Le texte d'une proposition est lié au corpus canonique");
reject(v=>integrity.inspectPollCompassBinding(v,compass),p,
  "La comparaison canonique doit refuser une question politiquement modifiée");
p=clone(poll);p.questions[0].axis="tax";
reject(v=>integrity.inspectPollCompassBinding(v,compass),p,
  "Les axes d'une proposition ne peuvent être modifiés");
p=clone(poll);p.questions[1].id=p.questions[0].id;
reject(integrity.inspectPoll,p,"Identifiants répétés");
p=clone(poll);p.options[5].label="Sans réponse masquée";
reject(integrity.inspectPoll,p,"Les six réponses sont canoniques");
p=clone(poll);p.published="true";
reject(integrity.inspectPoll,p,"Pas d'activation par chaîne de caractères");
let c=clone(compass);c.questions[0].direction=-c.questions[0].direction;
reject(integrity.inspectCompass,c,"Pôle inversé sans mise à jour du chargement");
c=clone(compass);c.questions[0].quality.neutralTone=false;
reject(integrity.inspectCompass,c,"Question de qualité non revue");
c=clone(compass);c.questions[0].text="";
reject(integrity.inspectCompass,c,"Question vide");
c=clone(compass);c.questions[0].loadings[0].weight=2;
reject(integrity.inspectCompass,c,"Poids de chargement altéré");
c=clone(compass);c.partyComparison.enabled=true;
reject(integrity.inspectCompass,c,"Comparaison de parti non approuvée");
// La formule utilise exclusivement les réponses locales; les scores n'existent
// qu'avec au moins deux réponses principales sur chaque dimension.
assert.equal(typeof integrity.scoreCompass,"function","Calcul officiel indépendant de l'interface");
const emptyScores=integrity.scoreCompass(compass,new Map());
assert.equal(emptyScores.length,16);
assert.ok(emptyScores.every(axis=>axis.score===null&&axis.answered===0));
const primary=compass.questions.filter(q=>q.axis===compass.axes[0].id);
const one=new Map([[primary[0].id,{value:3,importance:"normal"}]]);
assert.equal(integrity.scoreCompass(compass,one)[0].score,null,"Une seule réponse ne crée pas de score");
one.set(primary[1].id,{value:-3,importance:"forte"});
assert.equal(integrity.scoreCompass(compass,one)[0].answered,2,"Seuil d'au moins deux réponses atteint");
assert.notEqual(integrity.scoreCompass(compass,one)[0].score,null);
const neutral=new Map(compass.questions.map(q=>[q.id,{value:0,importance:"normal"}]));
assert.ok(integrity.scoreCompass(compass,neutral).every(axis=>
  axis.score===0&&axis.answered===4&&axis.coverage===100),"Seize axes neutres réellement calculables");
assert.throws(()=>integrity.scoreCompass(compass,new Map([["q99",{value:3,importance:"normal"}]])),
  /INVALID_ANSWER/,"Ne jamais calculer une question inconnue");
assert.throws(()=>integrity.scoreCompass(compass,new Map([[primary[0].id,{value:4,importance:"normal"}]])),
  /INVALID_ANSWER/,"Ne jamais accepter des réponses hors échelle");
assert.throws(()=>integrity.scoreCompass(compass,new Map([[primary[0].id,{value:3,importance:"inconnue"}]])),
  /INVALID_ANSWER/,"Importance hors barème refusée");
const html=fs.readFileSync(path.join(nova,"sondage-citoyen.html"),"utf8");
const corpusIndex=html.indexOf("assets/sondage-public-corpus.js?v=1");
const integrityIndex=html.indexOf("assets/nova-civic-integrity.js?v=2");
const appIndex=html.indexOf("assets/sondage-citoyen.js?v=12");
assert.ok(corpusIndex>=0 && corpusIndex<integrityIndex && integrityIndex<appIndex,
  "La validation partagée doit être chargée avant le code qui l'utilise");
console.log("OK NOVA : intégrité canonique 64/16 et 8 questions, neutralité, 10 scénarios de corruption, ordre des scripts.");
