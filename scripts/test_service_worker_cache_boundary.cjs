#!/usr/bin/env node
// Tests synthétiques du vrai service worker, sans serveur ni données privées.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const SOURCE = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');
const ORIGIN = 'https://www.benoitcantin.com';

function harness(responseFor = () => new Response('public', {status: 200}), cacheNames = [], cacheHit = () => undefined) {
  const listeners = {};
  const puts = [];
  const matches = [];
  const globalMatches = [];
  const deletes = [];
  const fetches = [];
  const cache = {
    put: async (req, resp) => { puts.push({url: req.url, status: resp.status}); },
    match: async req => { matches.push(String(req.url || req)); return cacheHit(req); },
  };
  const caches = {
    open: async () => cache,
    match: async req => { globalMatches.push(String(req.url || req)); throw new Error('CacheStorage.match global interdit'); },
    keys: async () => cacheNames,
    delete: async name => { deletes.push(name); return true; },
  };
  const self = {
    addEventListener: (name, listener) => { listeners[name] = listener; },
    skipWaiting: async () => {},
    clients: {claim: async () => {}},
  };
  const context = {
    self, caches, location: {origin: ORIGIN},
    URL, Request, Response, Headers,
    fetch: async req => { fetches.push(req); return responseFor(req); },
  };
  vm.runInNewContext(SOURCE + '\n;globalThis.__test = {cacheableResponse,isPrivatePath,isPublicCachePath,CORE,CACHE};', context, {filename: 'sw.js'});
  return {listeners, puts, matches, globalMatches, deletes, fetches, ...context.__test};
}

function request(url, options) {
  return new Request(new URL(url, ORIGIN), options);
}
function response(headers = {}) {
  return new Response('synthetic', {status: 200, headers});
}
function eventFor(req) {
  return {
    request: req,
    respondWith(promise) { this.result = promise; },
    waitUntil(promise) { this.done = promise; },
  };
}

test('seuls les chemins publics explicites et les médias statiques sont persistables', () => {
  const sw = harness();
  for (const p of ['/compte/', '/Admin/index.html', '/admin/', '/app/', '/administration.html',
    '/histoire-de-vie/index.html', '/supabase/', '/api/user', '/auth/session',
    '/.netlify/functions/private']) {
    assert.equal(sw.isPrivatePath(p), true, p);
    assert.equal(sw.isPublicCachePath(p), false, p);
  }
  for (const p of ['/api/profile.json', '/user/info', '/projets/sinjira/documents/private.pdf',
    '/projets/projet-nova/data/ballots.json', '/unknown.html', '/.env.js']) {
    assert.equal(sw.isPublicCachePath(p), false, p);
  }
  for (const p of ['/assets/js/site.js', '/assets/media/logo.webp', '/projets/sinjira/jeux/game.mjs', '/']) {
    assert.equal(sw.isPublicCachePath(p), true, p);
  }
  assert.ok(sw.CACHE.startsWith('benoitcantin-'));
  assert.ok(sw.CORE.every(p => !sw.isPrivatePath(p) && sw.isPublicCachePath(p) && !p.includes('?')));
});

test('Cache-Control private et directives sensibles ne sont jamais persistés', () => {
  const sw = harness();
  const r = request('/assets/js/site.js', {credentials: 'omit'});
  assert.equal(sw.cacheableResponse(r, response({'Cache-Control': 'public, max-age=600'})), true);
  for (const h of [
    {'Cache-Control': 'private, max-age=3600'},
    {'Cache-Control': 'max-age=600, no-store'},
    {'Cache-Control': 'no-cache'},
    {'Cache-Control': 'private="Set-Cookie"'},
    {'Surrogate-Control': 'private'},
    {'Pragma': 'no-cache'},
    {'Vary': 'Accept-Encoding, Cookie'},
    {'Vary': 'Authorization'},
    {'Vary': '*'},
    {'Set-Cookie': 'session=synthetic; HttpOnly'},
  ]) {
    assert.equal(sw.cacheableResponse(r, response(h)), false, JSON.stringify(h));
  }
});

test('les URL à token, ambiguës, détournées ou partielles restent hors cache', () => {
  const sw = harness();
  for (const r of [
    request('/assets/js/site.js?token=synthetic'),
    request('/assets/js/%73ite.js'),
    request('/assets/js/site.js', {headers: {Authorization: 'Bearer synthetic'}}),
    request('/compte/index.html'),
    request('/api/user'),
    request('/projets/projet-nova/data/snapshot.json'),
  ]) assert.equal(sw.cacheableResponse(r, response()), false, r.url);
  const r = request('/assets/js/site.js');
  for (const denied of [
    {status: 206}, {redirected: true}, {type: 'opaque'},
    {url: 'https://external.invalid/site.js'},
  ]) {
    const fake = {
      ok: true, status: 200, redirected: false, type: 'basic',
      headers: new Headers(), url: r.url, ...denied,
    };
    assert.equal(sw.cacheableResponse(r, fake), false, JSON.stringify(denied));
  }
});

test('précache install : une page CORE privée n’est pas écrite', async () => {
  const sw = harness(req => response(req.url === ORIGIN + '/' ? {'Cache-Control': 'private'} : {}));
  const event = eventFor();
  sw.listeners.install(event);
  await event.done;
  assert.ok(sw.fetches.length >= sw.CORE.length);
  assert.ok(sw.fetches.every(req => req.credentials === 'omit'), 'aucun cookie envoyé au précache');
  assert.equal(sw.puts.some(x => x.url === ORIGIN + '/'), false);
  assert.equal(sw.puts.some(x => x.url === ORIGIN + '/offline.html'), true);
});

