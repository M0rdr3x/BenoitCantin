#!/usr/bin/env node
// Exercices réels du handler fetch PWA : aucun contenu privé dans Cache Storage.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const worker=readFileSync('sw.js','utf8');
assert.match(worker,/public-14-owned-lifecycle/);
assert.ok(worker.includes("'/projets/projet-nova/script.js'"));
assert.ok(worker.includes("'/projets/projet-nova/styles.css'"));

function testHarness({installCC='public, max-age=300',installVary='',installRedirected=false,installStatus=200,installResponsePath='',installOffline=false}={}) {
  const listeners=new Map();
  const requests=[], stored=[], lookups=[], deleted=[];
  let skipWaitingCount=0,claimCount=0;
  let cacheControl=installCC;
  let varyHeader=installVary;
  let redirected=installRedirected;
  let status=installStatus;
  let responseUrl=installResponsePath?new URL(installResponsePath,'https://www.benoitcantin.com').href:'';
  let networkOffline=installOffline;
  let storedFallbackPath=null;
  const response=()=>({
    ok:status>=200&&status<300,
    status,redirected,url:responseUrl,
    headers:{get(name){return name.toLowerCase()==='cache-control'?cacheControl:name.toLowerCase()==='vary'?varyHeader:null;}},
    clone(){return this;},
  });
  const cache={
    put(request){stored.push(request.url);return Promise.resolve();},
    addAll(){throw new Error('addAll sans validation est interdit pour le précache');},
  };
  const caches={
    open(){return Promise.resolve(cache);},
    match(request){const key=typeof request==='string'?request:request.url;lookups.push(key);return Promise.resolve(key===storedFallbackPath?response():undefined);},
    keys(){return Promise.resolve([
      'benoitcantin-v24-4-95-public-14-owned-lifecycle',
      'benoitcantin-v24-4-95-public-13-verified-install',
      'benoitcantin-old-release',
      'sinjira-account-private-cache',
      'other-project-cache',
    ]);},
    delete(key){deleted.push(key);return Promise.resolve(true);},
  };
  const self={
    addEventListener(name,handler){listeners.set(name,handler);},
    skipWaiting(){skipWaitingCount++;},clients:{claim(){claimCount++;return Promise.resolve();}},
  };
  class Request {
    constructor(original,settings={}) {
      this.url=typeof original==='string'?new URL(original,'https://www.benoitcantin.com').href:original.url;
      this.method=typeof original==='string'?'GET':original.method;
      this.destination=typeof original==='string'?'':original.destination;
      this.headers=typeof original==='string'?{get(){return null;}}:original.headers;
      this.cache=settings.cache||original.cache;
      this.credentials=settings.credentials||original.credentials;
    }
  }
  async function fetch(request){requests.push(request);if(networkOffline)throw new Error('offline');return response();}
  vm.runInNewContext(worker,{self,caches,fetch,Request,location:{origin:'https://www.benoitcantin.com'},URL,console},{filename:'sw.js',timeout:2000});
  const handler=listeners.get('fetch');
  assert.equal(typeof handler,'function');
  return {
    async verifyInstall({expectedCache=true,expectFailure=false}={}) {
      let pending;
      listeners.get('install')({waitUntil(p){pending=p;}});
      if(expectFailure) {
        await assert.rejects(pending,/offline/,'Une installation réseau incomplète doit échouer');
        assert.ok(deleted.includes('benoitcantin-v24-4-95-public-14-owned-lifecycle'),
          'Le cache partiel de cette installation doit être nettoyé');
        assert.equal(skipWaitingCount,0,'Un worker incomplet ne doit pas devenir actif');
        return;
      }
      await pending;
      assert.equal(skipWaitingCount,1,'Seule une installation valide peut activer le nouveau worker');
      assert.ok(requests.length>=60,'Les chemins publics doivent être téléchargés anonymement');
      assert.equal(stored.length,expectedCache?requests.length:0,
        'Seules les réponses publiques validées peuvent entrer dans le précache');
      for(const request of requests){
        assert.equal(request.credentials,'omit','Aucun cookie utilisateur dans le précache');
        assert.equal(request.cache,'no-store','Le précache initial doit ignorer le cache HTTP');
        assert.ok(request.url.startsWith('https://www.benoitcantin.com/'));
        assert.ok(!/\/(?:compte|admin|Admin|app|supabase|histoire-de-vie)\//.test(request.url),
          'Aucun espace privé admis dans le précache');
      }
    },
    async verifyActivate() {
      let pending;
      listeners.get('activate')({waitUntil(p){pending=p;}});
      await pending;
      assert.equal(claimCount,1,'Le nouveau worker doit prendre le contrôle après nettoyage');
      assert.deepEqual(deleted.sort(),[
        'benoitcantin-old-release',
        'benoitcantin-v24-4-95-public-13-verified-install',
      ].sort(),'Ne supprimer que les anciennes versions du cache BenoitCantin');
    },
    async run(path,{authorization='',key='',cc='public, max-age=300',vary='',destination='',offline=false,cachedPath=null,redirectedResponse=false,responseStatus=200,responsePath=''}={}) {
      cacheControl=cc;
      varyHeader=vary;
      redirected=redirectedResponse;
      status=responseStatus;
      responseUrl=responsePath?new URL(responsePath,'https://www.benoitcantin.com').href:'';
      networkOffline=offline;
      storedFallbackPath=cachedPath;
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
      const outcome=await result;
      await new Promise(resolve=>setImmediate(resolve));
      return {requests:[...requests],stored:[...stored],lookups:[...lookups],outcome};
    },
  };
}

