import { escapeHtml, getSupabase, isSinjiraBackendConfigured } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const s = getSupabase();
const initialized = new WeakSet();

function money(cents, currency = 'CAD') {
  if (cents === null || cents === undefined || !Number.isFinite(Number(cents))) return null;
  try { return new Intl.NumberFormat('fr-CA', { style: 'currency', currency }).format(Number(cents) / 100); }
  catch { return `${(Number(cents) / 100).toFixed(2)} ${currency}`; }
}

function range(min, max, currency) {
  const a = money(min, currency); const b = money(max, currency);
  if (!a || !b) return null;
  return Number(min) === Number(max) ? a : `${a} à ${b}`;
}

async function rpc(name, args = {}) {
  const { data, error } = await s.rpc(name, args);
  if (error) throw error;
  return data;
}

function addUi(summary) {
  const controls = summary.querySelector('.sinjira-cost-summary-controls');
  const grid = summary.querySelector('.sinjira-cost-summary-grid');
  const guard = summary.querySelector('.sinjira-cost-summary-guard');
  if (!controls || !grid) return null;

  const taxControl = document.createElement('label');
  taxControl.dataset.ptaxPublicWrap = 'true';
  taxControl.innerHTML = `Zone fiscale indicative<select data-ptax-public><option value="">Aucune estimation fiscale publiée</option></select><small>Choisissez uniquement un profil publié correspondant à votre situation.</small>`;
  controls.appendChild(taxControl);

  const taxCard = document.createElement('div');
  taxCard.dataset.ptaxTaxCard = 'true';
  taxCard.innerHTML = `<span>Taxes estimées</span><strong data-ptax-tax>Aucune estimation publiée</strong><small data-ptax-tax-note>Les taxes finales devront être vérifiées avant tout paiement.</small>`;
  grid.appendChild(taxCard);

  const totalCard = document.createElement('div');
  totalCard.className = 'sinjira-cost-summary-total';
  totalCard.dataset.ptaxTotalCard = 'true';
  totalCard.innerHTML = `<span>Total indicatif après taxes</span><strong data-ptax-total>Indisponible pour le moment</strong><small data-ptax-total-note>Aucun total fiscal n’est inventé lorsqu’un taux ou un élément du coût manque.</small>`;
  grid.appendChild(totalCard);

  if (guard) guard.innerHTML = `<strong>Réservation ≠ vente.</strong> Aucun paiement n’est prélevé maintenant. L’estimation de livraison est non contractuelle. Une estimation fiscale peut être affichée uniquement lorsqu’un profil vérifié est publié; elle n’est jamais un montant de facturation. Le prix, la livraison, les taxes réellement applicables et le total final devront être présentés puis acceptés séparément avant tout futur paiement.`;

  return {
    select: taxControl.querySelector('[data-ptax-public]'),
    tax: taxCard.querySelector('[data-ptax-tax]'),
    taxNote: taxCard.querySelector('[data-ptax-tax-note]'),
    total: totalCard.querySelector('[data-ptax-total]'),
    totalNote: totalCard.querySelector('[data-ptax-total-note]')
  };
}

function currentControls(summary) {
  return {
    format: String(summary.querySelector('[data-pcs-format]')?.value || 'undecided'),
    quantity: Math.max(1, Math.min(5, Number(summary.querySelector('[data-pcs-quantity]')?.value || 1))),
    method: String(summary.querySelector('[data-pcs-method]')?.value || 'undecided'),
    zone: String(summary.querySelector('[data-pcs-zone]')?.value || '')
  };
}

function resetUi(n, message = 'Aucune estimation fiscale publiée') {
  n.tax.textContent = message;
  n.taxNote.textContent = 'Les taxes finales devront être vérifiées avant tout paiement.';
  n.total.textContent = 'Indisponible pour le moment';
  n.totalNote.textContent = 'Aucun total fiscal n’est inventé lorsqu’un taux ou un élément du coût manque.';
}

