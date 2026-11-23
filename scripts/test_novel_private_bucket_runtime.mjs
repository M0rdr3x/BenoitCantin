#!/usr/bin/env node
// Exécute le vrai handler Edge get-novel-file-url dans une simulation sans réseau.
// Vérifie autorisation, identité du bucket, preuve public=false et absence de fuite.
import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { readLimitedUtf8BodyWithDeadline } from '../supabase/functions/_shared/read-chunk-deadline.mjs';
import { privateBookLocationValid, isVerifiedPrivateBucket } from '../supabase/functions/_shared/private-book-storage-guard.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(resolve(root, 'supabase/functions/get-novel-file-url/index.ts'), 'utf8');
const substitutions = [
  ['function json(data:unknown,status=200)', 'function json(data,status=200)'],
  ['async function readBoundedJson(req:Request)', 'async function readBoundedJson(req)'],
];
let executable = source.replace(/^import [^\n]+;\n/gm, '');
for (const [before, after] of substitutions) {
  assert.equal(executable.split(before).length - 1, 1, 'Source Edge modifiée : ' + before);
  executable = executable.replace(before, after);
}
assert.doesNotMatch(executable, /^\s*import\s/m);
assert.equal(executable.split('Deno.serve(async(req)=>{').length - 1, 1);

const user = { id: 'user-1' };
const novelSlug = 'la-cendre-du-jugement';
const bucket = 'sinjira-livres-prives';
const objectPath = 'romans/la-cendre-du-jugement.pdf';

async function invoke({
  authenticated = true,
  published = true,
  fileReady = true,
  isOwner = false,
  isAdmin = false,
  ownerError = false,
  adminError = false,
  entitlement = true,
  productActive = true,
  privateBucket = true,
  bucketMismatch = false,
  bucketError = false,
  path = objectPath,
  bucketName = bucket,
  slug = novelSlug,
} = {}) {
  const calls = { auth: 0, queries: [], rpc: [], buckets: 0, signed: 0, logs: [] };
  const novel = {
    id: 'novel-1', slug: novelSlug, title: 'Livre fictif',
    status: published ? 'published' : 'draft', product_id: 'product-1',
    private_storage_bucket: bucketName, private_storage_path: path,
    file_ready: fileReady, page_count: 300, file_version: 1,
    file_sha256: null, file_size_bytes: null,
  };
  const service = {
    from(table) {
      assert.ok(['sinjira_novels', 'user_entitlements', 'products'].includes(table));
      calls.queries.push(table);
      const query = {
        select() { return this; },
        eq(field, value) {
          if (table === 'sinjira_novels') assert.deepEqual([field, value], ['slug', novelSlug]);
          if (table === 'user_entitlements') {
            assert.ok((field === 'user_id' && value === user.id) ||
                      (field === 'product_id' && value === 'product-1'));
          }
          if (table === 'products') assert.deepEqual([field, value], ['id', 'product-1']);
          return this;
        },
        async maybeSingle() {
          if (table === 'sinjira_novels') return { data: novel, error: null };
          if (table === 'user_entitlements') {
            return { data: entitlement ? { product_id: 'product-1' } : null, error: null };
          }
          return { data: { active: productActive }, error: null };
        },
      };
      return query;
    },
    async rpc(functionName, params) {
      assert.equal(params.p_user_id, user.id);
      calls.rpc.push(functionName);
      if (functionName === 'is_sinjira_owner') return { data: isOwner, error: ownerError ? { code: 'SIMULATED_FAILURE' } : null };
      if (functionName === 'is_sinjira_admin') return { data: isAdmin, error: adminError ? { code: 'SIMULATED_FAILURE' } : null };
      throw Error('Unexpected RPC');
    },
    storage: {
      async getBucket(actual) {
        calls.buckets++;
        assert.equal(actual, bucketName);
        if (bucketError) return { data: null, error: { code: 'SIMULATED_FAILURE' } };
        return { data: {
          id: bucketMismatch ? 'another-bucket' : actual,
          public: privateBucket ? false : true,
        }, error: null };
      },
      from(actual) {
        assert.equal(actual, bucketName);
        return {
          async createSignedUrl(actualPath, duration, options) {
            calls.signed++;
            assert.equal(actualPath, path);
            assert.equal(duration, 600);
            assert.equal(options.download, novelSlug + '.pdf');
            return { data: { signedUrl: 'https://storage.invalid/object/sign/novel?token=simulated' }, error: null };
          },
        };
      },
    },
  };
  const runtime = {
    Request, Response, URL, TextDecoder,
    readLimitedUtf8BodyWithDeadline, privateBookLocationValid, isVerifiedPrivateBucket,
    corsHeaders: { 'Access-Control-Allow-Origin': 'https://www.benoitcantin.com' },
    requiredUser: async () => {
      calls.auth++;
      if (!authenticated) throw new Error('AUTH_REQUIRED');
      return user;
    },
    serviceClient: () => service,
    console: { error(label, record) {
      calls.logs.push({ label, code: record?.code });
    } },
    Deno: { serve(handler) { runtime.handler = handler; } },
  };
  vm.runInNewContext(executable, runtime, { timeout: 2000 });
  assert.equal(typeof runtime.handler, 'function');
  const req = new Request('https://edge.invalid/functions/v1/get-novel-file-url', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ slug }),
  });
  const response = await runtime.handler(req);
  assert.equal(response.headers.get('Cache-Control'), 'private, no-store, max-age=0');
  assert.equal(response.headers.get('Referrer-Policy'), 'no-referrer');
  return { response, data: await response.json(), calls };
}

