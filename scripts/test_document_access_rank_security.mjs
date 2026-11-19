#!/usr/bin/env node
// Exécuter le véritable handler get-document-url en simulation isolée :
// aucun secret, appel Supabase réel, document utilisateur ou réseau.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';

import { readLimitedUtf8Body } from '../supabase/functions/_shared/limited-body.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(resolve(root, 'supabase/functions/get-document-url/index.ts'), 'utf8');
const UUID = '11111111-1111-4111-8111-111111111111';

// On supprime seulement les annotations TypeScript connues de cette fonction.
// La logique d'autorisation et la réponse HTTP exécutées sont celles du dépôt.
function runnableHandlerSource() {
  let code = source.replace(/^import [^\n]+;\n/gm, '');
  const substitutions = [
    ['const ranks:Record<string,number>=', 'const ranks='],
    ['function documentAccessAllowed(accessLevel:unknown,userRank:number)', 'function documentAccessAllowed(accessLevel,userRank)'],
    ['function privateJson(data:unknown,status=200)', 'function privateJson(data,status=200)'],
    ['function externalUrlAllowed(value:string)', 'function externalUrlAllowed(value)'],
    ['async function readLimitedJson(req:Request):Promise<{body?:any;response?:Response}>', 'async function readLimitedJson(req)'],
  ];
  for (const [from, to] of substitutions) {
    assert.equal(code.split(from).length - 1, 1, 'Signature du serveur modifiée : ' + from);
    code = code.replace(from, to);
  }
  assert.ok(!/^\s*import\s/m.test(code), 'Imports Edge non isolés');
  assert.ok(code.includes('Deno.serve(async(req)=>{'), 'Handler HTTP réel introuvable');
  return code;
}

const runtimeCode = runnableHandlerSource();

async function invoke({
  accessLevel,
  visibility = 'private',
  rank = 0,
  signed = false,
  user = null,
  approved = true,
  active = true,
  mime = 'application/json',
  requestBody = JSON.stringify({ document_id: UUID }),
}) {
  const counters = { documentReads: 0, signedUrls: 0, bucketReads: 0, rpcCalls: [] };
  const doc = {
    project_id: UUID,
    status: approved ? 'approved' : 'pending',
    access_level: accessLevel,
    external_url: signed ? null : '/projets/sinjira/documents/example.pdf',
    storage_bucket: 'sinjira-private-documents',
    storage_path: 'projets/exemple.pdf',
    projects: { visibility, status: active ? 'active' : 'archived' },
  };

  const query = {
    select() { return this; },
    eq() { return this; },
    async maybeSingle() { counters.documentReads += 1; return { data: doc, error: null }; },
  };
  const service = {
    from(name) {
      assert.equal(name, 'documents');
      return query;
    },
    async rpc(name) {
      counters.rpcCalls.push(name);
      if (name === 'is_sinjira_admin') return { data: rank === 100, error: null };
      if (name === 'project_access_rank') return { data: rank, error: null };
      throw new Error('Unexpected RPC');
    },
    storage: {
      async getBucket(bucket) {
        counters.bucketReads += 1;
        assert.equal(bucket, doc.storage_bucket);
        return { data: { id: bucket, public: false }, error: null };
      },
      from(bucket) {
        assert.equal(bucket, doc.storage_bucket);
        return {
          async createSignedUrl(path, seconds) {
            counters.signedUrls += 1;
            assert.equal(path, doc.storage_path);
            assert.equal(seconds, 600);
            return {
              data: { signedUrl: 'https://storage.example.invalid/private-token' },
              error: null,
            };
          },
        };
      },
    },
  };

  const runtime = {
    Request, Response, URL, Number, Object,
    console: { error() { throw new Error('Unexpected server logging'); } },
    readLimitedUtf8Body,
    corsHeaders: {
      'Access-Control-Allow-Origin': 'https://www.benoitcantin.com',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
    },
    serviceClient: () => service,
    optionalUser: async () => user,
    privateDocumentLocationValid: () => true,
    isVerifiedPrivateDocumentBucket: metadata =>
      metadata?.public === false && metadata?.id === doc.storage_bucket,
  };
  runtime.Deno = { serve(handler) { runtime.handler = handler; } };
  vm.runInNewContext(runtimeCode, runtime, { timeout: 1000 });
  assert.equal(typeof runtime.handler, 'function');

  const request = new Request('https://edge.example.invalid/functions/v1/get-document-url', {
    method: 'POST',
    headers: { 'content-type': mime },
    body: requestBody,
  });
  const response = await runtime.handler(request);
  assert.equal(response.headers.get('Cache-Control'), 'private, no-store, max-age=0');
  assert.equal(response.headers.get('Referrer-Policy'), 'no-referrer');
  return { response, payload: await response.json(), counters };
}

