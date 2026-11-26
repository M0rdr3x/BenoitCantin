/* Cache hors ligne réservé aux ressources publiques (pas de réponses privées/dynamiques). */
const CACHE='benoitcantin-v24-4-95-public-18';
const CORE=[
  '/','/offline.html','/manifest.webmanifest','/transparence-ia.html',
  '/assets/css/site.css','/assets/css/error-pages-ux-v1.css','/assets/css/browser-compat-v24-4-22.css','/assets/css/ai-transparency.css','/assets/css/home-v24-4-12.css','/assets/css/home-sinjira-only-v1.css','/assets/css/site-ux-sinjira-v1.css','/assets/css/v19-pro.css','/assets/css/v24-platform.css','/assets/css/v24-3-2-fixes.css','/assets/css/v24-3-3-fixes.css','/assets/css/fracture-engine.css','/assets/css/sinjira-assistant.css','/assets/css/sinjira-mobile-app-v24-4-94.css','/assets/css/sinjira-mobile-account-shell-v24-4-95.css',
  '/assets/js/site.js','/assets/js/error-pages-ux-v1.js','/assets/js/sinjira-nav-boot-v2.js','/assets/js/sinjira-pwa-install.js','/assets/js/v24-3-1-runtime.js','/assets/js/v24-3-2-runtime.js','/assets/js/v24-3-3-runtime.js','/assets/js/v24-3-6-runtime.js','/assets/js/sinjira-fracture-lobby.js','/assets/js/sinjira-fracture-engine.js','/assets/js/sinjira-fracture-result.js','/assets/js/sinjira-assistant.js','/assets/js/sinjira-mobile-social-v24-4-94.js','/assets/js/sinjira-mobile-account-shell-v24-4-95.js',
  '/assets/icons/benoit-sigil.svg','/android-chrome-192x192.png','/android-chrome-512x512.png','/assets/icons/sinjira-favicon.png','/assets/icons/sinjira-officiel-20261120.png','/assets/media/sinjira-registre.webp','/assets/media/sinjira-livre-1-cover-480.webp','/assets/media/fracture-card-back.webp',
  '/assets/media/sinjira-registre-home-160.webp','/assets/media/sinjira-registre-home-336.webp','/assets/media/sinjira-jeux-home-160.webp','/assets/media/sinjira-jeux-home-336.webp','/assets/media/sinjira-communaute-home-160.webp','/assets/media/sinjira-communaute-home-336.webp',
  '/projets/sinjira/','/projets/sinjira/romans/','/projets/sinjira/romans/lire-demo.html','/projets/sinjira/registre/','/projets/sinjira/communaute/','/projets/sinjira/codex/','/projets/sinjira/monde-parallele/','/projets/sinjira/marche/','/projets/sinjira/jeux/fracture-du-reseau-mere/'
];
const PUBLIC_DOCUMENTS=new Set(CORE.filter(path=>path==='/'||path.endsWith('/')||path.endsWith('.html')));
const PUBLIC_ASSET=/^\/(?:assets\/(?:css\/[^/]+\.css|js\/[^/]+\.(?:js|mjs)|icons\/[^/]+\.(?:svg|png|ico|webp)|media\/[^/]+\.(?:png|jpe?g|webp|avif|svg))|android-chrome-\d+x\d+\.png|manifest\.webmanifest)$/i;
function cacheableResponse(resp){
  if(!resp||resp.status!==200||resp.type==='opaque'||resp.redirected)return false;
  const cc=String(resp.headers.get('Cache-Control')||'').toLowerCase();
  const vary=String(resp.headers.get('Vary')||'');
  return !/(?:^|[,\s])(?:private|no-store)(?:$|[,\s=])/.test(cc)&&!vary.split(',').some(value=>['*','cookie','authorization'].includes(value.trim().toLowerCase()))&&!resp.headers.has('Set-Cookie');
}
function publicAsset(path){return PUBLIC_ASSET.test(path)}
// Les réponses destinées au cache public ne doivent jamais dépendre d’une session.
function anonymousPublicRequest(request){return new Request(request,{credentials:'omit',cache:'no-store'})}
function matchPublicCache(request){return caches.open(CACHE).then(c=>c.match(request))}
function offlineDocument(){return matchPublicCache('/offline.html').then(response=>response||Response.error())}
function networkOnly(request,isDocument){
  return fetch(new Request(request,{cache:'no-store'})).catch(()=>isDocument?offlineDocument():Response.error());
}
// Le précache ne doit jamais contourner les critères de confidentialité du cache runtime.
async function installPublicCache(){
  try{
    const entries=await Promise.all(CORE.map(async path=>{
      const request=new Request(new URL(path,location.origin),{credentials:'omit',cache:'no-store',redirect:'error'});
      const response=await fetch(request);
      if(!cacheableResponse(response))throw new Error('Réponse de précache non admissible: '+path);
      return [request,response];
    }));
    const cache=await caches.open(CACHE);
    await Promise.all(entries.map(([request,response])=>cache.put(request,response)));
  }catch(error){
    await caches.delete(CACHE);
    throw error;
  }
  await self.skipWaiting();
}
self.addEventListener('install',e=>e.waitUntil(installPublicCache()));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('benoitcantin-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;
  const isDocument=r.mode==='navigate'||r.destination==='document';
  const privatePath=u.pathname==='/app'||u.pathname.startsWith('/app/')||u.pathname==='/compte'||u.pathname.startsWith('/compte/')||u.pathname==='/Admin'||u.pathname.startsWith('/Admin/')||u.pathname==='/admin'||u.pathname.startsWith('/admin/')||u.pathname==='/histoire-de-vie'||u.pathname.startsWith('/histoire-de-vie/')||u.pathname==='/supabase'||u.pathname.startsWith('/supabase/');
  const isPublicDocument=isDocument&&PUBLIC_DOCUMENTS.has(u.pathname);
  const isPublicAsset=!isDocument&&publicAsset(u.pathname);
  // Jamais de cache pour les chemins inconnus, les droits ou les PDF partiels.
  if(privatePath||r.headers.has('Authorization')||r.headers.has('Cookie')||r.headers.has('Range')||(!isPublicDocument&&!isPublicAsset)){
    e.respondWith(networkOnly(r,isDocument));return;
  }
  if(u.search){
    // Le cache-busting ?v=VERSION peut lire le fichier public précaché hors ligne,
    // mais la réponse réseau avec paramètres n'entre jamais dans CacheStorage.
    const versionedAsset=isPublicAsset&&/^\?v=[a-zA-Z0-9._-]+$/.test(u.search);
    e.respondWith(fetch(new Request(r,{cache:'no-store'})).catch(()=>
      versionedAsset?matchPublicCache(u.pathname).then(cached=>cached||Response.error()):
      isDocument?offlineDocument():Response.error()));return;
  }
  const publicRequest=anonymousPublicRequest(r);
  async function fetchAndCachePublic(){
    const resp=await fetch(publicRequest);
    if(cacheableResponse(resp)){
      try{await (await caches.open(CACHE)).put(publicRequest,resp.clone())}catch{/* Une erreur de stockage ne doit pas bloquer la réponse réseau. */}
    }
    return resp;
  }
  if(isDocument){
    e.respondWith(fetchAndCachePublic().catch(()=>matchPublicCache(publicRequest).then(x=>x||offlineDocument())));return;
  }
  const liveAsset=/\/assets\/(?:js|css)\//.test(u.pathname);
  if(liveAsset){
    e.respondWith(fetchAndCachePublic().catch(()=>matchPublicCache(publicRequest).then(x=>x||Response.error())));return;
  }
  e.respondWith(matchPublicCache(publicRequest).then(cached=>cached||fetchAndCachePublic()).catch(()=>Response.error()));
});
