'use strict';
// Tests hors ligne du VRAI helper Edge Formspree : pas de réseau, compte ou secret.
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const sourceId = '10000000-0000-4000-8000-000000000001';
let assertions = 0;
function eq(actual, expected, label) { assert.equal(actual, expected, label); assertions++; }
function yes(value, label) { assert.ok(value, label); assertions++; }
function contains(text, value, label) { yes(text.includes(value), label); }

function fakeLedger({ reserveError = false, lookupError = false, updateError = false, updateNoRow = false } = {}) {
  const rows = new Map(), history = { inserts: [], updates: [], lookups: 0 };
  let sequence = 0;
  const service = {
    from(table) {
      eq(table, 'sinjira_formspree_events', 'Seul le journal serveur est accessible');
      return {
        insert(entry) {
          history.inserts.push({ ...entry });
          return {
            select(column) {
              eq(column, 'id', 'La réservation ne renvoie que son identifiant');
              return {
                async single() {
                  if (reserveError) return { data: null, error: { code: '42501' } };
                  const key = entry.event_type + ':' + entry.source_id;
                  if (rows.has(key)) return { data: null, error: { code: '23505' } };
                  const id = '20000000-0000-4000-8000-' + String(++sequence).padStart(12, '0');
                  rows.set(key, { id, ...entry });
                  return { data: { id }, error: null };
                }
              };
            }
          };
        },
        select(column) {
          eq(column, 'delivery_status', 'Consultation doublon limitée au statut');
          const filter = {};
          return {
            eq(columnName, value) { filter[columnName] = value; return this; },
            async maybeSingle() {
              history.lookups++;
              if (lookupError) return { data: null, error: { code: '42501' } };
              const row = rows.get(filter.event_type + ':' + filter.source_id);
              return { data: row ? { delivery_status: row.delivery_status } : null, error: null };
            }
          };
        },
        update(patch) {
          return {
            eq(columnName, id) {
              eq(columnName, 'id', 'Mise à jour réservée à la ligne idempotente');
              history.updates.push({ id, ...patch });
              return {
                select(column) {
                  eq(column, 'id', 'Vérification SQL limitée à l’identifiant');
                  return {
                    async maybeSingle() {
                      if (updateError) return { data: null, error: { code: '500' } };
                      const row = updateNoRow
                        ? null : [...rows.values()].find(r => r.id === id);
                      if (row) Object.assign(row, patch);
                      return { data: row ? { id: row.id } : null, error: null };
                    }
                  };
                }
              };
            }
          };
        }
      };
    }
  };
  return { service, rows, history };
}

