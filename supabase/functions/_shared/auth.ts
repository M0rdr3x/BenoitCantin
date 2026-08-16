import { createClient } from 'npm:@supabase/supabase-js@2.112.3';

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

export async function optionalUser(req: Request) {
  const header = req.headers.get('Authorization') || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : '';
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
