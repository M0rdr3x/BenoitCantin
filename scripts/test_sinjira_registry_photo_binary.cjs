'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const src=fs.readFileSync(path.join(__dirname,'../supabase/functions/submit-character-questionnaire/index.ts'),'utf8');
const start=src.indexOf('function registryPhotoSignature('),end=src.indexOf('// Le chemin seul',start);
assert.ok(start>=0&&end>start);
const code=src.slice(start,end)
 .replace('(header:Uint8Array,ext:string,total:number):boolean','(header,ext,total)')
 .replace('(offset:number,expected:number[])','(offset,expected)')
 .replace('(offset:number,value:string)','(offset,value)')
 .replace('(file:any,photoPath:string,expectedSize:number,deadlineMs=8000):Promise<boolean>','(file,photoPath,expectedSize,deadlineMs=8000)')
 .replace('timer:ReturnType<typeof setTimeout>|undefined','timer')
 .replace('new Promise<never>','new Promise')
 .replace('reader:ReadableStreamDefaultReader<Uint8Array>|undefined','reader');
const ctx={Uint8Array,DataView,AbortSignal,AbortController,setTimeout,clearTimeout};vm.runInNewContext(code+'\nthis.verify=registryPhotoBinaryVerified;',ctx);
const make=(n)=>new Uint8Array(n);
const ascii=(buf,offset,s)=>buf.set(Buffer.from(s,'ascii'),offset);
const png=make(33);png.set([137,80,78,71,13,10,26,10,0,0,0,13]);ascii(png,12,'IHDR');
const jpg=Uint8Array.from([255,216,255,224,0,0,255,217]);
const gif=make(14);ascii(gif,0,'GIF89a');
const webp=make(20);ascii(webp,0,'RIFF');new DataView(webp.buffer).setUint32(4,12,true);ascii(webp,8,'WEBPVP8 ');
const avif=make(24);new DataView(avif.buffer).setUint32(0,24);ascii(avif,4,'ftypmif1');ascii(avif,16,'avifmif1');
let assertions=0;
async function check(ext,buf,want,{size=buf.length,error=null,throwRead=false,split=3}={}){
 let cancelled=false,called=false;
 const stream=new ReadableStream({start(c){if(throwRead){c.error(Error('read failed'));return;}for(let i=0;i<buf.length;i+=split)c.enqueue(buf.slice(i,i+split));c.close();},cancel(){cancelled=true;}});
 const file={download(p,opt,params){called=true;assert.equal(p,'u/file.'+ext);assert.equal(params.cache,'no-store');assert.ok(params.signal instanceof AbortSignal);return {asStream:async()=>({data:stream,error})}}};
 assert.equal(await ctx.verify(file,'u/file.'+ext,size),want);assertions++;
 if(!Number.isSafeInteger(size)||size<1||size>10*1024*1024)assert.equal(called,false);
}
(async()=>{
 for(const [ext,buf] of Object.entries({png,jpg,gif,webp,avif})){
   await check(ext,buf,true);
   await check(ext,Buffer.from('<html>not an image</html>'),false);
   await check(ext,buf.slice(0,3),false);
   await check(ext,buf,false,{size:buf.length+1});
   await check(ext,buf,false,{size:buf.length-1});
 }
 await check('jpg',png,false);await check('png',jpg,false);await check('svg',png,false);
 await check('avif',avif.map((v,i)=>i>=16&&i<20?0:v),false);
 await check('webp',webp.map((v,i)=>i===4?0:v),false);
 await check('png',png,false,{error:{code:'STORAGE_ERROR'}});
 for(const error of [false,0,''])await check('png',png,false,{error});
 await check('png',png,false,{throwRead:true});
 for(const size of [0,-1,NaN,Infinity,3.5,10*1024*1024+1])await check('png',png,false,{size});
 let cancelled=false,released=false;
 const reader={async read(){return {done:false,value:new Uint8Array(100)}},async cancel(){cancelled=true},releaseLock(){released=true}};
 const file={download(){return {asStream:async()=>({data:{getReader:()=>reader},error:null})}}};
 assert.equal(await ctx.verify(file,'u/file.png',33),false);assert.ok(cancelled&&released);assertions++;
 // Fournisseur qui ignore AbortSignal : le délai doit rester effectif.
 for(const phase of ['download','read','cancel','empty','ambiguous']){
   let aborted=false;
   const never=()=>new Promise(()=>{});
   const fake={download(_p,_opt,{signal}){
     signal.addEventListener('abort',()=>{aborted=true},{once:true});
     return {asStream:()=>phase==='download'?never():Promise.resolve({error:null,data:{getReader:()=>({
       read:()=>phase==='read'?never():Promise.resolve(phase==='empty'?{done:false,value:new Uint8Array(0)}:phase==='ambiguous'?{done:1}:{done:false,value:new Uint8Array(100)}),
       cancel:()=>phase==='cancel'?never():Promise.resolve(),releaseLock(){}
     })}})};
   }};
   assert.equal(await ctx.verify(fake,'u/file.png',33,20),false,phase);
   assert.ok(aborted,phase+' aborted');assertions++;
 }
 assert.ok(src.includes('return await registryPhotoBinaryVerified(file,photoPath,info.size)'));
 console.log('PASS registry binary validation: '+assertions+' cases.');
})().catch(e=>{console.error(e);process.exitCode=1});
