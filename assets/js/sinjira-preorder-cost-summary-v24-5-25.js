import { escapeHtml, getSupabase, isSinjiraBackendConfigured } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const roots = [...document.querySelectorAll('[data-preorder-fulfillment]')];
const s = getSupabase();
let styleLoaded = false;

function ensureStyle() {
  if (styleLoaded || document.querySelector('link[data-preorder-cost-summary-style]')) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = new URL('../css/sinjira-preorder-cost-summary-v24-5-25.css?v=24.5.25', import.meta.url).href;
  link.dataset.preorderCostSummaryStyle = 'true';
  document.head.appendChild(link);
  styleLoaded = true;
}

function money(cents, currency) {
  if (!Number.isFinite(Number(cents))) return null;
  try {
    return new Intl.NumberFormat('fr-CA', { style: 'currency', currency: currency || 'CAD' }).format(Number(cents) / 100);
  } catch {
    return `${(Number(cents) / 100).toFixed(2)} ${currency || 'CAD'}`;
  }
}

function safeCommercial(info) {
  if (!info) return null;
  if (info.sales_enabled !== false || info.checkout_enabled !== false || info.payment_enabled !== false
      || info.external_fulfillment_enabled !== false || info.auto_conversion_allowed !== false) return null;
  return info;
}

function markup() {
  return `<section class="sinjira-cost-summary" data-preorder-cost-summary aria-labelledby="preorder-cost-summary-title">
    <div class="sinjira-cost-summary-head">
      <span class="eyebrow">V24.5.25 · avant tout futur achat</span>
      <h3 id="preorder-cost-summary-title">Résumé estimatif du coût</h3>
      <p>Voyez ce qui est connu avant de réserver ou d’acheter. <strong>Les frais de livraison seront à la charge du client.</strong> Aucun montant affiché ici n’est prélevé.</p>
    </div>
    <div class="sinjira-cost-summary-controls">
      <label>Format à estimer<select data-pcs-format><option value="undecided">Je déciderai plus tard</option><option value="paper">Papier</option><option value="digital">Numérique</option><option value="both">Papier + numérique</option></select></label>
      <label>Quantité<select data-pcs-quantity><option value="1">1 exemplaire</option><option value="2">2 exemplaires</option><option value="3">3 exemplaires</option><option value="4">4 exemplaires</option><option value="5">5 exemplaires</option></select></label>
      <label>Réception<select data-pcs-method><option value="undecided">Je déciderai plus tard</option><option value="shipping">Livraison — frais à ma charge</option><option value="pickup">Ramassage sur place — 0 $ de frais de livraison</option></select></label>
      <label data-pcs-zone-wrap hidden>Zone de livraison<select data-pcs-zone><option value="">Choisir une zone</option></select></label>
    </div>
    <div class="sinjira-cost-summary-grid" aria-live="polite">
      <div><span>Prix du livre</span><strong data-pcs-book>Prix pas encore annoncé</strong><small data-pcs-book-note>Seul un prix officiellement publié peut être utilisé.</small></div>
      <div><span>Livraison</span><strong data-pcs-shipping>Estimation pas encore disponible</strong><small data-pcs-shipping-note>Le coût final devra être confirmé avant toute future commande.</small></div>
      <div class="sinjira-cost-summary-total"><span>Total estimatif</span><strong data-pcs-total>Total estimatif indisponible pour le moment</strong><small data-pcs-total-note>Aucun total n’est inventé lorsqu’une donnée manque.</small></div>
    </div>
    <p class="sinjira-cost-summary-guard"><strong>Réservation ≠ vente.</strong> Aucun paiement n’est prélevé maintenant. L’estimation de livraison est non contractuelle, aucune adresse exacte n’est demandée pour ce calcul, et le prix/coût final devront être présentés puis acceptés séparément avant un futur achat.</p>
  </section>`;
}

function ui(summary) {
  return {
    format: summary.querySelector('[data-pcs-format]'),
    quantity: summary.querySelector('[data-pcs-quantity]'),
    method: summary.querySelector('[data-pcs-method]'),
    zoneWrap: summary.querySelector('[data-pcs-zone-wrap]'),
    zone: summary.querySelector('[data-pcs-zone]'),
    book: summary.querySelector('[data-pcs-book]'),
    bookNote: summary.querySelector('[data-pcs-book-note]'),
    shipping: summary.querySelector('[data-pcs-shipping]'),
    shippingNote: summary.querySelector('[data-pcs-shipping-note]'),
    total: summary.querySelector('[data-pcs-total]'),
    totalNote: summary.querySelector('[data-pcs-total-note]')
  };
}

