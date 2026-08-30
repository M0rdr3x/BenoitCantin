import { getSupabase, escapeHtml, friendlyBackendMessage } from './sinjira-supabase.js';

const s = getSupabase();
const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const fmt = new Intl.DateTimeFormat('fr-CA', { dateStyle: 'medium', timeStyle: 'short' });
let logisticsRows = [];

function dt(value) {
  if (!value) return 'Jamais modifié';
  try { return fmt.format(new Date(value)); } catch { return '—'; }
}
function workflowLabel(value) {
  return ({
    pending: 'À traiter',
    ready_for_future_contact: 'Prêt pour étape future',
    completed: 'Terminé'
  })[value] || 'À traiter';
}
function formatLabel(value) {
  return ({ paper: 'Papier', digital: 'Numérique', both: 'Papier + numérique', undecided: 'Indécis' })[value] || value || '—';
}
function fulfillmentLabel(value) {
  return ({ shipping: 'Livraison — frais client', pickup: 'Ramassage — 0 $ livraison', undecided: 'À décider' })[value] || value || '—';
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
function installPanel() {
  if (document.querySelector('[data-pa-workflow-panel]')) return;
  const hero = document.querySelector('.preorder-admin-hero');
  if (!hero) return;
  hero.insertAdjacentHTML('afterend', `<section class="section section-tight" data-pa-workflow-panel><div class="container"><article class="account-card preorder-admin-card"><div class="preorder-admin-list-head"><div><span class="eyebrow">V24.5.36 · suivi interne non financier</span><h2>Suivi opérationnel des réservations</h2><p>Ce suivi sert uniquement à organiser le travail administratif. Il ne modifie pas la réservation, n’envoie aucun message, ne crée aucune commande et ne déclenche aucun paiement. Aucune note libre, adresse, courriel ou UUID n’est stocké ici.</p></div><button class="btn btn-secondary" data-pa-workflow-refresh type="button">Actualiser</button></div><div class="preorder-admin-filters"><label>État interne<select data-pa-workflow-filter><option value="">Tous</option><option value="pending">À traiter</option><option value="ready_for_future_contact">Prêt pour étape future</option><option value="completed">Terminé</option></select></label></div><div class="account-status" data-pa-workflow-status hidden></div><div class="preorder-admin-list" data-pa-workflow-list><p>Chargement…</p></div></article></div></section>`);
}
function installLogisticsPanel() {
  if (document.querySelector('[data-pa-logistics-panel]')) return;
  const workflow = document.querySelector('[data-pa-workflow-panel]');
  if (!workflow) return;
  workflow.insertAdjacentHTML('afterend', `<section class="section section-tight" data-pa-logistics-panel><div class="container"><article class="account-card preorder-admin-card"><div class="preorder-admin-list-head"><div><span class="eyebrow">V24.5.39 · préparation logistique locale</span><h2>Préparer les exemplaires sans données privées</h2><p>Cette vue utilise uniquement la référence PR-…, le produit, le format, la quantité, le mode de réception et, si applicable, le nom public du point de retrait. Aucun nom de compte, courriel, adresse, UUID ou donnée de paiement n’est retourné, exporté ou imprimé.</p></div><div class="preorder-announcement-actions"><button class="btn btn-secondary" data-pa-logistics-refresh type="button">Actualiser</button><button class="btn btn-secondary" data-pa-logistics-export type="button" disabled>Exporter CSV local</button><button class="btn btn-secondary" data-pa-logistics-print type="button" disabled>Imprimer feuille locale</button></div></div><div class="preorder-admin-filters"><label>Réservations<select data-pa-logistics-filter><option value="reserved">Actives seulement</option><option value="all">Toutes, incluant annulées</option></select></label></div><div class="preorder-admin-stat-grid"><article class="preorder-admin-stat"><span>Unités papier à prévoir</span><strong data-pa-logistics-paper>0</strong><small>papier ou papier + numérique</small></article><article class="preorder-admin-stat"><span>Livraison</span><strong data-pa-logistics-shipping>0</strong><small>réservations</small></article><article class="preorder-admin-stat"><span>Ramassage</span><strong data-pa-logistics-pickup>0</strong><small>réservations</small></article><article class="preorder-admin-stat"><span>Mode à décider</span><strong data-pa-logistics-undecided>0</strong><small>réservations</small></article></div><div class="account-status" data-pa-logistics-status hidden></div><div class="preorder-admin-list" data-pa-logistics-list><p>Chargement…</p></div><p><small>Le CSV et la feuille imprimable sont créés localement dans votre navigateur. Aucun fichier n’est envoyé vers SINJIRA, un transporteur ou un service externe.</small></p></article></div></section>`);
}
function setStatus(message, kind = '') {
  const node = document.querySelector('[data-pa-workflow-status]');
  if (!node) return;
  node.hidden = false;
  node.textContent = message;
  node.dataset.kind = kind;
}
function setLogisticsStatus(message, kind = '') {
  const node = document.querySelector('[data-pa-logistics-status]');
  if (!node) return;
  node.hidden = false;
  node.textContent = message;
  node.dataset.kind = kind;
}
function renderRows(rows) {
  const list = document.querySelector('[data-pa-workflow-list]');
  if (!list) return;
  if (!rows.length) {
    list.innerHTML = '<div class="preorder-admin-empty">Aucune réservation pour cet état de suivi.</div>';
    return;
  }
  list.innerHTML = rows.map((row) => {
    const reference = String(row.reservation_reference || '').toUpperCase();
    const state = row.workflow_state || 'pending';
    return `<article class="preorder-admin-row" data-pa-workflow-row="${escapeHtml(reference)}"><strong>${escapeHtml(reference)}</strong><span>${escapeHtml(row.user_label || 'Compte SINJIRA')}</span><span>${escapeHtml(row.product_name || 'Livre I')} · ${escapeHtml(formatLabel(row.preferred_format))} · ${escapeHtml(String(row.quantity ?? 1))} exemplaire(s)</span><span>${escapeHtml(fulfillmentLabel(row.fulfillment_preference))}<br><small>Réservation : ${escapeHtml(row.preorder_status || '—')}</small></span><span><label>Suivi interne<select data-pa-workflow-state><option value="pending"${state === 'pending' ? ' selected' : ''}>À traiter</option><option value="ready_for_future_contact"${state === 'ready_for_future_contact' ? ' selected' : ''}>Prêt pour étape future</option><option value="completed"${state === 'completed' ? ' selected' : ''}>Terminé</option></select></label><button class="btn btn-secondary" data-pa-workflow-save type="button">Enregistrer</button><br><small>${escapeHtml(workflowLabel(state))} · ${escapeHtml(dt(row.workflow_updated_at))}</small></span></article>`;
  }).join('');
}
function filteredLogisticsRows() {
  const filter = document.querySelector('[data-pa-logistics-filter]')?.value || 'reserved';
  return filter === 'all' ? logisticsRows : logisticsRows.filter((row) => row.preorder_status === 'reserved');
}
function logisticsSummary(rows) {
  return {
    paperUnits: rows.reduce((sum, row) => sum + (['paper','both'].includes(row.preferred_format) ? Number(row.quantity || 0) : 0), 0),
    shipping: rows.filter((row) => row.fulfillment_preference === 'shipping').length,
    pickup: rows.filter((row) => row.fulfillment_preference === 'pickup').length,
    undecided: rows.filter((row) => !['shipping','pickup'].includes(row.fulfillment_preference)).length
  };
}
function renderLogistics() {
  const rows = filteredLogisticsRows();
  const list = document.querySelector('[data-pa-logistics-list]');
  const summary = logisticsSummary(rows);
  const set = (selector, value) => { const node = document.querySelector(selector); if (node) node.textContent = String(value); };
  set('[data-pa-logistics-paper]', summary.paperUnits);
  set('[data-pa-logistics-shipping]', summary.shipping);
  set('[data-pa-logistics-pickup]', summary.pickup);
  set('[data-pa-logistics-undecided]', summary.undecided);
  const exportButton = document.querySelector('[data-pa-logistics-export]');
  const printButton = document.querySelector('[data-pa-logistics-print]');
  if (exportButton) exportButton.disabled = rows.length === 0;
  if (printButton) printButton.disabled = rows.length === 0;
  if (!list) return;
  if (!rows.length) {
    list.innerHTML = '<div class="preorder-admin-empty">Aucune réservation à préparer pour ce filtre.</div>';
    return;
  }
  list.innerHTML = rows.map((row) => {
    const pickup = row.fulfillment_preference === 'pickup'
      ? [row.pickup_point_label, row.pickup_city].filter(Boolean).join(' · ') || 'Point à confirmer'
      : '—';
    return `<article class="preorder-admin-row"><strong>${escapeHtml(row.reservation_reference || '—')}</strong><span>${escapeHtml(row.product_name || 'Livre I')}</span><span>${escapeHtml(formatLabel(row.preferred_format))} · ${escapeHtml(String(row.quantity ?? 1))} exemplaire(s)</span><span>${escapeHtml(fulfillmentLabel(row.fulfillment_preference))}<br><small>Point : ${escapeHtml(pickup)}</small></span><span>${escapeHtml(workflowLabel(row.workflow_state))}<br><small>Conditions : ${escapeHtml(row.disclosure_version || 'ancienne réservation')} · ${escapeHtml(dt(row.disclosure_acknowledged_at))}</small></span></article>`;
  }).join('');
}
async function loadQueue(message = '') {
  const filter = document.querySelector('[data-pa-workflow-filter]');
  try {
    const rows = await rpc('admin_preorder_workflow_queue', {
      p_workflow_state: filter?.value || null,
      p_limit: 200
    });
    renderRows(Array.isArray(rows) ? rows : []);
    if (message) setStatus(message, 'success');
  } catch (error) {
    setStatus(friendlyBackendMessage(error?.message, 'Impossible de charger le suivi administratif.'), 'error');
  }
}
async function loadLogistics(message = '') {
  try {
    const rows = await rpc('admin_preorder_logistics_queue', { p_product_slug: PRODUCT_SLUG, p_limit: 500 });
    logisticsRows = Array.isArray(rows) ? rows : [];
    renderLogistics();
    if (message) setLogisticsStatus(message, 'success');
  } catch (error) {
    logisticsRows = [];
    renderLogistics();
    setLogisticsStatus(friendlyBackendMessage(error?.message, 'Impossible de charger la préparation logistique.'), 'error');
  }
}
async function saveState(button) {
  const row = button.closest('[data-pa-workflow-row]');
  const reference = String(row?.dataset.paWorkflowRow || '').toUpperCase();
  const select = row?.querySelector('[data-pa-workflow-state]');
  const workflowState = String(select?.value || '');
  if (!/^PR-[0-9A-F]{16}$/.test(reference)) {
    setStatus('Référence de réservation invalide.', 'error');
    return;
  }
  if (!['pending','ready_for_future_contact','completed'].includes(workflowState)) {
    setStatus('État de suivi invalide.', 'error');
    return;
  }
  button.disabled = true;
  try {
    await rpc('admin_preorder_set_workflow_state', {
      p_reservation_reference: reference,
      p_workflow_state: workflowState
    });
    await Promise.all([
      loadQueue(`Suivi ${workflowLabel(workflowState).toLowerCase()} enregistré pour ${reference}. Aucun avis, aucune commande et aucun paiement n’ont été déclenchés.`),
      loadLogistics()
    ]);
  } catch (error) {
    setStatus(friendlyBackendMessage(error?.message, 'Impossible de modifier le suivi administratif.'), 'error');
  } finally {
    button.disabled = false;
  }
}
function csvCell(value) {
  const text = String(value ?? '').replace(/\r?\n/g, ' ');
  return `"${text.replace(/"/g, '""')}"`;
}
function exportLogisticsCsv() {
  const rows = filteredLogisticsRows();
  if (!rows.length) return;
  const header = ['reference','produit','quantite','format','mode_reception','point_retrait','ville_retrait','etat_reservation','etat_suivi','version_conditions','conditions_confirmees_le'];
  const lines = [header.map(csvCell).join(',')];
  for (const row of rows) {
    lines.push([
      row.reservation_reference,
      row.product_name,
      row.quantity,
      formatLabel(row.preferred_format),
      fulfillmentLabel(row.fulfillment_preference),
      row.pickup_point_label || '',
      row.pickup_city || '',
      row.preorder_status || '',
      workflowLabel(row.workflow_state),
      row.disclosure_version || '',
      row.disclosure_acknowledged_at || ''
    ].map(csvCell).join(','));
  }
  const blob = new Blob([`\ufeff${lines.join('\r\n')}`], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const stamp = new Date().toISOString().slice(0,10);
  link.href = url;
  link.download = `sinjira-precommandes-logistique-${stamp}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  setLogisticsStatus(`Export local créé pour ${rows.length} réservation(s). Aucun fichier n’a été envoyé vers un service externe.`, 'success');
}
function printLogisticsSheet() {
  const rows = filteredLogisticsRows();
  if (!rows.length) return;
  const summary = logisticsSummary(rows);
  const scope = document.querySelector('[data-pa-logistics-filter]')?.value === 'all' ? 'Toutes les réservations affichées' : 'Réservations actives seulement';
  const generatedAt = dt(new Date().toISOString());
  const bodyRows = rows.map((row) => {
    const pickup = row.fulfillment_preference === 'pickup'
      ? [row.pickup_point_label, row.pickup_city].filter(Boolean).join(' · ') || 'Point à confirmer'
      : '—';
    return `<tr><td>${escapeHtml(row.reservation_reference || '—')}</td><td>${escapeHtml(row.product_name || 'Livre I')}</td><td>${escapeHtml(String(row.quantity ?? 1))}</td><td>${escapeHtml(formatLabel(row.preferred_format))}</td><td>${escapeHtml(fulfillmentLabel(row.fulfillment_preference))}</td><td>${escapeHtml(pickup)}</td><td>${escapeHtml(workflowLabel(row.workflow_state))}</td><td>${escapeHtml(row.disclosure_version || 'ancienne réservation')}<br><small>${escapeHtml(dt(row.disclosure_acknowledged_at))}</small></td></tr>`;
  }).join('');
  const sheet = `<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>SINJIRA — Feuille logistique locale</title><style>body{font-family:Arial,sans-serif;margin:24px;color:#111}h1{margin:0 0 6px}p{margin:6px 0}.notice{border:1px solid #555;padding:10px;margin:14px 0}.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:16px 0}.summary div{border:1px solid #aaa;padding:8px}.summary strong{display:block;font-size:20px}table{width:100%;border-collapse:collapse;font-size:11px}th,td{border:1px solid #aaa;padding:6px;text-align:left;vertical-align:top}th{background:#eee}@media print{body{margin:10mm}.no-print{display:none}.summary{break-inside:avoid}tr{break-inside:avoid}}</style></head><body><h1>SINJIRA™ — Feuille de préparation logistique</h1><p>Générée localement : ${escapeHtml(generatedAt)} · ${escapeHtml(scope)}</p><div class="notice"><strong>Document interne préparatoire — ce n’est ni une commande ni une preuve de paiement.</strong><br>Livraison : frais à la charge du client. Ramassage : 0 $ de frais de livraison. Aucun nom, courriel, adresse, UUID ou donnée de paiement n’est inclus.</div><div class="summary"><div><span>Unités papier</span><strong>${escapeHtml(String(summary.paperUnits))}</strong></div><div><span>Livraison</span><strong>${escapeHtml(String(summary.shipping))}</strong></div><div><span>Ramassage</span><strong>${escapeHtml(String(summary.pickup))}</strong></div><div><span>À décider</span><strong>${escapeHtml(String(summary.undecided))}</strong></div></div><table><thead><tr><th>Référence</th><th>Produit</th><th>Qté</th><th>Format</th><th>Réception</th><th>Point de retrait</th><th>Suivi</th><th>Conditions</th></tr></thead><tbody>${bodyRows}</tbody></table><p class="no-print"><button type="button" onclick="window.print()">Imprimer / Enregistrer en PDF</button></p></body></html>`;
  const printWindow = window.open('', '_blank', 'width=1100,height=800');
  if (!printWindow) {
    setLogisticsStatus('La fenêtre d’impression a été bloquée par le navigateur. Autorisez les fenêtres contextuelles pour cette page puis réessayez.', 'error');
    return;
  }
  printWindow.document.open();
  printWindow.document.write(sheet);
  printWindow.document.close();
  printWindow.focus();
  setLogisticsStatus(`Feuille locale préparée pour ${rows.length} réservation(s). Aucun fichier n’a été envoyé vers un service externe.`, 'success');
}
function bind() {
  document.querySelector('[data-pa-workflow-refresh]')?.addEventListener('click', () => loadQueue('Suivi actualisé.'));
  document.querySelector('[data-pa-workflow-filter]')?.addEventListener('change', () => loadQueue());
  document.querySelector('[data-pa-workflow-list]')?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-pa-workflow-save]');
    if (button) saveState(button);
  });
  document.querySelector('[data-pa-logistics-refresh]')?.addEventListener('click', () => loadLogistics('Préparation logistique actualisée.'));
  document.querySelector('[data-pa-logistics-filter]')?.addEventListener('change', renderLogistics);
  document.querySelector('[data-pa-logistics-export]')?.addEventListener('click', exportLogisticsCsv);
  document.querySelector('[data-pa-logistics-print]')?.addEventListener('click', printLogisticsSheet);
}
async function init() {
  installPanel();
  installLogisticsPanel();
  bind();
  try {
    await requireAdminAal2();
    await Promise.all([loadQueue(), loadLogistics()]);
  } catch (error) {
    if (error?.message === 'AUTH_REQUIRED') location.replace('/compte/connexion.html?next=/admin/sinjira/precommandes.html');
    else if (error?.message === 'ADMIN_REQUIRED') location.replace('/compte/index.html');
    else if (error?.message === 'MFA_REQUIRED') location.replace(`/compte/mfa.html?security=1&next=${encodeURIComponent('/admin/sinjira/precommandes.html')}`);
    else {
      const message = friendlyBackendMessage(error?.message, 'Impossible de charger le suivi administratif.');
      setStatus(message, 'error');
      setLogisticsStatus(message, 'error');
    }
  }
}

init();