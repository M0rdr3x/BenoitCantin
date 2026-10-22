#!/usr/bin/env node
'use strict';
// Exercices du vrai sw.js via vm, sans navigateur, npm ni service externe.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SW_PATH = path.resolve(__dirname, '../sw.js');
const source = fs.readFileSync(SW_PATH, 'utf8');
const listeners = new Map();
const origin = 'https://www.benoitcantin.com';
const requests = [];
const writes = [];
const deletes = [];
const matches = [];
const publicEntries = new Map();
let globalLookups = 0;
const responseHeaders = new Map();
let networkFails = false;
let currentCache;

const cache = {
  async addAll(paths) { for (const p of paths) assert.ok(p.startsWith('/')); },
  async put(r, response) {
    assert.ok(response.ok, 'Only successful responses are cached');
    const pathname = new URL(r.url).pathname;
    writes.push(pathname);
    publicEntries.set(pathname, response.clone());
  },
  async match(r) {
    const pathname = typeof r === 'string' ? r : new URL(r.url).pathname;
    matches.push(pathname);
    return publicEntries.get(pathname);
  },
};
const storage = {
  async open(key) { currentCache = key; return cache; },
  async match(request) {
    // CacheStorage.match() peut retourner des données venant d'une AUTRE PWA.
    // Le code de production ne doit jamais appeler cette méthode globale.
    globalLookups += 1;
    return new Response('DONNEE PRIVEE CACHE TIERS', { status: 200 });
  },
  async keys() { return ['benoitcantin-v24-4-95-public-4', 'benoitcantin-v24-4-95-public-5', 'other-product-cache', currentCache]; },
  async delete(key) { deletes.push(key); return true; },
};
const environment = {
  URL, Request, Response, Set, Promise, console,
  location: { origin },
  caches: storage,
  self: {
    addEventListener(type, fn) { listeners.set(type, fn); },
    skipWaiting: async () => {},
    clients: { claim: async () => {} },
  },
  async fetch(r) {
    requests.push({ path: new URL(r.url).pathname, cache: r.cache, credentials: r.credentials });
    if (networkFails) throw new Error('network offline');
    const uri = new URL(r.url);
    const headers = responseHeaders.get(uri.pathname) || {};
    return new Response('public test', { status: 200, headers });
  },
};
vm.runInNewContext(source, environment, { filename: SW_PATH, timeout: 2500 });
assert.deepEqual([...listeners.keys()].sort(), ['activate', 'fetch', 'install']);

