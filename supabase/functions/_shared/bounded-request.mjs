/* Lecture HTTP bornée AVANT allocation/décodage d'un corps JSON administrateur.
 * Compatible Supabase Edge Runtime (Deno) et Node (tests sans réseau).
 */
export async function readBoundedRequestText(req, maxBytes) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1 || maxBytes > 1024 * 1024) {
    throw new Error('REQUEST_TOO_LARGE');
  }
  const declared = req.headers.get('content-length');
  if (declared !== null &&
      (!/^[0-9]+$/.test(declared) || !Number.isSafeInteger(Number(declared)) ||
       Number(declared) > maxBytes)) {
    throw new Error('REQUEST_TOO_LARGE');
  }
  if (!req.body) return '';
  if (typeof req.body.getReader !== 'function') throw new Error('INVALID_JSON');
  const reader = req.body.getReader();
  const parts = [];
  let total = 0;
  try {
    for (;;) {
      const {done, value} = await reader.read();
      if (done) break;
      if (!(value instanceof Uint8Array)) throw new Error('INVALID_JSON');
      total += value.byteLength;
      if (total > maxBytes) throw new Error('REQUEST_TOO_LARGE');
      parts.push(value);
    }
  } catch (error) {
    await reader.cancel().catch(() => {});
    throw error;
  } finally {
    reader.releaseLock();
  }
  const output = new Uint8Array(total);
  let offset = 0;
  for (const part of parts) {
    output.set(part, offset);
    offset += part.byteLength;
  }
  try {
    return new TextDecoder('utf-8', {fatal: true}).decode(output);
  } catch {
    throw new Error('INVALID_JSON');
  }
}
