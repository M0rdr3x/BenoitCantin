'use strict';
// Test du rendu réel dans un DOM minimal, sans réseau ni réponses individuelles.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const NOVA = path.resolve(__dirname, '../projets/projet-nova');
const script = fs.readFileSync(path.join(NOVA, 'assets/resultats-sondages.js'), 'utf8');
const read = name => JSON.parse(fs.readFileSync(path.join(NOVA, 'data', name), 'utf8'));
const original = read('resultats-sondages-publics-v1.json');
const copy = value => JSON.parse(JSON.stringify(value));

class FakeElement {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.attributes = {};
    this.handlers = {};
    this.style = {};
    this.textContent = '';
  }
  setAttribute(key, value) { this.attributes[key] = value; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; }
  addEventListener(name, callback) { this.handlers[name] = callback; }
  click() { if (this.handlers.click) this.handlers.click(); }
}

async function mount(snapshot, {badManifest = false, fetchFailure = false} = {}) {
  const elements = new Map();
  const document = {
    readyState: 'complete',
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, new FakeElement(id));
      return elements.get(id);
    },
    createElement(tag) { return new FakeElement(tag); },
  };
  const fixtures = {
    'data/consultation-40-v1.json': read('consultation-40-v1.json'),
    'data/sondage-questions-v1.json': read('sondage-questions-v1.json'),
    'data/resultats-sondages-publics-v1.json': snapshot,
  };
  if (badManifest) fixtures['data/consultation-40-v1.json'].questions[0].text = 'X';
  const context = {
    document,
    fetch: async url => {
      if (fetchFailure) throw Error('network unavailable');
      if (!Object.hasOwn(fixtures, url)) throw Error('unexpected fixture: '+url);
      return {ok: true, json: async () => copy(fixtures[url])};
    },
  };
  vm.runInNewContext(script, context, {filename:'resultats-sondages.js',timeout:1500});
  await new Promise(resolve => setImmediate(resolve));
  return id => document.getElementById(id);
}

function syntheticApproved() {
  const result=copy(original);
  result.publicationStatus='approved_aggregate';
  result.publicationApproved=true;
  result.privacyReviewApproved=true;
  result.publishedOn='2026-10-22';
  result.source='Fixture strictement synthétique, jamais publiée';
  const entry=result.surveys['nova-orientations-40-v1'];
  entry.status='approved_aggregate';
  entry.respondents=30;
  entry.questions=Array.from({length:40},(_,i)=>({
    id:'q'+String(i+1).padStart(2,'0'),status:'published',total:30,
    counts:{pour:20,contre:10,sans_opinion:0},
  }));
  return result;
}

async function assertUnavailable(snapshot,options) {
  const el=await mount(snapshot,options);
  assert.match(el('results-state').textContent,/indisponibles ou non validées/);
  assert.match(el('results-explainer').textContent,/vérification a échoué/);
  assert.equal(el('results-question-list').children.length,1);
  el('results-show-64').click();
  assert.match(el('results-state').textContent,/indisponibles ou non validées/);
  assert.equal(el('results-question-list').children.length,1);
}

test('registre fermé : 40 et 64 formulations sans résultats inventés',async()=>{
  const el=await mount(copy(original));
  assert.match(el('results-state').textContent,/Aucun résultat publié/);
  assert.equal(el('results-question-list').children.length,40);
  el('results-show-64').click();
  assert.equal(el('results-question-list').children.length,64);
  assert.equal(el('results-show-64').attributes['aria-pressed'],'true');
});

test('erreur réseau ne devient pas un état fermé faussement validé',async()=>{
  await assertUnavailable(copy(original),{fetchFailure:true});
});
test('manifestation d’une question altérée rejetée',async()=>{
  await assertUnavailable(copy(original),{badManifest:true});
});
test('champ public inconnu bloqué, même sans identité visible',async()=>{
  const data=copy(original);
  data.surveys['nova-orientations-40-v1'].statisticsByNeighborhood=[];
  await assertUnavailable(data);
});
test('mentions publiques non approuvées sur état fermé : aucun résultat affiché',async()=>{
  for (const field of ['source','notes']) {
    const data=copy(original);
    data[field]='contact de participant fictif: test@example.invalid';
    await assertUnavailable(data);
  }
});

test('date non autorisée sur état fermé bloquée',async()=>{
  const data=copy(original);data.publishedOn='2026-10-22';
  await assertUnavailable(data);
});
test('agrégats exclusivement synthétiques : affichage des comptes sûrs',async()=>{
  const el=await mount(syntheticApproved());
  assert.match(el('results-state').textContent,/Résultats agrégés approuvés/);
  assert.equal(el('results-question-list').children.length,40);
  assert.equal(el('results-question-list').children[0].children.length,4);
});
test('petite cellule bloque tous les résultats, sans affichage partiel',async()=>{
  const data=syntheticApproved();
  data.surveys['nova-orientations-40-v1'].questions[0].counts=
    {pour:25,contre:5,sans_opinion:0};
  await assertUnavailable(data);
});
test('question masquée : aucun total résiduel dans sa ligne',async()=>{
  const data=syntheticApproved();
  const row=data.surveys['nova-orientations-40-v1'].questions[0];
  row.status='suppressed';
  await assertUnavailable(data);
  delete row.total;delete row.counts;
  const el=await mount(data);
  assert.match(el('results-question-list').children[0].children[1].textContent,/Répartition masquée/);
});
