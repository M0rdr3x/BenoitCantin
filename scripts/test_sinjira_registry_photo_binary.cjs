'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const src=fs.readFileSync(path.join(__dirname,'../supabase/functions/submit-character-questionnaire/index.ts'),'utf8');
const start=src.indexOf('function registryPhotoSignature('),end=src.indexOf('// Le chemin seul',start);
assert.ok(start>=0&&end>start);
const code=src.slice(start,end)
 .replace('(header:Uint8Array,ext:string,total:number):boolean','(header,ext,total)')
 .replace('(offset:number,expected:number[])','(offset,expected)')
 .replace('(offset:number,value:string)','(offset,value)')
 .replace('(width:number,height:number)','(width,height)')
 .replace('(file:any,photoPath:string,expectedSize:number,deadlineMs=8000):Promise<boolean>','(file,photoPath,expectedSize,deadlineMs=8000)')
 .replace('timer:ReturnType<typeof setTimeout>|undefined','timer')
 .replace('new Promise<never>','new Promise')
 .replace('reader:ReadableStreamDefaultReader<Uint8Array>|undefined','reader');
const ctx={Uint8Array,DataView,AbortSignal,AbortController,setTimeout,clearTimeout};vm.runInNewContext(code+'\nthis.verify=registryPhotoBinaryVerified;',ctx);
const make=(n)=>new Uint8Array(n);
const ascii=(buf,offset,s)=>buf.set(Buffer.from(s,'ascii'),offset);
const png=make(33);png.set([137,80,78,71,13,10,26,10,0,0,0,13]);ascii(png,12,'IHDR');new DataView(png.buffer).setUint32(16,640);new DataView(png.buffer).setUint32(20,480);
const jpg=Uint8Array.from([255,216,255,192,0,11,8,1,224,2,128,1,1,17,0,255,217]);
const gif=make(14);ascii(gif,0,'GIF89a');new DataView(gif.buffer).setUint16(6,640,true);new DataView(gif.buffer).setUint16(8,480,true);
const webp=make(30);ascii(webp,0,'RIFF');new DataView(webp.buffer).setUint32(4,22,true);ascii(webp,8,'WEBPVP8X');new DataView(webp.buffer).setUint32(16,10,true);webp.set([127,2,0,223,1,0],24);
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
 // Dimensions déclarées : zéro, côté excessif et produit excessif.
 for(const [width,height] of [[0,480],[8193,1],[5001,5000]]){
   const p=png.slice();new DataView(p.buffer).setUint32(16,width);new DataView(p.buffer).setUint32(20,height);await check('png',p,false);
   const j=jpg.slice();new DataView(j.buffer).setUint16(9,width);new DataView(j.buffer).setUint16(7,height);await check('jpg',j,false);
   const g=gif.slice();new DataView(g.buffer).setUint16(6,width,true);new DataView(g.buffer).setUint16(8,height,true);await check('gif',g,false);
 }
 for(const [width,height] of [[8193,1],[5001,5000]]){
   const w=webp.slice();const v=new DataView(w.buffer);v.setUint16(24,width-1,true);v.setUint16(27,height-1,true);await check('webp',w,false);
 }
 const exact=png.slice();new DataView(exact.buffer).setUint32(16,5000);new DataView(exact.buffer).setUint32(20,5000);await check('png',exact,true);
 const lossless=make(26);ascii(lossless,0,'RIFF');new DataView(lossless.buffer).setUint32(4,18,true);ascii(lossless,8,'WEBPVP8L');new DataView(lossless.buffer).setUint32(16,5,true);lossless[20]=47;new DataView(lossless.buffer).setUint32(21,639|(479<<14),true);await check('webp',lossless,true);
 const lossy=make(30);ascii(lossy,0,'RIFF');new DataView(lossy.buffer).setUint32(4,22,true);ascii(lossy,8,'WEBPVP8 ');new DataView(lossy.buffer).setUint32(16,10,true);lossy.set([157,1,42],23);new DataView(lossy.buffer).setUint16(26,640,true);new DataView(lossy.buffer).setUint16(28,480,true);await check('webp',lossy,true);
 const oversizedLossless=lossless.slice();new DataView(oversizedLossless.buffer).setUint32(21,8192|(479<<14),true);await check('webp',oversizedLossless,false);
 const oversizedLossy=lossy.slice();new DataView(oversizedLossy.buffer).setUint16(26,8193,true);await check('webp',oversizedLossy,false);
 await check('jpg',Uint8Array.from([255,216,255,217]),false);
 const truncated=jpg.slice();truncated[5]=255;await check('jpg',truncated,false);
 const malformedWebp=webp.slice();new DataView(malformedWebp.buffer).setUint32(16,99,true);await check('webp',malformedWebp,false);
 // JPEG avec métadonnées avant SOF, au-delà de l'ancien préfixe 256 octets.
 const withApp=make(jpg.length+304);withApp.set(jpg.slice(0,2));withApp.set([255,225,1,46],2);withApp.set(jpg.slice(2),304);await check('jpg',withApp,false);
 const app=make(jpg.length+304);app.set(jpg.slice(0,2));app.set([255,225,1,46],2);app.set(jpg.slice(2),306);await check('jpg',app,true);
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