const h=testHarness();
await h.verifyInstall();
await h.verifyActivate();
await testHarness({installOffline:true}).verifyInstall({expectFailure:true});
for(const scenario of [
  {installCC:'private, max-age=300'},
  {installCC:'no-store'},
  {installCC:'no-cache'},
  {installVary:'Cookie'},
  {installVary:'Authorization'},
  {installVary:'*'},
  {installRedirected:true},
  {installStatus:206},
  {installResponsePath:'/auth/session'},
  {installResponsePath:'https://evil.invalid/fallback'},
]){
  const isolated=testHarness(scenario);
  await isolated.verifyInstall({expectedCache:false});
}
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
// Nouvelle règle positive : futures routes publiques apparentes ne sont
// JAMAIS retenues dans le cache tant qu'elles ne sont pas en liste CORE.
await expectedNoStore('/projets/projet-nova/registre-dynamique.html');
await expectedNoStore('/assets/js/nouveau-module.js');
await expectedNoStore('/projets/sinjira/nouveau-rapport.json');
await expectedNoStore('/projets/projet-nova/?section=privee');
await expectedNoStore('/?mode=personnalise');
await expectedNoStore('/a-propos.html?v=42');
await expectedNoStore('/assets/js/site.js?v=26.2.0&mode=session');


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
const redirectedPublic=await h.run(publicJson,{redirectedResponse:true,responsePath:'/auth/session'});
assert.equal(redirectedPublic.stored.length,0,'Une redirection vers la connexion ne doit jamais entrer dans le cache');
const partialPublic=await h.run(publicJson,{responseStatus:206});
assert.equal(partialPublic.stored.length,0,'Une réponse HTTP 206 partielle ne doit jamais entrer dans le cache');

for(const vary of ['Cookie','Authorization','Accept-Language, Cookie','*']){
  const result=await h.run(publicJson,{vary});
  assert.equal(result.stored.length,0,'La réponse variant selon '+vary+' ne doit pas être cachée');
}


// Les scripts/CSS Nova sont servis réseau d'abord, même si une ancienne
// version pourrait déjà se trouver en Cache Storage.
for(const path of [
  '/projets/projet-nova/script.js?v=26.2.0',
  '/projets/projet-nova/styles.css?v=25',
  '/assets/js/site.js?v=24.4.100',
]){
  const fresh=await h.run(path);
  assert.equal(fresh.requests.length,1,path+' doit consulter le réseau avant le cache');
  assert.equal(fresh.requests[0].cache,'no-store',path+' doit ignorer le cache HTTP local');
  assert.deepEqual(fresh.lookups,[],path+' ne doit pas charger en priorité une vieille version');
  assert.equal(fresh.stored.length,1,path+' peut garder un repli public');
  if(path.startsWith('/projets/projet-nova/')){
    const offline=await h.run(path,{offline:true,cachedPath:path.split('?')[0]});
    assert.equal(offline.requests.length,1,'Une requête réseau doit être tentée avant le repli');
    assert.equal(offline.requests[0].cache,'no-store');
    assert.equal(offline.lookups[0],'https://www.benoitcantin.com'+path);
    assert.ok(offline.lookups.includes(path.split('?')[0]),
      'En cas de panne réseau, rechercher la ressource Nova précachée sans version');
    assert.ok(offline.outcome,'La ressource statique Nova doit rester disponible hors ligne');
  }
  const privateAsset=await h.run(path,{cc:'private, no-store'});
  assert.equal(privateAsset.stored.length,0,path+' ne doit jamais sauvegarder une réponse privée');
}

console.log('OK PWA : précache public uniquement, requêtes à paramètres non conservées, Vary Cookie/auth, API et assets Nova frais.');
