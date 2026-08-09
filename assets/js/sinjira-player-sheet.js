import {
  getSupabase,
  getCurrentUser,
  formatDate,
  setStatus,
  isSinjiraBackendConfigured
} from './sinjira-supabase.js';

const GAME_SLUG = 'fracture-du-reseau-mere';
const FORM = document.querySelector('[data-player-sheet-form]');
const STATUS = document.querySelector('[data-sheet-status]');
const MODE = document.querySelector('[data-player-mode]');
const ACCOUNT_ACTIONS = document.querySelector('[data-account-actions]');
const GUEST_ACTIONS = document.querySelector('[data-guest-actions]');
const SESSION_BADGE = document.querySelector('[data-session-badge]');
const EMAIL_PANEL = document.querySelector('[data-email-panel]');
const EMAIL_INPUT = document.querySelector('[data-report-email]');
const EMAIL_CONSENT = document.querySelector('[data-report-email-consent]');

let user = null;
let currentSessionId = new URLSearchParams(location.search).get('session') || null;
let currentStatus = 'in_progress';
let dirty = false;

const TEXT_FIELDS = [
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
];

const CHECKBOX_FIELDS = [
  ...Array.from({ length: 10 }, (_, index) => `ronde_${index + 1}_preuve`),
  'preuve_unique_confirmee'
];

function buildRounds() {
  const body = document.querySelector('[data-rounds-body]');
  if (!body) return;
  body.innerHTML = Array.from({ length: 10 }, (_, index) => {
    const n = index + 1;
    return `
      <tr>
        <th scope="row">${n}</th>
        <td><input aria-label="Ronde ${n} carte A" name="ronde_${n}_carte_a" type="text" maxlength="160"></td>
        <td><input aria-label="Ronde ${n} carte B" name="ronde_${n}_carte_b" type="text" maxlength="160"></td>
        <td><input aria-label="Ronde ${n} rapport" name="ronde_${n}_rapport" type="text" maxlength="800"></td>
        <td class="center-cell"><input aria-label="Ronde ${n} preuve" name="ronde_${n}_preuve" type="checkbox" value="yes"></td>
        <td><input aria-label="Ronde ${n} soupçon" name="ronde_${n}_soupcon" type="text" maxlength="800"></td>
      </tr>
    `;
  }).join('');
}

function buildAccusations() {
  const wrap = document.querySelector('[data-accusations]');
  if (!wrap) return;
  wrap.innerHTML = Array.from({ length: 7 }, (_, index) => `
    <label class="compact-field">
      <span>${index + 1}</span>
      <input name="accusation_${index + 1}" type="text" maxlength="180" aria-label="Accusation finale ${index + 1}">
    </label>
  `).join('');
}

function collectSheetData() {
  const data = {};
  TEXT_FIELDS.forEach((name) => {
    data[name] = String(FORM.elements[name]?.value || '').trim();
  });
  CHECKBOX_FIELDS.forEach((name) => {
    data[name] = Boolean(FORM.elements[name]?.checked);
  });
  return data;
}

function applySheetData(data = {}) {
  TEXT_FIELDS.forEach((name) => {
    if (FORM.elements[name]) FORM.elements[name].value = data[name] ?? '';
  });
  CHECKBOX_FIELDS.forEach((name) => {
    if (FORM.elements[name]) FORM.elements[name].checked = Boolean(data[name]);
  });
}

function collectMeta() {
  return {
    player_count: Number(FORM.elements.player_count?.value || 0) || null,
    duration_minutes: Number(FORM.elements.duration_minutes?.value || 0) || null,
    title: String(FORM.elements.session_title?.value || '').trim() || 'Partie Fracture du Réseau-Mère'
  };
}

function collectFeedback() {
  return {
    rating: Number(FORM.elements.feedback_rating?.value || 0) || null,
    difficulty: String(FORM.elements.feedback_difficulty?.value || '').trim() || null,
    favorite_mechanic: String(FORM.elements.feedback_favorite?.value || '').trim() || null,
    unclear_text: String(FORM.elements.feedback_unclear?.value || '').trim() || null,
    extension_idea: String(FORM.elements.feedback_extension?.value || '').trim() || null
  };
}

function applyFeedback(data = {}) {
  if (FORM.elements.feedback_rating) FORM.elements.feedback_rating.value = data.rating ?? '';
  if (FORM.elements.feedback_difficulty) FORM.elements.feedback_difficulty.value = data.difficulty ?? '';
  if (FORM.elements.feedback_favorite) FORM.elements.feedback_favorite.value = data.favorite_mechanic ?? '';
  if (FORM.elements.feedback_unclear) FORM.elements.feedback_unclear.value = data.unclear_text ?? '';
  if (FORM.elements.feedback_extension) FORM.elements.feedback_extension.value = data.extension_idea ?? '';
}

