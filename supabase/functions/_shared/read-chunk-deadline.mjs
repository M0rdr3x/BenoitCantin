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
