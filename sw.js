const CACHE='benoitcantin-v24-4-96-private-cache-guard';
const CORE=[
  '/','/offline.html','/manifest.webmanifest','/transparence-ia.html',
  '/assets/css/site.css','/assets/css/browser-compat-v24-4-22.css','/assets/css/ai-transparency.css','/assets/css/home-v24-4-12.css','/assets/css/v19-pro.css','/assets/css/v24-platform.css','/assets/css/v24-3-2-fixes.css','/assets/css/v24-3-3-fixes.css','/assets/css/fracture-engine.css','/assets/css/sinjira-assistant.css','/assets/css/sinjira-mobile-app-v24-4-94.css','/assets/css/sinjira-mobile-account-shell-v24-4-95.css',
  '/assets/js/site.js','/assets/js/sinjira-pwa-install.js','/assets/js/v24-3-1-runtime.js','/assets/js/v24-3-2-runtime.js','/assets/js/v24-3-3-runtime.js','/assets/js/v24-3-6-runtime.js','/assets/js/sinjira-fracture-lobby.js','/assets/js/sinjira-fracture-engine.js','/assets/js/sinjira-fracture-result.js','/assets/js/sinjira-assistant.js','/assets/js/sinjira-mobile-social-v24-4-94.js','/assets/js/sinjira-mobile-account-shell-v24-4-95.js',
  '/assets/icons/benoit-sigil.svg','/android-chrome-192x192.png','/android-chrome-512x512.png','/assets/media/sinjira-emblem.webp','/assets/media/sinjira-registre.webp','/assets/media/nova-logo.webp','/assets/media/sinjira-livre-1-cover-480.webp','/assets/media/fracture-card-back.webp',
  '/projets/sinjira/','/projets/sinjira/romans/','/projets/sinjira/romans/lire-demo.html','/projets/sinjira/registre/','/projets/sinjira/communaute/','/projets/sinjira/codex/','/projets/sinjira/monde-parallele/','/projets/sinjira/marche/','/projets/sinjira/jeux/fracture-du-reseau-mere/','/projets/projet-nova/'
];
// Ne jamais mettre en cache un chemin privé, même sans en-tête HTTP protecteur.
function isPrivatePath(pathname){
  const path=pathname.toLowerCase();
  if(path==='/administration'||path==='/administration.html')return true;
  return ['/app','/compte','/admin','/histoire-de-vie','/supabase','/api','/auth','/.netlify/functions'].some(prefix=>path===prefix||path.startsWith(prefix+'/'));
}
// Liste fermée : pas de cache opportuniste d'API, de JSON ou de PDF privé.
function isPublicCachePath(pathname){
  if(CORE.includes(pathname))return true;
  return /^\/(?:assets\/|projets\/)/.test(pathname)
    && /\.(?:css|js|mjs|png|jpe?g|gif|webp|avif|svg|ico|woff2?|ttf|otf|mp3|ogg|wav|mp4|webm|webmanifest)$/i.test(pathname);
}
function cacheableResponse(request,resp){
  if(!resp||!resp.ok||resp.status!==200||resp.redirected||['opaque','opaqueredirect','error'].includes(resp.type))return false;
  const url=new URL(request.url);
  if(url.origin!==location.origin||url.search||url.pathname.includes('%')||isPrivatePath(url.pathname)||!isPublicCachePath(url.pathname))return false;
  if(request.headers.has('authorization'))return false;
  if(resp.url){
    try{if(new URL(resp.url).origin!==url.origin)return false}
    catch(_error){return false}
  }
  const cc=String(resp.headers.get('Cache-Control')||'');
  const surrogate=String(resp.headers.get('Surrogate-Control')||'');
  if(/(?:^|,)\s*(?:no-store|no-cache|private)\b/i.test(cc)||/(?:^|,)\s*(?:no-store|no-cache|private)\b/i.test(surrogate))return false;
  if(/\bno-cache\b/i.test(String(resp.headers.get('Pragma')||'')))return false;
  const vary=String(resp.headers.get('Vary')||'').toLowerCase().split(',').map(x=>x.trim());
  if(vary.some(x=>x==='*'||x==='authorization'||x==='cookie'))return false;
  if(resp.headers.get('Set-Cookie'))return false;
  return true;
}
self.addEventListener('install',e=>e.waitUntil(
  caches.open(CACHE).then(c=>Promise.all(CORE.map(async path=>{
    const request=new Request(new URL(path,location.origin),{cache:'no-store'});
    const response=await fetch(request);
    // addAll() ignorait Cache-Control: private sur les pages précachées.
    if(cacheableResponse(request,response))await c.put(request,response);
  }))).then(()=>self.skipWaiting())
));
self.addEventListener('activate',e=>e.waitUntil(
  caches.keys().then(keys=>Promise.all(keys
    .filter(k=>k.startsWith('benoitcantin-')&&k!==CACHE)
    .map(k=>caches.delete(k)))).then(()=>self.clients.claim())
));
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;
  // Les chemins inconnus, URL encodées, requêtes avec token et API passent
  // seulement par le réseau, sans lecture ni écriture dans Cache Storage.
  if(isPrivatePath(u.pathname)||!isPublicCachePath(u.pathname)||u.search||
      u.pathname.includes('%')||r.headers.has('authorization')){
    e.respondWith(fetch(new Request(r,{cache:'no-store'})).catch(()=>caches.match('/offline.html')));
    return;
  }
  if(r.destination==='document'){
    e.respondWith(fetch(new Request(r,{cache:'no-store'})).then(resp=>{
      if(cacheableResponse(r,resp)){
        const cp=resp.clone();
        caches.open(CACHE).then(c=>c.put(r,cp));
      }
      return resp;
    }).catch(()=>caches.match(r).then(x=>x||caches.match('/offline.html'))));
    return;
  }
  // Le code JS/CSS doit rester network-first : une correction de sécurité ne
  // doit pas être masquée par une version ancienne en Cache Storage.
  const liveAsset=/\.(?:js|mjs|css)$/i.test(u.pathname);
  if(liveAsset){
    e.respondWith(fetch(new Request(r,{cache:'no-store'})).then(resp=>{
      if(cacheableResponse(r,resp))caches.open(CACHE).then(c=>c.put(r,resp.clone()));
      return resp;
    }).catch(()=>caches.match(r).then(x=>x||caches.match(u.pathname))));
    return;
  }
  e.respondWith(caches.match(r).then(cached=>cached||fetch(r).then(resp=>{
    if(cacheableResponse(r,resp))caches.open(CACHE).then(c=>c.put(r,resp.clone()));
    return resp;
  })).catch(()=>caches.match('/offline.html')));
});
