import './sinjira-preorder-cost-summary-v24-5-25.js';
import './sinjira-preorder-tax-estimate-v24-5-27.js';
import { escapeHtml, getCurrentUser, getSupabase, isSinjiraBackendConfigured } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const roots = [...document.querySelectorAll('[data-preorder-fulfillment]')];
const s = getSupabase();
const states = new WeakMap();
function state(root) {
  if (!states.has(root)) states.set(root, { estimateVersion: 0, loading: false, saving: false, preferenceVersion: 0, dirty: false });
  return states.get(root);
}
function preferenceControls(n, disabled) {
  [n.method, n.pickupSelect, n.savePreference].forEach(control => { if (control) control.disabled = disabled; });
}
function invalidateEstimate(root) {
  const n = nodes(root);
  state(root).estimateVersion++;
  if (n.estimateButton) n.estimateButton.disabled = false;
  n.estimateResult?.setAttribute('aria-busy', 'false');
  status(n.estimateResult, 'Options modifiées. Calculez une nouvelle estimation.', 'info');
}

function money(cents, currency) {
  if ((typeof cents !== 'number' && (typeof cents !== 'string' || !/^\d+$/.test(cents))) ||
      !Number.isSafeInteger(Number(cents)) || Number(cents) < 0 || !/^[A-Z]{3}$/.test(currency || '')) return null;
  try {
    return new Intl.NumberFormat('fr-CA', { style: 'currency', currency }).format(Number(cents) / 100);
  } catch {
    return null;
  }
}

function nodes(root) {
  return {
    estimator: root.querySelector('[data-pf-estimator]'),
    estimatorEmpty: root.querySelector('[data-pf-estimator-empty]'),
    zone: root.querySelector('[data-pf-zone]'),
    quantity: root.querySelector('[data-pf-quantity]'),
    estimateButton: root.querySelector('[data-pf-estimate]'),
    estimateResult: root.querySelector('[data-pf-estimate-result]'),
    pickupList: root.querySelector('[data-pf-pickup-list]'),
    pickupEmpty: root.querySelector('[data-pf-pickup-empty]'),
    preferencePanel: root.querySelector('[data-pf-preference-panel]'),
    preferenceAuth: root.querySelector('[data-pf-preference-auth]'),
    preferenceNoPreorder: root.querySelector('[data-pf-no-preorder]'),
    method: root.querySelector('[data-pf-method]'),
    pickupSelectWrap: root.querySelector('[data-pf-pickup-select-wrap]'),
    pickupSelect: root.querySelector('[data-pf-pickup-select]'),
    savePreference: root.querySelector('[data-pf-save-preference]'),
    preferenceStatus: root.querySelector('[data-pf-preference-status]')
  };
}

function show(node, visible = true) {
  if (node) node.hidden = !visible;
}

function status(node, message, kind = '') {
  if (!node) return;
  node.hidden = false;
  node.textContent = message;
  node.dataset.kind = kind;
}

async function rpc(name, args = {}) {
  const result = await s.rpc(name, args);
  if (result?.error !== null || !Object.hasOwn(result, 'data')) throw result?.error || new Error('Réponse non confirmée');
  return result.data;
}

async function loadOptions() {
  return await rpc('product_preorder_fulfillment_options', { p_product_slug: PRODUCT_SLUG });
}

function renderZones(n, options) {
  const zones = Array.isArray(options?.shipping_zones) ? options.shipping_zones : [];
  if (!options?.shipping_estimates_enabled || !zones.length) {
    show(n.estimator, false);
    show(n.estimatorEmpty, true);
    return;
  }
  show(n.estimatorEmpty, false);
  show(n.estimator, true);
  if (n.zone) {
    n.zone.innerHTML = '<option value="">Choisir une zone</option>' + zones.map(z =>
      `<option value="${escapeHtml(z.zone_code)}">${escapeHtml(z.label)}</option>`
    ).join('');
  }
}

function renderPickups(n, options) {
  const points = Array.isArray(options?.pickup_points) ? options.pickup_points : [];
  if (!options?.pickup_points_enabled || !points.length) {
    show(n.pickupList, false);
    show(n.pickupEmpty, true);
  } else {
    show(n.pickupEmpty, false);
    show(n.pickupList, true);
    n.pickupList.innerHTML = points.map(p => `<article class="sinjira-pickup-point">
      <strong>${escapeHtml(p.label || 'Point de ramassage')}</strong>
      <span>${escapeHtml([p.public_address, p.city, p.region].filter(Boolean).join(' · '))}</span>
      ${p.pickup_window_text ? `<small><b>Disponibilité :</b> ${escapeHtml(p.pickup_window_text)}</small>` : ''}
      ${p.instructions ? `<small>${escapeHtml(p.instructions)}</small>` : ''}
    </article>`).join('');
  }
  if (n.pickupSelect) {
    n.pickupSelect.innerHTML = '<option value="">Lieu à confirmer plus tard</option>' + points.map(p =>
      `<option value="${escapeHtml(p.pickup_code)}">${escapeHtml(p.label)}${p.city ? ` — ${escapeHtml(p.city)}` : ''}</option>`
    ).join('');
  }
}

