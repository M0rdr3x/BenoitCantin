import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import ts from 'typescript';

const app = await readFile(new URL('../App.tsx', import.meta.url), 'utf8');
const share = await readFile(new URL('../safePublicShare.ts', import.meta.url), 'utf8');

function between(text, start, end) {
  const from = text.indexOf(start);
  assert.notEqual(from, -1, `Marqueur absent: ${start}`);
  const to = text.indexOf(end, from);
  assert.notEqual(to, -1, `Fin absente: ${end}`);
  return text.slice(from, to);
}

function compileAndRun(source, sandbox) {
  const output = ts.transpileModule(source, {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022, strict: true },
    reportDiagnostics: true,
  });
  const errors = (output.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error);
  assert.equal(errors.length, 0, 'Les fonctions de sécurité extraites doivent compiler: ' + errors.map(e => ts.flattenDiagnosticMessageText(e.messageText, '\n')).join(' | '));
  vm.runInNewContext(output.outputText, sandbox, { filename: 'sinjira-real-origin-guards.js' });
  return sandbox.__boundary;
}

// Exécuter les vraies fonctions de App.tsx en isolation, sans monter React Native.
const originalAppSource = [
  between(app, 'const DEFAULT_ORIGIN', 'const EXTERNAL_SAFE_PROTOCOLS'),
  between(app, 'const PRIVATE_SHARE_PATH_PREFIXES', 'const VAULT_PATH'),
  between(app, 'function configuredWebOrigin()', '\nconst ORIGIN = configuredWebOrigin();'),
  'const ORIGIN = configuredWebOrigin();',
  between(app, 'function normalizeSinjiraUrl(', '\nfunction shareableSinjiraUrl('),
  between(app, 'function shareableSinjiraUrl(', '\nfunction containsSensitiveExternalAssignment('),
  between(app, 'function isNativeHomeUrl(', '\nfunction tabForUrl('),
  'globalThis.__boundary = { configuredWebOrigin, normalizeSinjiraUrl, shareableSinjiraUrl, isNativeHomeUrl };',
].join('\n');

const constants = { expoConfig: { extra: { webOrigin: 'https://www.benoitcantin.com' } } };
const native = compileAndRun(originalAppSource, { URL, Constants: constants });
const trusted = [
  'https://www.benoitcantin.com',
  'https://benoitcantin.com',
  'https://sinjira.com',
  'https://www.sinjira.com',
];
for (const origin of trusted) {
  constants.expoConfig.extra.webOrigin = origin;
  assert.equal(native.configuredWebOrigin(), origin, `Origine HTTPS standard refusée: ${origin}`);
  assert.equal(native.normalizeSinjiraUrl(`${origin}/app/`), 'https://www.benoitcantin.com/app/');
  assert.equal(native.isNativeHomeUrl(`${origin}/app/`), true);
}
for (const candidate of [
  'https://www.benoitcantin.com:8443',
  'https://sinjira.com:8080',
  'https://www.sinjira.com:4443',
  'https://user:pass@www.benoitcantin.com',
]) {
  constants.expoConfig.extra.webOrigin = candidate;
  assert.equal(native.configuredWebOrigin(), 'https://www.benoitcantin.com', `Origine non canonique acceptée: ${candidate}`);
  assert.equal(native.normalizeSinjiraUrl(`${candidate}/compte/securite.html`), null);
  assert.equal(native.shareableSinjiraUrl(`${candidate}/projets/sinjira/`), null);
  assert.equal(native.isNativeHomeUrl(`${candidate}/app/`), false);
}
assert.equal(native.normalizeSinjiraUrl('https://sinjira.com:443/app/'), 'https://www.benoitcantin.com/app/', 'Le port HTTPS par défaut ne doit pas être bloqué');
assert.equal(native.shareableSinjiraUrl('https://sinjira.com/projets/sinjira/?token=confidentiel#secret'), 'https://www.benoitcantin.com/projets/sinjira/');
assert.equal(native.shareableSinjiraUrl('https://www.benoitcantin.com/compte/profil.html'), null);

