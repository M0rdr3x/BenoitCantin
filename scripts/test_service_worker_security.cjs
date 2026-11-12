'use strict';
// Exécute le vrai Service Worker en VM avec un faux réseau et CacheStorage isolés.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../sw.js'),'utf8');
const ORIGIN='https://www.benoitcantin.com';
function mime(p){
  if(p.endsWith('.js'))return 'text/javascript';
  if(p.endsWith('.css'))return 'text/css';
  if(p.endsWith('.webmanifest'))return 'application/manifest+json';
  if(p.endsWith('.png'))return 'image/png';
  if(p.endsWith('.webp'))return 'image/webp';
  if(p.endsWith('.svg'))return 'image/svg+xml';
  return 'text/html';
}
class MockRequest {
  constructor(input,opts={}){
    const src=typeof input==='string'?{}:input;
    this.url=new URL(typeof input==='string'?input:input.url,ORIGIN).href;
    this.method=opts.method||src.method||'GET';
    this.mode=opts.mode||src.mode||'cors';
    this.cache=opts.cache||src.cache||'default';
    this.credentials=opts.credentials||src.credentials||'include';
    this.headers=new Headers(opts.headers||src.headers||{});
    this.redirect=opts.redirect||src.redirect||'follow';
  }
}
class MockResponse {
  constructor(url,opts={}){
    this.url=opts.url||url;
    this.status=opts.status??200;
    this.redirected=!!opts.redirected;
    this.type=opts.type||'basic';
    this.headers=new Headers({'Content-Type':mime(new URL(url).pathname),...(opts.headers||{})});
    this.value=opts.value||'public';
  }
  clone(){return this;}
}
function boot(options={}){
  const events={};
  const map=new Map();
  const calls=[];
  const caches={
    async open(name){
      if(!map.has(name))map.set(name,new Map());
      const bucket=map.get(name);
      return {async put(key,value){bucket.set(new URL(key,ORIGIN).pathname,value);},async match(key){return bucket.get(new URL(key,ORIGIN).pathname);}};
    },
    async keys(){return [...map.keys()];},
    async delete(name){return map.delete(name);},
    async match(key){for(const bucket of map.values()){const got=bucket.get(new URL(key,ORIGIN).pathname);if(got)return got;}},
  };
  const fetch=async request=>{
    const req=new MockRequest(request);
    calls.push(req);
    if(options.offline)throw Error('offline');
    const url=new URL(req.url);
    const overrides=options.overrides||{};
    const over=overrides[url.pathname]||{};
    if(over.throw)throw Error('network failure');
    return new MockResponse(req.url,over);
  };
  const self={addEventListener(name,fn){events[name]=fn;},async skipWaiting(){},clients:{async claim(){}}};
  const context=vm.createContext({self,caches,fetch,Request:MockRequest,URL,location:{origin:ORIGIN},Set,Promise,Error});
  vm.runInContext(source,context,{filename:'sw.js'});
  const cacheName=vm.runInContext('CACHE',context);
  const core=[...vm.runInContext('CORE',context)];
  async function trigger(name,request){
    let response;
    const promises=[];
    events[name]({request,waitUntil(p){promises.push(p);},respondWith(p){response=p;}});
    if(promises.length)await Promise.all(promises);
    return response===undefined?undefined:response;
  }
  return {trigger,cacheName,core,caches,map,calls};
}
function req(path,opts={}){return new MockRequest(ORIGIN+path,opts);}
async function fetchEvent(env,path,opts={}){
  const promise=await env.trigger('fetch',req(path,opts));
  return promise===undefined?undefined:await promise;
}
async function run(){
  let total=0;
  function check(message,condition){assert.ok(condition,message);total++;}

  {
    const env=boot();
    await env.caches.open('other-application-cache');
    await env.caches.open('benoitcantin-v24-4-95-public-3');
    await env.trigger('install');
    check('precache complet',env.map.get(env.cacheName).size===env.core.length);
    check('precache sans cookies',env.calls.every(x=>x.credentials==='omit'&&x.redirect==='error'));
    await env.trigger('activate');
    check('ne jamais supprimer les caches étrangers',env.map.has('other-application-cache'));
    check('supprimer uniquement ancien cache détenu',!env.map.has('benoitcantin-v24-4-95-public-3'));
  }
  {
    const env=boot({overrides:{'/assets/css/site.css':{headers:{'Cache-Control':'private, max-age=0'}}}});
    await assert.rejects(()=>env.trigger('install'),/non admissible/);
    check('installation refuse et efface le précache incomplet',!env.map.has(env.cacheName));
  }
  for(const path of ['/compte/mon-profil.html','/admin/sinjira/','/Admin/sinjira/','/app/','/supabase/config.toml','/histoire-de-vie/','/administration.html']){
    const env=boot();
    await fetchEvent(env,path,{mode:'navigate'});
    check('chemin privé sans stockage: '+path,!env.map.has(env.cacheName));
    check('chemin privé réseau sans cache HTTP: '+path,env.calls[0].cache==='no-store');
  }
  for(const [path,opts] of [
    ['/api/private'],['/assets/js/site.js?token=test'],
    ['/assets/js/site.js',{headers:{Authorization:'Bearer secret'}}],
    ['/assets/js/site.js',{headers:{Range:'bytes=0-10'}}],
    ['/assets/js/site.js',{cache:'no-store'}],
    ['/assets/media/other.pdf'],
  ]){
    const env=boot();
    await fetchEvent(env,path,opts||{});
    check('aucune entrée illégitime: '+path+' '+JSON.stringify(opts||{}),!env.map.has(env.cacheName));
  }
  const scenarios=[
    {headers:{'Cache-Control':'no-store'}},
    {headers:{'Cache-Control':'private'}},
    {headers:{'Cache-Control':'no-cache'}},
    {headers:{Vary:'Accept, Cookie'}},
    {headers:{Vary:'Authorization'}},
    {headers:{'Set-Cookie':'sid=secret'}},
    {headers:{'Content-Type':'text/html'}},
    {status:206},
    {status:302,redirected:true},
    {url:'https://evil.example/assets/js/site.js'},
    {type:'opaque'},
  ];
  for(const over of scenarios){
    const env=boot({overrides:{'/assets/js/site.js':over}});
    await fetchEvent(env,'/assets/js/site.js');
    check('réponse dangereuse non cachée: '+JSON.stringify(over),!env.map.get(env.cacheName)?.has('/assets/js/site.js'));
  }
  {
    const env=boot();
    await fetchEvent(env,'/assets/js/site.js');
    check('asset statique admissible mis en cache',env.map.get(env.cacheName)?.has('/assets/js/site.js'));
    check('asset statique sans credentials',env.calls[0].credentials==='omit');
  }
  {
    const env=boot({offline:true});
    const foreign=await env.caches.open('foreign-cache');
    await foreign.put('/assets/js/site.js',new MockResponse(ORIGIN+'/assets/js/site.js',{value:'foreign'}));
    await assert.rejects(async()=>fetchEvent(env,'/assets/js/site.js'),/offline/);
    check('aucune lecture d’un cache étranger en panne réseau',!env.map.get(env.cacheName)?.has('/assets/js/site.js'));
  }
  {
    const env=boot();
    const x=await env.trigger('fetch',new MockRequest('https://evil.example/assets/js/site.js'));
    check('autre origine non interceptée',x===undefined&&env.calls.length===0);
  }
  console.log('PASS: '+total+' vérifications Service Worker, refus privés, réponses et isolation des caches');
}
run().catch(error=>{console.error(error);process.exitCode=1;});