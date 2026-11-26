'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const src=fs.readFileSync(path.join(__dirname,'../supabase/functions/submit-character-questionnaire/index.ts'),'utf8');
const start=src.indexOf('function registryPhotoSignature('),end=src.indexOf('// Admission locale par instance Edge',start);
assert.ok(start>=0&&end>start);
const code=src.slice(start,end)
 .replace('(header:Uint8Array,ext:string,total:number):boolean','(header,ext,total)')
 .replace('(offset:number,expected:number[])','(offset,expected)')
 .replace('(offset:number,value:string)','(offset,value)')
 .replace('(width:number,height:number)','(width,height)')
 .replace('new Set<string>()','new Set()')
 .replace('(from:number,to:number,level:number):boolean','(from,to,level)')
 .replace('(packed:number)','(packed)')
 .replace('subBlocks=():boolean','subBlocks=()')
 .replace('(file:any,photoPath:string,expectedSize:number,deadlineMs=8000):Promise<boolean>','(file,photoPath,expectedSize,deadlineMs=8000)')
 .replace('timer:ReturnType<typeof setTimeout>|undefined','timer')
 .replace('new Promise<never>','new Promise')
 .replace('reader:ReadableStreamDefaultReader<Uint8Array>|undefined','reader');
const ctx={Uint8Array,DataView,AbortSignal,AbortController,setTimeout,clearTimeout};vm.runInNewContext(code+'\nthis.verify=registryPhotoBinaryVerified;',ctx);
const make=(n)=>new Uint8Array(n);
const ascii=(buf,offset,s)=>buf.set(Buffer.from(s,'ascii'),offset);
// CRC de référence indépendant, bit à bit (vecteur connu vérifié ci-dessous).
const crc32=(data)=>{let crc=0xffffffff;for(const b of data){crc^=b;for(let i=0;i<8;i++)crc=(crc&1)?(0xedb88320^(crc>>>1)):(crc>>>1);}return (crc^0xffffffff)>>>0;};
assert.equal(crc32(Buffer.from('123456789')),0xcbf43926);
const sealChunk=(buf,pos)=>{const v=new DataView(buf.buffer,buf.byteOffset,buf.byteLength),n=v.getUint32(pos);v.setUint32(pos+8+n,crc32(buf.subarray(pos+4,pos+8+n)));return buf;};
const png=make(58);png.set([137,80,78,71,13,10,26,10,0,0,0,13]);ascii(png,12,'IHDR');new DataView(png.buffer).setUint32(16,640);new DataView(png.buffer).setUint32(20,480);new DataView(png.buffer).setUint32(33,1);ascii(png,37,'IDAT');png[41]=1;ascii(png,50,'IEND');png[24]=8;png[25]=2;for(const pos of [8,33,46])sealChunk(png,pos);
const jpg=Uint8Array.from([255,216,255,192,0,11,8,1,224,2,128,1,1,17,0,255,218,0,8,1,1,0,0,63,0,1,255,217]);
const gif=make(28);ascii(gif,0,'GIF89a');new DataView(gif.buffer).setUint16(6,640,true);new DataView(gif.buffer).setUint16(8,480,true);gif[13]=44;new DataView(gif.buffer).setUint16(18,640,true);new DataView(gif.buffer).setUint16(20,480,true);gif.set([2,1,1,0,59],23);
const webp=make(44);ascii(webp,0,'RIFF');new DataView(webp.buffer).setUint32(4,36,true);ascii(webp,8,'WEBPVP8X');new DataView(webp.buffer).setUint32(16,10,true);webp.set([127,2,0,223,1,0],24);ascii(webp,30,'VP8L');new DataView(webp.buffer).setUint32(34,5,true);webp[38]=47;new DataView(webp.buffer).setUint32(39,639|(479<<14),true);
// Fixtures de conteneurs : elles ne représentent pas des images décodables.
const box=(kind,payload)=>{const b=make(8+payload.length);new DataView(b.buffer).setUint32(0,b.length);ascii(b,4,kind);b.set(payload,8);return b;};
const concat=(...parts)=>Uint8Array.from(Buffer.concat(parts.map(p=>Buffer.from(p))));
const brand=make(16);ascii(brand,0,'mif1');ascii(brand,8,'avifmif1');
const ftyp=box('ftyp',brand);
const ispe=(width,height)=>{const p=make(12);new DataView(p.buffer).setUint32(4,width);new DataView(p.buffer).setUint32(8,height);return box('ispe',p);};
const meta=(...properties)=>box('meta',concat(make(4),box('iprp',box('ipco',concat(...properties)))));
const mdat=box('mdat',Uint8Array.of(1));
const avif=concat(ftyp,meta(ispe(640,480)),mdat);
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
   const p=png.slice();new DataView(p.buffer).setUint32(16,width);new DataView(p.buffer).setUint32(20,height);sealChunk(p,8);await check('png',p,false);
   const j=jpg.slice();new DataView(j.buffer).setUint16(9,width);new DataView(j.buffer).setUint16(7,height);await check('jpg',j,false);
   const g=gif.slice();new DataView(g.buffer).setUint16(6,width,true);new DataView(g.buffer).setUint16(8,height,true);await check('gif',g,false);
 }
 for(const [width,height] of [[8193,1],[5001,5000]]){
   const w=webp.slice();const v=new DataView(w.buffer);v.setUint16(24,width-1,true);v.setUint16(27,height-1,true);await check('webp',w,false);
 }
 const exact=png.slice();new DataView(exact.buffer).setUint32(16,5000);new DataView(exact.buffer).setUint32(20,5000);sealChunk(exact,8);await check('png',exact,true);
 // Le parcours doit continuer après les premiers en-têtes.
 const chunk=(type,data=make(0))=>{const c=make(12+data.length);new DataView(c.buffer).setUint32(0,data.length);ascii(c,4,type);c.set(data,8);return sealChunk(c,0);};
 for(const type of ['acTL','fcTL','fdAT'])await check('png',concat(png.slice(0,33),chunk(type,make(8)),png.slice(33)),false);
 await check('png',concat(png,Uint8Array.of(1)),false);
 await check('png',png.slice(0,-1),false);
 await check('png',concat(png.slice(0,33),png.slice(46)),false);
 await check('png',concat(png.slice(0,33),chunk('IHDR',make(13)),png.slice(33)),false);
 await check('png',concat(png.slice(0,33),chunk('ABCD'),png.slice(33)),false);
 await check('png',concat(png.slice(0,46),chunk('tEXt'),chunk('IDAT',make(1)),png.slice(46)),false);
 const oversizedChunk=png.slice();new DataView(oversizedChunk.buffer).setUint32(33,0xffffffff);await check('png',oversizedChunk,false);
 await check('png',concat(png.slice(0,33),chunk('IDAT',make(270000)),png.slice(33)),true,{split:4096});
 await check('png',concat(png.slice(0,33),chunk('IDAT',make(270000)),chunk('acTL',make(8)),png.slice(33)),false,{split:4096});
 // Corruptions CRC dans chacun des trois chunks, y compris leur contenu.
 for(const offset of [29,41,42,54]){const p=png.slice();p[offset]^=1;await check('png',p,false);}
 for(const kind of ['eXIf','tEXt','zTXt','iTXt','iCCP','vpAg','pHys'])await check('png',concat(png.slice(0,33),chunk(kind,make(16)),png.slice(33)),false);
 for(const [offset,value] of [[24,3],[25,1],[26,1],[27,1],[28,2]]){const p=png.slice();p[offset]=value;sealChunk(p,8);await check('png',p,false);}
 const srgb=chunk('sRGB',Uint8Array.of(0));
 const phys=chunk('pHYs',Uint8Array.of(0,0,0,1,0,0,0,1,1));
 await check('png',concat(png.slice(0,33),srgb,phys,png.slice(33)),true);
 await check('png',concat(png.slice(0,33),srgb,srgb,png.slice(33)),false);
 await check('png',concat(png.slice(0,33),chunk('sRGB',Uint8Array.of(4)),png.slice(33)),false);
 const indexed=png.slice();indexed[25]=3;indexed[24]=1;sealChunk(indexed,8);
 await check('png',indexed,false);
 await check('png',concat(indexed.slice(0,33),chunk('PLTE',Uint8Array.of(0,0,0,255,255,255)),indexed.slice(33)),true);
 await check('png',concat(indexed.slice(0,33),chunk('PLTE',make(9)),indexed.slice(33)),false);
 // Vrai PNG 1x1 RGB : données zlib générées localement.
 const ihdr=make(13);new DataView(ihdr.buffer).setUint32(0,1);new DataView(ihdr.buffer).setUint32(4,1);ihdr[8]=8;ihdr[9]=2;
 const real=concat(png.slice(0,8),chunk('IHDR',ihdr),chunk('IDAT',require('node:zlib').deflateSync(Buffer.from([0,255,0,0]))),chunk('IEND'));
 await check('png',real,true);
 await check('gif',concat(gif.slice(0,-1),gif.slice(13,-1),gif.slice(-1)),false);
 await check('gif',concat(gif,Uint8Array.of(1)),false);
 await check('gif',gif.slice(0,-1),false);
 const frame=gif.slice();new DataView(frame.buffer).setUint16(18,641,true);await check('gif',frame,false);
 const empty=gif.slice();empty[24]=0;await check('gif',empty,false);
 await check('gif',concat(gif.slice(0,13),Uint8Array.of(33,255,0),gif.slice(13)),false);
 await check('gif',concat(gif.slice(0,13),Uint8Array.of(33,254,1,65,0),gif.slice(13)),false);
 const lossless=make(26);ascii(lossless,0,'RIFF');new DataView(lossless.buffer).setUint32(4,18,true);ascii(lossless,8,'WEBPVP8L');new DataView(lossless.buffer).setUint32(16,5,true);lossless[20]=47;new DataView(lossless.buffer).setUint32(21,639|(479<<14),true);await check('webp',lossless,true);
 const lossy=make(30);ascii(lossy,0,'RIFF');new DataView(lossy.buffer).setUint32(4,22,true);ascii(lossy,8,'WEBPVP8 ');new DataView(lossy.buffer).setUint32(16,10,true);lossy.set([157,1,42],23);new DataView(lossy.buffer).setUint16(26,640,true);new DataView(lossy.buffer).setUint16(28,480,true);await check('webp',lossy,true);
 const oversizedLossless=lossless.slice();new DataView(oversizedLossless.buffer).setUint32(21,8192|(479<<14),true);await check('webp',oversizedLossless,false);
 const oversizedLossy=lossy.slice();new DataView(oversizedLossy.buffer).setUint16(26,8193,true);await check('webp',oversizedLossy,false);
 await check('jpg',Uint8Array.from([255,216,255,217]),false);
 const truncated=jpg.slice();truncated[5]=255;await check('jpg',truncated,false);
 const malformedWebp=webp.slice();new DataView(malformedWebp.buffer).setUint32(16,99,true);await check('webp',malformedWebp,false);
 // JPEG avec métadonnées avant SOF, au-delà de l'ancien préfixe 256 octets.
 const withApp=make(jpg.length+304);withApp.set(jpg.slice(0,2));withApp.set([255,225,1,46],2);withApp.set(jpg.slice(2),304);await check('jpg',withApp,false);
 const app=make(jpg.length+304);app.set(jpg.slice(0,2));app.set([255,225,1,46],2);app.set(jpg.slice(2),306);await check('jpg',app,false);
 const jfif=Uint8Array.of(255,224,0,16,74,70,73,70,0,1,1,0,0,1,0,1,0,0);
 await check('jpg',concat(jpg.slice(0,2),jfif,jpg.slice(2)),true);
 for(const marker of [225,226,237,254]){
   const seg=Uint8Array.of(255,marker,0,4,65,66);
   await check('jpg',concat(jpg.slice(0,2),seg,jpg.slice(2)),false);
   await check('jpg',concat(jpg.slice(0,-2),seg,jpg.slice(-2)),false);
 }
 await check('jpg',concat(jpg,Uint8Array.of(0)),false);
 await check('jpg',jpg.slice(0,-2),false);
 await check('jpg',concat(jpg.slice(0,-2),Uint8Array.of(255,0,7),jpg.slice(-2)),true);
 const webChunk=(kind,payload)=>{const b=make(8+payload.length+(payload.length%2));ascii(b,0,kind);new DataView(b.buffer).setUint32(4,payload.length,true);b.set(payload,8);return b;};
 const riff=(...parts)=>{const b=concat(webp.slice(0,12),...parts);new DataView(b.buffer).setUint32(4,b.length-8,true);return b;};
 for(const kind of ['EXIF','XMP ','ICCP','ANIM','ANMF','JUNK'])await check('webp',riff(webp.slice(12),webChunk(kind,make(2))),false);
 await check('webp',riff(webp.slice(12,30)),false);
 await check('webp',riff(webp.slice(30),webp.slice(30)),false);
 const wrongCanvas=webp.slice();wrongCanvas[24]--;await check('webp',wrongCanvas,false);
 const badPad=webp.slice();badPad[43]=1;await check('webp',badPad,false);
 const metadataFlag=webp.slice();metadataFlag[20]=8;await check('webp',metadataFlag,false);
 await check('jpg',png,false);await check('png',jpg,false);await check('svg',png,false);
 await check('avif',avif.map((v,i)=>i>=16&&i<20?0:v),false);
 for(const [width,height] of [[0,480],[8193,1],[5001,5000]])await check('avif',concat(ftyp,meta(ispe(width,height)),mdat),false);
 await check('avif',concat(ftyp,meta(ispe(5000,5000)),mdat),true);
 await check('avif',concat(ftyp,meta(ispe(640,480),ispe(9000,1)),mdat),false);
 await check('avif',concat(ftyp,meta(ispe(640,480),ispe(320,240)),mdat),true);
 await check('avif',concat(ftyp,meta(),mdat),false);
 await check('avif',concat(ftyp,mdat),false);
 await check('avif',concat(ftyp,meta(ispe(640,480))),false);
 await check('avif',concat(ftyp,meta(ispe(640,480)),meta(ispe(640,480)),mdat),false);
 const animated=ftyp.slice();ascii(animated,16,'avis');await check('avif',concat(animated,meta(ispe(640,480)),mdat),false);
 await check('avif',concat(ftyp,meta(ispe(640,480)),box('moov',make(0)),mdat),false);
 const invalidBox=avif.slice();new DataView(invalidBox.buffer).setUint32(24,0);await check('avif',invalidBox,false);
 const versioned=ispe(640,480);versioned[8]=1;await check('avif',concat(ftyp,meta(versioned),mdat),false);
 await check('avif',concat(ftyp,meta(box('free',ispe(640,480))),mdat),false);
 const animatedWebp=webp.slice();animatedWebp[20]=2;await check('webp',animatedWebp,false);
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
