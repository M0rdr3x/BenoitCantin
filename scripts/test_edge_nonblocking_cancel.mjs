import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import {
  readLimitedUtf8Body,
  readLimitedBinaryResponse,
} from '../supabase/functions/_shared/limited-body.mjs';

// Exécuter le véritable helper Edge, sans requête réseau ni secret.
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(resolve(root, 'supabase/functions/_shared/limited-body.mjs'), 'utf8');

function mockStream(chunks, { cancelMode = 'pending', failRead = false } = {}) {
  const state = { reads: 0, cancels: 0, released: 0 };
  const reader = {
    async read() {
      state.reads++;
      if (failRead) throw new Error('SECRET_UPSTREAM_ERROR_DO_NOT_LOG');
      if (chunks.length) return { done: false, value: chunks.shift() };
      return { done: true, value: undefined };
    },
    cancel() {
      state.cancels++;
      if (cancelMode === 'throw') throw new Error('SECRET_CANCEL_ERROR');
      if (cancelMode === 'reject') return Promise.reject(new Error('SECRET_CANCEL_ERROR'));
      if (cancelMode === 'pending') return new Promise(() => {});
      return Promise.resolve();
    },
    releaseLock() { state.released++; },
  };
  return { state, body: { getReader: () => reader } };
}

async function promptly(work, context) {
  let timer;
  const start = performance.now();
  try {
    const result = await Promise.race([
      Promise.resolve().then(work),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('BLOCAGE_CANCEL: ' + context)), 350);
      }),
    ]);
    assert.ok(performance.now() - start < 350, context + ' doit terminer sans attendre cancel()');
    return result;
  } finally {
    clearTimeout(timer);
  }
}

