import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const code = readFileSync(new URL('../sw.js', import.meta.url), 'utf8');
const ORIGIN = 'https://www.benoitcantin.com';

function harness() {
  const events = {};
  const stores = new Map([['another-app-cache', new Map()]]);
  const writes = [];
  const requests = [];
  let online = true;
  let reply = req => new Response('precache:' + new URL(req.url).pathname, { status: 200 });
  const key = request => new URL(typeof request === 'string' ? request : request.url, ORIGIN).href;
  const open = async name => {
    if (!stores.has(name)) stores.set(name, new Map());
    const store = stores.get(name);
    return {
      async addAll(paths) { for (const path of paths) store.set(key(path), new Response('precache:' + path)); },
      async put(req, response) { writes.push({ cache: name, url: key(req) }); store.set(key(req), response); },
      async match(req) { return store.get(key(req)); },
    };
  };
  const caches = {
    open,
    keys: async () => [...stores.keys()],
    delete: async name => stores.delete(name),
    async match(req) {
      for (const store of stores.values()) if (store.has(key(req))) return store.get(key(req));
    },
  };
  const self = {
    addEventListener(type, handler) { events[type] = handler; },
    skipWaiting: async () => undefined,
    clients: { claim: async () => undefined },
  };
  function mockFetch(req) {
    requests.push(req);
    if (!online) return Promise.reject(new Error('offline'));
    return Promise.resolve(reply(req));
  }
  runInNewContext(code, { self, caches, fetch: mockFetch, URL, Request, Response, location: { origin: ORIGIN } }, { filename: 'sw.js' });
  async function lifecycle(name) {
    let pending;
    events[name]({ waitUntil(value) { pending = value; } });
    await pending;
  }
  async function request(path, options = {}) {
    const req = new Request(new URL(path, ORIGIN), { headers: options.headers });
    Object.defineProperty(req, 'destination', { value: options.destination ?? 'document' });
    Object.defineProperty(req, 'mode', { value: options.destination === 'document' ? 'navigate' : 'cors' });
    let pending;
    events.fetch({ request: req, respondWith(value) { pending = value; } });
    const response = await pending;
    await new Promise(resolve => setImmediate(resolve));
    return response;
  }
  return { caches, writes, requests, stores, request, lifecycle, setReply: fn => reply = fn, setOnline: value => online = value };
}

test('installation publique et nettoyage limité aux caches de ce site', async () => {
  const h = harness();
  h.stores.set('benoitcantin-v24-4-95-public-4', new Map());
  h.stores.set('benoitcantin-v24-4-95-public-6', new Map());
  h.stores.set('benoitcantin-v24-4-95-public-7', new Map());
  await h.lifecycle('install');
  await h.lifecycle('activate');
  assert.equal(h.stores.has('benoitcantin-v24-4-95-public-4'), false);
  assert.equal(h.stores.has('benoitcantin-v24-4-95-public-6'), false);
  assert.equal(h.stores.has('benoitcantin-v24-4-95-public-7'), false);
  assert.equal(await (await h.caches.match('/assets/icons/sinjira-officiel-20261120.png')).text(), 'precache:/assets/icons/sinjira-officiel-20261120.png');
  assert.equal(h.stores.has('another-app-cache'), true);
  assert.equal(await (await h.caches.match('/')).text(), 'precache:/');
  assert.equal(await h.caches.match('/compte/'), undefined);
});

test('les pages HTML ne sont jamais ajoutées au cache pendant la navigation', async () => {
  const h = harness(); await h.lifecycle('install'); h.writes.length = 0;
  await h.request('/');
  assert.equal(h.writes.length, 0);
  for (const path of ['/profil-prive-inconnu/', '/app/', '/compte/connexion.html', '/admin/', '/supabase/', '/histoire-de-vie/']) {
    await h.request(path);
  }
  assert.equal(h.writes.length, 0);
  assert.equal(h.requests.at(-1).cache, 'no-store');
  h.setOnline(false);
  assert.equal(await (await h.request('/')).text(), 'precache:/');
});

test('GET JSON, URL à paramètres et headers sensibles ne sont jamais cachés', async () => {
  const h = harness(); await h.lifecycle('install'); h.writes.length = 0;
  await h.request('/api/profil.json', { destination: '' });
  await h.request('/assets/media/roman-prive.pdf', { destination: '' });
  await h.request('/assets/js/site.js?token=confidentiel', { destination: 'script' });
  await h.request('/assets/js/site.js', { destination: 'script', headers: { Authorization: 'Bearer fictif' } });
  await h.request('/assets/media/sinjira-registre.webp', { destination: 'image', headers: { Range: 'bytes=0-10' } });
  assert.equal(h.writes.length, 0);
});

