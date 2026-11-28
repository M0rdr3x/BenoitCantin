import { createClient } from 'npm:@supabase/supabase-js@2.119.2';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Validate key class before handing configuration to the SDK. The legacy
// JWT payload is inspected only for its role; the API verifies the signature.
function decodeClaims(token: string) {
  const parts = token.split('.');
  if (parts.length !== 3 || token.length > 16384 ||
      parts.some(part => !part || /[^A-Za-z0-9_-]/.test(part))) throw new Error();
  const raw = parts[1].replace(/-/g, '+').replace(/_/g, '/');
  const bytes = Uint8Array.from(atob(raw.padEnd(Math.ceil(raw.length / 4) * 4, '=')), c => c.charCodeAt(0));
  const claims = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  if (!claims || typeof claims !== 'object' || Array.isArray(claims)) throw new Error();
  return claims;
}

function userContextKey() {
  const raw = Deno.env.get('SUPABASE_PUBLISHABLE_KEYS');
  if (raw !== undefined) {
    const keys = JSON.parse(raw);
    if (!keys || typeof keys !== 'object' || Array.isArray(keys)) throw new Error();
    if (Object.prototype.hasOwnProperty.call(keys, 'default')) {
      const key = keys.default;
      if (typeof key !== 'string' || key.length > 512 ||
          !/^sb_publishable_[A-Za-z0-9_-]+$/.test(key) || key.trim() !== key) throw new Error();
      return key;
    }
  }
  const key = Deno.env.get('SUPABASE_ANON_KEY');
  if (!key || decodeClaims(key).role !== 'anon') throw new Error();
  return key;
}

// Le jeton est déjà vérifié par le garde Auth de l'Edge (Auth et AAL2).
// Aucune revendication provenant du corps de requête n'est utilisée.
function verifiedSessionId(token: string, userId: string) {
  try {
    const claims = decodeClaims(token);
    if (!claims || typeof claims !== 'object' || Array.isArray(claims) ||
        claims.sub !== userId || claims.aal !== 'aal2' ||
        typeof claims.session_id !== 'string' || claims.session_id.length !== 36 ||
        !UUID_RE.test(claims.session_id)) throw new Error();
    return claims.session_id;
  } catch {
    throw new Error('AUTH_REQUIRED');
  }
}

export async function requireActiveAal2Session(token: string, userId: string) {
  const sessionId = verifiedSessionId(token, userId);
  let result;
  try {
    const url = Deno.env.get('SUPABASE_URL');
    const key = userContextKey();
    if (!url) throw new Error();
    // Client limité à l'identité du demandeur; jamais la clé service_role.
    const client = createClient(url, key, {
      auth: { persistSession: false, autoRefreshToken: false },
      global: { headers: { Authorization: `Bearer ${token}` } },
    });
    result = await client.rpc('security_list_sessions');
  } catch {
    throw new Error('SECURITY_DECISION_INVALID');
  }
  if (!result || typeof result !== 'object' || Array.isArray(result) ||
      result.error !== null || !Array.isArray(result.data)) {
    throw new Error('SECURITY_DECISION_INVALID');
  }
  // Vérifier la totalité du contrat avant de reconnaître une session.
  // Une réponse ambiguë ne doit jamais autoriser une opération privilégiée.
  const seen = new Set<string>();
  for (const row of result.data) {
    if (!row || typeof row !== 'object' || Array.isArray(row) ||
        typeof row.id !== 'string' || row.id.length !== 36 || !UUID_RE.test(row.id) ||
        typeof row.is_current !== 'boolean' || seen.has(row.id) ||
        row.is_current !== (row.id === sessionId)) {
      throw new Error('SECURITY_DECISION_INVALID');
    }
    seen.add(row.id);
  }
  // La RPC filtre par auth.uid() et par expiration sur auth.sessions.
  // Le JWT peut survivre à une déconnexion: exiger une ligne active unique.
  const current = result.data.filter(row => row?.is_current === true);
  if (current.length !== 1 || current[0].id !== sessionId) throw new Error('AUTH_REQUIRED');
  // Ne pas se fier uniquement à l'AAL inscrit dans un ancien JWT.
  if (current[0].aal !== 'aal2') throw new Error('AUTH_REQUIRED');
  const expiry = current[0].not_after;
  if (expiry !== null) {
    if (typeof expiry !== 'string' || !Number.isFinite(Date.parse(expiry))) {
      throw new Error('SECURITY_DECISION_INVALID');
    }
    if (Date.parse(expiry) <= Date.now()) throw new Error('AUTH_REQUIRED');
  }
}
