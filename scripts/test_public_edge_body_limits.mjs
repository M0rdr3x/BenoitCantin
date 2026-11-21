import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readLimitedUtf8Body } from '../supabase/functions/_shared/limited-body.mjs';
import { readLimitedUtf8BodyWithDeadline } from '../supabase/functions/_shared/read-chunk-deadline.mjs';

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

  // Droit de lecture d'un roman privé : même contrôle réel, délai absolu et
  // annulation NON BLOQUANTE si un attaquant fige à la fois read et cancel.
  const novelValid = streamRequest([encoder.encode('{"slug":"livre-prive"}')]);
  assert.deepEqual(
    await readLimitedUtf8BodyWithDeadline(novelValid, 2048, 200),
    { ok: true, raw: '{"slug":"livre-prive"}' }
  );
  let cancellationCount = 0;
  const never = new Request('https://example.invalid/edge', {
    method: 'POST',
    duplex: 'half',
    body: new ReadableStream({
      pull() { return new Promise(() => {}); },
      cancel() { cancellationCount++; return new Promise(() => {}); }
    })
  });
  const before = performance.now();
  assert.deepEqual(await readLimitedUtf8BodyWithDeadline(never, 2048, 40),
    { ok: false, reason: 'REQUEST_TIMEOUT' });
  assert.ok(performance.now() - before < 1000, 'Une annulation bloquée doit finir rapidement');
  assert.equal(cancellationCount, 1, 'Une annulation doit être tentée au délai');

  const novelSrc = readFileSync(
    resolve(root, 'supabase/functions/get-novel-file-url/index.ts'), 'utf8'
  );
  for (const guard of [
    'MAX_REQUEST_BYTES=2048',
    'MAX_REQUEST_READ_TIMEOUT_MS=4_000',
    'readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,MAX_REQUEST_READ_TIMEOUT_MS)',
    "message==='REQUEST_TIMEOUT'",
    "message==='UNSUPPORTED_MEDIA_TYPE'",
    "message==='AUTH_REQUIRED'",
    'createSignedUrl(novel.private_storage_path,600'
  ]) {
    assert.ok(novelSrc.includes(guard), 'Contrat get-novel-file-url absent: ' + guard);
  }
  assert.match(novelSrc, /\/\^application\\\/json\(\?:\\s\*;\|\$\)\/.test\(contentType\)/);
  assert.ok(!novelSrc.includes('await reader.cancel()'), 'Annulation bloquante interdite');
  assert.ok(!novelSrc.includes('await req.text()'), 'Lecture du corps illimitée interdite');
  assert.ok(!novelSrc.includes('await req.json()'), 'Lecture JSON illimitée interdite');

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
  console.log('PASS: lecture HTTP bornée, URL roman privé avec deadline absolue, annulation bloquée et fonctions publiques.');
}
await run();
