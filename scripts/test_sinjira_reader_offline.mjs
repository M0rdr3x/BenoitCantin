#!/usr/bin/env node
// Intégration locale DOM simulée : le PDF gratuit doit survivre à une panne
// Supabase et respecter le contrat 84 pages sans exposer l'édition intégrale.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync('assets/js/sinjira-reader.js', 'utf8')
  .replace(/^import \{[^\n]+\} from '[^']+';\n/m, '')
  .replace('(async()=>{', 'globalThis.__readerDone=(async()=>{');
const html = readFileSync('projets/sinjira/romans/lire-demo.html', 'utf8');
const contract = JSON.parse(readFileSync(
  'projets/sinjira/codex/livre-i-delivery-contract.json', 'utf8',
));
const maxPages = contract.demo.pages;

assert.equal(maxPages, 84, 'Le contrat démo de ce candidat exige 84 pages');
assert.equal(contract.publication_state, 'not_activated');
assert.equal(contract.full_edition.public_static_url_allowed, false);
assert.match(html, new RegExp('data-reader-total-pages="' + maxPages + '"'));
assert.match(html, new RegExp('data-reader-page-number[^>]*max="' + maxPages + '"'));
assert.doesNotMatch(source, /(?:\/83\b|Math\.min\(83\b)/);

function node() {
  const listeners = new Map();
  return {
    style: {},
    listeners,
    addEventListener(type, listener) {listeners.set(type, listener);},
    click() {const cb = listeners.get('click');assert.ok(cb, 'Bouton non raccordé');return cb();},
    change(value) {
      this.value = value;
      const cb = listeners.get('change');
      assert.ok(cb, 'Champ non raccordé');
      return cb();
    },
    textContent: '',
    value: 1,
    max: '',
    src: '',
    hidden: false,
    dataset: {},
  };
}

async function scenario({ auth = 'offline', persisted = '83', blockedStorage = false }) {
  const controls = new Map();
  for(const selector of [
    '[data-pdf-reader]', '[data-reader-page-number]', '[data-reader-progress-bar]',
    '[data-reader-progress-native]', '[data-reader-resume]', '[data-reader-prev]',
    '[data-reader-next]', '[data-reader-bookmark]', '[data-reader-status]',
  ]) controls.set(selector, node());
  const writes = [];
  let forbiddenRemoteCalls = 0;
  const storage = {
    getItem() { if(blockedStorage)throw new Error('stockage bloqué');return persisted; },
    setItem(key,value) {
      if(blockedStorage)throw new Error('stockage bloqué');
      writes.push({key,value});
    },
  };
  const context = {
    document: {
      body: { dataset: {readerPage: 'demo',novelSlug: 'la-cendre-du-jugement',readerTotalPages: String(maxPages)} },
      querySelector(selector) {return controls.get(selector) ?? null;},
    },
    localStorage: storage,
    getCurrentUser: async () => {
      if(auth === 'offline')throw new Error('réseau indisponible');
      if(auth === 'anon')return null;
      return {id:'u1'};
    },
    getSupabase: () => {
      forbiddenRemoteCalls++;
      if(auth === 'signed-offline')throw new Error('backend indisponible');
      throw new Error('accès réseau imprévu dans la lecture publique');
    },
    escapeHtml: x => String(x),
    formatDate: x => String(x),
  };
  vm.runInNewContext(source, context, {filename:'sinjira-reader.js', timeout:2000});
  await context.__readerDone;
  const element = selector => controls.get(selector);
  const frame = element('[data-pdf-reader]');
  assert.ok(frame.src.includes('SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf#page='),
    'Le lecteur doit charger uniquement le PDF public de démo');
  const initialPage = blockedStorage ? 1 : Math.min(maxPages,Math.max(1,Number(persisted)||1));
  assert.ok(frame.src.includes('#page=' + initialPage + '&'));
  element('[data-reader-page-number]').change('999');
  assert.ok(frame.src.includes('#page=' + maxPages + '&'), 'Dépassement de la dernière page');
  element('[data-reader-next]').click();
  assert.ok(frame.src.includes('#page=' + maxPages + '&'), 'Page suivante au-delà du PDF');
  element('[data-reader-prev]').click();
  assert.ok(frame.src.includes('#page=' + (maxPages-1) + '&'), 'Page précédente incorrecte');
  assert.equal(Number(element('[data-reader-progress-native]').max),maxPages);
  assert.equal(element('[data-reader-progress-native]').textContent,
    (maxPages-1) + ' sur ' + maxPages);
  element('[data-reader-bookmark]').click();
  if(!blockedStorage) {
    assert.deepEqual(writes,[{key:'sinjira-reader-la-cendre-du-jugement',value:String(maxPages-1)}]);
  }
  assert.equal(forbiddenRemoteCalls, auth === 'signed-offline' ? 1 : 0,
    'Les visiteurs non authentifiés ne doivent pas accéder à la base');
  return true;
}

await scenario({auth:'offline',persisted:'83'});
await scenario({auth:'anon',persisted:'999'});
await scenario({auth:'signed-offline',persisted:'83'});
await scenario({auth:'offline',persisted:'bad-number'});
await scenario({auth:'offline',persisted:'83',blockedStorage:true});
console.log('OK lecteur public : 84 pages, bornes de navigation, progression locale et pannes Supabase/stockage.');
