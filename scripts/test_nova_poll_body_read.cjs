#!/usr/bin/env node
"use strict";
// Exécuter le VRAI parseur du sondage, sans réseau ni données politiques.
// En particulier, une source dont read() ET cancel() ne finissent jamais
// ne doit pas retenir une fonction Edge publique au-delà de son délai absolu.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const edge=fs.readFileSync(path.resolve(__dirname,
  "../supabase/functions/nova-civic-poll/index.ts"),"utf8");
const match=edge.match(/async function readLimitedJson\(req: Request\): Promise<unknown> \{[\s\S]*?\n\}\n(?=async function db\()/);
assert.ok(match,"Parseur Edge NOVA introuvable");
const js=match[0].replace("readLimitedJson(req: Request): Promise<unknown>","readLimitedJson(req)");
assert.match(edge,/const MAX_BODY_BYTES = 8192;/);
assert.match(edge,/const BODY_READ_TIMEOUT_MS = 8000;/);
assert.match(edge,/from '..\/_shared\/read-chunk-deadline.mjs'/);
assert.match(js,/readLimitedUtf8BodyWithDeadline\(req,MAX_BODY_BYTES,BODY_READ_TIMEOUT_MS\)/);
assert.match(js,/\/\^application\\\/json/);
assert.doesNotMatch(js,/\.startsWith\(["']application\/json/);
assert.doesNotMatch(js,/await req\.(?:json|text)\(/);
assert.doesNotMatch(js,/await reader\.read\(/);
assert.doesNotMatch(js,/await reader\.cancel\(/);
const encoder=new TextEncoder();
const bytes=s=>encoder.encode(s);
const full=s=>new ReadableStream({start(c){c.enqueue(bytes(s));c.close();}});
const make=(body,{mime="application/json",length,controller=new AbortController()}={})=>{
  const headers=new Headers({"content-type":mime});
  if(length!==undefined)headers.set("content-length",length);
  return {body,headers,signal:controller.signal,controller};
};

(async()=>{
  const {readLimitedUtf8BodyWithDeadline}=await import(
    "../supabase/functions/_shared/read-chunk-deadline.mjs");
  let calls=0;
  const sharedReader=(req,max,ms)=>{
    calls++;
    assert.equal(max,8192,"Limite réelle du corps NOVA conservée");
    assert.equal(ms,8000,"Délai absolu du sondage inchangé");
    // Réduire le temps de test en gardant la VRAIE primitive de production.
    return readLimitedUtf8BodyWithDeadline(req,max,40);
  };
  const context={sharedReader};
  const read=vm.runInNewContext(
    "const MAX_BODY_BYTES=8192;const BODY_READ_TIMEOUT_MS=8000;"+
    "const readLimitedUtf8BodyWithDeadline=sharedReader;\n"+
    js+"\nglobalThis.__read=readLimitedJson;__read",
    context,{timeout:3000}
  );
  const rejected=async(req,pattern)=>assert.rejects(read(req),pattern);

  const value=await read(make(full('{"x":true,"number":3}'),{length:"21"}));
  assert.equal(value.x,true);
  assert.equal(value.number,3);
  assert.equal((await read(make(full('{"name":"été"}'),
    {mime:"application/json; charset=utf-8"}))).name,"été");

  await rejected(make(full("{}"),{mime:"text/plain"}),/type/);
  await rejected(make(full("{}"),{mime:"application/json-evil"}),/type/);
  await rejected(make(full("{}"),{mime:"application/jsonx"}),/type/);
  await rejected(make(full("{}"),{length:"8193"}),/size/);
  await rejected(make(full("{}"),{length:"NaN"}),/size/);
  await rejected(make(full("{}"),{length:"9007199254740992"}),/size/);
  await rejected(make(full("{}"),{length:"01"}),/size/);
  await rejected(make(full("invalide")),/SyntaxError|Unexpected token|JSON/);
  await rejected(make(new ReadableStream({
    start(c){c.enqueue(new Uint8Array([0xc3,0x28]));c.close();}
  })),/size/);
  await rejected(make(full("")),/body/);
  await rejected(make(new ReadableStream({
    start(c){c.enqueue(new Uint8Array(8193));c.close();}
  })),/size/);

  let cancelCount=0;
  const stalled=new ReadableStream({
    pull(){return new Promise(()=>{});},
    cancel(){cancelCount++;return new Promise(()=>{});}
  });
  const start=performance.now();
  await rejected(make(stalled),/body_interrupted/);
  const elapsed=performance.now()-start;
  assert.ok(elapsed<1000,"Une annulation bloquée ne doit jamais suspendre la réponse");
  assert.ok(cancelCount>0,"La primitive doit tenter d'annuler la source au délai");

  // Même après un fragment valide, l'échéance reste absolue.
  const partial=new ReadableStream({
    start(c){c.enqueue(bytes('{"x":'));},
    pull(){return new Promise(()=>{});},
    cancel(){return new Promise(()=>{});}
  });
  const partialStart=performance.now();
  await rejected(make(partial),/body_interrupted/);
  assert.ok(performance.now()-partialStart<1000);

  const aborted=new AbortController();
  aborted.abort();
  await rejected(make(full("{}"),{controller:aborted}),/body_interrupted/);

  assert.ok(calls>=10,"Les contrôles réels doivent passer par le lecteur partagé");
  console.log("OK NOVA: MIME strict, UTF-8, longueur, flux gelé, cancel bloquant, deadline absolue et déconnexion (sans aucun vote).");
})().catch(error=>{console.error(error);process.exitCode=1;});
