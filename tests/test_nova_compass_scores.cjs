#!/usr/bin/env node
"use strict";
/**
 * Contrats du VRAI moteur calculate() de la Boussole Nova.
 * Corpus officiel en lecture seule, opinions synthétiques, zéro réseau/POST.
 * Les 16 dimensions sont indépendantes; aucune note électorale globale.
 */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const nova = path.resolve(__dirname, "../projets/projet-nova");
const corpus = JSON.parse(fs.readFileSync(path.join(nova, "data/boussole-electorale-v2.json"), "utf8"));
const source = fs.readFileSync(path.join(nova, "assets/boussole-electorale.js"), "utf8");
const start = source.indexOf("  function calculate(){");
const end = source.indexOf("\n  function resultCard", start);
assert.ok(start >= 0 && end > start, "La fonction de calcul officielle est introuvable");
const program = new vm.Script(source.slice(start, end) + "\ncalculate()", {
  filename: "boussole-electorale.js:calculate"
});
const questions = corpus.questions;
const axes = corpus.axes;

function calculate(pairs) {
  const answers = new Map(pairs);
  // Contexte isolé : pas de DOM, de fetch ou de capacités réseau.
  return program.runInNewContext({state: {data: corpus, answers}}, {timeout: 1000});
}
function respond(select, importance = "normal") {
  return questions.map(q => [q.id, {value: select(q), importance}]);
}
function verifyDimensions(results) {
  assert.equal(results.length, 16);
  assert.deepEqual(new Set(results.map(r => r.id)), new Set(axes.map(a => a.id)));
  for (const r of results) {
    assert.equal(r.total, 4);
    assert.ok(r.answered >= 0 && r.answered <= 4);
    assert.ok(r.coverage >= 0 && r.coverage <= 100);
    if (r.score !== null) assert.ok(r.score >= -100 && r.score <= 100);
  }
}

test("Corpus figé : 64 propositions, 16 axes équilibrés", () => {
  assert.equal(questions.length, 64);
  assert.equal(axes.length, 16);
  assert.equal(new Set(questions.map(q => q.id)).size, 64);
  for (const axis of axes) {
    const subset = questions.filter(q => q.axis === axis.id);
    assert.equal(subset.length, 4);
    assert.equal(subset.filter(q => q.direction === 1).length, 2);
    assert.equal(subset.filter(q => q.direction === -1).length, 2);
  }
});

test("64 réponses explicites neutres : scores 0, couverture 100 %", () => {
  const results = calculate(respond(() => 0));
  verifyDimensions(results);
  for (const r of results) {
    assert.equal(r.score, 0, r.id);
    assert.equal(r.coverage, 100, r.id);
    assert.equal(r.answered, 4, r.id);
  }
});

test("64 choix Sans opinion : aucun score inventé", () => {
  const results = calculate(respond(() => null));
  verifyDimensions(results);
  for (const r of results) {
    assert.equal(r.score, null, r.id);
    assert.equal(r.coverage, 0, r.id);
    assert.equal(r.answered, 0, r.id);
  }
});

test("Une réponse par axe : couverture 25 %, aucun score fiable", () => {
  const oneEach = axes.map(a => {
    const question = questions.find(q => q.axis === a.id);
    return [question.id, {value: 3, importance: "forte"}];
  });
  const results = calculate(oneEach);
  verifyDimensions(results);
  for (const r of results) {
    assert.equal(r.answered, 1, r.id);
    assert.equal(r.coverage, 25, r.id);
    assert.equal(r.score, null, r.id);
  }
});

test("Deux réponses par axe : seuil 50 % franchi", () => {
  const twoEach = axes.flatMap(axis => questions.filter(q => q.axis === axis.id)
    .slice(0, 2).map(q => [q.id, {value: 3 * q.direction, importance: "normal"}]));
  const results = calculate(twoEach);
  verifyDimensions(results);
  for (const r of results) {
    assert.equal(r.answered, 2, r.id);
    assert.equal(r.coverage, 50, r.id);
    assert.notEqual(r.score, null, r.id);
  }
});

test("Positions synthétiques polarisées : scores bornés et symétriques", () => {
  const plus = calculate(respond(q => 3 * q.direction));
  const minus = calculate(respond(q => -3 * q.direction));
  verifyDimensions(plus);
  verifyDimensions(minus);
  for (let i = 0; i < 16; i++) {
    assert.equal(plus[i].coverage, 100);
    assert.equal(minus[i].coverage, 100);
    assert.equal(plus[i].score, -minus[i].score, plus[i].id);
    // Certaines questions ont des contributions secondaires aux autres axes.
    // Un score autre que 100 est donc possible et ne signifie pas faible couverture.
  }
});