function denied(result, code) {
  assert.equal(result.response.status, code);
  assert.equal(result.data.ok, false);
  assert.equal('url' in result.data, false);
  assert.equal(result.calls.signed, 0);
}

test('authentification obligatoire avant accès aux données et au Storage', async () => {
  const r = await invoke({ authenticated: false });
  denied(r, 401);
  assert.equal(r.calls.auth, 1);
  assert.deepEqual(r.calls.queries, []);
  assert.equal(r.calls.buckets, 0);
});

test('roman non publié, licence absente ou fichier indisponible : aucune URL', async () => {
  const cases = [
    [{ published: false }, 404],
    [{ entitlement: false }, 403],
    [{ entitlement: true, productActive: false }, 403],
    [{ fileReady: false }, 409],
  ];
  for (const [options, status] of cases) {
    const r = await invoke(options);
    denied(r, status);
    assert.equal(r.calls.buckets, 0);
  }
});

test('les chemins PDF invalides sont refusés avant la lecture du bucket', async () => {
  for (const path of [
    '', '/roman.pdf', '../secret.pdf', 'romans/../secret.pdf',
    'romans//livre.pdf', 'romans/livre.pdf?download=true',
    'romans/%2e%2e/livre.pdf', 'romans/livre.txt',
  ]) {
    const r = await invoke({ path });
    denied(r, 503);
    assert.equal(r.calls.buckets, 0, path);
  }
});

test('bucket public, identité divergente ou erreur Supabase : refus sans signature', async () => {
  for (const options of [
    { privateBucket: false },
    { bucketMismatch: true },
    { bucketError: true },
  ]) {
    const r = await invoke(options);
    denied(r, 503);
    assert.equal(r.calls.buckets, 1);
    assert.equal(r.calls.logs.length, 1);
    assert.equal(r.calls.logs[0].code, 'NOVEL_PRIVATE_BUCKET_UNVERIFIED');
  }
});

test('un compte autorisé ne reçoit une URL signée qu’après preuve du bucket privé', async () => {
  const r = await invoke();
  assert.equal(r.response.status, 200);
  assert.equal(r.data.ok, true);
  assert.equal(r.data.protected, true);
  assert.equal(r.data.expires_in, 600);
  assert.equal(r.data.novel.slug, novelSlug);
  assert.equal(r.calls.auth, 1);
  assert.equal(r.calls.buckets, 1);
  assert.equal(r.calls.signed, 1);
  assert.ok(r.data.url.includes('/object/sign/'));
});

test('une réponse RPC truthy non booléenne ou en erreur ne confère aucun privilège', async () => {
  for (const options of [
    { isOwner: 'false', isAdmin: false, entitlement: false },
    { isOwner: false, isAdmin: 'false', entitlement: false },
    { isOwner: { active: false }, isAdmin: false, entitlement: false },
    { isOwner: 1, isAdmin: 0, entitlement: false },
    { isOwner: true, ownerError: true, entitlement: false },
    { isAdmin: true, adminError: true, entitlement: false },
  ]) {
    const r = await invoke(options);
    denied(r, 403);
    assert.equal(r.calls.buckets, 0);
  }
});

test('le droit propriétaire conserve la lecture sans entitlement marchand', async () => {
  const r = await invoke({ isOwner: true, entitlement: false });
  assert.equal(r.response.status, 200);
  assert.equal(r.data.ok, true);
  assert.equal(r.calls.buckets, 1);
  assert.equal(r.calls.signed, 1);
});
