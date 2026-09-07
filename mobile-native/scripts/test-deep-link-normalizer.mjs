import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import ts from 'typescript';

const appSource = await readFile(new URL('../App.tsx', import.meta.url), 'utf8');
const TEST_ORIGIN = 'https://www.benoitcantin.com';

function requireSlice(startMarker, endMarker, label) {
  const start = appSource.indexOf(startMarker);
  assert.notEqual(start, -1, `${label}: marqueur de début introuvable`);
  const end = appSource.indexOf(endMarker, start);
  assert.notEqual(end, -1, `${label}: marqueur de fin introuvable`);
  return appSource.slice(start, end);
}

const allowedHostsLine = requireSlice(
  "const ALLOWED_WEB_HOSTS = new Set(['www.benoitcantin.com', 'benoitcantin.com', 'sinjira.com', 'www.sinjira.com']);",
  '\n',
  'hôtes web approuvés',
);
const normalizeFunction = requireSlice(
  'function normalizeSinjiraUrl(url: string | null): string | null {',
  '\nfunction shareableSinjiraUrl',
  'normaliseur deep link',
);

const runtimeSource = `${allowedHostsLine}\n` +
  `const ORIGIN = ${JSON.stringify(TEST_ORIGIN)};\n` +
  `${normalizeFunction}\n` +
  `(globalThis as any).__sinjiraDeepLinkRuntime = { normalizeSinjiraUrl };`;

const transpiled = ts.transpileModule(runtimeSource, {
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
assert.equal(compileErrors.length, 0, 'le normaliseur extrait de App.tsx doit compiler sans erreur');

const sandbox = { URL, console };
vm.runInNewContext(transpiled.outputText, sandbox, {
  filename: 'App.deep-link-normalizer.runtime.js',
});
const runtime = sandbox.__sinjiraDeepLinkRuntime;
assert.ok(runtime, 'le normaliseur deep link extrait doit être disponible');
const { normalizeSinjiraUrl } = runtime;

function assertPinnedToSinjiraOrigin(rawUrl, expectedPathAndSuffix) {
  const normalized = normalizeSinjiraUrl(rawUrl);
  assert.equal(normalized, `${TEST_ORIGIN}${expectedPathAndSuffix}`, `normalisation inattendue: ${rawUrl}`);
  const parsed = new URL(normalized);
  assert.equal(parsed.protocol, 'https:', `le résultat doit rester HTTPS: ${rawUrl}`);
  assert.equal(parsed.origin, TEST_ORIGIN, `le résultat ne doit jamais quitter l'origine SINJIRA: ${rawUrl}`);
  assert.equal(parsed.username, '', `le résultat ne doit conserver aucun username: ${rawUrl}`);
  assert.equal(parsed.password, '', `le résultat ne doit conserver aucun password: ${rawUrl}`);
}

const safeCustomSchemeCases = [
  ['sinjira:/compte/profil.html', '/compte/profil.html'],
  ['sinjira://compte/profil.html', '/compte/profil.html'],
  ['sinjira:///compte/profil.html', '/compte/profil.html'],
  ['sinjira:///////compte/profil.html?tab=1#bio', '/compte/profil.html?tab=1#bio'],
  ['sinjira://evil.example/path', '/evil.example/path'],
  ['sinjira:////evil.example/path', '/evil.example/path'],
  ['sinjira://user@evil.example/path', '/user@evil.example/path'],
  ['sinjira://%2F%2Fevil.example/path', '/%2F%2Fevil.example/path'],
  ['sinjira://%5C%5Cevil.example/path', '/%5C%5Cevil.example/path'],
];
for (const [rawUrl, expected] of safeCustomSchemeCases) {
  assertPinnedToSinjiraOrigin(rawUrl, expected);
}

const approvedHttpsCases = [
  ['https://sinjira.com/compte/profil.html?tab=1#bio', '/compte/profil.html?tab=1#bio'],
  ['https://www.sinjira.com/app/', '/app/'],
  ['https://benoitcantin.com/compte/messages.html', '/compte/messages.html'],
  ['https://www.benoitcantin.com//evil.example/path', '//evil.example/path'],
  ['https://user:password@sinjira.com/compte/profil.html', '/compte/profil.html'],
];
for (const [rawUrl, expected] of approvedHttpsCases) {
  assertPinnedToSinjiraOrigin(rawUrl, expected);
}

const rejectedInputs = [
  null,
  '',
  'sinjira:compte/profil.html',
  'https://evil.example/compte/profil.html',
  'http://sinjira.com/compte/profil.html',
  '//evil.example/compte/profil.html',
  'javascript:alert(1)',
  'file:///tmp/example',
  'https://%',
];
for (const rawUrl of rejectedInputs) {
  assert.equal(normalizeSinjiraUrl(rawUrl), null, `entrée deep link non approuvée: ${String(rawUrl)}`);
}

for (const [rawUrl] of [...safeCustomSchemeCases, ...approvedHttpsCases]) {
  const normalized = normalizeSinjiraUrl(rawUrl);
  assert.ok(normalized, `le cas sûr doit produire une URL: ${rawUrl}`);
  const reparsed = new URL(normalized);
  assert.equal(reparsed.hostname, 'www.benoitcantin.com', `aucun deep link ne doit changer l'hôte final: ${rawUrl}`);
}

console.log(
  `OK deep links V25: ${safeCustomSchemeCases.length} formes sinjira: épinglées à l'origine, ` +
  `${approvedHttpsCases.length} liens HTTPS approuvés canonicalisés, ${rejectedInputs.length} entrées non approuvées refusées.`,
);
