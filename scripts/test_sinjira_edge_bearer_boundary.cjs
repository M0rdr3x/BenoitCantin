'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../supabase/functions/_shared/auth.ts'),'utf8');
const start=source.indexOf('export function bearerToken('),end=source.indexOf('\nfunction edgeFunctionName(',start);
const authStart=source.indexOf('async function authenticatedContext('),authEnd=source.indexOf('\nasync function assuranceLevel(',authStart);
assert.ok(start>=0&&end>start&&authStart>=0&&authEnd>authStart);
let serviceCalls=0,authCalls=0,lastToken='';
const ctx={serviceClient(){serviceCalls++;return {auth:{async getUser(token){authCalls++;lastToken=token;return {data:{user:{id:'synthetic'}},error:null}}}}}};
vm.runInNewContext(source.slice(start,end).replace('export function','function').replace('req: Request','req')+
 source.slice(authStart,authEnd).replace('req: Request','req')+
 '\nthis.parse=bearerToken;this.auth=authenticatedContext;',ctx,{timeout:1000});
const request=value=>({headers:{get(name){assert.equal(name,'Authorization');return value}}});
const token='eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.synthetic_signature-1';
let count=0;
(async()=>{
 for(const scheme of ['Bearer ','bearer ','BEARER ','Bearer  ']){
   const req=request(scheme+token);
   assert.equal(ctx.parse(req),token);
   await ctx.auth(req);
   assert.equal(lastToken,token);
   count++;
 }
 const maximum='a'.repeat(16384-7-4)+'.b.c';
 assert.equal(ctx.parse(request('Bearer '+maximum)),maximum);count++;
 const malformed=[null,'','Basic '+token,'Bearer','Bearer ','Bearer opaque','Bearer a.b','Bearer a.b.c.d','Bearer a..c','Bearer .b.c','Bearer a.b.','Bearer a.b.c=','Bearer a.b.c+','Bearer a/b.c.d','Bearer '+token+', Bearer '+token,'Bearer '+token+',' ,'Bearer '+token+' ','Bearer '+token+'\n','Bearer '+token+'\r','Bearer\t'+token,'Bearer '+token+'\tfoo','Bearer a. b.c','Bearer a.b.c\u0000','Bearer a.b.c\u2028','Bearer a.b.c\u2029','Bearer '+maximum+'x'];
 for(const header of malformed){
   const before=[serviceCalls,authCalls];
   assert.equal(ctx.parse(request(header)),'');
   await assert.rejects(ctx.auth(request(header)),/AUTH_REQUIRED/);
   assert.deepEqual([serviceCalls,authCalls],before,'No privileged client or Auth request on malformed header');
   count++;
 }
 const combined=new Headers();combined.append('Authorization','Bearer '+token);combined.append('Authorization','Bearer '+token);
 assert.equal(ctx.parse({headers:combined}),'');count++;
 console.log('PASS: '+count+' bearer boundary scenarios; malformed input never reaches Auth.');
})().catch(e=>{console.error(e);process.exitCode=1});
