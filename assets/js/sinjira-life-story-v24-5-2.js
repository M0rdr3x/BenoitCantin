import { getSupabase, requireUser, friendlyBackendMessage } from './sinjira-supabase.js';

const statusNode = document.querySelector('[data-life-story-posthumous-status]');
const panel = document.querySelector('[data-life-story-posthumous-case]');
const contestForm = document.querySelector('[data-life-story-contest-form]');
const fmt = new Intl.DateTimeFormat('fr-CA', { dateStyle: 'long', timeStyle: 'short' });

function showStatus(message, kind = '') {
  if (!statusNode) return;
  statusNode.hidden = false;
  statusNode.textContent = message;
  statusNode.dataset.kind = kind;
}
function dateTime(value) {
  if (!value) return '—';
  try { return fmt.format(new Date(value)); } catch { return '—'; }
}
function humanStatus(value) {
  return ({
    verified_hold: 'Décès vérifié — délai de sécurité en cours',
    contested: 'Vérification contestée — toute opération est suspendue',
    rejected: 'Vérification rejetée',
    ready_for_export: 'Deuxième validation humaine effectuée',
    closed_no_delivery: 'Dossier fermé sans remise',
    completed: 'Remise posthume terminée'
  })[value] || value || 'Aucun dossier';
}

async function loadCase() {
  await requireUser();
  const { data, error } = await getSupabase().rpc('life_story_my_posthumous_case');
  if (error) throw error;
  const current = data && Object.keys(data).length ? data : null;
  if (!panel) return;
  if (!current) {
    panel.innerHTML = '<strong>Aucune procédure posthume active.</strong><p>Aucune vérification de décès ne vous concerne actuellement.</p>';
    contestForm?.setAttribute('hidden', '');
    return;
  }
  panel.innerHTML = '';
  const title = document.createElement('strong');
  title.textContent = humanStatus(current.status);
  const details = document.createElement('p');
  details.textContent = `Date déclarée : ${current.date_of_death || '—'} · Première vérification : ${dateTime(current.first_verified_at)} · Fin du délai de sécurité : ${dateTime(current.hold_until)}.`;
  const guard = document.createElement('p');
  guard.textContent = current.open_contest
    ? 'Une contestation est ouverte. SINJIRA bloque la deuxième validation et toute génération.'
    : 'Aucun PDF ne peut être préparé avant la fin du délai et une deuxième validation humaine.';
  panel.append(title, details, guard);
  if (contestForm) {
    contestForm.hidden = !current.can_contest;
    contestForm.dataset.caseId = current.case_id || '';
  }
}

contestForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const caseId = contestForm.dataset.caseId || '';
  const reason = String(new FormData(contestForm).get('reason') || '').trim();
  if (!caseId || reason.length < 5) {
    showStatus('Expliquez brièvement pourquoi cette déclaration est incorrecte.', 'error');
    return;
  }
  if (!confirm('Contester cette vérification de décès ? Toute opération posthume sera immédiatement suspendue.')) return;
  const button = contestForm.querySelector('button[type="submit"]');
  if (button) button.disabled = true;
  try {
    const { error } = await getSupabase().rpc('life_story_contest_death_verification', { p_case_id: caseId, p_reason: reason });
    if (error) throw error;
    contestForm.reset();
    showStatus('Contestation enregistrée. La procédure posthume est suspendue jusqu’à révision humaine.', 'success');
    await loadCase();
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'La contestation n’a pas pu être enregistrée.'), 'error');
  } finally {
    if (button) button.disabled = false;
  }
});

loadCase().catch((error) => showStatus(friendlyBackendMessage(error?.message, 'Le statut posthume est temporairement indisponible.'), 'error'));
