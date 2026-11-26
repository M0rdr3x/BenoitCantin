'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const src=fs.readFileSync(path.join(__dirname,'../supabase/functions/submit-character-questionnaire/index.ts'),'utf8');
const start=src.indexOf('async function registryPhotoStored(');
const end=src.indexOf('// Une violation UNIQUE',start);
assert.ok(start>=0&&end>start);
const code=src.slice(start,end).replace('(service:any,photoPath:string,metadataDeadlineMs=5000):Promise<boolean>','(service,photoPath,metadataDeadlineMs=5000)').replace('formats:Record<string,string>','formats').replace('metadataTimer:ReturnType<typeof setTimeout>|undefined','metadataTimer').replace('new Promise<never>','new Promise');
let binaryCalls=0;
const ctx={setTimeout,clearTimeout,registryPhotoBinaryVerified:async()=>{binaryCalls++;return true;}};vm.runInNewContext(code+'\nthis.verify=registryPhotoStored;',ctx,{timeout:1000});
const prefix='10000000-0000-4000-8000-000000000001/aabbccdd-1234-4abc-8abc-001122334455.';
const bucketId='sinjira-character-sources';
let count=0;
async function check({ext='png',bucket={id:bucketId,public:false},bucketError=null,info={size:100,contentType:'image/png'},infoError=null,throws=false,want=false}={}){
  let reads=0;
  const service={storage:{async getBucket(id){assert.equal(id,bucketId);if(throws)throw Error('offline');return {data:bucket,error:bucketError}},from(id){assert.equal(id,bucketId);return {async info(p){assert.equal(p,prefix+ext);reads++;return {data:info,error:infoError}}}}}};
  assert.equal(await ctx.verify(service,prefix+ext),want);count++;
  if(bucketError!==null||bucket?.id!==bucketId||bucket.public!==false||throws)assert.equal(reads,0);
}
(async()=>{
  for(const [ext,contentType] of Object.entries({jpg:'image/jpeg',png:'image/png',webp:'image/webp',avif:'image/avif',gif:'image/gif'}))await check({ext,info:{size:10*1024*1024,contentType},want:true});
  for(const size of [0,-1,0.5,10*1024*1024+1,Infinity,NaN,'100',null,undefined])await check({info:{size,contentType:'image/png'}});
  for(const contentType of ['image/svg+xml','image/jpeg','text/html','application/octet-stream',null,undefined])await check({info:{size:100,contentType}});
  for(const bucket of [null,{}, {id:bucketId,public:true},{id:bucketId,public:'false'},{id:'other',public:false}])await check({bucket});
  for(const error of [false,0,'']){await check({bucketError:error});await check({infoError:error});}
  await check({bucketError:{code:'FAIL'}});await check({infoError:{code:'FAIL'}});await check({info:null});await check({throws:true});await check({ext:'svg'});await check({ext:'constructor'});
  // Un fournisseur bloqué ne doit jamais déclencher une lecture binaire tardive.
  for(const phase of ['bucket','info']){
    let settle,infos=0;
    const pending=new Promise(resolve=>{settle=resolve;});
    const previous=binaryCalls;
    const service={storage:{
      getBucket:()=>phase==='bucket'?pending:Promise.resolve({data:{id:bucketId,public:false},error:null}),
      from:()=>({info:()=>{infos++;return pending;}})
    }};
    assert.equal(await ctx.verify(service,prefix+'png',20),false,phase);count++;
    settle(phase==='bucket'?{data:{id:bucketId,public:false},error:null}:{data:{size:100,contentType:'image/png'},error:null});
    await new Promise(resolve=>setTimeout(resolve,0));
    assert.equal(binaryCalls,previous,phase+' late binary');count++;
    assert.equal(infos,phase==='bucket'?0:1,phase+' later metadata');count++;
  }
  // Le budget est partagé, pas renouvelé entre les appels.
  let secondCalled=false;
  const shared={storage:{
    getBucket:()=>new Promise(resolve=>setTimeout(()=>resolve({data:{id:bucketId,public:false},error:null}),30)),
    from:()=>({info:()=>{secondCalled=true;return new Promise(resolve=>setTimeout(()=>resolve({data:{size:100,contentType:'image/png'},error:null}),60));}})
  }};
  const prior=binaryCalls;
  assert.equal(await ctx.verify(shared,prefix+'png',70),false);count++;
  assert.equal(secondCalled,true);count++;
  assert.equal(binaryCalls,prior);count++;
  // Tester le vrai garde local, y compris la libération répétée d'un ancien slot.
  const slotStart=src.indexOf('const registryPhotoActiveAccounts=');
  const slotEnd=src.indexOf('// Le chemin seul',slotStart);
  assert.ok(slotStart>=0&&slotEnd>slotStart);
  const slotCode=src.slice(slotStart,slotEnd).replace('new Set<string>()','new Set()').replace('(userId:string):(()=>void)|null','(userId)');
  const slots={};vm.runInNewContext(slotCode+'\nthis.reserve=reserveRegistryPhotoSlot;',slots,{timeout:1000});
  const a=slots.reserve('account-a');assert.equal(typeof a,'function');count++;
  assert.equal(slots.reserve('account-a'),null);count++;
  const b=slots.reserve('account-b');assert.equal(typeof b,'function');count++;
  assert.equal(slots.reserve('account-c'),null);count++;
  a();const renewed=slots.reserve('account-a');assert.equal(typeof renewed,'function');count++;
  a();assert.equal(slots.reserve('account-a'),null);count++;
  b();const c=slots.reserve('account-c');assert.equal(typeof c,'function');count++;
  renewed();c();const d=slots.reserve('account-d');assert.equal(typeof d,'function');count++;d();
  const route=src.slice(src.indexOf('Deno.serve(async(req)=>{'));
  const canonical=route.indexOf('isCanonicalRegistryPhotoPath(photo_path,user.id)');
  const verified=route.indexOf('await registryPhotoStored(service,photo_path as string)');
  const state=route.indexOf("service.from('character_submissions')");
  const reserve=route.indexOf('reserveRegistryPhotoSlot(user.id)');
  const release=route.indexOf('releasePhotoSlot();');
  assert.ok(canonical>=0&&canonical<reserve&&reserve<verified&&verified<release&&release<state,'Path, admission and object verification precede dossier access');
  assert.ok(route.includes("code:'CHARACTER_PHOTO_BUSY',version:VERSION},429)"));
  assert.match(route,/finally\s*\{\s*releasePhotoSlot\(\);\s*\}/);
  assert.ok(route.includes("code:'CHARACTER_PHOTO_UNVERIFIED'"));
  console.log('PASS registry upload metadata: '+count+' cases.');
})().catch(e=>{console.error(e);process.exitCode=1});
