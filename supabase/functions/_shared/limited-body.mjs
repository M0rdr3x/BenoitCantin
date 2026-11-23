import { readChunkWithDeadline } from './read-chunk-deadline.mjs';

// Délai ABSOLU de l'ensemble de la lecture, pas 8 secondes par fragment.
// Même un client qui envoie des octets très lentement doit finir ou être refusé.
const UTF8_BODY_DEADLINE_MS = 8000;

/**
 * Read a public Edge request incrementally. Never call Request.text()/json()
 * before enforcing a byte ceiling: Content-Length is optional and untrusted.
 *
 * Fail closed for malformed length, malformed UTF-8, aborted streams and
 * streaming bodies that exceed the byte limit. Do not echo request data.
 */
// Ne pas attendre l'annulation : un producteur distant peut laisser la Promise
// de cancel() indéfiniment en attente, même quand la limite est déjà dépassée.
// La fermeture est consultative ; le refus HTTP doit toujours pouvoir terminer.
function cancelReaderWithoutWaiting(reader) {
  try {
    void Promise.resolve(reader.cancel()).catch(() => {});
  } catch {
    // Même une erreur synchrone du producteur ne doit pas empêcher le refus.
  }
}

export async function readLimitedUtf8Body(req, maxBytes) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 0) {
    throw new TypeError('Invalid request body limit');
  }

  const declared = req.headers.get('content-length');
  if (declared !== null) {
    if (!/^(0|[1-9][0-9]*)$/.test(declared) ||
        !Number.isSafeInteger(Number(declared)) ||
        Number(declared) > maxBytes) {
      return { ok: false };
    }
  }

  if (req.signal?.aborted) return { ok: false };
  if (!req.body) return { ok: true, raw: '' };
  const reader = req.body.getReader();
  const deadlineAt = performance.now() + UTF8_BODY_DEADLINE_MS;
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let byteCount = 0;
  let text = '';
  try {
    while (true) {
      const { done, value } = await readChunkWithDeadline(reader, req.signal, deadlineAt);
      if (done) break;
      if (!(value instanceof Uint8Array)) {
        // Chemin unique de refus et d'annulation dans catch : pas de second cancel().
        throw new TypeError('INVALID_STREAM_CHUNK');
      }
      byteCount += value.byteLength;
      if (byteCount > maxBytes) {
        cancelReaderWithoutWaiting(reader);
        return { ok: false };
      }
      text += decoder.decode(value, { stream: true });
    }
    text += decoder.decode();
    return { ok: true, raw: text };
  } catch {
    cancelReaderWithoutWaiting(reader);
    return { ok: false };
  } finally {
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
export async function readLimitedBinaryResponse(response, maxBytes) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1) {
    throw new TypeError('Invalid binary response limit');
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
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!(value instanceof Uint8Array) ||
          value.byteLength > maxBytes - byteCount) {
        cancelReaderWithoutWaiting(reader);
        return { ok: false };
      }
      byteCount += value.byteLength;
      chunks.push(value);
    }

    if (byteCount === 0) return { ok: false };
    const bytes = new Uint8Array(byteCount);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return { ok: true, bytes };
  } catch {
    cancelReaderWithoutWaiting(reader);
    return { ok: false };
  } finally {
    reader.releaseLock();
  }
}
