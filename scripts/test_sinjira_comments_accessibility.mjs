#!/usr/bin/env node
// Tests sans navigateur : contrat de rendu, échappement et annonces accessibles.
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import test from 'node:test';

const read = path => readFileSync(new URL('../' + path, import.meta.url), 'utf8');
const reader = read('assets/js/sinjira-reader.js');
const page = read('projets/sinjira/romans/index.html');
const css = read('assets/css/sinjira-comments-responsive-v2.css');
const source = reader.match(/function spoiler\(c,index\)\{[\s\S]*?\n\}/)?.[0];
assert.ok(source, 'fonction spoiler disponible');
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));
const spoiler = new Function('escapeHtml', source + '\nreturn spoiler;')(escapeHtml);

test('un commentaire normal reste visible et son HTML est neutralisé', () => {
  const markup = spoiler({ body: '<script>alert(1)</script>', spoiler: false }, 0);
  assert.match(markup, /&lt;script&gt;/);
  assert.doesNotMatch(markup, /<script| hidden|data-reveal-spoiler/);
});

test('les divulgâcheurs sont cachés jusqu’à activation volontaire', () => {
  const markup = spoiler({ body: 'Fin du livre', spoiler: true }, 7);
  assert.match(markup, /id="sinjira-divulgacheur-7" data-spoiler-content hidden/);
  assert.match(markup, /aria-controls="sinjira-divulgacheur-7"/);
  assert.match(markup, /aria-expanded="false"/);
  assert.match(reader, /content\.hidden=!revealed/);
  assert.match(reader, /button\.setAttribute\('aria-expanded',String\(revealed\)\)/);
  assert.match(css, /\[data-spoiler-content\]\[hidden\]\s*\{\s*display:none!important/);
});

test('les divulgâcheurs successifs ne partagent pas le même identifiant', () => {
  const first = spoiler({ body: 'Un', spoiler: true }, 0);
  const second = spoiler({ body: 'Deux', spoiler: true }, 1);
  assert.match(first, /sinjira-divulgacheur-0/);
  assert.match(second, /sinjira-divulgacheur-1/);
  assert.doesNotMatch(first, /sinjira-divulgacheur-1/);
});

test('le champ de commentaires est décrit et mesuré sans annonces par frappe', () => {
  assert.match(page, /aria-describedby="commentaire-aide commentaire-compteur"/);
  assert.match(page, /<output[^>]+id="commentaire-compteur"[^>]+data-comment-count aria-live="off"/);
  assert.match(reader, /textarea\?\.addEventListener\('input',updateCount\)/);
  assert.match(reader, /form\.reset\(\);\s*updateCount\(\);/);
  assert.match(css, /\.reader-comment-helper-row/);
});
