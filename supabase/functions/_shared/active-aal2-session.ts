import { createClient } from 'npm:@supabase/supabase-js@2.119.2';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Le jeton est déjà vérifié par le garde Auth de l'Edge (Auth et AAL2).
// Aucune revendication provenant du corps de requête n'est utilisée.
function verifiedSessionId(token: string, userId: string) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) throw new Error();
    const raw = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const bytes = Uint8Array.from(atob(raw.padEnd(Math.ceil(raw.length / 4) * 4, '=')), c => c.charCodeAt(0));
    const claims = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
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
    const keys = Deno.env.get('SUPABASE_PUBLISHABLE_KEYS');
    const publishable = keys ? JSON.parse(keys)?.default : null;
    const key = typeof publishable === 'string' && publishable.startsWith('sb_publishable_')
      ? publishable : Deno.env.get('SUPABASE_ANON_KEY');
    if (!url || !key) throw new Error();
    // Client limité à l'identité du demandeur; jamais la clé service_role.
    const client = createClient(url, key, {
      auth: { persistSession: false, autoRefreshToken: false },
      global: { headers: { Authorization: `Bearer ${token}` } },
    });
    result = await client.rpc('security_list_sessions');
  } catch {
    throw new Error('SECURITY_DECISION_INVALID');
  }
  if (result.error !== null || !Array.isArray(result.data)) {
    throw new Error('SECURITY_DECISION_INVALID');
  }
  // La RPC filtre par auth.uid() et par expiration sur auth.sessions.
  // Le JWT peut survivre à une déconnexion: exiger une ligne active unique.
  const current = result.data.filter(row => row?.is_current === true);
  if (current.length !== 1 || current[0].id !== sessionId) throw new Error('AUTH_REQUIRED');
}
