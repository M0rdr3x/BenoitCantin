// Projet Nova: lecture JSON en flux borné, commune aux sondages 40 et 64.
export const MAX_REQUEST_BYTES = 8192;

export async function readBoundedJson(req) {
  if (!req.body) throw new Error('INVALID_JSON');
  const reader = req.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let complete = false;
  let total = 0;
  let raw = '';
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) { complete = true; break; }
      total += value.byteLength;
      if (total > MAX_REQUEST_BYTES) throw new Error('REQUEST_TOO_LARGE');
      raw += decoder.decode(value, { stream: true });
    }
    raw += decoder.decode();
    return JSON.parse(raw);
  } catch (error) {
    if (error instanceof Error && error.message === 'REQUEST_TOO_LARGE') throw error;
    throw new Error('INVALID_JSON');
  } finally {
    if (!complete) {
      try { await reader.cancel(); } catch { /* flux déjà interrompu */ }
    }
    reader.releaseLock();
  }
}