test("L'importance forte pèse davantage que l'importance faible", () => {
  const q = questions[0];
  const baseline = respond(() => 0);
  const weak = calculate(baseline.map(([id,answer]) => [
    id, id === q.id ? {value: 3 * q.direction, importance: "faible"} : answer
  ]));
  const strong = calculate(baseline.map(([id,answer]) => [
    id, id === q.id ? {value: 3 * q.direction, importance: "forte"} : answer
  ]));
  const id = q.axis;
  assert.ok(Math.abs(strong.find(r => r.id === id).score) >
            Math.abs(weak.find(r => r.id === id).score));
});


test("Partage Boussole : jamais de paramètres ni de fragment de l'URL source", async () => {
  const startShare = source.indexOf("  function configureSharing(results){");
  const endShare = source.indexOf("\n  async function copyText(", startShare);
  assert.ok(startShare >= 0 && endShare > startShare,
    "Le partage réel de la Boussole est introuvable");

  const safePage = "https://exemple.test/projets/projet-nova/boussole-electorale.html";
  const secret = "jeton-prive-ne-pas-transmettre";
  const link = href => ({
    href,
    getAttribute(name) { return name === "href" ? this.href : null; }
  });
  const nodes = {
    "#compass-share-email": link("mailto:"),
    "#compass-email-recipient": {value:""},
    "#compass-share-facebook": link("https://www.facebook.com/sharer/sharer.php"),
    "#compass-share-x": link("https://twitter.com/intent/tweet"),
    "#compass-share-linkedin": link("https://www.linkedin.com/sharing/share-offsite/"),
    "#compass-share-native": {},
    "#compass-copy-result": {},
    "#compass-status": {textContent:""}
  };
  let nativeShare = null;
  let copied = null;
  const mock = {
    $: selector => nodes[selector] || null,
    URL,
    window: {location: {
      origin: "https://exemple.test",
      pathname: "/projets/projet-nova/boussole-electorale.html",
      href: safePage + "?token=" + secret + "#resultat-prive"
    }},
    navigator: {share: async payload => {nativeShare = payload;}},
    buildResultText: () => "Profil synthétique local",
    encodeURIComponent,
    copyText: async text => {copied = text; return true;}
  };
  new vm.Script(source.slice(startShare, endShare) + "\nconfigureSharing([]);",
    {filename:"boussole-electorale.js:configureSharing"})
    .runInNewContext(mock, {timeout:1000});

  const facebook = new URL(nodes["#compass-share-facebook"].href);
  const twitter = new URL(nodes["#compass-share-x"].href);
  const linkedin = new URL(nodes["#compass-share-linkedin"].href);
  assert.equal(facebook.searchParams.get("u"), safePage);
  assert.equal(twitter.searchParams.get("url"), safePage);
  assert.equal(linkedin.searchParams.get("url"), safePage);
  for(const name of ["#compass-share-email", "#compass-share-facebook",
                    "#compass-share-x", "#compass-share-linkedin"]) {
    assert.ok(!nodes[name].href.includes(secret), name + " divulgue un paramètre privé");
    assert.ok(!nodes[name].href.includes("resultat-prive"), name + " divulgue un fragment privé");
  }

  await nodes["#compass-share-native"].onclick();
  assert.equal(nativeShare.url, safePage);
  assert.ok(!nativeShare.text.includes(secret));
  await nodes["#compass-copy-result"].onclick();
  assert.ok(copied.endsWith(safePage));
  assert.ok(!copied.includes(secret));

  // Le chemin //hôte-tiers n'est jamais traité comme une autre origine.
  const maliciousPath = "//faux-domaine.example/vol";
  mock.window.location.pathname = maliciousPath;
  mock.window.location.href = safePage + "?token=" + secret + "#resultat-prive";
  const sameOriginLink = mock.window.location.origin + maliciousPath;
  assert.notEqual(new URL(maliciousPath, mock.window.location.origin).href,
    sameOriginLink, "Le cas de phishing doit être réellement reproductible");
  nativeShare = null;
  copied = null;
  new vm.Script(source.slice(startShare, endShare) + "\nconfigureSharing([]);",
    {filename:"boussole-electorale.js:double-slash-share"})
    .runInNewContext(mock, {timeout:1000});
  assert.equal(new URL(nodes["#compass-share-facebook"].href).searchParams.get("u"), sameOriginLink);
  assert.equal(new URL(nodes["#compass-share-x"].href).searchParams.get("url"), sameOriginLink);
  assert.equal(new URL(nodes["#compass-share-linkedin"].href).searchParams.get("url"), sameOriginLink);
  await nodes["#compass-share-native"].onclick();
  await nodes["#compass-copy-result"].onclick();
  assert.equal(nativeShare.url, sameOriginLink);
  assert.ok(copied.endsWith(sameOriginLink));
  assert.ok(!nodes["#compass-share-email"].href.includes(secret));
});


