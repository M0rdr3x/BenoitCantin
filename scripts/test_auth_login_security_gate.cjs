'use strict';
// Vérifie le parcours de connexion réel sans réseau, secrets ni compte de test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SOURCE = fs.readFileSync(
  path.join(__dirname, '..', 'assets/js/sinjira-auth-pages.js'), 'utf8'
);
assert.match(SOURCE, /^import \{getSupabase,/);
const body = SOURCE.replace(/^import[^\n]*\n/, '');
const script = new vm.Script('(async function(){\n' + body + '\n})()', {
  filename: 'sinjira-auth-pages.js'
});

async function scenario(response, options = {}) {
  let submit;
  const navigations = [];
  const signOutCalls = [];
  const statuses = [];
  const warnings = [];
  const store = new Map();
  const storage = {
    getItem: key => store.get(key) || null,
    setItem: (key, value) => store.set(key, value),
    removeItem: key => store.delete(key)
  };
  const form = {
    checkValidity: () => true,
    setAttribute: () => {},
    querySelector: () => ({disabled: false}),
    addEventListener: (name, callback) => {
      if (name === 'submit') submit = callback;
    }
  };
  const client = {
    auth: {
      signInWithPassword: async () => ({error: null}),
      signOut: async ({scope}) => {
        signOutCalls.push(scope);
        if (options.signOutThrows) throw new Error('private sign-out failure');
        return {error: options.signOutError ? new Error('private sign-out failure') : null};
      },
      mfa: {getAuthenticatorAssuranceLevel: async () => ({
        data: {nextLevel: 'aal2'}, error: null
      })}
    },
    functions: {
      invoke: async (name) => {
        assert.equal(name, 'security-context');
        if (response instanceof Error) throw response;
        return response;
      }
    }
  };
  const context = {
    document: {
      body: {dataset: {accountPage: 'login'}},
      querySelector: selector => selector === '[data-login-form]' ? form : null
    },
    window: {SINJIRA_AUTH_ROUTE: {next: () => '/compte/index.html'}},
    location: {replace: dest => navigations.push(dest)},
    navigator: {userAgent: 'Test Chrome', platform: 'Testing'},
    crypto: {randomUUID: () => 'synthetic-device-key'},
    localStorage: storage,
    sessionStorage: storage,
    getSupabase: () => client,
    getCurrentUser: async () => null,
    isSinjiraBackendConfigured: () => true,
    SINJIRA_CONFIG: {siteUrl: 'https://example.test'},
    setStatus: (_, message, kind) => statuses.push({message, kind}),
    FormData: class {
      get(key) {
        return key === 'email' ? 'synthetic@example.test' : 'synthetic-password';
      }
    },
    console: {warn: (...values) => warnings.push(values)},
    Uint8Array,
    setTimeout: () => {}
  };
  await script.runInNewContext(context, {timeout: 1500});
  assert.equal(typeof submit, 'function', 'Le flux login doit déclarer son handler');
  await submit({preventDefault() {}});
  for (const args of warnings) {
    assert.equal(args.length, 1, 'Ne jamais journaliser des erreurs Auth ou des objets privés');
    assert.equal(typeof args[0], 'string');
    assert.ok(!args[0].includes('synthetic@example.test'));
    assert.ok(!args[0].includes('private'));
  }
  return {navigations, signOutCalls, statuses, warnings};
}

async function main() {
  let count = 0;
  for (const response of [
    new Error('private network failure synthetic@example.test'),
    {data: null, error: {message: 'private backend message'}},
    {data: {ok: false, error: 'private server error'}},
    {data: {ok: true, security: {}}},
    {data: {ok: true, security: {outcome: 'unexpected'}}},
    {data: {ok: true, security: {outcome: null}}}
  ]) {
    const result = await scenario(response);
    assert.deepEqual(result.navigations, [], 'Le contrôle indéterminé ne doit jamais ouvrir le compte');
    assert.deepEqual(result.signOutCalls, ['local'], 'Révocation locale demandée');
    assert.equal(result.statuses.at(-1)?.kind, 'error', 'Message non technique obligatoire');
    count++;
  }

  const allow = await scenario({data: {ok: true, security: {outcome: 'allow'}}});
  assert.deepEqual(allow.navigations, ['/compte/index.html']);
  assert.deepEqual(allow.signOutCalls, []);
  count++;

  const blocked = await scenario({data: {ok: true, security: {outcome: 'block'}}});
  assert.deepEqual(blocked.navigations, []);
  assert.deepEqual(blocked.signOutCalls, ['local']);
  count++;

  const challenged = await scenario({
    data: {ok: true, security: {outcome: 'challenge', challenge_id: 'synthetic-challenge'}}
  });
  assert.equal(challenged.navigations.length, 1);
  assert.match(challenged.navigations[0], /^\/compte\/mfa\.html\?security=1&next=/);
  assert.deepEqual(challenged.signOutCalls, []);
  count++;

  for (const options of [{signOutThrows: true}, {signOutError: true}]) {
    const unresolved = await scenario(new Error('private unexpected failure'), options);
    assert.deepEqual(unresolved.navigations, []);
    assert.deepEqual(unresolved.signOutCalls, ['local']);
    assert.match(unresolved.statuses.at(-1)?.message || '', /non confirmée/);
    count++;
  }
  console.log('PASS: ' + count + ' scénarios Auth sécurité (fail-closed, redaction, blocage, MFA).');
}

main().catch(error => {
  console.error('FAIL: invariant d’authentification non satisfait', error);
  process.exitCode = 1;
});
