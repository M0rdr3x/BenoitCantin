#!/usr/bin/env node
// Tests sur le vrai lecteur Storage privé : aucun réseau, clé ou PDF réel.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import test from 'node:test';
import { readPrivateLifeStoryPdf } from '../supabase/functions/_shared/private-life-story-pdf.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const host='https://gpvivleexywljowcqkru.supabase.co';
const key='sb_secret_'+ 'x'.repeat(32);
const objectPath='11111111-1111-4111-8111-111111111111/22222222-2222-4222-8222-222222222222/33333333-3333-4333-8333-333333333333.pdf';
const bytes=new TextEncoder().encode('%PDF-1.7\nvery small synthetic pdf');

function streaming(chunks,headers={},onCancel=()=>{}){
 return new Response(new ReadableStream({
  start(c){for(const part of chunks)c.enqueue(part);c.close();},
  cancel(r){onCancel(r);}
 }),{headers});
}
function args(fetchImpl,more={}){
 return{projectUrl:host,serviceKey:key,objectPath,timeoutMs:500,
        maxBytes:bytes.byteLength,fetchImpl,...more};
}

test('les bytes PDF privés sont reçus seulement après un GET Storage authentifié',async()=>{
 let called=0;
 const result=await readPrivateLifeStoryPdf(args((url,options)=>{
  called++;
  assert.equal(url,host+'/storage/v1/object/authenticated/sinjira-life-story-exports/'+objectPath);
  assert.equal(options.method,'GET');
  assert.equal(options.headers.Authorization,'Bearer '+key);
  assert.equal(options.headers.apikey,key);
  assert.equal(options.credentials,'omit');
  assert.equal(options.redirect,'error');
  assert.equal(options.referrerPolicy,'no-referrer');
  assert.equal(options.cache,'no-store');
  assert.ok(options.signal instanceof AbortSignal);
  return Promise.resolve(streaming([bytes.subarray(0,5),bytes.subarray(5)]));
 }));
 assert.equal(called,1);
 assert.equal(result.ok,true);
 assert.deepEqual(result.bytes,bytes);
});

test('la taille binaire est imposée pendant la réception, même si Content-Length manque',async()=>{
 let cancelled=false;
 const result=await readPrivateLifeStoryPdf(args(async()=>new Response(new ReadableStream({
  pull(c){c.enqueue(new Uint8Array(8192));},
  cancel(){cancelled=true;}
 },{highWaterMark:0}))));
 assert.deepEqual(result,{ok:false});
 assert.ok(cancelled,'le flux volumineux est annulé');
});

test('un Content-Length trompeur est refusé avant toute lecture du flux',async()=>{
 let read=false;
 const result=await readPrivateLifeStoryPdf(args(async()=>new Response(new ReadableStream({
  pull(){read=true;}
 },{highWaterMark:0}),{headers:{'content-length':'99999999'}})));
 assert.deepEqual(result,{ok:false});
 assert.equal(read,false);
});

test('les erreurs Storage restent opaques',async()=>{
 for(const status of [401,403,404,500]){
  const result=await readPrivateLifeStoryPdf(args(async()=>new Response('secret sql diagnostics',{status})));
  assert.deepEqual(result,{ok:false});
 }
});

test('les flux qui ne se terminent jamais expirent, même si cancel() est bloqué',async()=>{
 const response=new Response(new ReadableStream({
  start(c){c.enqueue(bytes.subarray(0,3));},
  cancel(){return new Promise(()=>{});}
 }));
 const started=Date.now();
 const result=await readPrivateLifeStoryPdf(args(async()=>response,{timeoutMs:40}));
 assert.deepEqual(result,{ok:false});
 assert.ok(Date.now()-started<1500,'expiration globale attendue');
});

test('le fetch privé est interrompu au délai sans exposer de données',async()=>{
 let aborted=false;
 const started=Date.now();
 const result=await readPrivateLifeStoryPdf(args((_url,opts)=>new Promise((_resolve,reject)=>{
  opts.signal.addEventListener('abort',()=>{
    aborted=true; reject(new Error('backend secret'));
  },{once:true});
 }),{timeoutMs:40}));
 assert.deepEqual(result,{ok:false});
 assert.ok(aborted);
 assert.ok(Date.now()-started<1500);
});

