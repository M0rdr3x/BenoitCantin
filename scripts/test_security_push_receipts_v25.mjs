import assert from 'node:assert/strict';
import {
  buildSecurityPushReceiptRequest,
  classifySecurityPushReceipt,
  resolveSecurityPushReceipts,
  SECURITY_PUSH_RECEIPT_MAX_BATCH,
} from '../supabase/functions/_shared/security-push-receipts.mjs';

const id = (n) => `receipt-${String(n).padStart(8, '0')}`;

assert.equal(SECURITY_PUSH_RECEIPT_MAX_BATCH, 1000);
assert.deepEqual(buildSecurityPushReceiptRequest([id(1), id(2)]), { ids: [id(1), id(2)] });
assert.equal(buildSecurityPushReceiptRequest(Array.from({ length: 1000 }, (_, i) => id(i))).ids.length, 1000);
assert.throws(() => buildSecurityPushReceiptRequest([]), /INVALID_EXPO_RECEIPT_BATCH/);
assert.throws(
  () => buildSecurityPushReceiptRequest(Array.from({ length: 1001 }, (_, i) => id(i))),
  /INVALID_EXPO_RECEIPT_BATCH/,
);
assert.throws(() => buildSecurityPushReceiptRequest(['short']), /INVALID_EXPO_RECEIPT_ID/);
assert.throws(() => buildSecurityPushReceiptRequest([id(1), id(1)]), /DUPLICATE_EXPO_RECEIPT_ID/);
assert.equal(buildSecurityPushReceiptRequest([`  ${id(3)}  `]).ids[0], id(3));

assert.equal(classifySecurityPushReceipt({ status: 'ok' }), 'provider_accepted');
assert.equal(
  classifySecurityPushReceipt({ status: 'error', details: { error: 'DeviceNotRegistered' } }),
  'device_not_registered',
);
assert.equal(
  classifySecurityPushReceipt({ status: 'error', details: { error: 'MessageRateExceeded' } }),
  'provider_error',
);
assert.equal(classifySecurityPushReceipt({ status: 'pending' }), 'invalid');
assert.equal(classifySecurityPushReceipt(null), 'invalid');

const pending = [
  { expo_receipt_id: id(11), endpoint_id: 'endpoint-a' },
  { expo_receipt_id: id(12), endpoint_id: 'endpoint-b' },
  { expo_receipt_id: id(13), endpoint_id: 'endpoint-c' },
];
const resolved = resolveSecurityPushReceipts(pending, {
  [id(11)]: { status: 'ok' },
  [id(12)]: { status: 'error', details: { error: 'DeviceNotRegistered' } },
});
assert.deepEqual(resolved, {
  handledReceiptIds: [id(11), id(12)],
  invalidEndpointIds: ['endpoint-b'],
});
assert.ok(!resolved.handledReceiptIds.includes(id(13)), 'un reçu absent de la réponse Expo doit rester en file');

const duplicateEndpoint = resolveSecurityPushReceipts(
  [
    { expo_receipt_id: id(21), endpoint_id: 'endpoint-z' },
    { expo_receipt_id: id(22), endpoint_id: 'endpoint-z' },
  ],
  {
    [id(21)]: { status: 'error', details: { error: 'DeviceNotRegistered' } },
    [id(22)]: { status: 'error', details: { error: 'DeviceNotRegistered' } },
  },
);
assert.deepEqual(duplicateEndpoint.invalidEndpointIds, ['endpoint-z']);

for (const forbidden of [
  'title',
  'body',
  'risk_score',
  'country_code',
  'region_code',
  'access_token',
  'refresh_token',
  'password',
  'session',
  'jwt',
]) {
  const serialized = JSON.stringify({ pending, resolved }).toLowerCase();
  assert.ok(!serialized.includes(forbidden), `matière non nécessaire interdite dans la file de reçus: ${forbidden}`);
}

console.log('OK security push receipts V25: requêtes <=1000, reçus absents conservés, DeviceNotRegistered isolé et aucune matière de notification persistée.');
