'use strict';
// Tests des URL réellement normalisées par le client Emploi SINJIRA V25.
// Exécution locale, sans backend, sans navigateur et sans données de candidats.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'assets/js/sinjira-employment-v25.js'), 'utf8'
);
const start = source.indexOf('function safeHttpUrl(value) {');
const end = source.indexOf('\nfunction formatDate(value)', start);
assert.ok(start >= 0 && end > start, 'Le garde URL du module réel doit exister');
const code = source.slice(start, end);
const sandbox = vm.createContext({URL});
vm.runInContext(code + '\nthis.validateUrl = safeHttpUrl;', sandbox, {timeout: 1500});
const safeHttpUrl = sandbox.validateUrl;
assert.equal(typeof safeHttpUrl, 'function');

let cases = 0;
function accept(value, expected = value) {
  assert.equal(safeHttpUrl(value), expected, 'URL HTTPS sûre refusée: ' + String(value));
  cases++;
}
function reject(value) {
  assert.equal(safeHttpUrl(value), null, 'URL incertaine acceptée: ' + String(value));
  cases++;
}

for (const good of [
  'https://example.com/',
  'https://jobs.example.org/career?role=dev#apply',
  'https://example.com/emploi/Montr%C3%A9al',
  'HTTPS://EXAMPLE.COM/',
  'https://sub.example.net:8443/poste'
]) {
  accept(good, new URL(good).href);
}

for (const bad of [
  '', null, undefined, 42, {}, [],
  'http://example.com/job', 'HTTP://example.com/job',
  'https://user:pass@example.com/secret',
  'https://user@example.com/',
  'https://:password@example.com/job',
  'https://trusted.example@evil.invalid/job',
  'https://example.com\\@evil.invalid/job',
  'https://example.com\\path',
  'https://example.com/\nprivate',
  'https://example.com/\tprivate',
  'https://example.com/\rprivate',
  'https://example.com/\u0000private',
  ' https://example.com/', 'https://example.com/ ',
  '//example.com/job',
  'javascript:alert(1)',
  'data:text/html,<script>alert(1)</script>',
  'file:///etc/passwd',
  'ftp://example.com/',
  'blob:https://example.com/id',
  'https:////evil.invalid/job',
  'https://',
  'https://example.com/'.padEnd(2049, 'x')
]) reject(bad);

const prefix = 'https://example.com/';
const atLimit = prefix + 'a'.repeat(2048 - prefix.length);
accept(atLimit);
reject(atLimit + 'a');

// Ne pas tronquer une URL correcte en entrée et introduire une URL résultante
// rompue ou ambiguë ; contrôler également sa longueur normalisée.
reject(prefix + 'é'.repeat(700));

assert.match(source, /const href = safeHttpUrl\(row\.source_url\)/,
  'Les liens réaffichés après lecture Supabase doivent passer par le garde');
assert.match(source, /const sourceUrl = safeHttpUrl\(sourceInput\)/,
  'Les liens enregistrés dans Supabase doivent passer par le même garde');
assert.match(source, /link\.rel = 'noopener noreferrer'/,
  'Les onglets externes doivent rester isolés');
assert.match(source, /Le lien source doit être une adresse HTTPS valide/,
  'Le formulaire doit annoncer la règle HTTPS');

console.log('PASS: ' + cases +
  ' cas de validation HTTPS, identifiants URL, caractères de contrôle et limites; ' +
  'stockage, affichage et onglets externes vérifiés.');
