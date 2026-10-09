#!/usr/bin/env node
'use strict';

// Tests de non-regression du runtime portail #449, sans navigateur ni reseau.
// Les elements simulent exclusivement l'API DOM utilisee par assets/js/site.js.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'assets', 'js', 'site.js'), 'utf8'
);

function element(tagName) {
  const attrs = {};
  const listeners = {};
  const node = {
    tagName: tagName.toUpperCase(),
    id: '',
    className: '',
    parentNode: null,
    listeners,
    setAttribute(key, value) { attrs[key] = String(value); },
    getAttribute(key) { return Object.hasOwn(attrs, key) ? attrs[key] : null; },
    addEventListener(name, fn) { (listeners[name] ||= []).push(fn); },
    contains(target) { return target === node; },
    fire(name, event = {}) {
      for (const fn of listeners[name] || []) fn(event);
    },
    focus() { node.focusCount = (node.focusCount || 0) + 1; }
  };
  if (tagName.toLowerCase() === 'script') node.noModule = true;
  return node;
}

function scenario({ host = 'www.benoitcantin.com', page = '/', noindex = false, disable = false } = {}) {
  const root = element('html');
  if (disable) root.setAttribute('data-disable-sinjira-assistant', 'true');
  const toggle = element('button');
  const nav = element('nav');
  const robots = element('meta');
  if (noindex) robots.setAttribute('content', 'noindex, nofollow');
  const appended = [];
  const documentListeners = {};
  const windowListeners = {};
  let desktop = false;
  const doc = {
    documentElement: root,
    head: { appendChild(node) { appended.push(node); } },
    querySelector(selector) {
      if (selector === '[data-menu-toggle]') return toggle;
      if (selector === '[data-main-nav]') return nav;
      if (selector === 'meta[name="robots"]') return noindex ? robots : null;
      return null;
    },
    querySelectorAll() { return []; },
    createElement(tag) { return element(tag); },
    addEventListener(name, fn) { (documentListeners[name] ||= []).push(fn); }
  };
  const win = {
    location: { hostname: host, pathname: page, href: 'https://' + host + page },
    crypto: { randomUUID: () => 'test-runtime-uuid' },
    sessionStorage: { getItem: () => null, setItem: () => undefined },
    matchMedia: () => ({ get matches() { return desktop; } }),
    addEventListener(name, fn) { (windowListeners[name] ||= []).push(fn); },
    console: { warn: () => {} }
  };
  vm.runInNewContext(source, { document: doc, window: win, Date, JSON, Math, Object, Array, String, Boolean }, { timeout: 2000, filename: 'site.js' });
  const assetUrls = appended.map(x => x.src || x.href).filter(Boolean);
  const fireDocument = (name, event = {}) => {
    for (const fn of documentListeners[name] || []) fn(event);
  };
  const fireWindow = (name, event = {}) => {
    for (const fn of windowListeners[name] || []) fn(event);
  };
  return { toggle, nav, assetUrls, fireDocument, fireWindow, setDesktop(value) { desktop = value; }, win };
}

const test = scenario();
const opened = () => test.toggle.getAttribute('aria-expanded') === 'true';
assert.equal(test.nav.id, 'navigation-principale');
assert.equal(test.toggle.getAttribute('aria-controls'), 'navigation-principale');
assert.equal(test.toggle.getAttribute('aria-label'), 'Ouvrir le menu');
assert.equal(opened(), false);
assert.match(test.nav.innerHTML, /href="\/projets\/sinjira\/"/);
assert.match(test.nav.innerHTML, /data-sinjira-session-nav/);
test.toggle.fire('click');
assert.equal(opened(), true);
assert.equal(test.toggle.getAttribute('aria-label'), 'Fermer le menu');
assert.match(test.nav.className, /open/);
test.toggle.fire('click');
assert.equal(opened(), false);
test.toggle.fire('click');
const link = element('a');
link.parentNode = test.nav;
test.nav.fire('click', { target: link });
assert.equal(opened(), false, 'Le clic sur un lien doit fermer le menu');
test.toggle.fire('click');
test.fireDocument('keydown', { key: 'Escape' });
assert.equal(opened(), false);
assert.equal(test.toggle.focusCount, 1, 'Echap doit rendre le focus au bouton');
test.toggle.fire('click');
test.fireDocument('pointerdown', { target: element('div') });
assert.equal(opened(), false, 'Un clic hors du menu doit le fermer');
test.toggle.fire('click');
test.fireDocument('pointerdown', { target: test.nav });
assert.equal(opened(), true, 'Un clic interne ne doit pas fermer le menu');
test.setDesktop(true);
test.fireWindow('resize');
assert.equal(opened(), false, 'Passer sur ordinateur doit fermer le menu');
assert.equal(test.nav.className.includes('open'), false);
assert.equal(test.win.__SINJIRA_RUNTIME__.requestId, 'test-runtime-uuid');

function hasAssistant(context) {
  return context.assetUrls.some(x => x.includes('/assets/js/sinjira-assistant.js'));
}
function hasTransparency(context) {
  return context.assetUrls.some(x => x.includes('/assets/js/ai-transparency.js'));
}

assert.equal(hasAssistant(test), false, 'Domaine officiel public: assistant local bloque');
assert.equal(hasTransparency(test), true, 'Transparence IA locale conservee');
assert.equal(hasAssistant(scenario({ page: '/projets/sinjira/codex/' })), false);
assert.equal(hasAssistant(scenario({ page: '/compte/' })), true, 'Assistant local prive conserve');
assert.equal(hasAssistant(scenario({ page: '/app/' })), true);
assert.equal(hasAssistant(scenario({ page: '/histoire-de-vie/' })), false, 'Histoire de vie sensible exclue');
assert.equal(hasAssistant(scenario({ host: 'example.net', page: '/' })), true, 'Preview: aide locale conservee');
assert.equal(hasAssistant(scenario({ noindex: true })), true, 'Espace noindex: aide locale conservee');
assert.equal(hasAssistant(scenario({ disable: true, page: '/compte/' })), false, 'Opt-out explicite respecte');
console.log('PASS site.js: menu mobile (clic, lien, clavier, pointeur, redimensionnement), aria-controls, assistant local et transparence IA.');
