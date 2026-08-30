import { getSupabase, escapeHtml, friendlyBackendMessage } from './sinjira-supabase.js';

const s = getSupabase();
const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';

function statusNode() { return document.querySelector('[data-readiness-status]'); }
function setStatus(message, kind = '') {
  const node = statusNode();
  if (!node) return;
  node.hidden = false;
  node.textContent = message;
  node.dataset.kind = kind;
}
function yesNo(value) { return value ? 'Prêt' : 'À compléter'; }
function locked(value) { return value ? 'ERREUR — activé' : 'désactivé'; }
function item(label, ready, detail = '') {
  return `<div class="readiness-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(yesNo(Boolean(ready)))}</strong>${detail ? `<small>${escapeHtml(detail)}</small>` : ''}</div>`;
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
function render(data) {
  const ready = data?.ready_for_future_manual_opening === true;
  const title = document.querySelector('[data-readiness-title]');
  const summary = document.querySelector('[data-readiness-summary]');
  if (title) title.textContent = ready ? 'Préparation complète — ouverture toujours manuelle' : 'Préparation incomplète';
  if (summary) summary.textContent = ready
    ? 'Les prérequis préparatoires sont présents. Vente, checkout et paiement restent néanmoins interdits tant qu’une décision humaine séparée n’est pas prise.'
    : 'Un ou plusieurs prérequis doivent encore être complétés avant même d’envisager une future ouverture manuelle.';

  const grid = document.querySelector('[data-readiness-grid]');
  if (grid) grid.innerHTML = [
    item('Fiche commerciale publiée', data?.commercial_plan_published),
    item('Prix papier publié', data?.paper_price_published),
    item('Prix numérique publié', data?.digital_price_published),
    item('Date de sortie publiée', data?.release_date_published),
    item('Conditions prêtes', data?.terms_ready),
    item('Disponibilité / production prête', data?.availability_ready),
    item('Estimation livraison prête', data?.shipping_estimate_ready, `${Number(data?.published_shipping_zones || 0)} zone(s)`),
    item('Ramassage prêt', data?.pickup_ready, `${Number(data?.published_pickup_points || 0)} point(s)`),
    item('Fiscalité indicative prête', data?.tax_estimate_ready, `${Number(data?.published_tax_profiles || 0)} profil(s)`),
    item('Réception papier prête', data?.paper_fulfillment_ready)
  ].join('');

  const blockers = document.querySelector('[data-readiness-blockers]');
  const rows = Array.isArray(data?.blockers) ? data.blockers.filter(Boolean) : [];
  if (blockers) blockers.innerHTML = rows.length
    ? `<ul class="readiness-blockers">${rows.map((value) => `<li>${escapeHtml(value)}</li>`).join('')}</ul>`
    : '<p class="readiness-ok">Aucun blocage préparatoire détecté. Une autorisation humaine séparée demeure obligatoire avant toute ouverture.</p>';

  const locks = document.querySelector('[data-readiness-locks]');
  if (locks) locks.innerHTML = [
    ['Ventes', locked(Boolean(data?.sales_enabled))],
    ['Checkout', locked(Boolean(data?.checkout_enabled))],
    ['Paiement', locked(Boolean(data?.payment_enabled))],
    ['Livraison externe', locked(Boolean(data?.external_fulfillment_enabled))],
    ['Conversion automatique', locked(Boolean(data?.auto_conversion_allowed))],
    ['API transporteur', locked(Boolean(data?.external_carrier_api_enabled))],
    ['Achat livraison externe', locked(Boolean(data?.external_shipping_purchase_enabled))],
    ['Frais livraison', data?.shipping_customer_pays === true ? 'à la charge du client' : 'ERREUR'],
    ['Ramassage — frais livraison', Number(data?.pickup_shipping_charge_cents || 0) === 0 ? '0 $' : 'ERREUR'],
    ['Taxes calculées par SINJIRA', data?.taxes_calculated_by_sinjira === false ? 'non' : 'ERREUR']
  ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join('');
}
async function load() {
  const button = document.querySelector('[data-readiness-refresh]');
  if (button) button.disabled = true;
  try {
    const { data, error } = await s.rpc('admin_preorder_sale_readiness', { p_product_slug: PRODUCT_SLUG });
    if (error) throw error;
    render(data || {});
    setStatus('Checklist actualisée. Aucune vente, aucun paiement et aucun fournisseur externe n’ont été activés.', 'success');
  } catch (error) {
    setStatus(friendlyBackendMessage(error?.message, 'Impossible de charger la checklist de préparation.'), 'error');
  } finally {
    if (button) button.disabled = false;
  }
}
async function init() {
  document.querySelector('[data-readiness-refresh]')?.addEventListener('click', load);
  try {
    await requireAdminAal2();
    await load();
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') location.replace('/compte/connexion.html?next=/admin/sinjira/precommandes-readiness.html');
    else if (error?.message === 'ADMIN_REQUIRED') location.replace('/compte/index.html');
    else if (error?.message === 'MFA_REQUIRED') location.replace(`/compte/mfa.html?security=1&next=${encodeURIComponent('/admin/sinjira/precommandes-readiness.html')}`);
    else setStatus(friendlyBackendMessage(error?.message, 'Impossible de vérifier l’accès administrateur.'), 'error');
  }
}

init();
