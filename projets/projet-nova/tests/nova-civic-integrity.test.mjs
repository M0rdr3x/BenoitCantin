import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {runInNewContext} from "node:vm";
const read=(file)=>readFile(new URL("../"+file,import.meta.url),"utf8");
const json=async name=>JSON.parse(await read("data/"+name));
const [script,compass,poll,parties,sources,evidence,pollBundle,compassBundle,compassHtml,pollHtml,compassJs,pollJs]=await Promise.all([
 read("assets/nova-civic-integrity.js"),
 json("boussole-electorale-v2.json"),json("sondage-citoyen-v1.json"),
 json("boussole-partis-2026.json"),json("boussole-sources-partis-2026.json"),
 json("boussole-preuves-2026.json"),
 read("assets/sondage-public-corpus.js"),read("assets/boussole-public-corpus.js"),
 read("boussole-electorale.html"),read("sondage-citoyen.html"),
 read("assets/boussole-electorale.js"),read("assets/sondage-citoyen.js")
]);
const sandbox={window:{}};
runInNewContext(script,sandbox,{timeout:1500});
const integrity=sandbox.window.__NOVA_CIVIC_INTEGRITY;
const copy=x=>structuredClone(x);
const pass=x=>assert.equal(x.ok,true,x.issues.join(","));
const fail=(x,code)=>{assert.equal(x.ok,false);assert.ok(x.issues.some(v=>v===code||v.startsWith(code)),x.issues.join(","));};

