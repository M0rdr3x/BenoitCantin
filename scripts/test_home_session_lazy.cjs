const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/js/home-session-lazy-v24-5-1.js'), 'utf8');
const target = "import('./v19-session.js?v=24.5.1')";
assert.equal(source.split(target).length, 2);
function run(readyState) {
  const events = new Map(), timers = new Map();
  let imports = 0;
  const window = {
    addEventListener: (name, cb) => events.set(name, cb),
    removeEventListener: (name, cb) => { if (events.get(name) === cb) events.delete(name); },
    setTimeout: (cb, ms) => { assert.equal(ms, 60000); timers.set(1, cb); return 1; },
    clearTimeout: id => timers.delete(id)
  };
  vm.runInNewContext(source.replace(target, 'loadModule()'), {
    window, document: {readyState}, loadModule: () => { imports++; return Promise.resolve(); }
  });
  return {events, timers, imports: () => imports};
}
for (const event of ['pointerdown','touchstart','keydown']) {
  const early = run('interactive');
  const callback = early.events.get(event);
  assert.equal(early.timers.size, 0);
  callback();
  callback();
  assert.equal(early.imports(), 1);
  assert.equal(early.events.size, 0);
  assert.equal(early.timers.size, 0);
}
const late = run('interactive');
late.events.get('load')();
assert.equal(late.timers.size, 1);
late.events.get('keydown')();
assert.equal(late.imports(), 1);
assert.equal(late.events.size, 0);
assert.equal(late.timers.size, 0);
const idle = run('complete');
idle.timers.get(1)();
assert.equal(idle.imports(), 1);
assert.equal(idle.events.size, 0);
assert.equal(idle.timers.size, 0);
console.log('OK session accueil : interactions, temporisation et nettoyage.');
