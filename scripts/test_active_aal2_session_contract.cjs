'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../supabase/functions/_shared/active-aal2-session.ts'), 'utf8');
const code = source.replace(/^import .*;\n/m, '')
  .replace('export async function', 'async function')
  .replaceAll('token: string, userId: string', 'token, userId')
  .replace('new Set<string>()', 'new Set()') +
  '\nglobalThis.gate = requireActiveAal2Session;';
const uid = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const sid = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const other = 'cccccccc-cccc-4ccc-8ccc-cccccccccccc';
const current = {id: sid, is_current: true, aal: 'aal2', not_after: null};
const token = claims => 'synthetic.' + Buffer.from(JSON.stringify(claims)).toString('base64url') + '.synthetic';
const validToken = token({sub:uid, aal:'aal2', session_id:sid});
function harness(response, env = {}, reject = false) {
  let calls = 0;
  const sandbox = {atob, TextDecoder, Uint8Array, Date,
    Deno: {env: {get: key => ({SUPABASE_URL:'https://local.invalid', SUPABASE_ANON_KEY:'synthetic-public-key', ...env})[key]}},
    createClient: (url, key, options) => {
      assert.equal(url, 'https://local.invalid');
      assert.equal(key, env.SUPABASE_PUBLISHABLE_KEYS ? 'sb_publishable_synthetic' : 'synthetic-public-key');
      assert.equal(options.global.headers.Authorization, 'Bearer ' + validToken);
      assert.equal(options.auth.persistSession, false);
      assert.equal(options.auth.autoRefreshToken, false);
      return {rpc: async name => {
        calls++; assert.equal(name, 'security_list_sessions');
        if (reject) throw new Error('synthetic provider detail');
        return response;
      }};
    }};
  vm.runInNewContext(code, sandbox, {timeout:1000});
  return {gate: sandbox.gate, calls:()=>calls};
}
async function main() {
  for (const rows of [[current], [current,{id:other,is_current:false,aal:'aal1',not_after:null}],
    [{...current,not_after:'2099-01-01T00:00:00Z'}]]) {
    const h=harness({error:null,data:rows}); await h.gate(validToken,uid); assert.equal(h.calls(),1);
  }
  const modern=harness({error:null,data:[current]},{SUPABASE_PUBLISHABLE_KEYS:'{"default":"sb_publishable_synthetic"}'});
  await modern.gate(validToken,uid);
  for (const response of [null, false, [], {}, {data:[current]}, {error:false,data:[current]},
    {error:0,data:[current]}, {error:{message:'private detail'},data:[current]}, {error:null,data:{}},
    {error:null,data:[null,current]}, {error:null,data:[current,current]},
    {error:null,data:[current,{...current,is_current:false}]},
    {error:null,data:[current,{...current,id:other}]},
    {error:null,data:[{...current,is_current:'true'}]},
    {error:null,data:[{...current,id: sid+'\n'}]},
    {error:null,data:[{...current,not_after:'invalid'}]},
    {error:null,data:[{...current,not_after:undefined}]}]) {
    const h=harness(response);
    await assert.rejects(h.gate(validToken,uid),{message:'SECURITY_DECISION_INVALID'});
  }
  for (const rows of [[],[{id:other,is_current:false,aal:'aal2',not_after:null}],
    [{...current,aal:'aal1'}],[{...current,aal:null}],[{...current,aal:'aal3'}],
    [{...current,not_after:'2000-01-01T00:00:00Z'}]]) {
    const h=harness({error:null,data:rows});
    await assert.rejects(h.gate(validToken,uid),{message:'AUTH_REQUIRED'});
  }
  for (const bad of ['invalid', token(null), token([]), token({sub:other,aal:'aal2',session_id:sid}),
    token({sub:uid,aal:'aal1',session_id:sid}), token({sub:uid,aal:'aal2',session_id:sid+'\n'})]) {
    const h=harness({error:null,data:[current]});
    await assert.rejects(h.gate(bad,uid),{message:'AUTH_REQUIRED'}); assert.equal(h.calls(),0);
  }
  const offline=harness(null,{},true);
  await assert.rejects(offline.gate(validToken,uid),{message:'SECURITY_DECISION_INVALID'});
  console.log('PASS: active AAL2 session contract, 30 negative cases and 4 positive cases.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
