export const SECURITY_PUSH_PATH = '/compte/securite.html';
export const SECURITY_PUSH_MAX_BATCH = 100;

// Expo clients accept only the two Expo Push Token envelope formats.
const EXPO_TOKEN_RE = /^(?:ExpoPushToken|ExponentPushToken)\[[A-Za-z0-9_-]+\]$/;
const SECURITY_PUSH_TITLE = 'Sécurité SINJIRA';
const SECURITY_PUSH_BODIES = Object.freeze({
  challenge: 'Une connexion inhabituelle demande votre attention.',
  block: 'SINJIRA a bloqué une tentative nécessitant votre attention.',
});

export function buildSecurityPushMessage(expoPushToken, outcome) {
  const token = typeof expoPushToken === 'string' ? expoPushToken.trim() : '';
  if (token.length < 20 || token.length > 300 || !EXPO_TOKEN_RE.test(token)) {
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

/**
 * Isolate malformed endpoints rather than suppressing alerts for other
 * devices. Keep returned messages and endpoint rows index-aligned so Expo
 * tickets cannot disable or attribute receipts to the wrong device.
 */
export function buildSecurityPushBatch(endpointRows, outcome) {
  if (!Array.isArray(endpointRows) || endpointRows.length > SECURITY_PUSH_MAX_BATCH) {
    throw new TypeError('INVALID_EXPO_PUSH_BATCH');
  }
  if (!Object.hasOwn(SECURITY_PUSH_BODIES, outcome)) {
    throw new TypeError('INVALID_SECURITY_PUSH_OUTCOME');
  }

  const messages = [];
  const acceptedEndpoints = [];
  const invalidEndpointIds = [];
  for (const endpoint of endpointRows) {
    try {
      const message = buildSecurityPushMessage(endpoint?.expo_push_token, outcome);
      if (typeof endpoint?.id !== 'string' || !endpoint.id.trim()) {
        continue;
      }
      messages.push(message);
      acceptedEndpoints.push(endpoint);
    } catch (error) {
      if (!(error instanceof TypeError) || error.message !== 'INVALID_EXPO_PUSH_TOKEN') {
        throw error;
      }
      if (typeof endpoint?.id === 'string' && endpoint.id.trim()) {
        invalidEndpointIds.push(endpoint.id);
      }
    }
  }

  return { messages, acceptedEndpoints, invalidEndpointIds };
}
