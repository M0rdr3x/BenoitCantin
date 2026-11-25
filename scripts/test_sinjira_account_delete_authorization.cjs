'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../supabase/functions/delete-player-account/index.ts'),'utf8');
const start=source.indexOf('Deno.serve(async (req) => {');
assert.ok(start>=0);
const pathStart=source.indexOf('function ownedStoragePaths(');
const pathEnd=source.indexOf('async function removeStoragePaths(',pathStart);
assert.ok(pathStart>=0&&pathEnd>pathStart);
const guard=source.slice(pathStart,pathEnd).replace('(paths:unknown[],userId:string):string[]','(paths,userId)').replace('new Set<string>()','new Set()');
const code=guard+source.slice(start).replaceAll('(row:any)','(row)');
const uid='10000000-0000-4000-8000-000000000001';
async function invoke({admin=false,adminError=null,canDelete=true,holdError=null,aal={currentLevel:'aal2',nextLevel:'aal2'},aalError=null,confirm='SUPPRIMER MON COMPTE',authDenied=false,avatar=uid+'/avatar.png',sources=[],applications=[]}={}){
  const calls=[];
  const service={
    async rpc(name,args){
      calls.push(name);
      assert.equal(args.p_user_id,uid);
      if(name==='is_sinjira_admin')return {data:admin,error:adminError};
      if(name==='privacy_service_can_delete_user')return {data:canDelete,error:holdError};
      if(name==='revoke_sinjira_contributions')return {data:1,error:null};
      throw Error('unexpected RPC');
    },
    auth:{mfa:{async getAuthenticatorAssuranceLevel(token){assert.equal(token,'synthetic-token');calls.push('mfa');return {data:aal,error:aalError}}},
      admin:{async deleteUser(id){assert.equal(id,uid);calls.push('delete-user');return {error:null}}}},
    from(table){
      calls.push('read:'+table);
      const result={data:table==='profiles'?{avatar_path:avatar}:table==='character_submissions'?sources:applications,error:null};
      return {select(){return this},eq(field,value){assert.equal(field,'user_id');assert.equal(value,uid);return this},async maybeSingle(){return result},then(resolve){resolve(result)}};
    }
  };
  const ctx={corsHeaders:{},Response,console:{error(){}},CONFIRM_PHRASE:'SUPPRIMER MON COMPTE',
    async requiredUser(){if(authDenied)throw Error('AUTH_REQUIRED');return {id:uid}},async readBoundedJson(){return {confirm}},
    serviceClient:()=>service,bearerToken:()=> 'synthetic-token',
    async removeStoragePaths(service,bucket,paths){calls.push('delete-storage');calls.push({bucket,paths:Array.from(paths)})},
    privateJson:(payload,status=200)=>({payload,status})};
  ctx.Deno={serve(handler){ctx.handler=handler}};
  vm.runInNewContext(code,ctx,{timeout:1000});
  const result=await ctx.handler({method:'POST'});
  return {...result,calls};
}
let count=0;
async function deny(options,status,code){
  const result=await invoke(options);
  assert.equal(result.status,status);
  assert.equal(result.payload.code,code);
  assert.equal(result.payload.ok,false);
  assert.ok(!result.calls.some(x=>(typeof x==='string'&&x.startsWith('read:'))||['delete-storage','revoke_sinjira_contributions','delete-user'].includes(x)),'no destructive operations');
  count++;
}
(async()=>{
  for(const admin of [null,0,1,'false','true',{},[],[false]])await deny({admin},503,'ADMIN_CHECK_FAILED');
  await deny({adminError:{code:'RPC_FAILED'}},503,'ADMIN_CHECK_FAILED');
  await deny({admin:true},403,'OWNER_OR_ADMIN_DELETE_BLOCKED');
  for(const aal of [null,{}, {currentLevel:'aal1'}, {nextLevel:'aal1'}, {currentLevel:'aal3',nextLevel:'aal2'}, {currentLevel:'aal1',nextLevel:'unknown'}, {currentLevel:'aal2',nextLevel:'aal1'}, {currentLevel:null,nextLevel:null}, {currentLevel:1,nextLevel:'aal2'}])await deny({aal},503,'MFA_STATE_UNAVAILABLE');
  await deny({aalError:{code:'RPC_FAILED'}},503,'MFA_STATE_UNAVAILABLE');
  await deny({aal:{currentLevel:'aal1',nextLevel:'aal2'}},403,'MFA_REQUIRED');
  for(const canDelete of [false,null,'true',1,{}])await deny({canDelete},409,'LEGAL_HOLD_ACTIVE');
  await deny({holdError:{code:'FAIL'}},503,'LEGAL_HOLD_CHECK_FAILED');
  await deny({confirm:'incorrect'},400,'CONFIRMATION_REQUIRED');
  await deny({authDenied:true},401,'AUTH_REQUIRED');
  for(const aal of [{currentLevel:'aal1',nextLevel:'aal1'},{currentLevel:'aal2',nextLevel:'aal2'}]){
    const result=await invoke({aal});
    assert.equal(result.status,200);assert.equal(result.payload.deleted,true);
    assert.ok(result.calls.indexOf('mfa')<result.calls.indexOf('delete-storage'));
    assert.ok(result.calls.indexOf('revoke_sinjira_contributions')<result.calls.indexOf('delete-user'));
    count++;
  }
  for(const value of ['other/avatar.png',uid+'-extra/photo.png',uid+'/../foreign.png',uid+'/%2e%2e/foreign.png',uid+'/a\\b.png',uid+'//a.png',uid+'/.',uid+'/a.png ',uid+'/a\u0000.png',uid+'/'+'a'.repeat(1024),42,{},[]]){
    // Put the bad reference in the last bucket: not even the valid avatar may be removed.
    const result=await invoke({sources:[{photo_path:uid+'/legitimate.png'}],applications:[{photo_path:value}]});
    assert.equal(result.status,503);assert.equal(result.payload.code,'STORAGE_PATH_OWNERSHIP_INVALID');
    assert.ok(!result.calls.some(x=>['delete-storage','revoke_sinjira_contributions','delete-user'].includes(x)));
    count++;
  }
  for(const options of [{sources:null},{applications:{} }]){
    const result=await invoke(options);
    assert.equal(result.status,503);assert.equal(result.payload.code,'STORAGE_PATH_LOOKUP_FAILED');
    assert.ok(!result.calls.some(x=>['delete-storage','revoke_sinjira_contributions','delete-user'].includes(x)));count++;
  }
  const good=await invoke({avatar:null,sources:[{photo_path:uid+'/photo.png'},{photo_path:uid+'/photo.png'},{photo_path:null}],applications:[{photo_path:uid+'/legacy/photo.jpg'}]});
  assert.equal(good.status,200);
  assert.deepEqual(good.calls.filter(x=>typeof x==='object'),[
    {bucket:'sinjira-avatars',paths:[]},
    {bucket:'sinjira-character-sources',paths:[uid+'/photo.png']},
    {bucket:'sinjira-character-submissions',paths:[uid+'/legacy/photo.jpg']}
  ]);count++;
  console.log('PASS: '+count+' account deletion authorization scenarios, no real data.');
})().catch(error=>{console.error(error);process.exitCode=1});
