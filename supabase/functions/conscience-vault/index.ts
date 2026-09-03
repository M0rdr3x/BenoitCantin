import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredVaultUser } from '../_shared/auth.ts';

const MAX_CONTENT_BYTES = 1024 * 1024;
const MAX_REQUEST_BYTES = MAX_CONTENT_BYTES + 64 * 1024;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function safeText(value: unknown, max: number) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}

function safeDeviceType(value: unknown) {
  const type = safeText(value, 20);
  return ['browser', 'ios', 'android', 'tablet', 'other'].includes(type) ? type : 'other';
}

function validUuid(value: unknown) {
  return typeof value === 'string' && UUID_RE.test(value);
}

function byteLength(value: string) {
  return new TextEncoder().encode(value).byteLength;
}

function contentPayload(value: unknown) {
  if (typeof value !== 'string') throw new Error('VAULT_ENTRY_CONTENT_INVALID');
  const size = byteLength(value);
  if (size < 1 || size > MAX_CONTENT_BYTES) throw new Error('VAULT_ENTRY_CONTENT_INVALID');
  return value;
}

function entryType(value: unknown) {
  const type = safeText(value, 64) || 'reflection';
  if (!type) throw new Error('VAULT_ENTRY_TYPE_INVALID');
  return type;
}

/**
 * La localisation n'est jamais acceptée depuis le JSON client.
 * Elle reste désactivée par défaut et n'est utilisée que si un proxy contrôlé par
 * SINJIRA fournit des en-têtes approximatifs et que SINJIRA_TRUST_GEO_HEADERS=true.
 * Aucune IP brute ni donnée GPS n'est lue ou stockée par cette fonction.
 */
function trustedGeo(req: Request) {
  if (Deno.env.get('SINJIRA_TRUST_GEO_HEADERS') !== 'true') {
    return { country: null, region: null };
  }
  const countryRaw = req.headers.get('cf-ipcountry') || '';
  const country = /^[A-Za-z]{2}$/.test(countryRaw) ? countryRaw.toUpperCase() : null;
  const regionRaw = req.headers.get('x-sinjira-region') || '';
  const region = regionRaw ? regionRaw.slice(0, 80) : null;
  return { country, region };
}

function rejectClientIdentity(body: Record<string, unknown>) {
  for (const key of ['user_id', 'target_user_id', 'subject_user_id']) {
    if (Object.prototype.hasOwnProperty.call(body, key)) {
      throw new Error('CLIENT_IDENTITY_FORBIDDEN');
    }
  }
}

function publicSecurityDecision(security: any) {
  return {
    outcome: String(security?.outcome || ''),
    risk_score: Number(security?.risk_score ?? -1),
    risk_band: String(security?.risk_band || ''),
    risk_model_version: String(security?.risk_model_version || ''),
    requires_step_up: security?.requires_step_up === true,
    mandatory_step_up: security?.mandatory_step_up === true,
    challenge_id: security?.challenge_id || null,
    display_code: security?.display_code || null
  };
}

function assertVaultRiskDecision(security: any) {
  const score = Number(security?.risk_score);
  const outcome = String(security?.outcome || '');
  if (
    security?.risk_model_version !== 'v25.0' ||
    security?.mandatory_step_up !== true ||
    security?.requires_step_up !== true ||
    !Number.isInteger(score) ||
    score < 0 ||
    score > 100 ||
    !['allow', 'approved', 'challenge', 'block'].includes(outcome)
  ) {
    throw new Error('SECURITY_DECISION_INVALID');
  }
  return { score, outcome };
}

