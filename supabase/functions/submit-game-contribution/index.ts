import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

function clean(value: unknown, max = 180) {
  return String(value ?? '').trim().slice(0, max);
}

function fractureMetrics(session: any, fields: Record<string, unknown>) {
  return {
    player_count: session.player_count,
    duration_minutes: session.duration_minutes,
    result: clean(fields.resultat_camp),
    final_identity: clean(fields.identite_finale),
    unique_proof_confirmed: Boolean(fields.preuve_unique_confirmee),
    final_accusation_count: Array.from({ length: 7 }, (_, index) => clean(fields[`accusation_${index + 1}`])).filter(Boolean).length,
    rounds: Array.from({ length: 10 }, (_, index) => {
      const n = index + 1;
      return {
        round: n,
        card_a: clean(fields[`ronde_${n}_carte_a`]),
        card_b: clean(fields[`ronde_${n}_carte_b`]),
        report_present: Boolean(clean(fields[`ronde_${n}_rapport`])),
        proof: Boolean(fields[`ronde_${n}_preuve`]),
        suspicion_present: Boolean(clean(fields[`ronde_${n}_soupcon`]))
      };
    })
  };
}

function genericMetrics(session: any, fields: Record<string, unknown>) {
  // Pour les futurs jeux : métriques sûres communes seulement.
  // Les adaptateurs propres à chaque jeu pourront être ajoutés ici.
  return {
    player_count: session.player_count,
    duration_minutes: session.duration_minutes,
    result: clean(fields.resultat_camp || fields.result || fields.outcome),
    completed: session.status === 'finished',
    field_count_used: Object.values(fields || {}).filter((v) => String(v ?? '').trim() !== '').length
  };
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ ok: false, error: 'Méthode non autorisée.' }, 405);

  try {
    const user = await requiredUser(req);
    const { session_id } = await req.json();
    if (!session_id) return json({ ok: false, error: 'Partie manquante.' }, 400);

    const service = serviceClient();
    const [{ data: consent }, { data: session }, { data: sheet }, { data: feedback }] = await Promise.all([
      service.from('research_consents').select('*').eq('user_id', user.id).maybeSingle(),
      service.from('game_sessions').select('*').eq('id', session_id).eq('user_id', user.id).maybeSingle(),
      service.from('player_sheets').select('fields').eq('session_id', session_id).eq('user_id', user.id).maybeSingle(),
      service.from('session_feedback').select('*').eq('session_id', session_id).eq('user_id', user.id).maybeSingle()
    ]);

    if (!consent?.participate) {
      return json({ ok: false, error: 'Activez d’abord le Programme Contributeur dans votre compte.' }, 403);
    }
    if (!session || !sheet) {
      return json({ ok: false, error: 'Sauvegardez d’abord cette partie dans votre compte.' }, 400);
    }

    const fields = sheet.fields || {};
    const metrics = session.game_slug === 'fracture-du-reseau-mere'
      ? fractureMetrics(session, fields)
      : genericMetrics(session, fields);

    const feedbackPayload: Record<string, unknown> = {
      rating: feedback?.rating || null,
      difficulty: feedback?.difficulty || null
    };

    if (consent.share_free_text) {
      feedbackPayload.favorite_mechanic = clean(feedback?.favorite_mechanic, 1000);
      feedbackPayload.unclear_text = clean(feedback?.unclear_text, 3000);
      feedbackPayload.extension_idea = clean(feedback?.extension_idea, 3000);
    }

    const { data: contributionId, error } = await service.rpc('record_sinjira_contribution', {
      p_user_id: user.id,
      p_session_id: session.id,
      p_game_slug: session.game_slug,
      p_metrics: metrics,
      p_feedback: feedbackPayload,
      p_version: '2.0'
    });

    if (error) {
      const duplicate = error.message?.includes('déjà été partagée');
      return json({
        ok: false,
        error: duplicate ? 'Cette partie a déjà été partagée.' : 'Le partage a échoué.'
      }, duplicate ? 409 : 500);
    }

    return json({ ok: true, contribution_id: contributionId });
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') return json({ ok: false, error: 'Connexion requise.' }, 401);
    console.error(error);
    return json({ ok: false, error: 'Erreur de contribution.' }, 500);
  }
});
