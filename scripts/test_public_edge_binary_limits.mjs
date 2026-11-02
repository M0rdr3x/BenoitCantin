#!/usr/bin/env node
// Runtime security tests: the real Edge helper must reject oversized PDF
// downloads BEFORE buffering the whole remote response.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readLimitedBinaryResponse } from '../supabase/functions/_shared/limited-body.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const encoder = new TextEncoder();
const pdf = encoder.encode('%PDF-1.7\n');

function streamResponse(chunks, headers = {}, onCancel = () => {}) {
  return new Response(new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(chunk);
      controller.close();
    },
    cancel(reason) { onCancel(reason); }
  }), { headers });
}

function rejectResult(result) {
  assert.deepEqual(result, { ok: false }, 'Invalid stream must expose no bytes');
}

async function run() {
  const expected = { ok: true, bytes: pdf };
  assert.deepEqual(await readLimitedBinaryResponse(streamResponse([pdf]), pdf.byteLength), expected);

  const chunks = [pdf.subarray(0, 2), pdf.subarray(2, 5), pdf.subarray(5)];
  assert.deepEqual(await readLimitedBinaryResponse(streamResponse(chunks), pdf.byteLength), expected);

  // A valid declared length must not replace the actual streaming byte limit.
  assert.deepEqual(await readLimitedBinaryResponse(streamResponse([pdf], {
    'content-length': String(pdf.byteLength)
  }), pdf.byteLength), expected);

  rejectResult(await readLimitedBinaryResponse(streamResponse([pdf]), pdf.byteLength - 1));
  rejectResult(await readLimitedBinaryResponse(streamResponse(chunks), pdf.byteLength - 1));
  rejectResult(await readLimitedBinaryResponse(streamResponse([pdf], {
    'content-length': '1'
  }), pdf.byteLength - 1));

  // A forged Content-Length must not allow unbounded reads.
  let oversizedHeaderRead = false;
  const oversizedHeaderResponse = new Response(new ReadableStream({
    pull() { oversizedHeaderRead = true; }
  }, { highWaterMark: 0 }), {
    headers: { 'content-length': String(pdf.byteLength + 1000) }
  });
  rejectResult(await readLimitedBinaryResponse(oversizedHeaderResponse, pdf.byteLength));
  assert.equal(oversizedHeaderRead, false, 'Reject oversized declared length before consuming data');

  for (const invalid of ['NaN', '-1', '+1', '1e100', '9007199254740993']) {
    rejectResult(await readLimitedBinaryResponse(
      streamResponse([pdf], { 'content-length': invalid }), pdf.byteLength
    ));
  }

  let cancelled = false;
  // Keep the source OPEN until the reader cancels it. A stream already
  // closed by the fixture cannot exercise the underlying cancel callback.
  const oversized = new Response(new ReadableStream({
    pull(controller) { controller.enqueue(new Uint8Array(pdf.byteLength + 1)); },
    cancel() { cancelled = true; }
  }, { highWaterMark: 0 }));
  rejectResult(await readLimitedBinaryResponse(oversized, pdf.byteLength));
  assert.equal(cancelled, true, 'Stop oversized streaming input immediately');

  rejectResult(await readLimitedBinaryResponse(streamResponse([]), pdf.byteLength));
  rejectResult(await readLimitedBinaryResponse(new Response(null), pdf.byteLength));

  const interrupted = new Response(new ReadableStream({
    start(controller) {
      controller.enqueue(pdf.subarray(0, 3));
      controller.error(new Error('sensitive upstream error'));
    }
  }));
  rejectResult(await readLimitedBinaryResponse(interrupted, pdf.byteLength));

  await assert.rejects(
    readLimitedBinaryResponse(streamResponse([pdf]), -1),
    TypeError
  );

  // Keep this test tied to the actual business code; a helper unused by the
  // report generator is not a mitigation.
  const report = readFileSync(resolve(root, 'supabase/functions/send-game-report/index.ts'), 'utf8');
  assert.match(report, /readLimitedBinaryResponse\(response,\s*MAX_TEMPLATE_BYTES\)/);
  assert.match(report, /MAX_TEMPLATE_BYTES=15\*1024\*1024/);
  assert.ok(report.includes("redirect:'error'"), 'Template redirects must be rejected');
  assert.ok(report.includes("url.origin!==TEMPLATE_ORIGIN"), 'Template origin must remain fixed');
  assert.ok(report.includes("!=='%PDF-'"), 'PDF signature must remain checked');
  assert.ok(!report.includes('await response.arrayBuffer()'), 'Unbounded PDF read is forbidden');
  console.log('PASS binary Edge: PDF streams capped, fake sizes, invalid headers, cancel on excess, interrupted/empty payloads, actual integration.');
}
await run();