async function estimate(root) {
  const n = nodes(root);
  const st = state(root);
  const version = ++st.estimateVersion;
  const current = () => version === st.estimateVersion;
  const zone = String(n.zone?.value || '');
  const quantity = Number(n.quantity?.value || 1);
  if (!zone || !Number.isInteger(quantity) || quantity < 1 || quantity > 5) {
    status(n.estimateResult, 'Choisissez une zone de livraison.', 'error');
    return;
  }
  if (n.estimateButton) n.estimateButton.disabled = true;
  n.estimateResult?.setAttribute('aria-busy', 'true');
  status(n.estimateResult, 'Calcul de l’estimation…', 'info');
  try {
    const data = await rpc('product_preorder_shipping_estimate', {
      p_product_slug: PRODUCT_SLUG,
      p_zone_code: zone,
      p_quantity: quantity
    });
    if (!current()) return;
    const row = Array.isArray(data) ? data[0] : data;
    if (!row) {
      status(n.estimateResult, 'Aucune estimation n’est publiée pour cette zone actuellement.', 'info');
      return;
    }
    const min = money(row.estimate_min_cents, row.currency);
    const max = money(row.estimate_max_cents, row.currency);
    if (min === null || max === null || Number(row.estimate_min_cents) > Number(row.estimate_max_cents)) throw new Error('Estimation non valide');
    n.estimateResult.hidden = false;
    n.estimateResult.dataset.kind = 'success';
    n.estimateResult.innerHTML = `<strong>Estimation : ${escapeHtml(min)} à ${escapeHtml(max)}</strong><span>pour ${quantity} exemplaire(s), zone « ${escapeHtml(row.zone_label)} ». Les frais de livraison seront à la charge du client. Cette fourchette est indicative : le coût final devra être affiché et confirmé avant tout futur achat.</span>${row.estimate_note ? `<small>${escapeHtml(row.estimate_note)}</small>` : ''}`;
  } catch (error) {
    if (current()) status(n.estimateResult, 'Impossible de calculer l’estimation. Réessayez.', 'error');
  } finally {
    if (current()) {
      if (n.estimateButton) n.estimateButton.disabled = false;
      n.estimateResult?.setAttribute('aria-busy', 'false');
    }
  }
}

async function loadPreference(root, user, options, { preserveDraft = false } = {}) {
  const n = nodes(root);
  const st = state(root);
  const version = ++st.preferenceVersion;
  const currentRequest = () => version === st.preferenceVersion;
  st.loading = true;
  const identity = user?.id || null;
  if (st.identity !== identity) {
    st.identity = identity;
    st.dirty = false;
    if (n.method) n.method.value = 'undecided';
    if (n.pickupSelect) n.pickupSelect.value = '';
    show(n.preferencePanel, false);
  }
  preferenceControls(n, true);
  n.preferencePanel?.setAttribute('aria-busy', 'true');
  try {
    if (!user) {
      st.dirty = false;
      show(n.preferenceAuth, true);
      show(n.preferencePanel, false);
      show(n.preferenceNoPreorder, false);
      return false;
    }
    show(n.preferenceAuth, false);
    show(n.preferenceNoPreorder, false);
    const current = await rpc('product_preorder_fulfillment_status', { p_product_slug: PRODUCT_SLUG });
    if (!currentRequest()) return false;
    if (!current) {
      st.dirty = false;
      show(n.preferencePanel, false);
      show(n.preferenceNoPreorder, true);
      return false;
    }
    if (!preserveDraft || !st.dirty || n.preferencePanel.hidden) {
      if (n.method) n.method.value = current.fulfillment_preference || 'undecided';
      if (n.pickupSelect) n.pickupSelect.value = current.pickup_code || '';
      st.dirty = false;
    }
    show(n.preferencePanel, true);
    togglePickupChoice(n, options);
    if (!st.saving) preferenceControls(n, false);
    if (st.dirty) status(n.preferenceStatus, 'Votre choix non enregistré est conservé.', 'info');
    return true;
  } catch {
    if (currentRequest()) {
      // Un échec de lecture n'est pas une preuve d'absence de réservation.
      show(n.preferenceNoPreorder, false);
      status(n.preferenceStatus, 'Impossible de vérifier votre réservation. Rechargez la page avant de modifier votre préférence.', 'error');
    }
    return false;
  } finally {
    if (currentRequest()) {
      st.loading = false;
      n.preferencePanel?.setAttribute('aria-busy', 'false');
    }
  }
}

