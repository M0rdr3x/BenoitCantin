import { PDFDocument, StandardFonts, rgb } from 'npm:pdf-lib@1.17.1';
import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredAdmin } from '../_shared/auth.ts';

const FUNCTION_VERSION = '24.5.49';
const BUCKET = 'sinjira-life-story-exports';
const DAY = 24 * 60 * 60 * 1000;
const MAX_REQUEST_BYTES = 32_768;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ALLOWED_ACTIONS = new Set(['generate', 'create_delivery_links', 'revoke', 'purge']);
const SAFE_ERROR_CODES = new Set([
  'AUTH_REQUIRED',
  'ADMIN_REQUIRED',
  'MFA_REQUIRED',
  'MFA_STATE_UNAVAILABLE',
  'SOURCE_BOUNDARY_VIOLATION',
  'EXPORT_NOT_GENERATABLE',
  'EXPORT_NOT_GENERATED',
  'NO_RECIPIENTS'
]);

function safeText(value: unknown, max = 10000) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}
function printable(value: unknown) {
  return safeText(value, 20000)
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/™/g, 'TM')
    .replace(/…/g, '...')
    .replace(/[^\u0009\u000A\u000D\u0020-\u007E\u00A0-\u00FF]/g, '');
}
function hex(bytes: Uint8Array) { return [...bytes].map((b) => b.toString(16).padStart(2, '0')).join(''); }
async function sha256Hex(value: Uint8Array | string) {
  const bytes = typeof value === 'string' ? new TextEncoder().encode(value) : value;
  return hex(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)));
}
function assertLifeStoryBoundary(record: any) {
  const snapshot = record?.content_snapshot;
  if (
    record?.source_boundary !== 'life_story_only' ||
    record?.registry_access_prohibited !== true ||
    snapshot?.source_boundary !== 'life_story_only' ||
    snapshot?.registry_access_prohibited !== true
  ) {
    throw new Error('SOURCE_BOUNDARY_VIOLATION');
  }
}
function wrap(text: string, max = 88) {
  const words = printable(text).split(/\s+/).filter(Boolean);
  const lines: string[] = []; let line = '';
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (next.length > max && line) { lines.push(line); line = word; }
    else line = next;
  }
  if (line) lines.push(line);
  return lines.length ? lines : [''];
}

async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }> {
  const rawLength = req.headers.get('content-length');
  if (rawLength) {
    const declaredLength = Number(rawLength);
    if (!Number.isFinite(declaredLength) || declaredLength < 0 || declaredLength > MAX_REQUEST_BYTES) {
      return { response: json({ ok: false, error: 'Requête trop volumineuse.', code: 'REQUEST_TOO_LARGE', function_version: FUNCTION_VERSION }, 413) };
    }
  }
  const raw = await req.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_REQUEST_BYTES) {
    return { response: json({ ok: false, error: 'Requête trop volumineuse.', code: 'REQUEST_TOO_LARGE', function_version: FUNCTION_VERSION }, 413) };
  }
  try {
    return { body: JSON.parse(raw || '{}') };
  } catch {
    return { response: json({ ok: false, error: 'Corps JSON invalide.', code: 'INVALID_JSON', function_version: FUNCTION_VERSION }, 400) };
  }
}

async function buildPdf(snapshot: any) {
  const pdf = await PDFDocument.create();
  const regular = await pdf.embedFont(StandardFonts.Helvetica);
  const bold = await pdf.embedFont(StandardFonts.HelveticaBold);
  const pageSize: [number, number] = [595.28, 841.89];
  const margin = 54; let page = pdf.addPage(pageSize); let y = 785;
  const drawLine = (text: string, size = 10.5, font = regular, gap = 15) => {
    if (y < 70) { page = pdf.addPage(pageSize); y = 785; }
    page.drawText(printable(text), { x: margin, y, size, font, color: rgb(0.08, 0.1, 0.15), maxWidth: pageSize[0] - margin * 2 });
    y -= gap;
  };
  const paragraph = (text: string, size = 10.5) => { for (const line of wrap(text)) drawLine(line, size, regular, size + 4); y -= 5; };

  const version = snapshot?.version || {};
  drawLine(printable(version.title || version.name || 'Histoire de vie'), 20, bold, 28);
  drawLine(`Version: ${printable(version.audience || 'personnelle')}`, 10, bold, 18);
  paragraph('Document numérique SINJIRA. Cette oeuvre est construite uniquement à partir des éléments de l Histoire de vie explicitement autorisés par la personne. Le Registre des Consciences n est jamais une source de ce PDF.', 9.5);
  if (version.instructions) { drawLine('Intentions de la personne', 12, bold, 20); paragraph(version.instructions, 10); }
  const entries = Array.isArray(snapshot?.entries) ? snapshot.entries : [];
  for (const entry of entries) {
    y -= 6;
    drawLine(printable(entry.title || 'Souvenir'), 13, bold, 20);
    const meta = [entry.occurred_on ? `Date: ${entry.occurred_on}` : '', entry.knowledge_status ? `Nature: ${entry.knowledge_status}` : ''].filter(Boolean).join(' | ');
    if (meta) drawLine(meta, 8.5, regular, 14);
    paragraph(entry.body || '', 10.5);
  }
  y -= 8;
  drawLine('Repères de lecture', 11, bold, 18);
  paragraph('fait déclaré = information déclarée par la personne; réflexion = pensée ou interprétation personnelle; reconstruction = texte assisté ou reconstitué qui ne doit pas être présenté comme un fait certain.', 8.8);
  paragraph('SINJIRA ne transmet pas les secrets d une personne après sa mort. Elle transmet l histoire qu elle a choisi de laisser derrière elle.', 8.8);
  return new Uint8Array(await pdf.save());
}

