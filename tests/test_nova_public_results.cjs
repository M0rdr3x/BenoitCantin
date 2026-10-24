'use strict';
// Test du rendu réel dans un DOM minimal, sans réseau ni réponses individuelles.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { webcrypto } = require('node:crypto');
const path = require('node:path');
const vm = require('node:vm');

const NOVA = path.resolve(__dirname, '../projets/projet-nova');
const script = fs.readFileSync(path.join(NOVA, 'assets/resultats-sondages.js'), 'utf8');
const CLOSED_GATE = 'const PUBLIC_AGGREGATES_ENABLED = false;';
assert.equal(script.split(CLOSED_GATE).length, 2,
  'Le verrou explicite de diffusion doit rester fermé dans le JS livré');
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

async function mount(snapshot, {
  badManifest = false, badManifest64 = false, fetchFailure = false,
  stallFetch = false, syntheticRelease = false,
} = {}) {
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
  if (badManifest64) fixtures['data/sondage-questions-v1.json'].questions[0].text = 'X';
  const context = {
    document,
    crypto: webcrypto,
    TextDecoder,
    AbortController,
    setTimeout: (fn, ms) => setTimeout(fn, stallFetch ? 10 : ms),
    clearTimeout,
    fetch: async (url, options = {}) => {
      if (stallFetch && url === 'data/resultats-sondages-publics-v1.json') {
        // Une connexion réellement bloquée ne résout la promesse qu'au signal
        // abort du navigateur; minuterie abrégée exclusivement pour ce test.
        return await new Promise((resolve, reject) => {
          options.signal?.addEventListener('abort',
            () => reject(new Error('REQUEST_ABORTED')), {once:true});
        });
      }
      if (fetchFailure) throw Error('network unavailable');
      if (!Object.hasOwn(fixtures, url)) throw Error('unexpected fixture: '+url);
      return {
        ok: true,
        json: async () => copy(fixtures[url]),
        // Les manifests sont servis dans leurs octets originaux, sauf mutation
        // intentionnelle : le test exerce la vraie vérification SHA-256 du client.
        arrayBuffer: async () => {
          const name = url.startsWith('data/') ? url.slice(5) : '';
          const data = (name === 'consultation-40-v1.json' ||
              name === 'sondage-questions-v1.json') &&
              !((badManifest && name === 'consultation-40-v1.json') ||
                (badManifest64 && name === 'sondage-questions-v1.json'))
            ? fs.readFileSync(path.join(NOVA, 'data', name))
            : Buffer.from(JSON.stringify(fixtures[url]), 'utf8');
          return Uint8Array.from(data).buffer;
        },
      };
    },
  };
  // Le seul déverrouillage autorisé est dans cette VM et avec des fixtures
  // de test : aucun octet de la page publiée ni du JSON réel n'est changé.
  const candidate = syntheticRelease
    ? script.replace(CLOSED_GATE, 'const PUBLIC_AGGREGATES_ENABLED = true;')
    : script;
  vm.runInNewContext(candidate, context, {filename:'resultats-sondages.js',timeout:1500});
  // Les digests Web Crypto des deux manifestes sont asynchrones : attendre
  // l'affichage effectif, et non un seul cycle d'événements non déterministe.
  const ready = () => Boolean(elements.get('results-state')?.textContent) &&
    (elements.get('results-question-list')?.children.length ?? 0) > 0;
  for (let attempt = 0; attempt < 200 && !ready(); attempt++) {
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  assert.ok(ready(), 'Résultats Nova : rendu DOM non terminé ou erreur asynchrone');
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
test('connexion bloquée : timeout, annulation et indisponibilité sans résultats',async()=>{
  await assertUnavailable(copy(original),{stallFetch:true});
});
test('manifestation d’une question altérée rejetée',async()=>{
  await assertUnavailable(copy(original),{badManifest:true});
});
test('manifeste 64 falsifié refusé même avec 64 questions et JSON valide',async()=>{
  await assertUnavailable(copy(original),{badManifest64:true});
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
test('un JSON approuvé ne peut pas ouvrir la publication tant que le verrou JS est fermé',async()=>{
  await assertUnavailable(syntheticApproved());
});

test('agrégats exclusivement synthétiques : affichage des comptes sûrs',async()=>{
  const el=await mount(syntheticApproved(), {syntheticRelease:true});
  assert.match(el('results-state').textContent,/Résultats agrégés approuvés/);
  assert.equal(el('results-question-list').children.length,40);
  assert.equal(el('results-question-list').children[0].children.length,4);
});
test('petite cellule bloque tous les résultats, sans affichage partiel',async()=>{
  const data=syntheticApproved();
  data.surveys['nova-orientations-40-v1'].questions[0].counts=
    {pour:25,contre:5,sans_opinion:0};
  await assertUnavailable(data,{syntheticRelease:true});
});
test('question masquée : aucun total résiduel dans sa ligne',async()=>{
  const data=syntheticApproved();
  const row=data.surveys['nova-orientations-40-v1'].questions[0];
  row.status='suppressed';
  await assertUnavailable(data,{syntheticRelease:true});
  delete row.total;delete row.counts;
  const el=await mount(data,{syntheticRelease:true});
  assert.match(el('results-question-list').children[0].children[1].textContent,/Répartition masquée/);
});


// Tests sans réseau du véritable chargeur de corpus de la Boussole, exécutés
// par la CI Nova/Jekyll en plus des contrôles SHA-256 du questionnaire.
const boussoleSource = fs.readFileSync(path.join(NOVA, 'assets/boussole-electorale.js'), 'utf8');
const networkStart=boussoleSource.indexOf('  async function fetchLimitedBytes(url,maxBytes){');
const networkEnd=boussoleSource.indexOf('  async function fetchApprovedQuestionCorpus(){',networkStart);
assert.ok(networkStart>=0 && networkEnd>networkStart, 'Chargeur Boussole de production introuvable');
const realNetworkRoutine=boussoleSource.slice(networkStart,networkEnd);

function novaNetworkHarness(mockFetch) {
  let fire=null, cleaned=0, signal=null;
  const context={
    AbortController,
    setTimeout(fn,ms){ assert.equal(ms,20000); fire=fn; return 7; },
    clearTimeout(id){ assert.equal(id,7); cleaned++; },
    fetch(url,options){
      assert.equal(options.cache,'no-store');
      assert.equal(options.credentials,'omit');
      assert.ok(options.signal instanceof AbortSignal);
      signal=options.signal;
      return mockFetch(url,options);
    },
  };
  vm.runInNewContext(realNetworkRoutine+'\nthis.fetchLimitedBytes=fetchLimitedBytes;',context,
    {filename:'boussole-electorale.js',timeout:1000});
  return {
    run:(url='data/boussole-electorale-v2.json',max=65536)=>context.fetchLimitedBytes(url,max),
    expire(){assert.ok(fire,'temporisation non armée');fire();},
    get cleaned(){return cleaned;},
    get signal(){return signal;}
  };
}
function novaResponse(content,length=null){
  const bytes=new TextEncoder().encode(content).buffer;
  return {ok:true,headers:{get:()=>length},arrayBuffer:async()=>bytes};
}
test('Boussole réseau : réponse intègre et temporisation correctement libérée',async()=>{
  const h=novaNetworkHarness(async()=>novaResponse('abc','3'));
  assert.equal(new TextDecoder().decode(await h.run()),'abc');
  assert.equal(h.cleaned,1);
  assert.equal(h.signal.aborted,false);
});
test('Boussole réseau : Content-Length dangereux, refus avant lecture',async()=>{
  let bodyRead=false;
  const h=novaNetworkHarness(async()=>({ok:true,headers:{get:()=>String(65537)},
    arrayBuffer:async()=>{bodyRead=true;return new ArrayBuffer(3);}}));
  await assert.rejects(h.run(),/CORPUS_SIZE/);
  assert.equal(bodyRead,false);
  assert.equal(h.cleaned,1);
});
test('Boussole réseau : longueur malformée et corps vide refusés',async()=>{
  const bad=novaNetworkHarness(async()=>novaResponse('abc','3, 5'));
  await assert.rejects(bad.run(),/CORPUS_SIZE/);
  assert.equal(bad.cleaned,1);
  const empty=novaNetworkHarness(async()=>novaResponse(''));
  await assert.rejects(empty.run(),/CORPUS_SIZE/);
  assert.equal(empty.cleaned,1);
});
test('Boussole réseau : rejet après lecture de trop nombreux octets',async()=>{
  const h=novaNetworkHarness(async()=>novaResponse('x'.repeat(65537),'9'));
  await assert.rejects(h.run(),/CORPUS_SIZE/);
  assert.equal(h.cleaned,1);
});
test('Boussole réseau : limite exacte de 512 Kio pour les preuves',async()=>{
  const h=novaNetworkHarness(async()=>novaResponse('x'.repeat(524288)));
  assert.equal((await h.run('data/boussole-preuves-2026.json',524288)).byteLength,524288);
  assert.equal(h.cleaned,1);
});
test('Boussole réseau : erreur HTTP, nettoyage sans lecture du corps',async()=>{
  const h=novaNetworkHarness(async()=>({ok:false,headers:{get:()=>null},
    arrayBuffer:async()=>{throw Error('lecture interdite')}}));
  await assert.rejects(h.run(),/CORPUS_HTTP/);
  assert.equal(h.cleaned,1);
});
test('Boussole réseau : AbortController interrompt une connexion figée',async()=>{
  const h=novaNetworkHarness((_url,{signal})=>new Promise((_resolve,reject)=>{
    signal.addEventListener('abort',()=>reject(Object.assign(
      new Error('annulé'),{name:'AbortError'})),{once:true});
  }));
  const running=h.run();
  h.expire();
  await assert.rejects(running,e=>e.name==='AbortError');
  assert.equal(h.signal.aborted,true);
  assert.equal(h.cleaned,1);
});
test('Boussole réseau : AbortController interrompt aussi la lecture du corps',async()=>{
  const h=novaNetworkHarness(async(_url,{signal})=>({ok:true,headers:{get:()=>null},
    arrayBuffer:()=>new Promise((_resolve,reject)=>signal.addEventListener(
      'abort',()=>reject(Object.assign(new Error('annulé'),{name:'AbortError'})),{once:true}))}));
  const running=h.run();
  await new Promise(resolve=>setImmediate(resolve));
  h.expire();
  await assert.rejects(running,e=>e.name==='AbortError');
  assert.equal(h.cleaned,1);
});
test('Boussole réseau : nettoyage en cas de panne immédiate',async()=>{
  const h=novaNetworkHarness(async()=>{throw Error('hors ligne')});
  await assert.rejects(h.run(),/hors ligne/);
  assert.equal(h.cleaned,1);
});
