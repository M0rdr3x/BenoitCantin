#!/usr/bin/env node
// Isolated tests for the real Expo-response reader. No provider or user data.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  MAX_SECURITY_PUSH_RESPONSE_BYTES,
  SECURITY_PUSH_RESPONSE_TIMEOUT_MS,
  readBoundedSecurityPushJson,
} from '../supabase/functions/_shared/security-push-response.mjs';

function jsonResponse(value, headers = {}) {
  return new Response(JSON.stringify(value), {
    headers: { 'content-type': 'application/json; charset=utf-8', ...headers },
  });
}
const DEFAULT_LIMIT = { maxBytes: 128, timeoutMs: 100 };

test('retains valid Expo tickets and receipt JSON (no provider fetch)', async () => {
  const tickets = { data: [{ status: 'ok', id: 'receipt-000001' }] };
  const receipts = { data: { 'receipt-000001': { status: 'ok' } } };
  assert.deepEqual(await readBoundedSecurityPushJson(jsonResponse(tickets)), tickets);
  assert.deepEqual(await readBoundedSecurityPushJson(jsonResponse(receipts)), receipts);
  assert.equal(MAX_SECURITY_PUSH_RESPONSE_BYTES, 1024 * 1024);
  assert.equal(SECURITY_PUSH_RESPONSE_TIMEOUT_MS, 4000);
});

test('accepts a valid chunked JSON response without Content-Length', async () => {
  const encoder = new TextEncoder();
  const chunks = ['{"data":', '{"hello":true}', '}'];
  const body = new ReadableStream({
    start(controller) {
      for (const item of chunks) controller.enqueue(encoder.encode(item));
      controller.close();
    },
  });
  const r = new Response(body, { headers: { 'content-type': 'application/json' } });
  assert.deepEqual(await readBoundedSecurityPushJson(r, DEFAULT_LIMIT),
    { data: { hello: true } });
});

test('rejects malformed and deceptive Content-Length before reading body', async () => {
  for (const header of ['500', '-1', '1.5', 'bogus', '012', '9007199254740992']) {
    const response = jsonResponse({ data: [] }, { 'content-length': header });
    assert.equal(await readBoundedSecurityPushJson(response, DEFAULT_LIMIT), null,
      'Invalid declared size: ' + header);
  }
  const small = jsonResponse({ data: [] }, { 'content-length': '13' });
  assert.deepEqual(await readBoundedSecurityPushJson(small, DEFAULT_LIMIT), { data: [] });
});

test('actual stream bytes are checked even if Content-Length lies', async () => {
  const response = jsonResponse({ data: 'x'.repeat(500) }, { 'content-length': '10' });
  assert.equal(await readBoundedSecurityPushJson(response, DEFAULT_LIMIT), null);
  const exact = jsonResponse({ data: 'x'.repeat(25) });
  const declared = new TextEncoder().encode(JSON.stringify({ data: 'x'.repeat(25) })).length;
  assert.deepEqual(await readBoundedSecurityPushJson(exact, { maxBytes: declared, timeoutMs: 100 }),
    { data: 'x'.repeat(25) });
});

test('rejects unsafe MIME, malformed UTF-8, JSON arrays and invalid JSON', async () => {
  const wrong = jsonResponse({ data: [] }, { 'content-type': 'text/html' });
  assert.equal(await readBoundedSecurityPushJson(wrong, DEFAULT_LIMIT), null);
  const jsonp = jsonResponse({ data: [] }, { 'content-type': 'application/jsonp' });
  assert.equal(await readBoundedSecurityPushJson(jsonp, DEFAULT_LIMIT), null);
  assert.equal(await readBoundedSecurityPushJson(new Response(new Uint8Array([0xc3,0x28]),
    { headers: { 'content-type': 'application/json' } }), DEFAULT_LIMIT), null);
  assert.equal(await readBoundedSecurityPushJson(new Response('[1,2,3]'), DEFAULT_LIMIT), null);
  assert.equal(await readBoundedSecurityPushJson(new Response('{malformed'), DEFAULT_LIMIT), null);
  assert.equal(await readBoundedSecurityPushJson(new Response('null'), DEFAULT_LIMIT), null);
  assert.equal(await readBoundedSecurityPushJson(new Response('', { status: 204 }), DEFAULT_LIMIT), null);
});

test('non-200 or missing provider bodies are ignored', async () => {
  assert.equal(await readBoundedSecurityPushJson(jsonResponse({ error: 'server' },
    { 'content-length': '18' }), DEFAULT_LIMIT), null);
  assert.equal(await readBoundedSecurityPushJson(null, DEFAULT_LIMIT), null);
  assert.equal(await readBoundedSecurityPushJson({ ok: true, headers: new Headers() }, DEFAULT_LIMIT), null);
  const badStatus = new Response('{"data":"not valid"}', { status: 502 });
  assert.equal(await readBoundedSecurityPushJson(badStatus, DEFAULT_LIMIT), null);
});

test('hanging source and never-ending cancel cannot hold Edge invocation', async () => {
  let cancellations = 0;
  const response = {
    ok: true,
    headers: new Headers({ 'content-type': 'application/json' }),
    body: {
      getReader() {
        return {
          read: () => new Promise(() => {}),
          cancel: () => { cancellations++; return new Promise(() => {}); },
          releaseLock() {},
        };
      },
    },
  };
  const start = performance.now();
  assert.equal(await readBoundedSecurityPushJson(response, { timeoutMs: 30 }), null);
  assert.ok(performance.now() - start < 1500, 'No wait for hanging cancel()');
  assert.ok(cancellations > 0, 'Cancellation is attempted');
});

test('a trickle stream cannot reset the total deadline for each chunk', async () => {
  let readCount = 0;
  let cancellations = 0;
  const response = {
    ok: true,
    headers: new Headers({ 'content-type': 'application/json' }),
    body: {
      getReader: () => ({
        read: () => new Promise(resolve => setTimeout(() => {
          readCount++;
          resolve({ done: false, value: new Uint8Array([32]) });
        }, 25)),
        cancel: () => { cancellations++; return Promise.resolve(); },
        releaseLock() {},
      }),
    },
  };
  assert.equal(await readBoundedSecurityPushJson(response, { timeoutMs: 46 }), null);
  assert.ok(readCount < 4);
  assert.ok(cancellations > 0);
});

test('stream errors and invalid configuration fail closed', async () => {
  const broken = {
    ok: true,
    headers: new Headers(),
    body: {
      getReader: () => ({
        read: () => Promise.reject(new Error('private upstream internals')),
        cancel: () => Promise.resolve(),
        releaseLock() {},
      }),
    },
  };
  assert.equal(await readBoundedSecurityPushJson(broken, DEFAULT_LIMIT), null);
  assert.throws(() => readBoundedSecurityPushJson(jsonResponse({}),
    { maxBytes: 1_048_577 }), /INVALID_EXPO_RESPONSE_LIMIT/);
  assert.throws(() => readBoundedSecurityPushJson(jsonResponse({}),
    { timeoutMs: 0 }), /INVALID_EXPO_RESPONSE_LIMIT/);
});
