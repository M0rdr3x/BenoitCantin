#!/usr/bin/env node
// Teste le vrai module de validation et les deux consommateurs DOM historiques.
// Aucun navigateur externe, aucune clé privée, aucun appel Supabase réel.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import vm from 'node:vm';
import {resolveDocumentUrl} from '../assets/js/sinjira-document-url-policy.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const SITE='https://www.benoitcantin.com';
const STORAGE='https://example.supabase.co';
const SIGNED=STORAGE+'/storage/v1/object/sign/sinjira-private-documents/livre.pdf?token=abc123';
const SCOPES={siteOrigin:SITE,storageOrigin:STORAGE};
let assertions=0;

function equal(got,want,message){
  assert.equal(got,want,message);
  assertions++;
}
function valid(value,protectedDocument,expected){
  const got=resolveDocumentUrl(value,{...SCOPES,protectedDocument});
  equal(got,expected||new URL(value,SITE).href,'Lien valide refusé : '+value);
}
function invalid(value,protectedDocument){
  const got=resolveDocumentUrl(value,{...SCOPES,protectedDocument});
  equal(got,null,'Lien dangereux accepté : '+JSON.stringify(value));
}
valid('/projets/sinjira/documents/guide.pdf',false);
valid('/compte/documents.html?view=one#read',false);
valid('https://www.benoitcantin.com/documents/public.pdf',false);
valid('https://example.org/external-public.pdf?download=1',false);
valid(SIGNED,true);
valid(STORAGE+'/storage/v1/object/sign/private/roman.pdf?token=tok%2Bxyz',true);
for(const value of [
  '',null,undefined,42,{},[], 'javascript:alert(1)',
  'data:text/html,<svg/onload=alert(1)>','blob:https://evil.example/abc',
  'file:///etc/passwd','http://example.org/doc.pdf',
  'https:evil.example/path', '//evil.example/document',
  '///evil.example/doc.pdf', '/\\evil.example/doc',
  '/docs/../compte/securite.html','/docs/%2e%2e/compte/securite.html',
  '/bad\nname.pdf','/bad\rname.pdf','/bad\tname.pdf',
  'https://user:pass@example.org/file.pdf',
  'https://example.org\\@evil.example/doc',
  'https://example.org/bad path/file.pdf',
  'https://example.org/file.pdf\n', '/'+ 'x'.repeat(2048)
])invalid(value,false);
for(const value of [
  '/projets/sinjira/documents/guide.pdf',
  'https://example.org/external-public.pdf',
  'https://example.supabase.co.evil.invalid/storage/v1/object/sign/doc?token=a',
  'https://evil.invalid/storage/v1/object/sign/file.pdf?token=x',
  STORAGE+'/storage/v1/object/public/doc.pdf',
  STORAGE+'/storage/v1/object/sign',
  STORAGE+'/storage/v1/object/sign/../public/secrets.txt',
  STORAGE+'/storage/v1/object/sign/%2e%2e/public/secrets.txt',
  'http://example.supabase.co/storage/v1/object/sign/file?token=x'
])invalid(value,true);
invalid(SIGNED,undefined);
invalid(SIGNED,'true');
valid('https://other.invalid/public.pdf',false);

equal(resolveDocumentUrl('/site.html',{...SCOPES,siteOrigin:'http://unsafe.invalid',protectedDocument:false}),null,'Origine HTTP locale rejetée');
equal(resolveDocumentUrl(SIGNED,{...SCOPES,storageOrigin:'http://unsafe.invalid',protectedDocument:true}),null,'Origine stockage HTTP rejetée');

// Chargement des vraies fonctions d'ouverture depuis les fichiers clients.
function extract(file,start,end){
  const source=readFileSync(resolve(ROOT,file),'utf8');
  const a=source.indexOf(start),b=source.indexOf(end,a+start.length);
  assert.ok(a>=0&&b>a,'Fonction manquante : '+file+' '+start);
  return source.slice(a,b);
}
function makeClient(file,start,end,name){
  const logs=[],calls=[];
  let answer={data:{ok:true,url:SIGNED,protected:true},error:null};
  const ctx=vm.createContext({
    location:{origin:SITE},
    SINJIRA_CONFIG:{supabaseUrl:STORAGE},
    resolveDocumentUrl,
    status:{},
    setStatus(_status,message,kind){logs.push({message,kind})},
    getSupabase(){return {functions:{invoke:async()=>answer}}},
    window:{open(...args){calls.push(args);return null}},
  });
  const code=extract(file,start,end);
  vm.runInContext(code,ctx,{filename:file,timeout:1000});
  return {run:vm.runInContext(name,ctx),logs,calls,setResponse(value){answer={data:value,error:null}}};
}
async function check(){
  const documents=makeClient(
    'assets/js/sinjira-library.js',
    'async function openDoc(id){','\nfunction bindDocs(','openDoc'
  );
  await documents.run('11111111-1111-4111-8111-111111111111');
  equal(documents.calls.length,1,'Document signé légitime ouvert');
  equal(documents.calls[0][0],SIGNED,'Destination signée canonique');
  equal(documents.calls[0][2],'noopener,noreferrer','Pas de canal opener ni de référent transmis');
  documents.setResponse({ok:true,url:'javascript:alert(1)',protected:false});
  await documents.run('22222222-2222-4222-8222-222222222222');
  equal(documents.calls.length,1,'Document javascript: bloqué');
  documents.setResponse({ok:true,url:'https://evil.invalid/storage/v1/object/sign/file?token=secret',protected:true});
  await documents.run('33333333-3333-4333-8333-333333333333');
  equal(documents.calls.length,1,'Document prétendument signé sur origine externe bloqué');
  documents.setResponse({ok:true,url:'https://example.org/public-guide.pdf',protected:false});
  await documents.run('44444444-4444-4444-8444-444444444444');
  equal(documents.calls.length,2,'Document public externe HTTPS conservé');
  equal(documents.calls[1][0],'https://example.org/public-guide.pdf','URL publique autorisée');

  const novel=makeClient(
    'assets/js/sinjira-library-v24-4-61.js',
    'async function openFullNovel(button){','\nfunction bindFullNovelButtons(','openFullNovel'
  );
  const button={disabled:false};
  await novel.run(button);
  equal(novel.calls.length,1,'Lien de roman signé valide ouvert');
  equal(button.disabled,false,'Bouton libéré après lien valide');
  novel.setResponse({ok:true,url:STORAGE+'/storage/v1/object/public/book.pdf',protected:true});
  await novel.run(button);
  equal(novel.calls.length,1,'Aucun PDF public non signé ne doit remplacer le roman intégral');
  equal(button.disabled,false,'Bouton libéré après rejet');
  novel.setResponse({ok:true,url:'https://phishing.invalid/roman.pdf',protected:true});
  await novel.run(button);
  equal(novel.calls.length,1,'Lien d’intégral étranger bloqué');
  assert.ok(novel.logs.some(entry=>entry.kind==='error'),'Rejet du roman notifié');
  novel.setResponse({ok:true,url:SIGNED,protected:false});
  await novel.run(button);
  equal(novel.calls.length,1,'Le roman intégral ne doit jamais être rétrogradé en lien public');
  equal(button.disabled,false,'Bouton libéré après tentative de downgrade');
  console.log('PASS: '+assertions+' gardes de liens de documents et de romans, contre-exemples URL et navigation DOM sans opener.');
}
check().catch(error=>{console.error(error);process.exitCode=1;});