function errorCode(error: unknown) {
  const message = error instanceof Error ? error.message : '';
  const known = new Set([
    'AUTH_REQUIRED',
    'MFA_SETUP_REQUIRED',
    'MFA_REQUIRED',
    'MFA_STATE_UNAVAILABLE',
    'CLIENT_IDENTITY_FORBIDDEN',
    'VAULT_SESSION_REQUIRED',
    'VAULT_SESSION_INVALID',
    'VAULT_ENTRY_ID_INVALID',
    'VAULT_ENTRY_TYPE_INVALID',
    'VAULT_ENTRY_CONTENT_INVALID',
    'VAULT_TTL_INVALID',
    'SECURITY_DECISION_INVALID'
  ]);
  return known.has(message) ? message : 'VAULT_OPERATION_REFUSED';
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ ok: false, error: 'Méthode non autorisée.' }, 405);

  const declaredLength = Number(req.headers.get('content-length') || '0');
  if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) {
    return json({ ok: false, error: 'Requête trop volumineuse.', code: 'REQUEST_TOO_LARGE' }, 413);
  }

  try {
    // AAL2 est vérifié à CHAQUE appel. Une capacité de coffre ne remplace jamais le JWT.
    const { user, service } = await requiredVaultUser(req);
    const parsed = await req.json().catch(() => ({}));
    const body = parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? parsed as Record<string, unknown>
      : {};

    // L'identité vient exclusivement du JWT vérifié par requiredVaultUser().
    rejectClientIdentity(body);

    const action = safeText(body.action, 40);

    if (action === 'open_session') {
      const deviceKey = safeText(body.device_key, 128);
      if (deviceKey.length < 16) {
        return json({ ok: false, error: 'Identifiant d’appareil invalide.', code: 'DEVICE_KEY_INVALID' }, 400);
      }

      const ttlRaw = body.ttl_seconds == null ? 300 : Number(body.ttl_seconds);
      if (!Number.isInteger(ttlRaw) || ttlRaw < 60 || ttlRaw > 600) {
        throw new Error('VAULT_TTL_INVALID');
      }

      const geo = trustedGeo(req);
      const { data: security, error: securityError } = await service.rpc('security_evaluate_context', {
        p_user_id: user.id,
        p_device_key: deviceKey,
        p_display_name: safeText(body.display_name, 120) || 'Appareil SINJIRA',
        p_device_type: safeDeviceType(body.device_type),
        p_platform: safeText(body.platform, 120),
        p_country_code: geo.country,
        p_region_code: geo.region,
        p_action: 'conscience_vault'
      });
      if (securityError) throw new Error('SECURITY_DECISION_INVALID');

      const decision = assertVaultRiskDecision(security);
      const publicDecision = publicSecurityDecision(security);

      if (decision.outcome === 'challenge') {
        return json({
          ok: false,
          error: 'Une vérification de sécurité supplémentaire est requise.',
          code: 'SECURITY_CHALLENGE_REQUIRED',
          security: publicDecision,
          geo_mode: geo.country ? 'trusted_coarse' : 'disabled'
        }, 403);
      }
      if (decision.outcome === 'block' || decision.score >= 75) {
        return json({
          ok: false,
          error: 'Accès au coffre refusé par la protection du compte.',
          code: 'SECURITY_BLOCKED',
          security: publicDecision,
          geo_mode: geo.country ? 'trusted_coarse' : 'disabled'
        }, 403);
      }
      if (!['allow', 'approved'].includes(decision.outcome)) {
        throw new Error('SECURITY_DECISION_INVALID');
      }

      const { data: sessionId, error: sessionError } = await service.rpc('service_conscience_open_session', {
        p_user_id: user.id,
        p_aal: 'aal2',
        p_risk_score: decision.score,
        p_risk_outcome: decision.outcome,
        p_risk_action: 'conscience_vault',
        p_risk_model_version: 'v25.0',
        p_ttl_seconds: ttlRaw
      });
      if (sessionError || !validUuid(sessionId)) throw new Error('VAULT_OPERATION_REFUSED');

      return json({
        ok: true,
        vault_session_id: sessionId,
        expires_in_seconds: ttlRaw,
        security: publicDecision,
        geo_mode: geo.country ? 'trusted_coarse' : 'disabled',
        privacy: {
          identity_from_verified_jwt: true,
          raw_ip_stored: false,
          gps_used: false,
          client_geo_accepted: false,
          legacy_access: false
        }
      });
    }

    const sessionId = safeText(body.vault_session_id, 80);
    if (!validUuid(sessionId)) throw new Error('VAULT_SESSION_REQUIRED');

    if (action === 'list_entries') {
      const { data, error } = await service.rpc('service_conscience_list_entries', {
        p_user_id: user.id,
        p_session_id: sessionId
      });
      if (error) throw new Error(error.message || 'VAULT_OPERATION_REFUSED');
      return json({ ok: true, entries: Array.isArray(data) ? data : [] });
    }

    if (action === 'create_entry') {
      const type = entryType(body.entry_type);
      const payload = contentPayload(body.content_payload);
      const { data: entryId, error } = await service.rpc('service_conscience_create_entry', {
        p_user_id: user.id,
        p_session_id: sessionId,
        p_entry_type: type,
        p_content_payload: payload
      });
      if (error) throw new Error(error.message || 'VAULT_OPERATION_REFUSED');
      return json({ ok: true, entry_id: entryId });
    }

    if (action === 'update_entry') {
      const id = safeText(body.entry_id, 80);
      if (!validUuid(id)) throw new Error('VAULT_ENTRY_ID_INVALID');
      const type = entryType(body.entry_type);
      const payload = contentPayload(body.content_payload);
      const { data: updated, error } = await service.rpc('service_conscience_update_entry', {
        p_user_id: user.id,
        p_session_id: sessionId,
        p_entry_id: id,
        p_entry_type: type,
        p_content_payload: payload
      });
      if (error) throw new Error(error.message || 'VAULT_OPERATION_REFUSED');
      return json({ ok: true, updated: updated === true });
    }

    if (action === 'delete_entry') {
      const id = safeText(body.entry_id, 80);
      if (!validUuid(id)) throw new Error('VAULT_ENTRY_ID_INVALID');
      const { data: deleted, error } = await service.rpc('service_conscience_delete_entry', {
        p_user_id: user.id,
        p_session_id: sessionId,
        p_entry_id: id
      });
      if (error) throw new Error(error.message || 'VAULT_OPERATION_REFUSED');
      return json({ ok: true, deleted: deleted === true });
    }

    if (action === 'revoke_session') {
      const { data: revoked, error } = await service.rpc('service_conscience_revoke_session', {
        p_user_id: user.id,
        p_session_id: sessionId
      });
      if (error) throw new Error(error.message || 'VAULT_OPERATION_REFUSED');
      return json({ ok: true, revoked: revoked === true });
    }

    return json({ ok: false, error: 'Action inconnue.', code: 'UNKNOWN_ACTION' }, 400);
  } catch (error) {
    const code = errorCode(error);
    // Ne jamais journaliser le corps de requête, le contenu du Registre ou un objet d'erreur SQL complet.
    console.warn('[conscience-vault] opération refusée', code);

    if (code === 'AUTH_REQUIRED') {
      return json({ ok: false, error: 'Connexion requise.', code }, 401);
    }
    if (code === 'MFA_SETUP_REQUIRED') {
      return json({ ok: false, error: 'Une authentification renforcée doit être configurée avant d’ouvrir le coffre.', code }, 403);
    }
    if (code === 'MFA_REQUIRED') {
      return json({ ok: false, error: 'Une vérification renforcée est requise.', code }, 403);
    }
    if (code === 'MFA_STATE_UNAVAILABLE' || code === 'SECURITY_DECISION_INVALID') {
      return json({ ok: false, error: 'La protection du coffre est temporairement indisponible.', code }, 503);
    }
    if (code === 'CLIENT_IDENTITY_FORBIDDEN') {
      return json({ ok: false, error: 'L’identité du compte ne peut pas être fournie par le client.', code }, 400);
    }
    if (code === 'VAULT_TTL_INVALID' || code === 'VAULT_ENTRY_ID_INVALID' || code === 'VAULT_ENTRY_TYPE_INVALID' || code === 'VAULT_ENTRY_CONTENT_INVALID') {
      return json({ ok: false, error: 'Données de coffre invalides.', code }, 400);
    }
    if (code === 'VAULT_SESSION_REQUIRED' || code === 'VAULT_SESSION_INVALID') {
      return json({ ok: false, error: 'Session de coffre invalide ou expirée.', code }, 403);
    }
    return json({ ok: false, error: 'Opération du coffre refusée.', code }, 400);
  }
});