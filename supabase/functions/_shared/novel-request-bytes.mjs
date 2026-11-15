/**
 * Lecture binaire strictement bornée pour les requêtes de la liseuse SINJIRA.
 *
 * Le délai couvre toute la lecture, même lorsqu'un client laisse une connexion
 * ouverte ou que son producteur refuse de terminer cancel(). Les octets
 * incomplets ne sont JAMAIS retournés en cas d'annulation.
 */
export async function collectNovelBodyBytes(req, maxBytes, timeoutMs = 8_000) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1 ||
      !Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30_000) {
    throw new TypeError('Invalid novel request limits');
  }
  if (!req.body) return new Uint8Array(0);
  const reader = req.body.getReader();
  const chunks = [];
  let total = 0;
  let interrupted = false;
  const interrupt = () => {
    interrupted = true;
    try { void reader.cancel().catch(() => {}); } catch { /* stream already closed */ }
  };
  const deadline = setTimeout(interrupt, timeoutMs);
  req.signal.addEventListener('abort', interrupt, {once:true});
  try {
    if (req.signal.aborted) throw new Error('REQUEST_INTERRUPTED');
    while (true) {
      const {done, value} = await reader.read();
      if (interrupted || req.signal.aborted) throw new Error('REQUEST_INTERRUPTED');
      if (done) break;
      if (!(value instanceof Uint8Array) || value.byteLength > maxBytes - total) {
        interrupt();
        throw new Error('REQUEST_TOO_LARGE');
      }
      total += value.byteLength;
      chunks.push(value);
    }
    if (interrupted || req.signal.aborted) throw new Error('REQUEST_INTERRUPTED');
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    if (interrupted || req.signal.aborted) throw new Error('REQUEST_INTERRUPTED');
    return bytes;
  } catch (error) {
    // Préserver le code 413 sur dépassement; les autres rejets après abandon
    // restent un délai/interruption 408, sans corps partiel ni détails de flux.
    if (error instanceof Error && error.message === 'REQUEST_TOO_LARGE') throw error;
    if (interrupted || req.signal.aborted) throw new Error('REQUEST_INTERRUPTED');
    throw error;
  } finally {
    clearTimeout(deadline);
    req.signal.removeEventListener('abort', interrupt);
    reader.releaseLock();
  }
}
