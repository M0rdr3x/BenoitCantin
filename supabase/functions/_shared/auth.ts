import { createClient } from 'npm:@supabase/supabase-js@2';

function serverSecretKey() {
  const modern = Deno.env.get('SUPABASE_SECRET_KEYS');
  if (modern) {
    try {
      const keys = JSON.parse(modern);
      const preferred = keys?.default;
      if (typeof preferred === 'string' && preferred.length > 20) return preferred;
      const fallback = Object.values(keys || {}).find(
        (value) => typeof value === 'string' && value.length > 20
      );
      if (typeof fallback === 'string') return fallback;
    } catch (error) {
      console.warn('[SINJIRA auth] SUPABASE_SECRET_KEYS illisible, repli sur la clé legacy.', error);
    }
  }
  return Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
}

export function serviceClient() {
  const url = Deno.env.get('SUPABASE_URL');
  const key = serverSecretKey();
  if (!url || !key) throw new Error('Configuration Supabase serveur manquante.');
  return createClient(url, key, {
    auth: { persistSession: false, autoRefreshToken: false }
  });
}

export function bearerToken(req: Request) {
  const header = req.headers.get('Authorization') || '';
  return header.startsWith('Bearer ') ? header.slice(7).trim() : '';
}

export async function optionalUser(req: Request) {
  const token = bearerToken(req);
  if (!token) return null;
  const client = serviceClient();
  const { data, error } = await client.auth.getUser(token);
  if (error || !data.user) return null;
  return data.user;
}

export async function requiredUser(req: Request) {
  const user = await optionalUser(req);
  if (!user) throw new Error('AUTH_REQUIRED');
  return user;
}

/**
 * Contexte administrateur V24.4.67.
 *
 * Politique MFA progressive :
 * - aucun facteur MFA vérifié -> la session aal1 reste permise;
 * - un facteur vérifié existe et la session peut monter à aal2 -> aal2 devient obligatoire;
 * - état MFA impossible à vérifier -> refus fermé pour une opération administrative.
 */
export async function requiredAdmin(req: Request) {
  const token = bearerToken(req);
  if (!token) throw new Error('AUTH_REQUIRED');

  const service = serviceClient();
  const { data: authData, error: authError } = await service.auth.getUser(token);
  const user = authData?.user;
  if (authError || !user) throw new Error('AUTH_REQUIRED');

  const { data: isAdmin, error: adminError } = await service.rpc('is_sinjira_admin', {
    p_user_id: user.id
  });
  if (adminError || !isAdmin) throw new Error('ADMIN_REQUIRED');

  const { data: aal, error: aalError } = await service.auth.mfa.getAuthenticatorAssuranceLevel(token);
  if (aalError || !aal) {
    console.error('[SINJIRA admin auth] état MFA indisponible', aalError);
    throw new Error('MFA_STATE_UNAVAILABLE');
  }
  if (aal.nextLevel === 'aal2' && aal.currentLevel !== 'aal2') {
    throw new Error('MFA_REQUIRED');
  }

  return { user, service, token, aal };
}