test('activation : supprimer uniquement les anciens caches du site', async () => {
  const sw = harness(undefined, ['benoitcantin-old', 'unrelated-app-v1', 'benoitcantin-newer', 'benoitcantin-v24-4-96-private-cache-guard']);
  const event = eventFor();
  sw.listeners.activate(event);
  await event.done;
  assert.deepEqual(sw.deletes.sort(), ['benoitcantin-newer', 'benoitcantin-old']);
});

test('les URL privées et endpoints dynamiques ne consultent pas Cache Storage', async () => {
  for (const r of [
    request('/administration.html'),
    request('/compte/index.html'),
    request('/api/user'),
    request('/assets/js/site.js?token=synthetic'),
    request('/assets/js/site.js', {headers: {Authorization: 'Bearer synthetic'}}),
  ]) {
    const sw = harness();
    const event = eventFor(r);
    sw.listeners.fetch(event);
    assert.ok(event.result, 'réponse interceptée');
    await event.result;
    assert.equal(sw.fetches.length, 1, r.url);
    assert.equal(sw.fetches[0].cache, 'no-store', r.url);
    assert.equal(sw.matches.length, 0, r.url);
    assert.equal(sw.puts.length, 0, r.url);
  }
});

test('fichiers publics : refuser le cache des réponses privées, conserver le public', async () => {
  const denied = harness(() => response({'Cache-Control': 'private'}));
  const e1 = eventFor(request('/assets/js/site.js'));
  denied.listeners.fetch(e1);
  await e1.result;
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(denied.puts.length, 0);

  const allowed = harness(() => response({'Cache-Control': 'public, max-age=600'}));
  const e2 = eventFor(request('/assets/js/site.js'));
  allowed.listeners.fetch(e2);
  await e2.result;
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(allowed.puts.length, 1);
});

test('les scripts JS/MJS/CSS restent network-first pour diffuser les correctifs', async () => {
  for (const asset of [
    '/assets/js/site.js',
    '/projets/projet-nova/script.js',
    '/projets/sinjira/jeux/game.mjs',
    '/projets/sinjira/jeux/style.css',
  ]) {
    const sw = harness(() => response({'Cache-Control': 'public, max-age=3600'}));
    const event = eventFor(request(asset));
    sw.listeners.fetch(event);
    await event.result;
    assert.equal(sw.fetches.length, 1, asset);
    assert.equal(sw.matches.length, 0, 'aucune copie obsolète lue avant le réseau: ' + asset);
  }
});

test('une application voisine ne peut pas influencer le cache hors ligne du site', async () => {
  const sw = harness(
    async () => { throw new TypeError('network unavailable'); },
    ['some-other-app-cache'],
    req => req === '/offline.html' ? new Response('Page locale approuvée') : undefined,
  );
  const event = eventFor(request('/assets/media/example.webp'));
  sw.listeners.fetch(event);
  const result = await event.result;
  assert.equal(await result.text(), 'Page locale approuvée');
  assert.deepEqual(sw.globalMatches, []);
  assert.equal(sw.matches.length, 2);
  assert.equal(sw.matches[1], '/offline.html');
});

test('une API privée indisponible propage son erreur réseau au lieu de renvoyer du HTML', async () => {
  const sw = harness(
    async () => { throw new TypeError('network unavailable'); },
    ['some-other-app-cache'],
    () => new Response('Page HTML hors ligne'),
  );
  const event = eventFor(request('/api/profile'));
  sw.listeners.fetch(event);
  await assert.rejects(event.result, /network unavailable/);
  assert.deepEqual(sw.globalMatches, []);
  assert.deepEqual(sw.matches, []);
  assert.equal(sw.puts.length, 0);
});

test('une ressource publique chargée avec cookies ne peut pas être stockée', () => {
  const sw = harness();
  const publicAsset = '/assets/js/site.js';
  assert.equal(sw.cacheableResponse(request(publicAsset), response()), false);
  assert.equal(sw.cacheableResponse(request(publicAsset, {credentials: 'include'}), response()), false);
  assert.equal(sw.cacheableResponse(request(publicAsset, {credentials: 'omit'}), response()), true);
});

test('seuls les chemins publics chargés sans cookies peuvent rejoindre le cache', async () => {
  for (const route of ['/', '/assets/js/site.js', '/assets/media/example.webp', '/projets/sinjira/romans/']) {
    const sw = harness(() => response({'Cache-Control': 'public, max-age=3600'}));
    const event = eventFor(request(route));
    sw.listeners.fetch(event);
    await event.result;
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(sw.fetches.length, 1, route);
    assert.equal(sw.fetches[0].credentials, 'omit', route);
    assert.equal(sw.puts.length, 1, route);
  }
});

test('un endpoint privé garde son mode authentifié et ne peut pas être mis en cache', async () => {
  const sw = harness();
  const event = eventFor(request('/compte/mon-profil.html'));
  sw.listeners.fetch(event);
  await event.result;
  assert.equal(sw.fetches.length, 1);
  assert.equal(sw.fetches[0].credentials, 'same-origin');
  assert.equal(sw.puts.length, 0);
  assert.deepEqual(sw.matches, []);
});
