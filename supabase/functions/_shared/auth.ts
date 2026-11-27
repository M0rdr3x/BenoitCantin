import { createClient } from 'npm:@supabase/supabase-js@2.119.2';

const ACTIVE_ADMIN_FUNCTIONS = new Set([
  'admin-analytics',
  'admin-console',
  'admin-license-codes',
  'admin-reports',
  'admin-sinjira-v18',
  'admin-social-v20',
  'admin-users'
]);

const EXTREMELY_SENSITIVE_FUNCTIONS = new Set([
  'submit-character-questionnaire'
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
      console.warn('[SINJIRA auth]', { code: 'SERVER_KEYS_PARSE_FAILED' });
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
  // Un JWT utilisateur compact possède exactement trois segments base64url.
  // Refuser les en-têtes combinés, les identifiants opaques et les entrées
  // excessives avant tout appel Auth; la vérification cryptographique reste
  // exclusivement confiée à auth.getUser(token).
  if (header.length > 16384) return '';
  const match = /^Bearer +([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/i.exec(header);
  return match && match[0] === header ? match[1] : '';
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
  // Une erreur de configuration ou de transport ne doit pas divulguer
  // les détails du fournisseur ni permettre de poursuivre sans identité.
  try {
    const service = serviceClient();
    const { data, error } = await service.auth.getUser(token);
    // Le contrat SDK de succès exige error === null; un champ omis ou falsy
    // inattendu ne constitue pas une preuve d'identité.
    if (error !== null || !data?.user || typeof data.user.id !== 'string' ||
        !data.user.id.trim() || data.user.id !== data.user.id.trim()) throw new Error('AUTH_REQUIRED');
    return { user: data.user, service, token };
  } catch {
    throw new Error('AUTH_REQUIRED');
  }
}

async function assuranceLevel(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  const { service, token } = context;
  // Une exception réseau/SDK est traitée comme un état MFA indisponible.
  // Ne jamais propager un message fournisseur ni accepter une réponse ambiguë.
  try {
    const { data: aal, error: aalError } = await service.auth.mfa.getAuthenticatorAssuranceLevel(token);
    if (aalError !== null || !aal || typeof aal !== 'object' || Array.isArray(aal) || !['aal1', 'aal2'].includes(aal.currentLevel ?? '') ||
        !['aal1', 'aal2'].includes(aal.nextLevel ?? '')) throw new Error('MFA_STATE_UNAVAILABLE');
    return aal;
  } catch {
    throw new Error('MFA_STATE_UNAVAILABLE');
  }
}

async function assertAdminMfa(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  const { user, service } = context;
  try {
    const { data: isAdmin, error: adminError } = await service.rpc('is_sinjira_admin', {
      p_user_id: user.id
    });
    if (adminError !== null || isAdmin !== true) throw new Error('ADMIN_REQUIRED');
  } catch {
    throw new Error('ADMIN_REQUIRED');
  }

  const aal = await assuranceLevel(context).catch((error) => {
    console.error('[SINJIRA admin auth]', { code: 'MFA_STATE_UNAVAILABLE' });
    throw error;
  });
  // Les accès administrateur ne doivent jamais retomber en AAL1,
  // y compris quand aucun facteur n'est encore enregistré.
  if (aal.nextLevel !== 'aal2') throw new Error('MFA_SETUP_REQUIRED');
  if (aal.currentLevel !== 'aal2') throw new Error('MFA_REQUIRED');
  return aal;
}

async function sensitiveStepUpEnabled(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  const { user, service } = context;
  try {
    const { data, error } = await service
      .from('security_user_settings')
      .select('user_id,sensitive_step_up')
      .eq('user_id', user.id)
      .maybeSingle();
    // Une absence de ligne conserve la protection par défaut. Seule une
    // préférence booléenne explicite appartenant au compte authentifié
    // peut désactiver le step-up sur les opérations où il est facultatif.
    if (error !== null || (data !== null && (
      typeof data !== 'object' || Array.isArray(data) ||
      data.user_id !== user.id || typeof data.sensitive_step_up !== 'boolean'
    ))) {
      throw new Error('SECURITY_STATE_UNAVAILABLE');
    }
    return data === null || data.sensitive_step_up;
  } catch {
    console.error('[SINJIRA sensitive auth]', { code: 'SECURITY_STATE_UNAVAILABLE' });
    throw new Error('SECURITY_STATE_UNAVAILABLE');
  }
}

async function assertSensitiveMfa(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  if (!(await sensitiveStepUpEnabled(context))) return null;

  const aal = await assuranceLevel(context).catch((error) => {
    console.error('[SINJIRA sensitive auth]', { code: 'MFA_STATE_UNAVAILABLE' });
    throw error;
  });
  if (aal.nextLevel !== 'aal2') throw new Error('MFA_SETUP_REQUIRED');
  if (aal.currentLevel !== 'aal2') throw new Error('MFA_REQUIRED');
  return aal;
}

async function assertVaultMfa(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  // Le Registre personnel ne consulte volontairement PAS sensitive_step_up :
  // sa vérification AAL2 est obligatoire et ne peut pas être désactivée par préférence.
  const aal = await assuranceLevel(context).catch(() => {
    throw new Error('MFA_STATE_UNAVAILABLE');
  });
  if (aal.nextLevel !== 'aal2') throw new Error('MFA_SETUP_REQUIRED');
  if (aal.currentLevel !== 'aal2') throw new Error('MFA_REQUIRED');
  return aal;
}

async function assertPersonalAiMfa(context: Awaited<ReturnType<typeof authenticatedContext>>) {
  // Mon IA privée appartient au périmètre ai_private du moteur V25 : AAL2 reste
  // obligatoire, indépendamment de la préférence sensitive_step_up.
  const aal = await assuranceLevel(context).catch(() => {
    throw new Error('MFA_STATE_UNAVAILABLE');
  });
  if (aal.nextLevel !== 'aal2') throw new Error('MFA_SETUP_REQUIRED');
  if (aal.currentLevel !== 'aal2') throw new Error('MFA_REQUIRED');
  return aal;
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
  const functionName = edgeFunctionName(req);
  if (ACTIVE_ADMIN_FUNCTIONS.has(functionName)) {
    await assertAdminMfa(context);
  }
  if (EXTREMELY_SENSITIVE_FUNCTIONS.has(functionName)) {
    await assertSensitiveMfa(context);
  }
  return context.user;
}

/**
 * Contexte du Registre personnel des consciences.
 * AAL2 est toujours obligatoire et ne dépend d'aucune préférence utilisateur.
 * Le contexte retourne le service serveur afin que l'Edge Function puisse appeler
 * uniquement les RPC étroites du coffre après l'évaluation de risque V25.
 */
export async function requiredVaultUser(req: Request) {
  const context = await authenticatedContext(req);
  const aal = await assertVaultMfa(context);
  return { ...context, aal };
}

/**
 * Contexte Mon IA V25. AAL2 est obligatoire et le service serveur n'est rendu
 * disponible qu'après vérification du JWT réel et de l'assurance MFA.
 */
export async function requiredPersonalAiUser(req: Request) {
  const context = await authenticatedContext(req);
  const aal = await assertPersonalAiMfa(context);
  return { ...context, aal };
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
  await assertSensitiveMfa(context);
  return context.user;
}

/**
 * Contexte administrateur V24.4.67.
 *
 * MFA administrateur obligatoire, sans exception AAL1 :
 * - sans facteur TOTP vérifié -> MFA_SETUP_REQUIRED (configurer Ma sécurité) ;
 * - facteur vérifié mais session non revalidée -> MFA_REQUIRED ;
 * - état MFA indisponible -> refus fermé pour toute opération administrative.
 * L'inscription TOTP reste accessible depuis /compte/securite.html, hors endpoints admin.
 */
export async function requiredAdmin(req: Request) {
  const context = await authenticatedContext(req);
  const aal = await assertAdminMfa(context);
  return { ...context, aal };
}
