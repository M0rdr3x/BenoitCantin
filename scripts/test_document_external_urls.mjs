#!/usr/bin/env node
// Runtime test of the actual get-document-url URL policy, not a duplicate.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const edge=readFileSync(resolve(root,'supabase/functions/get-document-url/index.ts'),'utf8');
const start=edge.indexOf("const DOCUMENT_URL_BASE=");
const end=edge.indexOf('\nasync function readLimitedJson(',start);
assert.ok(start>=0&&end>start,'The production URL guard was not found');
const implementation=edge.slice(start,end).replace('value:string','value');
const externalUrlAllowed=new Function(implementation+'\nreturn externalUrlAllowed;')();

for(const value of [
  '/', '/projets/sinjira/documents/roman.pdf', '/compte/securite.html?tab=2#titre',
  'https://www.benoitcantin.com/projets/sinjira/', 'https://example.org/public.pdf',
  '/'+ 'a'.repeat(2047)
]){
  assert.equal(externalUrlAllowed(value),true,'Legitimate document URL rejected: '+value.slice(0,90));
}

const rejected=[
  '', 'not-a-url', '#fragment', '?download=1', '//evil.example/file.pdf',
  '/\\evil.example/file.pdf', '/\\/evil.example/file.pdf',
  'https:\\evil.example\\path', 'http://example.org/a',
  'javascript:alert(1)', 'data:text/html,<h1>X</h1>', 'file:///etc/passwd',
  'https://user:pass@example.org/private.pdf', 'https://user@example.org/private.pdf',
  'https://example.org\\@untrusted.example/a',
  '/bad\npath', '/bad\rpath', '/bad\tpath', '/bad\u0000path',
  '/bad\u007fpath', ' /projets/sinjira/', '/projets/sinjira/ ',
  'https://example.org/path\n', '/'+ 'x'.repeat(2048)
];
for(const value of rejected){
  assert.equal(externalUrlAllowed(value),false,'Unsafe document URL allowed: '+JSON.stringify(value).slice(0,130));
}
// Server-side access decisions must still precede either kind of document link.
const access=edge.indexOf('if(userRank<(ranks[doc.access_level]||999))');
const external=edge.indexOf('if(doc.external_url){');
const signed=edge.indexOf('createSignedUrl(doc.storage_path,600)');
assert.ok(access>0&&external>access&&signed>external,'Access gate must precede document links');
assert.ok(edge.includes('externalUrlAllowed(url)'),'URL policy not enforced in handler');
assert.ok(!edge.includes('await req.text()'),'Unbounded public request reader restored');
console.log('PASS: actual document URL guard rejects ambiguous slash/backslash origins, credentials, protocols and control characters; server access gate precedes links.');