test('une échéance globale unique couvre la connexion et le flux du PDF privé',async()=>{
 const started=Date.now();
 const result=await readPrivateLifeStoryPdf(args(async()=>{
  await new Promise(resolve=>setTimeout(resolve,170));
  return new Response(new ReadableStream({
   start(controller){controller.enqueue(bytes.subarray(0,3));},
   cancel(){return new Promise(()=>{});}
  }));
 },{timeoutMs:300}));
 assert.deepEqual(result,{ok:false});
 // Sans budget restant, fetch (170 ms) + lecture (300 ms) prendraient
 // environ 470 ms. La protection doit plafonner l'ensemble à ~300 ms.
 assert.ok(Date.now()-started<420,'deadline unique sur fetch + lecture');
});

test('aucune origine externe, credentials URL ou endpoint non sûr accepté',async()=>{
 const inputs=[
 'https://evil.invalid', 'https://gpvivleexywljowcqkru.supabase.co.evil.invalid',
 'http://gpvivleexywljowcqkru.supabase.co',
 'https://user:password@gpvivleexywljowcqkru.supabase.co',
 'https://gpvivleexywljowcqkru.supabase.co/path',
 'https://gpvivleexywljowcqkru.supabase.co/?token=secret',
 'file:///etc/passwd', 'https://gpvivleexywljowcqkru.supabase.co:444',
 ];
 let calls=0;
 for(const projectUrl of inputs){
  const result=await readPrivateLifeStoryPdf(args(async()=>{
   calls++;return streaming([bytes]);
  },{projectUrl}));
  assert.deepEqual(result,{ok:false},projectUrl);
 }
 assert.equal(calls,0);
});

test('les chemins de Storage arbitraires sont refusés avant la requête réseau',async()=>{
 const inputs=[
 '../other-bucket/file.pdf','/private/file.pdf','abc/../file.pdf',
 'abc/%2e%2e/file.pdf','abc/secret\\file.pdf','abc//file.pdf',
 'abc/file.pdf?token=x','abc/file.jpg','https://evil.invalid/file.pdf',
 ];
 let calls=0;
 for(const objectPath of inputs){
  const result=await readPrivateLifeStoryPdf(args(async()=>{
   calls++;return streaming([bytes]);
  },{objectPath}));
  assert.deepEqual(result,{ok:false},objectPath);
 }
 assert.equal(calls,0);
});

test('les clés absentes et les valeurs de limite non autorisées sont refusées',async()=>{
 let calls=0;
 assert.deepEqual(await readPrivateLifeStoryPdf(args(async()=>{
  calls++;return streaming([bytes]);
 },{serviceKey:''})),{ok:false});
 assert.equal(calls,0);
 for(const maxBytes of [0,-1,15*1024*1024+1,Number.MAX_SAFE_INTEGER]){
  await assert.rejects(readPrivateLifeStoryPdf(args(async()=>streaming([bytes]),{maxBytes})),TypeError);
 }
 await assert.rejects(readPrivateLifeStoryPdf(args(async()=>streaming([bytes]),{timeoutMs:0})),TypeError);
});

test('le lecteur fonctionne aussi avec Supabase local pour les essais de staging',async()=>{
 const result=await readPrivateLifeStoryPdf(args(async(url)=>{
  assert.ok(url.startsWith('http://kong:8000/storage/v1/object/authenticated/'));
  return streaming([bytes]);
 },{projectUrl:'http://kong:8000'}));
 assert.equal(result.ok,true);
});

test('la remise réelle ne charge plus un Blob arbitraire avant la vérification',()=>{
 const path=resolve(root,'supabase/functions/life-story-delivery/index.ts');
 const src=readFileSync(path,'utf8');
 const reader=src.indexOf('await readPrivateLifeStoryPdf(');
 const check=src.indexOf('hasPdfSignature(bytes)',reader);
 const register=src.indexOf("service.rpc('service_life_story_register_download'",reader);
 assert.ok(reader>0&&check>reader&&register>check,'lire, vérifier, puis compter');
 assert.ok(src.includes("record.storage_bucket !== 'sinjira-life-story-exports'"));
 assert.ok(!src.includes("storage.from('sinjira-life-story-exports').download("));
 assert.ok(!src.includes('await file.arrayBuffer()'));
 assert.ok(src.includes('MAX_PDF_BYTES = 15 * 1024 * 1024'));
 const helper=readFileSync(resolve(root,'supabase/functions/_shared/private-life-story-pdf.mjs'),'utf8');
 assert.ok(helper.includes('Math.floor(timeoutMs - (performance.now() - startedAt))'));
 assert.ok(src.includes("if (!pdf.ok) return errorResponse(req, 410)"));
 assert.ok(src.includes("'Cache-Control': 'private, no-store, max-age=0'"));
});
