import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

function increment(map: Record<string, number>, key: string) {
  const normalized = key || 'Non indiqué';
  map[normalized] = (map[normalized] || 0) + 1;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  try {
    const user = await requiredUser(req);
    const body = await req.json().catch(() => ({}));
    const gameSlug = body?.game_slug || 'fracture-du-reseau-mere';
    const service = serviceClient();

    const { data: admin } = await service
      .from('internal_admin_users')
      .select('user_id')
      .eq('user_id', user.id)
      .maybeSingle();

    if (!admin) return json({ ok: false, error: 'Accès administrateur refusé.' }, 403);

    const { data: rows = [], error } = await service
      .from('internal_gameplay_contributions')
      .select('metrics,feedback,created_at')
      .eq('game_slug', gameSlug)
      .order('created_at', { ascending: false })
      .limit(10000);

    if (error) return json({ ok: false, error: 'Impossible de charger les données.' }, 500);

    const results: Record<string, number> = {};
    const difficulty: Record<string, number> = {};
    const cardCounts: Record<string, number> = {};
    let playersTotal = 0, playersCount = 0;
    let durationTotal = 0, durationCount = 0;
    let ratingTotal = 0, ratingCount = 0;

    for (const row of rows) {
      const m = row.metrics || {};
      const f = row.feedback || {};
      increment(results, String(m.result || ''));
      increment(difficulty, String(f.difficulty || ''));

      if (Number.isFinite(Number(m.player_count))) {
        playersTotal += Number(m.player_count); playersCount++;
      }
      if (Number.isFinite(Number(m.duration_minutes))) {
        durationTotal += Number(m.duration_minutes); durationCount++;
      }
      if (Number.isFinite(Number(f.rating)) && Number(f.rating) > 0) {
        ratingTotal += Number(f.rating); ratingCount++;
      }

      for (const round of (m.rounds || [])) {
        for (const card of [round.card_a, round.card_b]) {
          const key = String(card || '').trim();
          if (key) cardCounts[key] = (cardCounts[key] || 0) + 1;
        }
      }
    }

    const topCards = Object.entries(cardCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([card, count]) => ({ card, count }));

    return json({
      ok: true,
      analytics: {
        total_contributions: rows.length,
        average_player_count: playersCount ? Math.round((playersTotal / playersCount) * 10) / 10 : null,
        average_duration_minutes: durationCount ? Math.round(durationTotal / durationCount) : null,
        average_rating: ratingCount ? Math.round((ratingTotal / ratingCount) * 10) / 10 : null,
        results,
        difficulty,
        top_cards: topCards
      }
    });
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') return json({ ok: false, error: 'Connexion requise.' }, 401);
    console.error(error);
    return json({ ok: false, error: 'Erreur d’analyse.' }, 500);
  }
});
