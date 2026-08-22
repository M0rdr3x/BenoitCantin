import { getSupabase, requireUser, friendlyBackendMessage } from './sinjira-supabase.js';

const statusNode = document.querySelector('[data-life-story-posthumous-status]');
const panel = document.querySelector('[data-life-story-posthumous-case]');
const contestForm = document.querySelector('[data-life-story-contest-form]');
const fmt = new Intl.DateTimeFormat('fr-CA', { dateStyle: 'long', timeStyle: 'short' });
const s = getSupabase();

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
  const { data, error } = await s.rpc('life_story_my_posthumous_case');
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

function installReportCodesPanel() {
  if (document.querySelector('[data-life-story-report-codes]')) return;
  const anchor = panel?.closest('.section');
  if (!anchor) return;
  const section = document.createElement('section');
  section.className = 'section section-tight';
  section.dataset.lifeStoryReportCodes = '';
  section.innerHTML = `<div class="account-shell"><div class="life-story-grid"><article class="account-card"><span class="eyebrow">Proche de confiance</span><h2>Code privé de signalement de décès</h2><p>Vous pouvez créer jusqu’à cinq codes et en remettre un à une personne de confiance. Le code brut est affiché une seule fois; SINJIRA n’en conserve que le hash.</p><form class="account-form" data-report-code-form><div class="field"><label for="report-code-label">À qui ou pour quel usage ?</label><input id="report-code-label" name="label" maxlength="160" placeholder="Ex. Ma sœur — signalement uniquement" required/></div><button class="btn btn-secondary" type="submit">Créer un code privé</button></form><div class="life-story-notice" data-report-code-once hidden></div></article><article class="account-card"><h2>Mes codes</h2><div data-report-code-list><p>Chargement…</p></div><p><small>Un code utilisé ou révoqué ne peut plus initier un nouveau signalement.</small></p><a class="btn btn-secondary" href="/compte/signaler-deces.html">J’ai reçu un code et je dois signaler un décès</a></article></div></div>`;
  anchor.insertAdjacentElement('beforebegin', section);
  section.querySelector('[data-report-code-form]')?.addEventListener('submit', createReportCode);
  section.querySelector('[data-report-code-list]')?.addEventListener('click', revokeReportCode);
}

async function loadReportCodes() {
  installReportCodesPanel();
  const list = document.querySelector('[data-report-code-list]');
  if (!list) return;
  const { data, error } = await s.rpc('life_story_list_report_codes');
  if (error) throw error;
  const rows = Array.isArray(data) ? data : [];
  if (!rows.length) { list.innerHTML = '<p>Aucun code créé.</p>'; return; }
  list.innerHTML = '';
  for (const row of rows) {
    const card = document.createElement('article');
    card.className = 'life-story-item';
    const title = document.createElement('strong'); title.textContent = row.label || 'Code privé';
    const meta = document.createElement('p'); meta.textContent = `${row.status === 'active' ? 'Actif' : row.status === 'used' ? 'Utilisé' : 'Révoqué'} · créé ${dateTime(row.created_at)}`;
    card.append(title, meta);
    if (row.status === 'active') {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'btn btn-secondary'; button.dataset.revokeReportCode = row.id; button.textContent = 'Révoquer ce code'; card.append(button);
    }
    list.append(card);
  }
}

async function createReportCode(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const label = String(new FormData(form).get('label') || '').trim();
  if (!label) return;
  const button = form.querySelector('button[type="submit"]'); if (button) button.disabled = true;
  try {
    const { data, error } = await s.rpc('life_story_create_report_code', { p_label: label });
    if (error) throw error;
    form.reset();
    const once = document.querySelector('[data-report-code-once]');
    if (once) {
      once.hidden = false; once.innerHTML = '';
      const strong = document.createElement('strong'); strong.textContent = 'Copiez ce code maintenant — SINJIRA ne pourra pas l’afficher de nouveau.';
      const input = document.createElement('input'); input.readOnly = true; input.value = String(data?.code || ''); input.setAttribute('aria-label', 'Code privé de signalement');
      const copy = document.createElement('button'); copy.type = 'button'; copy.className = 'btn btn-primary'; copy.textContent = 'Copier le code';
      copy.addEventListener('click', async () => { try { await navigator.clipboard.writeText(input.value); copy.textContent = 'Copié'; } catch { input.select(); } });
      once.append(strong, input, copy);
    }
    await loadReportCodes();
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Le code n’a pas pu être créé.'), 'error');
  } finally { if (button) button.disabled = false; }
}

async function revokeReportCode(event) {
  const button = event.target.closest('[data-revoke-report-code]');
  if (!button) return;
  if (!confirm('Révoquer ce code ? Il ne pourra plus servir à signaler un décès.')) return;
  button.disabled = true;
  try {
    const { error } = await s.rpc('life_story_revoke_report_code', { p_code_id: button.dataset.revokeReportCode });
    if (error) throw error;
    await loadReportCodes();
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Le code n’a pas pu être révoqué.'), 'error');
    button.disabled = false;
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
    const { error } = await s.rpc('life_story_contest_death_verification', { p_case_id: caseId, p_reason: reason });
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

Promise.all([loadCase(), loadReportCodes()]).catch((error) => showStatus(friendlyBackendMessage(error?.message, 'La protection posthume est temporairement indisponible.'), 'error'));
