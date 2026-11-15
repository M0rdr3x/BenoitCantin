'use strict';
// SINJIRA — le vrai script de confirmation est exécuté avec des services simulés.
// Aucun email, compte, jeton réel, secret, navigateur externe ou POST réseau.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const file = path.join(__dirname, '..', 'assets/js/sinjira-confirm-email.js');
const input = fs.readFileSync(file, 'utf8');
const moduleImport = /^import \{[^;\n]+\} from '\.\/sinjira-supabase\.js';\r?\n/;
assert.match(input, moduleImport, 'La frontière du module de confirmation a changé.');
const source = input.replace(moduleImport, '');

function el() {
  return {
    hidden: true, disabled: false, href: '', textContent: '', handlers: {},
    addEventListener(name, callback) { this.handlers[name] = callback; }
  };
}
async function flush() {
  await new Promise(resolve => setImmediate(resolve));
}
async function scenario(options = {}) {
  const confirm = el(), next = el(), resend = el(), resendStatus = el();
  const resendButton = el(), status = el();
  resend.querySelector = () => resendButton;
  resend.reportValidity = () => options.resendValid !== false;
  resend.testEmail = 'test-inerte@example.invalid';
  const lookup = {
    '[data-confirm-status]': status,
    '[data-confirm-button]': confirm,
    '[data-confirm-next]': next,
    '[data-confirm-resend-form]': resend,
    '[data-resend-status]': resendStatus
  };
  const calls = { verify: [], notify: 0, resend: [], getUser: 0, urls: [], statuses: [] };
  const fakeUser = {
    email_confirmed_at: '2026-11-08T00:00:00Z',
    user_metadata: { wants_character_questionnaire: !!options.questionnaire }
  };
  const supabase = {
    auth: {
      async getUser() {
        calls.getUser++;
        return { data: { user: options.existingUser ? fakeUser : null }, error: null };
      },
      async verifyOtp(args) {
        calls.verify.push(args);
        if (options.invalidToken) return { data: null, error: new Error('Jeton expiré') };
        if (options.emptyVerification) return { data: null, error: null };
        if (options.unconfirmedVerification) {
          return { data: { user: { ...fakeUser, email_confirmed_at: null } }, error: null };
        }
        return { data: { user: fakeUser }, error: null };
      },
      async resend(args) {
        calls.resend.push(args);
        if (options.holdResend) {
          await new Promise(resolve => { calls.releaseResend = resolve; });
        }
        return options.resendError
          ? { error: new Error('Limite') } : { error: null };
      }
    },
    functions: {
      async invoke(name) {
        assert.equal(name, 'notify-account-confirmation');
        calls.notify++;
        if (options.notificationError) throw new Error('Formspree indisponible');
        return { data: { ok: true }, error: null };
      }
    }
  };
  const context = {
    URLSearchParams, AbortSignal, location: {
      hash: options.hash || '', pathname: '/compte/confirmer.html'
    },
    history: {
      state: null,
      replaceState(_state, _title, url) { calls.urls.push(url); }
    },
    document: { querySelector(selector) { return lookup[selector] ?? null; } },
    FormData: class {
      constructor(form) { this.form = form; }
      get(name) { return name === 'email' ? this.form.testEmail : null; }
    },
    SINJIRA_CONFIG: { siteUrl: 'https://www.benoitcantin.com' },
    getSupabase() { return supabase; },
    isSinjiraBackendConfigured() { return options.backend !== false; },
    setStatus(target, message, kind) {
      calls.statuses.push({ target, message, kind });
    }
  };
  vm.runInNewContext(source, context, { timeout: 2000, filename: 'sinjira-confirm-email.js' });
  await flush();
  return { confirm, next, resend, resendButton, status, resendStatus, calls };
}

