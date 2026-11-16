import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import { readLimitedUtf8BodyWithDeadline } from '../supabase/functions/_shared/read-chunk-deadline.mjs';
import { readLimitedBinaryResponse } from '../supabase/functions/_shared/limited-body.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(resolve(root, 'supabase/functions/send-game-report/index.ts'), 'utf8');

function productionJsonParser(timeoutMs = 45) {
  const start = source.indexOf('async function readLimitedJson(');
  const end = source.indexOf('const MAX_TEXT =', start);
  assert.ok(start !== -1 && end > start, 'Le parser serveur réel doit rester accessible au test');
  const functionText = source.slice(start, end).replace(
    'async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }>',
    'async function readLimitedJson(req)'
  );
  assert.ok(!functionText.includes('req: Request'), 'Retirer uniquement le typage TypeScript de la signature');
  const environment = {
    readLimitedUtf8BodyWithDeadline,
    privateJson: (data, status = 200) => new Response(JSON.stringify(data), {
      status, headers: { 'Cache-Control': 'private, no-store, max-age=0' }
    }),
    Response
  };
  const script = [
    "const FUNCTION_VERSION='24.5.2';",
    'const MAX_REQUEST_BYTES=220_000;',
    'const MAX_REQUEST_READ_TIMEOUT_MS=' + timeoutMs + ';',
    functionText,
    'readLimitedJson'
  ].join('\n');
  return vm.runInNewContext(script, environment, { timeout: 1000 });
}

function request(body, contentType = 'application/json', options = {}) {
  return new Request('https://edge.invalid/functions/v1/send-game-report', {
    method: 'POST',
    headers: { 'content-type': contentType, ...options.headers },
    body,
    ...(body instanceof ReadableStream ? { duplex: 'half' } : {}),
    ...(options.signal ? { signal: options.signal } : {})
  });
}

function neverEndingStream() {
  return new ReadableStream({
    pull() { return new Promise(() => {}); },
    cancel() { return new Promise(() => {}); }
  });
}

test('JSON public valide préservé et type MIME strict', async () => {
  const parse = productionJsonParser();
  const good = await parse(request('{"mode":"download"}', 'application/json; charset=utf-8'));
  assert.deepEqual(JSON.parse(JSON.stringify(good.body)), { mode: 'download' });
  for (const type of ['application/jsonp', 'application/json-sequence', 'text/plain']) {
    const result = await parse(request('{}', type));
    assert.equal(result.response.status, 415, type);
  }
  const invalid = await parse(request('{"broken":'));
  assert.equal(invalid.response.status, 400);
});

test('Content-Length trompeur et plafond réel de 220 000 octets refusés', async () => {
  const parse = productionJsonParser();
  const mismatched = await parse(request('{}', 'application/json', {
    headers: { 'content-length': '220001' }
  }));
  assert.equal(mismatched.response.status, 413);
  const oversized = await parse(request('x'.repeat(220001)));
  assert.equal(oversized.response.status, 413);
});

test('flux bloqué et annulation bloquante : réponse 408, sans attendre cancel()', async () => {
  const parse = productionJsonParser(50);
  const start = performance.now();
  const result = await parse(request(neverEndingStream()));
  assert.equal(result.response.status, 408);
  const payload = await result.response.json();
  assert.equal(payload.code, 'REQUEST_TIMEOUT');
  assert.ok(performance.now() - start < 2000, 'Une annulation bloquée ne doit pas bloquer la réponse');
});

test('déconnexion client et UTF-8 malformé refusés sans exposer de données', async () => {
  const parse = productionJsonParser();
  const ac = new AbortController();
  ac.abort();
  const aborted = await parse(request(neverEndingStream(), 'application/json', { signal: ac.signal }));
  assert.equal(aborted.response.status, 408);
  const malformed = await parse(request(new Uint8Array([0xff, 0xfe])));
  assert.equal(malformed.response.status, 413);
  assert.ok(!(await malformed.response.text()).includes('ff'));
});

function productionPdfDownload(fetchFn, configuredUrl = null) {
  const names = ['MAX_TEMPLATE_BYTES', 'TEMPLATE_FETCH_TIMEOUT_MS',
    'DEFAULT_TEMPLATE_URL', 'TEMPLATE_ORIGIN', 'TEMPLATE_PATH_PREFIX'];
  let declarations = source.split('\n').filter(line =>
    names.some(name => line.startsWith('const ' + name + '='))
  ).join('\n');
  for (const name of names) {
    assert.ok(declarations.includes('const ' + name + '='), 'Constante manquante : ' + name);
  }
  declarations = declarations.replace(
    'const TEMPLATE_FETCH_TIMEOUT_MS=12_000;',
    'const TEMPLATE_FETCH_TIMEOUT_MS=45;'
  );
  const start = source.indexOf('function reportTemplateUrl(){');
  const end = source.indexOf('async function readLimitedJson(', start);
  assert.ok(start !== -1 && end > start, 'Les fonctions PDF réelles doivent rester accessibles');
  const functions = source.slice(start, end).replace('let url:URL;', 'let url;');
  return vm.runInNewContext(
    declarations + '\n' + functions + '\n({ reportTemplateUrl, fetchTemplateBytes })',
    {
      Deno: { env: { get: key => key === 'REPORT_TEMPLATE_URL' ? configuredUrl : '' } },
      fetch: fetchFn,
      AbortSignal,
      URL,
      readLimitedBinaryResponse,
      Response,
      Uint8Array
    },
    { timeout: 1000 }
  );
}

test('modèle PDF public : HTTPS, sans redirection, délai absolu et signature vérifiée', async () => {
  let seen;
  const pdf = productionPdfDownload(async (url, options) => {
    seen = { url, options };
    return new Response(new TextEncoder().encode('%PDF-1.5 fixture'));
  });
  const bytes = await pdf.fetchTemplateBytes();
  assert.equal(String.fromCharCode(...bytes.slice(0, 5)), '%PDF-');
  assert.equal(seen.options.redirect, 'error');
  assert.equal(seen.options.cache, 'no-store');
  assert.ok(seen.options.signal instanceof AbortSignal);
  assert.ok(seen.url.startsWith('https://www.benoitcantin.com/'));
});

test('le chargement PDF suspendu expire et le signal est aborté', async () => {
  let signal;
  const pdf = productionPdfDownload((_url, options) => new Promise((_resolve, reject) => {
    signal = options.signal;
    signal.addEventListener('abort', () => reject(new Error('REMOTE_ABORTED')), { once: true });
  }));
  const started = performance.now();
  await assert.rejects(pdf.fetchTemplateBytes(), /REMOTE_ABORTED/);
  assert.equal(signal.aborted, true);
  assert.ok(performance.now() - started < 2000);
});

test('flux du modèle PDF suspendu est interrompu par le délai réseau', async () => {
  const pdf = productionPdfDownload(async (_url, options) => {
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('%PDF-'));
        options.signal.addEventListener('abort', () => {
          controller.error(new Error('REMOTE_STREAM_ABORTED'));
        }, { once: true });
      }
    });
    return new Response(body);
  });
  await assert.rejects(pdf.fetchTemplateBytes(), /REPORT_TEMPLATE_TOO_LARGE/);
});

test('une origine externe ne déclenche aucun téléchargement PDF', async () => {
  let called = false;
  const pdf = productionPdfDownload(async () => {
    called = true;
    throw new Error('FETCH_INTERDIT');
  }, 'https://evil.invalid/documents/rapport.pdf');
  await assert.rejects(pdf.fetchTemplateBytes(), /REPORT_TEMPLATE_URL_NOT_ALLOWED/);
  assert.equal(called, false);
});
