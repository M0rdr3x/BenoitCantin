import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
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
await new Promise((resolve) => setTimeout(resolve, 30));
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
assert.equal(captured.init.redirect, 'error', 'Aucun renvoi de token via HTTP 307/308');
assert.equal(captured.init.credentials, 'omit', 'Aucun cookie implicite vers Expo');
assert.equal(captured.init.referrerPolicy, 'no-referrer', 'Aucun référent externe');
assert.ok(captured.init.signal instanceof AbortSignal);
assert.equal(captured.init.signal.aborted, false);
assert.match(captured.init.body, /ExponentPushToken/);

await postSecurityPushJson(SECURITY_PUSH_RECEIPT_URL, { ids: ['receipt-00000001'] }, fakeFetch);
assert.equal(captured.url, SECURITY_PUSH_RECEIPT_URL);
assert.deepEqual(JSON.parse(captured.init.body), { ids: ['receipt-00000001'] });

let timedOutSignal = null;
const stalledFetch = async (_url, init) => {
  timedOutSignal = init.signal;
  return await new Promise((resolve, reject) => {
    init.signal.addEventListener('abort', () => reject(init.signal.reason), { once: true });
    setTimeout(() => resolve({ ok: true, status: 200 }), SECURITY_PUSH_NETWORK_TIMEOUT_MS + 1000);
  });
};
await assert.rejects(
  () => postSecurityPushJson(SECURITY_PUSH_SEND_URL, {}, stalledFetch),
  (error) => error?.name === 'TimeoutError',
);
assert.equal(timedOutSignal.aborted, true);

await assert.rejects(
  () => postSecurityPushJson('https://example.com/push', {}, fakeFetch),
  /INVALID_SECURITY_PUSH_URL/,
);
await assert.rejects(
  () => postSecurityPushJson(SECURITY_PUSH_SEND_URL, {}, null),
  /INVALID_SECURITY_PUSH_FETCH/,
);

// Test d'intégration isolé : un fournisseur simulé renvoie 307 vers un
// second serveur local. Un POST de jeton ne doit JAMAIS atteindre ce serveur.
let forwardedRequests = 0;
const destination = createServer((req, res) => {
  forwardedRequests += 1;
  req.resume();
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end('{}');
});
const redirector = createServer((_req, res) => {
  res.writeHead(307, { Location: `http://127.0.0.1:${destination.address().port}/capture` });
  res.end();
});
try {
  destination.listen(0, '127.0.0.1');
  await once(destination, 'listening');
  redirector.listen(0, '127.0.0.1');
  await once(redirector, 'listening');
  const origin = `http://127.0.0.1:${redirector.address().port}/push`;
  const sensitiveToken = 'ExponentPushToken[synthetic-never-real]';
  await assert.rejects(
    () => postSecurityPushJson(
      SECURITY_PUSH_SEND_URL,
      [{ to: sensitiveToken }],
      (_url, init) => fetch(origin, init),
    ),
    /fetch failed|redirect|network|TypeError/i,
    'Une redirection HTTP 307 doit faire échouer un POST de notifications',
  );
  assert.equal(forwardedRequests, 0,
    'Aucun jeton de notification ne doit être retransmis à la destination de la redirection');
} finally {
  redirector.closeAllConnections();
  destination.closeAllConnections();
  if (redirector.listening) await new Promise(resolve => redirector.close(resolve));
  if (destination.listening) await new Promise(resolve => destination.close(resolve));
}

console.log('OK security push network V25: endpoints Expo exacts, POST JSON centralisé, pas de redirection/cookies/référents, tests HTTP 307 local et timeout 4s réellement observé.');
