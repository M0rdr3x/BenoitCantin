'use strict';
// Exécute le VRAI module TOTP de la page sécurité avec une interface simulée.
// Aucun compte réel, requête réseau, code de production ou secret TOTP utilisé.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const modulePath = path.resolve(__dirname, '..', 'assets/js/v24-security.js');
const original = fs.readFileSync(modulePath, 'utf8');
const imported = /^import \{[^;\r\n]+\} from '[^'\r\n]+';\r?\n/;
assert.match(original, imported, 'Import du module sécurisé attendu');
const source = original.replace(imported, '');
let assertions = 0;
function eq(actual, expected, label) {
  assert.equal(actual, expected, label);
  assertions++;
}
function yes(actual, label) {
  assert.ok(actual, label);
  assertions++;
}
function element() {
  const listeners = Object.create(null);
  return {
    listeners, disabled: false, hidden: true, innerHTML: '', textContent: '',
    src: '', alt: '',
    addEventListener(event, fn) { listeners[event] = fn; },
    querySelector(selector) {
      if (selector === '[type="submit"]') return this.submitButton || null;
      return null;
    },
    reset() { this.resetCalled = true; },
    removeAttribute(attribute) { if (attribute === 'src') this.src = ''; }
  };
}
async function scenario(mode) {
  const enroll = element();
  const form = element();
  form.submitButton = element();
  const setup = element();
  const qr = element();
  const secret = element();
  const status = element();
  let factorStatus = 'unverified';
  let enrollCalls = 0, verifyCalls = 0, factorRefresh = 0;
  let releaseVerification = null;
  const messages = [];
  const mfa = {
    async listFactors() {
      factorRefresh++;
      if (mode === 'refresh-failure' && factorStatus === 'verified') {
        throw new Error('Simulated refresh failure');
      }
      return { data: { totp: factorStatus === 'verified'
        ? [{ id: 'TEST_FACTOR_ID', status: 'verified', friendly_name: 'TEST' }]
        : [] }, error: null };
    },
    async getAuthenticatorAssuranceLevel() {
      return { data: { currentLevel: factorStatus === 'verified' ? 'aal2' : 'aal1' }, error: null };
    },
    async enroll() {
      enrollCalls++;
      return { data: {
        id: 'TEST_FACTOR_ID',
        totp: { qr_code: 'data:image/png;base64,FAKE_FOR_TEST', secret: 'TEST_SECRET_NOT_REAL' }
      }, error: null };
    },
    async unenroll() { return { error: null }; },
    async challengeAndVerify({ factorId, code }) {
      verifyCalls++;
      eq(factorId, 'TEST_FACTOR_ID', 'Vérification du facteur appartenant à cette session');
      eq(code, '123456', 'Code fictif issu du formulaire et non de la page');
      if (mode === 'network-error') throw new Error('Simulated network failure');
      if (mode === 'invalid-code') return { error: { message: 'Invalid TOTP' } };
      if (mode === 'slow-success') {
        await new Promise(resolve => { releaseVerification = resolve; });
      }
      factorStatus = 'verified';
      return { data: { access_token: 'FAKE_ACCESS_TOKEN' }, error: null };
    }
  };
  const auth = {
    mfa,
    async getSession() { return { data: { session: { synthetic: true } }, error: null }; }
  };
  const targets = new Map([
    ['[data-mfa-enroll]', enroll],
    ['[data-mfa-enroll-form]', form],
    ['[data-mfa-setup]', setup],
    ['[data-mfa-qr]', qr],
    ['[data-mfa-secret]', secret],
    ['[data-v24-security-status]', status]
  ]);
  const context = {
    document: { querySelector(selector) { return targets.get(selector) || null; } },
    requireUser: async () => ({ email: 'test@example.invalid', email_confirmed_at: '2026-11-09' }),
    getSupabase() { return { auth }; },
    escapeHtml: text => String(text).replace(/&/g, '&amp;'),
    setStatus(node, message, level) {
      eq(node, status, 'Le statut reste dans la page de sécurité');
      messages.push({ message, level });
    },
    FormData: class { constructor(node) { eq(node, form, 'Le code vient du formulaire TOTP'); }
      get(name) { eq(name, 'code', 'Champ code uniquement'); return '123456'; } },
    console: { warn() {} },
    confirm: () => false,
    location: { replace() { throw new Error('No navigation should occur'); } }
  };
  const start = vm.runInNewContext('(async () => {\n' + source + '\n})()', context, {
    filename: 'assets/js/v24-security.js', timeout: 1500
  });
  await start;
  eq(typeof enroll.listeners.click, 'function', 'Démarrage enrollment accessible');
  eq(typeof form.listeners.submit, 'function', 'Vérification manuelle disponible');
  await enroll.listeners.click();
  eq(enrollCalls, 1, 'Un seul enrôlement de test');
  eq(setup.hidden, false, 'Secret temporaire présenté uniquement après enrôlement');
  eq(form.submitButton.disabled, false, 'Code utilisable après enrôlement');
  if (mode === 'slow-success') {
    const inFlight = form.listeners.submit({ preventDefault() {} });
    eq(form.submitButton.disabled, true, 'Challenge initial en cours : bouton verrouillé');
    eq(typeof releaseVerification, 'function', 'Le transport MFA est volontairement en attente');
    await form.listeners.submit({ preventDefault() {} });
    eq(verifyCalls, 1, 'Une seconde soumission ne lance pas un second challenge TOTP');
    eq(form.submitButton.disabled, true, 'Le doublon ne déverrouille pas le premier challenge');
    releaseVerification();
    await inFlight;
  } else {
    await form.listeners.submit({ preventDefault() {} });
  }
  eq(verifyCalls, 1, 'Un seul challengeAndVerify par soumission');
  if (mode === 'network-error') {
    eq(form.submitButton.disabled, false, 'Exception réseau : bouton réactivé');
    eq(setup.hidden, false, 'Exception réseau : conserver le facteur en attente');
    eq(form.resetCalled, undefined, 'Exception réseau : ne pas perdre le code par reset');
    yes(messages.some(x => x.level === 'error' && x.message.includes('temporairement indisponible')),
      'Erreur réseau non exposée et réessai proposé');
    eq(factorStatus, 'unverified', 'Exception réseau : TOTP non confirmé');
    await form.listeners.submit({ preventDefault() {} });
    eq(verifyCalls, 2, 'Une deuxième tentative manuelle est possible');
  } else if (mode === 'invalid-code') {
    eq(form.submitButton.disabled, false, 'Code incorrect : bouton réactivé');
    eq(setup.hidden, false, 'Code incorrect : facteur conservé');
    yes(messages.some(x => x.level === 'error' && x.message.includes('invalide ou expiré')),
      'Message correct sans fuite de détail Auth');
    eq(factorStatus, 'unverified', 'Code incorrect : TOTP non confirmé');
  } else {
    eq(form.submitButton.disabled, false, 'Succès : bouton non bloqué');
    eq(setup.hidden, true, 'Succès : QR et secret ne sont plus affichés');
    eq(qr.src, '', 'QR retiré après vérification');
    eq(secret.textContent, '—', 'Secret TOTP effacé de la page');
    eq(factorStatus, 'verified', 'Seul challengeAndVerify active le facteur');
    if (mode === 'refresh-failure') {
      yes(messages.some(x => x.level === 'info' && x.message.includes('Actualisez la page')),
        'Impossible de rafraîchir : succès de vérification préservé');
    } else {
      yes(messages.some(x => x.level === 'success' && x.message.includes('TOTP activée')),
        'Succès signalé après confirmation réelle');
      yes(factorRefresh >= 3, 'Facteurs rechargés après vérification');
    }
  }
}
async function main() {
  await scenario('network-error');
  await scenario('invalid-code');
  await scenario('success');
  await scenario('refresh-failure');
  await scenario('slow-success');
  console.log('PASS SINJIRA sécurité TOTP : ' + assertions +
    ' assertions exécutées sur le vrai module, sans compte ni réseau.');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
