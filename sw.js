const CACHE='benoitcantin-v24-4-95-public-10';
const CACHE_PREFIX='benoitcantin-v24-4-95-public-';
const CORE=[
  '/','/offline.html','/manifest.webmanifest','/transparence-ia.html',
  '/assets/css/site.css','/assets/css/browser-compat-v24-4-22.css','/assets/css/ai-transparency.css','/assets/css/home-v24-4-12.css','/assets/css/v19-pro.css','/assets/css/v24-platform.css','/assets/css/v24-3-2-fixes.css','/assets/css/v24-3-3-fixes.css','/assets/css/fracture-engine.css','/assets/css/sinjira-assistant.css','/assets/css/sinjira-mobile-app-v24-4-94.css','/assets/css/sinjira-mobile-account-shell-v24-4-95.css',
  '/assets/js/site.js','/assets/js/sinjira-pwa-install.js','/assets/js/v24-3-1-runtime.js','/assets/js/v24-3-2-runtime.js','/assets/js/v24-3-3-runtime.js','/assets/js/v24-3-6-runtime.js','/assets/js/sinjira-fracture-lobby.js','/assets/js/sinjira-fracture-engine.js','/assets/js/sinjira-fracture-result.js','/assets/js/sinjira-assistant.js','/assets/js/sinjira-mobile-social-v24-4-94.js','/assets/js/sinjira-mobile-account-shell-v24-4-95.js',
  '/assets/icons/benoit-sigil.svg','/android-chrome-192x192.png','/android-chrome-512x512.png','/assets/media/sinjira-emblem.webp','/assets/media/sinjira-registre.webp','/assets/media/nova-logo.webp','/assets/media/sinjira-livre-1-cover-480.webp','/assets/media/fracture-card-back.webp',
  '/projets/sinjira/','/projets/sinjira/romans/','/projets/sinjira/jeux/','/projets/sinjira/logiciels/','/projets/sinjira/romans/lire-demo.html','/projets/sinjira/registre/','/projets/sinjira/communaute/','/projets/sinjira/codex/','/projets/sinjira/monde-parallele/','/projets/sinjira/marche/','/projets/sinjira/jeux/fracture-du-reseau-mere/','/projets/projet-nova/'
];
// Seules les ressources statiques publiques connues peuvent entrer dans ce cache.
// Les requêtes privées, authentifiées et les reçus de publication restent réseau seul.
const PUBLIC_PATHS=new Set(CORE);
// Les questionnaires et leurs données publiques ne doivent pas être
// servis hors ligne : exige toujours la version réseau, jamais un cache PWA.
const NOVA_SURVEY_NETWORK_ONLY=new Set([
  '/projets/projet-nova/consultation-40.html',
  '/projets/projet-nova/sondage.html',
  '/projets/projet-nova/assets/consultation-40.js',
  '/projets/projet-nova/assets/sondage.js',
  '/projets/projet-nova/assets/sondage.css',
  '/projets/projet-nova/data/consultation-40-v1.json',
  '/projets/projet-nova/data/sondage-questions-v1.json'
  ,'/projets/projet-nova/resultats-sondages.html'
  ,'/projets/projet-nova/assets/resultats-sondages.js'
  ,'/projets/projet-nova/data/resultats-sondages-publics-v1.json'
]);
function surveyNetworkOnly(path){return NOVA_SURVEY_NETWORK_ONLY.has(path)}
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
  return PUBLIC_PATHS.has(u.pathname)&&!privatePath(u.pathname)&&!surveyNetworkOnly(u.pathname)&&
    !u.search&&!r.headers.has('Authorization')&&!r.headers.has('Cookie')&&
    !r.headers.has('Range')&&!r.headers.has('If-Range')&&
    (r.credentials==='omit'||r.credentials==='same-origin')&&
    (r.destination!=='document'||r.mode!=='no-cors');
}
// Les 200 HTML de fallback (404 réécrits en accueil) ne doivent jamais
// devenir des JS/CSS/images dans le cache public hors ligne.
function expectedMime(path){
  if(path==='/'||path.endsWith('/')||path.endsWith('.html'))return ['text/html'];
  if(path.endsWith('.js'))return ['application/javascript','text/javascript','application/x-javascript'];
  if(path.endsWith('.css'))return ['text/css'];
  if(path.endsWith('.svg'))return ['image/svg+xml'];
  if(path.endsWith('.webp'))return ['image/webp'];
  if(path.endsWith('.png'))return ['image/png'];
  if(path.endsWith('.webmanifest'))return ['application/manifest+json','application/json'];
  return [];
}
function cacheableResponse(resp,path){
  const mime=String(resp.headers.get('Content-Type')||'').split(';',1)[0].trim().toLowerCase();
  if(!expectedMime(path).includes(mime))return false;
  // Cache API ne revalide pas automatiquement les copies hors ligne :
  // refuser aussi no-cache / must-revalidate, en plus des réponses privées.
  const directives=String(resp.headers.get('Cache-Control')||'').toLowerCase()
    .split(',').map(token=>token.trim().split('=')[0].trim());
  const forbid=['no-store','private','no-cache','must-revalidate','proxy-revalidate'];
  // Cache API conserve les réponses sans appliquer les règles HTTP 1.0.
  // Pragma: no-cache requiert le réseau même sans Cache-Control explicite.
  const pragma=String(resp.headers.get('Pragma')||'').toLowerCase()
    .split(',').some(token=>token.trim()==='no-cache');
  // Politique de réutilisation fermée : Accept-Encoding est la seule
  // variation technique tolérée. Langue, origine, User-Agent et en-têtes
  // inconnus peuvent faire dépendre la réponse du contexte de l'utilisateur.
  const vary=String(resp.headers.get('Vary')||'').toLowerCase()
    .split(',').map(token=>token.trim()).filter(Boolean);
  // HTTP 206 est un fragment, jamais un objet public complet à conserver.
  return resp.status===200&&!resp.redirected&&!pragma&&
    !directives.some(directive=>forbid.includes(directive))&&
    !resp.headers.has('Set-Cookie')&&
    vary.every(token=>token==='accept-encoding');
}
// La précharge est anonyme et soumise aux MÊMES protections que les accès réseau.
// Ne jamais précharger une réponse personnalisée, un token ni un reçu de release.
function safePrecache(path){
  const u=new URL(path,location.origin);
  return path.startsWith('/')&&u.origin===location.origin&&u.pathname===path&&
    !u.search&&!u.hash&&!privatePath(u.pathname)&&!surveyNetworkOnly(u.pathname);
}
self.addEventListener('install',e=>e.waitUntil((async()=>{
  if(!CORE.every(safePrecache))throw Error('Chemin privé interdit dans le precache PWA');
  const store=await caches.open(CACHE);
  // Attendre toutes les opérations, y compris celles qui échouent : sinon
  // une écriture encore en vol pourrait recréer un cache après sa suppression.
  const results=await Promise.allSettled(CORE.map(async path=>{
    const request=new Request(new URL(path,location.origin).href,
      {cache:'no-store',credentials:'omit'});
    const response=await fetch(request);
    if(!cacheableResponse(response,path))throw Error('Réponse non publique interdite dans le precache');
    await store.put(request,response);
  }));
  const failed=results.find(result=>result.status==='rejected');
  if(failed){
    // Aucun demi-precache ne doit survivre à une installation refusée.
    await caches.delete(CACHE);
    throw failed.reason;
  }
  await self.skipWaiting();
})()));

