import { getSupabase, escapeHtml, friendlyBackendMessage } from './sinjira-supabase.js';

const s = getSupabase();
const statusNode = document.querySelector('[data-legacy-admin-status]');
const requestList = document.querySelector('[data-legacy-request-list]');
const cleanupList = document.querySelector('[data-legacy-cleanup-list]');
const caseSection = document.querySelector('[data-legacy-case-section]');
const caseSummary = document.querySelector('[data-legacy-case-summary]');
const caseActions = document.querySelector('[data-legacy-case-actions]');
const contestsBox = document.querySelector('[data-legacy-contests]');
const versionsBox = document.querySelector('[data-legacy-versions]');
const caseCleanupBox = document.querySelector('[data-legacy-case-cleanup]');
const deliveryOnce = document.querySelector('[data-legacy-delivery-once]');
const state = { user: null, requests: [], detail: null };
const fmt = new Intl.DateTimeFormat('fr-CA', { dateStyle: 'medium', timeStyle: 'short' });

function showStatus(message, kind = '') {
  if (!statusNode) return;
  statusNode.hidden = false;
  statusNode.textContent = message;
  statusNode.dataset.kind = kind;
}
function dt(value) {
  if (!value) return '—';
  try { return fmt.format(new Date(value)); } catch { return '—'; }
}
function statusLabel(value) {
  return ({
    pending: 'Signalement à vérifier', verified: 'Signalement vérifié', verified_hold: 'Délai de sécurité',
    contested: 'Contesté — suspendu', rejected: 'Rejeté', ready_for_export: 'Prêt pour export',
    closed_no_delivery: 'Fermé sans remise', completed: 'Terminé', prepared: 'Instantané préparé',
    generated: 'PDF généré', delivered: 'Remis', revoked: 'Révoqué', purged: 'Purgé',
    open: 'Ouverte', upheld: 'Fondée', dismissed: 'Rejetée', active: 'Actif', ready: 'Prête', draft: 'Brouillon'
  })[value] || value || '—';
}
async function rpc(name, args = {}) {
  const { data, error } = await s.rpc(name, args);
  if (error) throw error;
  return data;
}
async function requireAdminAal2() {
  const { data: { user }, error } = await s.auth.getUser();
  if (error || !user) {
    location.replace('/compte/connexion.html?next=/admin/sinjira/heritage.html');
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
    location.replace(`/compte/mfa.html?security=1&next=${encodeURIComponent('/admin/sinjira/heritage.html')}`);
    throw new Error('MFA_REQUIRED');
  }
  state.user = user;
}

async function loadRequests() {
  const data = await rpc('admin_life_story_pending_requests', { p_limit: 100 });
  state.requests = Array.isArray(data) ? data : [];
  renderRequests();
}
function renderRequests() {
  if (!requestList) return;
  if (!state.requests.length) {
    requestList.innerHTML = '<p>Aucun signalement ou dossier posthume actif.</p>';
    return;
  }
  requestList.innerHTML = state.requests.map((row) => {
    const caseState = row.case_status ? statusLabel(row.case_status) : statusLabel(row.status);
    const hold = row.hold_until ? ` · délai jusqu’au ${escapeHtml(dt(row.hold_until))}` : '';
    const contest = row.has_open_contest ? ' · contestation ouverte' : '';
    const verify = !row.case_id ? `<div class="life-story-form-row" data-verify-box="${row.id}"><div class="field"><label>Date vérifiée</label><input type="date" data-verify-date value="${escapeHtml(row.date_of_death || '')}"/></div><div class="field"><label>Base de vérification</label><select data-verify-basis><option value="official_record">Registre officiel</option><option value="funeral_home">Maison funéraire</option><option value="family_document">Document familial vérifié</option><option value="other_verified">Autre source vérifiée</option></select></div><button class="btn btn-primary" type="button" data-verify-request="${row.id}">Enregistrer la première vérification</button></div>` : '';
    const open = row.case_id ? `<button class="btn btn-secondary" type="button" data-open-case="${row.case_id}">Ouvrir le dossier</button>` : '';
    return `<article class="life-story-item"><div class="life-story-item-head"><div><strong>${escapeHtml(row.subject_display_name || 'Compte SINJIRA')}</strong><p>${escapeHtml(row.relationship_claim || 'Lien non précisé')}</p></div><span class="life-story-pill ${row.has_open_contest ? 'warn' : ''}">${escapeHtml(caseState)}</span></div><p><small>Signalé le ${escapeHtml(dt(row.created_at))}${hold}${contest}</small></p>${verify}<div class="life-story-actions">${open}</div></article>`;
  }).join('');
}