async function init(summary) {
  if (initialized.has(summary)) return;
  initialized.add(summary);
  const n = addUi(summary);
  if (!n) return;

  if (!isSinjiraBackendConfigured()) {
    resetUi(n, 'Estimation fiscale temporairement indisponible');
    return;
  }

  let options = null;
  try {
    options = await rpc('product_preorder_tax_options', { p_product_slug: PRODUCT_SLUG });
  } catch (error) {
    console.error('[SINJIRA tax options]', error);
    resetUi(n, 'Estimation fiscale temporairement indisponible');
    return;
  }

  if (options?.external_tax_api_enabled !== false || options?.billing_authoritative !== false || options?.estimate_nonbinding !== true || options?.final_tax_confirmation_required !== true) {
    resetUi(n, 'Estimation fiscale désactivée par sécurité');
    return;
  }

  const profiles = Array.isArray(options?.tax_profiles) ? options.tax_profiles : [];
  n.select.innerHTML = '<option value="">Aucune estimation fiscale sélectionnée</option>' + profiles.map(p =>
    `<option value="${escapeHtml(p.tax_code)}">${escapeHtml(p.label)}${p.effective_on ? ` — effet ${escapeHtml(p.effective_on)}` : ''}</option>`
  ).join('');
  if (profiles.length === 1) n.select.value = profiles[0].tax_code;
  if (!profiles.length) resetUi(n);

  let calculation = 0;
  async function calculate() {
    const id = ++calculation;
    const taxCode = String(n.select.value || '');
    const c = currentControls(summary);
    if (!taxCode) { resetUi(n); return; }
    if (c.format === 'undecided') { resetUi(n, 'Choisissez d’abord un format'); return; }
    if ((c.format === 'paper' || c.format === 'both') && c.method === 'undecided') { resetUi(n, 'Choisissez livraison ou ramassage'); return; }
    if ((c.format === 'paper' || c.format === 'both') && c.method === 'shipping' && !c.zone) { resetUi(n, 'Choisissez une zone de livraison'); return; }

    n.tax.textContent = 'Calcul de l’estimation…';
    n.total.textContent = 'Calcul…';
    try {
      const data = await rpc('product_preorder_tax_estimate', {
        p_product_slug: PRODUCT_SLUG,
        p_tax_code: taxCode,
        p_format: c.format,
        p_quantity: c.quantity,
        p_fulfillment_method: c.method,
        p_shipping_zone_code: c.zone || null
      });
      if (id !== calculation) return;
      const row = Array.isArray(data) ? data[0] : data;
      if (!row || row.estimate_nonbinding !== true || row.billing_authoritative !== false || row.external_tax_api_enabled !== false || row.final_tax_confirmation_required !== true) {
        resetUi(n, 'Estimation fiscale incomplète');
        return;
      }
      if (row.estimate_complete !== true) {
        resetUi(n, 'Estimation fiscale incomplète');
        n.taxNote.textContent = 'Un prix, un taux fiscal ou une estimation de livraison vérifiée manque pour ce choix.';
        return;
      }
      const taxRange = range(row.estimated_tax_min_cents, row.estimated_tax_max_cents, row.currency);
      const totalRange = range(row.estimated_total_min_cents, row.estimated_total_max_cents, row.currency);
      if (!taxRange || !totalRange) { resetUi(n, 'Estimation fiscale incomplète'); return; }
      n.tax.textContent = taxRange;
      n.taxNote.innerHTML = `Estimation non contractuelle — ${escapeHtml(row.tax_label || taxCode)}.${row.effective_on ? ` Effet : ${escapeHtml(row.effective_on)}.` : ''}${row.source_reference ? ` Source vérifiée : ${escapeHtml(row.source_reference)}.` : ''}`;
      n.total.textContent = totalRange;
      n.totalNote.textContent = 'Total indicatif seulement. Les taxes réellement applicables et le montant final devront être confirmés avant toute transaction.';
      if (row.estimate_note) n.totalNote.textContent += ` ${row.estimate_note}`;
    } catch (error) {
      if (id !== calculation) return;
      console.error('[SINJIRA tax estimate]', error);
      resetUi(n, 'Estimation fiscale temporairement indisponible');
    }
  }

  n.select.addEventListener('change', calculate);
  summary.querySelectorAll('[data-pcs-format],[data-pcs-quantity],[data-pcs-method],[data-pcs-zone]').forEach(el => el.addEventListener('change', calculate));
  await calculate();
}

function initAll() {
  const summaries = [...document.querySelectorAll('[data-preorder-cost-summary]')];
  summaries.forEach(init);
  return summaries.length > 0;
}

if (!initAll()) {
  const observer = new MutationObserver(() => {
    if (initAll()) observer.disconnect();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
}
