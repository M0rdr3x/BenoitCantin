import { corsHeaders } from '../_shared/cors.ts';
import { requiredAdmin } from '../_shared/auth.ts';

const MAX_REQUEST_BYTES = 4096;
const SAFE_LOG_CODES = new Set([
  'AUTH_REQUIRED','ADMIN_REQUIRED','MFA_REQUIRED','MFA_STATE_UNAVAILABLE',
  'REQUEST_TOO_LARGE','JSON_REQUIRED','INVALID_JSON',
  'REPORT_DASHBOARD_QUERY_FAILED','REPORT_PROFILES_LOOKUP_FAILED','REPORT_OWNER_LOOKUP_FAILED'
]);
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

function safeLogCode(error: unknown) {
  const code = error instanceof Error ? error.message : '';
  return SAFE_LOG_CODES.has(code) ? code : 'ADMIN_REPORTS_FAILED';
}

async function readLimitedJson(req: Request): Promise<Record<string, unknown>> {
  const rawLength = req.headers.get('content-length');
  if (rawLength) {
    const declared = Number(rawLength);
    if (!Number.isFinite(declared) || declared < 0 || declared > MAX_REQUEST_BYTES) {
      throw new Error('REQUEST_TOO_LARGE');
    }
  }

  const contentType = (req.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase();
  if (contentType !== 'application/json') throw new Error('JSON_REQUIRED');

  const raw = await req.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_REQUEST_BYTES) {
    throw new Error('REQUEST_TOO_LARGE');
  }

  let body: unknown;
  try {
    body = JSON.parse(raw || '{}');
  } catch {
    throw new Error('INVALID_JSON');
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    throw new Error('INVALID_JSON');
  }
  return body as Record<string, unknown>;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return privateJson({ ok:false, error:'Méthode non autorisée.' }, 405);

  try {
    const { service } = await requiredAdmin(req);
    const body = await readLimitedJson(req);
    const action = typeof body.action === 'string' ? body.action.trim().slice(0, 64) : '';

    if (action === 'dashboard') {
      const [
        reports,
        active,
        finished
      ] = await Promise.all([
        service.from('fracture_endgame_reports').select('id', { count:'exact', head:true }).not('submitted_at','is',null),
        service.from('fracture_parties').select('id', { count:'exact', head:true }).eq('status','in_progress'),
        service.from('fracture_parties').select('id', { count:'exact', head:true }).eq('status','finished')
      ]);
      if (reports.error || active.error || finished.error) throw new Error('REPORT_DASHBOARD_QUERY_FAILED');

      return privateJson({
        ok:true,
        dashboard:{
          game_reports: reports.count || 0,
          active_parties: active.count || 0,
          finished_parties: finished.count || 0
        }
      });
    }

    if (action === 'list_game_reports') {
      const { data: rows = [], error } = await service
        .from('fracture_endgame_reports')
        .select(`
          id, party_id, owner_user_id, fields, submitted_at, created_at,
          fracture_parties(
            party_code, human_player_count, effective_player_count,
            play_mode, round_count, status
          )
        `)
        .not('submitted_at','is',null)
        .order('submitted_at',{ ascending:false })
        .limit(2000);

      if (error) throw error;

      const ownerIds = [...new Set(rows.map((r:any) => r.owner_user_id).filter(Boolean))];
      const profileResult = ownerIds.length
        ? await service.from('profiles').select('user_id,pseudo,display_name').in('user_id', ownerIds)
        : { data: [] as any[], error: null };
      if (profileResult.error) throw new Error('REPORT_PROFILES_LOOKUP_FAILED');
      const profiles = profileResult.data || [];

      const profileMap = new Map((profiles || []).map((p:any) => [p.user_id,p]));
      const emails = new Map<string,string>();

      for (const id of ownerIds) {
        const { data, error: ownerError } = await service.auth.admin.getUserById(id);
        if (ownerError) throw new Error('REPORT_OWNER_LOOKUP_FAILED');
        if (data?.user?.email) emails.set(id, data.user.email);
      }

      const reports = rows.map((r:any) => {
        const p = r.fracture_parties || {};
        const profile = profileMap.get(r.owner_user_id) || {};
        return {
          id: r.id,
          party_code: p.party_code,
          human_player_count: p.human_player_count,
          effective_player_count: p.effective_player_count,
          play_mode: p.play_mode,
          round_count: p.round_count,
          party_status: p.status,
          fields: r.fields || {},
          submitted_at: r.submitted_at,
          owner: {
            pseudo: profile.pseudo || '',
            display_name: profile.display_name || '',
            email: emails.get(r.owner_user_id) || ''
          }
        };
      });

      let resistance = 0, network = 0, ties = 0;
      for (const r of reports) {
        const winner = String(r.fields?.winner_final || '').toLowerCase();
        if (winner.includes('résistance') || winner.includes('resistance')) resistance++;
        else if (winner.includes('réseau') || winner.includes('reseau')) network++;
        else ties++;
      }

      return privateJson({
        ok:true,
        reports,
        summary:{
          count: reports.length,
          resistance_wins: resistance,
          network_wins: network,
          ties
        }
      });
    }

    return privateJson({ ok:false, error:'Action inconnue.' }, 400);
  } catch (error) {
    console.error('[admin-reports]', safeLogCode(error));
    if (error?.message === 'AUTH_REQUIRED') return privateJson({ ok:false, error:'Connexion requise.', code:'AUTH_REQUIRED' }, 401);
    if (error?.message === 'ADMIN_REQUIRED') return privateJson({ ok:false, error:'Accès administrateur refusé.', code:'ADMIN_REQUIRED' }, 403);
    if (error?.message === 'MFA_REQUIRED') return privateJson({ ok:false, error:'MFA_REQUIRED', code:'MFA_REQUIRED' }, 403);
    if (error?.message === 'MFA_STATE_UNAVAILABLE') return privateJson({ ok:false, error:'État MFA temporairement indisponible.', code:'MFA_STATE_UNAVAILABLE' }, 503);
    if (error?.message === 'REQUEST_TOO_LARGE') return privateJson({ ok:false, error:'Requête trop volumineuse.', code:'REQUEST_TOO_LARGE' }, 413);
    if (error?.message === 'JSON_REQUIRED') return privateJson({ ok:false, error:'Corps JSON requis.', code:'JSON_REQUIRED' }, 415);
    if (error?.message === 'INVALID_JSON') return privateJson({ ok:false, error:'JSON invalide.', code:'INVALID_JSON' }, 400);
    if (error?.message === 'REPORT_DASHBOARD_QUERY_FAILED') return privateJson({ ok:false, error:'Rapport administrateur temporairement indisponible.', code:'REPORT_DASHBOARD_QUERY_FAILED' }, 503);
    if (error?.message === 'REPORT_PROFILES_LOOKUP_FAILED') return privateJson({ ok:false, error:'Identités des rapports temporairement indisponibles.', code:'REPORT_PROFILES_LOOKUP_FAILED' }, 503);
    if (error?.message === 'REPORT_OWNER_LOOKUP_FAILED') return privateJson({ ok:false, error:'Comptes des rapports temporairement indisponibles.', code:'REPORT_OWNER_LOOKUP_FAILED' }, 503);
    return privateJson({ ok:false, error:'Erreur rapports administrateur.', code:'ADMIN_REPORTS_FAILED' }, 500);
  }
});
