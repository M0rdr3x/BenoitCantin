import assert from 'node:assert/strict';
import {consumeRegistryPhotoBudget as consume} from '../security/candidates/registry-photo-budget.mjs';
const user='10000000-0000-4000-8000-000000000001';
let calls=0,count=0;
const service=(result)=>({rpc(name,args){calls++;assert.equal(name,'consume_registry_photo_budget');assert.deepEqual(args,{p_user_id:user});return {abortSignal(signal){assert.ok(signal instanceof AbortSignal);return Promise.resolve(result)}}}});
for(const [result,want] of [[{error:null,data:true},'allowed'],[{error:null,data:false},'limited'],[null,'unavailable'],[{},'unavailable'],[{data:true},'unavailable'],[{error:false,data:true},'unavailable'],[{error:0,data:true},'unavailable'],[{error:'',data:true},'unavailable'],[{error:{code:'FAIL'},data:true},'unavailable'],[{error:null,data:'true'},'unavailable'],[{error:null,data:1},'unavailable'],[{error:null,data:[true]},'unavailable']]){
  assert.equal(await consume(service(result),user),want);count++;
}
const before=calls;
for(const bad of [null,undefined,'',user+'\n',user.toUpperCase().replace('1000','ABCD'),'00000000-0000-0000-0000-000000000000',{},1]){
  assert.equal(await consume(service({error:null,data:true}),bad),'unavailable');count++;
}
for(const timeout of [0,-1,1.5,1501,NaN,Infinity]){
  assert.equal(await consume(service({error:null,data:true}),user,timeout),'unavailable');count++;
}
assert.equal(calls,before);
let aborted=false;
const pending={rpc(){return {abortSignal(signal){signal.addEventListener('abort',()=>{aborted=true},{once:true});return new Promise(()=>{})}}}};
assert.equal(await consume(pending,user,20),'unavailable');assert.ok(aborted);count++;
assert.equal(await consume({rpc(){throw Error('offline')}},user),'unavailable');count++;
assert.equal(await consume({rpc(){return {abortSignal(){return Promise.reject(Error('offline'))}}}},user),'unavailable');count++;
console.log('PASS quota RPC candidate: '+count+' cases.');
