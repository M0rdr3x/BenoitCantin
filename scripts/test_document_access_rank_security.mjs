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
import { privateDocumentLocationValid, isVerifiedPrivateDocumentBucket } from '../supabase/functions/_shared/private-document-storage.mjs';

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
  adminData = undefined,
  adminError = false,
  rankData = undefined,
  rankError = false,
  signed = false,
  user = null,
  approved = true,
  active = true,
  bucketPublic = false,
  bucketReadError = false,
  bucketErrorValue = null,
  signedResponse = { data: { signedUrl: 'https://storage.example.invalid/private-token' }, error: null },
  bucketMismatch = false,
  storagePath = 'projets/exemple.pdf',
  storageBucket = 'sinjira-private-documents',
  externalUrl = '/projets/sinjira/documents/example.pdf',
}) {
  const counters = { documentReads: 0, signedUrls: 0, bucketReads: 0, rpcCalls: [], logs: [] };
  const doc = {
    project_id: UUID,
    status: approved ? 'approved' : 'pending',
    access_level: accessLevel,
    external_url: signed ? null : externalUrl,
    storage_bucket: storageBucket,
    storage_path: storagePath,
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
      if (name === 'is_sinjira_admin') return {
        data: adminData === undefined ? rank === 100 : adminData,
        error: adminError ? new Error('Simulated admin RPC error') : null,
      };
      if (name === 'project_access_rank') return {
        data: rankData === undefined ? rank : rankData,
        error: rankError ? new Error('Simulated rank RPC error') : null,
      };
      throw new Error('Unexpected RPC');
    },
    storage: {
      async getBucket(bucket) {
        counters.bucketReads += 1;
        assert.equal(bucket, doc.storage_bucket);
        if (bucketReadError) return { data: null, error: new Error('simulated provider unavailable') };
        return { data: { id: bucketMismatch ? 'other-bucket' : bucket, public: bucketPublic }, error: bucketErrorValue };
      },
      from(bucket) {
        assert.equal(bucket, doc.storage_bucket);
        return {
          async createSignedUrl(path, seconds) {
            counters.signedUrls += 1;
            assert.equal(path, doc.storage_path);
            assert.equal(seconds, 600);
            return signedResponse;
          },
        };
      },
    },
  };

  const runtime = {
    Request, Response, URL, Number, Object,
    console: { error(label, detail) { counters.logs.push([label, detail]); } },
    readLimitedUtf8Body,
    corsHeaders: {
      'Access-Control-Allow-Origin': 'https://www.benoitcantin.com',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
    },
    serviceClient: () => service,
    optionalUser: async () => user,
    privateDocumentLocationValid,
    isVerifiedPrivateDocumentBucket,
  };
  runtime.Deno = { serve(handler) { runtime.handler = handler; } };
  vm.runInNewContext(runtimeCode, runtime, { timeout: 1000 });
  assert.equal(typeof runtime.handler, 'function');

  const request = new Request('https://edge.example.invalid/functions/v1/get-document-url', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ document_id: UUID }),
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
    const result = await invoke({
      accessLevel: 'account', rank, user: { id: UUID }, signed: true,
    });
    assert.equal(result.response.status, 503, 'rang RPC non fini : ' + rank);
    assert.equal(result.payload.ok, false);
    assert.equal('url' in result.payload, false);
    assert.equal(result.counters.bucketReads, 0);
    assert.equal(result.counters.signedUrls, 0);
  }
});

test('une RPC refusée ou mal typée ne peut jamais autoriser un document', async () => {
  const cases = [
    { adminData: 'false' }, { adminData: 'true' },
    { adminData: 1 }, { adminData: null }, { adminData: [] },
    { adminData: { is_admin: true } },
    { adminData: true, adminError: true },
    { adminData: false, adminError: true },
    { rankData: '30' }, { rankData: 30.5 }, { rankData: NaN },
    { rankData: Infinity }, { rankData: -1 }, { rankData: 31 },
    { rankData: 100 }, { rankData: 1000 }, { rankData: '100' }, { rankData: '20' }, { rankData: null }, { rankData: true }, { rankData: [100] },
    { rankData: { rank: 30 } }, { rankData: [30] },
    { rankData: 30, rankError: true },
  ];
  for (const options of cases) {
    const result = await invoke({
      accessLevel: 'account', visibility: 'private',
      user: { id: UUID }, signed: true, rank: 10, ...options,
    });
    assert.equal(result.response.status, 503, JSON.stringify(options));
    assert.equal(result.payload.ok, false);
    assert.equal('url' in result.payload, false);
    assert.equal(result.counters.bucketReads, 0);
    assert.equal(result.counters.signedUrls, 0);
    assert.equal(result.counters.rpcCalls.length,
      ('adminData' in options || 'adminError' in options) ? 1 : 2);
  }
});

