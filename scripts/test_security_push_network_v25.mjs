import assert from 'node:assert/strict';
import {
  SECURITY_PUSH_NETWORK_TIMEOUT_MS,
  SECURITY_PUSH_RECEIPT_URL,
  SECURITY_PUSH_SEND_URL,
  createSecurityPushAbortSignal,
  postSecurityPushJson,
} from '../supabase/functions/_shared/security-push-network.mjs';

assert.equal(SECURITY_PUSH_NETWORK_TIMEOUT_MS, 4000);
assert.throws(() => createSecurityPushAbortSignal(0), /INVALID_SECURITY_PUSH_TIMEOUT/);
assert.throws(() => createSecurityPushAbortSignal(30001), /INVALID_SECURITY_PUSH_TIMEOUT/);
assert.throws(() => createSecurityPushAbortSignal(1.5), /INVALID_SECURITY_PUSH_TIMEOUT/);

const shortSignal = createSecurityPushAbortSignal(15);
assert.equal(shortSignal.aborted, false);
await new Promise((resolve) => shortSignal.addEventListener('abort', resolve, { once: true }));
assert.equal(shortSignal.aborted, true);

let captured = null;
const fakeFetch = async (url, init) => {
  captured = { url, init };
  return { ok: true, status: 200 };
};
const response = await postSecurityPushJson(
  SECURITY_PUSH_SEND_URL,
  [{ to: 'ExponentPushToken[test]', title: 'SINJIRA' }],
  fakeFetch,
);
assert.equal(response.ok, true);
assert.equal(captured.url, SECURITY_PUSH_SEND_URL);
assert.equal(captured.init.method, 'POST');
assert.equal(captured.init.headers['Content-Type'], 'application/json');
assert.equal(captured.init.headers.Accept, 'application/json');
assert.ok(captured.init.signal instanceof AbortSignal);
assert.equal(captured.init.signal.aborted, false);
assert.match(captured.init.body, /ExponentPushToken/);

await postSecurityPushJson(SECURITY_PUSH_RECEIPT_URL, { ids: ['receipt-00000001'] }, fakeFetch);
assert.equal(captured.url, SECURITY_PUSH_RECEIPT_URL);
assert.deepEqual(JSON.parse(captured.init.body), { ids: ['receipt-00000001'] });

await assert.rejects(
  () => postSecurityPushJson('https://example.com/push', {}, fakeFetch),
  /INVALID_SECURITY_PUSH_URL/,
);
await assert.rejects(
  () => postSecurityPushJson(SECURITY_PUSH_SEND_URL, {}, null),
  /INVALID_SECURITY_PUSH_FETCH/,
);

console.log('OK security push network V25: endpoints Expo exacts, POST JSON centralisé et timeout 4s via AbortSignal testé.');