function safeFailure(error: unknown) {
  const raw = String((error as any)?.message || '');
  const code = SAFE_ERROR_CODES.has(raw) ? raw : 'INTERNAL_ERROR';
  const status = raw === 'AUTH_REQUIRED'
    ? 401
    : raw === 'ADMIN_REQUIRED' || raw === 'MFA_REQUIRED'
      ? 403
      : raw === 'MFA_STATE_UNAVAILABLE'
        ? 503
        : SAFE_ERROR_CODES.has(raw)
          ? 400
          : 500;
  return { code, status };
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ ok: false, error: 'Méthode non autorisée.', function_version: FUNCTION_VERSION }, 405);
  try {
    const { service } = await requiredAdmin(req);
    const parsed = await readLimitedJson(req);
    if (parsed.response) return parsed.response;
    const body = parsed.body || {};
    const action = safeText(body?.action, 40);
    const exportId = safeText(body?.export_id, 80);
    if (!ALLOWED_ACTIONS.has(action)) return json({ ok: false, error: 'Action inconnue.', function_version: FUNCTION_VERSION }, 400);
    if (!UUID_RE.test(exportId)) return json({ ok: false, error: 'Export requis ou invalide.', function_version: FUNCTION_VERSION }, 400);

    if (action === 'generate') {
      const { data: record, error } = await service.rpc('admin_life_story_get_export', { p_export_id: exportId });
      if (error) throw error;
      if (!record || !['prepared', 'generated'].includes(record.status)) throw new Error('EXPORT_NOT_GENERATABLE');
      assertLifeStoryBoundary(record);
      if (record.status === 'generated' && record.storage_path) return json({ ok: true, export_id: exportId, status: 'generated', sha256: record.sha256, function_version: FUNCTION_VERSION });
      const bytes = await buildPdf(record.content_snapshot);
      const digest = await sha256Hex(bytes);
      const path = `${record.subject_user_id}/${record.case_id}/${exportId}.pdf`;
      const { error: uploadError } = await service.storage.from(BUCKET).upload(path, bytes, { contentType: 'application/pdf', upsert: true, cacheControl: '0' });
      if (uploadError) throw uploadError;
      const { error: markError } = await service.rpc('service_life_story_mark_export_generated', { p_export_id: exportId, p_storage_path: path, p_sha256: digest });
      if (markError) throw markError;
      return json({ ok: true, export_id: exportId, status: 'generated', sha256: digest, function_version: FUNCTION_VERSION });
    }

    if (action === 'create_delivery_links') {
      const { data: record, error } = await service.rpc('admin_life_story_get_export', { p_export_id: exportId });
      if (error) throw error;
      if (!record || record.status !== 'generated' || !record.storage_path) throw new Error('EXPORT_NOT_GENERATED');
      assertLifeStoryBoundary(record);
      const recipients = Array.isArray(record.recipients_snapshot) ? record.recipients_snapshot : [];
      if (!recipients.length) throw new Error('NO_RECIPIENTS');
      await service.from('life_story_delivery_links').delete().eq('export_id', exportId);
      const rows: any[] = []; const responseLinks: any[] = [];
      const base = `${Deno.env.get('SUPABASE_URL')}/functions/v1/life-story-delivery`;
      for (let i = 0; i < recipients.length; i += 1) {
        const raw = hex(crypto.getRandomValues(new Uint8Array(32)));
        const tokenHash = await sha256Hex(raw);
        const expiresAt = new Date(Date.now() + 30 * DAY).toISOString();
        rows.push({ export_id: exportId, recipient_index: i, recipient_label: safeText(recipients[i]?.recipient_label, 160) || `Destinataire ${i + 1}`, token_hash: tokenHash, expires_at: expiresAt, max_downloads: 3 });
        responseLinks.push({ recipient_label: safeText(recipients[i]?.recipient_label, 160), recipient_email: safeText(recipients[i]?.recipient_email, 254) || null, expires_at: expiresAt, download_url: `${base}?token=${encodeURIComponent(raw)}` });
      }
      const { error: insertError } = await service.from('life_story_delivery_links').insert(rows);
      if (insertError) throw insertError;
      return json({ ok: true, export_id: exportId, links: responseLinks, transport: 'manual_or_future_sender', note: 'Les liens sont retournés une seule fois. Aucun courriel externe n est envoyé automatiquement.', function_version: FUNCTION_VERSION });
    }

    if (action === 'revoke') {
      const { error } = await service.rpc('admin_life_story_revoke_export', { p_export_id: exportId });
      if (error) throw error;
      return json({ ok: true, export_id: exportId, status: 'revoked', function_version: FUNCTION_VERSION });
    }

    if (action === 'purge') {
      const { data: record, error } = await service.rpc('admin_life_story_get_purgeable_export', { p_export_id: exportId });
      if (error) throw error;
      if (record?.storage_path) {
        const { error: removeError } = await service.storage.from(BUCKET).remove([record.storage_path]);
        if (removeError) throw removeError;
      }
      const { error: markError } = await service.rpc('service_life_story_mark_export_purged', { p_export_id: exportId });
      if (markError) throw markError;
      return json({ ok: true, export_id: exportId, status: 'purged', function_version: FUNCTION_VERSION });
    }

    return json({ ok: false, error: 'Action inconnue.', function_version: FUNCTION_VERSION }, 400);
  } catch (error) {
    console.error('[life-story-export]', error);
    const { code, status } = safeFailure(error);
    return json({ ok: false, error: 'Opération Histoire de vie refusée.', code, function_version: FUNCTION_VERSION }, status);
  }
});
