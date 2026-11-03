#!/usr/bin/env node
// Runtime regression tests for the real administrative MFA guard.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(resolve(root, 'supabase/functions/_shared/auth.ts'), 'utf8');
const start = source.indexOf('async function assertAdminMfa(');
const end = source.indexOf('async function sensitiveStepUpEnabled(', start);
assert.ok(start !== -1 && end > start, 'Admin MFA guard not found');

const implementation = source.slice(start, end).replace(
  'context: Awaited<ReturnType<typeof authenticatedContext>>', 'context'
);
assert.ok(!implementation.includes('nextLevel ==='), 'Conditional AAL2 guard is forbidden');
assert.ok(implementation.includes("aal.currentLevel !== 'aal2'"), 'AAL2 must be mandatory');
assert.ok(implementation.includes("throw new Error('MFA_REQUIRED')"), 'Missing MFA denial');
assert.ok(implementation.includes("if (adminError || !isAdmin)"), 'Admin authorization must precede MFA');

function makeGuard(assuranceLevel) {
  // Evaluate the original function's body, with only its TS parameter annotation
  // removed; the user-facing Edge code is otherwise executed unchanged.
  return new Function('assuranceLevel', implementation + '\nreturn assertAdminMfa;')(assuranceLevel);
}
function context(isAdmin = true, adminError = null) {
  return {
    user: { id: 'subject-for-test' },
    service: { rpc: async (fn, args) => {
      assert.equal(fn, 'is_sinjira_admin');
      assert.deepEqual(args, { p_user_id: 'subject-for-test' });
      return { data: isAdmin, error: adminError };
    } }
  };
}
async function denied(promise, code) {
  await assert.rejects(promise, error => error?.message === code, 'Expected denial: ' + code);
}
async function run() {
  const level = (currentLevel, nextLevel) => ({ currentLevel, nextLevel });
  const guard = makeGuard(async () => level('aal2', 'aal2'));
  assert.equal((await guard(context())).currentLevel, 'aal2');

  // No MFA factor enrolled: must NOT inherit the historic AAL1 admin bypass.
  await denied(makeGuard(async () => level('aal1', 'aal1'))(context()), 'MFA_REQUIRED');
  await denied(makeGuard(async () => level('aal1', 'aal2'))(context()), 'MFA_REQUIRED');
  await denied(makeGuard(async () => level(null, null))(context()), 'MFA_REQUIRED');

  // An Auth provider failure must be fail-closed AND must never expose its
  // original error object (which could contain tokens or personal data).
  const providerLogs = [];
  const previousConsoleError = console.error;
  console.error = (...args) => { providerLogs.push(args); };
  try {
    await denied(
      makeGuard(async () => { throw new Error('SENSITIVE_PROVIDER_ERROR'); })(context()),
      'MFA_STATE_UNAVAILABLE'
    );
  } finally {
    console.error = previousConsoleError;
  }
  assert.deepEqual(providerLogs, [
    ['[SINJIRA admin auth]', { code: 'ADMIN_MFA_STATE_UNAVAILABLE' }]
  ]);


  let consultedAal = false;
  const unauthorized = makeGuard(async () => { consultedAal = true; return level('aal2', 'aal2'); });
  await denied(unauthorized(context(false)), 'ADMIN_REQUIRED');
  await denied(unauthorized(context(true, new Error('database error'))), 'ADMIN_REQUIRED');
  assert.equal(consultedAal, false, 'Non-admin must be refused before MFA/other processing');

  const adminSet = source.match(/const ACTIVE_ADMIN_FUNCTIONS = new Set\(\[([\s\S]*?)\]\);/);
  assert.ok(adminSet, 'Explicit admin route list absent');
  for (const name of ['admin-analytics','admin-console','admin-license-codes','admin-reports','admin-sinjira-v18','admin-social-v20','admin-users']) {
    assert.ok(adminSet[1].includes("'" + name + "'"), 'Admin route unprotected: ' + name);
  }
  const requiredUser = source.slice(source.indexOf('export async function requiredUser('), source.indexOf('export async function requiredVaultUser('));
  assert.match(requiredUser, /ACTIVE_ADMIN_FUNCTIONS\.has\(functionName\)/);
  assert.match(requiredUser, /await assertAdminMfa\(context\)/);
  const requiredAdmin = source.slice(source.indexOf('export async function requiredAdmin('));
  assert.match(requiredAdmin, /await assertAdminMfa\(context\)/);
  console.log('PASS admin AAL2: no-factor and aal1 fail closed; aal2 allowed; non-admin rejected; all admin entry points guarded.');
}
await run();
