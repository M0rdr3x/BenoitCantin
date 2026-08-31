import { PDFDocument, StandardFonts } from 'npm:pdf-lib@1.17.1';
import { corsHeaders } from '../_shared/cors.ts';
import { optionalUser, serviceClient } from '../_shared/auth.ts';

const FUNCTION_VERSION='24.5.2';
const MAX_REQUEST_BYTES=220_000;
const MAX_TEMPLATE_BYTES=15*1024*1024;
const TEMPLATE_FETCH_TIMEOUT_MS=10_000;
// Intégration préparée, jamais activée implicitement. Une future activation exige
// une décision explicite distincte sur le fournisseur et les coûts.
const PAID_EXTERNAL_SERVICES_ENABLED=false;
const DEFAULT_TEMPLATE_URL='https://www.benoitcantin.com/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fracture_du_Reseau_Mere_Fiche_Joueur_Web.pdf';
const TEMPLATE_ORIGIN='https://www.benoitcantin.com';
const TEMPLATE_PATH_PREFIX='/projets/sinjira/jeux/fracture-du-reseau-mere/documents/';

const PRIVATE_JSON_HEADERS = {
  ...corsHeaders,
  'Content-Type': 'application/json; charset=utf-8',
  'Cache-Control': 'private, no-store, max-age=0',
  'Pragma': 'no-cache',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer'
};

function privateJson(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: PRIVATE_JSON_HEADERS });
}

function reportTemplateUrl(){
  const raw=String(Deno.env.get('REPORT_TEMPLATE_URL')||DEFAULT_TEMPLATE_URL).trim();
  let url:URL;
  try{url=new URL(raw)}catch{throw new Error('REPORT_TEMPLATE_URL_INVALID')}
  if(
    url.protocol!=='https:' ||
    url.origin!==TEMPLATE_ORIGIN ||
    !url.pathname.startsWith(TEMPLATE_PATH_PREFIX) ||
    !url.pathname.toLowerCase().endsWith('.pdf') ||
    url.username || url.password || url.search || url.hash
  ) throw new Error('REPORT_TEMPLATE_URL_NOT_ALLOWED');
  return url.toString();
}

async function readTemplateStreamLimited(response:Response){
  if(!response.body)throw new Error('REPORT_TEMPLATE_EMPTY');
  const reader=response.body.getReader();
  const chunks:Uint8Array[]=[];
  let total=0;
  try{
    while(true){
      const {done,value}=await reader.read();
      if(done)break;
      if(!value)continue;
      total+=value.byteLength;
      if(total>MAX_TEMPLATE_BYTES){
        try{await reader.cancel('REPORT_TEMPLATE_TOO_LARGE')}catch{/* non bloquant */}
        throw new Error('REPORT_TEMPLATE_TOO_LARGE');
      }
      chunks.push(value);
    }
  }finally{
    try{reader.releaseLock()}catch{/* non bloquant */}
  }
  if(total===0)throw new Error('REPORT_TEMPLATE_EMPTY');
  const bytes=new Uint8Array(total);
  let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength}
  return bytes;
}

async function fetchTemplateBytes(){
  const response=await fetch(reportTemplateUrl(),{
    cache:'no-store',
    redirect:'error',
    signal:AbortSignal.timeout(TEMPLATE_FETCH_TIMEOUT_MS)
  });
  if(!response.ok)throw new Error('REPORT_TEMPLATE_FETCH_FAILED');
  const declared=Number(response.headers.get('content-length')||'0');
  if(Number.isFinite(declared)&&declared>MAX_TEMPLATE_BYTES)throw new Error('REPORT_TEMPLATE_TOO_LARGE');
  const bytes=await readTemplateStreamLimited(response);
  if(bytes.length<5||String.fromCharCode(...bytes.subarray(0,5))!=='%PDF-')throw new Error('REPORT_TEMPLATE_NOT_PDF');
  return bytes;
}

async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }> {
  const rawLength = req.headers.get('content-length');
  if (rawLength) {
    const declaredLength = Number(rawLength);
    if (!Number.isFinite(declaredLength) || declaredLength < 0 || declaredLength > MAX_REQUEST_BYTES) {
      return { response: privateJson({ ok:false, error:'Requête trop volumineuse.', function_version:FUNCTION_VERSION }, 413) };
    }
  }

  const raw = await req.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_REQUEST_BYTES) {
    return { response: privateJson({ ok:false, error:'Requête trop volumineuse.', function_version:FUNCTION_VERSION }, 413) };
  }

  try {
    return { body: JSON.parse(raw || '{}') };
  } catch {
    return { response: privateJson({ ok:false, error:'Corps JSON invalide.', function_version:FUNCTION_VERSION }, 400) };
  }
}

const MAX_TEXT = 6000;
const CHECKBOXES = new Set([
  ...Array.from({ length: 10 }, (_, index) => `ronde_${index + 1}_preuve`),
  'preuve_unique_confirmee'
]);

