'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../supabase/functions/security-context/index.ts'),'utf8');
const start=source.indexOf('function validDeviceKey(');
const end=source.indexOf('function safeDeviceType(',start);
assert.ok(start>=0&&end>start);
const uuid=source.match(/^const UUID_RE = .*;$/m);
assert.ok(uuid);
const code=uuid[0]+'\n'+source.slice(start,end)
  .replaceAll('value: unknown','value').replace('value as Record<string, unknown>','value')
  +'\nglobalThis.gates={validDeviceKey,validSecurityDecision};';
const ctx={};
vm.runInNewContext(code,ctx,{timeout:1000});
const {validDeviceKey,validSecurityDecision}=ctx.gates;
const id='12345678-1234-4234-8234-123456789abc';
const challenge='87654321-4321-4321-8321-abcdef123456';
let checks=0;
for(const key of [id,'sinjira-'+'ab'.repeat(24),'a'.repeat(16),'b'.repeat(128)]){
  assert.equal(validDeviceKey(key),key);checks++;
}
for(const key of [null,undefined,42,{},[], 'a'.repeat(15),'a'.repeat(129),' '+id,id+' ',id+'\n',id+'\u0000','é'.repeat(16)]){
  assert.equal(validDeviceKey(key),null);checks++;
}
for(const outcome of ['allow','approved','block','challenge']){
  assert.equal(validSecurityDecision({outcome,device_id:id,challenge_id:outcome==='challenge'?challenge:null}),true);checks++;
}
for(const value of [null,undefined,[],{},true,{outcome:'allow'},
  {outcome:'allow',device_id:'invalid'},{outcome:'unknown',device_id:id},{outcome:1,device_id:id},
  {outcome:'challenge',device_id:id},{outcome:'challenge',device_id:id,challenge_id:'invalid'}]){
  assert.equal(validSecurityDecision(value),false);checks++;
}
const check=source.indexOf('if (!validSecurityDecision(data))');
const push=source.indexOf('EdgeRuntime.waitUntil(runSecurityPushBackground');
const success=source.indexOf('security: data,',push);
assert.ok(check>=0&&check<push&&push<success,'La décision doit être vérifiée avant les notifications et le succès');checks++;
assert.ok(!source.includes("console.error('[security-context]', error)"),'Pas de journalisation brute des erreurs');checks++;
console.log('PASS: '+checks+' contrôles de frontière security-context.');
