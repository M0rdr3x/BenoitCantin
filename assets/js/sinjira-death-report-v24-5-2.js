import { getSupabase, requireUser, friendlyBackendMessage } from './sinjira-supabase.js';

const form = document.querySelector('[data-death-report-form]');
const statusNode = document.querySelector('[data-death-report-status]');
const s = getSupabase();

function showStatus(message, kind = '') {
  if (!statusNode) return;
  statusNode.hidden = false;
  statusNode.textContent = message;
  statusNode.dataset.kind = kind;
}

function normalizeCode(value) {
  return String(value || '').trim().toLowerCase();
}

async function boot() {
  await requireUser();
  if (!form) return;
  const dateInput = form.elements.date_of_death;
  if (dateInput) dateInput.max = new Date().toISOString().slice(0, 10);
}

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const code = normalizeCode(data.get('code'));
  const relationship = String(data.get('relationship_claim') || '').trim();
  const dateOfDeath = String(data.get('date_of_death') || '').trim();
  if (!/^[a-f0-9]{64}$/.test(code)) {
    showStatus('Le code privé doit contenir exactement 64 caractères hexadécimaux.', 'error');
    return;
  }
  if (relationship.length < 2 || !dateOfDeath) {
    showStatus('Indiquez la date déclarée du décès et votre lien avec la personne.', 'error');
    return;
  }
  if (!confirm('Envoyer ce signalement ? Il ouvrira une demande de vérification humaine, sans valider automatiquement le décès.')) return;
  const button = form.querySelector('button[type="submit"]');
  if (button) button.disabled = true;
  try {
    const { data: result, error } = await s.rpc('life_story_report_death_by_code', {
      p_code: code,
      p_relationship_claim: relationship,
      p_date_of_death: dateOfDeath
    });
    if (error) throw error;
    form.reset();
    showStatus(result?.message || 'Signalement reçu. Une vérification humaine est obligatoire avant toute opération posthume.', 'success');
  } catch (error) {
    const raw = String(error?.message || '');
    const known = {
      REPORT_CODE_INVALID: 'Ce code est invalide, révoqué ou déjà utilisé.',
      INVALID_DATE_OF_DEATH: 'La date du décès est invalide.',
      RELATIONSHIP_CLAIM_REQUIRED: 'Décrivez brièvement votre lien avec la personne.',
      SELF_DEATH_REPORT_FORBIDDEN: 'Vous ne pouvez pas utiliser votre propre code pour vous déclarer décédé.',
      REPORT_ALREADY_EXISTS: 'Un signalement est déjà en cours pour cette personne.'
    };
    const matched = Object.entries(known).find(([key]) => raw.includes(key));
    showStatus(matched ? matched[1] : friendlyBackendMessage(raw, 'Le signalement n’a pas pu être enregistré.'), 'error');
  } finally {
    if (button) button.disabled = false;
  }
});

boot().catch((error) => showStatus(friendlyBackendMessage(error?.message, 'Connexion requise pour envoyer un signalement.'), 'error'));
