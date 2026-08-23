import './sinjira-admin-preorder-tax-v24-5-27.js';
import { escapeHtml, getSupabase, friendlyBackendMessage } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const s = getSupabase();

function yesNo(value) { return value ? 'Oui' : 'Non'; }
function item(label, value, good = value) { return `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(yesNo(value))}</strong><small>${good ? 'conforme' : 'à compléter'}</small></div>`; }

function renderReadiness(data) {
  const host = document.querySelector('.preorder-commercial-admin .container');
  if (!host) return;
  let card = host.querySelector('[data-preorder-sale-readiness]');
  if (!card) {
    card = document.createElement('article');
    card.className = 'account-card preorder-admin-card';
    card.dataset.preorderSaleReadiness = 'true';
    host.appendChild(card);
  }
  const blockers = Array.isArray(data?.blockers) ? data.blockers : [];
  const ready = data?.ready_for_future_manual_opening === true;
  const flagsLocked = data?.sales_enabled === false && data?.checkout_enabled === false && data?.payment_enabled === false
    && data?.external_fulfillment_enabled === false && data?.auto_conversion_allowed === false
    && data?.external_carrier_api_enabled === false && data?.external_shipping_purchase_enabled === false;

  card.innerHTML = `
    <div class="preorder-admin-card-head"><div><span class="eyebrow">V24.5.26 · garde de préparation</span><h2>Checklist avant toute future ouverture</h2><p>Cette checklist vérifie uniquement si les informations sont assez complètes pour envisager plus tard une ouverture manuelle. <strong>Elle n’ouvre aucune vente, aucun checkout et aucun paiement. Vente toujours désactivée.</strong></p></div><span class="preorder-status-pill" data-state="${ready ? 'ready' : 'draft'}">${ready ? 'Préparation complète' : 'Préparation incomplète'}</span></div>
    <div class="preorder-commercial-checklist">
      ${item('Fiche commerciale publiée', data?.commercial_plan_published === true)}
      ${item('Au moins un prix publié', data?.paper_price_published === true || data?.digital_price_published === true)}
      ${item('Date de sortie publiée', data?.release_date_published === true)}
      ${item('Conditions suffisamment complètes', data?.terms_ready === true)}
      ${item('Disponibilité / production renseignée', data?.availability_ready === true)}
      ${item('Réception papier prête si nécessaire', data?.paper_fulfillment_ready === true)}
      ${item('Profil fiscal indicatif publié', data?.tax_estimate_ready === true)}
      ${item('Frais de livraison à la charge du client', data?.shipping_customer_pays === true)}
      ${item('Verrous vente / paiement / transport externe', flagsLocked)}
      <div><span>Ramassage — frais de livraison</span><strong>${Number(data?.pickup_shipping_charge_cents || 0) === 0 ? '0 $' : 'À corriger'}</strong><small>${Number(data?.pickup_shipping_charge_cents || 0) === 0 ? 'conforme' : 'à compléter'}</small></div>
      <div><span>Taxes calculées dans SINJIRA</span><strong>Non</strong><small>une estimation indicative séparée peut être publiée; les taxes de facturation devront être déterminées avant tout futur paiement</small></div>
    </div>
    <div class="preorder-admin-contract">
      <div><span>Zones de livraison publiées</span><strong>${Number(data?.published_shipping_zones || 0)}</strong></div>
      <div><span>Points de ramassage publiés</span><strong>${Number(data?.published_pickup_points || 0)}</strong></div>
      <div><span>Profils fiscaux publiés</span><strong>${Number(data?.published_tax_profiles || 0)}</strong></div>
      <div><span>Ouverture automatique</span><strong>impossible</strong></div>
      <div><span>Paiement</span><strong>désactivé</strong></div>
    </div>
    ${blockers.length ? `<div class="pf-admin-warning"><strong>Éléments à compléter avant toute future vente :</strong><ul>${blockers.map(x => `<li>${escapeHtml(String(x))}</li>`).join('')}</ul></div>` : '<div class="pf-admin-warning"><strong>Préparation complète :</strong> les informations requises sont présentes, mais la vente reste désactivée et nécessitera une décision humaine séparée.</div>'}
  `;
}

async function loadReadiness() {
  const host = document.querySelector('.preorder-commercial-admin .container');
  if (!host) return;
  try {
    const { data, error } = await s.rpc('admin_preorder_sale_readiness', { p_product_slug: PRODUCT_SLUG });
    if (error) throw error;
    renderReadiness(data || {});
  } catch (error) {
    let card = host.querySelector('[data-preorder-sale-readiness]');
    if (!card) { card = document.createElement('article'); card.className = 'account-card preorder-admin-card'; card.dataset.preorderSaleReadiness = 'true'; host.appendChild(card); }
    card.innerHTML = `<span class="eyebrow">V24.5.26 · garde de préparation</span><h2>Checklist indisponible</h2><p>${escapeHtml(friendlyBackendMessage(error?.message, 'Impossible de charger la checklist de préparation commerciale.'))}</p><p>La vente, le checkout et le paiement restent désactivés.</p>`;
  }
}

window.addEventListener('sinjira:preorder-commercial-updated', loadReadiness);
loadReadiness();