async function rpc(name, args = {}) {
  const { data, error } = await s.rpc(name, args);
  if (error) throw error;
  return data;
}

function commercialRow(data) {
  const row = Array.isArray(data) ? (data[0] || null) : (data || null);
  return safeCommercial(row);
}

function bookSubtotal(info, format, quantity) {
  if (!info || format === 'undecided') return null;
  const paper = Number(info.paper_price_cents);
  const digital = Number(info.digital_price_cents);
  if (format === 'paper') return Number.isFinite(paper) ? paper * quantity : null;
  if (format === 'digital') return Number.isFinite(digital) ? digital * quantity : null;
  if (format === 'both') return Number.isFinite(paper) && Number.isFinite(digital) ? (paper + digital) * quantity : null;
  return null;
}

function renderZones(n, options) {
  const zones = Array.isArray(options?.shipping_zones) ? options.shipping_zones : [];
  n.zone.innerHTML = '<option value="">Choisir une zone</option>' + zones.map(z =>
    `<option value="${escapeHtml(z.zone_code)}">${escapeHtml(z.label)}</option>`
  ).join('');
  return zones;
}

async function init(root) {
  ensureStyle();
  const holder = document.createElement('div');
  holder.innerHTML = markup();
  const summary = holder.firstElementChild;
  const grid = root.querySelector('.sinjira-fulfillment-grid');
  if (grid) root.insertBefore(summary, grid);
  else root.appendChild(summary);
  const n = ui(summary);

  if (!isSinjiraBackendConfigured()) {
    n.book.textContent = 'Prix pas encore annoncé';
    n.shipping.textContent = 'Estimation pas encore disponible';
    n.total.textContent = 'Total estimatif indisponible pour le moment';
    return;
  }

  let commercial = null;
  let options = {};
  try {
    const [commercialData, fulfillmentData] = await Promise.all([
      rpc('product_preorder_commercial_info', { p_product_slug: PRODUCT_SLUG }),
      rpc('product_preorder_fulfillment_options', { p_product_slug: PRODUCT_SLUG })
    ]);
    commercial = commercialRow(commercialData);
    options = fulfillmentData || {};
  } catch (error) {
    console.error('[SINJIRA preorder cost summary]', error);
  }
  const zones = renderZones(n, options);
  let calculationId = 0;

  async function calculate() {
    const thisCalculation = ++calculationId;
    const format = String(n.format.value || 'undecided');
    const quantity = Math.max(1, Math.min(5, Number(n.quantity.value || 1)));
    const method = String(n.method.value || 'undecided');
    const includesPhysical = format === 'paper' || format === 'both';
    const digitalOnly = format === 'digital';
    const subtotal = bookSubtotal(commercial, format, quantity);
    const currency = commercial?.currency || null;

    n.zoneWrap.hidden = !(includesPhysical && method === 'shipping' && zones.length > 0);
    if (!n.zoneWrap.hidden && !n.zone.value && zones.length === 1) n.zone.value = zones[0].zone_code;

    if (subtotal === null) {
      n.book.textContent = commercial ? 'Prix non disponible pour ce choix' : 'Prix pas encore annoncé';
      n.bookNote.textContent = commercial ? 'Choisissez un format dont le prix officiel a été publié.' : 'Seul un prix officiellement publié peut être utilisé.';
    } else {
      n.book.textContent = money(subtotal, currency) || 'Prix indisponible';
      n.bookNote.textContent = `Sous-total indicatif pour ${quantity} exemplaire(s), selon le format sélectionné.`;
    }

    let shippingMin = null;
    let shippingMax = null;
    let shippingCurrency = currency;
    let fulfillmentComplete = false;

    if (digitalOnly) {
      shippingMin = 0; shippingMax = 0; fulfillmentComplete = true;
      n.shipping.textContent = '0 $ — livraison non requise';
      n.shippingNote.textContent = 'Le format numérique ne nécessite pas d’expédition physique.';
    } else if (!includesPhysical) {
      n.shipping.textContent = 'Mode de réception à déterminer';
      n.shippingNote.textContent = 'Choisissez d’abord un format papier ou numérique.';
    } else if (method === 'pickup') {
      shippingMin = 0; shippingMax = 0;
      const points = Array.isArray(options?.pickup_points) ? options.pickup_points : [];
      fulfillmentComplete = Boolean(options?.pickup_points_enabled && points.length);
      n.shipping.textContent = '0 $ de frais de livraison';
      n.shippingNote.textContent = fulfillmentComplete
        ? 'Ramassage sur place : utilisez uniquement un point de retrait publié.'
        : 'Option prévue; le lieu de ramassage doit encore être confirmé et publié.';
    } else if (method === 'shipping') {
      if (!options?.shipping_estimates_enabled || !zones.length) {
        n.shipping.textContent = 'Estimation pas encore publiée';
        n.shippingNote.textContent = 'Les frais seront à la charge du client; aucune fourchette fiable n’est publiée actuellement.';
      } else if (!n.zone.value) {
        n.shipping.textContent = 'Choisissez une zone';
        n.shippingNote.textContent = 'Aucune adresse exacte n’est demandée : la zone publiée suffit pour l’estimation.';
      } else {
        n.shipping.textContent = 'Calcul de l’estimation…';
        try {
          const data = await rpc('product_preorder_shipping_estimate', {
            p_product_slug: PRODUCT_SLUG,
            p_zone_code: n.zone.value,
            p_quantity: quantity
          });
          if (thisCalculation !== calculationId) return;
          const row = Array.isArray(data) ? data[0] : data;
          if (row && row.shipping_customer_pays === true && row.estimate_nonbinding === true) {
            shippingMin = Number(row.estimate_min_cents);
            shippingMax = Number(row.estimate_max_cents);
            shippingCurrency = row.currency || currency;
            if (Number.isFinite(shippingMin) && Number.isFinite(shippingMax)) {
              fulfillmentComplete = true;
              n.shipping.textContent = `${money(shippingMin, shippingCurrency)} à ${money(shippingMax, shippingCurrency)}`;
              n.shippingNote.textContent = `Estimation non contractuelle — ${row.zone_label || 'zone publiée'}. Coût final à confirmer avant achat.`;
            }
          }
          if (!fulfillmentComplete) {
            n.shipping.textContent = 'Estimation pas encore disponible';
            n.shippingNote.textContent = 'Aucune estimation publiée et valide n’est disponible pour ce choix.';
          }
        } catch {
          if (thisCalculation !== calculationId) return;
          n.shipping.textContent = 'Estimation temporairement indisponible';
          n.shippingNote.textContent = 'Aucun montant de livraison n’est inventé lorsque le service ne peut pas répondre.';
        }
      }
    } else {
      n.shipping.textContent = 'Choisissez livraison ou ramassage';
      n.shippingNote.textContent = 'Le ramassage, lorsqu’un lieu est publié, ajoute 0 $ de frais de livraison.';
    }

    const sameCurrency = !shippingCurrency || !currency || shippingCurrency === currency;
    if (subtotal !== null && fulfillmentComplete && sameCurrency && Number.isFinite(shippingMin) && Number.isFinite(shippingMax)) {
      const totalMin = subtotal + shippingMin;
      const totalMax = subtotal + shippingMax;
      n.total.textContent = totalMin === totalMax
        ? (money(totalMin, currency || shippingCurrency) || '—')
        : `${money(totalMin, currency || shippingCurrency)} à ${money(totalMax, currency || shippingCurrency)}`;
      n.totalNote.textContent = 'Total estimatif seulement. Le prix et les frais finaux devront être présentés et acceptés avant toute future commande.';
    } else {
      n.total.textContent = 'Total estimatif indisponible pour le moment';
      n.totalNote.textContent = sameCurrency
        ? 'Aucun total n’est inventé lorsqu’un prix, une estimation ou un mode de réception confirmé manque.'
        : 'Les monnaies du prix et de la livraison ne correspondent pas; aucun total n’est calculé.';
    }
  }

  [n.format, n.quantity, n.method, n.zone].forEach(control => control?.addEventListener('change', calculate));
  await calculate();
}

for (const root of roots) init(root);