test('les réponses privées, non stockables, partielles ou redirigées sont refusées', async () => {
  const h = harness(); await h.lifecycle('install'); h.writes.length = 0;
  for (const init of [
    { headers: { 'Cache-Control': 'private, max-age=30' } },
    { headers: { 'Cache-Control': 'no-store' } },
    { headers: { 'Cache-Control': 'no-cache, max-age=300' } },
    { headers: { 'Cache-Control': 'public, no-cache="Set-Cookie"' } },
    { headers: { Pragma: 'no-cache' } },
    { headers: { 'Set-Cookie': 'session=fictive' } },
    { headers: { Vary: '*' } },
    { headers: { Vary: 'Cookie' } },
    { headers: { Vary: 'Accept-Language, AUTHORIZATION' } },
    { headers: { Vary: 'Proxy-Authorization' } },
    { headers: { Vary: 'Set-Cookie' } },
    { headers: { Vary: 'X-Account-Id' } },
    { headers: { Vary: 'Origin' } },
    { status: 206 },
  ]) {
    h.setReply(() => new Response('non public', { status: init.status ?? 200, headers: init.headers }));
    await h.request('/assets/js/site.js', { destination: 'script' });
  }
  h.setReply(() => {
    const resp = new Response('redirection');
    Object.defineProperty(resp, 'redirected', { value: true });
    return resp;
  });
  await h.request('/assets/js/site.js', { destination: 'script' });
  assert.equal(h.writes.length, 0);
});

test('hors ligne, le CSS versionné précaché reste disponible sans cacher la query', async () => {
  const h = harness(); await h.lifecycle('install'); h.writes.length = 0;
  h.setOnline(false);
  const css = await h.request('/assets/css/home-sinjira-only-v1.css?v=1.1.0', { destination: 'style' });
  assert.equal(await css.text(), 'precache:/assets/css/home-sinjira-only-v1.css');
  assert.equal(h.writes.length, 0);
  assert.equal(await (await h.request('/accueil-non-precachee.html')).text(), 'precache:/offline.html');
});

test('seuls les en-têtes Vary de contenu public permettent le cache statique', async () => {
  const h = harness(); await h.lifecycle('install'); h.writes.length = 0;
  h.setReply(() => new Response('public negotiated', {
    headers: { Vary: 'Accept-Encoding, Accept-Language' },
  }));
  await h.request('/assets/js/site.js', { destination: 'script' });
  assert.equal(h.writes.length, 1, 'négociation publique bénigne autorisée');
  h.writes.length = 0;
  h.setReply(() => new Response('session-bound', {
    headers: { Vary: 'X-Tenant-ID' },
  }));
  await h.request('/assets/js/site.js', { destination: 'script' });
  assert.equal(h.writes.length, 0, 'un en-tête de personnalisation inconnu reste privé');
});

test('précache sans cookie : toutes les requêtes sont anonymes et non stockées côté HTTP', async () => {
  const h = harness();
  await h.lifecycle('install');
  assert.ok(h.requests.length >= 20, 'CORE précharge plusieurs fichiers publics');
  for (const req of h.requests) {
    assert.equal(req.credentials, 'omit', 'aucun cookie/session pour le précache');
    assert.equal(req.cache, 'no-store');
    assert.equal(req.redirect, 'error', 'aucune redirection vers une autre origine');
  }
  assert.equal(await (await h.caches.match('/')).text(), 'precache:/');
});

test('le précache échoue fermement si une page publique reçoit une réponse privée', async () => {
  for (const headers of [
    { 'Cache-Control': 'private, max-age=300' },
    { 'Cache-Control': 'no-store' },
    { 'Cache-Control': 'no-cache, max-age=60' },
    { Pragma: 'no-cache' },
    { Vary: 'Accept-Language, Cookie' },
    { Vary: 'Authorization' },
    { 'Set-Cookie': 'session=synthetic' },
  ]) {
    const h = harness();
    h.setReply(req => new Response('synthetic', {
      status: 200,
      headers: new URL(req.url).pathname === '/' ? headers : {},
    }));
    await assert.rejects(h.lifecycle('install'), /Réponse non publique refusée au précache/);
    assert.equal(await h.caches.match('/'), undefined,
      'une page personnalisée ne doit jamais apparaître dans CacheStorage');
  }
});

test('une ressource statique est téléchargée sans cookies; le chemin privé garde sa session', async () => {
  const h = harness(); await h.lifecycle('install'); h.writes.length = 0;
  const requests = [];
  h.setReply(req => {
    requests.push(req);
    return new Response('anonymous asset');
  });
  await h.request('/assets/js/site.js', { destination: 'script' });
  assert.equal(requests.at(-1).credentials, 'omit');
  assert.equal(h.writes.length, 1, 'le JS public peut être mémorisé après validation');
  await h.request('/compte/index.html', { destination: 'document' });
  assert.equal(requests.at(-1).credentials, 'same-origin',
    'les accès privés doivent conserver les credentials pour le serveur');
  assert.equal(h.writes.length, 1, 'aucune donnée privée n’est mémorisée');
});