function togglePickupChoice(n, options) {
  const pickup = n.method?.value === 'pickup';
  show(n.pickupSelectWrap, pickup);
  if (pickup && !options?.pickup_points_enabled && n.pickupSelect) n.pickupSelect.value = '';
}

async function savePreference(root, options) {
  const n = nodes(root);
  const st = state(root);
  if (st.saving || st.loading || n.savePreference?.disabled || n.preferencePanel?.hidden) return;
  const method = String(n.method?.value || 'undecided');
  const pickupCode = method === 'pickup' ? String(n.pickupSelect?.value || '') : '';
  st.saving = true;
  preferenceControls(n, true);
  n.preferencePanel?.setAttribute('aria-busy', 'true');
  status(n.preferenceStatus, 'Enregistrement en cours…', 'info');
  let confirmed = false;
  try {
    const ok = await rpc('product_preorder_set_fulfillment_preference', {
      p_product_slug: PRODUCT_SLUG,
      p_fulfillment_preference: method,
      p_pickup_code: pickupCode || null
    });
    if (!ok) throw new Error('Réservez d’abord le Livre I avant d’enregistrer ce choix.');
    const message = method === 'shipping'
      ? 'Préférence enregistrée : livraison. Les frais de livraison seront à votre charge et devront être confirmés avant tout futur achat.'
      : method === 'pickup'
        ? 'Préférence enregistrée : ramassage sur place. Aucun frais de livraison ne sera associé au ramassage; le lieu et la plage de retrait devront être confirmés lorsqu’ils seront publiés.'
        : 'Préférence enregistrée : vous déciderez plus tard entre livraison et ramassage.';
    confirmed = true;
    st.dirty = false;
    status(n.preferenceStatus, message, 'success');
  } catch {
    status(n.preferenceStatus, 'Enregistrement non confirmé. Votre choix est conservé. Rechargez la page pour vérifier avant de réessayer.', 'error');
  } finally {
    st.saving = false;
    n.preferencePanel?.setAttribute('aria-busy', 'false');
  }
  if (confirmed) {
    try {
      const available = await loadPreference(root, await getCurrentUser(), options);
      if (!available) status(n.preferenceStatus, 'Préférence enregistrée. Rechargez la page pour actualiser votre réservation.', 'success');
    } catch {
      status(n.preferenceStatus, 'Préférence enregistrée. Rechargez la page pour actualiser votre réservation.', 'success');
    }
  }
}

async function initRoot(root, user) {
  const n = nodes(root);
  let options;
  try {
    options = await loadOptions();
  } catch (error) {
    status(n.estimateResult, 'Les options de livraison sont temporairement indisponibles.', 'error');
    return;
  }
  renderZones(n, options || {});
  renderPickups(n, options || {});
  n.estimateButton?.addEventListener('click', () => estimate(root));
  [n.zone, n.quantity].forEach(control => control?.addEventListener('change', () => invalidateEstimate(root)));
  n.method?.addEventListener('change', () => {
    state(root).dirty = true;
    togglePickupChoice(n, options || {});
    status(n.preferenceStatus, 'Choix modifié. Enregistrez votre préférence.', 'info');
  });
  n.pickupSelect?.addEventListener('change', () => {
    state(root).dirty = true;
    status(n.preferenceStatus, 'Choix modifié. Enregistrez votre préférence.', 'info');
  });
  n.savePreference?.addEventListener('click', () => savePreference(root, options || {}));
  await loadPreference(root, user, options || {});
  window.addEventListener('sinjira:preorder-updated', async () => {
    if (state(root).saving) return;
    try {
      await loadPreference(root, await getCurrentUser(), options || {}, { preserveDraft: true });
    } catch {
      preferenceControls(n, true);
      status(n.preferenceStatus, 'Impossible de vérifier votre session. Rechargez la page.', 'error');
    }
  });
}

if (roots.length) {
  if (!isSinjiraBackendConfigured()) {
    for (const root of roots) status(nodes(root).estimateResult, 'Le service de livraison est temporairement indisponible.', 'error');
  } else {
    const user = await getCurrentUser();
    for (const root of roots) await initRoot(root, user);
  }
}
