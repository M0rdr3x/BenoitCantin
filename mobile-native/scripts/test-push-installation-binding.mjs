import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import ts from 'typescript';

const bindingSource = await readFile(new URL('../pushInstallationBinding.ts', import.meta.url), 'utf8');
const appSource = await readFile(new URL('../App.tsx', import.meta.url), 'utf8');

const transpiled = ts.transpileModule(bindingSource, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.CommonJS,
    strict: true,
  },
  reportDiagnostics: true,
});
const compileErrors = (transpiled.diagnostics || []).filter(
  (diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error,
);
assert.equal(compileErrors.length, 0, 'la règle de liaison push doit compiler sans erreur');

const module = { exports: {} };
vm.runInNewContext(transpiled.outputText, { module, exports: module.exports }, {
  filename: 'pushInstallationBinding.runtime.js',
});
const { reusablePushTokenForInstallation } = module.exports;
assert.equal(typeof reusablePushTokenForInstallation, 'function', 'la règle de production doit être exécutable');

const currentDeviceKey = 'device-current';
const token = 'ExponentPushToken[test-current]';

assert.equal(
  reusablePushTokenForInstallation({ optedIn: true, token, boundDeviceKey: currentDeviceKey, currentDeviceKey }),
  token,
  'le token de la même installation peut être réutilisé',
);

for (const scenario of [
  { label: 'restauration héritée sans liaison', optedIn: true, token, boundDeviceKey: '', currentDeviceKey },
  { label: 'restauration depuis un ancien appareil', optedIn: true, token, boundDeviceKey: 'device-old', currentDeviceKey },
  { label: 'opt-in absent', optedIn: false, token, boundDeviceKey: currentDeviceKey, currentDeviceKey },
  { label: 'token absent', optedIn: true, token: '', boundDeviceKey: currentDeviceKey, currentDeviceKey },
  { label: 'clé appareil absente', optedIn: true, token, boundDeviceKey: currentDeviceKey, currentDeviceKey: '' },
]) {
  assert.equal(
    reusablePushTokenForInstallation(scenario),
    '',
    `${scenario.label}: le token technique doit être invalidé`,
  );
}

const requiredAppMarkers = [
  "import { reusablePushTokenForInstallation } from './pushInstallationBinding';",
  "const PUSH_DEVICE_KEY_STORAGE = 'sinjira_security_push_device_key_v1';",
  'const enableSecurityPush = async (quiet = false, deviceKey = nativeDeviceKey) => {',
  "if (!deviceKey) {",
  'SecureStore.setItemAsync(PUSH_TOKEN_STORAGE, token, { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY })',
  'SecureStore.setItemAsync(PUSH_DEVICE_KEY_STORAGE, deviceKey, { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY })',
  'SecureStore.deleteItemAsync(PUSH_DEVICE_KEY_STORAGE)',
  'const storedToken = (await SecureStore.getItemAsync(PUSH_TOKEN_STORAGE)) || \'\';',
  'const boundDeviceKey = (await SecureStore.getItemAsync(PUSH_DEVICE_KEY_STORAGE)) || \'\';',
  'const token = reusablePushTokenForInstallation({',
  'if (!token && (storedToken || boundDeviceKey)) {',
  'if (push && !token) void enableSecurityPush(true, key);',
];
for (const marker of requiredAppMarkers) {
  assert.ok(appSource.includes(marker), `App.tsx doit conserver le contrat de liaison push: ${marker}`);
}

const cleanupStart = appSource.indexOf('if (!token && (storedToken || boundDeviceKey)) {');
assert.notEqual(cleanupStart, -1, 'le nettoyage technique de restauration doit exister');
const cleanupEnd = appSource.indexOf('\n      }', cleanupStart);
assert.notEqual(cleanupEnd, -1, 'le bloc de nettoyage technique doit être borné');
const cleanupBlock = appSource.slice(cleanupStart, cleanupEnd);
assert.ok(cleanupBlock.includes('SecureStore.deleteItemAsync(PUSH_TOKEN_STORAGE)'), 'le token obsolète doit être supprimé');
assert.ok(cleanupBlock.includes('SecureStore.deleteItemAsync(PUSH_DEVICE_KEY_STORAGE)'), 'la liaison obsolète doit être supprimée');
assert.ok(!cleanupBlock.includes('PUSH_OPT_IN_STORAGE'), 'une restauration ne doit jamais effacer le choix utilisateur');

console.log('OK push installation V25: token réutilisé uniquement sur la même installation; restauration et migration invalident les artefacts techniques sans effacer l opt-in.');
