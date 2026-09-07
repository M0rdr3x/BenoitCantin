export const SECURITY_PUSH_PATH = '/compte/securite.html';
export const SECURITY_PUSH_MAX_BATCH = 100;

const SECURITY_PUSH_TITLE = 'Sécurité SINJIRA';
const SECURITY_PUSH_BODIES = Object.freeze({
  challenge: 'Une connexion inhabituelle demande votre attention.',
  block: 'SINJIRA a bloqué une tentative nécessitant votre attention.',
});

export function buildSecurityPushMessage(expoPushToken, outcome) {
  const token = typeof expoPushToken === 'string' ? expoPushToken.trim() : '';
  if (token.length < 20 || token.length > 300) {
    throw new TypeError('INVALID_EXPO_PUSH_TOKEN');
  }
  if (!Object.hasOwn(SECURITY_PUSH_BODIES, outcome)) {
    throw new TypeError('INVALID_SECURITY_PUSH_OUTCOME');
  }

  return {
    to: token,
    sound: null,
    title: SECURITY_PUSH_TITLE,
    body: SECURITY_PUSH_BODIES[outcome],
    data: { path: SECURITY_PUSH_PATH },
    channelId: 'security',
    priority: 'high',
    ttl: 600,
  };
}
