'use strict';
// Teste les vraies fonctions du client, sans navigateur ni réseau.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets/js/sinjira-account.js'), 'utf8');

function extract(startMarker, endMarker) {
  const from = source.indexOf(startMarker);
  const to = source.indexOf(endMarker, from + startMarker.length);
  assert.ok(from >= 0 && to > from, 'Code de navigation source absent: ' + startMarker);
  return source.slice(from, to);
}

const functions = extract('function safeLocalNavigation(', '\nfunction backendNotice(')
  + '\n' + extract('function sessionUrl(', '\nfunction avatarPublicUrl(')
  + '\n globalThis.checkNavigation = {safeLocalNavigation, nextDestination, sessionUrl};';
const origin = 'https://www.benoitcantin.com';
const location = {origin, search: ''};
const sandbox = {URL, URLSearchParams, location};
vm.runInNewContext(functions, sandbox, {timeout: 2000});
const {safeLocalNavigation, nextDestination, sessionUrl} = sandbox.checkNavigation;
const HOME = '/compte/index.html';
let assertions = 0;

function accepted(url, expected = url) {
  assert.equal(safeLocalNavigation(url), expected, 'Un lien local légitime a été modifié.');
  assertions++;
}
function rejected(url, fallback = HOME) {
  assert.equal(safeLocalNavigation(url), fallback, 'Une destination externe/ambiguë a été acceptée.');
  assertions++;
}

accepted('/compte/index.html');
accepted('/app/');
accepted('/projets/sinjira/romans/index.html');
accepted('/compte/index.html?tab=1#profile');
accepted('/?from=sinjira');
accepted('/compte/../app/', '/app/');
accepted('/app/?value=1&value=2#section');

[
  '', '   ', 'compte/index.html', 'https://attacker.example/login',
  'http://attacker.example/', 'javascript:alert(1)',
  '//attacker.example/login', '///attacker.example/',
  '/\\attacker.example/', '/%5cattacker.example/',
  '/%2fattacker.example/', '/%2F%2Fattacker.example/',
  '/%0aattacker.example/', '/%1fattacker.example/',
  '/%7fattacker.example/', '/app/\nmalicious',
  '/app/\rmalicious', '/app/\tmalicious',
  '\\\\attacker.example/', 'https:%2f%2fattacker.example/',
].forEach(value => rejected(value));

location.search = '?next=%2Fcompte%2Findex.html%3Ftab%3D2';
assert.equal(nextDestination(), '/compte/index.html?tab=2');
assertions++;
location.search = '?next=%2F%2Fattacker.example%2Fphishing';
assert.equal(nextDestination(), HOME);
assertions++;
location.search = '?next=javascript%3Aalert%281%29';
assert.equal(nextDestination(), HOME);
assertions++;
location.search = '?next=%2Fapp%2F';
assert.equal(nextDestination(), '/app/');
assertions++;
location.search = '';
assert.equal(nextDestination('/compte/bibliotheque.html'), '/compte/bibliotheque.html');
assertions++;

assert.equal(sessionUrl({game_slug:'another-game', projects:{public_path:'/projets/sinjira/jeux/'}}), '/projets/sinjira/jeux/');
assertions++;
assert.equal(sessionUrl({game_slug:'another-game', projects:{public_path:'javascript:alert(1)'}}), '/compte/bibliotheque.html');
assertions++;
assert.equal(sessionUrl({game_slug:'another-game', projects:{public_path:'//attacker.example/landing'}}), '/compte/bibliotheque.html');
assertions++;
assert.equal(sessionUrl({game_slug:'another-game', projects:{public_path:'/%5cattacker.example'}}), '/compte/bibliotheque.html');
assertions++;
assert.equal(sessionUrl({game_slug:'another-game', projects:{public_path:'/projets/sinjira/jeux/?a=1&b=2'}}), '/projets/sinjira/jeux/?a=1&b=2');
assertions++;
assert.equal(sessionUrl({game_slug:'fracture-du-reseau-mere', party_code:'ABC-42'}),
  '/projets/sinjira/jeux/fracture-du-reseau-mere/partie.html?code=ABC-42');
assertions++;
assert.equal(sessionUrl({game_slug:'fracture-du-reseau-mere', party_code:'"><script>alert(1)</script>'}).includes('<'), false);
assertions++;

const escapedSink = 'href="' + '$' + '{escapeHtml(sessionUrl(x))}' + '"';
assert.equal(source.split(escapedSink).length - 1, 2, 'Deux liens de parties échappés requis.');
assertions++;
assert.equal(source.includes('return n&&n.startsWith'), false, 'Ancien validateur de redirection dangereux.');
assertions++;
assert.equal(source.includes('return s.projects?.public_path||'), false, 'Ancien lien de jeu non revu.');
assertions++;
assert.equal(source.includes('location.href=nextDestination()'), true, 'Parcours de connexion inchangé.');
assertions++;

console.log('PASS: ' + assertions + ' contrôles de navigation locale SINJIRA (redirections, URL de jeu et attributs HTML).');
