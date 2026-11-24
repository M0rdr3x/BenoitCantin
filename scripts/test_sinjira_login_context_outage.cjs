'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-auth-pages.js'),'utf8');
const start=source.indexOf('async function login(){');
const end=source.indexOf('async function forgot(){',start);
assert.ok(start>=0&&end>start,'Module de connexion introuvable');
const login=source.slice(start,end);
async function run({outage,signout,authError=false}){
  const redirects=[],messages=[],scopes=[];
  let submit;
  const form={addEventListener(_event,handler){submit=handler}};
  const client={auth:{
    signInWithPassword:async()=>({error:authError?{message:'denied'}:null}),
    signOut:async({scope})=>{scopes.push(scope);if(signout==='throw')throw Error('offline');return signout;}
  }};
  const ctx={document:{querySelector:()=>form},getCurrentUser:async()=>null,
    ready:()=>true,reportInvalid:()=>false,FormData:class{get(){return ''}},
    destination:()=>'/compte/index.html',setBusy(){},clearPendingChallenge(){},
    securityDeviceMetadata:()=>({device_key:'synthetic-device-key'}),
    getSupabase:()=>client,evaluateLoginSecurity:async()=>{
      if(outage)throw Error('context unavailable');return {security:{outcome:'allow'}};
    },setStatus:(_node,message,type)=>messages.push({message,type}),
    status:null,location:{replace:v=>redirects.push(v)},console:{warn(){}}};
  vm.runInNewContext(login+'\nglobalThis.init=login;',ctx,{timeout:1000});
  await ctx.init();
  await submit({preventDefault(){}});
  return {redirects,messages,scopes};
}
async function main(){
  for(const signout of [{error:null},{error:{message:'denied'}},'throw',undefined,{}]){
    const result=await run({outage:true,signout});
    assert.deepEqual(result.redirects,[]);
    assert.deepEqual(result.scopes,['local']);
    assert.equal(result.messages.length,1);
    assert.equal(result.messages[0].type,'error');
    assert.equal(result.messages[0].message.includes('fermeture de cette session n’a pas été confirmée'),signout?.error!==null);
  }
  const allowed=await run({outage:false});
  assert.deepEqual(allowed.redirects,['/compte/index.html']);
  assert.deepEqual(allowed.scopes,[]);
  const refused=await run({outage:true,authError:true});
  assert.deepEqual(refused.redirects,[]);
  assert.deepEqual(refused.scopes,[]);
  console.log('PASS: 7 scénarios de connexion, panne contextuelle et fermeture non confirmée.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
