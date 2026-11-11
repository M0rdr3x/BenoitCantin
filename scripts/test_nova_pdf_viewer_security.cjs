#!/usr/bin/env node
'use strict';
// Tests du vrai script de la visionneuse, sans réseau, PDF ou compte utilisateur.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../projets/projet-nova/visionneuse.html'), 'utf8');
const opening = '<script>\n(function(){';
const start = html.indexOf(opening);
assert.ok(start >= 0, 'visionneuse: script principal manquant');
const end = html.indexOf('</script>', start);
assert.ok(end > start, 'visionneuse: balise de fermeture manquante');
const source = html.slice(start + '<script>\n'.length, end);
const ORIGIN = 'https://www.benoitcantin.com/projets/projet-nova/visionneuse.html';

class FakeElement {
  constructor() {
    this.children = [];
    this.textContent = '';
    this.value = '';
    this.href = '';
    this.attributes = {};
    this.style = {};
  }
  set innerHTML(_) {
    throw new Error('Insertion HTML interdite dans la visionneuse');
  }
  replaceChildren(...children) { this.children = [...children]; }
  appendChild(child) { this.children.push(child); }
  setAttribute(name, value) { this.attributes[name] = value; }
}

function good(overrides = {}) {
  return {id:'resume', order:'01', title:'Résumé public', path:'documents/resume.pdf', file:'resume.pdf', ...overrides};
}
function boot(documents, search = '') {
  const elements = Object.fromEntries(
    ['docSelect', 'viewerTitle', 'viewerStatus', 'downloadBtn', 'pdfPages',
     'pageInfo', 'prevPage', 'nextPage', 'zoomIn', 'zoomOut']
      .map(id => [id, new FakeElement()]),
  );
  const pageUrl = ORIGIN + search;
  const historyCalls = [];
  const sandbox = {
    window: {NOVA_DOCUMENTS: documents},
    document: {
      getElementById(id) { return elements[id]; },
      createElement(name) {
        assert.equal(name, 'option', 'La sélection ne doit créer que des options sûres');
        return new FakeElement();
      },
    },
    location: {search, href: pageUrl},
    history: {replaceState(_state, _unused, value) { historyCalls.push(value); }},
    URL, URLSearchParams,
    console: {error() {}},
  };
  vm.runInNewContext(source, sandbox, {filename:'visionneuse-inline.js',timeout:1500});
  return {elements, historyCalls};
}

test('le catalogue PDF public conserve son fonctionnement sans écriture HTML', () => {
  const {elements, historyCalls} = boot([good(),good({
    id:'manifeste',order:'02',title:'Manifeste public',
    path:'documents/manifeste.pdf',file:'manifeste.pdf',
  })], '?doc=manifeste');
  assert.equal(elements.docSelect.children.length, 2);
  assert.equal(elements.docSelect.children[1].textContent, '02 — Manifeste public');
  assert.equal(elements.downloadBtn.href, 'documents/manifeste.pdf');
  assert.equal(elements.downloadBtn.attributes.download, 'manifeste.pdf');
  assert.equal(elements.docSelect.value, 'manifeste');
  assert.equal(historyCalls.length, 1);
  assert.ok(historyCalls[0].includes('doc=manifeste'));
});

test('un titre hostile reste du texte et ne peut pas devenir du HTML actif', () => {
  const title = '<img src=x onerror=alert(1)> & <svg onload=alert(2)>';
  const {elements} = boot([good({title})]);
  assert.equal(elements.docSelect.children.length, 1);
  assert.equal(elements.docSelect.children[0].textContent, '01 — ' + title);
  assert.equal(elements.viewerTitle.textContent, title);
  assert.equal(elements.downloadBtn.href, 'documents/resume.pdf');
});

test('lien détourné, traversal, token, encodage et identifiant malformé sont rejetés', () => {
  const untrusted = [
    good({id:'outside',path:'https://evil.example/evil.pdf',file:'evil.pdf'}),
    good({id:'script',path:'javascript:alert(1)',file:'evil.pdf'}),
    good({id:'traversal',path:'documents/../secret.pdf',file:'secret.pdf'}),
    good({id:'percent',path:'documents/%2e%2e.pdf',file:'%2e%2e.pdf'}),
    good({id:'query',path:'documents/a.pdf?token=secret',file:'a.pdf'}),
    good({id:'anchor',path:'documents/a.pdf#fragment',file:'a.pdf'}),
    good({id:'backslash',path:'documents\\a.pdf',file:'a.pdf'}),
    good({id:'slash',path:'//evil.example/a.pdf',file:'a.pdf'}),
    good({id:'mismatch',file:'other.pdf'}),
    good({id:'bad" onclick="alert(1)',path:'documents/evil.pdf',file:'evil.pdf'}),
    null, 'injection', false, 42,
  ];
  const {elements} = boot([...untrusted, good()], '?doc=script');
  assert.equal(elements.docSelect.children.length, 1);
  assert.equal(elements.docSelect.children[0].value, 'resume');
  assert.equal(elements.downloadBtn.href, 'documents/resume.pdf');
});

test('un catalogue vide ou invalide ne crée aucun téléchargement', () => {
  for(const value of [undefined,null,{},'not-an-array',[],[good({path:'data:application/pdf,x'})]]){
    const {elements,historyCalls} = boot(value, '?doc=resume');
    assert.equal(elements.docSelect.children.length, 0);
    assert.equal(elements.downloadBtn.href, '');
    assert.equal(elements.viewerStatus.textContent, 'Aucun document public disponible.');
    assert.deepEqual(historyCalls, []);
  }
});

test('aucune écriture innerHTML ni chemin PDF arbitraire', () => {
  assert.ok(!/\.innerHTML\s*=/.test(source));
  assert.ok(source.includes("pdfjsLib.getDocument({url:d.path"));
  assert.ok(source.includes("filter(isSafeDocument)"));
  assert.ok(source.includes("select.replaceChildren()"));
});
