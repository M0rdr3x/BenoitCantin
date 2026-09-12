import { corsHeaders } from '../_shared/cors.ts';
import { requiredAdmin } from '../_shared/auth.ts';

const MAX_REQUEST_BYTES = 4096;
const DEFAULT_GAME_SLUG = 'fracture-du-reseau-mere';
const GAME_SLUG_RE = /^[a-z0-9][a-z0-9_-]{0,79}$/;
const PRIVATE_HEADERS = {
  ...corsHeaders,
  'Content-Type': 'application/json; charset=utf-8',
  'Cache-Control': 'private, no-store, max-age=0',
  'Pragma': 'no-cache',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer'
};
const SAFE_LOG_CODES = new Set([
  'AUTH_REQUIRED','ADMIN_REQUIRED','MFA_REQUIRED','MFA_STATE_UNAVAILABLE',
  'REQUEST_TOO_LARGE','JSON_REQUIRED','INVALID_JSON','INVALID_GAME_SLUG'
]);

function privateJson(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: PRIVATE_HEADERS });
}

function adminAnalyticsLogCode(error: unknown) {
  const code = error instanceof Error ? error.message : '';
  return SAFE_LOG_CODES.has(code) ? code : 'ADMIN_ANALYTICS_BACKEND_FAILED';
}

async function readLimitedJson(req: Request) {
  const declaredRaw = req.headers.get('content-length');
  if (declaredRaw) {
    const declared = Number(declaredRaw);
    if (!Number.isFinite(declared) || declared < 0 || declared > MAX_REQUEST_BYTES) {
      throw new Error('REQUEST_TOO_LARGE');
    }
  }

  const reader = req.body?.getReader();
  if (!reader) return {};
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    if (!value) continue;
    total += value.byteLength;
    if (total > MAX_REQUEST_BYTES) {
      try { await reader.cancel(); } catch { /* Le rejet de taille reste prioritaire. */ }
      throw new Error('REQUEST_TOO_LARGE');
    }
    chunks.push(value);
  }

  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }

  let raw: string;
  try {
    raw = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  } catch {
    throw new Error('INVALID_JSON');
  }
  if (!raw.trim()) return {};

  const contentType = (req.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase();
  if (contentType !== 'application/json') throw new Error('JSON_REQUIRED');

  let body: unknown;
  try {
    body = JSON.parse(raw);
  } catch {
    throw new Error('INVALID_JSON');
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) throw new Error('INVALID_JSON');
  return body as Record<string, unknown>;
}

function gameSlugFrom(body: Record<string, unknown>) {
  const candidate = body.game_slug == null || body.game_slug === ''
    ? DEFAULT_GAME_SLUG
    : String(body.game_slug).trim();
  if (!GAME_SLUG_RE.test(candidate)) throw new Error('INVALID_GAME_SLUG');
  return candidate;
}

function increment(map: Record<string, number>, key: string) {
  const normalized = key || 'Non indiqué';
  map[normalized] = (map[normalized] || 0) + 1;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return privateJson({ ok: false, error: 'Méthode non autorisée.', code: 'METHOD_NOT_ALLOWED' }, 405);

  try {
    const { service } = await requiredAdmin(req);
    const body = await readLimitedJson(req);
    const gameSlug = gameSlugFrom(body);

    const { data: rows = [], error } = await service
      .from('internal_gameplay_contributions')
      .select('metrics,feedback')
      .eq('game_slug', gameSlug)
      .order('created_at', { ascending: false })
      .limit(10000);

    if (error) throw error;

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

    return privateJson({
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
    console.error('[admin-analytics]', adminAnalyticsLogCode(error));
    if (error?.message === 'AUTH_REQUIRED') return privateJson({ ok: false, error: 'Connexion requise.', code: 'AUTH_REQUIRED' }, 401);
    if (error?.message === 'ADMIN_REQUIRED') return privateJson({ ok: false, error: 'Accès administrateur refusé.', code: 'ADMIN_REQUIRED' }, 403);
    if (error?.message === 'MFA_REQUIRED') return privateJson({ ok: false, error: 'MFA_REQUIRED', code: 'MFA_REQUIRED' }, 403);
    if (error?.message === 'MFA_STATE_UNAVAILABLE') return privateJson({ ok: false, error: 'État MFA temporairement indisponible.', code: 'MFA_STATE_UNAVAILABLE' }, 503);
    if (error?.message === 'REQUEST_TOO_LARGE') return privateJson({ ok: false, error: 'Requête trop volumineuse.', code:'REQUEST_TOO_LARGE' }, 413);
    if (error?.message === 'JSON_REQUIRED') return privateJson({ ok: false, error: 'Corps JSON requis.', code:'JSON_REQUIRED' }, 415);
    if (error?.message === 'INVALID_JSON') return privateJson({ ok: false, error: 'JSON invalide.', code:'INVALID_JSON' }, 400);
    if (error?.message === 'INVALID_GAME_SLUG') return privateJson({ ok: false, error: 'Identifiant de jeu invalide.', code:'INVALID_GAME_SLUG' }, 400);
    return privateJson({ ok: false, error: 'Erreur d’analyse.', code:'ANALYTICS_FAILED' }, 500);
  }
});
