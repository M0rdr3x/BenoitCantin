'use strict';
// Test du VRAI contrôleur Edge SINJIRA, exécuté avec des dépendances simulées.
// Aucune connexion, aucun compte, aucun envoi Formspree ni secret.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const file = path.resolve(__dirname, '..', 'supabase/functions/notify-account-confirmation/index.ts');
const original = fs.readFileSync(file, 'utf8');
const imports = /^import \{[^;\n]+\} from '[^'\n]+';\r?\n/gm;
const matches = [...original.matchAll(imports)];
assert.equal(matches.length, 3, 'La frontière d’importation du contrôleur Edge a changé.');
let source = original.replace(imports, '');
const typedResponse = 'const response=(body:unknown,status=200)=>';
assert.ok(source.includes(typedResponse), 'Le contrat du contrôleur Edge a changé.');
source = source.replace(typedResponse, 'const response=(body,status=200)=>');
let assertions = 0;
function eq(actual, expected, message) {
  assert.equal(actual, expected, message);
  assertions++;
}
async function scenario(options = {}) {
  let handler;
  const calls = { auth: 0, client: 0, formspree: [] };
  const user = {
    id: '10000000-0000-4000-8000-000000000001',
    email: 'synthetic@example.invalid',
    email_confirmed_at: options.confirmed === false ? null : '2026-11-08T00:00:00Z',
    user_metadata: { formspree_receipt_opt_in: options.consent === true }
  };
  const fakeClient = { synthetic: true };
  const context = {
    Deno: { serve(callback) { handler = callback; } },
    Response,
    JSON,
    console: { warn() {} },
    corsHeaders: { 'Access-Control-Allow-Origin': 'https://www.benoitcantin.com' },
    async requiredUser(req) {
      calls.auth++;
      if (options.authError) throw new Error('Jeton invalide : simulé');
      eq(req.method, options.method || 'POST', 'Requête autorisée prévue');
      return user;
    },
    serviceClient() {
      calls.client++;
      return fakeClient;
    },
    async sendFormspreeNotice(service, type, id, data) {
      calls.formspree.push({ service, type, id, data });
      if (options.formspreeError) throw new Error('Transport indisponible : simulé');
      return {
        accepted: options.accepted !== false,
        already: options.already === true,
        configured: true
      };
    }
  };
  vm.runInNewContext(source, context, {
    timeout: 2000, filename: 'notify-account-confirmation/index.ts'
  });
  assert.equal(typeof handler, 'function');
  const response = await handler({ method: options.method || 'POST' });
  const payload = options.method === 'OPTIONS' ? null : await response.json();
  return { response, payload, calls, user, fakeClient };
}
async function main() {
  const get = await scenario({ method: 'GET' });
  eq(get.response.status, 405, 'GET interdit');
  eq(get.payload.code, 'METHOD_NOT_ALLOWED', 'Motif méthode refusée');
  eq(get.calls.auth, 0, 'Pas d’authentification sur GET');
  eq(get.calls.formspree.length, 0, 'Pas de notification sur GET');

  const preflight = await scenario({ method: 'OPTIONS' });
  eq(preflight.response.status, 200, 'Prévol CORS sans POST');
  eq(preflight.calls.auth, 0, 'Prévol sans utilisateur');
  eq(preflight.calls.formspree.length, 0, 'Prévol sans notification');

  const badAuth = await scenario({ authError: true, consent: true });
  eq(badAuth.response.status, 503, 'Echec auth isolé sans livraison');
  eq(badAuth.calls.client, 0, 'Pas de client privilégié sur JWT rejeté');
  eq(badAuth.calls.formspree.length, 0, 'Pas d’avis sur JWT rejeté');

  const unconfirmed = await scenario({ confirmed: false, consent: true });
  eq(unconfirmed.response.status, 403, 'Compte non confirmé bloqué');
  eq(unconfirmed.payload.code, 'EMAIL_NOT_CONFIRMED', 'Motif courriel non confirmé');
  eq(unconfirmed.calls.client, 0, 'Pas de client privilégié sans confirmation');
  eq(unconfirmed.calls.formspree.length, 0, 'Pas d’avis avant confirmation');

  const noConsent = await scenario({ consent: false });
  eq(noConsent.response.status, 200, 'Compte confirmé sans consentement conserve le succès');
  eq(noConsent.payload.notification_sent, false, 'Aucun avis sans consentement');
  eq(noConsent.payload.reason, 'NO_FORMSPREE_CONSENT', 'Refus explicite respecté');
  eq(noConsent.calls.client, 0, 'Pas de client service_role pour non consentant');
  eq(noConsent.calls.formspree.length, 0, 'Aucun POST tiers pour non consentant');

  const allow = await scenario({ consent: true });
  eq(allow.response.status, 200, 'Notification consentante répond 200');
  eq(allow.payload.notification_sent, true, 'Transport simulé accepté');
  eq(allow.payload.already_recorded, false, 'Premier avis');
  eq(allow.calls.client, 1, 'Client privilégié seulement après garde');
  eq(allow.calls.formspree.length, 1, 'Un seul envoi simulé');
  eq(allow.calls.formspree[0].service, allow.fakeClient, 'Le service reçoit le bon client');
  eq(allow.calls.formspree[0].type, 'compte_confirme', 'Type d’avis fixé côté serveur');
  eq(allow.calls.formspree[0].id, allow.user.id, 'Source issue du compte authentifié');
  eq(allow.calls.formspree[0].data.email, allow.user.email, 'Courriel serveur et non corps HTTP');

  const duplicate = await scenario({ consent: true, already: true });
  eq(duplicate.payload.already_recorded, true, 'Un doublon est présenté comme préexistant');
  eq(duplicate.payload.notification_sent, true, 'Avis auparavant accepté conservé');

  const noDelivery = await scenario({ consent: true, accepted: false });
  eq(noDelivery.response.status, 200, 'Échec Formspree ne désactive pas le compte');
  eq(noDelivery.payload.notification_sent, false, 'Échec de livraison non masqué');
  eq(noDelivery.calls.formspree.length, 1, 'Un seul envoi même si refusé');

  const fail = await scenario({ consent: true, formspreeError: true });
  eq(fail.response.status, 503, 'Exception transport transmise comme indisponibilité');
  eq(fail.calls.formspree.length, 1, 'Échec secondaire borné');

  const headers = allow.response.headers;
  eq(headers.get('cache-control'), 'private, no-store, max-age=0', 'Réponse privée non mise en cache');
  eq(headers.get('referrer-policy'), 'no-referrer', 'Référant confidentiel');
  eq(headers.get('x-content-type-options'), 'nosniff', 'Entête nosniff');

  console.log('PASS SINJIRA avis confirmation Edge : ' + assertions +
    ' assertions sur le vrai contrôleur, aucune donnée ni réseau réels.');
}
main().catch(err => { console.error(err); process.exitCode = 1; });
