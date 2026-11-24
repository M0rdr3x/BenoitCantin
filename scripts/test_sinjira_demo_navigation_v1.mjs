#!/usr/bin/env node
import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeDemoPage, startDemoNavigation } from '../assets/js/sinjira-demo-navigation-v1.mjs';

function element(initial = {}) {
  const handlers = {};
  const attrs = { ...(initial.attributes || {}) };
  return {
    ...initial,
    handlers, style: {}, disabled: false,
    addEventListener(name, handler) { handlers[name] = handler; },
    getAttribute(name) { return attrs[name] ?? null; },
    setAttribute(name, value) { attrs[name] = String(value); this.loads = (this.loads || 0) + 1; },
    fire(name, extras = {}) { handlers[name]?.({ target: this, preventDefault() {}, ...extras }); }
  };
}
function fixture({ saved = null, storageProvider = null, onBookmark = async () => false } = {}) {
  const map = new Map(saved === null ? [] : [['sinjira-reader-la-cendre', String(saved)]]);
  const storage = { getItem: key => map.get(key) ?? null, setItem: (key, value) => map.set(key, value) };
  const els = Object.fromEntries([
    '[data-reader-page-number]', '[data-reader-progress-bar]', '[data-reader-progress-native]',
    '[data-reader-resume]', '[data-reader-prev]', '[data-reader-next]',
    '[data-reader-bookmark]', '[data-reader-controls]'
  ].map(name => [name, element()]));
  const frame = element({ attributes: { src: '../documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf#page=1&zoom=page-width&view=FitH' } });
  const reader = startDemoNavigation({
    document: { querySelector: selector => els[selector] }, frame, slug: 'la-cendre', totalPages: 82,
    storageProvider: storageProvider || (() => storage), onBookmark
  });
  return { reader, els, frame, map };
}

test('les numéros invalides et extrêmes sont ramenés dans 1–82', () => {
  assert.equal(normalizeDemoPage('abc', 82, 6), 6);
  assert.equal(normalizeDemoPage('', 82, 6), 6);
  assert.equal(normalizeDemoPage('1.5', 82, 6), 6);
  assert.equal(normalizeDemoPage('0', 82), 1);
  assert.equal(normalizeDemoPage('999', 82), 82);
});

test('la première page n’entraîne aucun rechargement superflu du PDF', () => {
  const { frame, els } = fixture();
  assert.equal(frame.loads || 0, 0);
  assert.equal(els['[data-reader-prev]'].disabled, true);
  assert.equal(els['[data-reader-next]'].disabled, false);
});

test('navigation clavier/boutons et stockage local fonctionnent sans compte', () => {
  const { reader, els, map, frame } = fixture();
  els['[data-reader-next]'].fire('click');
  assert.equal(reader.currentPage, 2);
  assert.equal(map.get('sinjira-reader-la-cendre'), '2');
  assert.match(frame.getAttribute('src'), /#page=2&/);
  els['[data-reader-controls]'].fire('keydown', { key: 'ArrowLeft', target: { closest: () => null } });
  assert.equal(reader.currentPage, 1);
  els['[data-reader-controls]'].fire('keydown', { key: 'ArrowRight', target: { closest: () => true } });
  assert.equal(reader.currentPage, 1);
});

test('page saisie: conserver la position si valeur invalide et borner à 82', () => {
  const { reader, els } = fixture({ saved: 12 });
  assert.equal(reader.currentPage, 12);
  const input = els['[data-reader-page-number]'];
  input.value = 'abc'; input.fire('change');
  assert.equal(reader.currentPage, 12);
  assert.equal(input.value, '12');
  input.value = '300'; input.fire('change');
  assert.equal(reader.currentPage, 82);
  assert.equal(els['[data-reader-next]'].disabled, true);
});

test('le lecteur reste utilisable si le stockage local est bloqué', () => {
  const { reader, els } = fixture({ storageProvider: () => { throw Error('blocked'); } });
  els['[data-reader-next]'].fire('click');
  assert.equal(reader.currentPage, 2);
});

test('une réponse de compte tardive ne remplace pas une page changée', () => {
  const { reader } = fixture({ saved: 4 });
  assert.equal(reader.restoreRemotePage(9), true);
  assert.equal(reader.currentPage, 9);
  reader.setPage(10);
  assert.equal(reader.restoreRemotePage(2), false);
  assert.equal(reader.currentPage, 10);
});

test('marque-page : retour explicite de la synchronisation et protection double clic', async () => {
  let resolve;
  const deferred = new Promise(r => { resolve = r; });
  let calls = 0;
  const { els } = fixture({ onBookmark: async () => { calls++; await deferred; return true; } });
  const bookmark = els['[data-reader-bookmark]'];
  bookmark.fire('click');
  assert.equal(bookmark.disabled, true);
  bookmark.fire('click');
  assert.equal(calls, 1);
  resolve();
  await new Promise(r => setImmediate(r));
  assert.equal(bookmark.disabled, false);
  assert.match(els['[data-reader-resume]'].textContent, /dans votre compte/);
});

test('échec du service : confirmation locale plutôt que fausse synchronisation', async () => {
  const { els } = fixture({ onBookmark: async () => { throw Error('offline'); } });
  els['[data-reader-bookmark]'].fire('click');
  await new Promise(r => setImmediate(r));
  assert.match(els['[data-reader-resume]'].textContent, /Synchronisation indisponible/);
});

test('le lecteur annonce si le stockage privé interdit une sauvegarde', async () => {
  const { els } = fixture({ storageProvider: () => { throw Error('blocked'); } });
  els['[data-reader-bookmark]'].fire('click');
  await new Promise(r => setImmediate(r));
  assert.match(els['[data-reader-resume]'].textContent, /stockage local indisponible/);
});

test('le démarrage de la démo ne dépend pas du CDN Supabase', async () => {
  const {readFileSync} = await import('node:fs');
  const bootstrap = readFileSync(new URL('../assets/js/sinjira-demo-bootstrap-v1.mjs', import.meta.url), 'utf8');
  const html = readFileSync(new URL('../projets/sinjira/romans/lire-demo.html', import.meta.url), 'utf8');
  assert.ok(bootstrap.includes("import {startDemoNavigation} from './sinjira-demo-navigation-v1.mjs'"));
  assert.ok(bootstrap.includes("await import('./sinjira-supabase.js')"));
  assert.ok(!bootstrap.includes("import {getSupabase"));
  assert.ok(!html.includes('sinjira-demo-bootstrap-v1.mjs?v='));
  assert.ok(html.includes('data-reader-page="demo-pending"'));
  assert.ok(html.includes('62 pages'));
  assert.ok(!html.includes('sinjira-reader.js?v='));
});
