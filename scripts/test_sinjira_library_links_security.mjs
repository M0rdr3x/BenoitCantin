#!/usr/bin/env node
// Tests du vrai rendu des cartes SINJIRA, sans réseau ni données réelles.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const accountSource = readFileSync(resolve(root, 'assets/js/sinjira-account-v18.js'), 'utf8');
const supabaseSource = readFileSync(resolve(root, 'assets/js/sinjira-supabase.js'), 'utf8');

const start = supabaseSource.indexOf('export function safeInternalDestination(');
const end = supabaseSource.indexOf('export async function requireUser(', start);
assert.ok(start >= 0 && end > start, 'Le filtre de destination local doit exister');
const helperContext = { location: { origin: 'https://www.benoitcantin.com' }, URL };
const helper = supabaseSource.slice(start, end).replace(/^export /, '');
const safeInternalDestination = vm.runInNewContext(helper + '\nsafeInternalDestination', helperContext, { timeout: 3000 });

const body = accountSource.replace(/^import [^\n]+\n/, '');
assert.ok(body.startsWith('const page='), 'Le test doit exécuter le vrai module Compte');
assert.match(accountSource, /safeInternalDestination\(n\.demo_path,''\)/);
assert.match(accountSource, /safeInternalDestination\(n\.public_path,'\/projets\/sinjira\/romans\/'\)/);

function escapeHtml(value = '') {
  return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

async function render(source, novels) {
  const box = { innerHTML: '' };
  const sandbox = {
    document: {
      body: { dataset: { v18Page: 'reads' } },
      querySelector(selector) { return selector === '[data-reader-library]' ? box : null; }
    },
    getSupabase() {
      return {
        from(table) {
          return {
            select() {
              if (table === 'novels') {
                return { in() { return { order: async () => ({ data: novels, error: null }) }; } };
              }
              if (table === 'reader_library') {
                return { eq: async () => ({ data: [], error: null }) };
              }
              throw new Error('Table inattendue : ' + table);
            }
          };
        }
      };
    },
    requireUser: async () => ({ id: 'fixture-user' }),
    safeInternalDestination,
    escapeHtml,
    friendlyBackendMessage: v => v,
    formatDate: () => 'date factice',
    console: { warn() {} }
  };
  await vm.runInNewContext(source, sandbox, { timeout: 3000 });
  return box.innerHTML;
}

const novels = [
  {
    id: 'malicious', title: '<img src=x onerror=alert(9)>', description: 'Donnée contrôlée',
    demo_path: 'javascript:alert(1)', public_path: '//evil.example/path',
    volume_label: 'SINJIRA', status: 'demo'
  },
  {
    id: 'safe', title: 'Livre sûr', description: 'Lecture normale',
    demo_path: '/projets/sinjira/romans/lire-demo.html',
    public_path: '/projets/sinjira/romans/', status: 'demo'
  },
  {
    id: 'external', title: 'Lien tiers', description: 'Le lien externe doit être refusé',
    demo_path: 'https://evil.example/route',
    public_path: 'data:text/html,hello', status: 'demo'
  }
];

test('filtre URL partagé : schémas actifs, domaines et chemins ambigus refusés', () => {
  for (const unsafe of [
    'javascript:alert(1)', 'data:text/html,test', 'https://evil.example/',
    '//evil.example/path', ' /projets/sinjira/', '/%2f%2fevil.example',
    '/projets\\evil', '/%2e%2e/compte/index.html'
  ]) {
    assert.equal(safeInternalDestination(unsafe, ''), '', 'Refus attendu: ' + unsafe);
  }
  assert.equal(
    safeInternalDestination('/projets/sinjira/romans/lire-demo.html', ''),
    '/projets/sinjira/romans/lire-demo.html'
  );
});

test('cartes bibliothèques : aucune URL active ni tierce ne devient cliquable', async () => {
  const html = await render(body, novels);
  const hrefs = [...html.matchAll(/href="([^"]+)"/g)].map(x => x[1]);
  assert.deepEqual(hrefs, [
    '/projets/sinjira/romans/',
    '/projets/sinjira/romans/lire-demo.html',
    '/projets/sinjira/romans/',
    '/projets/sinjira/romans/'
  ]);
  assert.doesNotMatch(html, /href="(?:javascript:|data:|https?:|\/\/)/i);
  assert.doesNotMatch(html, /<img\\b/i);
  assert.match(html, /&lt;img src=x onerror=alert\(9\)&gt;/);
});

test('mutation négative : un retour aux liens bruts fait échouer le contrat', async () => {
  assert.ok(body.includes("const demoHref=safeInternalDestination(n.demo_path,'');"));
  const mutated = body.replace(
    "const demoHref=safeInternalDestination(n.demo_path,'');",
    "const demoHref=n.demo_path;"
  );
  assert.notEqual(mutated, body, 'Mutation inactive');
  const html = await render(mutated, novels);
  assert.match(html, /href="javascript:alert\(1\)"/);
});
