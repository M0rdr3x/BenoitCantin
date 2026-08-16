import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

function increment(map: Record<string, number>, key: string) {
  const normalized = String(key || '').trim().slice(0,120) || 'Non indiqué';
  map[normalized] = (map[normalized] || 0) + 1;
}
function finite(v:unknown){const n=Number(v);return Number.isFinite(n)?n:null}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ok:false,error:'Méthode non autorisée.'},405);
  try {
    const user = await requiredUser(req);
    const body = await req.json().catch(() => ({}));
    const gameSlug = String(body?.game_slug || 'fracture-du-reseau-mere').trim().toLowerCase();
    if(!/^[a-z0-9-]{1,80}$/.test(gameSlug))return json({ok:false,error:'Identifiant de jeu invalide.'},400);
    const service = serviceClient();
    const { data: admin, error:adminError } = await service.rpc('is_sinjira_admin',{p_user_id:user.id});
    if(adminError||!admin) return json({ ok: false, error: 'Accès administrateur refusé.' }, 403);

    const { data: rows = [], error } = await service
      .from('internal_gameplay_contributions')
      .select('metrics,feedback,created_at')
      .eq('game_slug', gameSlug)
      .order('created_at', { ascending: false })
      .limit(10000);
    if (error) return json({ ok: false, error: 'Impossible de charger les données.' }, 500);

    const results: Record<string, number> = {},difficulty: Record<string, number> = {},cardCounts: Record<string, number> = {};
    let playersTotal = 0, playersCount = 0,durationTotal = 0, durationCount = 0,ratingTotal = 0, ratingCount = 0;

    for (const row of rows) {
      const m = row.metrics || {},f = row.feedback || {};
      increment(results, String(m.result || m.winner || m.winner_final || ''));
      increment(difficulty, String(f.difficulty || ''));
      const players=finite(m.human_player_count ?? m.player_count);
      if (players!=null && players>0 && players<=20) { playersTotal += players; playersCount++; }
      const duration=finite(m.duration_minutes);
      if (duration!=null && duration>=0 && duration<=1440) { durationTotal += duration; durationCount++; }
      const rating=finite(f.rating);
      if (rating!=null && rating>0 && rating<=5) { ratingTotal += rating; ratingCount++; }
      for (const round of Array.isArray(m.rounds)?m.rounds:[]) {
        for (const card of [round?.card_a, round?.card_b]) {
          const key = String(card || '').trim().slice(0,160);
          if (key) cardCounts[key] = (cardCounts[key] || 0) + 1;
        }
      }
    }

    const topCards = Object.entries(cardCounts).sort((a, b) => b[1] - a[1]).slice(0, 20).map(([card, count]) => ({ card, count }));
    return json({ok:true,analytics:{
      total_contributions: rows.length,
      average_player_count: playersCount ? Math.round((playersTotal / playersCount) * 10) / 10 : null,
      average_duration_minutes: durationCount ? Math.round(durationTotal / durationCount) : null,
      average_rating: ratingCount ? Math.round((ratingTotal / ratingCount) * 10) / 10 : null,
      results,difficulty,top_cards:topCards
    }});
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') return json({ ok: false, error: 'Connexion requise.' }, 401);
    console.error('[SINJIRA analytics]',error);
    return json({ ok: false, error: 'Erreur d’analyse.' }, 500);
  }
});
