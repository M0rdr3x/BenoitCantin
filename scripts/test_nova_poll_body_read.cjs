#!/usr/bin/env node
"use strict";
// Exécuter le VRAI parseur de corps du service Edge dans une VM sans réseau.
// Aucun formulaire réel, aucune opinion, aucune requête Supabase.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const edge=fs.readFileSync(path.resolve(__dirname,
  "../supabase/functions/nova-civic-poll/index.ts"),"utf8");
const match=edge.match(/async function readLimitedJson\(req: Request\): Promise<unknown> \{[\s\S]*?\n\}\n(?=async function db\()/);
assert.ok(match,"Parser Edge de corps limité introuvable");
const js=match[0]
  .replace("readLimitedJson(req: Request): Promise<unknown>","readLimitedJson(req)")
  .replace("const chunks: Uint8Array[]=[]","const chunks=[]");
assert.equal(js.includes("Promise<unknown>"),false);
assert.match(edge,/const BODY_READ_TIMEOUT_MS = 8000;/);
assert.match(js,/reader\.cancel\(\)/,"Le délai doit débloquer le lecteur suspendu");
assert.match(js,/req\.signal\.addEventListener\("abort"/,"Déconnexion client traitée");

const scheduled=[],cleared=[];
let timerId=0;
const context={
  Uint8Array,TextDecoder,Headers,ReadableStream,
  setTimeout(fn,ms){const id=++timerId;scheduled.push({id,fn,ms});return id;},
  clearTimeout(id){cleared.push(id);}
};
const read=vm.runInNewContext("const MAX_BODY_BYTES=8192; const BODY_READ_TIMEOUT_MS=8000;\n"
  +js+"\nglobalThis.__read=readLimitedJson; __read",context,{timeout:3000});
const encoder=new TextEncoder();
const make=(body,{mime="application/json",length,controller=new AbortController()}={})=>{
  const headers=new Headers({"content-type":mime});
  if(length!==undefined)headers.set("content-length",length);
  return {body,headers,signal:controller.signal,controller};
};
const bytes=text=>encoder.encode(text);
const full=text=>new ReadableStream({start(s){s.enqueue(bytes(text));s.close();}});
async function rejected(req,reason){
  await assert.rejects(read(req),reason);
}
(async()=>{
  let req=make(full('{"x":true,"number":3}'),{length:"21"});
  const data=await read(req);
  assert.equal(data.x,true);
  assert.equal(data.number,3);
  assert.equal(cleared.at(-1),scheduled.at(-1).id,"Délai libéré après succès");
  assert.equal(scheduled.at(-1).ms,8000,"Durée maximum de lecture");

  req=make(full('{"x":1}'),{mime:"text/plain"});
  await rejected(req,/type/);
  req=make(full('{"x":1}'),{length:"999999"});
  await rejected(req,/size/);
  req=make(full('{"x":1}'),{length:"pas-un-nombre"});
  await rejected(req,/size/);
  req=make(full('{"x":1}'),{length:"9007199254740992"});
  await rejected(req,/size/);
  req=make(full('pas du JSON'));
  await rejected(req,/SyntaxError|Unexpected token|JSON/);
  // Le décodeur fatal refuse les octets illisibles avant toute décision.
  req=make(new ReadableStream({start(s){
    s.enqueue(new Uint8Array([0xc3,0x28]));s.close();
  }}));
  await rejected(req,/TypeError|encoded data|encoding|UTF-8/);

  let cancelled=0;
  const large=new ReadableStream({
    start(s){s.enqueue(new Uint8Array(8193));},
    cancel(){cancelled++;}
  });
  await rejected(make(large),/size/);
  assert.equal(cancelled,1,"Dépassement du volume : annulation du lecteur");
  assert.equal(cleared.at(-1),scheduled.at(-1).id);

  cancelled=0;
  const slow=new ReadableStream({
    start(s){s.enqueue(bytes('{"x":'));},
    cancel(){cancelled++;}
  });
  const pending=read(make(slow));
  // Laisser la première portion être reçue; ensuite aucun octet n'arrive.
  await Promise.resolve();await Promise.resolve();await Promise.resolve();
  const deadline=scheduled.at(-1);
  assert.equal(cleared.includes(deadline.id),false,"Lecture bloquée encore sous délai");
  deadline.fn();
  await assert.rejects(pending,/body_interrupted/,
    "Une transmission suspendue doit se terminer après le délai");
  assert.equal(cancelled,1,"Le lecteur partiel est annulé au délai");
  assert.equal(cleared.at(-1),deadline.id);

  cancelled=0;
  const controller=new AbortController();
  const disconnected=new ReadableStream({
    start(s){s.enqueue(bytes('{"x":'));},
    cancel(){cancelled++;}
  });
  const session=make(disconnected,{controller});
  const interrupted=read(session);
  await Promise.resolve();await Promise.resolve();
  controller.abort();
  await assert.rejects(interrupted,/body_interrupted/,"Déconnexion client traitée");
  assert.equal(cancelled,1);
  assert.equal(cleared.at(-1),scheduled.at(-1).id);

  const already=new AbortController();already.abort();
  await rejected(make(full('{"x":1}'),{controller:already}),/body_interrupted/);
  assert.equal(cleared.length,scheduled.length,"Tous les délais de lecture sont nettoyés");
  console.log("OK NOVA : corps JSON valides, MIME/longueur/UTF8, surcharge, flux suspendu, abandon client et temporisateurs sans aucun vote.");
})().catch(error=>{console.error(error);process.exitCode=1;});
