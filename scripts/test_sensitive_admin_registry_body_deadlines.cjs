#!/usr/bin/env node
'use strict';
// Exécute les parseurs Edge réels en Node VM, sans compte ni réseau externe.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

(async()=>{
  const {readLimitedUtf8BodyWithDeadline}=await import('../supabase/functions/_shared/read-chunk-deadline.mjs');
  const enc=new TextEncoder();
  const bytes=s=>enc.encode(s);
  const make=(body,{mime='application/json',length,signal}={})=>{
    const headers=new Headers({'content-type':mime});
    if(length!==undefined)headers.set('content-length',length);
    return new Request('https://example.invalid/private-edge',{
      method:'POST',duplex:'half',headers,body,...(signal?{signal}:{})
    });
  };
  const chunks=list=>new ReadableStream({
    start(c){for(const item of list)c.enqueue(item);c.close();}
  });
  const full=(s,options)=>make(chunks([bytes(s)]),options);
  const privateJson=(data,status=200)=>new Response(JSON.stringify(data),
    {status,headers:{'Cache-Control':'private, no-store'}});

  function load(slug,bytesLimit,ms) {
    const source=fs.readFileSync(path.resolve(__dirname,'../supabase/functions',slug,'index.ts'),'utf8');
    const marker=slug==='life-story-export'
      ? 'async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }> {'
      : 'async function readBoundedJson(req:Request){';
    const start=source.indexOf(marker);
    const end=source.indexOf(slug==='life-story-export' ? '\nfunction safeText(' : '\n// La photo source',start);
    assert.ok(start>=0&&end>start,slug+': vrai parseur non trouvé');
    let block=source.slice(start,end);
    if(slug==='life-story-export'){
      block=block.replace('readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }>',
        'readLimitedJson(req)');
      block=block.replace('const body: unknown', 'const body');
    }else{
      block=block.replace('readBoundedJson(req:Request)','readBoundedJson(req)')
        .replace('let body:unknown;', 'let body;')
        .replace('return body as Record<string,unknown>;', 'return body;');
    }
    assert.doesNotMatch(block,/await\s+reader\.(?:read|cancel)\s*\(/);
    assert.doesNotMatch(block,/await\s+req\.(?:json|text)\s*\(/);
    assert.match(block,/readLimitedUtf8BodyWithDeadline/);
    let uses=0;
    const guarded=(req,max,timeout)=>{
      uses++;
      assert.equal(max,bytesLimit,slug+': plafond de transport inchangé');
      assert.equal(timeout,ms,slug+': échéance de production inchangée');
      return readLimitedUtf8BodyWithDeadline(req,max,45);
    };
    const ctx={guarded,privateJson,TextEncoder};
    const name=slug==='life-story-export'?'readLimitedJson':'readBoundedJson';
    const code='const MAX_REQUEST_BYTES='+bytesLimit+';\n' +
      'const MAX_REQUEST_READ_TIMEOUT_MS='+ms+';\n' +
      'const readLimitedUtf8BodyWithDeadline=guarded;\n' + block+'\n'+name;
    const read=vm.runInNewContext(code,ctx,{timeout:3000});
    assert.match(source,/await requiredVaultUser\(req\)|await requiredAdmin\(req\)/);
    return {read,uses:()=>uses};
  }

  const exportReader=load('life-story-export',4096,4000);
  const characterReader=load('submit-character-questionnaire',2*1024*1024,20000);
  const cases=[
    {name:'life-story-export',...exportReader,valid:'{"action":"list"}',expected:"return"},
    {name:'submit-character-questionnaire',...characterReader,valid:'{"answers":{}}',expected:'throw'}
  ];
  async function refusal(item,req,code){
    if(item.expected==='throw') {
      await assert.rejects(item.read(req),e=>e?.message===code,
        item.name+': mauvais code refus');
    }else{
      const result=await item.read(req);
      const expectedCode=({'JSON_REQUIRED':415,'REQUEST_TOO_LARGE':413,
        'REQUEST_TIMEOUT':408,'INVALID_JSON':400})[code];
      assert.equal(result.response?.status,expectedCode,
        item.name+': statut attendu '+expectedCode);
      assert.equal(result.response.headers.get('Cache-Control'),'private, no-store');
    }
  }

  for(const item of cases) {
    const good=await item.read(full(item.valid));
    assert.ok(item.expected==='throw'?good&&typeof good==='object':good.body,
      item.name+': JSON valide refusé');
    await item.read(full(item.valid,{mime:'application/json; charset=utf-8'}));
    await refusal(item,full(item.valid,{mime:'text/plain'}),'JSON_REQUIRED');
    await refusal(item,full(item.valid,{mime:'application/json-evil'}),'JSON_REQUIRED');
    await refusal(item,full(item.valid,{length:'NaN'}),'REQUEST_TOO_LARGE');
    await refusal(item,full(item.valid,{length:'01'}),'REQUEST_TOO_LARGE');
    await refusal(item,full(item.valid,{length:item.name==='life-story-export'?'4097':'2097153'}),'REQUEST_TOO_LARGE');
    await refusal(item,full('invalid json'),'INVALID_JSON');
    await refusal(item,full('[]'),'INVALID_JSON');
    await refusal(item,make(chunks([new Uint8Array([0xc3])])),'INVALID_JSON');
    const bound=item.name==='life-story-export'?4096:2*1024*1024;
    await refusal(item,make(chunks([new Uint8Array(bound+1)]),{length:'1'}),'REQUEST_TOO_LARGE');

    let cancels=0;
    const frozen=new ReadableStream({
      pull(){return new Promise(()=>{});},
      cancel(){cancels++;return new Promise(()=>{});}
    });
    const before=performance.now();
    await refusal(item,make(frozen),'REQUEST_TIMEOUT');
    assert.ok(performance.now()-before<1000,item.name+': cancel bloquant');
    assert.equal(cancels,1,item.name+': annulation non tentée');

    const partial=new ReadableStream({
      start(c){c.enqueue(bytes('{"action":'));},
      pull(){return new Promise(()=>{});},
      cancel(){return new Promise(()=>{});}
    });
    await refusal(item,make(partial),'REQUEST_TIMEOUT');

    const abort=new AbortController();abort.abort();
    await refusal(item,make(chunks([bytes('{}')]),{signal:abort.signal}),'REQUEST_TIMEOUT');
    // Le questionnaire rejette certains mauvais MIME/Content-Length avant même d'ouvrir le flux.
    assert.ok(item.uses()>=9,item.name+': lecteur partagé insuffisamment exercé');
  }

  console.log('OK admin/Registre : deux vrais parseurs testés, 4 KiB/2 MiB, échéance globale, annulation bloquée, MIME, JSON et déconnexion.');
})().catch(error=>{console.error(error);process.exitCode=1});
