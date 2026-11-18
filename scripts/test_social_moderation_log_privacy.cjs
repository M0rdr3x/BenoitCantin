'use strict';
// Régression des journaux des centres de modération et de sécurité communautaire.
// Simulation locale de réponses RPC privées : aucun compte, réseau ou secret réel.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.resolve(__dirname, '..');
const SENSITIVE = 'private-sentinel@example.invalid token=synthetic-only';
const MODULES = {
  moderation: 'assets/js/sinjira-moderation-appeals-v24-4-90.js',
  safety: 'assets/js/sinjira-social-safety-center-v24-4-79.js'
};
const observed = [];
function stubConsole() {
  return {
    warn(...values) {
      observed.push(values);
    },
    error(...values) {
      observed.push(values);
    }
  };
}
function verifyLogs(label, expectedTag) {
  assert.equal(observed.length, 1, label + ': diagnostic constant attendu');
  assert.deepEqual(observed[0], [expectedTag], label + ': une erreur RPC ne doit jamais sortir dans la console');
  assert.doesNotMatch(JSON.stringify(observed), /private-sentinel|synthetic-only/);
  observed.length = 0;
}
function loadModule(name, injected) {
  const src = fs.readFileSync(path.join(ROOT, MODULES[name]), 'utf8');
  assert.match(src, /^import \{/);
  assert.doesNotMatch(src, /console\.error\s*\(/, name + ': erreur brute dans les traces');
  const body = src.replace(/^import[^\n]*\n/, '');
  const script = new vm.Script(body, {filename: MODULES[name]});
  return script.runInNewContext(injected, {timeout: 1200});
}

async function testModerationRpcFailure() {
  const statuses = [];
  const error = new Error(SENSITIVE);
  const list = {innerHTML: '', querySelectorAll: () => []};
  await loadModule('moderation', {
    document: {querySelector: selector =>
      selector === '[data-moderation-list]' ? list :
      selector === '[data-moderation-status]' ? {} : null
    },
    requireUser: async () => ({id: 'fictional-user'}),
    getSupabase: () => ({rpc: async () => ({data: null, error})}),
    setStatus: (_node, message, kind) => statuses.push({message, kind}),
    escapeHtml: value => String(value),
    formatDate: value => String(value),
    console: stubConsole()
  });
  verifyLogs('moderation', '[SINJIRA moderation appeals unavailable]');
  assert.equal(statuses.at(-1)?.kind, 'error');
  assert.doesNotMatch(JSON.stringify(statuses), /private-sentinel|synthetic-only/);
  assert.match(list.innerHTML, /Impossible de charger/);
}

async function testSafetyInitializationFailure() {
  const status = {hidden: true, dataset: {}, textContent: ''};
  const blocks = {
    innerHTML: '', closest: () => null,
    querySelectorAll: () => []
  };
  const reports = {innerHTML: '', closest: () => null};
  await loadModule('safety', {
    document: {querySelector: selector => ({
      '[data-social-blocks]': blocks,
      '[data-social-reports]': reports,
      '[data-social-safety-status]': status
    })[selector] || null},
    requireUser: async () => ({id: 'fictional-user'}),
    getSupabase: () => ({
      rpc: async () => ({data: null, error: new Error(SENSITIVE)})
    }),
    escapeHtml: value => String(value),
    formatDate: value => String(value),
    console: stubConsole()
  });
  verifyLogs('safety-init', '[SINJIRA social safety initialization failed]');
  assert.equal(status.dataset.statusType, 'error');
  assert.doesNotMatch(status.textContent, /private-sentinel|synthetic-only/);
}

async function testSafetyUnblockFailure() {
  const status = {hidden: true, dataset: {}, textContent: ''};
  let onUnblock = null;
  const button = {
    disabled: false,
    addEventListener: (type, callback) => {
      assert.equal(type, 'click');
      onUnblock = callback;
    }
  };
  const row = {
    dataset: {blockedUser: 'fictional-blocked-user'},
    querySelector: selector => selector === '[data-unblock]' ? button : null
  };
  const blocks = {
    innerHTML: '', closest: () => null,
    querySelectorAll: () => [row]
  };
  const reports = {innerHTML: '', closest: () => null};
  await loadModule('safety', {
    document: {querySelector: selector => ({
      '[data-social-blocks]': blocks,
      '[data-social-reports]': reports,
      '[data-social-safety-status]': status
    })[selector] || null},
    requireUser: async () => ({id: 'fictional-user'}),
    getSupabase: () => ({
      rpc: async name =>
        name === 'social_my_blocks' ? {
          data: [{blocked_user_id: 'fictional-blocked-user', blocked_at: '2026-11-15'}],
          error: null
        } : name === 'social_my_reports' ? {
          data: [], error: null
        } : name === 'social_unblock_user' ? {
          data: null, error: new Error(SENSITIVE)
        } : (() => {throw new Error('RPC inattendue')})()
    }),
    escapeHtml: value => String(value),
    formatDate: value => String(value),
    confirm: () => true,
    console: stubConsole()
  });
  assert.equal(typeof onUnblock, 'function', 'Le gestionnaire de déblocage doit exister');
  await onUnblock();
  verifyLogs('safety-unblock', '[SINJIRA social safety unblock failed]');
  assert.equal(status.dataset.statusType, 'error');
  assert.doesNotMatch(status.textContent, /private-sentinel|synthetic-only/);
  assert.equal(button.disabled, false);
}

async function main() {
  await testModerationRpcFailure();
  await testSafetyInitializationFailure();
  await testSafetyUnblockFailure();
  console.log('PASS: 3 parcours de confidentialité modération/sécurité, aucune erreur RPC privée journalisée.');
}
main().catch(err => {
  console.error('FAIL: contract de confidentialité des traces non respecté', err);
  process.exitCode = 1;
});