function markDirty() {
  dirty = true;
  document.querySelector('[data-dirty-state]')?.replaceChildren(document.createTextNode('Modifications non sauvegardées'));
}

function markClean(message = 'À jour') {
  dirty = false;
  document.querySelector('[data-dirty-state]')?.replaceChildren(document.createTextNode(message));
}

function setMode() {
  if (user) {
    MODE.textContent = `Compte joueur · ${user.email}`;
    MODE.dataset.mode = 'account';
    ACCOUNT_ACTIONS.hidden = false;
    GUEST_ACTIONS.hidden = true;
    if (EMAIL_INPUT) {
      EMAIL_INPUT.value = user.email || '';
      EMAIL_INPUT.readOnly = true;
    }
  } else {
    MODE.textContent = 'Mode invité · aucune sauvegarde serveur';
    MODE.dataset.mode = 'guest';
    ACCOUNT_ACTIONS.hidden = true;
    GUEST_ACTIONS.hidden = false;
  }
}

async function loadSession() {
  if (!user || !currentSessionId) return;
  const supabase = getSupabase();

  const { data: session, error } = await supabase
    .from('game_sessions')
    .select('*')
    .eq('id', currentSessionId)
    .eq('user_id', user.id)
    .single();

  if (error) {
    setStatus(STATUS, 'Cette partie est introuvable ou ne vous appartient pas.', 'error');
    currentSessionId = null;
    return;
  }

  currentStatus = session.status;
  FORM.elements.session_title.value = session.title || '';
  FORM.elements.player_count.value = session.player_count || '';
  FORM.elements.duration_minutes.value = session.duration_minutes || '';
  SESSION_BADGE.textContent = session.status === 'finished' ? 'Partie terminée' : 'Partie sauvegardée';

  const [{ data: sheet }, { data: feedback }] = await Promise.all([
    supabase
      .from('player_sheets')
      .select('fields')
      .eq('session_id', currentSessionId)
      .eq('user_id', user.id)
      .maybeSingle(),
    supabase
      .from('session_feedback')
      .select('*')
      .eq('session_id', currentSessionId)
      .eq('user_id', user.id)
      .maybeSingle()
  ]);

  applySheetData(sheet?.fields || {});
  applyFeedback(feedback || {});
  markClean(`Dernière sauvegarde chargée · ${formatDate(session.updated_at)}`);
}

async function saveSession({ finish = false } = {}) {
  if (!user) {
    setStatus(STATUS, 'Créez un compte ou connectez-vous pour sauvegarder une partie.', 'error');
    return null;
  }

  const supabase = getSupabase();
  const meta = collectMeta();
  const sheetData = collectSheetData();
  const feedback = collectFeedback();
  const now = new Date().toISOString();

  if (!currentSessionId) {
    const { data: created, error } = await supabase
      .from('game_sessions')
      .insert({
        user_id: user.id,
        game_slug: GAME_SLUG,
        title: meta.title,
        status: finish ? 'finished' : 'in_progress',
        player_count: meta.player_count,
        duration_minutes: meta.duration_minutes,
        finished_at: finish ? now : null
      })
      .select('id')
      .single();

    if (error) {
      setStatus(STATUS, error.message, 'error');
      return null;
    }
    currentSessionId = created.id;
    history.replaceState({}, '', `${location.pathname}?session=${encodeURIComponent(currentSessionId)}`);
  } else {
    const update = {
      title: meta.title,
      status: finish ? 'finished' : currentStatus,
      player_count: meta.player_count,
      duration_minutes: meta.duration_minutes
    };
    if (finish) update.finished_at = now;

    const { error } = await supabase
      .from('game_sessions')
      .update(update)
      .eq('id', currentSessionId)
      .eq('user_id', user.id);

    if (error) {
      setStatus(STATUS, error.message, 'error');
      return null;
    }
  }

  const { error: sheetError } = await supabase
    .from('player_sheets')
    .upsert({
      session_id: currentSessionId,
      user_id: user.id,
      fields: sheetData
    }, { onConflict: 'session_id' });

  if (sheetError) {
    setStatus(STATUS, sheetError.message, 'error');
    return null;
  }

  const feedbackHasContent = Object.values(feedback).some((value) => value !== null && value !== '');
  if (feedbackHasContent) {
    const { error: feedbackError } = await supabase
      .from('session_feedback')
      .upsert({
        session_id: currentSessionId,
        user_id: user.id,
        ...feedback
      }, { onConflict: 'session_id' });

    if (feedbackError) {
      setStatus(STATUS, feedbackError.message, 'error');
      return null;
    }
  }

  currentStatus = finish ? 'finished' : currentStatus;
  SESSION_BADGE.textContent = finish ? 'Partie terminée' : 'Partie sauvegardée';
  markClean(`Sauvegardé · ${new Intl.DateTimeFormat('fr-CA', { timeStyle: 'short' }).format(new Date())}`);
  setStatus(STATUS, finish ? 'Partie terminée et sauvegardée dans votre compte.' : 'Partie sauvegardée.', 'success');
  return currentSessionId;
}

