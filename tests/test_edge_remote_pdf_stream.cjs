'use strict';
// Essais déterministes sans requête externe ni PDF personnel.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..');
const helperPromise=import(pathToFileURL(path.join(
  root,'supabase/functions/_shared/bounded-pdf-fetch.mjs')).href);
const bytes=s=>new TextEncoder().encode(s);

function mockPdf(chunks,header=null,notify=()=>{}){
  let index=0;
  const headers=new Headers();
  if(header!==null)headers.set('content-length',header);
  return {ok:true,headers,body:new ReadableStream({
    pull(controller){if(index===chunks.length)controller.close();else controller.enqueue(chunks[index++]);},
    cancel(){notify();}
  })};
}
async function withFetch(mock,run) {
  const old=globalThis.fetch;
  globalThis.fetch=mock;
  try{return await run();}finally{globalThis.fetch=old;}
}
test('modèle PDF valide, morcelé, avec origin/redirect/cache contrôlés',async()=>{
  const {fetchBoundedPdf}=await helperPromise;
  let observed;
  const response=mockPdf([bytes('%P'),bytes('DF-'),bytes(' test')],'10');
  await withFetch(async(url,options)=>{observed={url,options};return response;},async()=>{
    assert.equal(new TextDecoder().decode(
      await fetchBoundedPdf('https://www.benoitcantin.com/test.pdf',1024)),
      '%PDF- test');
  });
  assert.equal(observed.url,'https://www.benoitcantin.com/test.pdf');
  assert.equal(observed.options.redirect,'error');
  assert.equal(observed.options.cache,'no-store');
  assert.equal(observed.options.signal.aborted,false);
});
test('Content-Length malformé ou plus grand que la borne refusé avant lecture',async()=>{
  const {fetchBoundedPdf}=await helperPromise;
  for(const header of ['1025','-5','1, 2','1e8','not a size']){
    let called=false;
    const res={ok:true,headers:new Headers({'content-length':header}),
      body:{getReader(){called=true;throw Error('SHOULD_NOT_READ');}}};
    await withFetch(async()=>res,async()=>{
      await assert.rejects(fetchBoundedPdf('https://example.invalid/test.pdf',1024),
        /REMOTE_PDF_TOO_LARGE/);
    });
    assert.equal(called,false);
  }
});
test('absence de Content-Length ne supprime pas la limite',async()=>{
  const {fetchBoundedPdf}=await helperPromise;
  let cancelled=0;
  await withFetch(async()=>mockPdf(
    [bytes('%PDF-'),bytes('x'.repeat(1020))],null,()=>cancelled++),async()=>{
    await assert.rejects(fetchBoundedPdf('https://example.invalid/test.pdf',1024),
      /REMOTE_PDF_TOO_LARGE/);
  });
  assert.equal(cancelled,1);
});
test('exactement la borne et le plus petit PDF admissible',async()=>{
  const {fetchBoundedPdf}=await helperPromise;
  await withFetch(async()=>mockPdf([bytes('%PDF-')],'5'),async()=>{
    assert.equal((await fetchBoundedPdf('https://example.invalid/a',5)).byteLength,5);
  });
});
test('corps non PDF, vide, invalide ou sans stream est refusé',async()=>{
  const {fetchBoundedPdf}=await helperPromise;
  for(const response of [
    mockPdf([bytes('HELLO')]),
    mockPdf([]),
    mockPdf([new Int16Array([1,2,3])]),
    {ok:true,headers:new Headers(),body:null}
  ]) {
    await withFetch(async()=>response,async()=>{
      await assert.rejects(fetchBoundedPdf('https://example.invalid/a',1024),
        /REMOTE_PDF_(?:NOT_PDF|INVALID)/);
    });
  }
});
test('4097 micro-fragments sont bloqués même sous 15 Mio',async()=>{
  const {fetchBoundedPdf}=await helperPromise;
  const many=[bytes('%PDF-'),...Array.from({length:4096},()=>bytes('x'))];
  let cancelled=0;
  await withFetch(async()=>mockPdf(many,null,()=>cancelled++),async()=>{
    await assert.rejects(fetchBoundedPdf('https://example.invalid/a',15*1024*1024),
      /REMOTE_PDF_INVALID/);
  });
  assert.equal(cancelled,1);
});
test('une connexion sans réponse expire et le signal est annulé',async()=>{
  const {fetchBoundedPdf}=await helperPromise;
  let signal;
  await withFetch((url,options)=>{
    signal=options.signal;
    return new Promise(()=>{});
  },async()=>{
    await assert.rejects(fetchBoundedPdf('https://example.invalid/a',1024,25),
      /REMOTE_PDF_TIMEOUT/);
  });
  assert.equal(signal.aborted,true);
});
test('une réponse en attente de nouveaux fragments expire',async()=>{
  const {fetchBoundedPdf}=await helperPromise;
  let cancelled=0;
  const res={ok:true,headers:new Headers(),body:new ReadableStream({
    start(controller){controller.enqueue(bytes('%PDF-'));},
    cancel(){cancelled++;}
  })};
  await withFetch(async()=>res,async()=>{
    await assert.rejects(fetchBoundedPdf('https://example.invalid/a',1024,25),
      /REMOTE_PDF_TIMEOUT/);
  });
  assert.equal(cancelled,1);
});
test('les deux routes PDF refusent tout retour au téléchargement intégral',()=>{
  for(const [name,signature] of [
    ['send-game-report','fetchBoundedPdf(reportTemplateUrl(),MAX_TEMPLATE_BYTES)'],
    ['send-player-sheet','fetchBoundedPdf(templateUrl(mode),MAX_TEMPLATE_BYTES)']
  ]){
    const code=fs.readFileSync(path.join(
      root,'supabase/functions',name,'index.ts'),'utf8');
    assert.ok(code.includes(signature),name);
    assert.ok(code.includes("import { fetchBoundedPdf } from '../_shared/bounded-pdf-fetch.mjs';"),name);
    assert.doesNotMatch(code,/response\.arrayBuffer\(\)/,name);
    assert.match(code,/MAX_TEMPLATE_BYTES=15\*1024\*1024/,name);
  }
});
