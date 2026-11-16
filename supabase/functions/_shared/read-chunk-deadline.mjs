/**
 * Read one chunk using a single absolute (monotonic) deadline shared by the
 * entire request body. A slow client must not reset the budget per chunk.
 * Cancellation is best-effort and never awaited, even for a stalled source.
 */
export function readChunkWithDeadline(reader, signal, deadlineAt) {
  if (!reader || typeof reader.read !== 'function' ||
      !Number.isFinite(deadlineAt)) {
    throw new TypeError('Invalid bounded stream reader');
  }

  return new Promise((resolve, reject) => {
    let settled = false;
    let timer;
    const cleanup = () => {
      clearTimeout(timer);
      signal?.removeEventListener('abort', abort);
    };
    const abort = () => {
      if (settled) return;
      settled = true;
      cleanup();
      try {
        void Promise.resolve(reader.cancel('REQUEST_TIMEOUT')).catch(() => {});
      } catch { /* Cancellation is advisory; the request is already rejected. */ }
      reject(new Error('REQUEST_TIMEOUT'));
    };

    const remainingMs = deadlineAt - performance.now();
    if (signal?.aborted || remainingMs <= 0) {
      abort();
      return;
    }
    timer = setTimeout(abort, remainingMs);
    signal?.addEventListener('abort', abort, { once: true });
    if (signal?.aborted) {
      abort();
      return;
    }
    Promise.resolve().then(() => reader.read()).then(
      chunk => {
        if (settled) return;
        settled = true;
        cleanup();
        resolve(chunk);
      },
      error => {
        if (settled) return;
        settled = true;
        cleanup();
        reject(error);
      }
    );
  });
}

/**
 * Lire un corps UTF-8 avec le même délai ABSOLU pour tous les fragments.
 * Le plafond réel en octets et Content-Length sont contrôlés séparément.
 * Les erreurs ne contiennent jamais les données ou diagnostics du client.
 */
export async function readLimitedUtf8BodyWithDeadline(req, maxBytes, timeoutMs = 8000) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 0 ||
      !Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000) {
    throw new TypeError('INVALID_REQUEST_BODY_BOUNDARY');
  }

  const declared = req.headers.get('content-length');
  if (declared !== null &&
      (!/^(0|[1-9][0-9]*)$/.test(declared) ||
       !Number.isSafeInteger(Number(declared)) ||
       Number(declared) > maxBytes)) {
    return { ok: false, reason: 'REQUEST_TOO_LARGE' };
  }

  if (req.signal?.aborted) return { ok: false, reason: 'REQUEST_TIMEOUT' };
  if (!req.body) return { ok: true, raw: '' };

  const reader = req.body.getReader();
  const deadlineAt = performance.now() + timeoutMs;
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let byteCount = 0;
  let raw = '';
  try {
    while (true) {
      const { done, value } = await readChunkWithDeadline(reader, req.signal, deadlineAt);
      if (done) break;
      if (!(value instanceof Uint8Array) || value.byteLength > maxBytes - byteCount) {
        // Ne jamais attendre une annulation qui peut elle-même rester bloquée.
        try { void Promise.resolve(reader.cancel('REQUEST_TOO_LARGE')).catch(() => {}); }
        catch { /* La réponse est déjà refusée. */ }
        return { ok: false, reason: 'REQUEST_TOO_LARGE' };
      }
      byteCount += value.byteLength;
      raw += decoder.decode(value, { stream: true });
    }
    raw += decoder.decode();
    return { ok: true, raw };
  } catch (error) {
    return {
      ok: false,
      reason: error?.message === 'REQUEST_TIMEOUT' ? 'REQUEST_TIMEOUT' : 'INVALID_BODY'
    };
  } finally {
    try { reader.releaseLock(); } catch { /* Lecture abandonnée. */ }
  }
}
