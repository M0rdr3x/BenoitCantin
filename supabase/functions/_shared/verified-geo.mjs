/**
 * Authenticate country/region supplied by a dedicated SINJIRA ingress proxy.
 *
 * HTTP headers are attacker-controlled at the public Supabase Edge endpoint.
 * "SINJIRA_TRUST_GEO_HEADERS=true" alone is NOT a trust boundary. Require an
 * HMAC-SHA256 proof created by an ingress that overwrites client geo headers.
 *
 * Signature input (UTF-8):
 *   sinjira-geo/v1\n<verified JWT session UUID>\n<Unix milliseconds>\n<ISO country>\n<region>
 *
 * On any missing/malformed/stale/unauthenticated proof, return no location.
 * Never use IP addresses or emit signing material to logs / responses.
 */
const EMPTY_GEO = Object.freeze({ country: null, region: null });
const MAX_PROOF_AGE_MS = 60_000;
const SIGNATURE_RE = /^v1=([0-9a-f]{64})$/;
const SESSION_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const COUNTRY_RE = /^[A-Z]{2}$/;
// Whitelist letters and ordinary geographic punctuation; refuse controls,
// raw headers, markup and silently truncated / ambiguous region values.
const REGION_RE = /^[\p{L}\p{M}\p{N} ._'-]{0,80}$/u;

export async function verifiedCoarseGeo(req, sessionId, options = {}) {
  if (options.enabled !== true) return EMPTY_GEO;

  try {
    const encoder = new TextEncoder();
    const secret = typeof options.secret === 'string' ? options.secret : '';
    const keyBytes = encoder.encode(secret);
    if (keyBytes.length < 32 || keyBytes.length > 1024) return EMPTY_GEO;
    if (typeof sessionId !== 'string' || !SESSION_RE.test(sessionId)) return EMPTY_GEO;

    const country = req.headers.get('cf-ipcountry') || '';
    const region = req.headers.get('x-sinjira-region') || '';
    const stamp = req.headers.get('x-sinjira-geo-timestamp') || '';
    const supplied = req.headers.get('x-sinjira-geo-proof') || '';

    const signature = SIGNATURE_RE.exec(supplied);
    if (!signature || !COUNTRY_RE.test(country) ||
        !REGION_RE.test(region) || !/^[1-9][0-9]{12}$/.test(stamp)) {
      return EMPTY_GEO;
    }

    const timestamp = Number(stamp);
    const now = options.now === undefined ? Date.now() : options.now;
    if (!Number.isSafeInteger(timestamp) || !Number.isSafeInteger(now) ||
        Math.abs(now - timestamp) > MAX_PROOF_AGE_MS) {
      return EMPTY_GEO;
    }

    const payload = ['sinjira-geo/v1', sessionId.toLowerCase(), stamp, country, region].join('\n');
    const bytes = signature[1].match(/.{2}/g).map(part => Number.parseInt(part, 16));
    const key = await crypto.subtle.importKey(
      'raw', keyBytes, { name: 'HMAC', hash: 'SHA-256' }, false, ['verify']
    );
    const valid = await crypto.subtle.verify(
      'HMAC', key, new Uint8Array(bytes), encoder.encode(payload)
    );
    return valid ? { country, region: region || null } : EMPTY_GEO;
  } catch {
    // Geo is optional; a failed HMAC/provider must not supply a fictitious
    // trusted location or prevent the ordinary device risk evaluation.
    return EMPTY_GEO;
  }
}