test("Liens de preuve Boussole : protocoles actifs et URL trompeuses refusés", () => {
  const startUrl = source.indexOf("  function safeDocumentSource(raw){");
  const endUrl = source.indexOf("\n  function validateDocumentaryCorpora", startUrl);
  assert.ok(startUrl >= 0 && endUrl > startUrl, "Validation officielle des liens absente");
  const validate = new vm.Script(source.slice(startUrl, endUrl) + "\nsafeDocumentSource(input)",
    {filename: "boussole-electorale.js:safeDocumentSource"});
  const inspect = input => validate.runInNewContext({input, URL}, {timeout:1000});
  for(const url of [
    "https://www.electionsquebec.qc.ca/",
    "https://exemple.org/document.pdf?version=1"
  ]) assert.equal(inspect(url), true, "Document HTTPS valide rejeté : " + url);
  for(const url of [
    "javascript:alert(1)",
    "data:text/html,Bonjour",
    "http://exemple.org/document.pdf",
    "//exemple.org/document.pdf",
    "https://utilisateur:motdepasse@exemple.org/",
    "https://exemple.org:8443/document.pdf",
    "https://exemple.org/a b",
    "https://exemple.org/a\nb",
    "https://",
    "",
    null,
    "x".repeat(2100)
  ]) assert.equal(inspect(url), false, "URL non sûre acceptée : " + String(url).slice(0,60));
});


test("La page Boussole prévient du partage des opinions sensibles",()=>{
  const html=fs.readFileSync(path.join(nova,"boussole-electorale.html"),"utf8");
  assert.ok(html.includes("Confidentialité du partage :"),
    "L'information préalable au partage doit être affichée à côté des actions");
  assert.ok(html.includes("opinions politiques sensibles"),
    "Le profil doit être présenté comme une information sensible");
  assert.ok(html.includes("le destinataire et, selon le service, son fournisseur"),
    "La divulgation aux tiers doit être explicitement annoncée");
  assert.ok(html.includes("Sans partage, il demeure local."),
    "La FAQ doit distinguer calcul local et transmission volontaire");
  for(const id of ["compass-share-facebook","compass-share-x","compass-share-linkedin"]){
    const pos=html.indexOf('id="'+id+'"');
    assert.ok(pos>=0,id+" : lien externe absent");
    const tag=html.slice(html.lastIndexOf("<a ",pos),html.indexOf("</a>",pos));
    assert.match(tag,/target="_blank"/);
    assert.match(tag,/rel="noopener noreferrer"/,id+" : protection des liens externes absente");
  }
});


