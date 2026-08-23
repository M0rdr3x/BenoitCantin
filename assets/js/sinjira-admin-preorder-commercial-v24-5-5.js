import './sinjira-admin-preorder-readiness-v24-5-26.js';
import { getSupabase, friendlyBackendMessage, escapeHtml } from './sinjira-supabase.js';

const PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement';
const s = getSupabase();
const form = document.querySelector('[data-pc-admin-form]');
const statusNode = document.querySelector('[data-pc-admin-status]');
const stateNode = document.querySelector('[data-pc-admin-state]');
const publishedNode = document.querySelector('[data-pc-admin-published]');
const state = { rows: [], working: null, published: null };
const dtFmt = new Intl.DateTimeFormat('fr-CA', { dateStyle: 'medium', timeStyle: 'short' });

function showStatus(message, kind = '') {
  if (!statusNode) return;
  statusNode.hidden = false;
  statusNode.textContent = message;
  statusNode.dataset.kind = kind;
}
function dt(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '—' : dtFmt.format(d);
}
function localDateTime(value) {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function dollars(cents) {
  if (cents === null || cents === undefined) return '';
  return (Number(cents) / 100).toFixed(2).replace('.', ',');
}
function cents(value, fieldName) {
  const raw = String(value || '').trim().replace(',', '.');
  if (!raw) return null;
  if (!/^\d{1,7}(?:\.\d{1,2})?$/.test(raw)) throw new Error(`INVALID_${fieldName}_PRICE`);
  return Math.round(Number(raw) * 100);
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
function statusLabel(status) {
  return ({ draft:'Brouillon', ready:'Prêt à publier', published:'Publié' })[status] || 'Non préparé';
}
function renderPublished() {
  if (!publishedNode) return;
  const p = state.published;
  if (!p) {
    publishedNode.innerHTML = '<p>Aucune information commerciale n’est publiée. Les pages utilisateurs continuent d’indiquer que le prix et la date ne sont pas encore annoncés.</p>';
    return;
  }
  const money = (v) => v === null || v === undefined ? '—' : `${(Number(v)/100).toFixed(2).replace('.', ',')} ${escapeHtml(p.currency || 'CAD')}`;
  publishedNode.innerHTML = `<dl class="preorder-commercial-summary">
    <dt>Révision publiée</dt><dd>${Number(p.revision || 0)}</dd>
    <dt>Sortie annoncée</dt><dd>${escapeHtml(dt(p.release_at))}</dd>
    <dt>Papier</dt><dd>${escapeHtml(p.paper_edition_label || '—')} · ${money(p.paper_price_cents)}</dd>
    <dt>Numérique</dt><dd>${escapeHtml(p.digital_edition_label || '—')} · ${money(p.digital_price_cents)}</dd>
    <dt>Publication</dt><dd>${escapeHtml(dt(p.published_at))}</dd>
  </dl><p class="preorder-commercial-lockline">Vente, checkout, paiement, livraison externe et conversion automatique : <strong>désactivés</strong>.</p>`;
}
function fillForm() {
  if (!form) return;
  const source = state.working || state.published;
  if (!source) {
    form.reset();
    form.elements.currency.value = 'CAD';
    return;
  }
  form.elements.currency.value = source.currency || 'CAD';
  form.elements.paper_price.value = dollars(source.paper_price_cents);
  form.elements.digital_price.value = dollars(source.digital_price_cents);
  form.elements.paper_edition_label.value = source.paper_edition_label || '';
  form.elements.digital_edition_label.value = source.digital_edition_label || '';
  form.elements.release_at.value = localDateTime(source.release_at);
  form.elements.reservation_closes_at.value = localDateTime(source.reservation_closes_at);
  form.elements.availability_note.value = source.availability_note || '';
  form.elements.terms_summary.value = source.terms_summary || '';
}
function render() {
  const working = state.working;
  if (stateNode) {
    stateNode.textContent = working ? `${statusLabel(working.status)} · révision ${working.revision}` : 'Aucun brouillon';
    stateNode.dataset.state = working?.status || 'none';
  }
  const readyBtn = document.querySelector('[data-pc-admin-ready]');
  const publishBtn = document.querySelector('[data-pc-admin-publish]');
  if (readyBtn) readyBtn.disabled = !working || working.status !== 'draft';
  if (publishBtn) publishBtn.disabled = !working || working.status !== 'ready';
  renderPublished();
  fillForm();
}
async function load() {
  const rows = await rpc('admin_preorder_commercial_plan_get', { p_product_slug: PRODUCT_SLUG });
  state.rows = Array.isArray(rows) ? rows : [];
  state.working = state.rows.find(row => row.status === 'draft' || row.status === 'ready') || null;
  state.published = state.rows.find(row => row.status === 'published') || null;
  render();
  window.dispatchEvent(new CustomEvent('sinjira:preorder-commercial-updated'));
}
function args() {
  const fd = new FormData(form);
  const release = String(fd.get('release_at') || '').trim();
  const closes = String(fd.get('reservation_closes_at') || '').trim();
  return {
    p_product_slug: PRODUCT_SLUG,
    p_currency: String(fd.get('currency') || 'CAD').trim().toUpperCase(),
    p_paper_price_cents: cents(fd.get('paper_price'), 'PAPER'),
    p_digital_price_cents: cents(fd.get('digital_price'), 'DIGITAL'),
    p_paper_edition_label: String(fd.get('paper_edition_label') || '').trim() || null,
    p_digital_edition_label: String(fd.get('digital_edition_label') || '').trim() || null,
    p_release_at: release ? new Date(release).toISOString() : null,
    p_reservation_closes_at: closes ? new Date(closes).toISOString() : null,
    p_availability_note: String(fd.get('availability_note') || '').trim() || null,
    p_terms_summary: String(fd.get('terms_summary') || '').trim() || null
  };
}
async function save(event) {
  event.preventDefault();
  const button = document.querySelector('[data-pc-admin-save]');
  if (button) button.disabled = true;
  try {
    const revision = await rpc('admin_preorder_commercial_plan_save', args());
    await load();
    showStatus(`Brouillon commercial révision ${revision} enregistré. Rien n’a été publié et aucun avis n’a été envoyé.`, 'success');
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Impossible d’enregistrer le brouillon commercial.'), 'error');
  } finally {
    if (button) button.disabled = false;
  }
}
async function markReady() {
  if (!state.working || state.working.status !== 'draft') return;
  if (!confirm('Marquer cette fiche commerciale prête ? Elle doit contenir une date de sortie, des conditions et au moins une édition avec son prix. Cela ne publie rien.')) return;
  try {
    const ok = await rpc('admin_preorder_commercial_plan_mark_ready', { p_product_slug: PRODUCT_SLUG });
    if (!ok) throw new Error('COMMERCIAL_PLAN_NOT_FOUND');
    await load();
    showStatus('Fiche commerciale marquée prête. Elle reste privée.', 'success');
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'La fiche commerciale est incomplète ou ne peut pas être marquée prête.'), 'error');
  }
}
async function publish() {
  if (!state.working || state.working.status !== 'ready') return;
  if (!confirm('Publier ces informations de prix, édition et date dans SINJIRA™ ? Cette action reste informative : elle n’ouvre aucune vente, ne crée aucune commande, ne prélève rien et n’envoie aucun avis.')) return;
  try {
    const ok = await rpc('admin_preorder_commercial_plan_publish', { p_product_slug: PRODUCT_SLUG });
    if (!ok) throw new Error('COMMERCIAL_PLAN_NOT_READY');
    await load();
    showStatus('Informations commerciales publiées. Les ventes, paiements et notifications restent désactivés.', 'success');
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'La publication des informations commerciales a été refusée.'), 'error');
  }
}

async function init() {
  if (!form) return;
  form.addEventListener('submit', save);
  document.querySelector('[data-pc-admin-ready]')?.addEventListener('click', markReady);
  document.querySelector('[data-pc-admin-publish]')?.addEventListener('click', publish);
  try {
    await requireAdminAal2();
    await load();
  } catch (error) {
    if (!['AUTH_REQUIRED','ADMIN_REQUIRED','MFA_REQUIRED'].includes(error?.message)) {
      showStatus(friendlyBackendMessage(error?.message, 'Impossible de charger la préparation commerciale.'), 'error');
    }
  }
}

init();