const TEXT_FIELDS = new Set([
  'nom_pseudo', 'numero_joueur', 'code_partie', 'identite_finale',
  ...Array.from({ length: 10 }, (_, index) => {
    const n = index + 1;
    return [
      `ronde_${n}_carte_a`,
      `ronde_${n}_carte_b`,
      `ronde_${n}_rapport`,
      `ronde_${n}_soupcon`
    ];
  }).flat(),
  ...Array.from({ length: 7 }, (_, index) => `accusation_${index + 1}`),
  'notes_privees',
  'resultat_camp'
]);

function sanitizeSheet(input: Record<string, unknown>) {
  const output: Record<string, string | boolean> = {};
  for (const name of TEXT_FIELDS) {
    output[name] = String(input?.[name] ?? '').slice(0, MAX_TEXT);
  }
  for (const name of CHECKBOXES) {
    output[name] = Boolean(input?.[name]);
  }
  return output;
}

function toBase64(bytes: Uint8Array) {
  let binary = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

async function buildPdf(sheet: Record<string, string | boolean>) {
  const bytes = await fetchTemplateBytes();
  const pdf = await PDFDocument.load(bytes);
  const form = pdf.getForm();
  const font = await pdf.embedFont(StandardFonts.Helvetica);

  for (const [name, value] of Object.entries(sheet)) {
    try {
      if (CHECKBOXES.has(name)) {
        const checkbox = form.getCheckBox(name);
        value ? checkbox.check() : checkbox.uncheck();
      } else {
        form.getTextField(name).setText(String(value ?? ''));
      }
    } catch {
      // Un champ absent dans une future version du PDF ne doit pas bloquer le rapport.
    }
  }

  try {
    form.updateFieldAppearances(font);
  } catch {
    // Certaines versions de lecteurs gèrent les apparences elles-mêmes.
  }

  return await pdf.save();
}

async function recordDelivery(userId: string, sessionId: unknown, delivery: 'download' | 'email') {
  if (!sessionId) return;
  const service = serviceClient();
  const { data: ownedSession } = await service
    .from('game_sessions')
    .select('id')
    .eq('id', String(sessionId))
    .eq('user_id', userId)
    .maybeSingle();
  if (!ownedSession?.id) return;
  const { error } = await service.from('player_reports').insert({
    user_id: userId,
    session_id: ownedSession.id,
    delivery
  });
  if (error) console.warn('[SINJIRA report] journalisation non bloquante:', error.message);
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return privateJson({ ok: false, error: 'Méthode non autorisée.', function_version: FUNCTION_VERSION }, 405);

  try {
    const parsed = await readLimitedJson(req);
    if (parsed.response) return parsed.response;
    const body = parsed.body || {};
    const mode = body?.mode === 'email' ? 'email' : 'download';
    const user = await optionalUser(req);
    const sheet = sanitizeSheet(body?.sheet_data || {});
    const pdfBytes = await buildPdf(sheet);
    const filename = `SINJIRA_Fracture_Rapport_${new Date().toISOString().slice(0, 10)}.pdf`;

    if (mode === 'download') {
      if (user) await recordDelivery(user.id, body?.session_id, 'download');
      return privateJson({ ok: true, filename, pdf_base64: toBase64(pdfBytes), function_version: FUNCTION_VERSION });
    }

    if (!PAID_EXTERNAL_SERVICES_ENABLED) {
      return privateJson({ ok:false, error:'Le transport courriel externe est préparé mais désactivé. Téléchargez le PDF directement.', code:'PAID_EXTERNAL_SERVICE_DISABLED', function_version:FUNCTION_VERSION }, 503);
    }

    // L'envoi de courriel est réservé à un compte authentifié et uniquement à son adresse.
    // Cette règle empêche la fonction publique de devenir un relais de spam.
    if (!user?.email) {
      return privateJson({ ok: false, error: 'Connexion requise pour l’envoi par courriel.', function_version: FUNCTION_VERSION }, 401);
    }

    const resendKey = Deno.env.get('RESEND_API_KEY');
    const from = Deno.env.get('REPORT_FROM_EMAIL') || 'SINJIRA <no-reply@benoitcantin.com>';
    if (!resendKey) return privateJson({ ok: false, error: 'Service courriel non configuré.', function_version: FUNCTION_VERSION }, 503);

    const resendResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${resendKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from,
        to: [user.email],
        subject: 'SINJIRA — Rapport de fin de partie — Fracture du Réseau-Mère',
        html: `
          <div style="font-family:Arial,sans-serif;max-width:640px;margin:auto">
            <h1>SINJIRA</h1>
            <h2>Fracture du Réseau-Mère</h2>
            <p>Voici la copie de votre fiche joueur telle qu’elle a été générée au moment de votre demande.</p>
            <p>— SINJIRA</p>
          </div>`,
        attachments: [{ filename, content: toBase64(pdfBytes) }]
      })
    });

    if (!resendResponse.ok) {
      const details = await resendResponse.text();
      console.error('Resend:', details);
      return privateJson({ ok: false, error: 'Le courriel n’a pas pu être envoyé.', function_version: FUNCTION_VERSION }, 502);
    }

    await recordDelivery(user.id, body?.session_id, 'email');
    return privateJson({ ok: true, emailed: true, function_version: FUNCTION_VERSION });
  } catch (error) {
    console.error(error);
    return privateJson({ ok: false, error: 'Erreur lors de la génération du rapport.', function_version: FUNCTION_VERSION }, 500);
  }
});
