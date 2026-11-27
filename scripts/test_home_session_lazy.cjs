const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/js/home-session-lazy-v24-5-1.js'), 'utf8');
const target = "import('./v19-session.js?v=24.5.1')";
assert.equal(source.split(target).length, 2);
class Element {
  constructor(account = false) { this.account = account; }
  closest(selector) {
    assert.equal(selector, '[data-sinjira-session-nav]');
    return this.account ? this : null;
  }
}
function run(readyState, activeElement = null, online = true) {
  const events = new Map(), docEvents = new Map(), timers = new Map(), classes = new Set();
  let imports = 0;
  const navigator = {onLine: online};
  const window = {
    addEventListener: (name, cb) => events.set(name, cb),
    removeEventListener: (name, cb) => { if (events.get(name) === cb) events.delete(name); },
    setTimeout: (cb, ms) => { assert.equal(ms, 60000); timers.set(1, cb); return 1; },
    clearTimeout: id => timers.delete(id)
  };
  const document = {
    readyState, activeElement,
    documentElement: {classList: {toggle(name, on) { if (on) classes.add(name); else classes.delete(name); }}},
    addEventListener(name, cb, options) { assert.equal(options.capture, true); docEvents.set(name, cb); },
    removeEventListener(name, cb, capture) { assert.equal(capture, true); if(docEvents.get(name)===cb)docEvents.delete(name); }
  };
  vm.runInNewContext(source.replace(target, 'loadModule()'), {
    window, document, navigator, Element, loadModule: () => { imports++; return Promise.resolve(); }
  });
  return {events, docEvents, timers, navigator, classes, imports: () => imports};
}
function verifyLoaded(state) {
  assert.equal(state.imports(), 1);
  assert.equal(state.docEvents.size, 0);
  assert.equal(state.events.has('load'), false);
  assert.equal(state.timers.size, 0);
  assert.equal(state.events.has('online'), true);
  assert.equal(state.events.has('offline'), true);
}
for (const event of ['pointerdown','focusin']) {
  const early = run('interactive');
  const callback = early.docEvents.get(event);
  assert.equal(early.timers.size, 0);
  callback({target: new Element(false)});
  callback({target: null});
  assert.equal(early.imports(), 0);
  callback({target: new Element(true)});
  callback({target: new Element(true)});
  verifyLoaded(early);
}
const late = run('interactive');
late.events.get('load')();
assert.equal(late.timers.size, 1);
late.docEvents.get('focusin')({target: new Element(false)});
assert.equal(late.imports(), 0);
late.docEvents.get('pointerdown')({target: new Element(true)});
verifyLoaded(late);
const idle = run('complete');
idle.timers.get(1)();
verifyLoaded(idle);
verifyLoaded(run('interactive', new Element(true)));
const offline = run('complete', null, false);
assert.equal(offline.classes.has('offline'), true);
offline.navigator.onLine = true;
offline.events.get('online')();
assert.equal(offline.classes.has('offline'), false);
offline.navigator.onLine = false;
offline.events.get('offline')();
assert.equal(offline.classes.has('offline'), true);
assert.equal(offline.imports(), 0);
console.log('OK session accueil : intention compte, interactions publiques, temporisation, réseau et nettoyage.');
