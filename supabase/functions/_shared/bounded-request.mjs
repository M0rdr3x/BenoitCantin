/* Lecture HTTP bornée AVANT allocation/décodage d'un corps JSON administrateur.
 * Compatible Supabase Edge Runtime (Deno) et Node (tests sans réseau).
 */
export async function readBoundedRequestText(req, maxBytes, timeoutMs = 15000) {
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000) {
    throw new Error('REQUEST_TIMEOUT');
  }
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1 || maxBytes > 2 * 1024 * 1024) {
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
  // Limiter aussi le nombre de fragments : 1 octet par trame ne doit pas
  // provoquer des millions de références et d'itérations pour un corps de 2 Mio.
  const MAX_CHUNKS = 4096;
  const parts = [];
  let total = 0;
  let count = 0;
  // Un délai absolu, et non réinitialisé pour chaque fragment : l'envoi au
  // compte-gouttes ne peut pas garder une fonction ouverte indéfiniment.
  let deadlineTimer;
  const deadline = new Promise((_, reject) => {
    deadlineTimer = setTimeout(() => reject(new Error('REQUEST_TIMEOUT')), timeoutMs);
  });
  try {
    for (;;) {
      const {done, value} = await Promise.race([reader.read(), deadline]);
      if (done) break;
      if (++count > MAX_CHUNKS) throw new Error('REQUEST_TOO_LARGE');
      if (!(value instanceof Uint8Array)) throw new Error('INVALID_JSON');
      total += value.byteLength;
      if (total > maxBytes) throw new Error('REQUEST_TOO_LARGE');
      parts.push(value);
    }
  } catch (error) {
    // Ne pas attendre un cancel() lui-même bloqué par la connexion hostile.
    // Le flux est annulé, et l'exception conserve sa nature pour la réponse.
    try { Promise.resolve(reader.cancel()).catch(() => {}); } catch {}
    throw error;
  } finally {
    clearTimeout(deadlineTimer);
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
