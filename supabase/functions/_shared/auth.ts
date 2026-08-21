import { createClient } from 'npm:@supabase/supabase-js@2';

const ACTIVE_ADMIN_FUNCTIONS = new Set([
  'admin-analytics',
  'admin-console',
  'admin-license-codes',
  'admin-reports',
  'admin-sinjira-v18',
  'admin-social-v20',
  'admin-users'
]);

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

function edgeFunctionName(req: Request) {
  try {
    const parts = new URL(req.url).pathname.split('/').filter(Boolean);
    const v1 = parts.indexOf('v1');
    if (v1 >= 0 && parts[v1 + 1]) return parts[v1 + 1];
    return parts.length ? parts[parts.length - 1] : '';
  } catch {
    return '';
  }
}

async function authenticatedContext(req: Request) {
  const token = bearerToken(req);
  if (!token) throw new Error('AUTH_REQUIRED');
  const service = serviceClient();
  const { data, error } = await service.auth.getUser(token);
  if (error || !data.user) throw new Error('AUTH_REQUIRED');
  return { user: data.user, service, token };
}

async function assuranceLevel(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  const { service, token } = context;
  const { data: aal, error: aalError } = await service.auth.mfa.getAuthenticatorAssuranceLevel(token);
  if (aalError || !aal) throw new Error('MFA_STATE_UNAVAILABLE');
  return aal;
}

async function assertAdminMfa(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  const { user, service } = context;
  const { data: isAdmin, error: adminError } = await service.rpc('is_sinjira_admin', {
    p_user_id: user.id
  });
  if (adminError || !isAdmin) throw new Error('ADMIN_REQUIRED');

  const aal = await assuranceLevel(context).catch((error) => {
    console.error('[SINJIRA admin auth] état MFA indisponible', error);
    throw error;
  });
  if (aal.nextLevel === 'aal2' && aal.currentLevel !== 'aal2') {
    throw new Error('MFA_REQUIRED');
  }
  return aal;
}

async function sensitiveStepUpEnabled(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  const { user, service } = context;
  const { data, error } = await service
    .from('security_user_settings')
    .select('sensitive_step_up')
    .eq('user_id', user.id)
    .maybeSingle();
  if (error) {
    console.error('[SINJIRA sensitive auth] préférences de sécurité indisponibles', error);
    throw new Error('SECURITY_STATE_UNAVAILABLE');
  }
  // Le défaut canonique est protecteur : si aucune ligne n'existe encore,
  // les zones extrêmement sensibles demandent le step-up.
  return data?.sensitive_step_up !== false;
}

export async function optionalUser(req: Request) {
  try {
    return (await authenticatedContext(req)).user;
  } catch {
    return null;
  }
}

export async function requiredUser(req: Request) {
  const context = await authenticatedContext(req);
  if (ACTIVE_ADMIN_FUNCTIONS.has(edgeFunctionName(req))) {
    await assertAdminMfa(context);
  }
  return context.user;
}

/**
 * Contexte pour une zone extrêmement sensible (Registre, récupération, etc.).
 * Si la protection renforcée est activée :
 * - aucun facteur vérifié -> la personne doit configurer un second facteur;
 * - facteur vérifié mais session aal1 -> une vérification aal2 est requise;
 * - état MFA impossible à vérifier -> refus fermé.
 *
 * L'utilisateur conserve une sortie : la préférence sensitive_step_up peut être
 * désactivée explicitement depuis Ma sécurité. SINJIRA ne rend donc pas le compte
 * irrécupérable pour une personne qui n'a pas encore de facteur MFA.
 */
export async function requiredSensitiveUser(req: Request) {
  const context = await authenticatedContext(req);
  if (!(await sensitiveStepUpEnabled(context))) return context.user;

  const aal = await assuranceLevel(context).catch((error) => {
    console.error('[SINJIRA sensitive auth] état MFA indisponible', error);
    throw error;
  });
  if (aal.nextLevel !== 'aal2') throw new Error('MFA_SETUP_REQUIRED');
  if (aal.currentLevel !== 'aal2') throw new Error('MFA_REQUIRED');
  return context.user;
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
  const context = await authenticatedContext(req);
  const aal = await assertAdminMfa(context);
  return { ...context, aal };
}
