import { escapeHtml, friendlyBackendMessage, getSupabase } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const s = getSupabase();
let host = null;
let form = null;
let list = null;
let statusNode = null;
let state = { profiles: [] };

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
  if (error || !user) throw new Error('AUTH_REQUIRED');
  const { data: isAdmin, error: adminError } = await s.rpc('is_sinjira_admin', { p_user_id: user.id });
  if (adminError || !isAdmin) throw new Error('ADMIN_REQUIRED');
  const { data: aal, error: aalError } = await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if (aalError) throw aalError;
  if (aal?.currentLevel !== 'aal2') throw new Error('MFA_REQUIRED');
}

function percentToBasisPoints(value) {
  const raw = String(value ?? '').trim().replace(',', '.');
  if (!raw) return null;
  if (!/^\d{1,3}(?:\.\d{1,5})?$/.test(raw)) throw new Error('TAX_RATE_INVALID');
  const percent = Number(raw);
  if (!Number.isFinite(percent) || percent < 0 || percent > 100) throw new Error('TAX_RATE_INVALID');
  return Number((percent * 100).toFixed(3));
}

function basisPointsToPercent(value) {
  if (value === null || value === undefined || value === '') return '';
  const n = Number(value);
  if (!Number.isFinite(n)) return '';
  return (n / 100).toFixed(3).replace(/0+$/, '').replace(/\.$/, '').replace('.', ',');
}

function markup() {
  return `<article class="account-card preorder-admin-card" data-preorder-tax-admin>
    <div class="preorder-admin-card-head">
      <div><span class="eyebrow">V24.5.27 · estimation fiscale indicative</span><h2>Profils de taxes à vérifier</h2>
      <p>Ajoutez un taux uniquement après vérification humaine. Une estimation publiée reste informative : elle ne facture rien et ne remplace pas la détermination finale des taxes avant paiement.</p></div>
      <span class="preorder-status-pill">API fiscale externe : désactivée</span>
    </div>
    <div class="account-status" data-ptax-admin-status hidden></div>
    <div class="pf-admin-warning"><strong>Aucun taux automatique.</strong> La source et la date d’effet sont obligatoires avant publication. Toute modification remet le profil en brouillon.</div>
    <form class="account-form pf-admin-form" data-ptax-admin-form>
      <div class="field"><label>Code du profil</label><input name="tax_code" required maxlength="40" placeholder="ex. qc-livres" pattern="[A-Za-z0-9][A-Za-z0-9_-]{1,39}"/></div>
      <div class="field"><label>Nom affiché</label><input name="label" required maxlength="160" placeholder="Ex. Québec — estimation vérifiée"/></div>
      <div class="field"><label>Pays ISO</label><input name="country_code" maxlength="2" placeholder="CA"/></div>
      <div class="field"><label>Province / État</label><input name="subdivision_code" maxlength="24" placeholder="QC"/></div>
      <div class="field"><label>Taux papier (%)</label><input name="paper_rate" inputmode="decimal" placeholder="À vérifier"/><small>Laissez vide si non vérifié.</small></div>
      <div class="field"><label>Taux numérique (%)</label><input name="digital_rate" inputmode="decimal" placeholder="À vérifier"/><small>Peut différer du papier.</small></div>
      <div class="field"><label>Taux livraison (%)</label><input name="shipping_rate" inputmode="decimal" placeholder="À vérifier"/><small>Laissez vide si l’application à la livraison n’est pas confirmée.</small></div>
      <div class="field"><label>Date d’effet</label><input name="effective_on" type="date"/></div>
      <div class="field wide"><label>Source / référence vérifiée</label><input name="source_reference" maxlength="700" placeholder="Titre ou référence publique utilisée pour vérifier le taux"/><small>Aucun document sensible n’est téléversé.</small></div>
      <div class="field wide"><label>Note publique</label><textarea name="estimate_note" maxlength="900" rows="3" placeholder="Précisions utiles sur la portée de l’estimation."></textarea></div>
      <label class="account-check wide"><input name="active" type="checkbox" checked/><span>Profil actif</span></label>
      <div class="wide"><button class="btn btn-secondary" type="submit">Enregistrer en brouillon</button></div>
    </form>
    <div class="pf-admin-list" data-ptax-admin-list></div>
    <p class="preorder-commercial-lockline"><strong>Facturation fiscale : désactivée.</strong> Aucun checkout, paiement ou fournisseur fiscal externe n’est activé par ce module.</p>
  </article>`;
}

