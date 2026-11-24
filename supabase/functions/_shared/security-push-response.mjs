/**
 * Bounded, fail-closed JSON intake for the two approved Expo Push endpoints.
 *
 * The sender transmits Expo device tokens to a third-party provider. A
 * provider/network error must not exhaust the Edge Function by returning an
 * unbounded or stalled HTTP 200 JSON response.
 *
 * Return null, never provider diagnostics, for malformed or oversized bodies.
 */
export const MAX_SECURITY_PUSH_RESPONSE_BYTES = 1024 * 1024;
export const SECURITY_PUSH_RESPONSE_TIMEOUT_MS = 4000;

function cancelWithoutWaiting(reader) {
  try {
    void Promise.resolve(reader.cancel()).catch(() => {});
  } catch { /* A failed cancellation must never delay the response. */ }
}

function readWithDeadline(reader, deadlineAt) {
  return new Promise((resolve, reject) => {
    let settled = false;
    let timer;
    const complete = (success, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (success) resolve(value);
      else reject(value);
    };
    const remaining = deadlineAt - performance.now();
    if (remaining <= 0) {
      complete(false, new Error('EXPO_RESPONSE_TIMEOUT'));
      return;
    }

    timer = setTimeout(() => {
      cancelWithoutWaiting(reader);
      complete(false, new Error('EXPO_RESPONSE_TIMEOUT'));
    }, remaining);
    Promise.resolve().then(() => reader.read()).then(
      chunk => complete(true, chunk),
      error => complete(false, error),
    );
  });
}

/**
 * Return the provider's parsed JSON object or null. The caller decides
 * whether it is a ticket list or a receipt object and validates its fields.
 * The optional limits only support deterministic isolated security tests.
 */
export async function readBoundedSecurityPushJson(
  response,
  { maxBytes = MAX_SECURITY_PUSH_RESPONSE_BYTES,
    timeoutMs = SECURITY_PUSH_RESPONSE_TIMEOUT_MS } = {},
) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1 ||
      maxBytes > MAX_SECURITY_PUSH_RESPONSE_BYTES ||
      !Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000) {
    throw new TypeError('INVALID_EXPO_RESPONSE_LIMIT');
  }

  if (!response?.ok || !response?.headers?.get || !response?.body?.getReader) {
    return null;
  }
  const reader = response.body.getReader();
  const deadlineAt = performance.now() + timeoutMs;
  const chunks = [];
  let byteCount = 0;
  try {
    const declared = response.headers.get('content-length');
    if (declared !== null && (
      !/^(0|[1-9][0-9]*)$/.test(declared) ||
      !Number.isSafeInteger(Number(declared)) ||
      Number(declared) > maxBytes
    )) {
      return null;
    }

    const contentType = response.headers.get('content-type');
    if (contentType !== null &&
        !/^application\/(?:json|[a-z0-9.+-]+\+json)(?:\s*;|\s*$)/i.test(contentType)) {
      return null;
    }

    while (true) {
      const { done, value } = await readWithDeadline(reader, deadlineAt);
      if (done) break;
      if (!(value instanceof Uint8Array) ||
          value.byteLength > maxBytes - byteCount) {
        return null;
      }
      byteCount += value.byteLength;
      chunks.push(value);
    }
    if (byteCount < 1) return null;
    const buffer = new Uint8Array(byteCount);
    let offset = 0;
    for (const chunk of chunks) {
      buffer.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const result = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(buffer));
    return result !== null && typeof result === 'object' && !Array.isArray(result)
      ? result
      : null;
  } catch {
    return null;
  } finally {
    // Reader cancellation may be permanently pending: never await it.
    cancelWithoutWaiting(reader);
    try { reader.releaseLock(); } catch { /* A read may still be settling. */ }
  }
}
