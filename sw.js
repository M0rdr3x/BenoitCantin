const CACHE='benoitcantin-v24-4-95-public-4';
const CACHE_PREFIX='benoitcantin-v24-4-95-public-';
const CORE=[
  '/','/offline.html','/manifest.webmanifest','/transparence-ia.html',
  '/assets/css/site.css','/assets/css/browser-compat-v24-4-22.css','/assets/css/ai-transparency.css','/assets/css/home-v24-4-12.css','/assets/css/v19-pro.css','/assets/css/v24-platform.css','/assets/css/v24-3-2-fixes.css','/assets/css/v24-3-3-fixes.css','/assets/css/fracture-engine.css','/assets/css/sinjira-assistant.css','/assets/css/sinjira-mobile-app-v24-4-94.css','/assets/css/sinjira-mobile-account-shell-v24-4-95.css',
  '/assets/js/site.js','/assets/js/sinjira-pwa-install.js','/assets/js/v24-3-1-runtime.js','/assets/js/v24-3-2-runtime.js','/assets/js/v24-3-3-runtime.js','/assets/js/v24-3-6-runtime.js','/assets/js/sinjira-fracture-lobby.js','/assets/js/sinjira-fracture-engine.js','/assets/js/sinjira-fracture-result.js','/assets/js/sinjira-assistant.js','/assets/js/sinjira-mobile-social-v24-4-94.js','/assets/js/sinjira-mobile-account-shell-v24-4-95.js',
  '/assets/icons/benoit-sigil.svg','/android-chrome-192x192.png','/android-chrome-512x512.png','/assets/media/sinjira-emblem.webp','/assets/media/sinjira-registre.webp','/assets/media/nova-logo.webp','/assets/media/sinjira-livre-1-cover-480.webp','/assets/media/fracture-card-back.webp',
  '/projets/sinjira/','/projets/sinjira/romans/','/projets/sinjira/romans/lire-demo.html','/projets/sinjira/registre/','/projets/sinjira/communaute/','/projets/sinjira/codex/','/projets/sinjira/monde-parallele/','/projets/sinjira/marche/','/projets/sinjira/jeux/fracture-du-reseau-mere/','/projets/projet-nova/'
];
// Seules les ressources statiques publiques connues peuvent entrer dans ce cache.
// Les requêtes privées, authentifiées et les reçus de publication restent réseau seul.
const PUBLIC_PATHS=new Set(CORE);
const PRIVATE_ROOTS=[
  '/app','/compte','/Admin','/admin','/histoire-de-vie','/supabase',
  '/api','/auth','/rest','/storage','/functions','/edge',
  '/account','/login','/logout'
];
function under(path,root){return path===root||path.startsWith(root+'/')}
function privatePath(path){
  return path==='/sw.js'||under(path,'/.well-known')||
    PRIVATE_ROOTS.some(root=>under(path,root))||
    under(path,'/projets/sinjira/codex/livre-i-delivery-contract.json');
}
function publicRequest(r,u){
  return PUBLIC_PATHS.has(u.pathname)&&!privatePath(u.pathname)&&
    !u.search&&!r.headers.has('Authorization')&&!r.headers.has('Cookie')&&
    (r.credentials==='omit'||r.credentials==='same-origin')&&
    (r.destination!=='document'||r.mode!=='no-cors');
}
function cacheableResponse(resp){
  const cc=String(resp.headers.get('Cache-Control')||'').toLowerCase();
  const vary=String(resp.headers.get('Vary')||'').toLowerCase();
  return resp.ok&&!resp.redirected&&!/(?:^|[,\s])(?:no-store|private)(?:$|[,\s=])/.test(cc)&&
    !resp.headers.has('Set-Cookie')&&!/(?:^|,\s*)(?:cookie|authorization)(?:,|$)/.test(vary);
}
// La précharge est anonyme et soumise aux MÊMES protections que les accès réseau.
// Ne jamais précharger une réponse personnalisée, un token ni un reçu de release.
function safePrecache(path){
  const u=new URL(path,location.origin);
  return path.startsWith('/')&&u.origin===location.origin&&u.pathname===path&&
    !u.search&&!u.hash&&!privatePath(u.pathname);
}
self.addEventListener('install',e=>e.waitUntil((async()=>{
  if(!CORE.every(safePrecache))throw Error('Chemin privé interdit dans le precache PWA');
  const store=await caches.open(CACHE);
  await Promise.all(CORE.map(async path=>{
    const request=new Request(new URL(path,location.origin).href,
      {cache:'no-store',credentials:'omit'});
    const response=await fetch(request);
    if(!cacheableResponse(response))throw Error('Réponse non publique interdite dans le precache');
    await store.put(request,response);
  }));
  await self.skipWaiting();
})()));

self.addEventListener('activate',e=>e.waitUntil(
  caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(CACHE_PREFIX)&&k!==CACHE)
    .map(k=>caches.delete(k)))).then(()=>self.clients.claim())
));
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;
  if(privatePath(u.pathname)||!publicRequest(r,u)){
    // Aucun cache, aucune réponse hors ligne de session, aucun fallback de reçu SHA.
    e.respondWith(fetch(new Request(r,{cache:'no-store'})));
    return;
  }
  if(r.destination==='document'||r.mode==='navigate'){
    // Une navigation peut être personnalisée par cookie, même sur une URL publique :
    // ne jamais conserver sa réponse. Le fallback ne contient que la précharge anonyme.
    e.respondWith(fetch(new Request(r,{cache:'no-store'}))
      .catch(()=>caches.match(r).then(x=>x||caches.match('/offline.html'))));
    return;
  }
  // Les ressources statiques destinées au cache sont toujours demandées sans
  // cookies de session, comme à l'installation du service worker.
  const anonymous=new Request(r,{cache:'no-store',credentials:'omit'});
  const liveAsset=/^\/assets\/(?:js|css)\//.test(u.pathname);
  if(liveAsset){
    e.respondWith(fetch(anonymous).then(resp=>{
      if(cacheableResponse(resp)){
        const store=caches.open(CACHE).then(c=>c.put(r,resp.clone()));
        e.waitUntil(store);
      }
      return resp;
    }).catch(()=>caches.match(r)));
    return;
  }
  e.respondWith(caches.match(r).then(cached=>cached||fetch(anonymous).then(resp=>{
    if(cacheableResponse(resp)){
      const store=caches.open(CACHE).then(c=>c.put(r,resp.clone()));
      e.waitUntil(store);
    }
    return resp;
  })));
});
