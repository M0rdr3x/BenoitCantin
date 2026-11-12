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

  const empty = new Request('https://example.invalid/edge', { method: 'POST' });
  assert.deepEqual(await readLimitedUtf8Body(empty, 8), { ok: true, raw: '' });
  // Flux bloqué après un premier fragment : expiration de durée, sans
  // attendre le fournisseur malveillant qui ne termine jamais cancel().
  const neverFinishes = new Request('https://example.invalid/edge', {
    method: 'POST', duplex: 'half',
    body: new ReadableStream({
      start(controller) { controller.enqueue(encoder.encode('part')); },
      cancel() { return new Promise(() => {}); }
    })
  });
  const startedAt = Date.now();
  assert.deepEqual(await readLimitedUtf8Body(neverFinishes, 8, 30), { ok: false });
  assert.ok(Date.now() - startedAt < 1000, 'La lecture bloquée doit être interrompue.');

  // L'abandon du client doit interrompre immédiatement la lecture partielle.
  const abort = new AbortController();
  const abandoned = new Request('https://example.invalid/edge', {
    method: 'POST', duplex: 'half', signal: abort.signal,
    body: new ReadableStream({ start(controller) { controller.enqueue(encoder.encode('abc')); } })
  });
  const pending = readLimitedUtf8Body(abandoned, 8, 1000);
  abort.abort();
  assert.deepEqual(await pending, { ok: false });

  await assert.rejects(readLimitedUtf8Body(streamRequest([encoder.encode('x')]), 8, 0), TypeError);

  const reportSource = readFileSync(resolve(root, 'supabase/functions/send-game-report/index.ts'), 'utf8');
  assert.ok(reportSource.includes('AbortSignal.timeout(MAX_TEMPLATE_FETCH_MS)'),
    'Le téléchargement PDF doit avoir une durée totale maximale.');

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
