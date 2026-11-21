#!/usr/bin/env node
// Tests du véritable handler Edge get-private-book-url avec DB et Storage simulés.
// Aucun secret, accès réseau, compte réel ou fichier privé n'est requis.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';
import { privateBookLocationValid, isVerifiedPrivateBucket } from '../supabase/functions/_shared/private-book-storage-guard.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(resolve(root, 'supabase/functions/get-private-book-url/index.ts'), 'utf8');
const runnable = source.replace(/^import [^\n]+;\n/gm, '')
  .replace('function privateJson(data:unknown,status=200)', 'function privateJson(data,status=200)');
assert.ok(runnable.includes("service.storage.getBucket(storage.bucket)"));
assert.ok(runnable.includes("!isVerifiedPrivateBucket(bucketMetadata,storage.bucket)"));
assert.doesNotMatch(runnable, /^import /m);
assert.doesNotMatch(runnable, /function privateJson\(data:unknown/);

function harness({
  authenticated = true,
  enabled = true,
  bucket = 'sinjira-livres-prives',
  path = 'livre-i/la-cendre-du-jugement.pdf',
  entitled = true,
  bucketPublic = false,
  bucketMismatch = false,
  bucketError = false,
} = {}) {
  const counters = { auth: 0, service: 0, product: 0, entitlement: 0, buckets: 0, signed: 0, logs: [] };
  const service = {
    from(table) {
      assert.ok(['products', 'user_entitlements'].includes(table));
      const query = {
        select() { return this; },
        eq() { return this; },
        async maybeSingle() {
          if (table === 'products') {
            counters.product++;
            return { data: { id: 'product-1', active: true }, error: null };
          }
          counters.entitlement++;
          return { data: entitled ? { product_id: 'product-1' } : null, error: null };
        },
      };
      return query;
    },
    storage: {
      async getBucket(bucketName) {
        counters.buckets++;
        assert.equal(bucketName, bucket);
        if (bucketError) return { data: null, error: new Error('simulated provider outage') };
        return { data: { id: bucketMismatch ? 'other-bucket' : bucketName, public: bucketPublic }, error: null };
      },
      from(bucketName) {
        assert.equal(bucketName, bucket);
        return {
          async createSignedUrl(storagePath, seconds, opts) {
            counters.signed++;
            assert.equal(storagePath, path);
            assert.equal(seconds, 300);
            assert.equal(opts.download, 'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf');
            return { data: { signedUrl: 'https://storage.invalid/object/sign/private-file?token=opaque' }, error: null };
          },
        };
      },
    },
  };
  const envVars = {
    SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED: enabled ? 'true' : 'false',
    SINJIRA_LIVRE_I_PRIVATE_BUCKET: bucket,
    SINJIRA_LIVRE_I_PRIVATE_PATH: path,
  };
  const runtime = {
    Error, Request, Response,
    corsHeaders: { 'Access-Control-Allow-Origin': 'https://www.benoitcantin.com' },
    privateBookLocationValid, isVerifiedPrivateBucket,
    requiredUser: async () => {
      counters.auth++;
      if (!authenticated) throw new Error('AUTH_REQUIRED');
      return { id: 'user-1' };
    },
    serviceClient: () => { counters.service++; return service; },
    console: { error(label, record) { counters.logs.push({ label, code: record?.code }); } },
    Deno: { env: { get: name => envVars[name] ?? null }, serve(handler) { runtime.handler = handler; } },
  };
  vm.runInNewContext(runnable, runtime, { timeout: 3000 });
  assert.equal(typeof runtime.handler, 'function');
  return {
    counters,
    async request() {
      const response = await runtime.handler(new Request('https://edge.invalid/functions/v1/get-private-book-url', { method: 'POST' }));
      assert.equal(response.headers.get('Cache-Control'), 'private, no-store, max-age=0');
      assert.equal(response.headers.get('Referrer-Policy'), 'no-referrer');
      return { response, data: await response.json() };
    },
  };
}

test('authentification obligatoire avant consultation de config, produit ou Storage', async () => {
  const h = harness({ authenticated: false });
  const r = await h.request();
  assert.equal(r.response.status, 401);
  assert.equal(r.data.ok, false);
  assert.equal('url' in r.data, false);
  assert.equal(h.counters.auth, 1);
  assert.equal(h.counters.service, 0);
  assert.equal(h.counters.buckets, 0);
  assert.equal(h.counters.signed, 0);
});

test('diffusion désactivée ou chemin privé invalide : aucun accès à Storage', async () => {
  for (const options of [
    { enabled: false },
    { path: 'livre-i/../archive.pdf' },
    { path: 'livre-i/roman.pdf?download=1' },
    { path: 'https://evil.invalid/roman.pdf' },
    { bucket: 'public/bucket' },
  ]) {
    const h = harness(options);
    const r = await h.request();
    assert.equal(r.response.status, 503, JSON.stringify(options));
    assert.equal(r.data.ok, false);
    assert.equal('url' in r.data, false);
    assert.equal(h.counters.service, 0);
    assert.equal(h.counters.buckets, 0);
    assert.equal(h.counters.signed, 0);
  }
});

test('sans entitlement, refuser avant la lecture du bucket et la signature', async () => {
  const h = harness({ entitled: false });
  const r = await h.request();
  assert.equal(r.response.status, 403);
  assert.equal('url' in r.data, false);
  assert.equal(h.counters.entitlement, 1);
  assert.equal(h.counters.buckets, 0);
  assert.equal(h.counters.signed, 0);
});

test('bucket public, identité erronée ou API indisponible : refus sécurisé', async () => {
  for (const options of [
    { bucketPublic: true },
    { bucketMismatch: true },
    { bucketError: true },
  ]) {
    const h = harness(options);
    const r = await h.request();
    assert.equal(r.response.status, 503, JSON.stringify(options));
    assert.equal(r.data.ok, false);
    assert.equal('url' in r.data, false);
    assert.equal(h.counters.entitlement, 1);
    assert.equal(h.counters.buckets, 1);
    assert.equal(h.counters.signed, 0);
    assert.equal(h.counters.logs.length, 1);
    assert.equal(h.counters.logs[0].code, 'BOOK_PRIVATE_BUCKET_UNVERIFIED');
  }
});

test('un compte autorisé obtient uniquement un lien signé de 300 secondes après preuve privée', async () => {
  const h = harness();
  const r = await h.request();
  assert.equal(r.response.status, 200);
  assert.equal(r.data.ok, true);
  assert.equal(r.data.protected, true);
  assert.equal(r.data.expires_in, 300);
  assert.equal(r.data.product_slug, 'sinjira-livre-01-la-cendre-du-jugement');
  assert.ok(r.data.url.includes('/object/sign/'));
  assert.equal(h.counters.auth, 1);
  assert.equal(h.counters.product, 1);
  assert.equal(h.counters.entitlement, 1);
  assert.equal(h.counters.buckets, 1);
  assert.equal(h.counters.signed, 1);
});
