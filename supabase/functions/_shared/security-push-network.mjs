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
    signal: createSecurityPushAbortSignal(),
  });
}
