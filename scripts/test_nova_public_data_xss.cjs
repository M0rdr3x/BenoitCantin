'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const src = fs.readFileSync(path.join(__dirname, '../projets/projet-nova/script.js'), 'utf8');
const firstIife = src.indexOf('(function(){');
assert.ok(firstIife > 0, 'Les fonctions de sécurité doivent précéder le rendu.');
const prefix = src.slice(0, firstIife);
const start = src.indexOf('      function card(d){');
const end = src.indexOf('      function render(){', start);
assert.ok(start >= 0 && end > start, 'Rendu des archives absent.');
const sandbox = {};
vm.runInNewContext(prefix + '\n' + src.slice(start, end)
  + '\nglobalThis.testFns = {novaEscapeHtml, novaSafeDocumentHref, novaSafeJournalHref, card};',
  sandbox, {timeout: 2000});
const {novaEscapeHtml:escape, novaSafeDocumentHref:doc, novaSafeJournalHref:journal, card} = sandbox.testFns;

let checks = 0;
function same(actual, expected, label) {
  assert.equal(actual, expected, label);
  checks++;
}
function deniedUrl(validator, url) {same(validator(url), '', 'URL non autorisée acceptée : ' + url);}

same(escape('<img src=x onerror=alert(1)>'), '&lt;img src=x onerror=alert(1)&gt;');
same(escape('"><svg/onload=alert(1)>'), '&quot;&gt;&lt;svg/onload=alert(1)&gt;');
same(escape("A & B 'C'"), 'A &amp; B &#039;C&#039;');
same(escape(null), '');
same(escape('Compétences publiques'), 'Compétences publiques');
same(doc('documents/03_Livre_Nova_Version_Courte.pdf'), 'documents/03_Livre_Nova_Version_Courte.pdf');
same(journal('index.html'), 'index.html');
same(journal('finances.html#budget'), 'finances.html#budget');

[
  'javascript:alert(1)', 'https://evil.example/file.pdf', '//evil.example/file.pdf',
  'documents/../secrets.pdf', 'documents/%2e%2e/secrets.pdf',
  'documents/file.pdf" onclick="alert(1)', 'documents/file.svg',
  'documents/file.pdf?download=1', '/documents/file.pdf',
].forEach(x => deniedUrl(doc, x));

[
  'javascript:alert(1)', 'https://evil.example', '//evil.example/',
  '/index.html', '../admin/index.html', 'index.html" onclick="alert(1)',
  'index.html?next=//evil.example', 'data:text/html,<script>alert(1)</script>',
].forEach(x => deniedUrl(journal, x));

const malicious = {
  id: 'resume',
  section: '<img src=x onerror=alert(1)>',
  title: '"><svg/onload=alert(2)>',
  description: '<script>alert(3)</script>',
  path: 'javascript:alert(4)',
};
const html = card(malicious);
assert.ok(!html.includes('<img src=x'), 'Injection HTML dans la section.');
assert.ok(!html.includes('<svg/onload'), 'Injection HTML dans le titre.');
assert.ok(!html.includes('<script>alert'), 'Injection HTML dans la description.');
assert.ok(!html.includes('javascript:alert'), 'Lien de téléchargement malveillant.');
assert.ok(html.includes('&lt;script&gt;'), 'Texte correctement échappé absent.');
checks += 5;

const valid = card({
  id:'programme', section:'Archives publiques',
  title:'Programme', description:'Document public',
  path:'documents/07_Programme_Electoral_Complet_Projet_Nova.pdf'
});
assert.ok(valid.includes('href="documents/07_Programme_Electoral_Complet_Projet_Nova.pdf"'));
checks++;
assert.ok(valid.includes('visionneuse.html?doc=programme'));
checks++;

const marker = '$' + '{';
const mandatoryRenderSnippets = [
  "function text(v){return(v===undefined||v===null||v==='')?'—':novaEscapeHtml(v);}",
  "Number.isNaN(d.getTime())?text(value):",
  'href="' + marker + 'novaEscapeHtml(novaSafeJournalHref(e.link))}"',
  "novaSafeJournalHref(e.link)?",
  'href="' + marker + 'novaEscapeHtml(documentUrl)}"',
];
for (const snippet of mandatoryRenderSnippets) {
  assert.ok(src.includes(snippet), 'Régression de rendu sécurisé : ' + snippet);
  checks++;
}
assert.equal(src.includes('href="' + marker + 'e.link}"'), false);
assert.equal(src.includes('<h3>' + marker + 'd.title}</h3>'), false);
checks += 2;
// Le second runtime conservé pour les archives doit avoir les mêmes barrières.
const legacy = fs.readFileSync(path.join(__dirname, '../projets/projet-nova/assets/script.js'), 'utf8');
const legacyPrefixEnd = legacy.indexOf('(function(){');
const legacyCardStart = legacy.indexOf('      const card=d=>');
const legacyCardEnd = legacy.indexOf('\n      function render()', legacyCardStart);
assert.ok(legacyPrefixEnd > 0 && legacyCardStart > 0 && legacyCardEnd > legacyCardStart);
const legacySandbox = {};
vm.runInNewContext(legacy.slice(0, legacyPrefixEnd) + '\n'
  + legacy.slice(legacyCardStart, legacyCardEnd)
  + '\nglobalThis.testFns = {novaLegacyEscapeHtml, novaLegacySafeDocumentHref, card};',
  legacySandbox, {timeout: 2000});
const {novaLegacyEscapeHtml:legacyEscape,
  novaLegacySafeDocumentHref:legacyHref, card:legacyCard} = legacySandbox.testFns;
same(legacyEscape('<svg onload=alert(1)>'), '&lt;svg onload=alert(1)&gt;');
same(legacyHref('documents/test.pdf'), 'documents/test.pdf');
deniedUrl(legacyHref, 'javascript:alert(1)');
deniedUrl(legacyHref, 'documents/../../secret.pdf');
const legacyRendered = legacyCard(malicious);
assert.ok(!legacyRendered.includes('<img src=x') && !legacyRendered.includes('<svg/onload')
  && !legacyRendered.includes('javascript:alert(4)'), 'Injection encore possible dans les archives historiques.');
checks++;
assert.ok(legacy.includes("function text(v){return(v===undefined||v===null||v==='')?'—':novaLegacyEscapeHtml(v);}"),
  'Ancienne table financière non échappée.');
checks++;

console.log('PASS: ' + checks + ' contrôles d’échappement HTML et d’URL NOVA avec données fictives.');