// La carte ne doit pas faire pivoter les axes non répondus ni dessiner une
// continuité trompeuse entre deux dimensions séparées par des valeurs nulles.
function renderRealRadar(data) {
  const startRadar = source.indexOf("  function renderRadar(results){");
  const endRadar = source.indexOf("\n  function coveragePercent(results){",startRadar);
  assert.ok(startRadar >= 0 && endRadar > startRadar, "Fonction radar introuvable");
  const host = {innerHTML:""};
  new vm.Script(source.slice(startRadar,endRadar)+"\nrenderRadar(input);",
    {filename:"boussole-electorale.js:renderRadar"})
    .runInNewContext({input:data,$:selector=>selector==="#compass-radar"?host:null,
      esc:value=>String(value).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")},
      {timeout:1000});
  return host.innerHTML;
}
test("Radar partiel : 16 axes fixes, aucun polygone à travers des dimensions absentes", () => {
  const partial=axes.map((a,i)=>({
    title:a.title,score:[0,1,4,7].includes(i)?(i*8)-30:null
  }));
  const html=renderRealRadar(partial);
  assert.equal((html.match(/<text /g)||[]).length,16,
    "Le graphique partiel doit conserver les 16 angles");
  assert.equal((html.match(/class="compass-radar-point"/g)||[]).length,4);
  assert.equal((html.match(/class="compass-radar-segment"/g)||[]).length,1,
    "Seuls les deux premiers axes sont adjacents et calculés");
  assert.doesNotMatch(html,/<polygon /,"Polygone trompeur sur données absentes");
  assert.match(html,/4 dimensions calculées sur 16/);
  assert.match(html,/—/);
});
test("Radar complet : polygone continu uniquement avec 16 scores connus", () => {
  const complete=axes.map(a=>({title:a.title,score:0}));
  const html=renderRealRadar(complete);
  assert.equal((html.match(/<text /g)||[]).length,16);
  assert.equal((html.match(/class="compass-radar-point"/g)||[]).length,16);
  assert.equal((html.match(/<polygon /g)||[]).length,1);
  assert.equal((html.match(/class="compass-radar-segment"/g)||[]).length,0);
  assert.match(html,/16 dimensions calculées sur 16/);
});
test("Radar insuffisant : aucun positionnement supposé sur 1 ou 2 axes", () => {
  const incomplete=axes.map((a,i)=>({title:a.title,score:i<2?75:null}));
  const html=renderRealRadar(incomplete);
  assert.doesNotMatch(html,/<svg/);
  assert.match(html,/pas encore assez de dimensions/);
});
test("Radar : la notice HTML explique les dimensions non calculées", () => {
  const html=fs.readFileSync(path.join(nova,"boussole-electorale.html"),"utf8");
  assert.match(html,/Chaque rayon correspond toujours à la même dimension/);
  assert.match(html,/aucun trait ne traverse une dimension manquante/);
});


// « Sans opinion » et dimension insuffisamment renseignée ne doivent pas
// placer un faux marqueur de neutralité au centre de l'échelle.
test("Carte détaillée Boussole : aucune position affichée pour un score non calculé",()=>{
  const startCard=source.indexOf("  function resultCard(result){");
  const endCard=source.indexOf("\n  function renderRadar(results){",startCard);
  assert.ok(startCard>=0 && endCard>startCard);
  const program=new vm.Script(source.slice(startCard,endCard)+"\nresultCard(input);",
    {filename:"boussole-electorale.js:resultCard"});
  const card=score=>program.runInNewContext({
    input:{title:"Dimension fictive",negative:"Pôle A",positive:"Pôle B",
      score,answered:score===null?0:4,total:4,coverage:score===null?0:100},
    esc:value=>String(value)
  },{timeout:1000});
  const missing=card(null);
  const neutral=card(0);
  assert.match(missing,/Données insuffisantes/);
  assert.match(missing,/Couverture : 0\/4/);
  assert.doesNotMatch(missing,/<i /,"Un score inconnu ne doit pas figurer à 50 %");
  assert.match(neutral,/Équilibre/);
  assert.match(neutral,/<i style="left:50%">/,"Un vrai choix neutre se place à 50 %");
  assert.match(card(-100),/<i style="left:0%">/);
  assert.match(card(100),/<i style="left:100%">/);
});


// L'inventaire politique est un instantané daté, et non une interrogation
// temps réel du registre électoral. Sa cohérence interne n'établit pas
// l'exhaustivité de la liste à une date ultérieure.
test("Registre Boussole : provenance datée et aucune exhaustivité temps réel supposée",()=>{
  const parties=JSON.parse(fs.readFileSync(path.join(nova,
    "data/boussole-partis-2026.json"),"utf8"));
  assert.equal(parties.registryEvidence.snapshotDate,"2026-10-07");
  const startRegistry=source.indexOf("  function renderPartyRegistry(corpus,evidenceCorpus){");
  const endRegistry=source.indexOf("\n  const DOCUMENTARY_STATUS_LABELS",startRegistry);
  assert.ok(startRegistry>=0 && endRegistry>startRegistry);
  const fragment=source.slice(startRegistry,endRegistry);
  assert.match(fragment,/registryEvidence\?\.snapshotDate/);
  assert.match(fragment,/Comptes du dossier cohérents avec l’instantané/);
  assert.match(fragment,/consulter le registre officiel d’Élections Québec/);
  assert.doesNotMatch(fragment,/Liste officielle 2026 complète/);
  const page=fs.readFileSync(path.join(nova,
    "boussole-electorale.html"),"utf8");
  assert.match(page,/instantané daté du 7 octobre 2026/);
  assert.match(page,/statut actuel doit être vérifié auprès d’Élections Québec/);
  assert.doesNotMatch(page,/Les 20 partis actuellement autorisés/);
});


test("Réinitialisation Boussole : aucune fermeture de partage ne retient le profil",()=>{
  const beginShare=source.indexOf("  function configureSharing(results){");
  const endShare=source.indexOf("\n  async function copyText(",beginShare);
  const beginReset=source.indexOf("  function reset(focusStart=true){");
  const endReset=source.indexOf("\n  function renderPartyRegistry",beginReset);
  assert.ok(beginShare>=0 && endShare>beginShare && beginReset>=0 && endReset>beginReset);
  const nodes = Object.create(null);
  function node(id) {
    if(!nodes[id]) {
      nodes[id] = {
        href:id==="#compass-share-facebook"?"https://www.facebook.com/sharer/sharer.php":
          id==="#compass-share-x"?"https://x.com/intent/post":
          id==="#compass-share-linkedin"?"https://www.linkedin.com/sharing/share-offsite/":
          id==="#compass-share-email"?"mailto:":"",
        value:"",hidden:false,textContent:"",onclick:null,oninput:null,
        getAttribute(key){return key==="href"?this.href:null;},
        setAttribute(key,value){if(key==="href")this.href=value;},
        replaceChildren(){this.children=[];},focus(){}
      };
    }
    return nodes[id];
  }
  const ctx={
    $:node,
    state:{
      answers:new Map([["q01",{value:3,importance:"forte"}]]),
      importance:new Map([["q01","forte"]]),currentIndex:42,
      started:true,results:[{title:"Profil sensible de démonstration"}]
    },
    buildResultText:()=>"PROFIL_PERSONNEL_SECRET_TEST",
    window:{location:{origin:"https://exemple.test",pathname:"/projets/projet-nova/boussole-electorale.html"}},
    navigator:{},encodeURIComponent,updateProgress(){},
    copyText:async()=>true
  };
  const action=new vm.Script(source.slice(beginShare,endShare)+
    "\n"+source.slice(beginReset,endReset)+
    "\nconfigureSharing([]);",{filename:"boussole-electorale.js:sharing-and-reset"});
  action.runInNewContext(ctx,{timeout:1000});
  const email=node("#compass-email-recipient");
  const link=node("#compass-share-email");
  email.value="personne@example.test";
  email.oninput();
  assert.match(link.href,/PROFIL_PERSONNEL_SECRET_TEST/);
  assert.equal(typeof node("#compass-share-native").onclick,"function");
  assert.equal(typeof node("#compass-copy-result").onclick,"function");
  ctx.reset(false);
  assert.equal(email.value,"");
  assert.equal(email.oninput,null,"la fermeture email contient encore le résumé");
  assert.equal(node("#compass-share-native").onclick,null,"le partage natif garde la fermeture");
  assert.equal(node("#compass-copy-result").onclick,null,"la copie garde la fermeture");
  for(const name of ["#compass-share-email","#compass-share-facebook",
                     "#compass-share-x","#compass-share-linkedin"]) {
    assert.doesNotMatch(node(name).href,/PROFIL_PERSONNEL_SECRET_TEST/);
  }
  assert.equal(link.href,"mailto:");
  assert.equal(ctx.state.answers.size,0);
  assert.equal(ctx.state.importance.size,0);
  assert.equal(ctx.state.results,null);
  assert.equal(node("#compass-results").hidden,true);
  assert.equal(node("#compass-summary").textContent,"");
  // Le navigateur ne peut plus recréer l'ancien mailto depuis le même champ.
  email.value="autre@example.test";
  assert.equal(email.oninput,null);
  assert.equal(link.href,"mailto:");
});


test("Boussole : après reset la progression ARIA indique zéro, pas question 1",()=>{
  const begin=source.indexOf("  function updateProgress(){");
  const end=source.indexOf("\n  function updateStepControls(){",begin);
  assert.ok(begin>=0 && end>begin,"Mise à jour de progression réelle introuvable");
  const nodes=Object.create(null);
  const $=selector=>(nodes[selector]??={
    style:{},attributes:{},textContent:"",
    setAttribute(k,v){this.attributes[k]=v;}
  });
  const state={
    data:corpus,currentIndex:38,started:false,
    answers:new Map([["q01",{value:2,importance:"normal"}]])
  };
  const vmContext={state,$};
  const run=new vm.Script(source.slice(begin,end)+"\nupdateProgress();",{
    filename:"boussole-electorale.js:updateProgress"});
  run.runInNewContext(vmContext,{timeout:1000});
  assert.equal(nodes["#compass-progress-track"].attributes["aria-valuenow"],"0");
  assert.equal(nodes["#compass-progress-track"].attributes["aria-valuetext"],
    "Questionnaire non commencé");
  assert.equal(nodes["#compass-progress-bar"].style.width,"0%");
  assert.match(nodes["#compass-progress-text"].textContent,/non commencé/);
  assert.doesNotMatch(nodes["#compass-progress-text"].textContent,/Question 1 sur 64/);
  // Commencer à répondre doit toujours restaurer une progression réelle.
  state.started=true;
  state.currentIndex=38;
  run.runInNewContext(vmContext,{timeout:1000});
  assert.equal(nodes["#compass-progress-track"].attributes["aria-valuenow"],"39");
  assert.equal(nodes["#compass-progress-track"].attributes["aria-valuetext"],"Question 39 sur 64");
  assert.match(nodes["#compass-progress-text"].textContent,/1 réponse enregistrée/);
});


test("Boussole : résumé exact si aucune, 8 ou 16 dimensions sont calculables",()=>{
  const startResults=source.indexOf("  function showResults(){");
  const endResults=source.indexOf("\n  function reset(focusStart=true){",startResults);
  assert.ok(startResults>=0 && endResults>startResults);
  const runner=new vm.Script(source.slice(startResults,endResults)+
    "\nshowResults();",{filename:"boussole-electorale.js:showResults"});
  const run=({answered,available})=>{
    const nodes=Object.create(null);
    const $=id=>(nodes[id]??={
      textContent:"",hidden:true,innerHTML:"",focused:false,
      focus(){this.focused=true;}
    });
    const result=axes.map((axis,i)=>({
      ...axis,score:i<available?0:null,answered:i<available?4:1,total:4,coverage:i<available?100:25
    }));
    let sharing=0;
    const context={
      state:{data:corpus,answers:new Map(Array.from({length:answered},(_,i)=>
        ["q"+String(i+1).padStart(2,"0"),{value:1,importance:"normal"}])),results:null},
      $,calculate:()=>result,resultCard:()=>"<article></article>",
      renderRadar:()=>{},coveragePercent:()=>Math.round(100*answered/64),
      configureSharing:()=>{sharing++;},scrollToSection:()=>{}
    };
    runner.runInNewContext(context,{timeout:1000});
    return {nodes,context,sharing};
  };
  const insufficient=run({answered:1,available:0});
  assert.match(insufficient.nodes["#compass-summary"].textContent,/Aucune dimension calculable/);
  assert.match(insufficient.nodes["#compass-summary"].textContent,/Aucun profil politique/);
  assert.equal(insufficient.nodes["#compass-share-card"].hidden,true);
  assert.equal(insufficient.nodes["#compass-results"].hidden,false);
  assert.equal(insufficient.sharing,0);
  assert.match(insufficient.nodes["#compass-status"].textContent,/Aucune dimension calculable/);
  const misleading=run({answered:32,available:8});
  assert.match(misleading.nodes["#compass-summary"].textContent,/Profil partiel/);
  assert.match(misleading.nodes["#compass-summary"].textContent,/8\/16 dimensions calculables/);
  assert.equal(misleading.nodes["#compass-share-card"].hidden,false);
  assert.equal(misleading.sharing,1);
  const complete=run({answered:64,available:16});
  assert.match(complete.nodes["#compass-summary"].textContent,/Profil calculé sur 16 dimensions/);
  assert.equal(complete.nodes["#compass-share-card"].hidden,false);
  assert.equal(complete.sharing,1);
  const html=fs.readFileSync(path.join(nova,"boussole-electorale.html"),"utf8");
  const css=fs.readFileSync(path.join(nova,"assets/boussole-electorale.css"),"utf8");
  assert.match(html,/au moins deux propositions du même thème/);
  assert.match(css,/\.compass-share-card\[hidden\]\{display:none!important\}/);
});