async function event(type) {
  let waited;
  listeners.get(type)({ waitUntil(p) { waited = p; } });
  await waited;
}
async function request(uri, options = {}, destination = '') {
  const url = uri.startsWith('http') ? uri : origin + uri;
  const req = new Request(url, options);
  if (destination) Object.defineProperty(req, 'destination', { value: destination });
  let responded;
  const background = [];
  listeners.get('fetch')({
    request: req,
    respondWith(p) { responded = p; },
    waitUntil(p) { background.push(p); },
  });
  assert.ok(responded, 'Same-origin GET must be handled by SW');
  const response = await responded;
  await Promise.all(background);
  return response;
}
async function test() {
  await event('install');
  assert.ok(requests.length >= 35, 'Expected the real public CORE resources to be prefetched');
  assert.ok(requests.every(r => r.credentials === 'omit' && r.cache === 'no-store'),
    'Prefetch must never carry cookies or reuse a personalized browser cache');
  assert.equal(writes.length, requests.length, 'Only vetted public responses were precached');
  // Une seule réponse privée doit invalider l'installation au lieu d'être cachée.
  responseHeaders.set('/', { 'Cache-Control': 'private, no-store' });
  await assert.rejects(event('install'), /non publique interdite/);
  responseHeaders.delete('/');
  // Le chargement initial doit aussi être refusé si une seule ressource
  // publique n'autorise pas une réutilisation déterministe du cache.
  responseHeaders.set('/', { 'Vary': '*' });
  await assert.rejects(event('install'), /non publique interdite/,
    'Vary: * must invalidate the complete pre-cache installation');
  responseHeaders.delete('/');
  writes.length = 0;
  requests.length = 0;
  await event('activate');
  assert.ok(deletes.includes('benoitcantin-v24-4-95-public-4'));
  assert.ok(deletes.includes('benoitcantin-v24-4-95-public-5'),
    'The prior weaker Vary-policy cache must be evicted on activation');
  assert.ok(!deletes.includes('other-product-cache'), 'Foreign caches must survive');

  // Refus de précacher une nouvelle route privée même si quelqu'un l'ajoute à CORE.
  const mutated = source.replace('const CORE=[', "const CORE=['/api/v1/private',");
  assert.notEqual(mutated, source);
  const malformedListeners = new Map();
  vm.runInNewContext(mutated, {
    ...environment,
    self: {
      ...environment.self,
      addEventListener(type, fn) { malformedListeners.set(type, fn); },
    },
  }, { filename: 'sw-with-forbidden-precache.js', timeout: 2500 });
  let rejectedInstall;
  malformedListeners.get('install')({ waitUntil(p) { rejectedInstall = p; } });
  await assert.rejects(rejectedInstall, /Chemin privé interdit/);

  const forbidden = [
    '/.well-known/sinjira-pages-release.json',
    '/.well-known/release.json', '/api/v1/account', '/auth/v1/user',
    '/functions/v1/profile', '/storage/v1/private', '/supabase/config.toml',
    '/compte/index.html', '/Admin/sinjira/', '/admin/', '/app/',
    '/projets/sinjira/codex/livre-i-delivery-contract.json',
    '/projets/projet-nova/data/boussole-preuves-2026.json',
  ];
  for (const pathname of forbidden) {
    const before = writes.length, lookedUp = matches.length;
    const result = await request(pathname);
    assert.equal(result.status, 200);
    assert.equal(writes.length, before, pathname + ' was cached');
    assert.equal(matches.length, lookedUp, pathname + ' read a cache');
    assert.equal(requests.at(-1).cache, 'no-store', pathname + ' not forced network-only');
  }

  // Proof must never be served from the old cache, even when offline.
  networkFails = true;
  await assert.rejects(request('/.well-known/sinjira-pages-release.json'));
  networkFails = false;

  // Les questionnaires et leurs données exigent le réseau, jamais un écran
  // obsolète depuis le cache PWA après une mise à jour de publication.
  const surveyRoutes = [
    '/projets/projet-nova/consultation-40.html',
    '/projets/projet-nova/sondage.html',
    '/projets/projet-nova/assets/consultation-40.js',
    '/projets/projet-nova/assets/sondage.js',
    '/projets/projet-nova/assets/sondage.css',
    '/projets/projet-nova/data/consultation-40-v1.json',
    '/projets/projet-nova/data/sondage-questions-v1.json',
    '/projets/projet-nova/resultats-sondages.html',
    '/projets/projet-nova/assets/resultats-sondages.js',
    '/projets/projet-nova/data/resultats-sondages-publics-v1.json',
  ];
  for (const url of surveyRoutes) {
    const beforeWrites = writes.length, beforeMatches = matches.length;
    const destination = url.endsWith('.html') ? 'document' : '';
    assert.equal((await request(url, {}, destination)).status, 200);
    assert.equal(requests.at(-1).cache, 'no-store', url + ' must be network only');
    assert.equal(writes.length, beforeWrites, url + ' should never enter PWA cache');
    assert.equal(matches.length, beforeMatches, url + ' should never read stale cache');
    networkFails = true;
    await assert.rejects(request(url, {}, destination));
    networkFails = false;
  }

  // Assets from the pinned public set are cached, but not credentials or tokens.
  await request('/assets/js/site.js');
  assert.deepEqual(writes, ['/assets/js/site.js']);
  assert.equal(requests.at(-1).credentials, 'omit',
    'Public static resources must be fetched without cookies');
  // Les documents de navigation restent fonctionnels, mais leurs réponses
  // peuvent être personnalisées : aucune écriture dans le cache.
  const navigationWrites = writes.length;
  await request('/projets/sinjira/', {}, 'document');
  assert.equal(writes.length, navigationWrites, 'Personalized navigation was cached');
  assert.equal(requests.at(-1).credentials, 'same-origin',
    'Navigation should still preserve session to render the current page');

  // Même si le domaine possède un cache tiers contenant une copie sensible,
  // le fallback offline lit uniquement le cache PUBLIC contrôlé.
  networkFails = true;
  const offlineNavigation = await request('/projets/sinjira/', {}, 'document');
  assert.equal(await offlineNavigation.text(), 'public test',
    'Offline navigation must come from this PWA public cache, never another app');
  const ownPublicAsset = await request('/assets/js/site.js');
  assert.equal(await ownPublicAsset.text(), 'public test',
    'Offline JS must come exclusively from the active cache');
  publicEntries.delete('/assets/js/site.js');
  const missingOwnAsset = await request('/assets/js/site.js');
  assert.equal(missingOwnAsset, undefined,
    'A missing own-cache asset must not be served from a foreign cache');
  assert.equal(globalLookups, 0, 'Global caches.match must never read third-party caches');
  networkFails = false;

  const n1 = writes.length;
  await request('/assets/js/site.js?token=private');
  assert.equal(writes.length, n1, 'URLs carrying tokens must not be cached');
  await request('/assets/js/site.js', { headers: { Authorization: 'Bearer fake' } });
  assert.equal(writes.length, n1, 'Authorized responses must not be cached');
  await request('/assets/js/site.js', { headers: { Cookie: 'session=dummy' } });
  assert.equal(writes.length, n1, 'Cookie-bearing requests must not be cached');

  responseHeaders.set('/assets/js/site.js', { 'Cache-Control': 'private, max-age=60' });
  await request('/assets/js/site.js');
  assert.equal(writes.length, n1, 'Cache-Control private must be honored');
  responseHeaders.set('/assets/js/site.js', { 'Vary': 'Cookie, Accept-Encoding' });
  await request('/assets/js/site.js');
  assert.equal(writes.length, n1, 'Vary: Cookie must block cache');
  for (const vary of [
    'Cookie , Accept-Encoding',
    'Accept-Encoding, Authorization ',
    '*',
    'Accept-Encoding, * ',
  ]) {
    responseHeaders.set('/assets/js/site.js', { 'Vary': vary });
    const before = writes.length;
    await request('/assets/js/site.js');
    assert.equal(writes.length, before,
      'Vary header forbids response caching: ' + vary);
  }
  responseHeaders.set('/assets/js/site.js', { 'Set-Cookie': 's=foo' });
  await request('/assets/js/site.js');
  assert.equal(writes.length, n1, 'Set-Cookie must block cache');
  responseHeaders.delete('/assets/js/site.js');

  // No non-GET or third-party request should be intercepted.
  let handled = false;
  listeners.get('fetch')({
    request: new Request(origin + '/assets/js/site.js', { method: 'POST' }),
    respondWith() { handled = true; },
  });
  assert.equal(handled, false);
  listeners.get('fetch')({
    request: new Request('https://other.example/assets/js/site.js'),
    respondWith() { handled = true; },
  });
  assert.equal(handled, false);

  assert.equal(globalLookups, 0, 'No cross-application cache lookup is allowed');
  assert.ok(/-public-6/.test(currentCache), 'Cache version must rotate');
  console.log('OK PWA: réseaux privés et release non cachés, allowlist statique, protections Cookie/Auth/Vary et isolation des caches.');
}
test().catch(error => { console.error(error); process.exitCode = 1; });
