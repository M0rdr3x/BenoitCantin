'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const src=fs.readFileSync(path.join(__dirname,'../supabase/functions/submit-character-questionnaire/index.ts'),'utf8');
const start=src.indexOf('async function registryPhotoStored(');
const end=src.indexOf('// Une violation UNIQUE',start);
assert.ok(start>=0&&end>start);
const code=src.slice(start,end).replace('(service:any,photoPath:string):Promise<boolean>','(service,photoPath)').replace('formats:Record<string,string>','formats');
const ctx={registryPhotoBinaryVerified:async()=>true};vm.runInNewContext(code+'\nthis.verify=registryPhotoStored;',ctx,{timeout:1000});
const prefix='10000000-0000-4000-8000-000000000001/aabbccdd-1234-4abc-8abc-001122334455.';
const bucketId='sinjira-character-sources';
let count=0;
async function check({ext='png',bucket={id:bucketId,public:false},bucketError=null,info={size:100,contentType:'image/png'},infoError=null,throws=false,want=false}={}){
  let reads=0;
  const service={storage:{async getBucket(id){assert.equal(id,bucketId);if(throws)throw Error('offline');return {data:bucket,error:bucketError}},from(id){assert.equal(id,bucketId);return {async info(p){assert.equal(p,prefix+ext);reads++;return {data:info,error:infoError}}}}}};
  assert.equal(await ctx.verify(service,prefix+ext),want);count++;
  if(bucketError||bucket?.id!==bucketId||bucket.public!==false||throws)assert.equal(reads,0);
}
(async()=>{
  for(const [ext,contentType] of Object.entries({jpg:'image/jpeg',png:'image/png',webp:'image/webp',avif:'image/avif',gif:'image/gif'}))await check({ext,info:{size:10*1024*1024,contentType},want:true});
  for(const size of [0,-1,0.5,10*1024*1024+1,Infinity,NaN,'100',null,undefined])await check({info:{size,contentType:'image/png'}});
  for(const contentType of ['image/svg+xml','image/jpeg','text/html','application/octet-stream',null,undefined])await check({info:{size:100,contentType}});
  for(const bucket of [null,{}, {id:bucketId,public:true},{id:bucketId,public:'false'},{id:'other',public:false}])await check({bucket});
  await check({bucketError:{code:'FAIL'}});await check({infoError:{code:'FAIL'}});await check({info:null});await check({throws:true});await check({ext:'svg'});await check({ext:'constructor'});
  const route=src.slice(src.indexOf('Deno.serve(async(req)=>{'));
  const canonical=route.indexOf('isCanonicalRegistryPhotoPath(photo_path,user.id)');
  const verified=route.indexOf('await registryPhotoStored(service,photo_path as string)');
  const state=route.indexOf("service.from('character_submissions')");
  assert.ok(canonical>=0&&canonical<verified&&verified<state,'Path and object verification precede dossier access');
  assert.ok(route.includes("code:'CHARACTER_PHOTO_UNVERIFIED'"));
  console.log('PASS registry upload metadata: '+count+' cases.');
})().catch(e=>{console.error(e);process.exitCode=1});
