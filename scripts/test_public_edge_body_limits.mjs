import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readLimitedUtf8Body } from '../supabase/functions/_shared/limited-body.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const encoder = new TextEncoder();

function streamRequest(chunks, headers = {}) {
  return new Request('https://example.invalid/edge', {
    method: 'POST',
    headers,
    duplex: 'half',
    body: new ReadableStream({
      start(controller) {
        for (const chunk of chunks) controller.enqueue(chunk);
        controller.close();
      }
    })
  });
}

async function run() {
  const valid = streamRequest([encoder.encode('{"ok":true}')]);
  assert.deepEqual(await readLimitedUtf8Body(valid, 11), { ok: true, raw: '{"ok":true}' });

  const unicode = streamRequest([new Uint8Array([0x7b, 0x22, 0xc3]), new Uint8Array([0xa9, 0x22, 0x7d])]);
  assert.deepEqual(await readLimitedUtf8Body(unicode, 7), { ok: true, raw: '{"é"}' });

  const exact = streamRequest([encoder.encode('12345678')]);
  assert.equal((await readLimitedUtf8Body(exact, 8)).ok, true);

  const excess = streamRequest([encoder.encode('1234'), encoder.encode('56789')]);
  assert.deepEqual(await readLimitedUtf8Body(excess, 8), { ok: false });

  const misleading = streamRequest([encoder.encode('123456789')], { 'content-length': '1' });
  assert.deepEqual(await readLimitedUtf8Body(misleading, 8), { ok: false });

  const oversizedHeader = streamRequest([encoder.encode('x')], { 'content-length': '9999999999' });
  assert.deepEqual(await readLimitedUtf8Body(oversizedHeader, 8), { ok: false });

  const badHeader = streamRequest([encoder.encode('x')], { 'content-length': 'NaN' });
  assert.deepEqual(await readLimitedUtf8Body(badHeader, 8), { ok: false });

  const invalidUtf8 = streamRequest([new Uint8Array([0xc3])]);
  assert.deepEqual(await readLimitedUtf8Body(invalidUtf8, 8), { ok: false });

  // Une connexion lente sans fin doit respecter un budget ABSOLU partagé entre
  // tous les fragments; la première lecture ne peut pas rester pendante.
  const readerSource = readFileSync(resolve(root, 'supabase/functions/_shared/limited-body.mjs'), 'utf8');
  assert.match(readerSource, /UTF8_BODY_DEADLINE_MS = 8000/);
  assert.match(readerSource, /const deadlineAt = performance\.now\(\) \+ UTF8_BODY_DEADLINE_MS/);
  assert.match(readerSource, /await readChunkWithDeadline\(reader, req\.signal, deadlineAt\)/);
  // Le lecteur PDF distinct conserve son propre traitement : seule la
  // fonction UTF-8 doit bannir reader.read() sans échéance.
  const utf8Source = readerSource.split('export async function readLimitedBinaryResponse')[0];
  assert.doesNotMatch(utf8Source, /await reader\.read\(\)/);

  const alreadyAborted = new AbortController();
  alreadyAborted.abort();
  const abortedRequest = new Request('https://example.invalid/edge', {
    method: 'POST', signal: alreadyAborted.signal
  });
  assert.deepEqual(await readLimitedUtf8Body(abortedRequest, 8), { ok: false });

  const interrupt = new AbortController();
  const hangingRequest = new Request('https://example.invalid/edge', {
    method: 'POST', duplex: 'half', signal: interrupt.signal,
    body: new ReadableStream({ start(controller) { controller.enqueue(encoder.encode('a')); } })
  });
  const pending = readLimitedUtf8Body(hangingRequest, 8);
  setTimeout(() => interrupt.abort(), 25);
  const abortResult = await Promise.race([
    pending,
    new Promise((_, reject) => setTimeout(() => reject(new Error('abort non borné')), 1500))
  ]);
  assert.deepEqual(abortResult, { ok: false });

  const empty = new Request('https://example.invalid/edge', { method: 'POST' });
  assert.deepEqual(await readLimitedUtf8Body(empty, 8), { ok: true, raw: '' });

  for (const [path, marker] of [
    ['supabase/functions/get-document-url/index.ts', 'readLimitedUtf8Body(req,MAX_REQUEST_BYTES)'],
    ['supabase/functions/send-game-report/index.ts', 'readLimitedUtf8Body(req, MAX_REQUEST_BYTES)'],
    ['supabase/functions/life-story-delivery/index.ts', 'readLimitedUtf8Body(req, MAX_REQUEST_BYTES)'],
  ]) {
    const source = readFileSync(resolve(root, path), 'utf8');
    assert.ok(source.includes("limited-body.mjs"), path + ': import absent');
    assert.ok(source.includes(marker), path + ': stream non limité');
    assert.ok(!source.includes('await req.text()'), path + ': lecture non bornée');
    assert.ok(!source.includes('await req.json()'), path + ': JSON non borné');
  }
  console.log('PASS: limites de corps HTTP en flux, UTF-8, headers trompeurs et intégration des 3 fonctions publiques.');
}
await run();