test('rangs exacts et administrateur confirmé conservent leurs accès', async () => {
  for (const rank of [0,1,10,20,30]) {
    const result = await invoke({
      accessLevel: 'public', visibility: 'public', rank,
      user: { id: UUID }, signed: true,
    });
    assert.equal(result.response.status, rank===0?403:200, String(rank));
    assert.equal(result.counters.rpcCalls.length, 2);
  }
  const admin = await invoke({
    accessLevel: 'admin', visibility: 'private', signed: true,
    rank: 100, user: { id: UUID },
  });
  assert.equal(admin.response.status, 200);
  assert.equal(admin.payload.protected, true);
  assert.deepEqual(admin.counters.rpcCalls, ['is_sinjira_admin']);
});

test('droits des niveaux canoniques préservés à leurs seuils exacts', async () => {
  const levels = [
    ['public', 1], ['account', 10], ['player', 20],
    ['tester', 30], ['admin', 100],
  ];
  for (const [accessLevel, required] of levels) {
    const allowed = await invoke({
      accessLevel, rank: required, user: { id: UUID },
      visibility: 'public', signed: accessLevel !== 'public',
    });
    assert.equal(allowed.response.status, 200, accessLevel);
    assert.equal(allowed.payload.ok, true, accessLevel);
    if(accessLevel === 'public'){
      assert.ok(allowed.payload.url.startsWith('/projets/'), accessLevel);
      assert.equal(allowed.payload.protected, false);
    }else{
      assert.equal(allowed.payload.protected, true, accessLevel);
      assert.equal(allowed.counters.signedUrls, 1, accessLevel);
    }
    if (required > 1) {
      assertDenied(await invoke({
        accessLevel, rank: ({ 10:1, 20:10, 30:20, 100:30 })[required], user: { id: UUID },
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

test('un lien statique restreint ne doit jamais être livré même à un administrateur', async () => {
  const user = { id: UUID };
  const cases = [
    { accessLevel: 'account', visibility: 'public' },
    { accessLevel: 'player', visibility: 'public' },
    { accessLevel: 'tester', visibility: 'public' },
    { accessLevel: 'admin', visibility: 'private' },
    { accessLevel: 'public', visibility: 'private' },
  ];
  for (const scenario of cases) {
    const result = await invoke({ ...scenario, user, rank: 100, signed: false });
    assert.equal(result.response.status, 500, JSON.stringify(scenario));
    assert.equal(result.payload.ok, false, JSON.stringify(scenario));
    assert.equal('url' in result.payload, false, JSON.stringify(scenario));
    assert.equal(result.counters.signedUrls, 0, JSON.stringify(scenario));
    assert.equal(result.counters.bucketReads, 0, JSON.stringify(scenario));
  }
});

test('un document public refuse la redirection vers un domaine tiers même si HTTPS', async () => {
  const result = await invoke({
    accessLevel: 'public', visibility: 'public',
    externalUrl: 'https://example.org/trusted-looking-document.pdf',
  });
  assert.equal(result.response.status, 500);
  assert.equal(result.payload.ok, false);
  assert.equal('url' in result.payload, false);
  const canonical = await invoke({
    accessLevel: 'public', visibility: 'public',
    externalUrl: 'https://www.benoitcantin.com/projets/sinjira/documents/exemple.pdf',
  });
  assert.equal(canonical.response.status, 200);
  assert.equal(canonical.payload.protected, false);
});

test('document réellement public conserve une URL statique, fichier restreint migré conserve un lien signé', async () => {
  const allowed = await invoke({ accessLevel: 'public', visibility: 'public', signed: false });
  assert.equal(allowed.response.status, 200);
  assert.equal(allowed.payload.protected, false);
  assert.ok(allowed.payload.url.startsWith('/projets/'));
  const privateSigned = await invoke({
    accessLevel: 'account', visibility: 'private', signed: true, rank: 10, user: { id: UUID },
  });
  assert.equal(privateSigned.response.status, 200);
  assert.equal(privateSigned.payload.protected, true);
  assert.equal(privateSigned.payload.expires_in, 600);
  assert.equal(privateSigned.counters.signedUrls, 1);
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


test('la signature exige un bucket réellement privé, identité exacte et aucune erreur fournisseur', async () => {
  for (const options of [
    { bucketPublic: true }, { bucketPublic: null }, { bucketPublic: 'false' },
    { bucketReadError: true },
    { bucketMismatch: true }, { bucketErrorValue: false }, { bucketErrorValue: 0 }, { bucketErrorValue: '' },
  ]) {
    const result = await invoke({
      accessLevel: 'account', visibility: 'private', signed: true,
      rank: 10, user: { id: UUID }, ...options,
    });
    assert.equal(result.response.status, 503, JSON.stringify(options));
    assert.equal(result.payload.ok, false);
    assert.equal('url' in result.payload, false);
    assert.equal(result.counters.bucketReads, 1);
    assert.equal(result.counters.signedUrls, 0);
    assert.equal(result.counters.logs.length, 1);
    assert.equal(result.counters.logs[0][1].code, 'DOCUMENT_PRIVATE_BUCKET_UNVERIFIED');
  }
});

test('aucune consultation Storage et aucun lien pour les chemins invalides', async () => {
  for (const storagePath of [
    '', '../secret.pdf', 'docs/../secret.pdf', '/other.pdf',
    'docs//file.pdf', 'docs/file.pdf?token=x', 'docs/file%2epdf',
  ]) {
    const result = await invoke({
      accessLevel: 'account', visibility: 'private', signed: true,
      rank: 10, user: { id: UUID }, storagePath,
    });
    assert.equal(result.response.status, 503, storagePath);
    assert.equal(result.payload.ok, false, storagePath);
    assert.equal('url' in result.payload, false, storagePath);
    assert.equal(result.counters.bucketReads, 0, storagePath);
    assert.equal(result.counters.signedUrls, 0, storagePath);
  }
});

test('la signature autorisée passe par une lecture du bucket privé avant signature', async () => {
  const result = await invoke({
    accessLevel: 'account', visibility: 'private', signed: true,
    rank: 10, user: { id: UUID },
  });
  assert.equal(result.response.status, 200);
  assert.equal(result.payload.protected, true);
  assert.equal(result.counters.bucketReads, 1);
  assert.equal(result.counters.signedUrls, 1);
});

test('un projet non approuvé ou inactif demeure inaccessible', async () => {
  const pending = await invoke({ accessLevel: 'public', visibility: 'public', approved: false });
  assert.equal(pending.response.status, 404);
  const archived = await invoke({ accessLevel: 'public', visibility: 'public', active: false });
  assert.equal(archived.response.status, 404);
});

test('une réponse de signature ambiguë ne peut pas être livrée comme URL privée', async () => {
  const cases = [
    {data:{signedUrl:'https://storage.example.invalid/private-token'}},
    {data:{signedUrl:'https://storage.example.invalid/private-token'},error:false},
    {data:{signedUrl:'https://storage.example.invalid/private-token'},error:0},
    {data:{signedUrl:'https://storage.example.invalid/private-token'},error:''},
    {data:{signedUrl:true},error:null}, {data:{signedUrl:123},error:null},
    {data:{signedUrl:[]},error:null}, {data:{signedUrl:{}},error:null},
    {data:{signedUrl:'   '},error:null}, {data:null,error:null},
  ];
  for(const signedResponse of cases){
    const result=await invoke({accessLevel:'account',visibility:'private',signed:true,rank:10,user:{id:UUID},signedResponse});
    assert.equal(result.response.status,500);
    assert.equal(result.payload.ok,false);
    assert.equal('url' in result.payload,false);
    assert.equal(result.counters.bucketReads,1);
    assert.equal(result.counters.signedUrls,1);
  }
});
