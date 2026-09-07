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
const vaultPathLine = requireSlice(
  "const VAULT_PATH = '/compte/registre-personnel.html';",
  '\n',
  'chemin Registre personnel',
);
const guardFunctions = requireSlice(
  'function containsSensitiveExternalAssignment(value: string)',
  '\nfunction isVaultUrl',
  'garde externe',
);
const shouldStartFunction = requireSlice(
  '  const shouldStart = (request: { url: string }) => {',
  '\n\n  if (!securityReady)',
  'décision shouldStart',
);

const runtimeSource = `${protocolLine}\n${sensitiveParams}\n${vaultPathLine}\n${guardFunctions}\n` +
  `function buildShouldStartHarness(deps: any) {\n` +
  `  const { allowedHosts, isVaultUrl, vaultLocalGateUntilRef, navigate, setNativeMessage, Linking } = deps;\n` +
  `${shouldStartFunction}\n` +
  `  return shouldStart;\n` +
  `}\n` +
  `(globalThis as any).__sinjiraNavigationRuntime = { ` +
  `EXTERNAL_SAFE_PROTOCOLS, containsSensitiveExternalAssignment, hasSensitiveExternalMaterial, buildShouldStartHarness };`;

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
assert.equal(compileErrors.length, 0, 'la frontière extraite de App.tsx doit compiler sans erreur');

const sandbox = {
  URL,
  URLSearchParams,
  decodeURIComponent,
  console,
};
vm.runInNewContext(transpiled.outputText, sandbox, {
  filename: 'App.external-navigation-boundary.runtime.js',
});

const runtime = sandbox.__sinjiraNavigationRuntime;
assert.ok(runtime, 'la frontière runtime extraite doit être disponible');
const {
  EXTERNAL_SAFE_PROTOCOLS,
  containsSensitiveExternalAssignment,
  hasSensitiveExternalMaterial,
  buildShouldStartHarness,
} = runtime;

function externalPolicyAllows(rawUrl) {
  const parsed = new URL(rawUrl);
  return EXTERNAL_SAFE_PROTOCOLS.has(parsed.protocol) && !hasSensitiveExternalMaterial(parsed);
}

