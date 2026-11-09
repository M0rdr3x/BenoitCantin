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
  'assets/js/sinjira-account.js'
];
const HTML = [
  { path: 'compte/confirmer.html', markers: [
    'data-confirm-button hidden', 'sinjira-confirm-email.js?v=2'
  ] },
  { path: 'compte/inscription.html', markers: [
    'data-signup-form', 'formspree_receipt_opt_in', 'v24-signup.js?v=24.5.3'
  ] },
  { path: 'projets/sinjira/registre/index.html', markers: [
    'sinjira-character-registry.js?v=24.5.8',
    'AAL2', 'formspree_receipt_opt_in'
  ] }
];

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
  assert.equal(SCRIPTS.length, 4);
  assert.equal(HTML.length, 3);
  const first = local(SCRIPTS[0]);
  assert.ok(first.toString('utf8').includes("confirmButton?.addEventListener('click'"));
  assert.ok(first.toString('utf8').includes('getSupabase().auth.verifyOtp('));
  assert.equal(verifyJs(SCRIPTS[0], first), true);
  assert.throws(() => verifyJs(SCRIPTS[0], Buffer.from('ancien code'), first),
    /DÉCALAGE DE PUBLICATION/);
  for (const route of SCRIPTS) assert.ok(local(route).length > 100);
  for (const entry of HTML) {
    const source = local(entry.path);
    assert.equal(verifyHtml(entry.path, source, entry.markers), true);
    assert.throws(() => verifyHtml(entry.path, Buffer.from('page obsolète'), entry.markers),
      /PAGE PUBLIÉE INCOMPLÈTE/);
  }
  assert.throws(() => local('../secret'));
  console.log('PASS prévol public SINJIRA : 4 JS, 3 pages, détection de dérive, aucun réseau.');
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
  console.log('BILAN : ' + (7 - errors.length) + '/7 ressources publiques vérifiées.');
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
