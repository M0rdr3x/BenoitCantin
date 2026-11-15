#!/usr/bin/env node
import assert from 'node:assert/strict';
import test from 'node:test';
import {
  privateDocumentLocationValid,
  isVerifiedPrivateDocumentBucket
} from '../supabase/functions/_shared/private-document-storage.mjs';

test('accepte un bucket privé exact et un chemin de document normal', () => {
  assert.equal(privateDocumentLocationValid('sinjira-private-documents','accounts/123/file.pdf'),true);
  assert.equal(privateDocumentLocationValid('a','documents/report.txt'),true);
  assert.equal(privateDocumentLocationValid('private.documents','docs/rapport_été.docx'),true);
  assert.equal(isVerifiedPrivateDocumentBucket({id:'sinjira-private-documents',public:false},'sinjira-private-documents'),true);
});

test('refuse les noms de buckets ambigus ou non canoniques', () => {
  for(const name of ['',null,{},'Hello','/private','private/x','private%2fx','private?name',' private','private '])
    assert.equal(privateDocumentLocationValid(name,'docs/report.pdf'),false,String(name));
});

test('refuse les traversées, chemins vides et chemins à composantes ambiguës', () => {
  for(const path of ['',null,{},'/docs/file.pdf','docs//file.pdf','docs/../file.pdf','./file.pdf','docs/./file.pdf','docs/.','docs/..','docs/ /file.pdf',' docs/file.pdf','docs/file.pdf '])
    assert.equal(privateDocumentLocationValid('private',path),false,String(path));
});

test('refuse les paramètres URL, l’encodage, les séparateurs alternatifs et les contrôles', () => {
  for(const path of ['docs/%2e%2e/file.pdf','docs/file%252f.pdf','docs/file.pdf?download=true','docs/file.pdf#section','docs\\file.pdf','docs/file\n.pdf','docs/file\0.pdf','docs/\tfile.pdf'])
    assert.equal(privateDocumentLocationValid('private',path),false,JSON.stringify(path));
});

test('refuse les chemins et buckets surdimensionnés', () => {
  assert.equal(privateDocumentLocationValid('a'.repeat(64),'file.pdf'),false);
  assert.equal(privateDocumentLocationValid('private','x'.repeat(1025)),false);
});

test('fail closed si le bucket est public ou manquant', () => {
  const id='private-documents';
  for(const metadata of [null,undefined,[],{}, {id}, {id,public:true}, {id,public:'false'}, {id,public:0}, {id:'other',public:false}, {id:null,public:false}])
    assert.equal(isVerifiedPrivateDocumentBucket(metadata,id),false,JSON.stringify(metadata));
});

test('accepte seulement le booléen false avec identité exact et ne dégrade pas en repli public', () => {
  assert.equal(isVerifiedPrivateDocumentBucket({id:'private-documents',public:false,extra:true},'private-documents'),true);
  assert.equal(isVerifiedPrivateDocumentBucket({id:'private-documents',public:false},'PRIVATE-DOCUMENTS'),false);
});
