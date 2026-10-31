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
