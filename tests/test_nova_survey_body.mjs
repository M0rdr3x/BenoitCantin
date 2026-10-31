import test from 'node:test';
import assert from 'node:assert/strict';
import { MAX_REQUEST_BYTES, readBoundedJson } from '../supabase/functions/_shared/nova_survey_body.mjs';

const request = value => new Request('https://www.benoitcantin.com', { method: 'POST', body: value });

test('UTF-8 en fragments', async () => {
  const bytes = new TextEncoder().encode('{"message":"Québec"}');
  const body = new ReadableStream({
    start(controller) {
      for (const byte of bytes) controller.enqueue(Uint8Array.of(byte));
      controller.close();
    }
  });
  assert.deepEqual(await readBoundedJson({ body }), { message: 'Québec' });
});

test('exactement 8192 octets acceptés', async () => {
  const overhead = JSON.stringify({ v: '' }).length;
  const payload = JSON.stringify({ v: 'x'.repeat(MAX_REQUEST_BYTES - overhead) });
  assert.equal(new TextEncoder().encode(payload).byteLength, MAX_REQUEST_BYTES);
  assert.equal((await readBoundedJson(request(payload))).v.length, MAX_REQUEST_BYTES - overhead);
});

test('8193 octets refusés', async () => {
  await assert.rejects(readBoundedJson(request(' '.repeat(MAX_REQUEST_BYTES + 1))),
    { message: 'REQUEST_TOO_LARGE' });
});

test('flux disproportionné arrêté et annulé', async () => {
  let cancelled = false;
  const body = new ReadableStream({
    start(controller) { controller.enqueue(new Uint8Array(MAX_REQUEST_BYTES + 1)); },
    cancel() { cancelled = true; }
  });
  await assert.rejects(readBoundedJson({ body }), { message: 'REQUEST_TOO_LARGE' });
  assert.equal(cancelled, true);
});

test('JSON incomplet et corps absent refusés', async () => {
  for (const value of ['{bad', '{"v":', '']) {
    await assert.rejects(readBoundedJson(request(value)), { message: 'INVALID_JSON' });
  }
  await assert.rejects(readBoundedJson({ body: null }), { message: 'INVALID_JSON' });
});

test('UTF-8 invalide refusé', async () => {
  const body = new ReadableStream({
    start(controller) { controller.enqueue(Uint8Array.of(0xc3, 0x28)); controller.close(); }
  });
  await assert.rejects(readBoundedJson({ body }), { message: 'INVALID_JSON' });
});