function assertDenied(result, context) {
  assert.equal(result.response.status, 403, context);
  assert.equal(result.payload.ok, false, context);
  assert.equal('url' in result.payload, false, context + ' ne doit produire aucune URL');
  assert.equal(result.counters.bucketReads, 0, context + ' ne doit consulter aucun bucket');
  assert.equal(result.counters.signedUrls, 0, context + ' ne doit signer aucun lien');
}

test('valeurs héritées de Object.prototype refusées, y compris sur projet privé', async () => {
  for (const level of [
    'constructor', '__proto__', 'toString', 'valueOf', 'hasOwnProperty',
    'isPrototypeOf', '__defineGetter__', 'propertyIsEnumerable',
  ]) {
    assertDenied(await invoke({ accessLevel: level }), 'niveau hérité : ' + level);
    assertDenied(await invoke({
      accessLevel: level, rank: 100, user: { id: UUID }, signed: true,
    }), 'niveau hérité même pour admin : ' + level);
  }
});

test('valeurs inconnues, non typées et rangs non finis refusés', async () => {
  for (const accessLevel of ['future_level', 'Public', '', null, 1, {}, ['public']]) {
    assertDenied(await invoke({ accessLevel }), 'niveau non déclaré : ' + String(accessLevel));
  }
  for (const rank of ['Infinity', '-Infinity', 'NaN']) {
    assertDenied(await invoke({
      accessLevel: 'account', rank, user: { id: UUID }, signed: true,
    }), 'rang RPC non fini : ' + rank);
  }
});

test('droits des niveaux canoniques préservés à leurs seuils exacts', async () => {
  const levels = [
    ['public', 1], ['account', 10], ['player', 20],
    ['tester', 30], ['admin', 100],
  ];
  for (const [accessLevel, required] of levels) {
    const isPublic = accessLevel === 'public';
    const allowed = await invoke({
      accessLevel, rank: required, user: { id: UUID },
      visibility: isPublic ? 'public' : 'private',
      signed: !isPublic,
    });
    assert.equal(allowed.response.status, 200, accessLevel);
    assert.equal(allowed.payload.ok, true, accessLevel);
    if (isPublic) {
      assert.ok(allowed.payload.url.startsWith('/projets/'), accessLevel);
      assert.equal(allowed.payload.protected, false);
      assert.equal(allowed.counters.signedUrls, 0);
    } else {
      assert.equal(allowed.payload.protected, true);
      assert.equal(allowed.counters.signedUrls, 1);
    }
    if (required > 1) {
      assertDenied(await invoke({
        accessLevel, rank: required - 1, user: { id: UUID },
      }), 'rang insuffisant pour ' + accessLevel);
    }
  }
});

test('document public anonyme préservé, accès privé anonyme refusé', async () => {
  const publicDoc = await invoke({ accessLevel: 'public', visibility: 'public' });
  assert.equal(publicDoc.response.status, 200);
  assert.equal(publicDoc.payload.protected, false);
  assertDenied(await invoke({ accessLevel: 'public', visibility: 'private' }), 'public sur projet privé');
  assertDenied(await invoke({ accessLevel: 'account', visibility: 'public' }), 'compte sans connexion');
});

