import {
  escapeHtml,
  formatDate,
  getCurrentUser,
  getSupabase,
  isSinjiraBackendConfigured,
  setStatus
} from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const DISCLOSURE_VERSION = 'preorder-disclosure-v24.5.31';
const FORMAT_LABELS = {
  digital: 'Numérique',
  paper: 'Papier',
  both: 'Papier + numérique',
  undecided: 'Je déciderai plus tard'
};
const FULFILLMENT_LABELS = {
  shipping: 'Livraison — frais à ma charge',
  pickup: 'Ramassage sur place — 0 $ de frais de livraison',
  undecided: 'Je déciderai plus tard'
};

const roots = [...document.querySelectorAll('[data-preorder-root]')];

function rootNodes(root) {
  return {
    auth: root.querySelector('[data-preorder-auth]'),
    login: root.querySelector('[data-preorder-login]'),
    form: root.querySelector('[data-preorder-form]'),
    format: root.querySelector('[data-preorder-format]'),
    quantity: root.querySelector('[data-preorder-quantity]'),
    contact: root.querySelector('[data-preorder-contact]'),
    disclosure: root.querySelector('[data-preorder-disclosure]'),
    submit: root.querySelector('[data-preorder-submit]'),
    state: root.querySelector('[data-preorder-state]'),
    cancel: root.querySelector('[data-preorder-cancel]'),
    status: root.querySelector('[data-preorder-status]')
  };
}

function loginHref() {
  const next = encodeURIComponent(`${location.pathname}${location.search}${location.hash}`);
  return `/compte/connexion.html?next=${next}`;
}

async function readPreorder() {
  const { data, error } = await getSupabase().rpc('product_preorder_my_status', {
    p_product_slug: PRODUCT_SLUG
  });
  if (error) throw error;
  return Array.isArray(data) ? (data[0] || null) : (data || null);
}

function renderState(nodes, preorder) {
  if (nodes.disclosure) nodes.disclosure.checked = false;
  if (!nodes.state) return;
  if (!preorder) {
    nodes.state.hidden = true;
    if (nodes.cancel) nodes.cancel.hidden = true;
    if (nodes.submit) nodes.submit.textContent = 'Réserver ma précommande';
    return;
  }

  const reserved = preorder.status === 'reserved';
  nodes.state.hidden = false;
  nodes.state.dataset.state = reserved ? 'reserved' : 'cancelled';
  const format = FORMAT_LABELS[preorder.preferred_format] || 'À déterminer';
  const fulfillment = FULFILLMENT_LABELS[preorder.fulfillment_preference] || 'Je déciderai plus tard';
  const title = reserved ? 'Précommande réservée' : 'Précommande annulée';
  const payment = preorder.payment_status === 'not_collected' && preorder.financial_commitment === false
    ? 'Aucun paiement — aucun engagement financier'
    : 'État financier à vérifier';
  const reference = preorder.reservation_reference || 'Référence en cours de génération';
  const disclosure = preorder.disclosure_version && preorder.disclosure_acknowledged_at
    ? `${escapeHtml(preorder.disclosure_version)} — confirmé le ${escapeHtml(formatDate(preorder.disclosure_acknowledged_at))}`
    : 'Confirmation non enregistrée pour cette ancienne réservation';

  nodes.state.innerHTML = `
    <strong>${title}</strong>
    <dl>
      <dt>Référence de réservation</dt><dd><code>${escapeHtml(reference)}</code></dd>
      <dt>Roman</dt><dd>${escapeHtml(preorder.product_name || 'SINJIRA™ — Livre I')}</dd>
      <dt>Format souhaité</dt><dd>${escapeHtml(format)}</dd>
      <dt>Quantité</dt><dd>${Number(preorder.quantity || 1)}</dd>
      <dt>Réception souhaitée</dt><dd>${escapeHtml(fulfillment)}</dd>
      <dt>État</dt><dd>${reserved ? 'Réservée' : 'Annulée'}</dd>
      <dt>Paiement</dt><dd>${payment}</dd>
      <dt>Conditions de réservation</dt><dd>${disclosure}</dd>
      <dt>Réservation créée</dt><dd>${escapeHtml(formatDate(preorder.created_at))}</dd>
      <dt>Dernière mise à jour</dt><dd>${escapeHtml(formatDate(preorder.updated_at))}</dd>
    </dl>
    <p><small>Cette référence identifie seulement votre réservation SINJIRA™. Elle n’est ni un numéro de commande ni un identifiant technique de votre compte.</small></p>`;

  if (nodes.format) nodes.format.value = preorder.preferred_format || 'undecided';
  if (nodes.quantity) nodes.quantity.value = String(preorder.quantity || 1);
  if (nodes.contact) nodes.contact.checked = preorder.contact_when_sales_open !== false;
  if (nodes.cancel) nodes.cancel.hidden = !reserved;
  if (nodes.submit) nodes.submit.textContent = reserved ? 'Mettre à jour ma précommande' : 'Réactiver ma précommande';
}

