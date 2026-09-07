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

const navigateFunction = requireSlice(
  '  const navigate = async (path: string, tab?: TabKey) => {',
  '\n\n  const navigateFromNativeModule',
  'navigation interne',
);
const notificationEffect = requireSlice(
  "  useEffect(() => {\n    const subscription = Notifications.addNotificationResponseReceivedListener((response) => {",
  "\n\n  useEffect(() => {\n    if (Platform.OS !== 'android') return;",
  'réponse notification',
);

const runtimeSource = `
function buildNotificationHarness() {
  const ORIGIN = ${JSON.stringify(TEST_ORIGIN)};
  const navigatedUrls: Array<{ url: string; tab: unknown }> = [];
  let notificationListener: ((response: any) => void) | null = null;
  const navigateToUrl = async (url: string, tab?: unknown) => {
    navigatedUrls.push({ url, tab });
  };
  const Notifications = {
    addNotificationResponseReceivedListener(listener: (response: any) => void) {
      notificationListener = listener;
      return { remove() {} };
    },
  };
  const useEffect = (effect: () => void | (() => void)) => {
    effect();
  };
${navigateFunction}
${notificationEffect}
  if (!notificationListener) throw new Error('listener notification introuvable');
  return {
    navigatedUrls,
    trigger(path: unknown) {
      notificationListener!({
        notification: {
          request: {
            content: {
              data: { path },
            },
          },
        },
      });
    },
  };
}
(globalThis as any).__sinjiraNotificationRuntime = { buildNotificationHarness };
`;

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
assert.equal(compileErrors.length, 0, 'le callback notification extrait de App.tsx doit compiler sans erreur');

const sandbox = { URL, console };
vm.runInNewContext(transpiled.outputText, sandbox, {
  filename: 'App.notification-navigation.runtime.js',
});
const runtime = sandbox.__sinjiraNotificationRuntime;
assert.ok(runtime, 'le runtime notification extrait doit être disponible');
const { buildNotificationHarness } = runtime;

const acceptedPaths = [
  '/compte/profil.html',
  '/compte/registre-personnel.html',
  '/compte/securite.html?surface=web#travel-title',
  '/https://evil.example/path',
  '/@evil.example/path',
  '/\\evil.example/path',
  '/%5C%5Cevil.example/path',
  '/%2F%2Fevil.example/path',
  '/%0Ahttps%3A%2F%2Fevil.example/path',
];
for (const path of acceptedPaths) {
  const harness = buildNotificationHarness();
  harness.trigger(path);
  assert.equal(harness.navigatedUrls.length, 1, `le chemin interne doit être routé une fois: ${path}`);
  const [{ url, tab }] = harness.navigatedUrls;
  assert.equal(tab, undefined, `une notification ne doit pas injecter d'onglet natif: ${path}`);
  assert.equal(url, `${TEST_ORIGIN}${path}`, `navigate doit préfixer l'origine SINJIRA: ${path}`);
  const reparsed = new URL(url);
  assert.equal(reparsed.protocol, 'https:', `la destination notification doit rester HTTPS: ${path}`);
  assert.equal(reparsed.origin, TEST_ORIGIN, `la destination notification ne doit jamais changer d'origine: ${path}`);
  assert.equal(reparsed.username, '', `aucun username ne doit apparaître: ${path}`);
  assert.equal(reparsed.password, '', `aucun password ne doit apparaître: ${path}`);
}

const rejectedPaths = [
  null,
  undefined,
  42,
  {},
  '',
  'compte/profil.html',
  'https://evil.example/path',
  'http://evil.example/path',
  'sinjira://compte/profil.html',
  'javascript:alert(1)',
  '//evil.example/path',
  '///evil.example/path',
  '\\evil.example/path',
  ' /compte/profil.html',
];
for (const path of rejectedPaths) {
  const harness = buildNotificationHarness();
  harness.trigger(path);
  assert.equal(harness.navigatedUrls.length, 0, `entrée notification non approuvée routée: ${String(path)}`);
}

{
  const harness = buildNotificationHarness();
  harness.trigger('/compte/profil.html');
  harness.trigger('//evil.example/path');
  harness.trigger('/compte/messages.html?thread=123#latest');
  assert.deepEqual(
    Array.from(harness.navigatedUrls, ({ url }) => url),
    [
      `${TEST_ORIGIN}/compte/profil.html`,
      `${TEST_ORIGIN}/compte/messages.html?thread=123#latest`,
    ],
    'une entrée rejetée ne doit pas altérer les navigations sûres suivantes',
  );
}

console.log(
  `OK notifications V25: ${acceptedPaths.length} chemins internes restent épinglés à l'origine SINJIRA, ` +
  `${rejectedPaths.length} entrées non approuvées sont ignorées, callback et navigate réels exécutés.`,
);
