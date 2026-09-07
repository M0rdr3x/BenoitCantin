import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';
import { buildSecurityPushMessage, SECURITY_PUSH_MAX_BATCH } from '../_shared/security-push-policy.mjs';
import {
  SECURITY_PUSH_RECEIPT_URL,
  SECURITY_PUSH_SEND_URL,
  postSecurityPushJson,
} from '../_shared/security-push-network.mjs';
import {
  buildSecurityPushReceiptRequest,
  resolveSecurityPushReceipts,
  resolveSecurityPushTickets,
  SECURITY_PUSH_RECEIPT_MAX_BATCH,
} from '../_shared/security-push-receipts.mjs';

function safeText(value: unknown, max: number) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}

function safeDeviceType(value: unknown) {
  const type = safeText(value, 20);
  return ['browser', 'ios', 'android', 'tablet', 'other'].includes(type) ? type : 'other';
}

/**
 * La localisation de sécurité est désactivée par défaut.
 * Elle ne peut être alimentée que lorsqu'un proxy contrôlé par SINJIRA ajoute
 * des en-têtes de géolocalisation approximative et que l'environnement active
 * explicitement SINJIRA_TRUST_GEO_HEADERS=true.
 *
 * On ne lit jamais l'IP du visiteur et aucune donnée GPS n'est demandée.
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

async function processSecurityPushReceipts(service: ReturnType<typeof serviceClient>) {
  const nowIso = new Date().toISOString();
  const { error: cleanupError } = await service
    .from('security_push_receipt_queue')
    .delete()
    .lte('expires_at', nowIso);
  if (cleanupError) {
    console.warn('[security-context] purge reçus push indisponible');
  }

  const { data: pending, error } = await service
    .from('security_push_receipt_queue')
    .select('expo_receipt_id,endpoint_id')
    .lte('available_after', nowIso)
    .gt('expires_at', nowIso)
    .order('available_after', { ascending: true })
    .limit(SECURITY_PUSH_RECEIPT_MAX_BATCH);
  if (error) {
    console.warn('[security-context] reçus push indisponibles');
    return;
  }
  if (!pending?.length) return;

  try {
    const request = buildSecurityPushReceiptRequest(pending.map((row: any) => row.expo_receipt_id));
    const response = await postSecurityPushJson(SECURITY_PUSH_RECEIPT_URL, request);
    if (!response.ok) {
      console.warn('[security-context] Expo Receipt HTTP', response.status);
      return;
    }

    const result = await response.json().catch(() => null);
    const resolved = resolveSecurityPushReceipts(pending, result?.data);
    if (!resolved.handledReceiptIds.length) return;

    if (resolved.invalidEndpointIds.length) {
      const { error: disableError } = await service
        .from('security_push_endpoints')
        .update({ enabled: false, updated_at: new Date().toISOString() })
        .in('id', resolved.invalidEndpointIds);
      if (disableError) {
        console.warn('[security-context] désactivation endpoint push indisponible');
        return;
      }
    }

    const { error: deleteError } = await service
      .from('security_push_receipt_queue')
      .delete()
      .in('expo_receipt_id', resolved.handledReceiptIds);
    if (deleteError) {
      console.warn('[security-context] suppression reçus push indisponible');
    }
  } catch {
    console.warn('[security-context] lecture reçus push impossible');
  }
}

async function sendSecurityPush(service: ReturnType<typeof serviceClient>, userId: string, security: any) {
  const outcome = String(security?.outcome || '');
  if (!['challenge', 'block'].includes(outcome)) return;

  const { data: endpoints, error } = await service
    .from('security_push_endpoints')
    .select('id,expo_push_token')
    .eq('user_id', userId)
    .eq('enabled', true);
  if (error) {
    console.warn('[security-context] endpoints push indisponibles');
    return;
  }
  if (!endpoints?.length) return;

  const invalidIds: string[] = [];
  for (let offset = 0; offset < endpoints.length; offset += SECURITY_PUSH_MAX_BATCH) {
    const endpointBatch = endpoints.slice(offset, offset + SECURITY_PUSH_MAX_BATCH);
    const messages = endpointBatch.map((endpoint: any) =>
      buildSecurityPushMessage(endpoint.expo_push_token, outcome)
    );

    try {
      const response = await postSecurityPushJson(SECURITY_PUSH_SEND_URL, messages);
      if (!response.ok) {
        console.warn('[security-context] Expo Push HTTP', response.status);
        continue;
      }
      const result = await response.json().catch(() => null);
      const tickets = Array.isArray(result?.data) ? result.data : [];
      const resolved = resolveSecurityPushTickets(tickets, endpointBatch);
      invalidIds.push(...resolved.invalidEndpointIds);

      if (resolved.receiptRows.length) {
        const { error: queueError } = await service
          .from('security_push_receipt_queue')
          .upsert(resolved.receiptRows, { onConflict: 'expo_receipt_id', ignoreDuplicates: true });
        if (queueError) {
          console.warn('[security-context] mise en file reçus push indisponible');
        }
      }
    } catch {
      console.warn('[security-context] envoi push impossible');
    }
  }

  if (invalidIds.length) {
    await service
      .from('security_push_endpoints')
      .update({ enabled: false, updated_at: new Date().toISOString() })
      .in('id', Array.from(new Set(invalidIds)));
  }
}

async function runSecurityPushBackground(
  service: ReturnType<typeof serviceClient>,
  userId: string,
  security: any,
) {
  try {
    await processSecurityPushReceipts(service);
    await sendSecurityPush(service, userId, security);
  } catch {
    console.warn('[security-context] tâche push de fond impossible');
  }
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ ok: false, error: 'Méthode non autorisée.' }, 405);

  try {
    const user = await requiredUser(req);
    const body = await req.json().catch(() => ({}));
    const deviceKey = safeText(body?.device_key, 128);
    if (deviceKey.length < 16) return json({ ok: false, error: 'Identifiant d’appareil invalide.' }, 400);

    const geo = trustedGeo(req);
    const service = serviceClient();
    const { data, error } = await service.rpc('security_evaluate_context', {
      p_user_id: user.id,
      p_device_key: deviceKey,
      p_display_name: safeText(body?.display_name, 120) || 'Appareil SINJIRA',
      p_device_type: safeDeviceType(body?.device_type),
      p_platform: safeText(body?.platform, 120),
      p_country_code: geo.country,
      p_region_code: geo.region,
      p_action: safeText(body?.action, 80) || 'session'
    });
    if (error) throw error;

    EdgeRuntime.waitUntil(runSecurityPushBackground(service, user.id, data));

    return json({
      ok: true,
      security: data,
      geo_mode: geo.country ? 'trusted_coarse' : 'disabled',
      privacy: {
        raw_ip_stored: false,
        gps_used: false,
        geo_reused_for_ads: false,
        push_reveals_location: false
      }
    });
  } catch (error) {
    console.error('[security-context]', error);
    if (error?.message === 'AUTH_REQUIRED') return json({ ok: false, error: 'Connexion requise.', code: 'AUTH_REQUIRED' }, 401);
    return json({ ok: false, error: 'Le contexte de sécurité est temporairement indisponible.' }, 500);
  }
});