function createShouldStartHarness({ vaultGateOpen = true, linkingRejects = false } = {}) {
  const messages = [];
  const openedUrls = [];
  const navigatedPaths = [];
  const allowedHosts = new Set([
    'www.benoitcantin.com',
    'benoitcantin.com',
    'sinjira.com',
    'www.sinjira.com',
  ]);
  const vaultLocalGateUntilRef = {
    current: vaultGateOpen ? Number.MAX_SAFE_INTEGER : 0,
  };
  const isVaultUrl = (rawUrl) => {
    try {
      return new URL(rawUrl, 'https://www.benoitcantin.com').pathname === '/compte/registre-personnel.html';
    } catch {
      return false;
    }
  };
  const navigate = async (path) => {
    navigatedPaths.push(path);
  };
  const setNativeMessage = (message) => {
    messages.push(message);
  };
  const Linking = {
    openURL: (rawUrl) => {
      openedUrls.push(rawUrl);
      return linkingRejects ? Promise.reject(new Error('simulated Linking failure')) : Promise.resolve();
    },
  };
  const shouldStart = buildShouldStartHarness({
    allowedHosts,
    isVaultUrl,
    vaultLocalGateUntilRef,
    navigate,
    setNativeMessage,
    Linking,
  });
  return { shouldStart, messages, openedUrls, navigatedPaths };
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

{
  const harness = createShouldStartHarness();
  assert.equal(harness.shouldStart({ url: 'about:blank' }), true, 'about:blank doit rester interne à la WebView');
  assert.deepEqual(harness.messages, [], 'about:blank ne doit produire aucun message');
  assert.deepEqual(harness.openedUrls, [], 'about:blank ne doit jamais ouvrir le système');
}

{
  const harness = createShouldStartHarness();
  assert.equal(harness.shouldStart({ url: 'pas une URL' }), false, 'une URL invalide doit être refusée');
  assert.match(harness.messages.at(-1) || '', /lien demandé est invalide/i);
  assert.deepEqual(harness.openedUrls, [], 'une URL invalide ne doit jamais atteindre Linking');
}

{
  const harness = createShouldStartHarness();
  assert.equal(
    harness.shouldStart({ url: 'https://www.sinjira.com/compte/profil.html' }),
    true,
    'un hôte SINJIRA HTTPS approuvé doit rester dans la WebView',
  );
  assert.deepEqual(harness.openedUrls, [], 'un lien SINJIRA interne ne doit jamais être envoyé à Linking');
}

{
  const harness = createShouldStartHarness();
  assert.equal(
    harness.shouldStart({ url: 'https://sinjira.com/compte/profil.html?access_token=interne' }),
    true,
    'la branche interne doit être décidée avant le filtre réservé aux sorties externes',
  );
  assert.deepEqual(harness.openedUrls, [], 'une URL SINJIRA interne sensible ne doit jamais sortir vers le système');
}

{
  const harness = createShouldStartHarness({ vaultGateOpen: false });
  assert.equal(
    harness.shouldStart({ url: 'https://www.benoitcantin.com/compte/registre-personnel.html' }),
    false,
    'le Registre doit être intercepté lorsque la barrière locale a expiré',
  );
  assert.deepEqual(harness.navigatedPaths, ['/compte/registre-personnel.html']);
  assert.deepEqual(harness.openedUrls, [], 'le Registre ne doit jamais être envoyé à Linking');
}

{
  const harness = createShouldStartHarness({ vaultGateOpen: true });
  assert.equal(
    harness.shouldStart({ url: 'https://www.benoitcantin.com/compte/registre-personnel.html' }),
    true,
    'le Registre peut rester dans la WebView pendant la fenêtre locale valide',
  );
  assert.deepEqual(harness.navigatedPaths, []);
}

{
  const harness = createShouldStartHarness();
  assert.equal(
    harness.shouldStart({ url: 'javascript:access_token=secret' }),
    false,
    'un protocole interdit doit être refusé avant toute tentative externe',
  );
  assert.match(harness.messages.at(-1) || '', /schémas ou connexions non autorisés/i);
  assert.deepEqual(harness.openedUrls, [], 'un protocole interdit ne doit jamais atteindre Linking');
}

{
  const harness = createShouldStartHarness();
  assert.equal(
    harness.shouldStart({ url: 'https://example.com/?access_token=secret' }),
    false,
    'une sortie HTTPS contenant de la matière sensible doit être refusée',
  );
  assert.match(harness.messages.at(-1) || '', /session ou d.authentification/i);
  assert.deepEqual(harness.openedUrls, [], 'une sortie sensible ne doit jamais atteindre Linking');
}

for (const rawUrl of [
  'https://example.com/article',
  'mailto:user@example.com?subject=Bonjour',
  'tel:+15145551234',
]) {
  const harness = createShouldStartHarness();
  assert.equal(harness.shouldStart({ url: rawUrl }), false, `la sortie OS doit être interceptée: ${rawUrl}`);
  assert.deepEqual(harness.openedUrls, [rawUrl], `la sortie propre doit atteindre Linking exactement une fois: ${rawUrl}`);
  assert.deepEqual(harness.messages, [], `la sortie propre ne doit pas afficher de blocage: ${rawUrl}`);
}

{
  const harness = createShouldStartHarness({ linkingRejects: true });
  const rawUrl = 'https://example.com/article';
  assert.equal(harness.shouldStart({ url: rawUrl }), false);
  assert.deepEqual(harness.openedUrls, [rawUrl]);
  await Promise.resolve();
  assert.match(
    harness.messages.at(-1) || '',
    /ne peut pas être ouvert de façon sûre/i,
    'un échec Linking doit être transformé en message sûr',
  );
}

console.log(
  `OK frontière navigation V25: ${blockedUrls.length} cas dangereux refusés, ` +
  `${allowedUrls.length} cas légitimes permis, et shouldStart exécuté avec ses effets de bord critiques sur le code réel de App.tsx.`,
);
