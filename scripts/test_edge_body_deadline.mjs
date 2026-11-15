import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { readChunkWithDeadline } from '../supabase/functions/_shared/read-chunk-deadline.mjs';

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

test('valid chunk is returned before the absolute deadline', async () => {
  const reader = { read: async () => ({ done: false, value: Uint8Array.of(42) }) };
  const result = await readChunkWithDeadline(reader, new AbortController().signal, performance.now() + 500);
  assert.deepEqual([...result.value], [42]);
});

test('never-resolving read is rejected, even when upstream cancellation hangs', async () => {
  let cancellations = 0;
  const reader = {
    read: () => new Promise(() => {}),
    cancel: () => { cancellations++; return new Promise(() => {}); }
  };
  await assert.rejects(readChunkWithDeadline(reader, null, performance.now() + 40), { message: 'REQUEST_TIMEOUT' });
  assert.equal(cancellations, 1);
});

test('trickle data does not reset the global deadline', async () => {
  let cancellations = 0;
  const reader = {
    read: async () => { await sleep(40); return { done: false, value: Uint8Array.of(1) }; },
    cancel: async () => { cancellations++; }
  };
  const deadline = performance.now() + 70;
  await readChunkWithDeadline(reader, null, deadline);
  await assert.rejects(readChunkWithDeadline(reader, null, deadline), { message: 'REQUEST_TIMEOUT' });
  assert.equal(cancellations, 1);
});

test('aborted requests reject without waiting for the upstream', async () => {
  const controller = new AbortController();
  let cancellations = 0;
  const reader = { read: () => new Promise(() => {}), cancel: async () => { cancellations++; } };
  const pending = readChunkWithDeadline(reader, controller.signal, performance.now() + 1000);
  controller.abort();
  await assert.rejects(pending, { message: 'REQUEST_TIMEOUT' });
  assert.equal(cancellations, 1);
});

test('pre-aborted signal never starts reading', async () => {
  const controller = new AbortController();
  controller.abort();
  let reads = 0;
  const reader = { read: () => { reads++; }, cancel: () => Promise.resolve() };
  await assert.rejects(readChunkWithDeadline(reader, controller.signal, performance.now() + 1000), { message: 'REQUEST_TIMEOUT' });
  assert.equal(reads, 0);
});

test('upstream stream errors propagate before the deadline', async () => {
  const reader = { read: () => Promise.reject(new Error('BROKEN_STREAM')) };
  await assert.rejects(readChunkWithDeadline(reader, null, performance.now() + 500), { message: 'BROKEN_STREAM' });
});

test('both sensitive Edge endpoints enforce a total 8-second deadline and reject malformed length', () => {
  for (const name of ['personal-ai', 'conscience-vault']) {
    const source = readFileSync(new URL(`../supabase/functions/${name}/index.ts`, import.meta.url), 'utf8');
    assert.match(source, /const BODY_READ_TIMEOUT_MS = 8_000;/);
    assert.match(source, /const deadlineAt = performance\.now\(\) \+ BODY_READ_TIMEOUT_MS;/);
    assert.match(source, /await readChunkWithDeadline\(reader, req\.signal, deadlineAt\)/);
    assert.match(source, /Number\.isSafeInteger\(Number\(declaredRaw\)\)/);
    assert.match(source, /total > MAX_REQUEST_BYTES/);
    assert.match(source, /new TextDecoder\('utf-8', \{ fatal: true \}\)/);
    assert.match(source, /REQUEST_TIMEOUT/);
    assert.match(source, /try \{ reader\.releaseLock\(\); \} catch/);
    assert.match(source, /408/);
  }
});
