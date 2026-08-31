import { PDFDocument, StandardFonts } from 'npm:pdf-lib@1.17.1';
import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser } from '../_shared/auth.ts';

const FUNCTION_VERSION = '24.5.49';
const MAX_REQUEST_BYTES = 160_000;
const PAID_EXTERNAL_SERVICES_ENABLED = false;

async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }> {
  const rawLength = req.headers.get('content-length');
  if (rawLength) {
    const declaredLength = Number(rawLength);
    if (!Number.isFinite(declaredLength) || declaredLength < 0 || declaredLength > MAX_REQUEST_BYTES) {
      return { response: json({ ok: false, error: 'Requête trop volumineuse.', function_version: FUNCTION_VERSION }, 413) };
    }
  }

  const raw = await req.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_REQUEST_BYTES) {
    return { response: json({ ok: false, error: 'Requête trop volumineuse.', function_version: FUNCTION_VERSION }, 413) };
  }

  try {
    return { body: JSON.parse(raw || '{}') };
  } catch {
    return { response: json({ ok: false, error: 'Corps JSON invalide.', function_version: FUNCTION_VERSION }, 400) };
  }
}

function base64(bytes: Uint8Array) {
  let binary = '';
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(binary);
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ ok: false, error: 'Méthode non autorisée.', function_version: FUNCTION_VERSION }, 405);

  try {
    const user = await requiredUser(req);
    if (!user?.email) return json({ ok: false, error: 'Connexion requise.', function_version: FUNCTION_VERSION }, 401);

    // Préparé uniquement. Aucun transport externe payant n'est activé implicitement.
    if (!PAID_EXTERNAL_SERVICES_ENABLED) {
      return json({
        ok: false,
        error: 'Le transport courriel externe est préparé mais désactivé.',
        code: 'PAID_EXTERNAL_SERVICE_DISABLED',
        function_version: FUNCTION_VERSION
      }, 503);
    }

    const parsed = await readLimitedJson(req);
    if (parsed.response) return parsed.response;
    const body = parsed.body || {};
    const mode = body?.mode === 'solo' ? 'solo' : 'standard';
    const fields = body?.fields && typeof body.fields === 'object' ? body.fields : {};
    const site = 'https://www.benoitcantin.com/projets/sinjira/jeux/fracture-du-reseau-mere/documents/';
    const template = mode === 'solo'
      ? `${site}SINJIRA_Mode_Solo_3_Joueurs_Interactive.pdf`
      : `${site}SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf`;

    const res = await fetch(template, { cache: 'no-store' });
    if (!res.ok) return json({ ok: false, error: 'Le modèle PDF n’est pas encore disponible sur le site.', function_version: FUNCTION_VERSION }, 503);

    const pdf = await PDFDocument.load(new Uint8Array(await res.arrayBuffer()));
    const form = pdf.getForm();
    for (const [name, value] of Object.entries(fields)) {
      if (['session_title', 'party_code', 'player_label'].includes(name)) continue;
      try {
        form.getTextField(name).setText(String(value ?? '').slice(0, 6000));
      } catch {
        // Un champ inconnu n'empêche pas la génération d'une future version du modèle.
      }
    }
    try {
      const font = await pdf.embedFont(StandardFonts.Helvetica);
      form.updateFieldAppearances(font);
    } catch {
      // Les lecteurs PDF peuvent recalculer les apparences.
    }

    const bytes = await pdf.save();
    const key = Deno.env.get('RESEND_API_KEY');
    if (!key) return json({ ok: false, error: 'Le service courriel SINJIRA n’est pas configuré.', function_version: FUNCTION_VERSION }, 503);

    const from = Deno.env.get('REPORT_FROM_EMAIL') || 'SINJIRA <no-reply@benoitcantin.com>';
    const filename = mode === 'solo'
      ? 'SINJIRA_Fracture_Mode_Solo_3_Joueurs.pdf'
      : 'SINJIRA_Fracture_Fiche_Joueur.pdf';
    const sent = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from,
        to: [user.email],
        subject: mode === 'solo' ? 'SINJIRA - Fiche privée mode solo' : 'SINJIRA - Fiche joueur privée',
        html: '<p>Voici votre fiche privée de <strong>SINJIRA - Fracture du Réseau-Mère</strong>.</p><p>Cette fiche n’est pas utilisée dans les données d’équilibrage du jeu.</p>',
        attachments: [{ filename, content: base64(bytes) }]
      })
    });

    if (!sent.ok) {
      console.error('[send-player-sheet] transport externe refusé:', sent.status);
      return json({ ok: false, error: 'Le courriel n’a pas pu être envoyé.', function_version: FUNCTION_VERSION }, 502);
    }

    // Ne jamais réémettre l'adresse du compte dans la réponse API.
    return json({ ok: true, mode, function_version: FUNCTION_VERSION });
  } catch (error) {
    console.error('[send-player-sheet]', error);
    const code = String(error?.message || '');
    const status = code === 'AUTH_REQUIRED' ? 401 : 500;
    return json({ ok: false, error: status === 401 ? 'Connexion requise.' : 'Erreur lors de la préparation de la fiche.', function_version: FUNCTION_VERSION }, status);
  }
});