async function refreshRoot(root, user = null) {
  const nodes = rootNodes(root);
  const currentUser = user || await getCurrentUser();

  if (!currentUser) {
    if (nodes.auth) nodes.auth.hidden = false;
    if (nodes.login) nodes.login.href = loginHref();
    if (nodes.form) nodes.form.hidden = true;
    if (nodes.state) nodes.state.hidden = true;
    if (nodes.cancel) nodes.cancel.hidden = true;
    return;
  }

  if (nodes.auth) nodes.auth.hidden = true;
  if (nodes.form) nodes.form.hidden = false;

  const preorder = await readPreorder();
  renderState(nodes, preorder);
}

async function refreshAll(user = null) {
  for (const root of roots) await refreshRoot(root, user);
}

function announcePreorderUpdate() {
  window.dispatchEvent(new CustomEvent('sinjira:preorder-updated'));
}

async function reserve(root, event) {
  event.preventDefault();
  const nodes = rootNodes(root);
  const quantity = Number(nodes.quantity?.value || 1);
  const preferredFormat = String(nodes.format?.value || 'undecided');
  const contactWhenSalesOpen = nodes.contact?.checked !== false;

  if (!Number.isInteger(quantity) || quantity < 1 || quantity > 5) {
    setStatus(nodes.status, 'Choisissez une quantité entre 1 et 5.', 'error');
    return;
  }

  if (!Object.prototype.hasOwnProperty.call(FORMAT_LABELS, preferredFormat)) {
    setStatus(nodes.status, 'Choisissez un format valide.', 'error');
    return;
  }

  if (!nodes.disclosure?.checked) {
    setStatus(nodes.status, 'Confirmez d’abord que vous avez compris les conditions de cette réservation sans paiement, y compris les frais de livraison à votre charge.', 'error');
    nodes.disclosure?.focus();
    return;
  }

  if (nodes.submit) nodes.submit.disabled = true;
  try {
    const { error } = await getSupabase().rpc('product_preorder_reserve_confirmed', {
      p_product_slug: PRODUCT_SLUG,
      p_preferred_format: preferredFormat,
      p_quantity: quantity,
      p_contact_when_sales_open: contactWhenSalesOpen,
      p_disclosure_version: DISCLOSURE_VERSION,
      p_disclosure_acknowledged: true
    });
    if (error) throw error;
    setStatus(nodes.status, 'Votre précommande est réservée. Aucun paiement n’a été prélevé; toute future commande devra être confirmée séparément.', 'success');
    await refreshAll();
    announcePreorderUpdate();
  } catch (error) {
    console.error('[SINJIRA preorder reserve]', error);
    const message = String(error?.message || '');
    setStatus(
      nodes.status,
      message.includes('PREORDER_DISCLOSURE_REQUIRED')
        ? 'La réservation exige la confirmation du texte de transparence actuel. Relisez l’avertissement et confirmez-le avant de continuer.'
        : (message || 'La précommande n’a pas pu être enregistrée.'),
      'error'
    );
  } finally {
    if (nodes.submit) nodes.submit.disabled = false;
  }
}

async function cancel(root) {
  const nodes = rootNodes(root);
  if (!confirm('Annuler votre réservation de précommande du Livre I ? Aucun paiement n’a été prélevé.')) return;
  if (nodes.cancel) nodes.cancel.disabled = true;
  try {
    const { data, error } = await getSupabase().rpc('product_preorder_cancel', {
      p_product_slug: PRODUCT_SLUG
    });
    if (error) throw error;
    setStatus(nodes.status, data ? 'Votre précommande a été annulée.' : 'Aucune précommande active à annuler.', data ? 'success' : 'info');
    await refreshAll();
    announcePreorderUpdate();
  } catch (error) {
    console.error('[SINJIRA preorder cancel]', error);
    setStatus(nodes.status, error?.message || 'La précommande n’a pas pu être annulée.', 'error');
  } finally {
    if (nodes.cancel) nodes.cancel.disabled = false;
  }
}

if (roots.length) {
  if (!isSinjiraBackendConfigured()) {
    for (const root of roots) {
      const nodes = rootNodes(root);
      if (nodes.form) nodes.form.hidden = true;
      setStatus(nodes.status, 'Le service de précommande SINJIRA™ est temporairement indisponible.', 'error');
    }
  } else {
    const user = await getCurrentUser();
    for (const root of roots) {
      const nodes = rootNodes(root);
      nodes.form?.addEventListener('submit', event => reserve(root, event));
      nodes.cancel?.addEventListener('click', () => cancel(root));
    }
    try {
      await refreshAll(user);
    } catch (error) {
      console.error('[SINJIRA preorder load]', error);
      for (const root of roots) setStatus(rootNodes(root).status, error?.message || 'Impossible de charger votre précommande.', 'error');
    }
  }
}