async function main() {
  const helper = pathToFileURL(path.join(__dirname, '..', 'supabase/functions/_shared/sinjira-formspree.ts')).href;
  // Node 22.16: --experimental-strip-types supprime les annotations TS sans les modifier.
  const { sendFormspreeNotice } = await import(helper);
  eq(typeof sendFormspreeNotice, 'function', 'Le vrai helper exporte la fonction');
  const originalFetch = globalThis.fetch;
  let mode = 'ok';
  const requests = [];
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options, fields: JSON.parse(options.body) });
    if (mode === 'network-error') throw new Error('Réseau indisponible, simulé');
    return { ok: mode === 'ok' };
  };
  try {
    const account = fakeLedger();
    const opts = { email: '  DEMO@EXAMPLE.INVALID  ' };
    const first = await sendFormspreeNotice(account.service, 'compte_confirme', sourceId, opts);
    eq(first.accepted, true, 'Formspree 2xx accepté');
    eq(first.already, false, 'Premier avis');
    eq(account.history.updates[0].delivery_status, 'sent', 'Réservation marquée sent');
    eq(requests.length, 1, 'Une seule requête sortante simulée');
    eq(requests[0].url, 'https://formspree.io/f/xzeeqynp', 'URL compte');
    eq(requests[0].options.method, 'POST', 'Méthode contrôlée');
    eq(requests[0].options.redirect, 'error', 'Redirections HTTP refusées');
    eq(requests[0].fields.email, 'demo@example.invalid', 'Adresse normalisée');
    eq(requests[0].fields.event, 'compte_confirme', 'Evénement compte');
    eq(Object.hasOwn(requests[0].fields, 'password'), false, 'Mot de passe absent');
    eq(Object.hasOwn(requests[0].fields, 'questionnaire'), false, 'Pas de questionnaire pour le compte');
    yes(requests[0].fields.reference !== sourceId, 'Référence externe décorrélée du compte');

    const duplicate = await sendFormspreeNotice(account.service, 'compte_confirme', sourceId, opts);
    eq(duplicate.already, true, 'Second avis dédoublonné');
    eq(duplicate.accepted, true, 'Statut antérieur sent pris en compte');
    eq(requests.length, 1, 'Aucun deuxième POST Formspree');

    const registry = fakeLedger();
    const answers = {
      appearance_eyes: 'verts', values: ['loyauté', 'honnêteté'],
      personality_notes: 'Notes fictives', password: 'MOT-DE-PASSE-SIMULÉ',
      code_parental: 'CODE-SIMULÉ', email: 'privé@example.invalid',
      photo: 'photo.jpg', date_naissance: '2000-01-01'
    };
    const registryResult = await sendFormspreeNotice(
      registry.service, 'registre_enregistre', sourceId,
      { email: 'demo@example.invalid', answers }
    );
    eq(registryResult.accepted, true, 'Avis Registre accepté');
    eq(requests.length, 2, 'Un POST supplémentaire pour le Registre distinct');
    eq(requests[1].url, 'https://formspree.io/f/mrppvrwa', 'URL Registre');
    contains(requests[1].fields.questionnaire, 'verts', 'Réponse créative exportée');
    contains(requests[1].fields.questionnaire, 'Notes fictives', 'Notes facultatives exportées');
    for (const forbidden of ['MOT-DE-PASSE-SIMULÉ','CODE-SIMULÉ','privé@example.invalid','photo.jpg','2000-01-01']) {
      eq(requests[1].fields.questionnaire.includes(forbidden), false,
        'Champ privé interdit dans la copie : ' + forbidden);
    }
    eq(requests[1].fields.reference === sourceId, false, 'Référence Registre décorrélée du dossier');

    const noAnswers = await sendFormspreeNotice(
      fakeLedger().service, 'registre_enregistre', sourceId, { email: 'demo@example.invalid', answers: {} }
    );
    eq(noAnswers.accepted, false, 'Registre vide non exporté');
    eq(noAnswers.reason, 'INVALID_QUESTIONNAIRE_EXPORT', 'Motif registre vide');

    const oversize = await sendFormspreeNotice(
      fakeLedger().service, 'registre_enregistre', sourceId,
      { email: 'demo@example.invalid', answers: { personality_notes: 'a'.repeat(30000) } }
    );
    eq(oversize.accepted, false, 'Copie dépassant 28 ko refusée');
    eq(oversize.reason, 'INVALID_QUESTIONNAIRE_EXPORT', 'Motif copie trop volumineuse');

    const invalidEmail = await sendFormspreeNotice(
      fakeLedger().service, 'compte_confirme', sourceId, { email: 'a@example.invalid\r\nBcc:injected' }
    );
    eq(invalidEmail.accepted, false, 'Injection en-tête de courriel refusée');
    eq(invalidEmail.reason, 'INVALID_RECIPIENT_OR_SOURCE', 'Motif email invalide');

    const invalidSource = await sendFormspreeNotice(
      fakeLedger().service, 'compte_confirme', 'not-a-uuid', { email: 'demo@example.invalid' }
    );
    eq(invalidSource.accepted, false, 'Source arbitraire refusée');
    eq(requests.length, 2, 'Aucun POST pendant les quatre rejets');

    mode = 'http-rejected';
    const rejected = fakeLedger();
    const rejectedResult = await sendFormspreeNotice(
      rejected.service, 'compte_confirme', sourceId, { email: 'demo@example.invalid' }
    );
    eq(rejectedResult.accepted, false, 'HTTP non 2xx non accepté');
    eq(rejected.history.updates[0].delivery_status, 'failed', 'HTTP rejeté consigné');
    const failedDuplicate = await sendFormspreeNotice(
      rejected.service, 'compte_confirme', sourceId, { email: 'demo@example.invalid' }
    );
    eq(failedDuplicate.already, true, 'Doublon après échec bloqué');
    eq(failedDuplicate.accepted, false, 'Un échec ne devient pas un succès au rejeu');
    eq(requests.length, 3, 'Pas de deuxième POST malgré échec');

    mode = 'network-error';
    const unreachable = fakeLedger();
    const networkResult = await sendFormspreeNotice(
      unreachable.service, 'compte_confirme', sourceId, { email: 'demo@example.invalid' }
    );
    eq(networkResult.accepted, false, 'Réseau indisponible ne valide pas');
    eq(unreachable.history.updates[0].delivery_status, 'failed', 'Echec réseau consigné');

    mode = 'ok';
    const reserveFailed = await sendFormspreeNotice(
      fakeLedger({ reserveError: true }).service, 'compte_confirme', sourceId,
      { email: 'demo@example.invalid' }
    );
    eq(reserveFailed.reason, 'OUTBOX_RESERVATION_FAILED', 'Erreur journal fail-closed');

    const exception = await sendFormspreeNotice(
      { from() { throw new Error('Base indisponible'); } },
      'compte_confirme', sourceId, { email: 'demo@example.invalid' }
    );
    eq(exception.accepted, false, 'Exception ne déclenche pas une livraison fictive');
    eq(exception.reason, 'SECONDARY_CHANNEL_UNAVAILABLE', 'Exception isolée du parcours principal');

    // Un HTTP 2xx sans confirmation du journal n'est pas une livraison
    // traçable. Le système doit rester non bloquant ET ne jamais rejouer
    // automatiquement une requête qui a peut-être été acceptée.
    const untracked = fakeLedger({ updateError: true });
    const uncertain = await sendFormspreeNotice(
      untracked.service, 'compte_confirme', sourceId,
      { email: 'demo@example.invalid' }
    );
    eq(uncertain.accepted, false, 'HTTP 2xx non certifié si le statut SQL échoue');
    eq(uncertain.reason, 'OUTBOX_STATUS_UPDATE_FAILED', 'Motif de traçabilité absent');
    eq(uncertain.configured, true, 'Canal renseigné mais réponse incertaine');
    eq(untracked.history.updates.length, 1, 'Une seule tentative de statut');
    eq(untracked.rows.values().next().value.delivery_status, 'pending',
      'Ligne reste pending si la mise à jour échoue');
    const countBeforeRetry = requests.length;
    const uncertainDuplicate = await sendFormspreeNotice(
      untracked.service, 'compte_confirme', sourceId,
      { email: 'demo@example.invalid' }
    );
    eq(uncertainDuplicate.already, true, 'Doublon toujours verrouillé après statut incertain');
    eq(uncertainDuplicate.accepted, false, 'Pending ne devient pas un succès fictif');
    eq(requests.length, countBeforeRetry, 'Aucun second POST Formspree après réponse incertaine');

    // PostgREST peut répondre sans erreur à un UPDATE sans aucune ligne modifiée.
    // Le test exige un retour conservateur et aucun réessai risquant un doublon.
    const absentRow = fakeLedger({ updateNoRow: true });
    const notPersisted = await sendFormspreeNotice(
      absentRow.service, 'compte_confirme', sourceId,
      { email: 'demo@example.invalid' }
    );
    eq(notPersisted.accepted, false, 'UPDATE de zéro ligne ne certifie pas la livraison');
    eq(notPersisted.reason, 'OUTBOX_STATUS_UPDATE_FAILED', 'Aucun identifiant mis à jour');
    eq(absentRow.rows.values().next().value.delivery_status, 'pending',
      'Réservation reste pending si zéro ligne mise à jour');
    const noRetryCount = requests.length;
    const noRowAgain = await sendFormspreeNotice(
      absentRow.service, 'compte_confirme', sourceId,
      { email: 'demo@example.invalid' }
    );
    eq(noRowAgain.already, true, 'Réservation précédente bloque le réessai');
    eq(noRowAgain.accepted, false, 'Pas de succès fictif après UPDATE de zéro ligne');
    eq(requests.length, noRetryCount, 'Aucun second POST sur UPDATE de zéro ligne');

    eq(requests.length, 6, 'Nombre exact de POST simulés sans réseau');
    console.log('PASS SINJIRA Formspree : ' + assertions +
      ' assertions sur le vrai module TS, zéro appel réseau externe.');
  } finally {
    globalThis.fetch = originalFetch;
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
