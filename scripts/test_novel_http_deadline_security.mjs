#!/usr/bin/env node
// Contrôle du véritable handler de roman et du lecteur à échéance absolue.
// Aucune requête réseau, aucun utilisateur et aucun jeton de production.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import {readLimitedUtf8BodyWithDeadline} from '../supabase/functions/_shared/read-chunk-deadline.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const source=readFileSync(resolve(root,'supabase/functions/get-novel-file-url/index.ts'),'utf8');
const signature="async function readBoundedJson(req:Request)";
assert.ok(source.includes('readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,8000)'));
assert.ok(source.includes("const user=await requiredUser(req);"));
assert.ok(!source.includes('await reader.cancel('),'La fonction ne doit pas attendre cancel()');
assert.ok(!source.includes('await req.text()')&&!source.includes('await req.json()'));
assert.equal(source.split(signature).length,2,'La fonction testée doit être le handler réel');

function handler({authenticate=async()=>({id:'user-1'}),query=()=>{throw Error('unexpected query')}}={}){
  let runnable=source.replace(/^import [^\n]+;\n/gm,'');
  for(const [before,after] of [
    ['function json(data:unknown,status=200)','function json(data,status=200)'],
    [signature,'async function readBoundedJson(req)'],
  ]){
    assert.equal(runnable.split(before).length,2,'Signature TypeScript attendue : '+before);
    runnable=runnable.replace(before,after);
  }
  assert.doesNotMatch(runnable,/^import /m);
  const environment={
    Request,Response,URL,TextDecoder,console:{error(){throw Error('Diagnostic serveur inattendu')}},
    corsHeaders:{'Access-Control-Allow-Origin':'https://www.benoitcantin.com'},
    readLimitedUtf8BodyWithDeadline,
    requiredUser:authenticate,
    serviceClient:()=>({from:query}),
    privateBookLocationValid(){throw Error('Signature Storage interdite dans ces tests')},
    isVerifiedPrivateBucket(){throw Error('Signature Storage interdite dans ces tests')},
  };
  environment.Deno={serve(fn){environment.server=fn}};
  vm.runInNewContext(runnable,environment,{timeout:3000});
  assert.equal(typeof environment.server,'function');
  return environment.server;
}

const endpoint='https://project.supabase.co/functions/v1/get-novel-file-url';
function request(body,extraHeaders={}){
  const headers=new Headers({'content-type':'application/json'});
  for(const [name,value] of Object.entries(extraHeaders))headers.set(name,value);
  return new Request(endpoint,{method:'POST',headers,
    body:typeof body==='string'?body:JSON.stringify(body)});
}
async function status(server,req,want){
  const answer=await server(req);
  const json=await answer.json();
  assert.equal(answer.status,want,JSON.stringify(json));
  assert.equal(json.ok,false);
  assert.equal(Object.hasOwn(json,'url'),false,'Une erreur ne doit jamais exposer une URL');
  assert.equal(answer.headers.get('Cache-Control'),'private, no-store, max-age=0');
  return json;
}

test('l’identité est vérifiée avant toute lecture du corps HTTP',async()=>{
  let reads=0;
  const server=handler({authenticate:async()=>{throw Error('AUTH_REQUIRED')}});
  const controller=new AbortController();
  const fake={
    method:'POST',headers:new Headers({'content-type':'application/json'}),
    signal:controller.signal,body:{getReader(){reads++;throw Error('Must not read body')}}};
  await status(server,fake,401);
  assert.equal(reads,0);
});

test('réfuse le contenu non JSON et le Content-Length excessif avant SQL',async()=>{
  const server=handler();
  await status(server,request('{}',{'content-type':'text/plain'}),415);
  await status(server,request('{}',{'content-length':'3000'}),413);
  await status(server,request('{}',{'content-type':'application/json-whatever'}),415);
});

test('refuse les corps JSON malformés et les slugs non typés',async()=>{
  const server=handler();
  await status(server,request('{not valid'),400);
  for(const input of [null,[],42,true,'texte',{slug:3},{slug:{}},{slug:[]},
    {slug:'../secret'},{slug:'la cendre'},{slug:' la-cendre-du-jugement '},
    {slug:'x'.repeat(121)}]){
    await status(server,request(input),400);
  }
});

test('conserve le parcours légitime sans signe ni accès anticipé au Storage',async()=>{
  let queries=0;
  const server=handler({query(name){
    queries++;assert.equal(name,'sinjira_novels');
    const db={select(){return this},eq(){return this},
      async maybeSingle(){return {data:null,error:null}}};
    return db;
  }});
  await status(server,request({slug:'la-cendre-du-jugement'}),404);
  assert.equal(queries,1);
});

test('aucun blocage sur un lecteur réseau immobile et cancel() indéfiniment en attente',async()=>{
  let cancelled=0;
  let unlocked=0;
  const signal=new AbortController().signal;
  const fake={
    headers:new Headers({'content-type':'application/json'}),
    signal,
    body:{getReader(){return {
      read(){return new Promise(()=>{})},
      cancel(){cancelled++;return new Promise(()=>{})},
      releaseLock(){unlocked++}
    }}}
  };
  const result=await Promise.race([
    readLimitedUtf8BodyWithDeadline(fake,2048,35),
    new Promise((_,reject)=>setTimeout(()=>reject(Error('Le lecteur est resté bloqué')),300))
  ]);
  assert.equal(result.ok,false);
  assert.equal(result.reason,'REQUEST_TIMEOUT');
  assert.equal(cancelled,1);
  assert.equal(unlocked,1);
});

test('un client qui dépasse le plafond en fragments est refusé sans attendre cancel()',async()=>{
  let canceled=0;
  const payload=[new Uint8Array(1024),new Uint8Array(1025)];
  const fake={
    headers:new Headers({'content-type':'application/json'}),
    signal:new AbortController().signal,
    body:{getReader(){return {
      async read(){return payload.length?{done:false,value:payload.shift()}:{done:true}},
      cancel(){canceled++;return new Promise(()=>{})},
      releaseLock(){}
    }}}
  };
  const result=await readLimitedUtf8BodyWithDeadline(fake,2048,200);
  assert.equal(result.ok,false);
  assert.equal(result.reason,'REQUEST_TOO_LARGE');
  assert.equal(canceled,1);
});

test('UTF-8 invalide et annulation client restent sans réponse signée',async()=>{
  const broken=new Uint8Array([0xff,0xfe,0xfd]);
  const bad=new Request(endpoint,{method:'POST',headers:{'content-type':'application/json'},body:broken});
  await status(handler(),bad,400);
  const ctrl=new AbortController();
  ctrl.abort();
  const fake={method:'POST',headers:new Headers({'content-type':'application/json'}),
    signal:ctrl.signal,body:{getReader(){throw Error('reader should not be created')}}};
  await status(handler(),fake,408);
});