function renderList() {
  if (!list) return;
  const rows = Array.isArray(state.profiles) ? state.profiles : [];
  if (!rows.length) {
    list.innerHTML = '<div class="pf-admin-row"><strong>Aucun profil fiscal.</strong><small>Ne créez rien tant que les taux applicables ne sont pas vérifiés.</small></div>';
    return;
  }
  list.innerHTML = rows.map(p => `<article class="pf-admin-row">
    <div class="pf-admin-row-head"><div><strong>${escapeHtml(p.label || p.tax_code)}</strong><div class="pf-admin-row-meta"><span>${escapeHtml(p.tax_code)}</span><span>${escapeHtml([p.country_code,p.subdivision_code].filter(Boolean).join(' · ') || 'zone libre')}</span></div></div><span class="pf-admin-badge ${p.published_at ? 'published' : ''}">${p.published_at ? 'Publié' : 'Brouillon'}</span></div>
    <div class="pf-admin-row-meta"><span>Papier : ${escapeHtml(basisPointsToPercent(p.paper_rate_basis_points) || '—')} %</span><span>Numérique : ${escapeHtml(basisPointsToPercent(p.digital_rate_basis_points) || '—')} %</span><span>Livraison : ${escapeHtml(basisPointsToPercent(p.shipping_rate_basis_points) || '—')} %</span></div>
    <small><b>Effet :</b> ${escapeHtml(p.effective_on || 'non défini')} · <b>Source :</b> ${escapeHtml(p.source_reference || 'non définie')}</small>
    ${p.estimate_note ? `<small>${escapeHtml(p.estimate_note)}</small>` : ''}
    <div class="pf-admin-row-actions"><button class="btn btn-secondary" type="button" data-ptax-edit="${escapeHtml(p.tax_code)}">Modifier</button><button class="btn btn-primary" type="button" data-ptax-publish="${escapeHtml(p.tax_code)}" ${p.published_at ? 'disabled' : ''}>Publier l’estimation</button></div>
  </article>`).join('');
}

async function load() {
  const data = await rpc('admin_preorder_tax_get', { p_product_slug: PRODUCT_SLUG });
  state = data || { profiles: [] };
  if (state.external_tax_api_enabled !== false || state.billing_authoritative !== false) throw new Error('TAX_GUARD_INVALID');
  renderList();
}

