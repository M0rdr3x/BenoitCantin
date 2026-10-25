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
