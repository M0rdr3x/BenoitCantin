'use strict';
// Audit GET uniquement : vérification de la parité des JS et de la présence
// des pages critiques SINJIRA en production. Aucun token, POST ni secret.
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const https = require('node:https');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const ORIGIN = 'https://www.benoitcantin.com';
const MAX = 512 * 1024;
const SCRIPTS = [
  'assets/js/sinjira-confirm-email.js',
  'assets/js/v24-signup.js',
  'assets/js/sinjira-character-registry.js',
  'assets/js/sinjira-account.js',
  'assets/js/v24-security.js' // TOTP / AAL2 : contrôler la version effectivement publiée
];
const HTML = [
  { path: 'compte/confirmer.html', markers: [
    'data-confirm-button hidden', 'sinjira-confirm-email.js?v=3'
  ] },
  { path: 'compte/inscription.html', markers: [
    'data-signup-form', 'formspree_receipt_opt_in', 'v24-signup.js?v=24.5.6'
  ] },
  { path: 'projets/sinjira/registre/index.html', markers: [
    'sinjira-character-registry.js?v=24.5.8',
    'AAL2', 'formspree_receipt_opt_in'
  ] }
];
const REQUIRED_MODULES = {
  'compte/confirmer.html': '../assets/js/sinjira-confirm-email.js?v=3',
  'compte/inscription.html': '../assets/js/v24-signup.js?v=24.5.6',
  'projets/sinjira/registre/index.html': '../../../assets/js/sinjira-character-registry.js?v=24.5.8'
};

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}
function local(route) {
  assert.match(route, /^[a-z0-9][a-z0-9/._-]*$/, 'Route relative interdite');
  const result = path.resolve(ROOT, route);
  assert.ok(result.startsWith(ROOT + path.sep), 'Sortie du répertoire interdite');
  return fs.readFileSync(result);
}
function verifyJs(route, served, expected = local(route)) {
  const matching = sha256(served) === sha256(expected);
  if (!matching) {
    throw new Error('DÉCALAGE DE PUBLICATION : ' + route +
      ' — le script servi ne correspond pas au dépôt. Ne pas certifier 100 %.');
  }
  return matching;
}
function verifyHtml(route, served, markers) {
  const content = served.toString('utf8');
  for (const marker of markers) {
    if (!content.includes(marker)) {
      throw new Error('PAGE PUBLIÉE INCOMPLÈTE : ' + route +
        ' — marqueur requis absent : ' + marker);
    }
  }
  const expected = REQUIRED_MODULES[route];
  if (expected) {
    // Un texte ou un commentaire contenant la bonne version n'est PAS une
    // balise <script src> active. Vérifier le src local exact et type=module.
    const withoutComments = content.replace(/<!--[\s\S]*?-->/g, '');
    const basename = expected.split('/').pop().split('?')[0];
    const candidates = [];
    for (const match of withoutComments.matchAll(/<script\b([^>]*)>/gi)) {
      const tag = match[1];
      const attrs = { src: [], type: [] };
      const pattern = /(?:^|\s)(src|type)\s*=\s*(?:"([^"]*)"|'([^']*)')/gi;
      for (const attr of tag.matchAll(pattern)) {
        attrs[attr[1].toLowerCase()].push(attr[2] ?? attr[3]);
      }
      if (tag.includes(basename)) candidates.push(attrs);
    }
    const sole = candidates.length === 1 ? candidates[0] : null;
    if (!sole || sole.src.length !== 1 || sole.src[0] !== expected ||
        sole.type.length !== 1 || sole.type[0].toLowerCase() !== 'module') {
      throw new Error('MODULE HTML NON CONFORME : ' + route +
        ' — balise script locale exacte, unique et type=module exigée.');
    }
  }
  return true;
}
function getPublic(route) {
  return new Promise((resolve, reject) => {
    const url = new URL('/' + route, ORIGIN);
    if (url.origin !== ORIGIN) {
      reject(new Error('Origine invalide')); return;
    }
    const request = https.get(url, {
      timeout: 12000, maxRedirects: 0,
      headers: {
        'Accept': 'text/html,application/javascript,*/*;q=0.1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'User-Agent': 'SINJIRA-release-readonly/1.0'
      }
    }, response => {
      if (response.statusCode !== 200) {
        response.resume();
        reject(new Error('HTTP ' + response.statusCode + ' pour ' + route));
        return;
      }
      const chunks = [];
      let length = 0;
      response.on('data', chunk => {
        length += chunk.length;
        if (length > MAX) {
          request.destroy(new Error('Ressource publique trop volumineuse : ' + route));
          return;
        }
        chunks.push(chunk);
      });
      response.on('end', () => resolve(Buffer.concat(chunks)));
      response.on('error', reject);
    });
    request.on('timeout', () => request.destroy(new Error('Délai public dépassé : ' + route)));
    request.on('error', reject);
  });
}
function selfTest() {
  assert.equal(SCRIPTS.length, 5);
  assert.equal(HTML.length, 3);
  const first = local(SCRIPTS[0]);
  assert.ok(first.toString('utf8').includes("confirmButton?.addEventListener('click'"));
  assert.ok(first.toString('utf8').includes('getSupabase().auth.verifyOtp('));
  assert.equal(verifyJs(SCRIPTS[0], first), true);
  assert.throws(() => verifyJs(SCRIPTS[0], Buffer.from('ancien code'), first),
    /DÉCALAGE DE PUBLICATION/);
  for (const route of SCRIPTS) assert.ok(local(route).length > 100);
  const totp = local('assets/js/v24-security.js');
  assert.ok(totp.toString('utf8').includes('challengeAndVerify'),
    'Le script TOTP publié doit permettre la vérification du second facteur.');
  assert.ok(totp.toString('utf8').includes('getAuthenticatorAssuranceLevel'),
    'Le script TOTP doit vérifier le niveau d’assurance.');
  assert.equal(verifyJs('assets/js/v24-security.js', totp), true);
  assert.throws(() => verifyJs('assets/js/v24-security.js',
    Buffer.concat([totp, Buffer.from('\n// ancienne version simulée')]), totp),
  /DÉCALAGE DE PUBLICATION/);
  for (const entry of HTML) {
    const source = local(entry.path);
    assert.equal(verifyHtml(entry.path, source, entry.markers), true);
    assert.throws(() => verifyHtml(entry.path, Buffer.from('page obsolète'), entry.markers),
      /PAGE PUBLIÉE INCOMPLÈTE/);
  }
  for (const entry of HTML) {
    const source = local(entry.path).toString('utf8');
    const expected = REQUIRED_MODULES[entry.path];
    const scriptTag = '<script src="' + expected + '" type="module"></script>';
    const marker = expected.split('/').pop();
    const stale = expected.replace(/v=([\d.]+)/, (_all, v) =>
      'v=' + v + '-stale');
    const variants = [
      // Le bon marqueur hors balise ne doit plus cacher l'ancien module.
      source.replace(expected, stale) + '<!-- ' + marker + ' -->',
      source.replace(expected, stale) + '<p>' + marker + '</p>',
      // Une balise redondante ne doit pas coexister avec la bonne.
      source + '<script src="' + stale + '" type="module"></script>',
      // Le src peut sembler sûr dans du texte mais être d'origine extérieure.
      source.replace(expected, 'https://evil.invalid/' + marker) +
        '<!-- ' + expected + ' -->',
      // Un double src est ambigu : les navigateurs ne le choisissent pas
      // nécessairement comme le premier vérificateur HTML.
      source.replace(expected, expected + '" src="https://evil.invalid/x.js'),
      // Même le bon src ne suffit pas avec un type de module incorrect.
      source.replace('src="' + expected + '" type="module"',
        'src="' + expected + '" type="text/plain"')
        .replace('type="module" src="' + expected + '"',
        'type="text/plain" src="' + expected + '"')
    ];
    for (const variant of variants) {
      assert.throws(() => verifyHtml(entry.path, Buffer.from(variant), entry.markers),
        /MODULE HTML NON CONFORME/, 'Fausse parité HTML non refusée : ' + entry.path);
    }
    // Le marqueur seul dans un commentaire ne remplace pas un vrai script.
    assert.throws(() => verifyHtml(entry.path, Buffer.from(
      source.replace(expected, stale) + '<!-- ' + scriptTag + ' -->'
    ), entry.markers), /MODULE HTML NON CONFORME/);
  }
  // Un cache ancien peut masquer un correctif déjà fusionné. Détecter
  // la régression de la révision chargée dans les vraies pages HTML.
  for (const [route, current, previous] of [
    ['compte/confirmer.html', 'sinjira-confirm-email.js?v=3', 'sinjira-confirm-email.js?v=2'],
    ['compte/inscription.html', 'v24-signup.js?v=24.5.6', 'v24-signup.js?v=24.5.5']
  ]) {
    const item = HTML.find(entry => entry.path === route);
    const currentHtml = local(route).toString('utf8');
    assert.ok(currentHtml.includes(current), 'Révision récente absente : ' + route);
    assert.ok(!currentHtml.includes(previous), 'Ancienne révision encore référencée : ' + route);
    const staleHtml = Buffer.from(currentHtml.replace(current, previous));
    assert.throws(() => verifyHtml(route, staleHtml, item.markers),
      /PAGE PUBLIÉE INCOMPLÈTE/, 'Révision obsolète non détectée : ' + route);
  }
  assert.throws(() => local('../secret'));
  console.log('PASS prévol public SINJIRA : 5 JS, 3 pages, vrais scripts HTML et tentatives de faux PASS refusées, aucun réseau.');
}
async function production() {
  const errors = [];
  // Un appel réseau fait exactement un GET par ressource, sans suivre de
  // redirection ni lire ou afficher un courriel, un cookie ou un jeton.
  for (const route of SCRIPTS) {
    try {
      verifyJs(route, await getPublic(route));
      console.log('PASS script publié : ' + route);
    } catch (error) {
      errors.push(route);
      console.error('ÉCHEC parité JS : ' + route + ' (' + error.message + ')');
    }
  }
  for (const entry of HTML) {
    try {
      verifyHtml(entry.path, await getPublic(entry.path), entry.markers);
      console.log('PASS page publiée : ' + entry.path);
    } catch (error) {
      errors.push(entry.path);
      console.error('ÉCHEC page : ' + entry.path + ' (' + error.message + ')');
    }
  }
  console.log('BILAN : ' + (SCRIPTS.length + HTML.length - errors.length) + '/' + (SCRIPTS.length + HTML.length) + ' ressources publiques vérifiées.');
  if (errors.length) {
    console.error('NON CERTIFIÉ : divergence publication / code ou accès public.');
    process.exitCode = 1;
  } else {
    console.log('Parité publique constatée. SMTP, courriels et E2E restent distincts.');
  }
}
async function main() {
  if (process.argv.length !== 3) throw new Error('Utilisation : --self-test ou --production');
  if (process.argv[2] === '--self-test') selfTest();
  else if (process.argv[2] === '--production') await production();
  else throw new Error('Mode inconnu; aucun changement effectué');
}
main().catch(error => {
  console.error('ÉCHEC du prévol : ' + error.message);
  process.exitCode = 1;
});
