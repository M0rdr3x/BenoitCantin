import assert from 'node:assert/strict';
import { resolveSecurityPushTickets } from '../supabase/functions/_shared/security-push-receipts.mjs';
import {
  buildSecurityPushMessage,
  buildSecurityPushBatch,
  SECURITY_PUSH_MAX_BATCH,
  SECURITY_PUSH_PATH,
} from '../supabase/functions/_shared/security-push-policy.mjs';

const TOKEN = 'ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]';

assert.equal(SECURITY_PUSH_MAX_BATCH, 100, 'un lot Expo ne doit pas dépasser 100 messages');
assert.equal(SECURITY_PUSH_PATH, '/compte/securite.html');
assert.match(SECURITY_PUSH_PATH, /^\/(?!\/)/);
assert.ok(!SECURITY_PUSH_PATH.includes('?'));
assert.ok(!SECURITY_PUSH_PATH.includes('#'));

const challenge = buildSecurityPushMessage(TOKEN, 'challenge');
assert.deepEqual(challenge, {
  to: TOKEN,
  sound: null,
  title: 'Sécurité SINJIRA',
  body: 'Une connexion inhabituelle demande votre attention.',
  data: { path: '/compte/securite.html' },
  channelId: 'security',
  priority: 'high',
  ttl: 600,
});

const blocked = buildSecurityPushMessage(TOKEN, 'block');
assert.deepEqual(Object.keys(blocked.data), ['path']);
assert.equal(blocked.body, 'SINJIRA a bloqué une tentative nécessitant votre attention.');
assert.equal(blocked.data.path, SECURITY_PUSH_PATH);

for (const message of [challenge, blocked]) {
  assert.deepEqual(Object.keys(message.data), ['path']);
  const serialized = JSON.stringify(message).toLowerCase();
  for (const forbidden of [
    'user_id',
    'device_id',
    'endpoint_id',
    'risk_score',
    'country_code',
    'region_code',
    'access_token',
    'refresh_token',
    'password=',
    'session=',
    'jwt=',
  ]) {
    assert.ok(!serialized.includes(forbidden), `matière sensible interdite dans le push: ${forbidden}`);
  }
}

assert.throws(
  () => buildSecurityPushMessage(TOKEN, 'allow'),
  /INVALID_SECURITY_PUSH_OUTCOME/,
);
assert.throws(
  () => buildSecurityPushMessage(TOKEN, { outcome: 'challenge' }),
  /INVALID_SECURITY_PUSH_OUTCOME/,
  'le builder ne doit pas accepter directement un objet de contexte de sécurité',
);
assert.throws(
  () => buildSecurityPushMessage('x'.repeat(19), 'challenge'),
  /INVALID_EXPO_PUSH_TOKEN/,
);
assert.throws(
  () => buildSecurityPushMessage('x'.repeat(301), 'challenge'),
  /INVALID_EXPO_PUSH_TOKEN/,
);
for (const invalid of [
  'x'.repeat(20),
  'x'.repeat(300),
  'https://attacker.invalid/notification',
  'ExpoPushToken[valid]\\nInjected',
  'ExpoPushToken[valid] extra',
  'ExpoPushToken[with space]',
  'ExpoPushToken[<script>]',
  'ExponentPushToken[malformed/?]',
  'ExpoPushToken[',
  'expoPushToken[xxxxxxxxxxxxxxxxxxxxxx]',
]) {
  assert.throws(
    () => buildSecurityPushMessage(invalid, 'challenge'),
    /INVALID_EXPO_PUSH_TOKEN/,
    'Rejeter les jetons falsifiés ou non Expo avant le fournisseur'
  );
}
const MODERN = 'ExpoPushToken[xxxxxxxxxxxxxxxxxxxxxx]';
assert.equal(buildSecurityPushMessage(MODERN, 'challenge').to, MODERN);
assert.equal(buildSecurityPushMessage(`  ${TOKEN}  `, 'challenge').to, TOKEN);

// One invalid recipient must not suppress the valid alert; preserving the
// index alignment matters for Expo's ticket -> endpoint receipt attribution.
const endpoints = [
  { id: 'endpoint-1', expo_push_token: TOKEN },
  { id: 'endpoint-bad', expo_push_token: 'https://attacker.invalid/tokens' },
  { id: 'endpoint-2', expo_push_token: MODERN },
];
const batch = buildSecurityPushBatch(endpoints, 'block');
assert.deepEqual(batch.acceptedEndpoints, [endpoints[0], endpoints[2]]);
assert.deepEqual(batch.messages.map(m => m.to), [TOKEN, MODERN]);
assert.deepEqual(batch.invalidEndpointIds, ['endpoint-bad']);
const tickets = resolveSecurityPushTickets(
  [
    { status: 'ok', id: 'receipt-00000001' },
    { status: 'error', details: { error: 'DeviceNotRegistered' } },
  ], batch.acceptedEndpoints
);
assert.deepEqual(tickets.receiptRows, [
  { expo_receipt_id: 'receipt-00000001', endpoint_id: 'endpoint-1' }
]);
assert.deepEqual(tickets.invalidEndpointIds, ['endpoint-2'],
  'Un ticket Expo ne doit jamais révoquer un autre appareil après filtrage');

const onlyBad = buildSecurityPushBatch([endpoints[1]], 'challenge');
assert.equal(onlyBad.messages.length, 0);
assert.deepEqual(onlyBad.invalidEndpointIds, ['endpoint-bad']);
assert.deepEqual(buildSecurityPushBatch([], 'challenge').messages, []);
assert.throws(
  () => buildSecurityPushBatch(Array.from({length:101}, () => endpoints[0]), 'challenge'),
  /INVALID_EXPO_PUSH_BATCH/
);
assert.throws(() => buildSecurityPushBatch(endpoints, 'allow'), /INVALID_SECURITY_PUSH_OUTCOME/);
assert.throws(() => buildSecurityPushBatch('not-an-array', 'block'), /INVALID_EXPO_PUSH_BATCH/);

console.log('OK security push policy V25: format Expo strict, isoler les jetons invalides, aligner tickets et appareils, payload minimal et lots <= 100.');
