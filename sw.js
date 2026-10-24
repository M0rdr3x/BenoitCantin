const CACHE='benoitcantin-v24-4-95-public-12-allowlisted';
const CORE=[
  '/','/offline.html','/manifest.webmanifest','/a-propos.html','/contact.html','/transparence-ia.html',
  '/assistant.html','/confidentialite.html','/gouvernance-vie-privee.html','/avis-legal.html',
  '/assets/css/site.css','/assets/css/browser-compat-v24-4-22.css','/assets/css/ai-transparency.css','/assets/css/home-v24-4-12.css','/assets/css/v19-pro.css','/assets/css/v24-platform.css','/assets/css/v24-3-2-fixes.css','/assets/css/v24-3-3-fixes.css','/assets/css/fracture-engine.css','/assets/css/sinjira-assistant.css','/assets/css/sinjira-mobile-app-v24-4-94.css','/assets/css/sinjira-mobile-account-shell-v24-4-95.css',
  '/assets/js/site.js','/assets/js/ai-transparency.js','/assets/js/sinjira-pwa-install.js','/assets/js/v24-3-1-runtime.js','/assets/js/v24-3-2-runtime.js','/assets/js/v24-3-3-runtime.js','/assets/js/v24-3-6-runtime.js','/assets/js/sinjira-fracture-lobby.js','/assets/js/sinjira-fracture-engine.js','/assets/js/sinjira-fracture-result.js','/assets/js/sinjira-assistant.js','/assets/js/sinjira-mobile-social-v24-4-94.js','/assets/js/sinjira-mobile-account-shell-v24-4-95.js',
  '/assets/media/nova-boussole-electorale.webp','/assets/media/nova-boussole-electorale-v2.webp',
  '/projets/projet-nova/script.js','/projets/projet-nova/styles.css',
  '/projets/projet-nova/assets/boussole-electorale.js','/projets/projet-nova/assets/boussole-electorale.css',
  '/projets/projet-nova/data/boussole-electorale-v2.json','/projets/projet-nova/data/boussole-partis-2026.json','/projets/projet-nova/data/boussole-sources-partis-2026.json','/projets/projet-nova/data/boussole-preuves-2026.json',
  '/assets/icons/benoit-sigil.svg','/android-chrome-192x192.png','/android-chrome-512x512.png','/assets/media/sinjira-emblem.webp','/assets/media/sinjira-registre.webp','/assets/media/nova-logo.webp','/assets/media/sinjira-livre-1-cover-480.webp','/assets/media/fracture-card-back.webp',
  '/projets/sinjira/','/projets/sinjira/romans/','/projets/sinjira/romans/lire-demo.html','/projets/sinjira/jeux/','/projets/sinjira/registre/','/projets/sinjira/communaute/','/projets/sinjira/codex/','/projets/sinjira/monde-parallele/','/projets/sinjira/marche/','/projets/sinjira/jeux/fracture-du-reseau-mere/','/projets/projet-nova/','/projets/projet-nova/boussole-electorale.html'
];
function cacheableResponse(resp){const cc=String(resp.headers.get('Cache-Control')||'').toLowerCase();const vary=String(resp.headers.get('Vary')||'').toLowerCase();return resp.ok&&cc.indexOf('no-store')===-1&&cc.indexOf('private')===-1&&cc.indexOf('no-cache')===-1&&!/(?:^|,)\s*(?:cookie|authorization|\*)\s*(?:,|$)/.test(vary)}
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;
  const privatePath=u.pathname==='/app'||u.pathname.startsWith('/app/')||u.pathname==='/compte'||u.pathname.startsWith('/compte/')||u.pathname==='/Admin'||u.pathname.startsWith('/Admin/')||u.pathname==='/admin'||u.pathname.startsWith('/admin/')||u.pathname==='/histoire-de-vie'||u.pathname.startsWith('/histoire-de-vie/')||u.pathname==='/supabase'||u.pathname.startsWith('/supabase/');
  const releaseMarker=u.pathname==='/.well-known/release.json';
  if(releaseMarker){e.respondWith(fetch(new Request(r,{cache:'no-store'})));return}
  if(privatePath){e.respondWith(fetch(new Request(r,{cache:'no-store'})).catch(()=>caches.match('/offline.html')));return}
  // Ne jamais écrire en Cache Storage des appels API, de session, de paiement
  // ou des réponses JSON dynamiques non explicitement précachées comme publiques.
  const sensitiveSegments=/(?:^|\/)(?:api|auth|oauth|graphql|functions|session|sessions|token|tokens|password|billing|checkout|payments|webhook|webhooks|\.netlify|\.vercel|\.well-known|_next|_nuxt)(?:\/|$)/i.test(u.pathname);
  const sensitiveQuery=[...u.searchParams.keys()].some(key=>/^(?:access_token|refresh_token|token|code|state|session|auth|api_key|key|jwt|signature|secret|user_id|download)$/i.test(key));
  const sensitiveHeaders=Boolean(r.headers.get('Authorization')||r.headers.get('X-Api-Key'));
  const unknownJSON=/\.json$/i.test(u.pathname)&&CORE.indexOf(u.pathname)===-1;
  const sensitiveRuntimePath=sensitiveSegments||sensitiveQuery||sensitiveHeaders||unknownJSON;
  if(sensitiveRuntimePath){e.respondWith(fetch(new Request(r,{cache:'no-store'})));return}

  // Liste positive : aucune future URL HTML, API ou réponse dynamique ne doit
  // entrer implicitement dans Cache Storage. Seules les ressources CORE sont
  // connues publiques ; seul ?v= peut varier sur un script/CSS de CORE.
  const publicCachePath=CORE.indexOf(u.pathname)!==-1;
  const versionOnly=u.searchParams.has('v')&&[...u.searchParams.keys()].length===1&&/^[A-Za-z0-9._-]{1,64}$/.test(u.searchParams.get('v')||'');
  const versionableAsset=/(?:^|\\/)assets\\/(?:js|css)\\//.test(u.pathname)||u.pathname==='/projets/projet-nova/script.js'||u.pathname==='/projets/projet-nova/styles.css';
  const publicCacheRequest=publicCachePath&&(!u.search||(versionOnly&&versionableAsset));
  if(!publicCacheRequest){e.respondWith(fetch(new Request(r,{cache:'no-store'})));return}

  if(r.destination==='document'){
    e.respondWith(fetch(new Request(r,{cache:'no-store'})).then(resp=>{if(cacheableResponse(resp)){const cp=resp.clone();caches.open(CACHE).then(c=>c.put(r,cp))}return resp}).catch(()=>caches.match(r).then(x=>x||caches.match('/offline.html'))));return;
  }
  const liveAsset=/\/assets\/(?:js|css)\//.test(u.pathname)||u.pathname==='/projets/projet-nova/script.js'||u.pathname==='/projets/projet-nova/styles.css';
  if(liveAsset){e.respondWith(fetch(new Request(r,{cache:'no-store'})).then(resp=>{if(cacheableResponse(resp))caches.open(CACHE).then(c=>c.put(r,resp.clone()));return resp}).catch(()=>caches.match(r).then(x=>x||caches.match(u.pathname))));return}
  e.respondWith(caches.match(r).then(cached=>cached||fetch(r).then(resp=>{if(cacheableResponse(resp)&&u.pathname.indexOf('/documents/')===-1)caches.open(CACHE).then(c=>c.put(r,resp.clone()));return resp})));
});