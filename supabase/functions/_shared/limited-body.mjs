/**
 * Read a public Edge request incrementally. Never call Request.text()/json()
 * before enforcing a byte ceiling: Content-Length is optional and untrusted.
 *
 * Fail closed for malformed length, malformed UTF-8, aborted streams and
 * streaming bodies that exceed the byte limit. Do not echo request data.
 */
export async function readLimitedUtf8Body(req, maxBytes, timeoutMs = 20_000) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 0) {
    throw new TypeError('Invalid request body limit');
  }
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 120_000) {
    throw new TypeError('Invalid request body timeout');
  }

  const declared = req.headers.get('content-length');
  if (declared !== null) {
    if (!/^(0|[1-9][0-9]*)$/.test(declared) ||
        !Number.isSafeInteger(Number(declared)) ||
        Number(declared) > maxBytes) {
      return { ok: false };
    }
  }

  if (!req.body) return { ok: true, raw: '' };
  const reader = req.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let byteCount = 0;
  let text = '';
  let interrupted = false;
  // Une connexion lente ou abandonnée ne peut pas monopoliser une invocation.
  // Ne jamais attendre cancel(): un producteur malveillant pourrait lui-même
  // bloquer la promesse d'annulation. La lecture en attente est débloquée
  // dès l'appel de cancel() selon le contrat WHATWG Streams.
  const interrupt = () => {
    interrupted = true;
    try { void reader.cancel().catch(() => {}); } catch { /* lecteur clos */ }
  };
  const timeout = setTimeout(interrupt, timeoutMs);
  req.signal.addEventListener('abort', interrupt, { once: true });
  try {
    if (req.signal.aborted) {
      interrupt();
      return { ok: false };
    }
    while (true) {
      const { done, value } = await reader.read();
      if (interrupted || req.signal.aborted) return { ok: false };
      if (done) break;
      if (!(value instanceof Uint8Array) || value.byteLength > maxBytes - byteCount) {
        interrupt();
        return { ok: false };
      }
      byteCount += value.byteLength;
      text += decoder.decode(value, { stream: true });
    }
    if (interrupted || req.signal.aborted) return { ok: false };
    text += decoder.decode();
    return { ok: true, raw: text };
  } catch {
    interrupt();
    return { ok: false };
  } finally {
    clearTimeout(timeout);
    req.signal.removeEventListener('abort', interrupt);
    reader.releaseLock();
  }
}

/**
 * Read a remote binary response with a strict byte ceiling *while streaming*.
 * The Content-Length header is optional and can lie, so the actual limit is
 * enforced against the stream before any whole-body allocation. Used for the
 * Fracture PDF template fetched by the public report-generating Edge Function.
 *
 * Return no bytes on malformed, empty, interrupted or oversized responses.
 * Never reflect remote content into logs or HTTP error messages.
 */
export async function readLimitedBinaryResponse(response, maxBytes, timeoutMs = 30_000) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1) {
    throw new TypeError('Invalid binary response limit');
  }
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 120_000) {
    throw new TypeError('Invalid binary response timeout');
  }

  const declared = response.headers.get('content-length');
  if (declared !== null) {
    if (!/^(0|[1-9][0-9]*)$/.test(declared) ||
        !Number.isSafeInteger(Number(declared)) ||
        Number(declared) > maxBytes) {
      return { ok: false };
    }
  }

  if (!response.body) return { ok: false };
  const reader = response.body.getReader();
  const chunks = [];
  let byteCount = 0;
  let interrupted = false;
  const interrupt = () => {
    interrupted = true;
    try { void reader.cancel().catch(() => {}); } catch { /* lecteur clos */ }
  };
  const timeout = setTimeout(interrupt, timeoutMs);
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (interrupted) return { ok: false };
      if (done) break;
      if (!(value instanceof Uint8Array) ||
          value.byteLength > maxBytes - byteCount) {
        interrupt();
        return { ok: false };
      }
      byteCount += value.byteLength;
      chunks.push(value);
    }

    if (interrupted || byteCount === 0) return { ok: false };
    const bytes = new Uint8Array(byteCount);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    if (interrupted) return { ok: false };
    return { ok: true, bytes };
  } catch {
    interrupt();
    return { ok: false };
  } finally {
    clearTimeout(timeout);
    reader.releaseLock();
  }
}