async function main() {
  let assertions = 0;
  const viewed = await scenario({ hash: '#token_hash=synthetic-inert-token&type=email' });
  assert.equal(viewed.calls.verify.length, 0, 'Ouverture automatique du lien a consommé le jeton.');
  assert.equal(viewed.calls.notify, 0, 'Notification avant le clic.');
  assert.equal(viewed.calls.getUser, 0, 'Chargement du lien a changé le parcours.');
  assert.equal(viewed.confirm.hidden, false, 'Bouton de confirmation absent.');
  assertions += 4;

  const confirmed = await scenario({
    hash: '#token_hash=synthetic-inert-token&type=email', questionnaire: true
  });
  await confirmed.confirm.handlers.click();
  assert.equal(confirmed.calls.verify.length, 1);
  assert.equal(confirmed.calls.verify[0].token_hash, 'synthetic-inert-token');
  assert.equal(confirmed.calls.verify[0].type, 'email');
  assert.equal(confirmed.calls.notify, 1);
  assert.deepEqual(confirmed.calls.urls, ['/compte/confirmer.html']);
  assert.equal(confirmed.next.href, '/projets/sinjira/registre/');
  assert.equal(confirmed.next.hidden, false);
  assert.ok(confirmed.calls.statuses.some(x => x.kind === 'success'));
  assertions += 8;

  const unavailable = await scenario({
    hash: '#token_hash=inert&type=signup', notificationError: true
  });
  await unavailable.confirm.handlers.click();
  assert.equal(unavailable.calls.verify.length, 1);
  assert.equal(unavailable.calls.notify, 1);
  assert.equal(unavailable.next.href, '/compte/index.html');
  assert.ok(unavailable.calls.statuses.some(x => x.kind === 'success'),
    'La panne Formspree a annulé une confirmation Auth réussie.');
  assertions += 4;

  const expired = await scenario({
    hash: '#token_hash=inert&type=email', invalidToken: true
  });
  await expired.confirm.handlers.click();
  assert.equal(expired.calls.verify.length, 1);
  assert.equal(expired.calls.notify, 0);
  assert.equal(expired.calls.urls.length, 0);
  assert.ok(expired.calls.statuses.some(x => x.kind === 'error'));
  assertions += 4;

  for (const mode of ['emptyVerification', 'unconfirmedVerification']) {
    const options = { hash: '#token_hash=inert&type=email', [mode]: true };
    const uncertain = await scenario(options);
    await uncertain.confirm.handlers.click();
    assert.equal(uncertain.calls.verify.length, 1, mode + ': le jeton est vérifié une fois');
    assert.equal(uncertain.calls.notify, 0, mode + ': Formspree ne doit pas être appelé');
    assert.equal(uncertain.calls.urls.length, 0, mode + ': fragment conservé avant preuve');
    assert.equal(uncertain.next.hidden, true, mode + ': lien de succès absent');
    assert.equal(uncertain.confirm.hidden, false, mode + ': réessai humain possible');
    assert.equal(uncertain.confirm.disabled, false, mode + ': bouton réactivé');
    assert.ok(uncertain.calls.statuses.some(x => x.kind === 'error'),
      mode + ': l’incertitude ne doit pas être affichée comme un succès');
    assert.ok(!uncertain.calls.statuses.some(x => x.kind === 'success'),
      mode + ': ne pas fabriquer un succès');
    assertions += 8;
  }

  for (const hash of [
    '#token_hash=one&token_hash=two&type=email',
    '#token_hash=one&type=email&type=signup',
    '#token_hash=one&type=email&redirect=https%3A%2F%2Fevil.invalid%2F',
    '#token_hash=&type=email',
    '#token_hash=one'
  ]) {
    const ambiguous = await scenario({ hash, existingUser: true });
    assert.equal(ambiguous.calls.verify.length, 0, 'Lien ambigu vérifié automatiquement');
    assert.equal(ambiguous.calls.getUser, 0, 'Lien ambigu détourné vers le succès de session');
    assert.equal(ambiguous.calls.notify, 0, 'Lien ambigu a déclenché Formspree');
    assert.equal(ambiguous.confirm.hidden, true, 'Lien ambigu a activé le bouton');
    assert.ok(ambiguous.calls.statuses.some(x => x.kind === 'error'),
      'Lien ambigu doit produire un diagnostic non certifié');
    assertions += 5;
  }

  const reordered = await scenario({hash:'#type=email&token_hash=inert'});
  assert.equal(reordered.confirm.hidden, false, 'Ordre inversé des paramètres valides refusé');
  await reordered.confirm.handlers.click();
  assert.equal(reordered.calls.verify.length, 1, 'Un fragment réordonné valide doit fonctionner');
  assert.ok(reordered.calls.statuses.some(x => x.kind === 'success'));
  assertions += 3;

  const badType = await scenario({ hash: '#token_hash=inert&type=recovery' });
  assert.equal(badType.calls.verify.length, 0);
  assert.equal(badType.calls.notify, 0);
  assert.ok(badType.calls.statuses.some(x => x.kind === 'error'));
  assertions += 3;

  const noToken = await scenario();
  assert.equal(noToken.calls.verify.length, 0);
  assert.equal(noToken.calls.notify, 0);
  assert.ok(noToken.calls.statuses.some(x => x.kind === 'error'));
  assertions += 3;

  const already = await scenario({ existingUser: true });
  assert.equal(already.calls.verify.length, 0);
  assert.equal(already.calls.getUser, 1);
  assert.equal(already.calls.notify, 1);
  assert.equal(already.next.href, '/compte/index.html');
  assertions += 4;

  const resend = await scenario();
  let prevented = false;
  await resend.resend.handlers.submit({ preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(resend.calls.resend.length, 1);
  assert.equal(resend.calls.resend[0].type, 'signup');
  assert.equal(resend.calls.resend[0].options.emailRedirectTo,
    'https://www.benoitcantin.com/compte/confirmer.html');
  assert.equal(resend.resendButton.disabled, false);
  assert.ok(resend.calls.statuses.some(x => x.kind === 'success'));
  assertions += 6;

  const repeated = await scenario({ holdResend: true });
  const inertSubmit = () => ({ preventDefault() {} });
  const firstSubmit = repeated.resend.handlers.submit(inertSubmit());
  assert.equal(repeated.calls.resend.length, 1, 'Une demande doit démarrer.');
  assert.equal(repeated.resendButton.disabled, true, 'Renvoi verrouillé durant la requête.');
  await repeated.resend.handlers.submit(inertSubmit());
  assert.equal(repeated.calls.resend.length, 1,
    'Un second événement submit pendant le renvoi a déclenché un doublon.');
  repeated.calls.releaseResend();
  await firstSubmit;
  assert.equal(repeated.resendButton.disabled, false,
    'Le formulaire doit pouvoir réessayer après la réponse.');
  assert.ok(repeated.calls.statuses.some(x => x.kind === 'success'),
    'La requête initiale doit toujours réussir.');
  assertions += 5;

  const refused = await scenario({ resendError: true });
  await refused.resend.handlers.submit(inertSubmit());
  assert.equal(refused.calls.resend.length, 1, 'Une erreur de renvoi compte un essai unique.');
  assert.equal(refused.resendButton.disabled, false, 'Erreur: bouton réactivé.');
  assert.ok(refused.calls.statuses.some(x => x.kind === 'error'),
    'Erreur de limite/réseau présentée sans faux succès.');
  assertions += 3;

  const invalid = await scenario({ resendValid: false });
  await invalid.resend.handlers.submit(inertSubmit());
  assert.equal(invalid.calls.resend.length, 0,
    'Formulaire invalide ne doit jamais lancer la requête.');
  assertions += 1;

  const offline = await scenario({ backend: false });
  await offline.resend.handlers.submit(inertSubmit());
  assert.equal(offline.calls.resend.length, 0,
    'Backend hors ligne: aucune requête même sur submit programmatique.');
  assertions += 1;
  assert.equal(offline.calls.verify.length, 0);
  assert.equal(offline.calls.notify, 0);
  assert.equal(offline.resendButton.disabled, true);
  assertions += 3;
  console.log('PASS SINJIRA confirmation : ' + assertions +
    ' assertions avec le vrai module, aucun réseau, aucun jeton réel.');
}
main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
