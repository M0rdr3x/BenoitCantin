import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {runInNewContext} from "node:vm";

const [code,questionnaire,poll,boussoleScript]=await Promise.all([
  readFile(new URL("../assets/nova-civic-integrity.js",import.meta.url),"utf8"),
  readFile(new URL("../data/boussole-electorale-v2.json",import.meta.url),"utf8").then(JSON.parse),
  readFile(new URL("../data/sondage-citoyen-v1.json",import.meta.url),"utf8").then(JSON.parse),
  readFile(new URL("../assets/boussole-electorale.js",import.meta.url),"utf8")
]);
const w={window:{}};
runInNewContext(code,w,{timeout:1500});
const {scoreCompass,inspectPoll}=w.window.__NOVA_CIVIC_INTEGRITY;
const a=(pairs)=>new Map(pairs.map(([id,value,importance="normal"])=>[id,{value,importance}]));
const axis=(answers,id="economy")=>scoreCompass(questionnaire,answers).find(x=>x.id===id);

test("moteur sans appels réseau ni persistance de réponses",()=>{
 assert.match(code,/function scoreCompass\(/);
 assert.doesNotMatch(code,/\bfetch\s*\(/);
 assert.doesNotMatch(code,/localStorage|sessionStorage/);
});
test("les 16 axes sans réponse demeurent inconnus",()=>{
 const out=scoreCompass(questionnaire,new Map());
 assert.equal(out.length,16);
 assert.ok(out.every(x=>x.score===null&&x.coverage===0&&x.answered===0));
});
test("64 questions volontairement passées : aucun score artificiel",()=>{
 const answers=a(questionnaire.questions.map(q=>[q.id,null]));
 const out=scoreCompass(questionnaire,answers);
 assert.ok(out.every(x=>x.score===null&&x.coverage===0&&x.answered===0));
});
test("une seule réponse principale ne suffit pas à un score",()=>{
 const result=axis(a([["q01",3]]));
 assert.equal(result.score,null);
 assert.equal(result.answered,1);
 assert.equal(result.total,4);
 assert.equal(result.coverage,25);
});
test("deux réponses orientées positivement : score +100",()=>{
 const result=axis(a([["q01",3],["q02",-3]]));
 assert.equal(result.score,100);
 assert.equal(result.answered,2);
 assert.equal(result.coverage,50);
});
test("deux réponses orientées négativement : score -100",()=>{
 const result=axis(a([["q01",-3],["q02",3]]));
 assert.equal(result.score,-100);
});
test("deux réponses qui s'annulent : score zéro",()=>{
 const result=axis(a([["q01",3],["q02",3]]));
 assert.equal(result.score,0);
});
test("la pondération utilisateur forte est prise en compte",()=>{
 const result=axis(a([["q01",3,"forte"],["q02",3,"faible"]]));
 assert.equal(result.score,50);
});
test("neutralité n'est pas l'absence d'une réponse",()=>{
 const result=axis(a([["q01",0],["q02",0]]));
 assert.equal(result.score,0);
 assert.equal(result.answered,2);
});
test("sans opinion est distinct de neutralité et n'augmente pas la couverture",()=>{
 const result=axis(a([["q01",null],["q02",0]]));
 assert.equal(result.score,null);
 assert.equal(result.answered,1);
 assert.equal(result.coverage,25);
});
test("toutes les réponses neutres calculent 16 scores zéro, pas null",()=>{
 const answers=a(questionnaire.questions.map(q=>[q.id,0]));
 const results=scoreCompass(questionnaire,answers);
 assert.ok(results.every(x=>x.score===0&&x.answered===4&&x.coverage===100));
});
test("64 réponses dirigées vers les pôles positifs restent dans [-100,100]",()=>{
 const answers=a(questionnaire.questions.map(q=>[q.id,q.direction*3]));
 const results=scoreCompass(questionnaire,answers);
 assert.ok(results.every(x=>x.score!==null&&x.score<=100&&x.score>=-100&&x.coverage===100));
});
test("une charge secondaire suit la question sans inventer une réponse principale",()=>{
 const answers=a([["q17",3],["q18",-3]]);
 const r=axis(answers,"territory");
 assert.equal(r.score,null);
 assert.equal(r.answered,0);
 assert.equal(r.coverage,0);
 assert.ok(r.evidenceWeight>0);
});
test("une réponse corrigée recalcule le résultat sans état caché",()=>{
 const answers=a([["q01",3],["q02",-3]]);
 assert.equal(axis(answers).score,100);
 answers.set("q02",{value:3,importance:"normal"});
 assert.equal(axis(answers).score,0);
});
test("les réponses hors échelle sont refusées",()=>{
 for(const invalid of [4,-4,1.5,NaN,Infinity,"2"]){
   assert.throws(()=>axis(a([["q01",invalid]])),/INVALID_ANSWER/);
 }
});
test("les questions inexistantes sont refusées",()=>{
 assert.throws(()=>scoreCompass(questionnaire,a([["q99",3]])),/INVALID_ANSWER/);
});
test("les importances inexistantes ou manquantes sont refusées",()=>{
 for(const weight of ["extra",null,5]){
   assert.throws(()=>scoreCompass(questionnaire,a([["q01",3,weight]])),/INVALID_ANSWER/);
 }
 assert.throws(()=>scoreCompass(questionnaire,new Map([["q01",{value:3}]])),/INVALID_ANSWER/);
});
test("un questionnaire modifié pendant le calcul est refusé",()=>{
 const corrupt=structuredClone(questionnaire);
 corrupt.methodology.minimumAnsweredRatio=0.01;
 assert.throws(()=>scoreCompass(corrupt,new Map()),/QUESTIONNAIRE_INVALID/);
});
test("formulations des huit questions verrouillées indépendamment du bundle",()=>{
 const altered=structuredClone(poll);
 altered.questions[0].text="Une nouvelle formulation orientée.";
 const result=inspectPoll(altered);
 assert.equal(result.ok,false);
 assert.ok(result.issues.some(x=>x==="QUESTION_1"));
});
test("un thème modifié du sondage est refusé indépendamment de la boussole",()=>{
 const altered=structuredClone(poll);
 altered.questions[2].axis="labour";
 assert.equal(inspectPoll(altered).ok,false);
});
test("la boussole délègue désormais ses calculs au moteur contrôlé",()=>{
 assert.match(boussoleScript,/core\.scoreCompass\(state\.data,state\.answers\)/);
 assert.match(boussoleScript,/validateQuestionnaireCorpus\(questionCorpus\)/);
});

test("le profil partiel est explicitement disponible avant Q64",async()=>{
 const html=await readFile(new URL("../boussole-electorale.html",import.meta.url),"utf8");
 assert.match(html,/id="compass-preview"[^>]*aria-controls="compass-results"/);
 assert.match(html,/Une dimension nécessitant moins de deux réponses principales restera non calculable/);
 assert.match(boussoleScript,/\$\("#compass-preview"\)\?\.addEventListener\("click"/);
 assert.match(boussoleScript,/if\(!state\.started \|\| !state\.data\)return;/);
 assert.match(boussoleScript,/showResults\(\);/);
});
test("la page charge la nouvelle version du validateur et du moteur",async()=>{
 const html=await readFile(new URL("../boussole-electorale.html",import.meta.url),"utf8");
 const pollHtml=await readFile(new URL("../sondage-citoyen.html",import.meta.url),"utf8");
 assert.match(html,/assets\/nova-civic-integrity\.js\?v=2/);
 assert.match(html,/assets\/boussole-electorale\.js\?v=3\.4\.22/);
 assert.match(pollHtml,/assets\/nova-civic-integrity\.js\?v=2/);
});
