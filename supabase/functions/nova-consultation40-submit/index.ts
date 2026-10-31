import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';
import { readBoundedJson, MAX_REQUEST_BYTES } from '../_shared/nova_survey_body.mjs';

// Préparé, jamais activé automatiquement : exige revue confidentialité,
// configuration du responsable du traitement et publication Edge distincte.
const SURVEY_ID = 'nova-orientations-40-v1';
const ORIGIN = 'https://www.benoitcantin.com';
const VALUES = new Set(['pour','contre','sans_opinion']);
const HEADERS = {
  ...corsHeaders,
  'Content-Type': 'application/json; charset=utf-8',
  'Cache-Control': 'private, no-store, max-age=0',
  'Pragma': 'no-cache',
  'X-Content-Type-Options': 'nosniff'
};
const response = (status: number, body: Record<string, unknown>) =>
  new Response(JSON.stringify(body), { status, headers: HEADERS });

function validAnswers(answers: unknown): answers is Record<string, string> {
  if (!answers || typeof answers !== 'object' || Array.isArray(answers)) return false;
  const list = Object.entries(answers);
  if (list.length !== 40) return false;
  const seen = new Set<string>();
  for (const [id, value] of list) {
    if (!/^q(0[1-9]|[1-3][0-9]|40)$/.test(id) ||
        seen.has(id) || typeof value !== 'string' || !VALUES.has(value)) return false;
    seen.add(id);
  }
  return true;
}
async function participantHash(userId: string): Promise<string> {
  const secret = Deno.env.get('NOVA40_SURVEY_PEPPER') || '';
  if (secret.length < 32) throw new Error('SURVEY_SECRET_MISSING');
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const digest = await crypto.subtle.sign('HMAC', key,
    new TextEncoder().encode(SURVEY_ID + ':' + userId));
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
}

Deno.serve(async req => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return response(405, { ok: false, code: 'METHOD_NOT_ALLOWED' });
  if (req.headers.get('origin') !== ORIGIN) {
    return response(403, { ok: false, code: 'ORIGIN_NOT_ALLOWED' });
  }
  const declaredSize = req.headers.get('content-length');
  if (declaredSize !== null &&
      (!/^[0-9]+$/.test(declaredSize) || Number(declaredSize) > MAX_REQUEST_BYTES)) {
    return response(413, { ok: false, code: 'REQUEST_TOO_LARGE' });
  }
  const contentType = (req.headers.get('content-type') || '').toLowerCase();
  if (!(contentType === 'application/json' || contentType.startsWith('application/json;'))) {
    return response(415, { ok: false, code: 'INVALID_CONTENT_TYPE' });
  }
  try {
    const user = await requiredUser(req);
    if (Deno.env.get('NOVA40_COLLECTION_ENABLED') !== 'true') {
      return response(503, { ok: false, code: 'COLLECTION_NOT_ENABLED' });
    }
    let parsed: unknown;
    try { parsed = await readBoundedJson(req); } catch (error) {
      if (error instanceof Error && error.message === 'REQUEST_TOO_LARGE') {
        return response(413, { ok: false, code: 'REQUEST_TOO_LARGE' });
      }
      return response(400, { ok: false, code: 'INVALID_JSON' });
    }
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return response(400, { ok: false, code: 'INCOMPLETE_OR_INELIGIBLE' });
    }
    const body = parsed as Record<string, unknown>;
    if (!body || typeof body !== 'object' || Array.isArray(body) ||
        body.survey !== SURVEY_ID || body.age18Confirmed !== true ||
        body.explicitConsent !== true || !validAnswers(body.answers)) {
      return response(400, { ok: false, code: 'INCOMPLETE_OR_INELIGIBLE' });
    }
    const service = serviceClient();
    const hash = await participantHash(user.id);
    const { data, error } = await service.rpc('nova_consultation40_submit_v1', {
      p_survey_version: SURVEY_ID,
      p_participant_hash: hash,
      p_answers: body.answers
    });
    if (error?.code === '23505' && error.message.includes('ALREADY_SUBMITTED')) {
      return response(409, { ok: false, code: 'ALREADY_SUBMITTED' });
    }
    if (error || data !== 'RECORDED') {
      return response(500, { ok: false, code: 'SERVER_UNAVAILABLE' });
    }
    return response(201, { ok: true, code: 'RECORDED', survey: SURVEY_ID });
  } catch {
    // Ne pas journaliser les réponses, l'UID ou le jeton HMAC.
    return response(401, { ok: false, code: 'AUTH_OR_SERVICE_UNAVAILABLE' });
  }
});
