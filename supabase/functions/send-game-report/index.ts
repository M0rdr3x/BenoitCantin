import { PDFDocument, StandardFonts } from 'npm:pdf-lib@1.17.1';
import { corsHeaders, json } from '../_shared/cors.ts';
import { optionalUser, serviceClient } from '../_shared/auth.ts';

const FUNCTION_VERSION='24.5.2';
const MAX_REQUEST_BYTES=220_000;
// Intégration préparée, jamais activée implicitement. Une future activation exige
// une décision explicite distincte sur le fournisseur et les coûts.
const PAID_EXTERNAL_SERVICES_ENABLED=false;
const TEMPLATE_URL =
  Deno.env.get('REPORT_TEMPLATE_URL') ||
  'https://www.benoitcantin.com/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fracture_du_Reseau_Mere_Fiche_Joueur_Web.pdf';

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
  const response = await fetch(TEMPLATE_URL, { cache: 'no-store' });
  if (!response.ok) throw new Error('Impossible de charger le modèle PDF.');
  const bytes = new Uint8Array(await response.arrayBuffer());
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
  if (req.method !== 'POST') return json({ ok: false, error: 'Méthode non autorisée.', function_version: FUNCTION_VERSION }, 405);

  const declaredLength=Number(req.headers.get('content-length')||0);
  if(declaredLength>MAX_REQUEST_BYTES){
    return json({ok:false,error:'Requête trop volumineuse.',function_version:FUNCTION_VERSION},413);
  }

  try {
    const body = await req.json();
    const mode = body?.mode === 'email' ? 'email' : 'download';
    const user = await optionalUser(req);
    const sheet = sanitizeSheet(body?.sheet_data || {});
    const pdfBytes = await buildPdf(sheet);
    const filename = `SINJIRA_Fracture_Rapport_${new Date().toISOString().slice(0, 10)}.pdf`;

    if (mode === 'download') {
      if (user) await recordDelivery(user.id, body?.session_id, 'download');
      return json({ ok: true, filename, pdf_base64: toBase64(pdfBytes), function_version: FUNCTION_VERSION });
    }

    if (!PAID_EXTERNAL_SERVICES_ENABLED) {
      return json({ ok:false, error:'Le transport courriel externe est préparé mais désactivé. Téléchargez le PDF directement.', code:'PAID_EXTERNAL_SERVICE_DISABLED', function_version:FUNCTION_VERSION }, 503);
    }

    // L'envoi de courriel est réservé à un compte authentifié et uniquement à son adresse.
    // Cette règle empêche la fonction publique de devenir un relais de spam.
    if (!user?.email) {
      return json({ ok: false, error: 'Connexion requise pour l’envoi par courriel.', function_version: FUNCTION_VERSION }, 401);
    }

    const resendKey = Deno.env.get('RESEND_API_KEY');
    const from = Deno.env.get('REPORT_FROM_EMAIL') || 'SINJIRA <no-reply@benoitcantin.com>';
    if (!resendKey) return json({ ok: false, error: 'Service courriel non configuré.', function_version: FUNCTION_VERSION }, 503);

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
      return json({ ok: false, error: 'Le courriel n’a pas pu être envoyé.', function_version: FUNCTION_VERSION }, 502);
    }

    await recordDelivery(user.id, body?.session_id, 'email');
    return json({ ok: true, emailed: true, function_version: FUNCTION_VERSION });
  } catch (error) {
    console.error(error);
    return json({ ok: false, error: 'Erreur lors de la génération du rapport.', function_version: FUNCTION_VERSION }, 500);
  }
});
