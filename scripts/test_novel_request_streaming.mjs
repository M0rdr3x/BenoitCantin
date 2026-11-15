#!/usr/bin/env node
import test from 'node:test';
import assert from 'node:assert/strict';
import {collectNovelBodyBytes} from '../supabase/functions/_shared/novel-request-bytes.mjs';

const encoder = new TextEncoder();
const url = 'https://example.invalid/functions/v1/get-novel-file-url';

function request(chunks, {signal, keepOpen=false, onCancel=()=>{}}={}) {
  return new Request(url, {
    method:'POST', duplex:'half', signal,
    body:new ReadableStream({
      start(controller) {
        for (const chunk of chunks) controller.enqueue(chunk);
        if (!keepOpen) controller.close();
      },
      cancel(reason) { return onCancel(reason); }
    })
  });
}

test('accepte uniquement le flux entier, fractionné et exactement borné', async()=>{
  const bytes=encoder.encode('{"slug":"roman-01"}');
  assert.deepEqual(await collectNovelBodyBytes(request([bytes]),bytes.length,500),bytes);
  assert.deepEqual(await collectNovelBodyBytes(request([bytes.subarray(0,4),bytes.subarray(4)]),bytes.length,500),bytes);
  assert.deepEqual(await collectNovelBodyBytes(new Request(url,{method:'POST'}),100,500),new Uint8Array(0));
});

test('refuse les corps dépassant la limite y compris les envois fractionnés',async()=>{
  const first=encoder.encode('abcdef'),extra=encoder.encode('g');
  await assert.rejects(collectNovelBodyBytes(request([first,extra]),6,500),{message:'REQUEST_TOO_LARGE'});
  await assert.rejects(collectNovelBodyBytes(request([encoder.encode('abcdefg')]),6,500),{message:'REQUEST_TOO_LARGE'});
});

test('annulation sans attente : le producteur peut refuser de terminer cancel()',async()=>{
  const started=Date.now();
  const req=request([encoder.encode('abc'),encoder.encode('def')],{
    keepOpen:true,
    onCancel:()=>new Promise(()=>{})
  });
  await assert.rejects(collectNovelBodyBytes(req,3,300),{message:'REQUEST_TOO_LARGE'});
  assert.ok(Date.now()-started<1000,'L’annulation ne doit pas bloquer l’appelant');
});

test('connexion bloquée : délai global refuse les octets partiels',async()=>{
  let cancelled=false;
  const req=request([encoder.encode('{"slug":')],{
    keepOpen:true,
    onCancel:()=>{cancelled=true; return new Promise(()=>{});}
  });
  const started=Date.now();
  await assert.rejects(collectNovelBodyBytes(req,2048,35),{message:'REQUEST_INTERRUPTED'});
  assert.ok(Date.now()-started<1000,'Le flux doit expirer même si cancel ne se termine jamais');
  assert.equal(cancelled,true,'Le flux doit être annulé');
});

test('abandon du client pendant la lecture refuse les octets partiels',async()=>{
  const controller=new AbortController();
  const req=request([encoder.encode('{"slug":')],{signal:controller.signal,keepOpen:true});
  const awaiting=collectNovelBodyBytes(req,2048,500);
  controller.abort();
  await assert.rejects(awaiting,{message:'REQUEST_INTERRUPTED'});
});

test('requête abandonnée avant lecture refusée',async()=>{
  const controller=new AbortController();
  const req=request([encoder.encode('{"slug":')],{signal:controller.signal,keepOpen:true});
  controller.abort();
  await assert.rejects(collectNovelBodyBytes(req,2048,500),{message:'REQUEST_INTERRUPTED'});
});

test('limites de timeout et de taille doivent être des entiers sûrs',async()=>{
  const good=request([encoder.encode('ok')]);
  await assert.rejects(collectNovelBodyBytes(good,0,100),TypeError);
  await assert.rejects(collectNovelBodyBytes(good,10,0),TypeError);
  await assert.rejects(collectNovelBodyBytes(good,10,30_001),TypeError);
  await assert.rejects(collectNovelBodyBytes(good,Infinity,100),TypeError);
});
