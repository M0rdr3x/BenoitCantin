import { getSupabase, escapeHtml, friendlyBackendMessage } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const s = getSupabase();
const statusNode = document.querySelector('[data-preorder-admin-status]');
const listNode = document.querySelector('[data-pa-list]');
const form = document.querySelector('[data-pa-announcement-form]');
const filterStatus = document.querySelector('[data-pa-filter-status]');
const filterFormat = document.querySelector('[data-pa-filter-format]');
const state = { overview: null, rows: [] };
const fmt = new Intl.DateTimeFormat('fr-CA', { dateStyle: 'medium', timeStyle: 'short' });

function showStatus(message, kind = '') {
  if (!statusNode) return;
  statusNode.hidden = false;
  statusNode.textContent = message;
  statusNode.dataset.kind = kind;
}
function dt(value) {
  if (!value) return '—';
  try { return fmt.format(new Date(value)); } catch { return '—'; }
}
function toLocalInput(value) {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function formatLabel(value) {
  return ({ paper: 'Papier', digital: 'Numérique', both: 'Papier + numérique', undecided: 'Indécis' })[value] || value || '—';
}
function fulfillmentLabel(value) {
  return ({ shipping: 'Livraison — frais à la charge du client', pickup: 'Ramassage sur place — 0 $ de frais de livraison', undecided: 'À décider' })[value] || value || '—';
}
function statusLabel(value) {
  return ({ reserved: 'Active', cancelled: 'Annulée', draft: 'Brouillon', ready: 'Prêt', sent: 'Envoyé', cancelled_campaign: 'Annulé' })[value] || value || 'Non préparé';
}
async function rpc(name, args = {}) {
  const { data, error } = await s.rpc(name, args);
  if (error) throw error;
  return data;
}
async function requireAdminAal2() {
  const { data: { user }, error } = await s.auth.getUser();
  if (error || !user) {
    location.replace('/compte/connexion.html?next=/admin/sinjira/precommandes.html');
    throw new Error('AUTH_REQUIRED');
  }
  const { data: isAdmin, error: adminError } = await s.rpc('is_sinjira_admin', { p_user_id: user.id });
  if (adminError || !isAdmin) {
    location.replace('/compte/index.html');
    throw new Error('ADMIN_REQUIRED');
  }
  const { data: aal, error: aalError } = await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if (aalError) throw aalError;
  if (aal?.currentLevel !== 'aal2') {
    location.replace(`/compte/mfa.html?security=1&next=${encodeURIComponent('/admin/sinjira/precommandes.html')}`);
    throw new Error('MFA_REQUIRED');
  }
}
function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) node.textContent = String(value ?? 0);
}
function installReferenceLookup() {
  if (document.querySelector('[data-pa-reference-lookup]')) return;
  const hero = document.querySelector('.preorder-admin-hero');
  if (!hero) return;
  hero.insertAdjacentHTML('afterend', `<section class="section section-tight" data-pa-reference-lookup><div class="container"><article class="account-card preorder-admin-card"><span class="eyebrow">V24.5.35 · assistance par référence</span><h2>Retrouver une réservation</h2><p>Entrez uniquement la référence <code>PR-…</code> fournie par la personne. Cette recherche n’accepte ni courriel, ni UUID, ni adresse et exige toujours l’administration avec MFA/AAL2.</p><form class="account-form" data-pa-reference-form><div class="field wide"><label for="pa-reference">Référence de réservation</label><input id="pa-reference" name="reservation_reference" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="19" placeholder="PR-0123456789ABCDEF" required/></div><div class="wide"><button class="btn btn-secondary" type="submit">Rechercher la réservation</button></div></form><div class="account-status" data-pa-reference-status hidden></div><div data-pa-reference-result hidden></div></article></div></section>`);
  document.querySelector('[data-pa-reference-form]')?.addEventListener('submit', lookupReference);
}
async function lookupReference(event) {
  event.preventDefault();
  const lookupForm = event.currentTarget;
  const input = lookupForm.elements.reservation_reference;
  const reference = String(input?.value || '').trim().toUpperCase();
  const resultNode = document.querySelector('[data-pa-reference-result]');
  const lookupStatus = document.querySelector('[data-pa-reference-status]');
  const button = lookupForm.querySelector('button[type="submit"]');
  const setLookupStatus = (message, kind = '') => {
    if (!lookupStatus) return;
    lookupStatus.hidden = false;
    lookupStatus.textContent = message;
    lookupStatus.dataset.kind = kind;
  };
  if (!/^PR-[0-9A-F]{16}$/.test(reference)) {
    if (resultNode) resultNode.hidden = true;
    setLookupStatus('Entrez une référence valide au format PR- suivi de 16 caractères hexadécimaux.', 'error');
    input?.focus();
    return;
  }
  if (button) button.disabled = true;
  try {
    const rows = await rpc('admin_preorder_find_by_reference', { p_reservation_reference: reference });
    const row = Array.isArray(rows) ? (rows[0] || null) : rows;
    if (!row) {
      if (resultNode) resultNode.hidden = true;
      setLookupStatus('Aucune réservation ne correspond à cette référence.', 'info');
      return;
    }
    if (resultNode) {
      resultNode.hidden = false;
      resultNode.innerHTML = `<div class="preorder-admin-row"><strong>${escapeHtml(row.reservation_reference || reference)}</strong><span>${escapeHtml(row.user_label || 'Compte SINJIRA')}</span><span>${escapeHtml(row.product_name || 'Livre I')} · ${escapeHtml(formatLabel(row.preferred_format))} · ${escapeHtml(String(row.quantity ?? 1))} exemplaire(s)</span><span class="${row.status === 'reserved' ? 'active' : 'cancelled'}">${escapeHtml(statusLabel(row.status))}</span><span>${escapeHtml(fulfillmentLabel(row.fulfillment_preference))}<br><small>Conditions : ${escapeHtml(row.disclosure_version || 'ancienne réservation')} · ${escapeHtml(dt(row.disclosure_acknowledged_at))}<br>Mise à jour : ${escapeHtml(dt(row.updated_at))}</small></span></div><p><small>Résultat volontairement minimal : aucun UUID, courriel, adresse de livraison, adresse de facturation ou donnée bancaire n’est retourné.</small></p>`;
    }
    setLookupStatus('Réservation retrouvée par sa référence.', 'success');
  } catch (error) {
    if (resultNode) resultNode.hidden = true;
    const message = String(error?.message || '');
    setLookupStatus(message.includes('INVALID_RESERVATION_REFERENCE') ? 'Référence invalide.' : friendlyBackendMessage(message, 'Impossible de rechercher cette réservation.'), 'error');
  } finally {
    if (button) button.disabled = false;
  }
}
function renderOverview() {
  const o = state.overview || {};
  const x = o.summary || {};
  setText('[data-pa-reserved]', x.reserved_accounts);
  setText('[data-pa-units]', x.reserved_units);
  setText('[data-pa-optin]', x.notify_opt_in);
  setText('[data-pa-cancelled]', x.cancelled_accounts);
  setText('[data-pa-paper-accounts]', x.paper_accounts);
  setText('[data-pa-paper-units]', x.paper_units);
  setText('[data-pa-digital-accounts]', x.digital_accounts);
  setText('[data-pa-digital-units]', x.digital_units);
  setText('[data-pa-both-accounts]', x.both_accounts);
  setText('[data-pa-both-units]', x.both_units);
  setText('[data-pa-undecided-accounts]', x.undecided_accounts);
  setText('[data-pa-undecided-units]', x.undecided_units);

  const a = o.announcement || null;
  const pill = document.querySelector('[data-pa-announcement-state]');
  const sentMeta = document.querySelector('[data-pa-sent-meta]');
  const markReady = document.querySelector('[data-pa-mark-ready]');
  const send = document.querySelector('[data-pa-send-internal]');
  if (pill) {
    pill.textContent = a ? statusLabel(a.status) : 'Non préparé';
    pill.dataset.state = a?.status || 'none';
  }
  if (sentMeta) sentMeta.textContent = a?.sent_at ? `${dt(a.sent_at)} · ${a.recipient_count ?? 0} destinataire(s)` : '—';
  if (markReady) markReady.disabled = !a || a.status !== 'draft';
  if (send) send.disabled = !a || a.status !== 'ready';

  if (!form || !a) return;
  form.elements.title.value = a.title || '';
  form.elements.body.value = a.body || '';
  form.elements.action_path.value = a.action_path || '/compte/mes-achats.html#precommandes';
  form.elements.sales_open_at.value = toLocalInput(a.sales_open_at);
  form.elements.public_price_text.value = a.public_price_text || '';
  form.elements.edition_note.value = a.edition_note || '';
  const locked = a.status === 'sent';
  [...form.elements].forEach((el) => {
    if (el.matches('[data-pa-send-internal]')) return;
    if (el.matches('[data-pa-mark-ready]')) return;
    if (el.matches('[data-pa-save-draft]')) return;
    el.disabled = locked;
  });
  const save = document.querySelector('[data-pa-save-draft]');
  if (save) save.disabled = locked;
}
async function loadOverview() {
  state.overview = await rpc('admin_preorder_overview', { p_product_slug: PRODUCT_SLUG });
  renderOverview();
}
async function loadRows() {
  const rows = await rpc('admin_preorder_list', {
    p_product_slug: PRODUCT_SLUG,
    p_status: filterStatus?.value || null,
    p_format: filterFormat?.value || null,
    p_limit: 250,
    p_offset: 0
  });
  state.rows = Array.isArray(rows) ? rows : [];
  renderRows();
}
function renderRows() {
  if (!listNode) return;
  if (!state.rows.length) {
    listNode.innerHTML = '<div class="preorder-admin-empty">Aucune réservation pour ce filtre.</div>';
    return;
  }
  listNode.innerHTML = state.rows.map((row) => `<article class="preorder-admin-row">
    <strong>${escapeHtml(row.user_label || 'Compte SINJIRA')}</strong>
    <span>${escapeHtml(formatLabel(row.preferred_format))}</span>
    <span>${escapeHtml(String(row.quantity ?? 1))} exemplaire(s)</span>
    <span class="${row.status === 'reserved' ? 'active' : 'cancelled'}">${escapeHtml(statusLabel(row.status))}</span>
    <span>${row.contact_when_sales_open ? 'Avis interne : oui' : 'Avis interne : non'}<br><small>${escapeHtml(dt(row.updated_at))}</small></span>
  </article>`).join('');
}
async function refreshAll(message = '') {
  await Promise.all([loadOverview(), loadRows()]);
  if (message) showStatus(message, 'success');
}
function formArgs() {
  const fd = new FormData(form);
  const sales = String(fd.get('sales_open_at') || '').trim();
  return {
    p_product_slug: PRODUCT_SLUG,
    p_title: String(fd.get('title') || '').trim(),
    p_body: String(fd.get('body') || '').trim(),
    p_action_path: String(fd.get('action_path') || '').trim(),
    p_sales_open_at: sales ? new Date(sales).toISOString() : null,
    p_public_price_text: String(fd.get('public_price_text') || '').trim() || null,
    p_edition_note: String(fd.get('edition_note') || '').trim()
  };
}
async function saveDraft(event) {
  event.preventDefault();
  const button = document.querySelector('[data-pa-save-draft]');
  if (button) button.disabled = true;
  try {
    await rpc('admin_preorder_save_announcement_draft', formArgs());
    await refreshAll('Brouillon enregistré. Aucun avis n’a été envoyé.');
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Impossible d’enregistrer le brouillon.'), 'error');
  } finally {
    if (button && state.overview?.announcement?.status !== 'sent') button.disabled = false;
  }
}
async function markReady() {
  const a = state.overview?.announcement;
  if (!a || a.status !== 'draft') return;
  if (!confirm('Marquer cet avis comme prêt ? Cela ne l’envoie pas encore et n’active aucun paiement.')) return;
  const button = document.querySelector('[data-pa-mark-ready]');
  if (button) button.disabled = true;
  try {
    const ok = await rpc('admin_preorder_mark_announcement_ready', { p_product_slug: PRODUCT_SLUG });
    if (!ok) throw new Error('ANNOUNCEMENT_NOT_READY');
    await refreshAll('Avis marqué prêt. Il n’a pas encore été envoyé.');
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Impossible de marquer l’avis prêt.'), 'error');
  } finally {
    if (button) button.disabled = false;
  }
}
async function sendInternal() {
  const a = state.overview?.announcement;
  if (!a || a.status !== 'ready') return;
  const count = state.overview?.summary?.notify_opt_in ?? 0;
  if (!confirm(`Envoyer maintenant cet avis dans SINJIRA™ aux ${count} réservation(s) actives ayant demandé à être averties ? Aucun courriel, SMS ou paiement ne sera déclenché.`)) return;
  const button = document.querySelector('[data-pa-send-internal]');
  if (button) button.disabled = true;
  try {
    const sent = await rpc('admin_preorder_send_internal_announcement', { p_product_slug: PRODUCT_SLUG });
    await refreshAll(`Avis interne envoyé à ${sent ?? 0} compte(s). Aucun service externe n’a été utilisé.`);
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'L’envoi interne a été refusé.'), 'error');
  } finally {
    if (button && state.overview?.announcement?.status === 'ready') button.disabled = false;
  }
}
function bind() {
  installReferenceLookup();
  form?.addEventListener('submit', saveDraft);
  document.querySelector('[data-pa-mark-ready]')?.addEventListener('click', markReady);
  document.querySelector('[data-pa-send-internal]')?.addEventListener('click', sendInternal);
  document.querySelector('[data-pa-refresh]')?.addEventListener('click', () => refreshAll('Données actualisées.'));
  filterStatus?.addEventListener('change', loadRows);
  filterFormat?.addEventListener('change', loadRows);
}
async function init() {
  bind();
  try {
    await requireAdminAal2();
    await refreshAll();
    showStatus('Administration des précommandes chargée. Aucun paiement ni transport externe n’est actif.', 'success');
  } catch (error) {
    if (!['AUTH_REQUIRED','ADMIN_REQUIRED','MFA_REQUIRED'].includes(error?.message)) {
      showStatus(friendlyBackendMessage(error?.message, 'Impossible de charger l’administration des précommandes.'), 'error');
    }
  }
}

init();
