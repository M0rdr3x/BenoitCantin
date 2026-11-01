/**
 * Read a public Edge request incrementally. Never call Request.text()/json()
 * before enforcing a byte ceiling: Content-Length is optional and untrusted.
 *
 * Fail closed for malformed length, malformed UTF-8, aborted streams and
 * streaming bodies that exceed the byte limit. Do not echo request data.
 */
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

  if (!req.body) return { ok: true, raw: '' };
  const reader = req.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let byteCount = 0;
  let text = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      byteCount += value.byteLength;
      if (byteCount > maxBytes) {
        await reader.cancel().catch(() => {});
        return { ok: false };
      }
      text += decoder.decode(value, { stream: true });
    }
    text += decoder.decode();
    return { ok: true, raw: text };
  } catch {
    await reader.cancel().catch(() => {});
    return { ok: false };
  } finally {
    reader.releaseLock();
  }
}
