import { getSupabase, escapeHtml, friendlyBackendMessage } from './sinjira-supabase.js';

const s = getSupabase();
const fmt = new Intl.DateTimeFormat('fr-CA', { dateStyle: 'medium', timeStyle: 'short' });

function dt(value) {
  if (!value) return 'Jamais modifié';
  try { return fmt.format(new Date(value)); } catch { return '—'; }
}
function workflowLabel(value) {
  return ({
    pending: 'À traiter',
    ready_for_future_contact: 'Prêt pour étape future',
    completed: 'Terminé'
  })[value] || 'À traiter';
}
function formatLabel(value) {
  return ({ paper: 'Papier', digital: 'Numérique', both: 'Papier + numérique', undecided: 'Indécis' })[value] || value || '—';
}
function fulfillmentLabel(value) {
  return ({ shipping: 'Livraison — frais client', pickup: 'Ramassage — 0 $ livraison', undecided: 'À décider' })[value] || value || '—';
}
async function rpc(name, args = {}) {
  const { data, error } = await s.rpc(name, args);
  if (error) throw error;
  return data;
}
async function requireAdminAal2() {
  const { data: { user }, error } = await s.auth.getUser();
  if (error || !user) throw new Error('AUTH_REQUIRED');
  const { data: isAdmin, error: adminError } = await s.rpc('is_sinjira_admin', { p_user_id: user.id });
  if (adminError || !isAdmin) throw new Error('ADMIN_REQUIRED');
  const { data: aal, error: aalError } = await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if (aalError) throw aalError;
  if (aal?.currentLevel !== 'aal2') throw new Error('MFA_REQUIRED');
}
function installPanel() {
  if (document.querySelector('[data-pa-workflow-panel]')) return;
  const hero = document.querySelector('.preorder-admin-hero');
  if (!hero) return;
  hero.insertAdjacentHTML('afterend', `<section class="section section-tight" data-pa-workflow-panel><div class="container"><article class="account-card preorder-admin-card"><div class="preorder-admin-list-head"><div><span class="eyebrow">V24.5.36 · suivi interne non financier</span><h2>Suivi opérationnel des réservations</h2><p>Ce suivi sert uniquement à organiser le travail administratif. Il ne modifie pas la réservation, n’envoie aucun message, ne crée aucune commande et ne déclenche aucun paiement. Aucune note libre, adresse, courriel ou UUID n’est stocké ici.</p></div><button class="btn btn-secondary" data-pa-workflow-refresh type="button">Actualiser</button></div><div class="preorder-admin-filters"><label>État interne<select data-pa-workflow-filter><option value="">Tous</option><option value="pending">À traiter</option><option value="ready_for_future_contact">Prêt pour étape future</option><option value="completed">Terminé</option></select></label></div><div class="account-status" data-pa-workflow-status hidden></div><div class="preorder-admin-list" data-pa-workflow-list><p>Chargement…</p></div></article></div></section>`);
}
function setStatus(message, kind = '') {
  const node = document.querySelector('[data-pa-workflow-status]');
  if (!node) return;
  node.hidden = false;
  node.textContent = message;
  node.dataset.kind = kind;
}
function renderRows(rows) {
  const list = document.querySelector('[data-pa-workflow-list]');
  if (!list) return;
  if (!rows.length) {
    list.innerHTML = '<div class="preorder-admin-empty">Aucune réservation pour cet état de suivi.</div>';
    return;
  }
  list.innerHTML = rows.map((row) => {
    const reference = String(row.reservation_reference || '').toUpperCase();
    const state = row.workflow_state || 'pending';
    return `<article class="preorder-admin-row" data-pa-workflow-row="${escapeHtml(reference)}"><strong>${escapeHtml(reference)}</strong><span>${escapeHtml(row.user_label || 'Compte SINJIRA')}</span><span>${escapeHtml(row.product_name || 'Livre I')} · ${escapeHtml(formatLabel(row.preferred_format))} · ${escapeHtml(String(row.quantity ?? 1))} exemplaire(s)</span><span>${escapeHtml(fulfillmentLabel(row.fulfillment_preference))}<br><small>Réservation : ${escapeHtml(row.preorder_status || '—')}</small></span><span><label>Suivi interne<select data-pa-workflow-state><option value="pending"${state === 'pending' ? ' selected' : ''}>À traiter</option><option value="ready_for_future_contact"${state === 'ready_for_future_contact' ? ' selected' : ''}>Prêt pour étape future</option><option value="completed"${state === 'completed' ? ' selected' : ''}>Terminé</option></select></label><button class="btn btn-secondary" data-pa-workflow-save type="button">Enregistrer</button><br><small>${escapeHtml(workflowLabel(state))} · ${escapeHtml(dt(row.workflow_updated_at))}</small></span></article>`;
  }).join('');
}
async function loadQueue(message = '') {
  const filter = document.querySelector('[data-pa-workflow-filter]');
  try {
    const rows = await rpc('admin_preorder_workflow_queue', {
      p_workflow_state: filter?.value || null,
      p_limit: 200
    });
    renderRows(Array.isArray(rows) ? rows : []);
    if (message) setStatus(message, 'success');
  } catch (error) {
    setStatus(friendlyBackendMessage(error?.message, 'Impossible de charger le suivi administratif.'), 'error');
  }
}
async function saveState(button) {
  const row = button.closest('[data-pa-workflow-row]');
  const reference = String(row?.dataset.paWorkflowRow || '').toUpperCase();
  const select = row?.querySelector('[data-pa-workflow-state]');
  const workflowState = String(select?.value || '');
  if (!/^PR-[0-9A-F]{16}$/.test(reference)) {
    setStatus('Référence de réservation invalide.', 'error');
    return;
  }
  if (!['pending','ready_for_future_contact','completed'].includes(workflowState)) {
    setStatus('État de suivi invalide.', 'error');
    return;
  }
  button.disabled = true;
  try {
    await rpc('admin_preorder_set_workflow_state', {
      p_reservation_reference: reference,
      p_workflow_state: workflowState
    });
    await loadQueue(`Suivi ${workflowLabel(workflowState).toLowerCase()} enregistré pour ${reference}. Aucun avis, aucune commande et aucun paiement n’ont été déclenchés.`);
  } catch (error) {
    setStatus(friendlyBackendMessage(error?.message, 'Impossible de modifier le suivi administratif.'), 'error');
  } finally {
    button.disabled = false;
  }
}
function bind() {
  document.querySelector('[data-pa-workflow-refresh]')?.addEventListener('click', () => loadQueue('Suivi actualisé.'));
  document.querySelector('[data-pa-workflow-filter]')?.addEventListener('change', () => loadQueue());
  document.querySelector('[data-pa-workflow-list]')?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-pa-workflow-save]');
    if (button) saveState(button);
  });
}
async function init() {
  installPanel();
  bind();
  try {
    await requireAdminAal2();
    await loadQueue();
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') location.replace('/compte/connexion.html?next=/admin/sinjira/precommandes.html');
    else if (error?.message === 'ADMIN_REQUIRED') location.replace('/compte/index.html');
    else if (error?.message === 'MFA_REQUIRED') location.replace(`/compte/mfa.html?security=1&next=${encodeURIComponent('/admin/sinjira/precommandes.html')}`);
    else setStatus(friendlyBackendMessage(error?.message, 'Impossible de charger le suivi administratif.'), 'error');
  }
}

init();