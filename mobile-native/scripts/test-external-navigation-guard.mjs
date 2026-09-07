import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import ts from 'typescript';

const appSource = await readFile(new URL('../App.tsx', import.meta.url), 'utf8');

function requireSlice(startMarker, endMarker, label) {
  const start = appSource.indexOf(startMarker);
  assert.notEqual(start, -1, `${label}: marqueur de début introuvable`);
  const end = appSource.indexOf(endMarker, start);
  assert.notEqual(end, -1, `${label}: marqueur de fin introuvable`);
  return appSource.slice(start, end);
}

const protocolLine = requireSlice(
  "const EXTERNAL_SAFE_PROTOCOLS = new Set(['https:', 'mailto:', 'tel:']);",
  '\n',
  'allowlist protocoles',
);
const sensitiveParams = requireSlice(
  'const SENSITIVE_EXTERNAL_PARAMS = new Set([',
  '\n]);',
  'paramètres sensibles',
) + '\n]);';
const guardFunctions = requireSlice(
  'function containsSensitiveExternalAssignment(value: string)',
  '\nfunction isVaultUrl',
  'garde externe',
);

const guardSource = `${protocolLine}\n${sensitiveParams}\n${guardFunctions}\n` +
  `(globalThis as any).__sinjiraExternalGuard = { ` +
  `EXTERNAL_SAFE_PROTOCOLS, containsSensitiveExternalAssignment, hasSensitiveExternalMaterial };`;

const transpiled = ts.transpileModule(guardSource, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022,
    strict: true,
  },
  reportDiagnostics: true,
});

const compileErrors = (transpiled.diagnostics || []).filter(
  (diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error,
);
assert.equal(compileErrors.length, 0, 'le garde extrait de App.tsx doit compiler sans erreur');

const sandbox = {
  URL,
  URLSearchParams,
  decodeURIComponent,
  console,
};
vm.runInNewContext(transpiled.outputText, sandbox, {
  filename: 'App.external-navigation-guard.runtime.js',
});

const guard = sandbox.__sinjiraExternalGuard;
assert.ok(guard, 'le garde runtime extrait doit être disponible');
const {
  EXTERNAL_SAFE_PROTOCOLS,
  containsSensitiveExternalAssignment,
  hasSensitiveExternalMaterial,
} = guard;

function externalPolicyAllows(rawUrl) {
  const parsed = new URL(rawUrl);
  return EXTERNAL_SAFE_PROTOCOLS.has(parsed.protocol) && !hasSensitiveExternalMaterial(parsed);
}

for (const protocol of ['https:', 'mailto:', 'tel:']) {
  assert.equal(EXTERNAL_SAFE_PROTOCOLS.has(protocol), true, `${protocol} doit rester permis`);
}
for (const protocol of ['http:', 'javascript:', 'data:', 'file:', 'intent:']) {
  assert.equal(EXTERNAL_SAFE_PROTOCOLS.has(protocol), false, `${protocol} doit rester refusé`);
}

const sensitiveAssignments = [
  'access_token=secret',
  'ACCESS_TOKEN=secret',
  'access_token%3Dsecret',
  'access_token%253Dsecret',
  'access_token%25253Dsecret',
];
for (const candidate of sensitiveAssignments) {
  assert.equal(
    containsSensitiveExternalAssignment(candidate),
    true,
    `affectation sensible non bloquée: ${candidate}`,
  );
}

const blockedUrls = [
  'http://example.com/',
  'javascript:alert(1)',
  'data:text/plain,hello',
  'file:///tmp/example',
  'intent://example/#Intent;scheme=https;end',
  'https://example.com/?access_token=secret',
  'https://example.com/?ACCESS_TOKEN=secret',
  'https://example.com/?access%5Ftoken=secret',
  'https://example.com/?access%255Ftoken=secret',
  'https://example.com/?access%25255Ftoken=secret',
  'https://example.com/?access%2525255Ftoken=secret',
  'https://example.com/?body=access_token%3Dsecret',
  'https://example.com/?body=access_token%253Dsecret',
  'https://example.com/?body=access_token%25253Dsecret',
  'mailto:user@example.com?body=refresh_token%25253Dsecret',
  'https://example.com/path/session%253Dsecret',
  'https://example.com/#jwt%253Dsecret',
  'https://user:password@example.com/',
  'https://example.com/?body=hello%2525252520world',
];
for (const rawUrl of blockedUrls) {
  assert.equal(externalPolicyAllows(rawUrl), false, `URL dangereuse autorisée: ${rawUrl}`);
}

const allowedUrls = [
  'https://example.com/',
  'https://example.com/article?topic=tokenization',
  'https://example.com/?body=Bring%20your%20password%20manager',
  'https://example.com/?redirect=https%253A%252F%252Fother.test%252Fpath',
  'mailto:user@example.com?subject=Session%20schedule&body=Hello',
  'tel:+15145551234',
];
for (const rawUrl of allowedUrls) {
  assert.equal(externalPolicyAllows(rawUrl), true, `URL légitime bloquée: ${rawUrl}`);
}

console.log(
  `OK garde navigation externe V25: ${blockedUrls.length} cas dangereux refusés, ` +
  `${allowedUrls.length} cas légitimes permis, protocoles et encodages imbriqués vérifiés sur le code runtime de App.tsx.`,
);
