import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  try {
    const user = await requiredUser(req);
    const body = await req.json().catch(() => ({}));
    const service = serviceClient();
    const { data, error } = await service.rpc('revoke_sinjira_contributions', {
      p_user_id: user.id,
      p_session_id: body?.all ? null : (body?.session_id || null)
    });
    if (error) return json({ ok: false, error: 'Suppression impossible.' }, 500);
    return json({ ok: true, removed: data || 0 });
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') return json({ ok: false, error: 'Connexion requise.' }, 401);
    return json({ ok: false, error: 'Erreur.' }, 500);
  }
});