function fill(code) {
  const p = (state.profiles || []).find(x => x.tax_code === code);
  if (!p || !form) return;
  form.elements.tax_code.value = p.tax_code || '';
  form.elements.label.value = p.label || '';
  form.elements.country_code.value = p.country_code || '';
  form.elements.subdivision_code.value = p.subdivision_code || '';
  form.elements.paper_rate.value = basisPointsToPercent(p.paper_rate_basis_points);
  form.elements.digital_rate.value = basisPointsToPercent(p.digital_rate_basis_points);
  form.elements.shipping_rate.value = basisPointsToPercent(p.shipping_rate_basis_points);
  form.elements.source_reference.value = p.source_reference || '';
  form.elements.effective_on.value = p.effective_on || '';
  form.elements.estimate_note.value = p.estimate_note || '';
  form.elements.active.checked = p.active !== false;
  form.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

async function save(event) {
  event.preventDefault();
  const fd = new FormData(form);
  const button = form.querySelector('button[type="submit"]');
  if (button) button.disabled = true;
  try {
    await rpc('admin_preorder_tax_profile_save', {
      p_product_slug: PRODUCT_SLUG,
      p_tax_code: String(fd.get('tax_code') || '').trim().toLowerCase(),
      p_label: String(fd.get('label') || '').trim(),
      p_country_code: String(fd.get('country_code') || '').trim().toUpperCase() || null,
      p_subdivision_code: String(fd.get('subdivision_code') || '').trim().toUpperCase() || null,
      p_paper_rate_basis_points: percentToBasisPoints(fd.get('paper_rate')),
      p_digital_rate_basis_points: percentToBasisPoints(fd.get('digital_rate')),
      p_shipping_rate_basis_points: percentToBasisPoints(fd.get('shipping_rate')),
      p_source_reference: String(fd.get('source_reference') || '').trim() || null,
      p_effective_on: String(fd.get('effective_on') || '').trim() || null,
      p_estimate_note: String(fd.get('estimate_note') || '').trim() || null,
      p_active: fd.get('active') === 'on'
    });
    form.reset();
    form.elements.active.checked = true;
    await load();
    showStatus('Profil fiscal enregistré en brouillon. Il n’est pas visible tant qu’il n’est pas publié séparément.', 'success');
  } catch (error) {
    const fallback = error?.message === 'TAX_RATE_INVALID' ? 'Taux invalide : utilisez une valeur entre 0 et 100 %.' : 'Impossible d’enregistrer le profil fiscal.';
    showStatus(friendlyBackendMessage(error?.message, fallback), 'error');
  } finally { if (button) button.disabled = false; }
}

async function publish(code) {
  if (!confirm('Publier ce profil fiscal comme estimation indicative ? Vérifiez la source, la date d’effet et chaque taux. Cette action ne facture rien et n’active aucun paiement.')) return;
  try {
    const ok = await rpc('admin_preorder_tax_profile_publish', { p_product_slug: PRODUCT_SLUG, p_tax_code: code });
    if (!ok) throw new Error('TAX_PROFILE_INCOMPLETE');
    await load();
    showStatus('Profil fiscal publié comme estimation non contractuelle. Les taxes finales devront encore être confirmées avant tout paiement.', 'success');
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Publication refusée : source, date d’effet et au moins un taux vérifié sont requis.'), 'error');
  }
}

function bind() {
  form?.addEventListener('submit', save);
  list?.addEventListener('click', event => {
    const edit = event.target.closest('[data-ptax-edit]');
    const publishButton = event.target.closest('[data-ptax-publish]');
    if (edit) fill(edit.dataset.ptaxEdit);
    if (publishButton) publish(publishButton.dataset.ptaxPublish);
  });
}

async function init() {
  const container = document.querySelector('.preorder-fulfillment-admin .container') || document.querySelector('.preorder-commercial-admin .container');
  if (!container || container.querySelector('[data-preorder-tax-admin]')) return;
  const wrapper = document.createElement('div');
  wrapper.innerHTML = markup();
  host = wrapper.firstElementChild;
  container.appendChild(host);
  form = host.querySelector('[data-ptax-admin-form]');
  list = host.querySelector('[data-ptax-admin-list]');
  statusNode = host.querySelector('[data-ptax-admin-status]');
  bind();
  try {
    await requireAdminAal2();
    await load();
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') location.replace('/compte/connexion.html?next=/admin/sinjira/precommandes.html');
    else if (error?.message === 'ADMIN_REQUIRED') location.replace('/compte/index.html');
    else if (error?.message === 'MFA_REQUIRED') location.replace(`/compte/mfa.html?security=1&next=${encodeURIComponent('/admin/sinjira/precommandes.html')}`);
    else showStatus(friendlyBackendMessage(error?.message, 'Impossible de charger les profils fiscaux.'), 'error');
  }
}

init();