test("les 64 questions et 16 dimensions passent le contrôle de neutralité",()=>pass(integrity.inspectCompass(compass)));
test("le sondage de huit questions 18+ et ses six réponses est conforme",()=>pass(integrity.inspectPoll(poll)));
test("les huit formulations du sondage reprennent exactement la boussole",()=>pass(integrity.inspectPollCompassBinding(poll,compass)));
test("chaque dimension a deux propositions dans chaque sens",()=>{
 for(const axis of compass.axes){
   const qs=compass.questions.filter(q=>q.axis===axis.id);
   assert.equal(qs.filter(q=>q.direction===-1).length,2);
   assert.equal(qs.filter(q=>q.direction===1).length,2);
 }
});
test("les pondérations déclarées restent dans les bornes explicites",()=>{
 assert.deepEqual(compass.methodology.importanceWeights,{faible:.5,normal:1,forte:1.5});
 assert.equal(compass.methodology.axisMinimumAnswered,2);
 assert.equal(compass.methodology.responseScale.min,-3);
 assert.equal(compass.methodology.responseScale.max,3);
});
test("une dimension supprimée est refusée",()=>{const d=copy(compass);d.axes.pop();fail(integrity.inspectCompass(d),"SCHEMA");});
test("une proposition manquante est refusée",()=>{const d=copy(compass);d.questions.pop();fail(integrity.inspectCompass(d),"SCHEMA");});
test("l'ordre des questions est verrouillé",()=>{const d=copy(compass);[d.questions[0],d.questions[1]]=[d.questions[1],d.questions[0]];fail(integrity.inspectCompass(d),"QUESTION_q01");});
test("un axe en double est refusé",()=>{const d=copy(compass);d.axes[1].id=d.axes[0].id;assert.equal(integrity.inspectCompass(d).ok,false);});
test("une modification de direction est refusée",()=>{const d=copy(compass);d.questions[0].direction=-1;fail(integrity.inspectCompass(d),"PRIMARY_LOADING_q01");});
test("une question avec trois orientations positives est refusée",()=>{
 const d=copy(compass);d.questions[1].direction=1;d.questions[1].loadings[0].direction=1;
 fail(integrity.inspectCompass(d),"UNBALANCED_AXIS_economy");
});
test("une direction de calcul 0 ou 2 n'est jamais acceptée",()=>{
 for(const value of [0,2,-2]){const d=copy(compass);d.questions[0].direction=value;fail(integrity.inspectCompass(d),"QUESTION_q01");}
});
test("la pondération principale ne peut favoriser artificiellement une question",()=>{
 const d=copy(compass);d.questions[0].loadings[0].weight=2;fail(integrity.inspectCompass(d),"PRIMARY_LOADING_q01");
});
test("la pondération secondaire ne peut dépasser 0,4",()=>{
 const d=copy(compass);d.questions.find(q=>q.loadings.length===2).loadings[1].weight=.6;
 assert.equal(integrity.inspectCompass(d).ok,false);
});
test("la pondération secondaire doit viser un autre axe existant",()=>{
 const d=copy(compass);const q=d.questions.find(q=>q.loadings.length===2);q.loadings[1].axis=q.axis;
 assert.equal(integrity.inspectCompass(d).ok,false);
});
test("les échelles et poids utilisateurs sont protégés contre une dérive de méthode",()=>{
 const d=copy(compass);d.methodology.importanceWeights.forte=5;
 fail(integrity.inspectCompass(d),"CALCULATION_OR_NEUTRALITY_RULE");
});
test("un code qualité manquant entraîne l'arrêt",()=>{
 const d=copy(compass);d.questions[0].quality.neutralTone=false;
 fail(integrity.inspectCompass(d),"QUESTION_q01");
});
test("la comparaison politique n'est pas activée sans sources",()=>{
 const d=copy(compass);d.partyComparison.enabled=true;
 fail(integrity.inspectCompass(d),"CALCULATION_OR_NEUTRALITY_RULE");
});
test("un consentement au sondage ne remplace pas une publication",()=>{
 assert.equal(poll.published,false);assert.equal(integrity.inspectPoll(poll).ok,true);
});
test("le sondage refuse des questions en doublon et des ordres modifiés",()=>{
 const d=copy(poll);d.questions[1].id=d.questions[0].id;
 fail(integrity.inspectPoll(d),"QUESTION_2");
});
test("le sondage refuse les choix inconnus ou inversés",()=>{
 const d=copy(poll);d.options[5].value=3;fail(integrity.inspectPoll(d),"OPTIONS");
});
test("le sondage refuse la transformation en sondage probabiliste non démontré",()=>{
 const d=copy(poll);d.format="sondage_representatif";fail(integrity.inspectPoll(d),"SCHEMA");
});
test("le sondage refuse une ouverture déclarée sans booléen",()=>{
 const d=copy(poll);d.published="true";fail(integrity.inspectPoll(d),"SCHEMA");
});
test("une formulation changée d'un côté est détectée",()=>{
 const d=copy(poll);d.questions[0].text+=" Nouvelle proposition.";
 fail(integrity.inspectPollCompassBinding(d,compass),"SOURCE_MISMATCH_q02");
});
test("une dimension différente dans le sondage est détectée",()=>{
 const d=copy(poll);d.questions[1].axis="economy";
 fail(integrity.inspectPollCompassBinding(d,compass),"SOURCE_MISMATCH_q09");
});
test("le bundle du sondage est identique au JSON source versionné",()=>{
 const w={window:{}};runInNewContext(pollBundle,w,{timeout:1500});
 assert.equal(JSON.stringify(w.window.__NOVA_POLL_PUBLIC_CORPUS),JSON.stringify(poll));
});
test("les quatre bundles de la boussole sont identiques aux sources JSON",()=>{
 const w={window:{}};runInNewContext(compassBundle,w,{timeout:4500});
 const x=w.window.__NOVA_COMPASS_PUBLIC_CORPORA;
 for(const [key,source] of Object.entries({questionnaire:compass,parties,sources,evidence}))
   assert.equal(JSON.stringify(x[key]),JSON.stringify(source),key);
});
test("les deux interfaces chargent le validateur AVANT les scripts de questionnaire",()=>{
 for(const [html,corpus,script] of [
   [pollHtml,"assets/sondage-public-corpus.js","assets/sondage-citoyen.js"],
   [compassHtml,"assets/boussole-public-corpus.js","assets/boussole-electorale.js"]
 ]){
   const a=html.indexOf('src="'+corpus),b=html.indexOf('src="assets/nova-civic-integrity.js'),
       c=html.indexOf('src="'+script);
   assert.ok(a>=0&&a<b&&b<c,corpus);
 }
});
test("les deux contrôleurs utilisent obligatoirement le validateur",()=>{
 assert.match(pollJs,/__NOVA_CIVIC_INTEGRITY\?\.inspectPoll\(corpus\)/);
 assert.match(compassJs,/__NOVA_CIVIC_INTEGRITY\?\.inspectCompass\(corpus\)/);
});
test("les réponses de la boussole restent locales; aucun POST de profil",()=>{
 assert.doesNotMatch(compassJs,/method\s*:\s*["']POST["']/);
 assert.match(compassHtml,/calculé(?:es)? localement|calcul local/);
});
test("le sondage comprend une progression accessible et désactive un envoi incomplet",()=>{
 assert.match(pollHtml,/id="poll-answer-progress"[^>]*role="status"/);
 assert.match(pollJs,/questions\.length===8 && answered===questions\.length/);
 assert.match(pollHtml,/id="poll-adult"/);
 assert.match(pollHtml,/id="poll-agree"/);
});
test("l'état du vote ne peut pas passer automatiquement à publié côté client",()=>{
 assert.equal(poll.published,false);
 assert.match(pollJs,/local\.published===true && remote\.open===true/);
 assert.match(pollJs,/!captchaToken/);
});
test("la comparaison des partis reste désactivée tant que les revues manquent",()=>{
 assert.equal(compass.partyComparison.enabled,false);
 assert.ok(parties.parties.every(p=>p.comparisonEligible===false));
 assert.ok(evidence.evidenceRecords.every(x=>x.secondIndependentReview?.status==="completed"||x.finalizable!==true));
});

test("l'explorateur des partis vérifie aussi les 64 questions avant de montrer les sources",()=>{
 const start=compassJs.indexOf("async function loadPoliticalRegistryAndEvidence()");
 const end=compassJs.indexOf("let questionnaireLoading",start);
 const block=compassJs.slice(start,end>start?end:start+6000);
 assert.match(block,/validateQuestionnaireCorpus\(questionCorpus\);/);
 assert.match(block,/validateDocumentaryCorpora\(questionCorpus,partyCorpus,sourceCorpus,evidenceCorpus\);/);
 assert.ok(block.indexOf("validateQuestionnaireCorpus(questionCorpus)")<
   block.indexOf("validateDocumentaryCorpora(questionCorpus"));
});
