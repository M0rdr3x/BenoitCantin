/* Cache hors ligne réservé aux ressources publiques (pas de réponses privées/dynamiques). */
const CACHE='benoitcantin-v24-4-95-public-8';
const CORE=[
  '/','/offline.html','/manifest.webmanifest','/transparence-ia.html',
  '/assets/css/site.css','/assets/css/browser-compat-v24-4-22.css','/assets/css/ai-transparency.css','/assets/css/home-v24-4-12.css','/assets/css/home-sinjira-only-v1.css','/assets/css/site-ux-sinjira-v1.css','/assets/css/v19-pro.css','/assets/css/v24-platform.css','/assets/css/v24-3-2-fixes.css','/assets/css/v24-3-3-fixes.css','/assets/css/fracture-engine.css','/assets/css/sinjira-assistant.css','/assets/css/sinjira-mobile-app-v24-4-94.css','/assets/css/sinjira-mobile-account-shell-v24-4-95.css',
  '/assets/js/site.js','/assets/js/sinjira-pwa-install.js','/assets/js/v24-3-1-runtime.js','/assets/js/v24-3-2-runtime.js','/assets/js/v24-3-3-runtime.js','/assets/js/v24-3-6-runtime.js','/assets/js/sinjira-fracture-lobby.js','/assets/js/sinjira-fracture-engine.js','/assets/js/sinjira-fracture-result.js','/assets/js/sinjira-assistant.js','/assets/js/sinjira-mobile-social-v24-4-94.js','/assets/js/sinjira-mobile-account-shell-v24-4-95.js',
  '/assets/icons/benoit-sigil.svg','/android-chrome-192x192.png','/android-chrome-512x512.png','/assets/icons/sinjira-favicon.png','/assets/icons/sinjira-officiel-20261120.png','/assets/media/sinjira-registre.webp','/assets/media/sinjira-livre-1-cover-480.webp','/assets/media/fracture-card-back.webp',
  '/projets/sinjira/','/projets/sinjira/romans/','/projets/sinjira/romans/lire-demo.html','/projets/sinjira/registre/','/projets/sinjira/communaute/','/projets/sinjira/codex/','/projets/sinjira/monde-parallele/','/projets/sinjira/marche/','/projets/sinjira/jeux/fracture-du-reseau-mere/'
];
const PUBLIC_DOCUMENTS=new Set(CORE.filter(path=>path==='/'||path.endsWith('/')||path.endsWith('.html')));
const PUBLIC_ASSET=/^\/(?:assets\/(?:css\/[^/]+\.css|js\/[^/]+\.(?:js|mjs)|icons\/[^/]+\.(?:svg|png|ico|webp)|media\/[^/]+\.(?:png|jpe?g|webp|avif|svg))|android-chrome-\d+x\d+\.png|manifest\.webmanifest)$/i;
function cacheableResponse(resp){
  // Seules les réponses anonymes, intactes et explicitement stockables dans
  // un cache navigateur sont admises. Les en-têtes Vary sensibles interdisent
  // une réutilisation intersession, même pour une URL normalement publique.
  if(!resp||resp.status!==200||!['basic','default'].includes(resp.type)||resp.redirected)return false;
  const cc=String(resp.headers.get('Cache-Control')||'').toLowerCase();
  if(/(?:^|[,\s])(?:private|no-store|no-cache)(?:$|[,\s;=])/.test(cc))return false;
  if(/(?:^|[,\s])no-cache(?:$|[,\s])/.test(String(resp.headers.get('Pragma')||'').toLowerCase()))return false;
  const vary=String(resp.headers.get('Vary')||'');
  // Allowlist stricte : tout autre Vary pourrait dépendre d'une identité ou
  // d'un droit utilisateur (X-Account-ID, Origin, Authorization, Cookie...).
  const harmlessVary=['accept','accept-encoding','accept-language'];
  if(vary.split(',').some(field=>field.trim()&&!harmlessVary.includes(field.trim().toLowerCase())))return false;
  return !resp.headers.has('Set-Cookie');
}
function publicAsset(path){return PUBLIC_ASSET.test(path)}
function offlineDocument(){return caches.match('/offline.html')}
function networkOnly(request,isDocument){
  return fetch(new Request(request,{cache:'no-store'})).catch(()=>isDocument?offlineDocument():Response.error());
}
async function precachePublicCore(){
  const cache=await caches.open(CACHE);
  // Cache.addAll() ne consulte pas cacheableResponse et pourrait conserver
  // une page personnalisée. Précharger sans cookie ni authentification puis
  // examiner CHAQUE réponse avant toute écriture dans CacheStorage.
  await Promise.all(CORE.map(async path=>{
    const url=new URL(path,location.origin);
    if(url.origin!==location.origin||url.search||url.hash)throw new Error('Ressource hors origine du précache');
    const publicRequest=new Request(url.href,{credentials:'omit',cache:'no-store',redirect:'error'});
    const response=await fetch(publicRequest);
    if(!cacheableResponse(response))throw new Error('Réponse non publique refusée au précache');
    await cache.put(new Request(url.href,{credentials:'omit'}),response);
  }));
}
self.addEventListener('install',e=>e.waitUntil(precachePublicCore().then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('benoitcantin-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;
  const isDocument=r.mode==='navigate'||r.destination==='document';
  const privatePath=u.pathname==='/app'||u.pathname.startsWith('/app/')||u.pathname==='/compte'||u.pathname.startsWith('/compte/')||u.pathname==='/Admin'||u.pathname.startsWith('/Admin/')||u.pathname==='/admin'||u.pathname.startsWith('/admin/')||u.pathname==='/histoire-de-vie'||u.pathname.startsWith('/histoire-de-vie/')||u.pathname==='/supabase'||u.pathname.startsWith('/supabase/');
  const isPublicDocument=isDocument&&PUBLIC_DOCUMENTS.has(u.pathname);
  const isPublicAsset=!isDocument&&publicAsset(u.pathname);
  // Jamais de cache pour les chemins inconnus, les droits ou les PDF partiels.
  if(privatePath||r.headers.has('Authorization')||r.headers.has('Cookie')||r.headers.has('X-API-Key')||r.headers.has('Range')||(!isPublicDocument&&!isPublicAsset)){
    e.respondWith(networkOnly(r,isDocument));return;
  }
  if(u.search){
    // Le cache-busting ?v=VERSION peut lire le fichier public précaché hors ligne,
    // mais la réponse réseau avec paramètres n'entre jamais dans CacheStorage.
    const versionedAsset=isPublicAsset&&/^\?v=[a-zA-Z0-9._-]+$/.test(u.search);
    e.respondWith(fetch(new Request(r,{cache:'no-store',credentials:isPublicAsset?'omit':r.credentials})).catch(()=>
      versionedAsset?caches.match(u.pathname).then(cached=>cached||Response.error()):
      isDocument?offlineDocument():Response.error()));return;
  }
  if(isDocument){
    // Ne jamais mémoriser le rendu d'une navigation : le réseau peut avoir
    // reçu des cookies de session, même si Cookie n'est pas lisible par le SW.
    // Hors ligne, seules les copies publiques anonymes du précache sont lues.
    e.respondWith(fetch(new Request(r,{cache:'no-store'}))
      .catch(()=>caches.match(r).then(x=>x||offlineDocument())));return;
  }
  const liveAsset=/\/assets\/(?:js|css)\//.test(u.pathname);
  // Ressources statiques uniquement : toute réponse admise en cache est
  // obtenue sans cookies de session, y compris pour les CSS/JS actualisés.
  const anonymousRequest=new Request(r,{cache:'no-store',credentials:'omit'});
  if(liveAsset){
    e.respondWith(fetch(anonymousRequest).then(resp=>{
      if(cacheableResponse(resp))caches.open(CACHE).then(c=>c.put(r,resp.clone()));
      return resp;
    }).catch(()=>caches.match(r).then(x=>x||caches.match(u.pathname))));return;
  }
  e.respondWith(caches.match(r).then(cached=>cached||fetch(anonymousRequest).then(resp=>{
    if(cacheableResponse(resp))caches.open(CACHE).then(c=>c.put(r,resp.clone()));
    return resp;
  })));
});
