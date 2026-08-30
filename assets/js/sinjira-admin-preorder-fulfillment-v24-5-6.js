import './sinjira-admin-preorder-tax-v24-5-27.js';
import { escapeHtml, friendlyBackendMessage, getSupabase } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const s = getSupabase();
const statusNode = document.querySelector('[data-pf-admin-status]');
const settingsForm = document.querySelector('[data-pf-admin-settings]');
const zoneForm = document.querySelector('[data-pf-admin-zone-form]');
const pickupForm = document.querySelector('[data-pf-admin-pickup-form]');
const zoneList = document.querySelector('[data-pf-admin-zones]');
const pickupList = document.querySelector('[data-pf-admin-pickups]');
let state = { settings: {}, zones: [], pickup_points: [], summary: {} };

function ensureReadinessLink() {
  const hero = document.querySelector('.preorder-admin-hero .container');
  if (!hero || hero.querySelector('[data-preorder-readiness-link]')) return;
  const actions = document.createElement('div');
  actions.className = 'hero-actions';
  actions.dataset.preorderReadinessLink = 'true';
  actions.innerHTML = '<a class="btn btn-secondary" href="/admin/sinjira/precommandes-readiness.html">Vérifier la préparation à une future vente</a>';
  const status = hero.querySelector('[data-preorder-admin-status]');
  hero.insertBefore(actions, status || null);
}

