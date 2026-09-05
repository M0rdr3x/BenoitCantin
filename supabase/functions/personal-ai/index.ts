import { corsHeaders } from '../_shared/cors.ts';
import { requiredPersonalAiUser } from '../_shared/auth.ts';

const MAX_REQUEST_BYTES = 16 * 1024;
const PRIVATE_HEADERS = {
  ...corsHeaders,
  'Content-Type': 'application/json; charset=utf-8',
  'Cache-Control': 'private, no-store, max-age=0',
  'Pragma': 'no-cache',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer'
};

function privateJson(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: PRIVATE_HEADERS });
}

async function readBoundedJson(req: Request) {
  const type = (req.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase();
  if (type !== 'application/json') throw new Error('JSON_REQUIRED');
  const declared = Number(req.headers.get('content-length') || 0);
  if (Number.isFinite(declared) && declared > MAX_REQUEST_BYTES) throw new Error('REQUEST_TOO_LARGE');
  if (!req.body) throw new Error('INVALID_JSON');
  const reader = req.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if (!value) continue;
      total += value.byteLength;
      if (total > MAX_REQUEST_BYTES) {
        await reader.cancel('REQUEST_TOO_LARGE').catch(() => undefined);
        throw new Error('REQUEST_TOO_LARGE');
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  try {
    const parsed = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error();
    return parsed as Record<string, unknown>;
  } catch {
    throw new Error('INVALID_JSON');
  }
}

function safeText(value: unknown, max: number) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}

function safeDeviceType(value: unknown) {
  const type = safeText(value, 20);
  return ['browser','ios','android','tablet','other'].includes(type) ? type : 'other';
}

function rejectClientIdentity(body: Record<string, unknown>) {
  for (const key of ['user_id','target_user_id','subject_user_id']) {
    if (Object.prototype.hasOwnProperty.call(body, key)) throw new Error('CLIENT_IDENTITY_FORBIDDEN');
  }
}

function trustedGeo(req: Request) {
  if (Deno.env.get('SINJIRA_TRUST_GEO_HEADERS') !== 'true') return { country: null, region: null };
  const raw = req.headers.get('cf-ipcountry') || '';
  const country = /^[A-Za-z]{2}$/.test(raw) ? raw.toUpperCase() : null;
  const regionRaw = req.headers.get('x-sinjira-region') || '';
  return { country, region: regionRaw ? regionRaw.slice(0, 80) : null };
}

function publicDecision(value: any) {
  return {
    outcome: String(value?.outcome || ''),
    risk_score: Number(value?.risk_score ?? -1),
    risk_band: String(value?.risk_band || ''),
    risk_model_version: String(value?.risk_model_version || ''),
    requires_step_up: value?.requires_step_up === true,
    mandatory_step_up: value?.mandatory_step_up === true,
    challenge_id: value?.challenge_id || null,
    display_code: value?.display_code || null,
    trusted_device_confirmation: String(value?.trusted_device_confirmation || '')
  };
}

function assertDecision(value: any) {
  const score = Number(value?.risk_score);
  const outcome = String(value?.outcome || '');
  if (
    value?.risk_model_version !== 'v25.0' ||
    value?.mandatory_step_up !== true ||
    value?.requires_step_up !== true ||
    !Number.isInteger(score) || score < 0 || score > 100 ||
    !['allow','approved','challenge','block'].includes(outcome)
  ) throw new Error('SECURITY_DECISION_INVALID');
  return { score, outcome };
}

function errorCode(error: unknown) {
  const code = error instanceof Error ? error.message : '';
  const known = new Set([
    'AUTH_REQUIRED','MFA_SETUP_REQUIRED','MFA_REQUIRED','MFA_STATE_UNAVAILABLE',
    'JSON_REQUIRED','REQUEST_TOO_LARGE','INVALID_JSON','CLIENT_IDENTITY_FORBIDDEN',
    'SECURITY_DECISION_INVALID','PERSONAL_AI_SOURCE_FORBIDDEN','PERSONAL_AI_LANGUAGE_INVALID'
  ]);
  return known.has(code) ? code : 'PERSONAL_AI_OPERATION_REFUSED';
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return privateJson({ ok: false, code: 'METHOD_NOT_ALLOWED', error: 'Méthode non autorisée.' }, 405);

  try {
    const { user, service } = await requiredPersonalAiUser(req);
    const body = await readBoundedJson(req);
    rejectClientIdentity(body);

    const deviceKey = safeText(body.device_key, 128);
    if (deviceKey.length < 16) return privateJson({ ok: false, code: 'DEVICE_KEY_INVALID', error: 'Identifiant d’appareil invalide.' }, 400);

    const geo = trustedGeo(req);
    const { data: security, error: securityError } = await service.rpc('service_personal_ai_evaluate_access', {
      p_user_id: user.id,
      p_device_key: deviceKey,
      p_display_name: safeText(body.display_name, 120) || 'Appareil SINJIRA',
      p_device_type: safeDeviceType(body.device_type),
      p_platform: safeText(body.platform, 120),
      p_country_code: geo.country,
      p_region_code: geo.region
    });
    if (securityError) throw new Error('SECURITY_DECISION_INVALID');

    const decision = assertDecision(security);
    const securityPublic = publicDecision(security);
    if (decision.outcome === 'challenge') {
      return privateJson({ ok: false, code: 'SECURITY_CHALLENGE_REQUIRED', error: 'Une confirmation de sécurité est requise.', security: securityPublic }, 403);
    }
    if (decision.outcome === 'block' || decision.score >= 75) {
      return privateJson({ ok: false, code: 'SECURITY_BLOCKED', error: 'Accès à Mon IA bloqué par la protection du compte.', security: securityPublic }, 403);
    }
    if (!['allow','approved'].includes(decision.outcome)) throw new Error('SECURITY_DECISION_INVALID');

    const risk = {
      p_aal: 'aal2',
      p_risk_score: decision.score,
      p_risk_outcome: decision.outcome,
      p_risk_model_version: 'v25.0'
    };
    const action = safeText(body.action, 40);

    if (action === 'get_state') {
      const { data, error } = await service.rpc('service_personal_ai_get_state', { p_user_id: user.id, ...risk });
      if (error) throw new Error('PERSONAL_AI_OPERATION_REFUSED');
      return privateJson({ ok: true, state: data, security: securityPublic });
    }

    if (action === 'update_settings') {
      const { data, error } = await service.rpc('service_personal_ai_update_settings', {
        p_user_id: user.id,
        p_enabled: body.enabled === true,
        p_display_name: safeText(body.ai_display_name, 80) || null,
        p_language_code: safeText(body.language_code, 16) || 'fr-CA',
        ...risk
      });
      if (error) throw new Error(error.message?.includes('LANGUAGE') ? 'PERSONAL_AI_LANGUAGE_INVALID' : 'PERSONAL_AI_OPERATION_REFUSED');
      return privateJson({ ok: true, settings: data, security: securityPublic });
    }

    if (action === 'set_source_permission') {
      const source = safeText(body.source_type, 40);
      if (!['life_story','employment'].includes(source)) throw new Error('PERSONAL_AI_SOURCE_FORBIDDEN');
      const { error } = await service.rpc('service_personal_ai_set_source_permission', {
        p_user_id: user.id,
        p_source_type: source,
        p_granted: body.granted === true,
        ...risk
      });
      if (error) throw new Error('PERSONAL_AI_OPERATION_REFUSED');
      return privateJson({ ok: true, source_type: source, granted: body.granted === true, runtime_access_enabled: false, security: securityPublic });
    }

    if (action === 'delete_personal_ai_data') {
      const { data, error } = await service.rpc('service_personal_ai_delete_data', { p_user_id: user.id, ...risk });
      if (error || data !== true) throw new Error('PERSONAL_AI_OPERATION_REFUSED');
      return privateJson({ ok: true, deleted: true, security: securityPublic });
    }

    // V25 n'offre volontairement aucun endpoint chat/memory/retrieve_source.
    return privateJson({ ok: false, code: 'UNKNOWN_ACTION', error: 'Action inconnue.' }, 400);
  } catch (error) {
    const code = errorCode(error);
    // Ne jamais journaliser le corps, un prompt, une réponse, un contenu source ou un objet SQL complet.
    console.warn('[personal-ai] opération refusée', code);
    if (code === 'AUTH_REQUIRED') return privateJson({ ok: false, code, error: 'Connexion requise.' }, 401);
    if (code === 'MFA_SETUP_REQUIRED') return privateJson({ ok: false, code, error: 'Configurez une authentification renforcée avant d’utiliser Mon IA.' }, 403);
    if (code === 'MFA_REQUIRED') return privateJson({ ok: false, code, error: 'Une vérification MFA récente est requise.' }, 403);
    if (code === 'MFA_STATE_UNAVAILABLE' || code === 'SECURITY_DECISION_INVALID') return privateJson({ ok: false, code, error: 'La protection de Mon IA est temporairement indisponible.' }, 503);
    if (code === 'JSON_REQUIRED') return privateJson({ ok: false, code, error: 'Corps JSON requis.' }, 415);
    if (code === 'REQUEST_TOO_LARGE') return privateJson({ ok: false, code, error: 'Requête trop volumineuse.' }, 413);
    if (code === 'INVALID_JSON' || code === 'CLIENT_IDENTITY_FORBIDDEN' || code === 'PERSONAL_AI_SOURCE_FORBIDDEN' || code === 'PERSONAL_AI_LANGUAGE_INVALID') return privateJson({ ok: false, code, error: 'Requête Mon IA invalide.' }, 400);
    return privateJson({ ok: false, code, error: 'Opération Mon IA refusée.' }, 403);
  }
});
