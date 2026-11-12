/* PWA publique SINJIRA : aucune donnée privée ni réponse authentifiée en CacheStorage. */
const CACHE='benoitcantin-v24-4-95-public-4';
const CACHE_FAMILY='benoitcantin-v24-4-95-public-';
const CORE=[
  '/','/offline.html','/manifest.webmanifest','/transparence-ia.html',
  '/assets/css/site.css','/assets/css/browser-compat-v24-4-22.css','/assets/css/ai-transparency.css','/assets/css/home-v24-4-12.css','/assets/css/v19-pro.css','/assets/css/v24-platform.css','/assets/css/v24-3-2-fixes.css','/assets/css/v24-3-3-fixes.css','/assets/css/fracture-engine.css','/assets/css/sinjira-assistant.css','/assets/css/sinjira-mobile-app-v24-4-94.css','/assets/css/sinjira-mobile-account-shell-v24-4-95.css',
  '/assets/js/site.js','/assets/js/sinjira-pwa-install.js','/assets/js/v24-3-1-runtime.js','/assets/js/v24-3-2-runtime.js','/assets/js/v24-3-3-runtime.js','/assets/js/v24-3-6-runtime.js','/assets/js/sinjira-fracture-lobby.js','/assets/js/sinjira-fracture-engine.js','/assets/js/sinjira-fracture-result.js','/assets/js/sinjira-assistant.js','/assets/js/sinjira-mobile-social-v24-4-94.js','/assets/js/sinjira-mobile-account-shell-v24-4-95.js',
  '/assets/icons/benoit-sigil.svg','/android-chrome-192x192.png','/android-chrome-512x512.png','/assets/media/sinjira-emblem.webp','/assets/media/sinjira-registre.webp','/assets/media/nova-logo.webp','/assets/media/sinjira-livre-1-cover-480.webp','/assets/media/fracture-card-back.webp',
  '/projets/sinjira/','/projets/sinjira/romans/','/projets/sinjira/romans/lire-demo.html','/projets/sinjira/registre/','/projets/sinjira/communaute/','/projets/sinjira/codex/','/projets/sinjira/monde-parallele/','/projets/sinjira/marche/','/projets/sinjira/jeux/fracture-du-reseau-mere/','/projets/projet-nova/'
];
const PRECACHE=new Set(CORE);
const PUBLIC_ASSET=/^\/assets\/(?:css|js|icons|media)\/[a-z0-9][a-z0-9._/-]*$/i;

function privatePath(path){
  // Toute l'administration, les données personnelles et l'espace applicatif restent réseau seul.
  return path==='/app'||path.startsWith('/app/')||
    path==='/compte'||path.startsWith('/compte/')||
    path==='/Admin'||path.startsWith('/Admin/')||
    path==='/admin'||path.startsWith('/admin/')||
    path==='/administration'||path==='/administration.html'||
    path==='/histoire-de-vie'||path.startsWith('/histoire-de-vie/')||
    path==='/supabase'||path.startsWith('/supabase/');
}
function permittedPublicPath(path){
  return !privatePath(path) && (PRECACHE.has(path)||PUBLIC_ASSET.test(path));
}
function expectedContentType(path, contentType){
  const type=String(contentType||'').split(';',1)[0].trim().toLowerCase();
  if(!type)return false; // Ne pas mémoriser une réponse non qualifiée.
  if(path.endsWith('/')||path==='/'||path.endsWith('.html'))return type==='text/html';
  if(path.endsWith('.js'))return /^(?:text|application)\/(?:javascript|x-javascript|ecmascript)$/.test(type);
  if(path.endsWith('.css'))return type==='text/css';
  if(path.endsWith('.webmanifest'))return type==='application/manifest+json'||type==='application/json';
  if(path.endsWith('.png'))return type==='image/png';
  if(path.endsWith('.webp'))return type==='image/webp';
  if(path.endsWith('.svg'))return type==='image/svg+xml';
  if(path.endsWith('.jpg')||path.endsWith('.jpeg'))return type==='image/jpeg';
  if(path.endsWith('.gif'))return type==='image/gif';
  return false;
}
function cacheableResponse(response,url){
  if(!response||response.status!==200||response.redirected||response.type==='opaque'||response.type==='opaqueredirect')return false;
  // Aucun redirect, aucun contenu d'un autre domaine et aucune réponse d'API déguisée.
  if(!response.url)return false;
  const final=new URL(response.url,location.origin);
  if(final.origin!==location.origin||final.pathname!==url.pathname||final.search)return false;
  const cc=String(response.headers.get('Cache-Control')||'').toLowerCase();
  if(/(?:^|[,\s])(?:private|no-store|no-cache)(?:[,\s=]|$)/.test(cc))return false;
  const vary=String(response.headers.get('Vary')||'').toLowerCase();
  if(/(?:^|,\s*)(?:\*|cookie|authorization)(?:\s*,|\s*$)/.test(vary))return false;
  if(response.headers.has('Set-Cookie'))return false;
  return expectedContentType(url.pathname,response.headers.get('Content-Type'));
}
function publicRequest(path){
  // credentials: omit empêche la capture d'un contenu variant selon la session.
  return new Request(new URL(path,location.origin).href,{credentials:'omit',redirect:'error',cache:'no-store'});
}
async function loadPublic(path){
  const response=await fetch(publicRequest(path));
  if(!cacheableResponse(response,new URL(path,location.origin)))throw new Error('Réponse publique non admissible au précache: '+path);
  return response;
}
self.addEventListener('install',event=>{
  event.waitUntil((async()=>{
    try{
      const cache=await caches.open(CACHE);
      for(const path of CORE){
        const response=await loadPublic(path);
        await cache.put(path,response);
      }
      await self.skipWaiting();
    }catch(error){
      // Fail-closed: aucun cache partiellement installé.
      await caches.delete(CACHE);
      throw error;
    }
  })());
});
self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(key=>key.startsWith(CACHE_FAMILY)&&key!==CACHE).map(key=>caches.delete(key)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch',event=>{
  const request=event.request;
  const url=new URL(request.url);
  if(url.origin!==location.origin||request.method!=='GET')return;
  const path=url.pathname;
  if(privatePath(path)){
    // Aucun accès à CacheStorage pour /app, /compte, /admin, /supabase, etc.
    event.respondWith(fetch(new Request(request,{cache:'no-store'})));
    return;
  }
  if(request.headers.has('Authorization')||request.headers.has('Range')||request.cache==='no-store')return;
  // Les requêtes avec paramètres, les chemins inconnus, les API et les documents sensibles
  // ne sont jamais capturés par le cache public, même si le serveur répond HTTP 200.
  if(url.search||!permittedPublicPath(path)){
    if(request.mode==='navigate'){
      event.respondWith(fetch(new Request(request,{cache:'no-store'})).catch(async()=> (await caches.open(CACHE)).match('/offline.html')));
    }
    return;
  }
  event.respondWith((async()=>{
    try{
      const response=await fetch(publicRequest(path));
      if(cacheableResponse(response,url)){
        try{await (await caches.open(CACHE)).put(path,response.clone());}catch(_error){/* stockage facultatif */}
      }
      return response;
    }catch(error){
      const ownedCache=await caches.open(CACHE);
      const fallback=await ownedCache.match(path);
      if(fallback)return fallback;
      if(request.mode==='navigate'){
        const offline=await ownedCache.match('/offline.html');
        if(offline)return offline;
      }
      throw error;
    }
  })());
});