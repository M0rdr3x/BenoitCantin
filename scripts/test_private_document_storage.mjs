#!/usr/bin/env node
import assert from 'node:assert/strict';
import test from 'node:test';
import {
  privateDocumentLocationValid,
  isVerifiedPrivateDocumentBucket,
  privateAdminDocumentUploadPath,
  privateSignedDownloadUrlValid
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

const VALID_UPLOAD_ID='123e4567-e89b-42d3-a456-426614174000';
test('génère un chemin de téléversement uniquement dans le bucket privé et projet canonique',()=>{
  const path=privateAdminDocumentUploadPath(
    'sinjira-private-documents','fracture-du-reseau-mere','compte-rendu','pdf',VALID_UPLOAD_ID
  );
  assert.equal(path,`fracture-du-reseau-mere/${VALID_UPLOAD_ID}/compte-rendu.pdf`);
  assert.equal(privateDocumentLocationValid('sinjira-private-documents',path),true);
});

test('rejette les slugs qui tentent de traverser ou sortir du projet',()=>{
  const bad=['','../other','../../admin','/root','other/project','other\\project','other%2fproject','other?x','other#y',' other','other ','a'.repeat(97),null,{},'UPPER'];
  for(const slug of bad){
    assert.equal(privateAdminDocumentUploadPath('sinjira-private-documents',slug,'file','pdf',VALID_UPLOAD_ID),null,String(slug));
  }
});

test('rejette les identifiants, noms et extensions suspects',()=>{
  const base=['..','./test','file/../../x','file%2epdf','file.pdf?x','file\\evil','file\nbar',null,{}];
  for(const name of base){
    assert.equal(privateAdminDocumentUploadPath('sinjira-private-documents','project',name,'pdf',VALID_UPLOAD_ID),null,JSON.stringify(name));
  }
  for(const ext of ['',null,{},'pdf/evil','PDF','html?x','exe;','x'.repeat(11)]){
    assert.equal(privateAdminDocumentUploadPath('sinjira-private-documents','project','file',ext,VALID_UPLOAD_ID),null,JSON.stringify(ext));
  }
  for(const uuid of ['',null,{},'../victim','123e4567-e89b-42d3-a456-426614174000/evil','123e4567-e89b-62d3-a456-426614174000']){
    assert.equal(privateAdminDocumentUploadPath('sinjira-private-documents','project','file','pdf',uuid),null,JSON.stringify(uuid));
  }
});

test('ne crée jamais de chemin dans un bucket malformé',()=>{
  for(const bucket of ['',null,'PUBLIC/evil','private?x']){
    assert.equal(privateAdminDocumentUploadPath(bucket,'project','file','pdf',VALID_UPLOAD_ID),null,String(bucket));
  }
});

test('une URL signée doit correspondre exactement au stockage et au fichier autorisés',()=>{
  const base='https://storage.example.invalid';
  const bucket='private-documents', path='docs/rapport_été.pdf';
  const token='abc.def.ghi';
  const valid=base+'/storage/v1/object/sign/'+bucket+'/docs/rapport_%C3%A9t%C3%A9.pdf?token='+token;
  assert.equal(privateSignedDownloadUrlValid(valid,base,bucket,path),true);
  assert.equal(privateSignedDownloadUrlValid(valid,base+'/',bucket,path),true);
  assert.equal(privateSignedDownloadUrlValid(valid+'&download=rapport.pdf',base,bucket,path,'rapport.pdf'),true);
  for(const value of [
    valid.replace('https:','http:'), valid.replace('storage.example.invalid','evil.example.invalid'),
    valid.replace('storage.example.invalid','user@storage.example.invalid'),
    valid.replace('storage.example.invalid','storage.example.invalid:8443'),
    valid.replace('/object/sign/','/object/public/'),
    valid.replace(bucket,'other-bucket'), valid.replace('rapport_','other_'),
    valid.replace('/docs/','/docs%2F'), valid.replace('/docs/','/x/../docs/'),
    valid.replace('/docs/','/%2e/docs/'), valid.replace('%C3%A9','%25C3%25A9'),
    valid+'#fragment', valid+'&token=abc.def.ghi', valid+'&next=https://evil.example.invalid',
    valid+'&download=other.pdf', valid.replace(token,''), valid.replace(token,'not-a-jwt'),
    valid.replace(token,'abc.def.ghi%0A'), valid+' ', '', null, {}, 123,
  ]) assert.equal(privateSignedDownloadUrlValid(value,base,bucket,path),false,String(value));
  for(const origin of ['',null,'http://storage.example.invalid',base+'/extra',base+'?x=1','https://user@storage.example.invalid'])
    assert.equal(privateSignedDownloadUrlValid(valid,origin,bucket,path),false);
  assert.equal(privateSignedDownloadUrlValid(valid,base,bucket,path,'rapport.pdf'),false);
  assert.equal(privateSignedDownloadUrlValid(valid+'&download=other.pdf',base,bucket,path,'rapport.pdf'),false);
  assert.equal(privateSignedDownloadUrlValid(valid+'&download=rapport.pdf&download=rapport.pdf',base,bucket,path,'rapport.pdf'),false);
  assert.equal(privateSignedDownloadUrlValid(valid,base,bucket+'\n',path),false);
});