async function invokeReport(mode) {
  if (!isSinjiraBackendConfigured()) {
    setStatus(STATUS, 'Supabase doit être configuré pour générer le rapport.', 'error');
    return;
  }

  const email = String(EMAIL_INPUT?.value || '').trim();
  if (mode === 'email' && !user) {
    if (!email || !EMAIL_CONSENT?.checked) {
      setStatus(STATUS, 'Indiquez votre courriel et autorisez explicitement cet envoi.', 'error');
      EMAIL_PANEL.hidden = false;
      return;
    }
  }

  const supabase = getSupabase();
  setStatus(STATUS, mode === 'email' ? 'Préparation et envoi du rapport…' : 'Préparation du PDF…', 'info');

  const { data, error } = await supabase.functions.invoke('send-game-report', {
    body: {
      mode,
      session_id: currentSessionId,
      sheet_data: collectSheetData(),
      email: user ? undefined : email
    }
  });

  if (error || !data?.ok) {
    setStatus(STATUS, data?.error || error?.message || 'Impossible de générer le rapport.', 'error');
    return;
  }

  if (mode === 'download' && data.pdf_base64) {
    const bytes = Uint8Array.from(atob(data.pdf_base64), (char) => char.charCodeAt(0));
    const blob = new Blob([bytes], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = data.filename || 'SINJIRA_Fracture_du_Reseau_Mere_Rapport.pdf';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setStatus(STATUS, 'Votre PDF rempli a été généré sur votre appareil.', 'success');
  } else if (mode === 'email') {
    EMAIL_PANEL.hidden = true;
    setStatus(
      STATUS,
      user
        ? `Rapport envoyé à ${user.email}.`
        : `Rapport envoyé à ${email}. Aucune partie n’a été sauvegardée sur le site.`,
      'success'
    );
  }
}

async function contribute() {
  if (!user) {
    setStatus(STATUS, 'Le Programme Contributeur est réservé aux comptes joueurs.', 'error');
    return;
  }

  const sessionId = await saveSession();
  if (!sessionId) return;

  const supabase = getSupabase();
  const { data, error } = await supabase.functions.invoke('submit-game-contribution', {
    body: { session_id: sessionId }
  });

  if (error || !data?.ok) {
    setStatus(
      STATUS,
      data?.error || error?.message ||
        'Le partage n’a pas été effectué. Activez d’abord le Programme Contributeur dans votre compte.',
      'error'
    );
    return;
  }

  setStatus(
    STATUS,
    'Merci. Une copie dissociée des données utiles de cette partie a été transmise au programme d’amélioration SINJIRA.',
    'success'
  );
  document.querySelector('[data-contribute]')?.setAttribute('disabled', 'disabled');
}

function bindActions() {
  FORM.addEventListener('input', markDirty);
  FORM.addEventListener('change', markDirty);

  document.querySelector('[data-save-session]')?.addEventListener('click', () => saveSession());
  document.querySelector('[data-finish-session]')?.addEventListener('click', () => saveSession({ finish: true }));
  document.querySelector('[data-download-report]')?.addEventListener('click', () => invokeReport('download'));
  document.querySelector('[data-email-report]')?.addEventListener('click', () => {
    EMAIL_PANEL.hidden = false;
    if (user) invokeReport('email');
  });
  document.querySelector('[data-confirm-email-report]')?.addEventListener('click', () => invokeReport('email'));
  document.querySelector('[data-cancel-email-report]')?.addEventListener('click', () => {
    EMAIL_PANEL.hidden = true;
  });
  document.querySelector('[data-contribute]')?.addEventListener('click', contribute);
  document.querySelector('[data-new-session]')?.addEventListener('click', () => {
    if (dirty && !confirm('Les modifications non sauvegardées seront perdues. Continuer?')) return;
    location.href = location.pathname;
  });

  window.addEventListener('beforeunload', (event) => {
    if (!dirty) return;
    event.preventDefault();
    event.returnValue = '';
  });
}

async function init() {
  buildRounds();
  buildAccusations();
  bindActions();

  if (isSinjiraBackendConfigured()) {
    user = await getCurrentUser();
  }
  setMode();

  if (user && currentSessionId) await loadSession();

  if (!user) {
    SESSION_BADGE.textContent = 'Mode invité';
    markClean('Aucune donnée enregistrée');
  } else if (!currentSessionId) {
    SESSION_BADGE.textContent = 'Nouvelle partie';
    markClean('Nouvelle partie non sauvegardée');
  }
}

init();
