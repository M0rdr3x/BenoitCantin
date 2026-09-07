import assert from 'node:assert/strict';
import {
  buildSecurityPushMessage,
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
assert.equal(buildSecurityPushMessage('x'.repeat(20), 'challenge').to.length, 20);
assert.equal(buildSecurityPushMessage('x'.repeat(300), 'block').to.length, 300);
assert.equal(buildSecurityPushMessage(`  ${TOKEN}  `, 'challenge').to, TOKEN);

console.log('OK security push policy V25: payload minimal, chemin interne fixe, données sensibles absentes et lot Expo borné à 100.');
