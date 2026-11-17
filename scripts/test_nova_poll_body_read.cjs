#!/usr/bin/env node
"use strict";
// Exécute le VRAI parseur de la fonction publique NOVA avec un réseau simulé.
// Aucun vote, aucun compte réel et aucune connexion Supabase.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");

const src=fs.readFileSync(path.resolve(__dirname,"../supabase/functions/nova-civic-poll/index.ts"),"utf8");
const match=src.match(/async function readLimitedJson\(req: Request\): Promise<unknown> \{[\s\S]*?\n\}\n(?=async function db\()/);
assert.ok(match,"Parser Edge de corps limité introuvable");
const js=match[0]
  .replace("readLimitedJson(req: Request): Promise<unknown>","readLimitedJson(req)")
  .replace("const chunks: Uint8Array[]=[]","const chunks=[]");
assert.match(src,/import \{ readChunkWithDeadline \} from '\.\.\/_shared\/read-chunk-deadline\.mjs';/);
assert.match(src,/const BODY_READ_TIMEOUT_MS = 8000;/);
assert.match(js,/const deadlineAt=performance\.now\(\)\+BODY_READ_TIMEOUT_MS/);
assert.match(js,/readChunkWithDeadline\(reader,req\.signal,deadlineAt\)/);
assert.match(js,/Number\.isSafeInteger\(Number\(declared\)\)/);
assert.match(src,/timedOut\?408:400/);
assert.doesNotMatch(js,/await reader\.cancel\(/);
assert.match(js,/try \{ reader\.releaseLock\(\); \} catch/);

const encoder=new TextEncoder();
const bytes=text=>encoder.encode(text);
const full=text=>new ReadableStream({start(controller){controller.enqueue(bytes(text));controller.close();}});
const make=(body,{mime="application/json",length,controller=new AbortController()}={})=>{
  const headers=new Headers({"content-type":mime});
  if(length!==undefined)headers.set("content-length",length);
  return {body,headers,signal:controller.signal,controller};
};
function fakeReader(read,cancel=async()=>{}){
  return {body:{getReader:()=>({read,cancel,releaseLock(){}})}};
}
(async()=>{
  const {readChunkWithDeadline}=await import("../supabase/functions/_shared/read-chunk-deadline.mjs");
  const deadlines=new WeakMap();
  const context={Uint8Array,TextDecoder,Headers,ReadableStream,performance,
    readChunkWithDeadline(reader,signal,actualDeadline){
      assert.ok(Number.isFinite(actualDeadline));
      const previous=deadlines.get(reader);
      if(previous)assert.equal(previous.actual,actualDeadline,"Le délai ne redémarre pas à chaque fragment");
      else deadlines.set(reader,{actual:actualDeadline,shortened:performance.now()+90});
      // 90ms seulement en environnement simulé; la source de production fixe 8000ms.
      return readChunkWithDeadline(reader,signal,deadlines.get(reader).shortened);
    }
  };
  const read=vm.runInNewContext("const MAX_BODY_BYTES=8192; const BODY_READ_TIMEOUT_MS=8000;\n"+
    js+"\nreadLimitedJson;",context,{timeout:3000});

  assert.equal((await read(make(full('{"x":true,"number":3}'),{length:"21"}))).number,3);
  assert.equal((await read(make(full('{"x":1}'),{mime:"application/json; charset=utf-8"}))).x,1);
  for(const mime of ["text/plain","application/jsonp","application/json-not-real"]){
    await assert.rejects(read(make(full('{"x":1}'),{mime})),/type/);
  }
  for(const declared of ["999999","pas-un-nombre","9007199254740992","01","-1"]){
    await assert.rejects(read(make(full('{"x":1}'),{length:declared})),/size/);
  }
  await assert.rejects(read(make(full("pas du JSON"))),/SyntaxError|Unexpected token|JSON/);
  await assert.rejects(read(make(new ReadableStream({start(s){
    s.enqueue(new Uint8Array([0xc3,0x28]));s.close();
  }}))),/TypeError|encoded data|encoding|UTF-8/);

  let cancelled=0;
  const large=new ReadableStream({
    start(s){s.enqueue(new Uint8Array(8193));},
    cancel(){cancelled++;}
  });
  await assert.rejects(read(make(large)),/size/);
  assert.equal(cancelled,1,"Le corps trop volumineux doit être annulé");

  cancelled=0;
  const hanging=fakeReader(
    ()=>new Promise(()=>{}),
    ()=>{cancelled++;return new Promise(()=>{});}
  );
  await assert.rejects(read(make(hanging.body)),/REQUEST_TIMEOUT/,
    "Le délai doit terminer la requête même si cancel() reste suspendu");
  assert.ok(cancelled>=1,"Annulation tentée sans l'attendre");

  cancelled=0;
  const disconnected=new AbortController();
  const stuck=fakeReader(
    ()=>new Promise(()=>{}),
    ()=>{cancelled++;return new Promise(()=>{});}
  );
  const pending=read(make(stuck.body,{controller:disconnected}));
  disconnected.abort();
  await assert.rejects(pending,/REQUEST_TIMEOUT/,"Un client déconnecté ne bloque pas la lecture");
  assert.ok(cancelled>=1);

  const already=new AbortController();already.abort();
  let reads=0;
  const preAborted=fakeReader(()=>{reads++;return Promise.resolve({done:true});});
  await assert.rejects(read(make(preAborted.body,{controller:already})),/REQUEST_TIMEOUT/);
  assert.equal(reads,0,"Ne jamais lire une requête déjà abandonnée");

  cancelled=0;
  let fragment=0;
  const trickle=fakeReader(
    async()=>{await new Promise(resolve=>setTimeout(resolve,55));fragment++;
      return {done:false,value:bytes(' ')};
    },
    async()=>{cancelled++;}
  );
  await assert.rejects(read(make(trickle.body)),/REQUEST_TIMEOUT/,
    "De petits fragments ne doivent pas prolonger le délai absolu");
  assert.ok(cancelled>=1);
  assert.ok(fragment<=2,"Seul un petit nombre de fragments a pu être lu");

  await assert.rejects(read(make(fakeReader(()=>Promise.reject(new Error("STREAM_FAILED"))).body)),/STREAM_FAILED/);
  console.log("OK NOVA : JSON/MIME/Content-Length/UTF-8, octets réels, timeout absolu, cancel bloqué, lenteur et déconnexion (aucun vote).");
})().catch(e=>{console.error(e);process.exitCode=1;});
