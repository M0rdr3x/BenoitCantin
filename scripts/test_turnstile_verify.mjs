import assert from "node:assert/strict";
import {test} from "node:test";
import {readFileSync} from "node:fs";
import {verifyTurnstileChallenge} from "../supabase/functions/_shared/turnstile-verify.mjs";

const hosts=["www.benoitcantin.com","benoitcantin.com"];
const token="synthetic-token-only";
const secret="fixture-not-a-real-secret";
const action="nova_poll_vote";
const fresh=()=>({success:true,hostname:hosts[0],action,challenge_ts:new Date().toISOString()});
const json=(obj)=>new Response(JSON.stringify(obj),{headers:{"content-type":"application/json"}});
const verify=(ms=7000)=>verifyTurnstileChallenge(token,secret,action,hosts,ms);
test("provider transport and fresh, strict context",async()=>{
  const original=globalThis.fetch;
  let calls=0;
  try{
    globalThis.fetch=async(url,options)=>{
      calls++;
      assert.equal(url,"https://challenges.cloudflare.com/turnstile/v0/siteverify");
      assert.equal(options.method,"POST");
      assert.equal(options.redirect,"error");
      assert.equal(options.credentials,"omit");
      assert.equal(options.referrerPolicy,"no-referrer");
      assert.equal(options.body.get("secret"),secret);
      assert.equal(options.body.get("response"),token);
      assert.equal(options.body.has("remoteip"),false);
      return json(fresh());
    };
    assert.equal(await verify(),true);assert.equal(calls,1);
    assert.equal(await verifyTurnstileChallenge("x".repeat(2049),secret,action,hosts),false);
    assert.equal(await verifyTurnstileChallenge(token,"",action,hosts),false);
    assert.equal(calls,1);
    const cases=[
      null,[],{...fresh(),success:"true"},{...fresh(),success:false},
      {...fresh(),hostname:"other.example.invalid"},{...fresh(),action:"different"},
      {...fresh(),challenge_ts:undefined},{...fresh(),challenge_ts:"not-a-date"},
      {...fresh(),challenge_ts:new Date(Date.now()-301000).toISOString()},
      {...fresh(),challenge_ts:new Date(Date.now()+31000).toISOString()}
    ];
    for(const value of cases){globalThis.fetch=async()=>json(value);assert.equal(await verify(),false);}
    for(const response of [
      new Response("{}",{status:503,headers:{"content-type":"application/json"}}),
      new Response(JSON.stringify(fresh()),{headers:{"content-type":"text/html"}}),
      new Response(JSON.stringify(fresh()),{headers:{"content-type":"application/json-evil"}}),
      new Response("not JSON",{headers:{"content-type":"application/json"}}),
      new Response("x".repeat(8193),{headers:{"content-type":"application/json"}}),
      new Response(JSON.stringify(fresh()),{headers:{"content-type":"application/json","content-length":"8193"}}),
      new Response(new Uint8Array([0xc3,0x28]),{headers:{"content-type":"application/json"}})
    ]){globalThis.fetch=async()=>response;assert.equal(await verify(),false);}
    globalThis.fetch=async()=>{throw Error("synthetic redirect rejection");};
    assert.equal(await verify(),false);
    globalThis.fetch=async()=>json({...fresh(),hostname:hosts[1]});
    assert.equal(await verify(),true);
  }finally{globalThis.fetch=original;}
});
test("absolute deadline covers headers, streaming body and stalled cancellation",async()=>{
  const original=globalThis.fetch;
  try{
    let signal;
    globalThis.fetch=(_url,options)=>{signal=options.signal;return new Promise(()=>{});};
    assert.equal(await verify(30),false);
    assert.equal(signal.aborted,true);
    let cancelled=0;
    globalThis.fetch=async()=>new Response(new ReadableStream({
      start(c){c.enqueue(new TextEncoder().encode('{"success":'));},
      pull(){return new Promise(()=>{});},
      cancel(){cancelled++;return new Promise(()=>{});}
    }),{headers:{"content-type":"application/json"}});
    const start=performance.now();
    assert.equal(await verify(50),false);
    assert.ok(performance.now()-start<1000);
    assert.equal(cancelled,1);
  }finally{globalThis.fetch=original;}
});
test("route keeps closure and challenge before privileged writes",()=>{
  const edge=readFileSync(new URL("../supabase/functions/nova-civic-poll/index.ts",import.meta.url),"utf8");
  assert.match(edge,/ballot\.captchaToken\.length>2048/);
  assert.match(edge,/return verifyTurnstileChallenge\(token, CAPTCHA_SECRET, "nova_poll_vote",\s*\["www\.benoitcantin\.com", "benoitcantin\.com"\]\)/);
  assert.match(edge,/Deno\.env\.get\("NOVA_POLL_ENABLED"\) === "true"/);
  const post=edge.slice(edge.indexOf('if(req.method!=="POST")'));
  assert.ok(post.indexOf('if(!isOpen())')<post.indexOf('if(!await confirmCaptcha(payload.captchaToken))'));
  assert.ok(post.indexOf('if(!await confirmCaptcha(payload.captchaToken))')<post.indexOf('db("rpc/nova_poll_submit"'));
});