// Exécuter la seconde frontière, dans le module réellement envoyé au menu natif.
const sharedSource = share.replace("import { Share } from 'react-native';", '').replace('export async function sharePublicSinjiraUrl', 'async function sharePublicSinjiraUrl') +
  '\nglobalThis.__boundary = { canonicalPublicSinjiraUrl, sharePublicSinjiraUrl };';
const sent = [];
const isolated = compileAndRun(sharedSource, { URL, Share: { share: async payload => { sent.push(payload); return { action: 'sharedAction' }; } } });
for (const candidate of [
  'https://www.benoitcantin.com:8443/projets/sinjira/',
  'https://www.sinjira.com:4443/',
  'https://user:pass@sinjira.com/',
  'http://www.benoitcantin.com/',
  'https://evil.example.com/',
  'https://sinjira.com/compte/profil.html',
]) {
  assert.equal(isolated.canonicalPublicSinjiraUrl(candidate), null, `Sortie non canonique acceptée: ${candidate}`);
  await assert.rejects(isolated.sharePublicSinjiraUrl(candidate), /PUBLIC_SHARE_URL_REQUIRED/);
}
assert.equal(sent.length, 0, 'Aucune demande refusée ne doit parvenir au menu de partage');
const allowed = 'https://sinjira.com/projets/sinjira/?session=private#frag';
assert.equal(isolated.canonicalPublicSinjiraUrl(allowed), 'https://sinjira.com/projets/sinjira/');
await isolated.sharePublicSinjiraUrl(allowed);
assert.equal(sent.length, 1);
assert.equal(sent[0].url, 'https://sinjira.com/projets/sinjira/');
assert.ok(!sent[0].message.includes('private') && !sent[0].message.includes('frag'));

// Les trois routes sont déclarées privées côté Netlify/Vercel mais n'étaient
// pas couvertes par l'ancienne liste de partage natif.
const privateShareCandidates = [
  'https://www.benoitcantin.com/administration.html',
  'https://sinjira.com/ADMINISTRATION.HTML?user=private',
  'https://www.benoitcantin.com/histoire-de-vie/remise.html',
  'https://www.sinjira.com/histoire-de-vie',
  'https://www.benoitcantin.com/supabase/config.json',
  'https://sinjira.com/supabase',
  'https://sinjira.com/%63ompte/profil.html',
  'https://sinjira.com/%2563ompte/profil.html',
  'https://sinjira.com/%61dministration.html',
  'https://sinjira.com/histoire-de-vie%2Fremise.html',
  'https://sinjira.com/supabase%252Fconfig.json',
  'https://sinjira.com/projets/%2fconfidentiel',
  'https://sinjira.com/projets/%ZZinvalide',
];
for (const candidate of privateShareCandidates) {
  assert.equal(native.shareableSinjiraUrl(candidate), null, `Le shell partage une route privée/ambiguë : ${candidate}`);
  assert.equal(isolated.canonicalPublicSinjiraUrl(candidate), null, `Le module partage une route privée/ambiguë : ${candidate}`);
  await assert.rejects(isolated.sharePublicSinjiraUrl(candidate), /PUBLIC_SHARE_URL_REQUIRED/);
}
assert.equal(sent.length, 1, 'Un rejet ultérieur ne doit pas déclencher un second partage');
const publicUnicodePath = 'https://sinjira.com/projets/sinjira/%C3%A9dition.html?confidentialite=retiree';
assert.equal(native.shareableSinjiraUrl(publicUnicodePath),
  'https://www.benoitcantin.com/projets/sinjira/%C3%A9dition.html');
assert.equal(isolated.canonicalPublicSinjiraUrl(publicUnicodePath),
  'https://sinjira.com/projets/sinjira/%C3%A9dition.html');

console.log('OK origines natives et confidentialité du partage : ports non standards, URL userinfo et routes privées/encodées refusés; chemins publics normaux préservés.');
