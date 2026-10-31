'use strict';
// Tests hors réseau des vrais lecteurs TS Edge (coffre personnel + Mon IA).
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..', 'supabase', 'functions');
const encode = value => new TextEncoder().encode(value);

function source(name) {
  return fs.readFileSync(path.join(root, name, 'index.ts'), 'utf8');
}

function reader(name, timeoutMs = 1500) {
  const code = source(name);
  assert.match(code, /const MAX_REQUEST_CHUNKS = 4096;/);
  assert.match(code, /const REQUEST_READ_TIMEOUT_MS = 15000;/);
  assert.match(code, /'REQUEST_TIMEOUT'/);
  assert.match(code, name === 'get-novel-file-url'
    ? /if\s*\(\s*message\s*===\s*'REQUEST_TIMEOUT'\s*\)[\s\S]{0,180}408/
    : /if\s*\(\s*code\s*===\s*'REQUEST_TIMEOUT'\s*\)[\s\S]{0,180}408/);
  const novel = name === 'get-novel-file-url';
  const start = code.indexOf(novel ? 'async function readBoundedJson(req:Request){' : 'async function readBoundedJson(req: Request) {');
  const end = code.indexOf(novel ? '\nDeno.serve(' : '\nfunction safeText(', start);
  assert.ok(start >= 0 && end > start, name + ': lecteur TS introuvable');
  const js = code.slice(start, end)
    .replace(/req:\s*Request/, 'req')
    .replace(/const chunks:\s*Uint8Array\[\]\s*=\s*\[\];/, 'const chunks = [];')
    .replace('return parsed as Record<string, unknown>;', 'return parsed;');
  const cap = name === 'conscience-vault' ? 6 * 1024 * 1024 + 64 * 1024 : name === 'get-novel-file-url' ? 2048 : 16 * 1024;
  return new Function('MAX_REQUEST_BYTES', 'MAX_REQUEST_CHUNKS',
    'REQUEST_READ_TIMEOUT_MS', js + '\nreturn readBoundedJson;')(
      cap, 4096, timeoutMs);
}

function request(chunks, { length = null, hang = false, type = 'application/json' } = {}) {
  let index = 0;
  let cancelled = 0;
  let readerStarted = 0;
  const body = new ReadableStream({
    pull(controller) {
      if (index < chunks.length) controller.enqueue(chunks[index++]);
      else if (!hang) controller.close();
    },
    cancel() { cancelled++; }
  });
  return {
    req: {
      headers: new Headers({
        'content-type': type,
        ...(length === null ? {} : { 'content-length': length })
      }),
      body: { getReader() { readerStarted++; return body.getReader(); } }
    },
    get cancelled() { return cancelled; },
    get readerStarted() { return readerStarted; }
  };
}

for (const name of ['conscience-vault', 'personal-ai', 'get-novel-file-url']) {
  test(name + ' : JSON UTF-8 fragmenté légitime accepté', async () => {
    const value = encode('{"nom":"Élève","ok":true}');
    const input = request([value.slice(0, 9), value.slice(9, 10), value.slice(10)]);
    assert.deepEqual(await reader(name)(input.req), { nom: 'Élève', ok: true });
  });

  test(name + ' : un corps au-delà de la borne est annulé', async () => {
    const cap = name === 'conscience-vault' ? 6 * 1024 * 1024 + 64 * 1024 : name === 'get-novel-file-url' ? 2048 : 16 * 1024;
    const input = request([encode('{"a":"'), encode('x'.repeat(cap)), encode('"}')]);
    await assert.rejects(reader(name)(input.req), /REQUEST_TOO_LARGE/);
    assert.equal(input.cancelled, 1);
  });

  test(name + ' : 4097 fragments minuscules sont rejetés', async () => {
    const input = request([encode('{'), ...Array.from({ length: 4098 }, () => encode('x'))]);
    await assert.rejects(reader(name)(input.req), /REQUEST_TOO_LARGE/);
    assert.equal(input.cancelled, 1);
  });

  test(name + ' : délai absolu sur lecture suspendue, avec annulation', async () => {
    const input = request([encode('{"a":')], { hang: true });
    await assert.rejects(reader(name, 35)(input.req), /REQUEST_TIMEOUT/);
    assert.equal(input.cancelled, 1);
  });

  test(name + ' : Content-Length ambigu bloqué avant accès au flux', async () => {
    const input = request([encode('{}')], { length: '1, 2' });
    await assert.rejects(reader(name)(input.req), /REQUEST_TOO_LARGE/);
    assert.equal(input.readerStarted, 0);
  });

  test(name + ' : type de fragment, UTF-8 et racine JSON stricts', async () => {
    for (const bytes of [new Int16Array([123]), Uint8Array.of(0xc3, 0x28), encode('[]')]) {
      const input = request([bytes]);
      await assert.rejects(reader(name)(input.req), /INVALID_JSON/);
    }
  });
}
