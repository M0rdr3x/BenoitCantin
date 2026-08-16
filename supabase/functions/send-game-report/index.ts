import { PDFDocument, StandardFonts } from 'npm:pdf-lib@1.17.1';
import { corsHeaders, json } from '../_shared/cors.ts';
import { optionalUser, serviceClient } from '../_shared/auth.ts';

const TEMPLATE_URL = Deno.env.get('REPORT_TEMPLATE_URL') || 'https://www.benoitcantin.com/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fracture_du_Reseau_Mere_Fiche_Joueur_Web.pdf';
const MAX_TEXT = 6000;
const MAX_REQUEST_BYTES = 160_000;
let templatePromise: Promise<Uint8Array> | null = null;

const CHECKBOXES = new Set([
  ...Array.from({ length: 10 }, (_, index) => `ronde_${index + 1}_preuve`),
  'preuve_unique_confirmee'
]);
const TEXT_FIELDS = new Set([
  'nom_pseudo', 'numero_joueur', 'code_partie', 'identite_finale',
  ...Array.from({ length: 10 }, (_, index) => {
    const n = index + 1;
    return [`ronde_${n}_carte_a`,`ronde_${n}_carte_b`,`ronde_${n}_rapport`,`ronde_${n}_soupcon`];
  }).flat(),
  ...Array.from({ length: 7 }, (_, index) => `accusation_${index + 1}`),
  'notes_privees','resultat_camp'
]);

function sanitizeSheet(input: Record<string, unknown>) {
  const output: Record<string, string | boolean> = {};
  for (const name of TEXT_FIELDS) output[name] = String(input?.[name] ?? '').slice(0, MAX_TEXT);
  for (const name of CHECKBOXES) output[name] = Boolean(input?.[name]);
  return output;
}

async function readJsonLimited(req: Request) {
  const declared = Number(req.headers.get('content-length') || 0);
  if (Number.isFinite(declared) && declared > MAX_REQUEST_BYTES) throw new Error('PAYLOAD_TOO_LARGE');
  if (!req.body) return {};
  const reader = req.body.getReader(), chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    if (!value) continue;
    total += value.byteLength;
    if (total > MAX_REQUEST_BYTES) {
      await reader.cancel('payload too large').catch(() => {});
      throw new Error('PAYLOAD_TOO_LARGE');
    }
    chunks.push(value);
  }
  const merged = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { merged.set(chunk, offset); offset += chunk.byteLength; }
  const text = new TextDecoder().decode(merged);
  try { return text ? JSON.parse(text) : {}; } catch { throw new Error('INVALID_JSON'); }
}

function toBase64(bytes: Uint8Array) {
  let binary = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  return btoa(binary);
}

async function templateBytes() {
  if (!templatePromise) {
    templatePromise = (async () => {
      const response = await fetch(TEMPLATE_URL, { cache: 'no-store', signal: AbortSignal.timeout(10_000) });
      if (!response.ok) throw new Error('TEMPLATE_UNAVAILABLE');
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (bytes.byteLength < 1000 || bytes.byteLength > 15 * 1024 * 1024) throw new Error('TEMPLATE_INVALID_SIZE');
      return bytes;
    })();
  }
  try { return await templatePromise; }
  catch (error) { templatePromise = null; throw error; }
}

async function buildPdf(sheet: Record<string, string | boolean>) {
  const bytes = await templateBytes();
  const pdf = await PDFDocument.load(bytes);
  const form = pdf.getForm();
  const font = await pdf.embedFont(StandardFonts.Helvetica);
  for (const [name, value] of Object.entries(sheet)) {
    try {
      if (CHECKBOXES.has(name)) {
        const checkbox = form.getCheckBox(name);
        value ? checkbox.check() : checkbox.uncheck();
      } else form.getTextField(name).setText(String(value ?? ''));
    } catch {
      // Un champ absent dans une future version du PDF ne doit pas bloquer le rapport.
    }
  }
  try { form.updateFieldAppearances(font); } catch { /* lecteurs PDF compatibles */ }
  return await pdf.save();
}

async function recordDelivery(userId: string, sessionId: unknown, delivery: 'download' | 'email') {
  if (!sessionId) return;
  const service = serviceClient();
  const { data: ownedSession } = await service.from('game_sessions').select('id').eq('id', String(sessionId)).eq('user_id', userId).maybeSingle();
  if (!ownedSession?.id) return;
  const { error } = await service.from('player_reports').insert({ user_id: userId, session_id: ownedSession.id, delivery });
  if (error) console.warn('[SINJIRA report] journalisation non bloquante:', error.message);
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ ok: false, error: 'Méthode non autorisée.' }, 405);
  try {
    const body = await readJsonLimited(req);
    const mode = body?.mode === 'email' ? 'email' : 'download';
    const user = await optionalUser(req);
    const sheet = sanitizeSheet(body?.sheet_data || {});
    const pdfBytes = await buildPdf(sheet);
    const filename = `SINJIRA_Fracture_Rapport_${new Date().toISOString().slice(0, 10)}.pdf`;

    if (mode === 'download') {
      if (user) await recordDelivery(user.id, body?.session_id, 'download');
      return json({ ok: true, filename, pdf_base64: toBase64(pdfBytes) });
    }

    if (!user?.email) return json({ ok: false, error: 'Connexion requise pour l’envoi par courriel.' }, 401);
    const resendKey = Deno.env.get('RESEND_API_KEY');
    const from = Deno.env.get('REPORT_FROM_EMAIL') || 'SINJIRA <no-reply@benoitcantin.com>';
    if (!resendKey) return json({ ok: false, error: 'Service courriel non configuré.' }, 503);

    const resendResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      signal: AbortSignal.timeout(12_000),
      headers: { 'Authorization': `Bearer ${resendKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from, to: [user.email],
        subject: 'SINJIRA — Rapport de fin de partie — Fracture du Réseau-Mère',
        html: '<div style="font-family:Arial,sans-serif;max-width:640px;margin:auto"><h1>SINJIRA</h1><h2>Fracture du Réseau-Mère</h2><p>Voici la copie de votre fiche joueur telle qu’elle a été générée au moment de votre demande.</p><p>— SINJIRA</p></div>',
        attachments: [{ filename, content: toBase64(pdfBytes) }]
      })
    });
    if (!resendResponse.ok) {
      console.error('Resend status:', resendResponse.status);
      return json({ ok: false, error: 'Le courriel n’a pas pu être envoyé.' }, 502);
    }
    await recordDelivery(user.id, body?.session_id, 'email');
    return json({ ok: true, emailed: true });
  } catch (error) {
    console.error('[SINJIRA report]', error);
    if (error?.message === 'PAYLOAD_TOO_LARGE') return json({ ok: false, error: 'La demande de rapport est trop volumineuse.' }, 413);
    if (error?.message === 'INVALID_JSON') return json({ ok: false, error: 'Demande de rapport invalide.' }, 400);
    return json({ ok: false, error: 'Erreur lors de la génération du rapport.' }, 500);
  }
});