test('signature Storage privée conservée uniquement après autorisation', async () => {
  assertDenied(await invoke({ accessLevel: 'admin', signed: true }), 'Storage admin anonyme');
  const allowed = await invoke({
    accessLevel: 'admin', signed: true, rank: 100, user: { id: UUID },
  });
  assert.equal(allowed.response.status, 200);
  assert.equal(allowed.payload.protected, true);
  assert.equal(allowed.payload.expires_in, 600);
  // Le contrôle du statut privé du bucket est une protection additionnelle en PR #1037.
  // Cette PR cible uniquement le refus des liens AVANT tout accès au Storage.
  assert.equal(allowed.counters.signedUrls, 1);
});

test('un projet non approuvé ou inactif demeure inaccessible', async () => {
  const pending = await invoke({ accessLevel: 'public', visibility: 'public', approved: false });
  assert.equal(pending.response.status, 404);
  const archived = await invoke({ accessLevel: 'public', visibility: 'public', active: false });
  assert.equal(archived.response.status, 404);
});

test('type MIME strict et forme JSON refusés avant tout accès service_role', async () => {
  for (const mime of [
    'application/jsonp', 'application/json-evil', 'text/plain',
    'application/x-www-form-urlencoded', 'application/JSON+extra',
  ]) {
    const result = await invoke({ accessLevel: 'public', visibility: 'public', mime });
    assert.equal(result.response.status, 415, mime);
    assert.equal(result.counters.documentReads, 0, mime + ' ne doit pas interroger documents');
    assert.equal(result.counters.signedUrls, 0, mime + ' ne doit pas signer de lien');
  }
  const charset = await invoke({
    accessLevel: 'public', visibility: 'public', mime: 'application/json; charset=utf-8',
  });
  assert.equal(charset.response.status, 200, 'JSON avec paramètre charset doit fonctionner');

  for (const requestBody of ['null', '[]', '"texte"', '123', 'true']) {
    const result = await invoke({ accessLevel: 'public', visibility: 'public', requestBody });
    assert.equal(result.response.status, 400, requestBody);
    assert.equal(result.payload.error, 'Corps JSON invalide.', requestBody);
    assert.equal(result.counters.documentReads, 0, requestBody + ' ne doit pas interroger documents');
    assert.equal(result.counters.signedUrls, 0, requestBody + ' ne doit pas signer de lien');
  }
});

test('aucun lien statique ne peut representer un document restreint, meme avec rang valide', async () => {
  for (const [accessLevel, visibility, rank] of [
    ['public', 'private', 100],
    ['account', 'public', 10],
    ['player', 'private', 20],
    ['tester', 'private', 30],
    ['admin', 'private', 100],
  ]) {
    const label = accessLevel + '/' + visibility;
    const result = await invoke({
      accessLevel, visibility, rank, user: { id: UUID }, signed: false,
    });
    assert.equal(result.response.status, 503, label);
    assert.equal(result.payload.ok, false, label);
    assert.equal('url' in result.payload, false, label);
    assert.equal(result.counters.documentReads, 1, label);
    assert.equal(result.counters.bucketReads, 0, label);
    assert.equal(result.counters.signedUrls, 0, label);
  }
});

test('un document prive avec vraie signature Storage reste autorise au rang legitime', async () => {
  const allowed = await invoke({
    accessLevel: 'account', visibility: 'public', rank: 10,
    user: { id: UUID }, signed: true,
  });
  assert.equal(allowed.response.status, 200);
  assert.equal(allowed.payload.protected, true);
  assert.equal(allowed.counters.bucketReads, 1);
  assert.equal(allowed.counters.signedUrls, 1);
});
