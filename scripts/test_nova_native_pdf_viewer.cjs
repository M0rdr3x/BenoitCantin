#!/usr/bin/env node
'use strict';
// Exécute le véritable client NOVA dans un DOM fictif, sans PDF ni réseau.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const ROOT = path.resolve(__dirname, '..');
const HTML = fs.readFileSync(path.join(ROOT, 'projets/projet-nova/visionneuse.html'), 'utf8');
const CLIENT = fs.readFileSync(path.join(ROOT, 'projets/projet-nova/assets/pdf-viewer-native.js'), 'utf8');
const ORIGIN = 'https://www.benoitcantin.com/projets/projet-nova/visionneuse.html';

class Element {
  constructor(tag = 'div') {
    this.tag = tag;
    this.children = [];
    this.attributes = {};
    this.listeners = {};
    this.textContent = '';
    this.value = '';
    this.href = '';
    this.src = '';
    this.disabled = false;
    this.className = '';
  }
  set innerHTML(_) {
    throw new Error('HTML actif interdit dans le catalogue PDF');
  }
  appendChild(child) { this.children.push(child); }
  replaceChildren(...children) { this.children = [...children]; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  removeAttribute(name) {
    delete this.attributes[name];
    if (name === 'href') this.href = '';
  }
  addEventListener(type, fn) {
    assert.equal(typeof fn, 'function');
    this.listeners[type] = fn;
  }
  emit(type) { assert.ok(this.listeners[type], 'écouteur absent: ' + type); this.listeners[type](); }
}

const good = (overrides = {}) => ({
  id: 'resume', order: '01', title: 'Résumé public',
  path: 'documents/resume.pdf', file: 'resume.pdf', ...overrides,
});

function boot(entries, search = '') {
  const ids = [
    'pdfPages', 'docSelect', 'viewerTitle', 'viewerStatus', 'downloadBtn',
    'pageInfo', 'prevPage', 'nextPage', 'zoomIn', 'zoomOut',
  ];
  const els = Object.fromEntries(ids.map(id => [id, new Element()]));
  const calls = [];
  const created = [];
  const sandbox = {
    window: {NOVA_DOCUMENTS: entries},
    document: {
      getElementById(id) { return els[id]; },
      createElement(tag) {
        assert.ok(['option', 'iframe'].includes(tag), 'élément non approuvé: ' + tag);
        created.push(tag);
        return new Element(tag);
      },
    },
    location: {search, href: ORIGIN + search},
    history: {replaceState(state, unused, url) { calls.push(url); }},
    URL, URLSearchParams,
    console: {error() { throw new Error('aucun détail PDF ne doit être journalisé'); }},
  };
  vm.runInNewContext(CLIENT, sandbox, {filename: 'pdf-viewer-native.js', timeout: 1500});
  return {els, calls, created};
}

test('le PDF natif local et le téléchargement contrôlé restent disponibles', () => {
  const r = boot([good()]);
  assert.equal(r.els.pdfPages.children.length, 1);
  const frame = r.els.pdfPages.children[0];
  assert.equal(frame.tag, 'iframe');
  assert.equal(frame.src, 'documents/resume.pdf#page=1&zoom=120');
  assert.equal(frame.attributes.referrerpolicy, 'no-referrer');
  assert.equal(frame.attributes.title, 'Document PDF : Résumé public');
  assert.equal(frame.attributes.sandbox, undefined, 'le navigateur doit pouvoir afficher son lecteur natif');
  assert.equal(r.els.downloadBtn.href, 'documents/resume.pdf');
  assert.equal(r.els.downloadBtn.attributes.download, 'resume.pdf');
  assert.equal(r.els.docSelect.children.length, 1);
  assert.equal(r.els.docSelect.children[0].textContent, '01 — Résumé public');
  assert.equal(r.calls.length, 1);
});

test('la sélection par identifiant public n’autorise pas une URL arbitraire', () => {
  const r = boot([good(), good({
    id:'manifeste',path:'documents/manifeste.pdf',file:'manifeste.pdf',
    title:'Manifeste',order:'05',
  })], '?doc=manifeste&token=synthetic#evil');
  assert.equal(r.els.docSelect.value, 'manifeste');
  assert.equal(r.els.downloadBtn.href, 'documents/manifeste.pdf');
  const url = new URL(r.calls[0]);
  assert.equal(url.search, '?doc=manifeste');
  assert.equal(url.hash, '');
  assert.ok(!r.calls[0].includes('token='));
});

test('le titre HTML hostile est toujours affiché comme texte, jamais interprété', () => {
  const title = '<img src=x onerror=alert(1)><svg onload=alert(1)>';
  const r = boot([good({title})]);
  assert.equal(r.els.viewerTitle.textContent, title);
  assert.equal(r.els.docSelect.children[0].textContent, '01 — ' + title);
  assert.equal(r.els.pdfPages.children[0].attributes.title, 'Document PDF : ' + title);
});

test('les chemins traversants, schémas externes, query et fragments sont refusés', () => {
  const invalid = [
    'https://evil.invalid/file.pdf', '//evil.invalid/file.pdf',
    '../secret.pdf', '/documents/resume.pdf', 'data:application/pdf;base64,eA==',
    'javascript:alert(1)', 'documents/../evil.pdf',
    'documents/subfolder/evil.pdf', 'documents/resume.pdf?token=secret',
    'documents/resume.pdf#page=1', 'documents/%2e%2e.pdf',
    'documents/a..b.pdf', 'documents/evil.svg', 'documents/evil.pdf/anything',
  ];
  const docs = invalid.map((value, i) => good({
    id:'evil-'+i, path:value, file:value.split('/').pop(),
  }));
  const r = boot([...docs, good()]);
  assert.equal(r.els.docSelect.children.length, 1);
  assert.equal(r.els.pdfPages.children[0].src, 'documents/resume.pdf#page=1&zoom=120');
  assert.equal(r.els.downloadBtn.href, 'documents/resume.pdf');
});

test('les fichiers et IDs incohérents ou dupliqués ne sont pas présentés', () => {
  const r = boot([
    good({id:'../external',file:'resume.pdf'}),
    good({id:'resume',file:'other.pdf'}),
    good(), good({title:'DUPLICATE'}),
    good({id:'autre',path:'documents/Autre.pdf',file:'Autre.pdf'}),
  ]);
  assert.equal(r.els.docSelect.children.length, 2);
  assert.equal(r.els.docSelect.children[0].textContent, '01 — Résumé public');
  assert.equal(r.els.docSelect.children[1].value, 'autre');
});

test('aucun chemin PDF non approuvé : toutes les commandes restent verrouillées', () => {
  const r = boot([good({path:'https://evil.invalid/evil.pdf',file:'evil.pdf'})]);
  assert.equal(r.els.pdfPages.children.length, 0);
  assert.equal(r.els.downloadBtn.href, '');
  for (const id of ['docSelect','prevPage','nextPage','zoomIn','zoomOut','downloadBtn']) {
    assert.equal(r.els[id].disabled, true, id);
  }
  assert.ok(r.els.viewerStatus.textContent.includes('Aucun document'));
});

test('page et zoom ne modifient que des fragments numériques bornés', () => {
  const r = boot([good()]);
  const frame = r.els.pdfPages.children[0];
  r.els.nextPage.emit('click');
  assert.equal(frame.src, 'documents/resume.pdf#page=2&zoom=120');
  r.els.prevPage.emit('click');
  assert.equal(frame.src, 'documents/resume.pdf#page=1&zoom=120');
  assert.equal(r.els.prevPage.disabled, true);
  r.els.zoomIn.emit('click');
  assert.equal(frame.src, 'documents/resume.pdf#page=1&zoom=135');
  r.els.zoomOut.emit('click');
  assert.equal(frame.src, 'documents/resume.pdf#page=1&zoom=120');
});

test('les choix extérieurs ou invalides ne modifient pas le PDF actuel', () => {
  const r = boot([good()]);
  const frame = r.els.pdfPages.children[0];
  r.els.docSelect.value = '__proto__';
  r.els.docSelect.emit('change');
  assert.equal(r.els.pdfPages.children[0], frame);
  assert.equal(frame.src, 'documents/resume.pdf#page=1&zoom=120');
});

test('la page n’importe plus de moteur PDF.js ou de worker tiers', () => {
  assert.ok(HTML.includes('assets/pdf-viewer-native.js?v=1'));
  for (const unsafe of ['cdnjs.cloudflare.com', 'pdf.min.js', 'pdf.min.mjs',
    'pdf.worker', 'pdfjsLib', 'getDocument(']) {
    assert.ok(!HTML.includes(unsafe), 'ancienne dépendance PDF dangereuse: ' + unsafe);
    assert.ok(!CLIENT.includes(unsafe), 'ancienne dépendance dans le client: ' + unsafe);
  }
  assert.ok(!/<script\s+[^>]*src\s*=\s*"https?:/i.test(HTML),
    'aucun script HTTP extérieur propre à la visionneuse');
});

test('les mécanismes de rendu HTML actif et exécution dynamique sont absents', () => {
  for (const forbidden of [/\.innerHTML\s*=/, /\bdocument\.write\s*\(/,
    /\b(?:eval|Function)\s*\(/, /\bsrcdoc\s*=/]) {
    assert.doesNotMatch(CLIENT, forbidden);
  }
  assert.match(CLIENT, /PATH_RE\.exec\(path\)/);
  assert.match(CLIENT, /root\.replaceChildren\(frame\)/);
  assert.match(CLIENT, /option\.textContent\s*=/);
});
