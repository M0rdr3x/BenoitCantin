import { requiredUser, serviceClient } from '../_shared/auth.ts';

const cors = {
  'Access-Control-Allow-Origin': 'https://www.benoitcantin.com',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Vary': 'Origin'
};
const MAX_REQUEST_BYTES = 4096;
const PARTY_CODE_RE = /^FRM-[A-Z0-9]{6}$/;
const PAID_EXTERNAL_SERVICES_ENABLED = false;

function privateJson(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      ...cors,
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'private, no-store, max-age=0',
      'Pragma': 'no-cache',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer',
      'X-Frame-Options': 'DENY',
      'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
    }
  });
}

function cleanText(value: unknown, max = 300) {
  return String(value ?? '').trim().slice(0, max);
}

function num(value: unknown) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function knownRpcError(error: { message?: string } | null) {
  const message = String(error?.message || '');
  const allowed = [
    'FRACTURE_PARTY_NOT_FOUND',
    'FRACTURE_OWNER_REQUIRED',
    'FRACTURE_ENDGAME_REPORT_NOT_FOUND',
    'FRACTURE_PARTY_NOT_ACTIVE',
    'FRACTURE_ENDGAME_INCONSISTENT',
    'FRACTURE_PARTY_CHANGED',
    'FRACTURE_ENDGAME_REPORT_CHANGED'
  ];
  return allowed.find((code) => message === code || message.includes(code)) || '';
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors });
  if (req.method !== 'POST') return privateJson({ ok: false, error: 'Méthode non autorisée.' }, 405);

  try {
    const contentType = (req.headers.get('content-type') || '').toLowerCase();
    if (!contentType.startsWith('application/json')) {
      return privateJson({ ok: false, error: 'Corps JSON requis.' }, 415);
    }
    const declaredLength = Number(req.headers.get('content-length') || '0');
    if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) {
      return privateJson({ ok: false, error: 'Requête trop volumineuse.' }, 413);
    }

    const user = await requiredUser(req);
    const service = serviceClient();

    const rawBody = await req.text();
    if (new TextEncoder().encode(rawBody).byteLength > MAX_REQUEST_BYTES) {
      return privateJson({ ok: false, error: 'Requête trop volumineuse.' }, 413);
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(rawBody);
    } catch {
      return privateJson({ ok: false, error: 'JSON invalide.' }, 400);
    }
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return privateJson({ ok: false, error: 'JSON invalide.' }, 400);
    }
    const body = parsed as Record<string, unknown>;
    if (Object.keys(body).length !== 1 || typeof body.party_code !== 'string') {
      return privateJson({ ok: false, error: 'Code de partie requis.' }, 400);
    }
    const code = body.party_code.trim().toUpperCase();
    if (!PARTY_CODE_RE.test(code)) {
      return privateJson({ ok: false, error: 'Code de partie invalide.' }, 400);
    }

    const { data: party, error: partyError } = await service
      .from('fracture_parties')
      .select('id,party_code,owner_user_id,human_player_count,effective_player_count,play_mode,round_count,updated_at,status')
      .eq('party_code', code)
      .maybeSingle();
    if (partyError) throw new Error('PARTY_LOOKUP_FAILED');
    if (!party) return privateJson({ ok: false, error: 'Partie introuvable.' }, 404);
    if (party.owner_user_id !== user.id) {
      return privateJson({ ok: false, error: 'Seul le créateur de la partie peut transmettre la fin de partie.' }, 403);
    }

    const { data: report, error: reportError } = await service
      .from('fracture_endgame_reports')
      .select('id,party_id,owner_user_id,fields,submitted_at,updated_at')
      .eq('party_id', party.id)
      .maybeSingle();
    if (reportError) throw new Error('REPORT_LOOKUP_FAILED');
    if (!report) {
      return privateJson({ ok: false, error: 'Sauvegardez la Feuille de fin de partie avant de la transmettre.' }, 400);
    }
    if (report.owner_user_id !== user.id) throw new Error('REPORT_OWNER_INCONSISTENT');

    const fields = report.fields && typeof report.fields === 'object' && !Array.isArray(report.fields)
      ? report.fields as Record<string, unknown>
      : {};
    const rounds: Array<Record<string, unknown>> = [];
    for (let i = 1; i <= party.round_count; i += 1) {
      rounds.push({
        round: i,
        resistance: num(fields[`r${i}_resistance`]),
        network: num(fields[`r${i}_network`]),
        winner: cleanText(fields[`r${i}_winner`], 4)
      });
    }

    const metrics = {
      human_player_count: party.human_player_count,
      effective_player_count: party.effective_player_count,
      play_mode: party.play_mode,
      round_count: party.round_count,
      network_agents: num(fields.network_agents),
      rounds,
      bonus_resistance: num(fields.bonus_resistance),
      bonus_network: num(fields.bonus_network),
      rounds_resistance: num(fields.rounds_resistance),
      rounds_network: num(fields.rounds_network),
      rounds_tied: num(fields.rounds_tied),
      total_resistance: num(fields.total_resistance),
      total_network: num(fields.total_network),
      winner_final: cleanText(fields.winner_final, 80),
      tiebreak_required: cleanText(fields.tiebreak_required, 8)
    };

    const { data: submitResult, error: submitError } = await service.rpc('service_submit_fracture_endgame', {
      p_user_id: user.id,
      p_party_id: party.id,
      p_party_updated_at: party.updated_at,
      p_report_id: report.id,
      p_report_updated_at: report.updated_at,
      p_metrics: metrics,
      p_feedback: {}
    });
    if (submitError) {
      const codeFromRpc = knownRpcError(submitError);
      console.error('[submit-fracture-endgame]', { code: codeFromRpc || 'FRACTURE_ENDGAME_RPC_FAILED' });
      if (codeFromRpc === 'FRACTURE_OWNER_REQUIRED') {
        return privateJson({ ok: false, error: 'Seul le créateur de la partie peut transmettre la fin de partie.' }, 403);
      }
      if (codeFromRpc === 'FRACTURE_PARTY_NOT_FOUND') {
        return privateJson({ ok: false, error: 'Partie introuvable.' }, 404);
      }
      if (codeFromRpc === 'FRACTURE_ENDGAME_REPORT_NOT_FOUND') {
        return privateJson({ ok: false, error: 'Sauvegardez la Feuille de fin de partie avant de la transmettre.' }, 400);
      }
      if (codeFromRpc === 'FRACTURE_PARTY_CHANGED' || codeFromRpc === 'FRACTURE_ENDGAME_REPORT_CHANGED') {
        return privateJson({ ok: false, error: 'La partie ou sa feuille a changé. Rechargez avant de transmettre.' }, 409);
      }
      if (codeFromRpc === 'FRACTURE_PARTY_NOT_ACTIVE' || codeFromRpc === 'FRACTURE_ENDGAME_INCONSISTENT') {
        return privateJson({ ok: false, error: 'Cette fin de partie ne peut plus être transmise dans son état actuel.' }, 409);
      }
      throw new Error('FRACTURE_ENDGAME_RPC_FAILED');
    }

    if (submitResult?.already_submitted === true) {
      return privateJson({ ok: false, error: 'Cette fin de partie a déjà été transmise.' }, 409);
    }

    let email_sent = false;
    const resend = Deno.env.get('RESEND_API_KEY');
    const from = Deno.env.get('REPORT_FROM_EMAIL');
    const to = Deno.env.get('FRACTURE_REPORT_TO_EMAIL') || 'kingtyrano@gmail.com';
    if (PAID_EXTERNAL_SERVICES_ENABLED && resend && from) {
      const bodyText = [
        `Fracture du Réseau-Mère — fin de partie ${party.party_code}`,
        `Humains : ${party.human_player_count}`,
        `Sièges effectifs : ${party.effective_player_count}`,
        `Format : ${party.round_count} rondes`,
        `Agents Réseau-Mère : ${metrics.network_agents}`,
        `Total Résistance : ${metrics.total_resistance}`,
        `Total Réseau-Mère : ${metrics.total_network}`,
        `Rondes gagnées R : ${metrics.rounds_resistance}`,
        `Rondes gagnées RM : ${metrics.rounds_network}`,
        `Égalités : ${metrics.rounds_tied}`,
        `Gagnant : ${metrics.winner_final}`,
        `Départage : ${metrics.tiebreak_required}`
      ].join('\n');
      const response = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { Authorization: `Bearer ${resend}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from,
          to: [to],
          subject: `SINJIRA — Fin de partie ${party.party_code}`,
          text: bodyText
        })
      });
      email_sent = response.ok;
    }

    return privateJson({ ok: true, email_sent, paid_external_services_enabled: PAID_EXTERNAL_SERVICES_ENABLED });
  } catch (error) {
    const code = error instanceof Error ? error.message : '';
    if (code === 'AUTH_REQUIRED') {
      return privateJson({ ok: false, error: 'Connexion requise.' }, 401);
    }
    console.error('[submit-fracture-endgame]', { code: 'FRACTURE_ENDGAME_FAILED' });
    return privateJson({ ok: false, error: 'Transmission de la fin de partie impossible.' }, 500);
  }
});