function showStatus(message, kind = '') {
  if (!statusNode) return;
  statusNode.hidden = false;
  statusNode.textContent = message;
  statusNode.dataset.kind = kind;
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

function centsFromInput(value) {
  const raw = String(value ?? '').trim().replace(',', '.');
  if (!raw) return null;
  const n = Number(raw);
  if (!Number.isFinite(n) || n < 0) throw new Error('Montant invalide.');
  return Math.round(n * 100);
}

function money(cents, currency = 'CAD') {
  if (cents === null || cents === undefined) return '—';
  try { return new Intl.NumberFormat('fr-CA', { style: 'currency', currency }).format(Number(cents) / 100); }
  catch { return `${(Number(cents) / 100).toFixed(2)} ${currency}`; }
}

function setText(selector, value) {
  const el = document.querySelector(selector);
  if (el) el.textContent = String(value ?? 0);
}

function renderSettings() {
  const x = state.settings || {};
  if (settingsForm) {
    settingsForm.elements.currency.value = x.currency || 'CAD';
    settingsForm.elements.shipping_estimates_enabled.checked = x.shipping_estimates_enabled === true;
    settingsForm.elements.pickup_points_enabled.checked = x.pickup_points_enabled === true;
  }
  setText('[data-pf-admin-shipping-count]', state.summary?.shipping || 0);
  setText('[data-pf-admin-pickup-count]', state.summary?.pickup || 0);
  setText('[data-pf-admin-undecided-count]', state.summary?.undecided || 0);
}

function renderZones() {
  if (!zoneList) return;
  const rows = Array.isArray(state.zones) ? state.zones : [];
  if (!rows.length) {
    zoneList.innerHTML = '<div class="pf-admin-row"><strong>Aucune zone de livraison.</strong><small>Ajoutez des fourchettes seulement lorsque vous avez des coûts raisonnablement fiables.</small></div>';
    return;
  }
  zoneList.innerHTML = rows.map(z => `<article class="pf-admin-row">
    <div class="pf-admin-row-head"><div><strong>${escapeHtml(z.label)}</strong><div class="pf-admin-row-meta"><span>${escapeHtml(z.zone_code)}</span><span>${escapeHtml(z.country_code || 'pays libre')}</span>${z.subdivision_code ? `<span>${escapeHtml(z.subdivision_code)}</span>` : ''}</div></div><span class="pf-admin-badge ${z.published_at ? 'published' : ''}">${z.published_at ? 'Publiée' : 'Brouillon'}</span></div>
    <div class="pf-admin-row-meta"><span>Base : ${escapeHtml(money(z.base_min_cents,z.currency))} à ${escapeHtml(money(z.base_max_cents,z.currency))}</span><span>Exemplaire additionnel : ${escapeHtml(money(z.additional_copy_min_cents,z.currency))} à ${escapeHtml(money(z.additional_copy_max_cents,z.currency))}</span></div>
    ${z.estimate_note ? `<small>${escapeHtml(z.estimate_note)}</small>` : ''}
    <div class="pf-admin-row-actions"><button class="btn btn-secondary" type="button" data-pf-edit-zone="${escapeHtml(z.zone_code)}">Modifier</button><button class="btn btn-primary" type="button" data-pf-publish-zone="${escapeHtml(z.zone_code)}" ${z.published_at ? 'disabled' : ''}>Publier la fourchette</button></div>
  </article>`).join('');
}

function renderPickups() {
  if (!pickupList) return;
  const rows = Array.isArray(state.pickup_points) ? state.pickup_points : [];
  if (!rows.length) {
    pickupList.innerHTML = '<div class="pf-admin-row"><strong>Aucun point de ramassage.</strong><small>La préférence « ramassage » peut tout de même être choisie; l’adresse sera confirmée plus tard.</small></div>';
    return;
  }
  pickupList.innerHTML = rows.map(p => `<article class="pf-admin-row">
    <div class="pf-admin-row-head"><div><strong>${escapeHtml(p.label)}</strong><div class="pf-admin-row-meta"><span>${escapeHtml(p.pickup_code)}</span><span>${escapeHtml([p.city,p.region,p.country_code].filter(Boolean).join(' · '))}</span></div></div><span class="pf-admin-badge ${p.published_at ? 'published' : ''}">${p.published_at ? 'Public' : 'Privé / brouillon'}</span></div>
    <small>${escapeHtml(p.public_address || 'Adresse publique non définie')}</small>
    ${p.pickup_window_text ? `<small><b>Plage :</b> ${escapeHtml(p.pickup_window_text)}</small>` : ''}
    <div class="pf-admin-row-actions"><button class="btn btn-secondary" type="button" data-pf-edit-pickup="${escapeHtml(p.pickup_code)}">Modifier</button><button class="btn btn-primary" type="button" data-pf-publish-pickup="${escapeHtml(p.pickup_code)}" ${p.published_at ? 'disabled' : ''}>Publier le point</button></div>
  </article>`).join('');
}

function render() {
  renderSettings();
  renderZones();
  renderPickups();
}

async function load() {
  state = await rpc('admin_preorder_fulfillment_get', { p_product_slug: PRODUCT_SLUG }) || state;
  render();
}

async function saveSettings(event) {
  event.preventDefault();
  const button = settingsForm?.querySelector('button[type="submit"]');
  if (button) button.disabled = true;
  try {
    await rpc('admin_preorder_fulfillment_settings_save', {
      p_product_slug: PRODUCT_SLUG,
      p_currency: String(settingsForm.elements.currency.value || 'CAD').toUpperCase(),
      p_shipping_estimates_enabled: settingsForm.elements.shipping_estimates_enabled.checked,
      p_pickup_points_enabled: settingsForm.elements.pickup_points_enabled.checked
    });
    await load();
    showStatus('Paramètres enregistrés. Livraison à la charge du client, API transporteur et achat d’étiquette restent verrouillés.', 'success');
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Impossible d’enregistrer les paramètres.'), 'error');
  } finally { if (button) button.disabled = false; }
}

async function saveZone(event) {
  event.preventDefault();
  const fd = new FormData(zoneForm);
  try {
    await rpc('admin_preorder_shipping_zone_save', {
      p_product_slug: PRODUCT_SLUG,
      p_zone_code: String(fd.get('zone_code') || '').trim().toLowerCase(),
      p_label: String(fd.get('label') || '').trim(),
      p_country_code: String(fd.get('country_code') || '').trim().toUpperCase() || null,
      p_subdivision_code: String(fd.get('subdivision_code') || '').trim().toUpperCase() || null,
      p_currency: String(fd.get('currency') || 'CAD').trim().toUpperCase(),
      p_base_min_cents: centsFromInput(fd.get('base_min')),
      p_base_max_cents: centsFromInput(fd.get('base_max')),
      p_additional_copy_min_cents: centsFromInput(fd.get('additional_min')) ?? 0,
      p_additional_copy_max_cents: centsFromInput(fd.get('additional_max')) ?? 0,
      p_estimate_note: String(fd.get('estimate_note') || '').trim() || null,
      p_active: fd.get('active') === 'on'
    });
    zoneForm.reset();
    zoneForm.elements.currency.value = state.settings?.currency || 'CAD';
    zoneForm.elements.active.checked = true;
    await load();
    showStatus('Zone enregistrée comme brouillon. Elle n’est pas visible tant que vous ne la publiez pas.', 'success');
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Impossible d’enregistrer la zone.'), 'error');
  }
}

async function publishZone(code) {
  if (!confirm('Publier cette estimation de livraison ? Elle sera visible comme fourchette indicative seulement; aucun transporteur ni paiement ne sera activé.')) return;
  try {
    const ok = await rpc('admin_preorder_shipping_zone_publish', { p_product_slug: PRODUCT_SLUG, p_zone_code: code });
    if (!ok) throw new Error('La fourchette minimale et maximale doivent être définies avant publication.');
    await load();
    showStatus('Fourchette de livraison publiée comme estimation indicative.', 'success');
  } catch (error) { showStatus(friendlyBackendMessage(error?.message, 'Publication refusée.'), 'error'); }
}

function editZone(code) {
  const z = (state.zones || []).find(x => x.zone_code === code);
  if (!z || !zoneForm) return;
  zoneForm.elements.zone_code.value = z.zone_code || '';
  zoneForm.elements.label.value = z.label || '';
  zoneForm.elements.country_code.value = z.country_code || '';
  zoneForm.elements.subdivision_code.value = z.subdivision_code || '';
  zoneForm.elements.currency.value = z.currency || 'CAD';
  zoneForm.elements.base_min.value = z.base_min_cents == null ? '' : (z.base_min_cents / 100).toFixed(2);
  zoneForm.elements.base_max.value = z.base_max_cents == null ? '' : (z.base_max_cents / 100).toFixed(2);
  zoneForm.elements.additional_min.value = ((z.additional_copy_min_cents || 0) / 100).toFixed(2);
  zoneForm.elements.additional_max.value = ((z.additional_copy_max_cents || 0) / 100).toFixed(2);
  zoneForm.elements.estimate_note.value = z.estimate_note || '';
  zoneForm.elements.active.checked = z.active !== false;
  zoneForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

async function savePickup(event) {
  event.preventDefault();
  const fd = new FormData(pickupForm);
  try {
    await rpc('admin_preorder_pickup_point_save', {
      p_product_slug: PRODUCT_SLUG,
      p_pickup_code: String(fd.get('pickup_code') || '').trim().toLowerCase(),
      p_label: String(fd.get('label') || '').trim(),
      p_public_address: String(fd.get('public_address') || '').trim() || null,
      p_city: String(fd.get('city') || '').trim() || null,
      p_region: String(fd.get('region') || '').trim() || null,
      p_country_code: String(fd.get('country_code') || 'CA').trim().toUpperCase(),
      p_pickup_window_text: String(fd.get('pickup_window_text') || '').trim() || null,
      p_instructions: String(fd.get('instructions') || '').trim() || null,
      p_active: fd.get('active') === 'on'
    });
    pickupForm.reset();
    pickupForm.elements.country_code.value = 'CA';
    pickupForm.elements.active.checked = true;
    await load();
    showStatus('Point de ramassage enregistré comme brouillon privé. Son adresse n’est pas encore publique.', 'success');
  } catch (error) { showStatus(friendlyBackendMessage(error?.message, 'Impossible d’enregistrer le point de ramassage.'), 'error'); }
}

async function publishPickup(code) {
  if (!confirm('Publier ce point de ramassage ? Son adresse, sa ville et ses instructions deviendront visibles au public. N’utilisez pas une adresse privée si vous ne souhaitez pas la rendre publique.')) return;
  try {
    const ok = await rpc('admin_preorder_pickup_point_publish', { p_product_slug: PRODUCT_SLUG, p_pickup_code: code });
    if (!ok) throw new Error('Une adresse publique et une ville sont obligatoires avant publication.');
    await load();
    showStatus('Point de ramassage publié. Aucun frais de livraison n’est associé au retrait.', 'success');
  } catch (error) { showStatus(friendlyBackendMessage(error?.message, 'Publication refusée.'), 'error'); }
}

function editPickup(code) {
  const p = (state.pickup_points || []).find(x => x.pickup_code === code);
  if (!p || !pickupForm) return;
  pickupForm.elements.pickup_code.value = p.pickup_code || '';
  pickupForm.elements.label.value = p.label || '';
  pickupForm.elements.public_address.value = p.public_address || '';
  pickupForm.elements.city.value = p.city || '';
  pickupForm.elements.region.value = p.region || '';
  pickupForm.elements.country_code.value = p.country_code || 'CA';
  pickupForm.elements.pickup_window_text.value = p.pickup_window_text || '';
  pickupForm.elements.instructions.value = p.instructions || '';
  pickupForm.elements.active.checked = p.active !== false;
  pickupForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function bind() {
  settingsForm?.addEventListener('submit', saveSettings);
  zoneForm?.addEventListener('submit', saveZone);
  pickupForm?.addEventListener('submit', savePickup);
  zoneList?.addEventListener('click', event => {
    const publish = event.target.closest('[data-pf-publish-zone]');
    const edit = event.target.closest('[data-pf-edit-zone]');
    if (publish) publishZone(publish.dataset.pfPublishZone);
    if (edit) editZone(edit.dataset.pfEditZone);
  });
  pickupList?.addEventListener('click', event => {
    const publish = event.target.closest('[data-pf-publish-pickup]');
    const edit = event.target.closest('[data-pf-edit-pickup]');
    if (publish) publishPickup(publish.dataset.pfPublishPickup);
    if (edit) editPickup(edit.dataset.pfEditPickup);
  });
  document.querySelector('[data-pf-admin-refresh]')?.addEventListener('click', async () => {
    await load();
    showStatus('Données de livraison actualisées.', 'success');
  });
}

async function init() {
  ensureReadinessLink();
  bind();
  try {
    await requireAdminAal2();
    await load();
    showStatus('Livraison, ramassage et préparation fiscale chargés. Aucun tarif, point public, transporteur ou paiement n’est activé automatiquement.', 'success');
  } catch (error) {
    if (!['AUTH_REQUIRED','ADMIN_REQUIRED','MFA_REQUIRED'].includes(error?.message)) {
      showStatus(friendlyBackendMessage(error?.message, 'Impossible de charger la gestion de livraison.'), 'error');
    }
  }
}

init();
