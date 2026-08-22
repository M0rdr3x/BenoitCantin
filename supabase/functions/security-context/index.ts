import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

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

async function sendSecurityPush(service: ReturnType<typeof serviceClient>, userId: string, security: any) {
  if (!security || !['challenge', 'block'].includes(String(security.outcome || ''))) return;

  const { data: endpoints, error } = await service
    .from('security_push_endpoints')
    .select('id,expo_push_token')
    .eq('user_id', userId)
    .eq('enabled', true);
  if (error) {
    console.warn('[security-context] endpoints push indisponibles', error.message);
    return;
  }
  if (!endpoints?.length) return;

  const challenged = security.outcome === 'challenge';
  const messages = endpoints.map((endpoint: any) => ({
    to: endpoint.expo_push_token,
    sound: null,
    title: 'Sécurité SINJIRA',
    body: challenged
      ? 'Une connexion inhabituelle demande votre attention.'
      : 'SINJIRA a bloqué une tentative nécessitant votre attention.',
    data: { path: '/compte/securite.html' },
    channelId: 'security',
    priority: 'high',
    ttl: 600
  }));

  try {
    const response = await fetch('https://exp.host/--/api/v2/push/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(messages)
    });
    if (!response.ok) {
      console.warn('[security-context] Expo Push HTTP', response.status, await response.text());
      return;
    }
    const result = await response.json().catch(() => null);
    const tickets = Array.isArray(result?.data) ? result.data : [];
    const invalidIds: string[] = [];
    tickets.forEach((ticket: any, index: number) => {
      if (ticket?.status === 'error' && ticket?.details?.error === 'DeviceNotRegistered' && endpoints[index]?.id) {
        invalidIds.push(endpoints[index].id);
      }
    });
    if (invalidIds.length) {
      await service.from('security_push_endpoints').update({ enabled: false, updated_at: new Date().toISOString() }).in('id', invalidIds);
    }
  } catch (error) {
    console.warn('[security-context] envoi push impossible', error);
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

    await sendSecurityPush(service, user.id, data);

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
