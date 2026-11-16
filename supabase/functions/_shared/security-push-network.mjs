export const SECURITY_PUSH_NETWORK_TIMEOUT_MS = 4000;
export const SECURITY_PUSH_SEND_URL = 'https://exp.host/--/api/v2/push/send';
export const SECURITY_PUSH_RECEIPT_URL = 'https://exp.host/--/api/v2/push/getReceipts';

const SECURITY_PUSH_NETWORK_URLS = new Set([
  SECURITY_PUSH_SEND_URL,
  SECURITY_PUSH_RECEIPT_URL,
]);

export function createSecurityPushAbortSignal(timeoutMs = SECURITY_PUSH_NETWORK_TIMEOUT_MS) {
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000) {
    throw new TypeError('INVALID_SECURITY_PUSH_TIMEOUT');
  }
  return AbortSignal.timeout(timeoutMs);
}

export async function postSecurityPushJson(url, payload, fetchImpl = globalThis.fetch) {
  if (!SECURITY_PUSH_NETWORK_URLS.has(url)) {
    throw new TypeError('INVALID_SECURITY_PUSH_URL');
  }
  if (typeof fetchImpl !== 'function') {
    throw new TypeError('INVALID_SECURITY_PUSH_FETCH');
  }

  return await fetchImpl(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
    // A 307/308 to another host would retransmit private Expo device tokens.
    // Never follow redirects or send ambient credentials to an upstream.
    redirect: 'error',
    credentials: 'omit',
    referrerPolicy: 'no-referrer',
    signal: createSecurityPushAbortSignal(),
  });
}