test('le contrat Edge ne peut plus attendre reader.cancel()', () => {
  assert.ok(source.includes('function cancelReaderWithoutWaiting(reader)'));
  assert.ok(source.includes('void Promise.resolve(reader.cancel()).catch(() => {})'));
  assert.ok(!/\bawait\s+reader\.cancel\s*\(/.test(source));
  assert.equal((source.match(/cancelReaderWithoutWaiting\(reader\);/g) || []).length, 4);
});

test('requête trop volumineuse : refus immédiat malgré cancel() qui ne résout jamais', async () => {
  const stream = mockStream([new TextEncoder().encode('123456789')]);
  const result = await promptly(
    () => readLimitedUtf8Body({ headers: new Headers(), body: stream.body }, 8),
    'requête trop volumineuse'
  );
  assert.deepEqual(result, { ok: false });
  assert.equal(stream.state.cancels, 1);
  assert.equal(stream.state.released, 1);
});

test('UTF-8 invalide : refus immédiat même lorsque cancel() ne résout jamais', async () => {
  const stream = mockStream([new Uint8Array([0xff])]);
  const result = await promptly(
    () => readLimitedUtf8Body({ headers: new Headers(), body: stream.body }, 8),
    'UTF-8 malformé'
  );
  assert.deepEqual(result, { ok: false });
  assert.equal(stream.state.cancels, 1);
  assert.equal(stream.state.released, 1);
});

test('erreur de lecture privée : aucun contenu ni diagnostic transmis', async () => {
  const stream = mockStream([], { failRead: true });
  const result = await promptly(
    () => readLimitedUtf8Body({ headers: new Headers(), body: stream.body }, 8),
    'erreur lecture entrée'
  );
  assert.deepEqual(result, { ok: false });
  assert.equal(stream.state.cancels, 1);
  assert.equal(stream.state.released, 1);
});

test('réponse PDF trop grande : refus immédiat avec annulation bloquée', async () => {
  const stream = mockStream([new Uint8Array(10)]);
  const result = await promptly(
    () => readLimitedBinaryResponse({ headers: new Headers(), body: stream.body }, 8),
    'PDF trop grand'
  );
  assert.deepEqual(result, { ok: false });
  assert.equal(stream.state.cancels, 1);
  assert.equal(stream.state.released, 1);
});

test('erreur de flux PDF : refus sans attente et sans divulgation upstream', async () => {
  const stream = mockStream([], { failRead: true });
  const result = await promptly(
    () => readLimitedBinaryResponse({ headers: new Headers(), body: stream.body }, 8),
    'erreur téléchargement PDF'
  );
  assert.deepEqual(result, { ok: false });
  assert.equal(stream.state.cancels, 1);
  assert.equal(stream.state.released, 1);
});

test('annulation qui échoue, même de façon synchrone, ne bloque jamais', async () => {
  for (const cancelMode of ['throw', 'reject']) {
    for (const binary of [false, true]) {
      const stream = mockStream([new Uint8Array(10)], { cancelMode });
      const read = binary ? readLimitedBinaryResponse : readLimitedUtf8Body;
      const result = await promptly(
        () => read({ headers: new Headers(), body: stream.body }, 8),
        'annulation ' + cancelMode + ', binaire=' + binary
      );
      assert.deepEqual(result, { ok: false });
      assert.equal(stream.state.cancels, 1);
      assert.equal(stream.state.released, 1);
    }
  }
});

test('flux valides préservés et Content-Length trompeur refusé avant lecture', async () => {
  const plain = mockStream([new TextEncoder().encode('{"ok":true}')]);
  assert.deepEqual(
    await readLimitedUtf8Body({ headers: new Headers(), body: plain.body }, 11),
    { ok: true, raw: '{"ok":true}' }
  );
  assert.equal(plain.state.cancels, 0);
  assert.equal(plain.state.released, 1);

  const bytes = new Uint8Array([37, 80, 68, 70, 45]);
  const pdf = mockStream([bytes]);
  assert.deepEqual(
    await readLimitedBinaryResponse({ headers: new Headers(), body: pdf.body }, 5),
    { ok: true, bytes }
  );
  assert.equal(pdf.state.cancels, 0);
  assert.equal(pdf.state.released, 1);

  const neverRead = mockStream([bytes]);
  assert.deepEqual(
    await readLimitedBinaryResponse({
      headers: new Headers({ 'content-length': '1000000000' }),
      body: neverRead.body,
    }, 5),
    { ok: false }
  );
  assert.equal(neverRead.state.reads, 0);
});

function stalledReader() {
  const state = { reads: 0, cancels: 0, released: 0 };
  const reader = {
    read() { state.reads++; return new Promise(() => {}); },
    cancel() { state.cancels++; return new Promise(() => {}); },
    releaseLock() { state.released++; },
  };
  return { state, body: { getReader: () => reader } };
}

test('les lecteurs partagent une échéance totale explicite', () => {
  assert.match(source, /performance\.now\(\) \+ 8_000/);
  assert.match(source, /performance\.now\(\) \+ 30_000/);
  assert.match(source, /readChunkWithDeadline\(reader, req\.signal, deadlineAt\)/);
  assert.match(source, /readChunkWithDeadline\(reader, null, deadlineAt\)/);
  assert.equal((source.match(/await reader\.read\(\)/g) || []).length, 0);
});

test('une requête interrompue ne monopolise pas un lecteur bloqué', async () => {
  const stuck = stalledReader();
  const controller = new AbortController();
  const pending = promptly(
    () => readLimitedUtf8Body({
      headers: new Headers(), body: stuck.body, signal: controller.signal,
    }, 1024),
    'lecture HTTP interrompue'
  );
  setTimeout(() => controller.abort(), 20);
  assert.deepEqual(await pending, { ok: false });
  assert.equal(stuck.state.reads, 1);
  assert.ok(stuck.state.cancels >= 1);
  assert.equal(stuck.state.released, 1);
});

test('la réponse binaire conserve une limite de lecture totale', () => {
  assert.match(source, /export async function readLimitedBinaryResponse\(response, maxBytes\)/);
  assert.match(source, /readChunkWithDeadline\(reader, null, deadlineAt\)/);
});
