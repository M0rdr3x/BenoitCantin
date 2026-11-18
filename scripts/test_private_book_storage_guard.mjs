#!/usr/bin/env node
import test from 'node:test';
import assert from 'node:assert/strict';
import { privateBookLocationValid, isVerifiedPrivateBucket } from '../supabase/functions/_shared/private-book-storage-guard.mjs';

test('chemins PDF privés valides', () => {
  for (const [bucket,path] of [
    ['sinjira-livres-prives','livre-i/La Cendre du Jugement.pdf'],
    ['sinjira_private_01','editions/édition complète.PDF'],
    ['livres.prives','2026/roman-01.pdf'], ['a','livre.pdf']
  ]) assert.equal(privateBookLocationValid(bucket,path),true,bucket+': '+path);
});

test('identifiants de bucket non canoniques rejetés', () => {
  for (const bucket of [
    '', 'PubLic', 'livre/privé', 'livre\\privé', 'livre?x',
    '.hidden', '-books', 'books ', 'books\n', 'a'.repeat(65), null, 42
  ]) assert.equal(privateBookLocationValid(bucket,'books/file.pdf'),false,String(bucket));
});

test('traversée de chemins, URL, encodage, extension et données malformées rejetés', () => {
  const bad=[
    '', '/', '/livre.pdf', 'livre.pdf/', 'dir//livre.pdf',
    'dir/../livre.pdf', 'dir/./livre.pdf', '../livre.pdf', './livre.pdf',
    'dir/.. /livre.pdf', 'dir/ ./livre.pdf', 'dir\\livre.pdf',
    'dir/%2e%2e/livre.pdf', 'dir/%2F/livre.pdf',
    'dir/livre.pdf?download=1', 'dir/livre.pdf#fragment',
    'dir/\nfile.pdf', 'dir/\u0000file.pdf', 'https://attacker.example/livre.pdf',
    'dir/livre.txt', 'dir/.hidden', ' dir/livre.pdf',
    'dir/livre.pdf ', 'x'.repeat(1025)+'.pdf', null, {}, ['dir/livre.pdf']
  ];
  for (const path of bad) assert.equal(privateBookLocationValid('private-books',path),false,JSON.stringify(path));
});

test('le serveur exige le drapeau booléen public=false et le bon id de bucket', () => {
  assert.equal(isVerifiedPrivateBucket({id:'private-books',public:false},'private-books'),true);
  for (const meta of [
    {id:'private-books',public:true}, {id:'private-books',public:'false'},
    {id:'private-books'}, {id:'other-bucket',public:false},
    null, [], {}, 'private-books'
  ]) assert.equal(isVerifiedPrivateBucket(meta,'private-books'),false,JSON.stringify(meta));
  assert.equal(isVerifiedPrivateBucket({id:'private-books',public:false},'other-bucket'),false);
});
