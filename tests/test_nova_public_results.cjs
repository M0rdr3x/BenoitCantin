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
  stallFetch = false, syntheticRelease = false, failFirstFetch = false,
  oversizedSnapshot = false, oversizedManifest = false, invalidChunk = false,
  malformedLength = false,
} = {}) {
  const elements = new Map();
  let rejectedOnce = false;
  const document = {
    readyState: 'complete',
    getElementById(id) {
      if (!elements.has(id)) {
        const element = new FakeElement(id);
        if (id === 'results-retry') element.hidden = true;
        elements.set(id, element);
      }
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
      if (failFirstFetch && !rejectedOnce &&
          url === 'data/resultats-sondages-publics-v1.json') {
        rejectedOnce = true;
        throw Error('initial network problem');
      }
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
      // Le client lit volontairement par flux : ne surtout pas fournir un
      // arrayBuffer()/json() facile qui contournerait le contrat de sécurité.
      const name = url.startsWith('data/') ? url.slice(5) : '';
      const body = (name === 'consultation-40-v1.json' ||
          name === 'sondage-questions-v1.json') &&
          !((badManifest && name === 'consultation-40-v1.json') ||
            (badManifest64 && name === 'sondage-questions-v1.json'))
        ? fs.readFileSync(path.join(NOVA,'data',name))
        : Buffer.from(JSON.stringify(fixtures[url]),'utf8');
      const isSnapshot = name === 'resultats-sondages-publics-v1.json';
      const isManifest = name === 'consultation-40-v1.json';
      const oversized = (isSnapshot && oversizedSnapshot) ||
                        (isManifest && oversizedManifest);
      const parts=oversized
        ? [Buffer.alloc(65530),Buffer.alloc(20),Buffer.from('should-not-read')]
        : [body.subarray(0,Math.floor(body.length/2)),
           body.subarray(Math.floor(body.length/2))];
      let cursor=0;
      return {
        ok:true,
        headers:{get: key => key.toLowerCase()==='content-length'
          ? (malformedLength && isSnapshot ? '12, 20' : null) : null},
        body:{getReader(){return {
          async read(){
            if(cursor>=parts.length)return {done:true};
            if(invalidChunk && isSnapshot)return {done:false,value:new Int16Array([42])};
            return {done:false,value:parts[cursor++]};
          },
          releaseLock(){}
        };}},
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
test('réessayer après panne : aucune fuite, restauration 40/64 sans faux chiffres',async()=>{
  const el=await mount(copy(original),{failFirstFetch:true});
  assert.equal(el('results-retry').hidden,false);
  assert.equal(el('results-retry').disabled,false);
  assert.match(el('results-state').textContent,/indisponibles ou non validées/);
  assert.equal(el('results-question-list').children.length,1);
  el('results-show-64').click();
  el('results-retry').click();
  assert.equal(el('results-retry').disabled,true);
  for (let n=0;n<200 && el('results-retry').disabled;n++) {
    await new Promise(resolve=>setTimeout(resolve,10));
  }
  assert.equal(el('results-retry').disabled,false,'Le second chargement reste figé');
  assert.equal(el('results-retry').hidden,true);
  assert.equal(el('results-question-list').children.length,64);
  assert.match(el('results-state').textContent,/Aucun résultat publié/);
  assert.equal(el('results-show-64').attributes['aria-pressed'],'true');
  assert.ok(el('results-question-list').children.every(item=>item.children.length===2));
});
test('réessai d’une panne persistante : bouton maintenu et zéro résultat',async()=>{
  const el=await mount(copy(original),{fetchFailure:true});
  el('results-retry').click();
  for (let n=0;n<200 && el('results-retry').disabled;n++) {
    await new Promise(resolve=>setTimeout(resolve,10));
  }
  assert.equal(el('results-retry').hidden,false);
  assert.equal(el('results-question-list').children.length,1);
  assert.match(el('results-state').textContent,/indisponibles ou non validées/);
});
test('connexion bloquée : timeout, annulation et indisponibilité sans résultats',async()=>{
  await assertUnavailable(copy(original),{stallFetch:true});
});
test('snapshot surdimensionné interrompu avant décodage ou publication',async()=>{
  await assertUnavailable(copy(original),{oversizedSnapshot:true});
});
test('manifeste surdimensionné interrompu avant vérification SHA-256',async()=>{
  await assertUnavailable(copy(original),{oversizedManifest:true});
});
test('en-tête Content-Length ambigu et segment non octet refusés',async()=>{
  await assertUnavailable(copy(original),{malformedLength:true});
  await assertUnavailable(copy(original),{invalidChunk:true});
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


// Recette déterministe sans réseau : fonction réseau RÉELLE extraite du client
// Boussole. Les chunks sont simulés en mémoire sans opinions ni attente de 20 s.
const boussoleSource=fs.readFileSync(path.join(NOVA,'assets/boussole-electorale.js'),'utf8');
const networkStart=boussoleSource.indexOf('  async function fetchLimitedBytes(url,maxBytes){');
const networkEnd=boussoleSource.indexOf('  async function fetchApprovedQuestionCorpus(){',networkStart);
assert.ok(networkStart>=0 && networkEnd>networkStart,'Chargeur Boussole de production introuvable');
const realNetworkRoutine=boussoleSource.slice(networkStart,networkEnd);

function novaNetworkHarness(mockFetch){
  let fire=null,cleaned=0,signal=null;
  const context={
    AbortController,
    setTimeout(fn,ms){assert.equal(ms,20000);fire=fn;return 7;},
    clearTimeout(id){assert.equal(id,7);cleaned++;},
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
function novaResponse(chunks,declared=null){
  const payloads=chunks.map(text=>new TextEncoder().encode(text));
  let next=0,released=0,readCount=0;
  const response={
    ok:true,headers:{get:()=>declared},
    body:{getReader(){return {
      async read(){
        readCount++;
        if(next<payloads.length)return {done:false,value:payloads[next++]};
        return {done:true,value:undefined};
      },
      releaseLock(){released++;},
    };}},
  };
  return {
    response,
    get released(){return released;},
    get readCount(){return readCount;},
  };
}
test('Boussole flux : deux segments concaténés et temporisation libérée',async()=>{
  const fixture=novaResponse(['ab','cd'],'4');
  const h=novaNetworkHarness(async()=>fixture.response);
  assert.equal(new TextDecoder().decode(await h.run()),'abcd');
  assert.equal(fixture.released,1);
  assert.equal(h.cleaned,1);
  assert.equal(h.signal.aborted,false);
});
test('Boussole flux : Content-Length trop grand refusé AVANT lecture',async()=>{
  const fixture=novaResponse(['abc'],'65537');
  const h=novaNetworkHarness(async()=>fixture.response);
  await assert.rejects(h.run(),/CORPUS_SIZE/);
  assert.equal(fixture.readCount,0);
  assert.equal(h.cleaned,1);
});
test('Boussole flux : longueur malformée et corps vide refusés',async()=>{
  const bad=novaResponse(['abc'],'3, 5');
  const h=novaNetworkHarness(async()=>bad.response);
  await assert.rejects(h.run(),/CORPUS_SIZE/);
  assert.equal(bad.readCount,0);
  const empty=novaResponse([]);
  const noData=novaNetworkHarness(async()=>empty.response);
  await assert.rejects(noData.run(),/CORPUS_SIZE/);
  assert.equal(empty.released,1);
  assert.equal(h.cleaned,1);
  assert.equal(noData.cleaned,1);
});
test('Boussole flux : sans Content-Length, dépassement arrêté avant segment suivant',async()=>{
  const fixture=novaResponse(['x'.repeat(65000),'x'.repeat(500),'x'.repeat(2000),'jamais lu']);
  const h=novaNetworkHarness(async()=>fixture.response);
  await assert.rejects(h.run(),/CORPUS_SIZE/);
  assert.equal(fixture.readCount,3);
  assert.equal(fixture.released,1);
  assert.equal(h.signal.aborted,true);
  assert.equal(h.cleaned,1);
});
test('Boussole flux : limite exacte 512 Kio acceptée pour les preuves',async()=>{
  const fixture=novaResponse(['x'.repeat(262144),'y'.repeat(262144)]);
  const h=novaNetworkHarness(async()=>fixture.response);
  assert.equal((await h.run('data/boussole-preuves-2026.json',524288)).byteLength,524288);
  assert.equal(fixture.released,1);
  assert.equal(h.cleaned,1);
});
test('Boussole flux : erreur HTTP ne lit aucun octet',async()=>{
  const fixture=novaResponse(['abc']);
  fixture.response.ok=false;
  const h=novaNetworkHarness(async()=>fixture.response);
  await assert.rejects(h.run(),/CORPUS_HTTP/);
  assert.equal(fixture.readCount,0);
  assert.equal(h.cleaned,1);
});
test('Boussole flux : corps sans lecteur sécurisé refusé',async()=>{
  const h=novaNetworkHarness(async()=>({ok:true,headers:{get:()=>null},body:null}));
  await assert.rejects(h.run(),/CORPUS_STREAM/);
  assert.equal(h.cleaned,1);
});
test('Boussole flux : AbortController interrompt la connexion figée',async()=>{
  const h=novaNetworkHarness((_url,{signal})=>new Promise((_resolve,reject)=>{
    signal.addEventListener('abort',()=>reject(Object.assign(
      new Error('annulé'),{name:'AbortError'})),{once:true});
  }));
  const pending=h.run();h.expire();
  await assert.rejects(pending,e=>e.name==='AbortError');
  assert.equal(h.signal.aborted,true);
  assert.equal(h.cleaned,1);
});
test('Boussole flux : annulation pendant la lecture d’un segment',async()=>{
  let freed=0;
  const h=novaNetworkHarness(async(_url,{signal})=>({
    ok:true,headers:{get:()=>null},
    body:{getReader(){return {
      read:()=>new Promise((_resolve,reject)=>signal.addEventListener(
        'abort',()=>reject(Object.assign(new Error('annulé'),{name:'AbortError'})),{once:true})),
      releaseLock(){freed++;},
    };}}
  }));
  const pending=h.run();
  await new Promise(resolve=>setImmediate(resolve));
  h.expire();
  await assert.rejects(pending,e=>e.name==='AbortError');
  assert.equal(freed,1);
  assert.equal(h.cleaned,1);
});
test('Boussole flux : erreur réseau et libération du minuteur',async()=>{
  const h=novaNetworkHarness(async()=>{throw Error('hors ligne')});
  await assert.rejects(h.run(),/hors ligne/);
  assert.equal(h.cleaned,1);
});


// Corpus des sondages 40 et 64 : exécuter la vraie lecture incrémentale
// et démontrer qu'aucun corps JSON massif n'est alloué avant la limite.
function novaSurveyManifestHarness(file,chunks,header=null){
  const client=fs.readFileSync(path.join(NOVA,'assets',file),'utf8');
  const start=client.indexOf('  async function readBoundedManifest(response,controller){');
  const end=client.indexOf('\n  }\n',start);
  assert.ok(start>=0 && end>start,file+': fonction de lecture bornée absente');
  const context={};
  vm.runInNewContext(client.slice(start,end+5)+'\nthis.readBoundedManifest=readBoundedManifest;',
    context,{filename:file,timeout:1000});
  let readCount=0,released=0,aborted=false;
  const response={headers:{get:key=>key==='content-length'?header:null},
    body:{getReader(){return {
      async read(){
        readCount++;
        if(readCount>chunks.length) return {done:true};
        return {done:false,value:new TextEncoder().encode(chunks[readCount-1])};
      },
      releaseLock(){released++;},
    };}}};
  return {
    run:()=>context.readBoundedManifest(response,{abort(){aborted=true;}}),
    get readCount(){return readCount;},
    get released(){return released;},
    get aborted(){return aborted;},
  };
}
for(const file of ['consultation-40.js','sondage.js']){
  test(file+' : téléchargement fragmenté reconstitué sans altération',async()=>{
    const fixture=novaSurveyManifestHarness(file,['{"id":','"nova"}'],'13');
    const bytes=await fixture.run();
    assert.equal(Buffer.from(new Uint8Array(bytes)).toString('utf8'),'{"id":"nova"}');
    assert.equal(fixture.released,1);
    assert.equal(fixture.aborted,false);
  });
  test(file+' : dépassement au troisième segment, sans quatrième lecture',async()=>{
    const fixture=novaSurveyManifestHarness(file,
      ['x'.repeat(65000),'y'.repeat(500),'z'.repeat(2000),'NE JAMAIS LIRE']);
    await assert.rejects(fixture.run(),/SIZE/);
    assert.equal(fixture.readCount,3);
    assert.equal(fixture.released,1);
    assert.equal(fixture.aborted,true);
  });
  test(file+' : en-tête Content-Length excessif refusé sans lecture',async()=>{
    const fixture=novaSurveyManifestHarness(file,['INATTEIGNABLE'],'65537');
    await assert.rejects(fixture.run(),/SIZE/);
    assert.equal(fixture.readCount,0);
    assert.equal(fixture.released,0);
  });
  test(file+' : fichier vide refusé, lecteur libéré',async()=>{
    const fixture=novaSurveyManifestHarness(file,[]);
    await assert.rejects(fixture.run(),/SIZE/);
    assert.equal(fixture.released,1);
  });
}
