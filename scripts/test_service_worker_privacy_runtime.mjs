#!/usr/bin/env node
// Exercices réels du handler fetch PWA : aucun contenu privé dans Cache Storage.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const worker=readFileSync('sw.js','utf8');
assert.match(worker,/public-10-private-cache/);

function testHarness() {
  const listeners=new Map();
  const requests=[], stored=[], lookups=[];
  let cacheControl='public, max-age=300';
  const response=()=>({
    ok:true,
    headers:{get(name){return name.toLowerCase()==='cache-control'?cacheControl:null;}},
    clone(){return this;},
  });
  const cache={
    put(request){stored.push(request.url);return Promise.resolve();},
    addAll(){return Promise.resolve();},
  };
  const caches={
    open(){return Promise.resolve(cache);},
    match(request){lookups.push(typeof request==='string'?request:request.url);return Promise.resolve(undefined);},
    keys(){return Promise.resolve([]);},
    delete(){return Promise.resolve(true);},
  };
  const self={
    addEventListener(name,handler){listeners.set(name,handler);},
    skipWaiting(){},clients:{claim(){return Promise.resolve();}},
  };
  class Request {
    constructor(original,settings={}) {
      this.url=original.url;
      this.method=original.method;
      this.destination=original.destination;
      this.headers=original.headers;
      this.cache=settings.cache||original.cache;
    }
  }
  async function fetch(request){requests.push(request);return response();}
  vm.runInNewContext(worker,{self,caches,fetch,Request,location:{origin:'https://www.benoitcantin.com'},URL,console},{filename:'sw.js',timeout:2000});
  const handler=listeners.get('fetch');
  assert.equal(typeof handler,'function');
  return {
    async run(path,{authorization='',key='',cc='public, max-age=300',destination=''}={}) {
      cacheControl=cc;
      requests.length=0;stored.length=0;lookups.length=0;
      const headers={get(name){
        if(name.toLowerCase()==='authorization')return authorization||null;
        if(name.toLowerCase()==='x-api-key')return key||null;
        return null;
      }};
      const request={url:'https://www.benoitcantin.com'+path,method:'GET',destination,headers};
      let result;
      handler({request,respondWith(p){result=p;}});
      assert.ok(result,'La requête doit recevoir une stratégie de service worker');
      await result;
      await new Promise(resolve=>setImmediate(resolve));
      return {requests:[...requests],stored:[...stored],lookups:[...lookups]};
    },
  };
}

const h=testHarness();
async function expectedNoStore(path,opts={}) {
  const r=await h.run(path,opts);
  assert.equal(r.requests.length,1,path+' : une seule requête réseau attendue');
  assert.equal(r.requests[0].cache,'no-store',path+' : réseau sans cache obligatoire');
  assert.equal(r.stored.length,0,path+' : ne jamais stocker en Cache Storage');
  assert.equal(r.lookups.length,0,path+' : ne jamais lire Cache Storage');
}
await expectedNoStore('/api/profile');
await expectedNoStore('/.netlify/functions/paid-book');
await expectedNoStore('/auth/session');
await expectedNoStore('/graphql');
await expectedNoStore('/projets/projet-nova/data/comptabilite.json');
await expectedNoStore('/projets/projet-nova/data/rencontres.json');
await expectedNoStore('/a-propos.html?access_token=abc');
await expectedNoStore('/a-propos.html',{authorization:'Bearer secret'});
await expectedNoStore('/a-propos.html',{key:'secret-key'});
await expectedNoStore('/.well-known/release.json');
await expectedNoStore('/compte/');
await expectedNoStore('/supabase/config.toml');

const publicJson='/projets/projet-nova/data/boussole-electorale-v2.json';
const allowed=await h.run(publicJson);
assert.equal(allowed.requests.length,1);
assert.equal(allowed.stored.length,1,'Le JSON de Boussole public autorisé reste précachable');

const privateResponse=await h.run(publicJson,{cc:'private, max-age=60'});
assert.equal(privateResponse.stored.length,0,'Les réponses Cache-Control: private ne sont jamais stockées');
const noCache=await h.run(publicJson,{cc:'no-cache, max-age=0'});
assert.equal(noCache.stored.length,0,'Les réponses sans cache ne sont jamais stockées');
const noStore=await h.run(publicJson,{cc:'no-store'});
assert.equal(noStore.stored.length,0,'Les réponses no-store ne sont jamais stockées');

console.log('OK PWA : routes API, sessions, jetons, données JSON non approuvées et réponses privées jamais cachées.');
