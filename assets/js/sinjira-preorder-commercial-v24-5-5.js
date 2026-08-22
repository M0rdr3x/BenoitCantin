import { escapeHtml, getSupabase, isSinjiraBackendConfigured } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const roots = [...document.querySelectorAll('[data-preorder-commercial]')];
const dateFmt = new Intl.DateTimeFormat('fr-CA', { dateStyle: 'long', timeStyle: 'short' });

function money(cents, currency) {
  if (cents === null || cents === undefined) return null;
  try {
    return new Intl.NumberFormat('fr-CA', { style: 'currency', currency: currency || 'CAD' }).format(Number(cents) / 100);
  } catch {
    return `${(Number(cents) / 100).toFixed(2)} ${currency || 'CAD'}`;
  }
}

function date(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '—' : dateFmt.format(d);
}

function locked(info) {
  return info.sales_enabled !== false
    || info.checkout_enabled !== false
    || info.payment_enabled !== false
    || info.external_fulfillment_enabled !== false
    || info.auto_conversion_allowed !== false;
}

function render(root, info) {
  const waiting = root.querySelector('[data-pc-waiting]');
  const published = root.querySelector('[data-pc-published]');
  const error = root.querySelector('[data-pc-error]');
  if (waiting) waiting.hidden = Boolean(info);
  if (published) published.hidden = !info;
  if (error) error.hidden = true;
  if (!info || !published) return;

  if (locked(info)) {
    published.hidden = true;
    if (error) {
      error.hidden = false;
      error.textContent = 'Les informations commerciales sont temporairement indisponibles. Aucune vente n’a été ouverte.';
    }
    return;
  }

  const priceRows = [];
  const paper = money(info.paper_price_cents, info.currency);
  const digital = money(info.digital_price_cents, info.currency);
  if (paper) priceRows.push(`<div><span>${escapeHtml(info.paper_edition_label || 'Édition papier')}</span><strong>${escapeHtml(paper)}</strong></div>`);
  if (digital) priceRows.push(`<div><span>${escapeHtml(info.digital_edition_label || 'Édition numérique')}</span><strong>${escapeHtml(digital)}</strong></div>`);

  const priceNode = root.querySelector('[data-pc-prices]');
  if (priceNode) priceNode.innerHTML = priceRows.join('');
  const releaseNode = root.querySelector('[data-pc-release]');
  if (releaseNode) releaseNode.textContent = date(info.release_at);
  const closeNode = root.querySelector('[data-pc-close]');
  if (closeNode) {
    closeNode.closest('[data-pc-close-row]').hidden = !info.reservation_closes_at;
    closeNode.textContent = date(info.reservation_closes_at);
  }
  const availabilityNode = root.querySelector('[data-pc-availability]');
  if (availabilityNode) {
    availabilityNode.hidden = !info.availability_note;
    availabilityNode.textContent = info.availability_note || '';
  }
  const termsNode = root.querySelector('[data-pc-terms]');
  if (termsNode) termsNode.textContent = info.terms_summary || '';
  const publishedNode = root.querySelector('[data-pc-published-at]');
  if (publishedNode) publishedNode.textContent = date(info.published_at);
}

async function load() {
  if (!roots.length) return;
  if (!isSinjiraBackendConfigured()) {
    roots.forEach(root => render(root, null));
    return;
  }
  try {
    const { data, error } = await getSupabase().rpc('product_preorder_commercial_info', { p_product_slug: PRODUCT_SLUG });
    if (error) throw error;
    const info = Array.isArray(data) ? (data[0] || null) : (data || null);
    roots.forEach(root => render(root, info));
  } catch (err) {
    console.error('[SINJIRA commercial info]', err);
    roots.forEach(root => {
      const waiting = root.querySelector('[data-pc-waiting]');
      const published = root.querySelector('[data-pc-published]');
      const error = root.querySelector('[data-pc-error]');
      if (waiting) waiting.hidden = true;
      if (published) published.hidden = true;
      if (error) {
        error.hidden = false;
        error.textContent = 'Impossible de charger les informations commerciales. Votre réservation demeure inchangée et aucun paiement n’est possible.';
      }
    });
  }
}

load();