async function verifyRequest(button) {
  const requestId = button.dataset.verifyRequest;
  const box = button.closest('[data-verify-box]');
  const date = box?.querySelector('[data-verify-date]')?.value || '';
  const basis = box?.querySelector('[data-verify-basis]')?.value || '';
  if (!date || !basis) { showStatus('Indiquez la date et la base de vérification.', 'error'); return; }
  if (!confirm('Confirmer cette première vérification humaine ? Un délai incompressible de 30 jours commencera.')) return;
  button.disabled = true;
  try {
    const caseId = await rpc('admin_life_story_verify_death', { p_memorial_request_id: requestId, p_date_of_death: date, p_verification_basis: basis });
    showStatus('Première vérification enregistrée. Le délai de sécurité de 30 jours est actif.', 'success');
    await loadRequests();
    await openCase(caseId);
  } catch (error) { showStatus(friendlyBackendMessage(error?.message, 'La vérification a été refusée.'), 'error'); }
  finally { button.disabled = false; }
}

async function openCase(caseId) {
  state.detail = await rpc('admin_life_story_case_detail', { p_case_id: caseId });
  renderCase();
  if (caseSection) { caseSection.hidden = false; caseSection.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
}
function renderCase() {
  const detail = state.detail || {};
  const c = detail.case || {};
  if (!c.id) return;
  const holdPassed = c.hold_until && new Date(c.hold_until).getTime() <= Date.now();
  if (caseSummary) caseSummary.innerHTML = `<span class="eyebrow">${escapeHtml(statusLabel(c.status))}</span><h3>Dossier posthume</h3><p>Date du décès : <strong>${escapeHtml(c.date_of_death || '—')}</strong></p><p>Base : ${escapeHtml(c.verification_basis || '—')} · première validation ${escapeHtml(dt(c.first_verified_at))}</p><p>Délai de sécurité : ${escapeHtml(dt(c.hold_until))}${holdPassed ? ' · écoulé' : ' · en cours'}</p><p>Deuxième validation : ${escapeHtml(dt(c.second_confirmed_at))}</p>`;
  renderCaseActions(c, holdPassed);
  renderContests(detail.contests || [], c);
  renderVersions(detail.versions || [], detail.exports || [], c);
  renderCaseCleanup(detail.cleanup_tasks || []);
}
function renderCaseActions(c, holdPassed) {
  if (!caseActions) return;
  const actions = [];
  if (c.status === 'verified_hold') {
    actions.push(`<button class="btn btn-primary" type="button" data-confirm-case="${c.id}" ${holdPassed ? '' : 'disabled'}>Deuxième validation humaine</button>`);
    actions.push(`<button class="btn btn-secondary" type="button" data-close-case="${c.id}" ${holdPassed ? '' : 'disabled'}>Fermer sans remise</button>`);
  }
  if (c.status === 'ready_for_export') actions.push(`<button class="btn btn-primary" type="button" data-complete-case="${c.id}">Clore après les remises</button>`);
  caseActions.innerHTML = actions.join('') || '<small>Aucune action de transition disponible pour cet état.</small>';
}
function renderContests(contests, c) {
  if (!contestsBox) return;
  if (!contests.length) { contestsBox.innerHTML = '<p>Aucune contestation.</p>'; return; }
  contestsBox.innerHTML = contests.map((x) => `<article class="life-story-item"><strong>${escapeHtml(statusLabel(x.status))}</strong><p>${escapeHtml(x.reason || '')}</p><small>${escapeHtml(dt(x.submitted_at))}${x.resolution_note ? ` · ${escapeHtml(x.resolution_note)}` : ''}</small>${x.status === 'open' && c.status === 'contested' ? `<div class="life-story-actions"><button class="btn btn-primary" type="button" data-resolve-contest="upheld">Confirmer que la contestation est fondée</button><button class="btn btn-secondary" type="button" data-resolve-contest="dismissed">Rejeter la contestation après vérification</button></div>` : ''}</article>`).join('');
}
function exportFor(versionId, exports) { return exports.find((e) => e.version_id === versionId); }
function renderVersions(versions, exports, c) {
  if (!versionsBox) return;
  if (!versions.length) { versionsBox.innerHTML = '<p>Aucune version Histoire de vie.</p>'; return; }
  versionsBox.innerHTML = versions.map((v) => {
    const exp = exportFor(v.id, exports);
    const eligible = c.status === 'ready_for_export' && v.status === 'ready' && Number(v.recipient_count || 0) > 0 && Number(v.authorized_entry_count || 0) > 0;
    let actions = '';
    if (!exp && eligible) actions = `<button class="btn btn-primary" type="button" data-prepare-export="${v.id}">Préparer l’instantané autorisé</button>`;
    if (exp?.status === 'prepared') actions = `<button class="btn btn-primary" type="button" data-export-action="generate" data-export-id="${exp.id}">Générer le PDF</button>`;
    if (exp?.status === 'generated') actions = `<button class="btn btn-primary" type="button" data-export-action="create_delivery_links" data-export-id="${exp.id}">Créer les liens de remise</button><button class="btn btn-secondary" type="button" data-export-action="revoke" data-export-id="${exp.id}">Révoquer</button>`;
    if (exp?.status === 'delivered') actions = `<button class="btn btn-secondary" type="button" data-export-action="revoke" data-export-id="${exp.id}">Révoquer</button>${exp.purge_after && new Date(exp.purge_after).getTime() <= Date.now() ? `<button class="btn btn-secondary" type="button" data-export-action="purge" data-export-id="${exp.id}">Purger le PDF</button>` : ''}`;
    if (exp?.status === 'revoked' && exp.purge_after && new Date(exp.purge_after).getTime() <= Date.now()) actions = `<button class="btn btn-secondary" type="button" data-export-action="purge" data-export-id="${exp.id}">Purger le PDF</button>`;
    return `<article class="life-story-version"><span class="eyebrow">${escapeHtml(v.audience || '')}</span><h3>${escapeHtml(v.title || v.name || 'Version')}</h3><p>${Number(v.authorized_entry_count || 0)} élément(s) · ${Number(v.recipient_count || 0)} destinataire(s) · version ${escapeHtml(statusLabel(v.status))}</p><p><strong>Export :</strong> ${escapeHtml(exp ? statusLabel(exp.status) : 'non préparé')}${exp?.generated_at ? ` · généré ${escapeHtml(dt(exp.generated_at))}` : ''}${exp?.purge_after ? ` · purge autorisée après ${escapeHtml(dt(exp.purge_after))}` : ''}</p><div class="life-story-actions">${actions || '<small>Aucune action disponible.</small>'}</div></article>`;
  }).join('');
}
function renderCaseCleanup(tasks) {
  if (!caseCleanupBox) return;
  caseCleanupBox.innerHTML = tasks.length ? tasks.map(cleanupCard).join('') : '<p>Aucune tâche de nettoyage pour ce dossier.</p>';
}
function cleanupCard(t) {
  const due = t.due_after && new Date(t.due_after).getTime() <= Date.now();
  return `<article class="life-story-item"><strong>${escapeHtml(t.task_type || 'Revue')}</strong><p>Échéance : ${escapeHtml(dt(t.due_after))} · ${escapeHtml(statusLabel(t.status))}</p>${t.status === 'pending' && due ? `<div class="life-story-actions"><button class="btn btn-primary" type="button" data-cleanup-task="${t.id}" data-cleanup-status="completed">Marquer la revue complétée</button><button class="btn btn-secondary" type="button" data-cleanup-task="${t.id}" data-cleanup-status="skipped">Ignorer cette suppression</button></div>` : '<small>Aucune suppression automatique.</small>'}</article>`;
}

async function confirmCase(caseId) {
  if (!confirm('Effectuer la deuxième validation humaine ? Cette action autorise seulement la préparation des versions déjà approuvées par la personne.')) return;
  await rpc('admin_life_story_confirm_case', { p_case_id: caseId });
  showStatus('Deuxième validation enregistrée. Les versions autorisées peuvent maintenant être préparées.', 'success');
  await openCase(caseId); await loadRequests();
}
async function closeCase(caseId) {
  if (!confirm('Fermer ce dossier sans remise ? Cette action est refusée si des destinataires actifs existent.')) return;
  const note = prompt('Note administrative optionnelle :', '') || '';
  await rpc('admin_life_story_close_without_delivery', { p_case_id: caseId, p_note: note });
  showStatus('Dossier fermé sans remise. Les revues de nettoyage restent humaines.', 'success');
  await openCase(caseId); await loadRequests(); await loadCleanup();
}
async function resolveContest(resolution) {
  const c = state.detail?.case;
  if (!c?.id) return;
  const message = resolution === 'upheld' ? 'Confirmer que la contestation est fondée et rejeter la déclaration de décès ?' : 'Rejeter la contestation après vérification ? Un nouveau délai complet de 30 jours commencera.';
  if (!confirm(message)) return;
  const note = prompt('Note de décision humaine (recommandée) :', '') || '';
  await rpc('admin_life_story_resolve_contest', { p_case_id: c.id, p_resolution: resolution, p_note: note });
  showStatus(resolution === 'upheld' ? 'Contestation confirmée : la procédure posthume est rejetée.' : 'Contestation rejetée : un nouveau délai de 30 jours est actif.', 'success');
  await openCase(c.id); await loadRequests();
}
async function prepareExport(versionId) {
  const c = state.detail?.case;
  if (!c?.id) return;
  if (!confirm('Figer un instantané de cette version ? Seuls les éléments Histoire de vie explicitement autorisés seront copiés.')) return;
  const exportId = await rpc('admin_life_story_prepare_export', { p_case_id: c.id, p_version_id: versionId });
  showStatus('Instantané autorisé préparé. Le Registre n’a pas été interrogé.', 'success');
  await openCase(c.id);
  return exportId;
}
async function exportAction(action, exportId) {
  const labels = { generate: 'Générer le PDF privé ?', create_delivery_links: 'Créer de nouveaux liens de remise ? Les anciens liens seront invalidés.', revoke: 'Révoquer cet export et ses liens ?', purge: 'Purger définitivement le PDF arrivé à échéance ?' };
  if (!confirm(labels[action] || 'Confirmer cette action ?')) return;
  const { data, error } = await s.functions.invoke('life-story-export', { body: { action, export_id: exportId } });
  if (error || !data?.ok) throw new Error(data?.code || data?.error || error?.message || 'EXPORT_ACTION_FAILED');
  if (action === 'create_delivery_links') renderDeliveryLinks(data.links || []);
  showStatus(action === 'generate' ? 'PDF généré dans le stockage privé.' : action === 'create_delivery_links' ? 'Liens créés. Ils sont affichés une seule fois ci-dessous.' : action === 'revoke' ? 'Export et liens révoqués.' : 'PDF purgé.', 'success');
  const c = state.detail?.case; if (c?.id) await openCase(c.id);
}
function renderDeliveryLinks(links) {
  if (!deliveryOnce) return;
  deliveryOnce.hidden = false;
  deliveryOnce.innerHTML = '<strong>Copiez maintenant ces liens de remise. Aucun courriel n’est envoyé automatiquement par SINJIRA.</strong>';
  for (const item of links) {
    const row = document.createElement('div'); row.className = 'life-story-item';
    const label = document.createElement('p'); label.textContent = `${item.recipient_label || 'Destinataire'}${item.recipient_email ? ` · ${item.recipient_email}` : ''} · expire ${dt(item.expires_at)}`;
    const input = document.createElement('input'); input.readOnly = true; input.value = String(item.download_url || ''); input.setAttribute('aria-label', `Lien de remise pour ${item.recipient_label || 'destinataire'}`);
    const copy = document.createElement('button'); copy.type = 'button'; copy.className = 'btn btn-secondary'; copy.textContent = 'Copier le lien';
    copy.addEventListener('click', async () => { try { await navigator.clipboard.writeText(input.value); copy.textContent = 'Copié'; } catch { input.select(); } });
    row.append(label, input, copy); deliveryOnce.append(row);
  }
}
async function completeCase(caseId) {
  if (!confirm('Clore ce dossier ? Toutes les versions ayant des destinataires doivent avoir été traitées.')) return;
  await rpc('admin_life_story_complete_case', { p_case_id: caseId });
  showStatus('Dossier marqué terminé. Les revues de données sources restent séparées et humaines.', 'success');
  await openCase(caseId); await loadRequests(); await loadCleanup();
}
async function completeCleanup(taskId, taskStatus) {
  const note = prompt(taskStatus === 'completed' ? 'Décrivez brièvement la revue effectuée. Cette action ne supprime rien automatiquement :' : 'Pourquoi cette suppression/revue est-elle ignorée ?', '') || '';
  if (!confirm(taskStatus === 'completed' ? 'Marquer cette revue comme complétée ?' : 'Marquer cette tâche comme ignorée ?')) return;
  await rpc('admin_life_story_complete_cleanup_task', { p_task_id: taskId, p_status: taskStatus, p_note: note });
  showStatus('Tâche de nettoyage mise à jour. Aucune suppression automatique n’a été exécutée.', 'success');
  await loadCleanup();
  const c = state.detail?.case; if (c?.id) await openCase(c.id);
}
async function loadCleanup() {
  const data = await rpc('admin_life_story_cleanup_due', { p_limit: 100 });
  const rows = Array.isArray(data) ? data : [];
  if (cleanupList) cleanupList.innerHTML = rows.length ? rows.map((t) => `<article class="life-story-item"><strong>${escapeHtml(t.subject_display_name || 'Compte SINJIRA')}</strong><p>${escapeHtml(t.task_type || '')} · échéance ${escapeHtml(dt(t.due_after))}</p><div class="life-story-actions"><button class="btn btn-primary" type="button" data-cleanup-task="${t.id}" data-cleanup-status="completed">Marquer la revue complétée</button><button class="btn btn-secondary" type="button" data-cleanup-task="${t.id}" data-cleanup-status="skipped">Ignorer</button></div></article>`).join('') : '<p>Aucune tâche arrivée à échéance.</p>';
}

document.addEventListener('click', async (event) => {
  const button = event.target.closest('button'); if (!button) return;
  try {
    if (button.dataset.verifyRequest) await verifyRequest(button);
    else if (button.dataset.openCase) await openCase(button.dataset.openCase);
    else if (button.dataset.confirmCase) await confirmCase(button.dataset.confirmCase);
    else if (button.dataset.closeCase) await closeCase(button.dataset.closeCase);
    else if (button.dataset.resolveContest) await resolveContest(button.dataset.resolveContest);
    else if (button.dataset.prepareExport) await prepareExport(button.dataset.prepareExport);
    else if (button.dataset.exportAction) await exportAction(button.dataset.exportAction, button.dataset.exportId);
    else if (button.dataset.completeCase) await completeCase(button.dataset.completeCase);
    else if (button.dataset.cleanupTask) await completeCleanup(button.dataset.cleanupTask, button.dataset.cleanupStatus);
  } catch (error) {
    showStatus(friendlyBackendMessage(error?.message, 'Opération refusée par le protocole posthume.'), 'error');
  }
});

async function boot() {
  await requireAdminAal2();
  await Promise.all([loadRequests(), loadCleanup()]);
  showStatus('Console Héritage numérique chargée. Toutes les transitions sensibles sont contrôlées côté serveur.', 'success');
}
boot().catch((error) => showStatus(friendlyBackendMessage(error?.message, 'Impossible de charger la console Héritage numérique.'), 'error'));
