import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ok:false,error:'Méthode non autorisée.'},405);
  try {
    const user = await requiredUser(req);
    const body = await req.json().catch(() => ({}));
    const all=body?.all===true,sessionId=all?null:String(body?.session_id||'').trim()||null;
    if(!all&&!sessionId)return json({ok:false,error:'Partie manquante.'},400);
    const service = serviceClient();
    const { data, error } = await service.rpc('revoke_sinjira_contributions', {
      p_user_id: user.id,
      p_session_id: sessionId
    });
    if (error) {
      console.error('[SINJIRA revoke contributions]',error);
      return json({ ok: false, error: 'Suppression impossible.' }, 500);
    }
    return json({ ok: true, removed: Number(data || 0) });
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') return json({ ok: false, error: 'Connexion requise.' }, 401);
    console.error('[SINJIRA revoke contributions]',error);
    return json({ ok: false, error: 'Erreur de révocation.' }, 500);
  }
});
