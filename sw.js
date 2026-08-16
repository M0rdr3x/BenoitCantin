const CACHE='benoitcantin-v24-4-12-public-1';
const CORE=[
  '/','/offline.html',
  '/assets/css/site.css','/assets/css/home-v24-4-12.css','/assets/css/v19-pro.css','/assets/css/v24-platform.css','/assets/css/v24-3-2-fixes.css','/assets/css/v24-3-3-fixes.css','/assets/css/fracture-engine.css',
  '/assets/js/site.js','/assets/js/v24-3-1-runtime.js','/assets/js/v24-3-2-runtime.js','/assets/js/v24-3-3-runtime.js','/assets/js/v24-3-6-runtime.js','/assets/js/sinjira-fracture-lobby.js','/assets/js/sinjira-fracture-engine.js','/assets/js/sinjira-fracture-result.js',
  '/assets/icons/benoit-sigil.svg','/assets/media/sinjira-emblem.webp','/assets/media/nova-logo.webp','/assets/media/sinjira-livre-1-cover-480.webp',
  '/projets/sinjira/','/projets/sinjira/romans/','/projets/sinjira/communaute/','/projets/sinjira/codex/','/projets/sinjira/monde-parallele/','/projets/sinjira/marche/','/projets/sinjira/jeux/fracture-du-reseau-mere/','/projets/projet-nova/'
];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;
  const privatePath=u.pathname.startsWith('/compte/')||u.pathname.startsWith('/Admin/')||u.pathname.startsWith('/admin/')||u.pathname.startsWith('/supabase/');
  if(privatePath){e.respondWith(fetch(new Request(r,{cache:'no-store'})).catch(()=>caches.match('/offline.html')));return}
  if(r.destination==='document'){
    e.respondWith(fetch(new Request(r,{cache:'no-store'})).then(resp=>{const cp=resp.clone();caches.open(CACHE).then(c=>c.put(r,cp));return resp}).catch(()=>caches.match(r).then(x=>x||caches.match('/offline.html'))));return;
  }
  const liveAsset=/\/assets\/(?:js|css)\//.test(u.pathname);
  if(liveAsset){e.respondWith(fetch(new Request(r,{cache:'no-store'})).then(resp=>{if(resp.ok)caches.open(CACHE).then(c=>c.put(r,resp.clone()));return resp}).catch(()=>caches.match(r)));return}
  e.respondWith(caches.match(r).then(cached=>cached||fetch(r).then(resp=>{if(resp.ok&&u.pathname.indexOf('/documents/')===-1)caches.open(CACHE).then(c=>c.put(r,resp.clone()));return resp})));
});