self.addEventListener('activate',e=>e.waitUntil(
  caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(CACHE_PREFIX)&&k!==CACHE)
    .map(k=>caches.delete(k)))).then(()=>self.clients.claim())
));
// Cache Storage.match() global fouille TOUS les caches de ce domaine.
// L'accès hors ligne doit rester strictement dans notre cache PUBLIC courant.
function matchPublicCache(request){
  return caches.open(CACHE).then(store=>store.match(request));
}
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;
  if(privatePath(u.pathname)||surveyNetworkOnly(u.pathname)||!publicRequest(r,u)){
    // Aucun cache, aucune réponse hors ligne de session, aucun fallback de reçu SHA.
    e.respondWith(fetch(new Request(r,{cache:'no-store'})));
    return;
  }
  if(r.destination==='document'||r.mode==='navigate'){
    // Une navigation peut être personnalisée par cookie, même sur une URL publique :
    // ne jamais conserver sa réponse. Le fallback ne contient que la précharge anonyme.
    e.respondWith(fetch(new Request(r,{cache:'no-store'}))
      .catch(()=>matchPublicCache(r).then(x=>x||matchPublicCache('/offline.html'))));
    return;
  }
  // Les ressources statiques destinées au cache sont toujours demandées sans
  // cookies de session, comme à l'installation du service worker.
  const anonymous=new Request(r,{cache:'no-store',credentials:'omit'});
  const liveAsset=/^\/assets\/(?:js|css)\//.test(u.pathname);
  if(liveAsset){
    e.respondWith(fetch(anonymous).then(resp=>{
      if(cacheableResponse(resp,u.pathname)){
        const store=caches.open(CACHE).then(c=>c.put(r,resp.clone()));
        e.waitUntil(store);
      }
      return resp;
    }).catch(()=>matchPublicCache(r)));
    return;
  }
  e.respondWith(matchPublicCache(r).then(cached=>cached||fetch(anonymous).then(resp=>{
    if(cacheableResponse(resp,u.pathname)){
      const store=caches.open(CACHE).then(c=>c.put(r,resp.clone()));
      e.waitUntil(store);
    }
    return resp;
  })));
});
