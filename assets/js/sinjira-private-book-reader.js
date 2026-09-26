import {getSupabase,requireUser} from './sinjira-supabase.js';

const DELIVERY_FUNCTION='get-private-novel-url';
const params=new URLSearchParams(location.search);
const novelSlug=String(params.get('novel')||document.body.dataset.novelSlug||'la-cendre-du-jugement').trim();
const storageKey=`sinjira-reader-full-${novelSlug}-v1`;
const frame=document.querySelector('[data-private-pdf-reader]');
const status=document.querySelector('[data-private-reader-status]');
const input=document.querySelector('[data-private-reader-page]');
const progress=document.querySelector('[data-private-reader-progress]');
const bar=document.querySelector('[data-private-reader-progress-bar]');
const resume=document.querySelector('[data-private-reader-resume]');
const titleNode=document.querySelector('[data-private-reader-title]');
const metaNode=document.querySelector('[data-private-reader-meta]');
let totalPages=Math.max(1,Number(document.body.dataset.readerTotalPages)||1);
let current=Math.min(totalPages,Math.max(1,Number(localStorage.getItem(storageKey))||1));
let signedUrl='';
let refreshAt=0;
let accessPromise=null;

function setStatus(message,type='info'){
  if(!status)return;
  status.hidden=false;
  status.dataset.statusType=type;
  status.textContent=message;
}

function updateProgress(){
  current=Math.min(totalPages,Math.max(1,current));
  const percent=Math.round((current/totalPages)*100);
  if(input){input.max=String(totalPages);input.value=String(current);}
  if(progress){progress.value=current;progress.max=totalPages;progress.textContent=`${current} sur ${totalPages}`;}
  if(bar)bar.style.width=`${percent}%`;
  if(resume)resume.textContent=`Page ${current} · ${percent} %`;
}

function applyMetadata(data){
  if(data?.title&&titleNode)titleNode.textContent=String(data.title);
  const pages=Number(data?.total_pages);
  if(Number.isFinite(pages)&&pages>0)totalPages=Math.floor(pages);
  if(metaNode)metaNode.textContent=`Édition intégrale · accès privé du compte · ${totalPages} page${totalPages===1?'':'s'}`;
  document.title=`Lecture intégrale privée | ${String(data?.title||'SINJIRA™')}`;
  updateProgress();
}

function savePage(){
  localStorage.setItem(storageKey,String(current));
  updateProgress();
  if(resume)resume.textContent=`Page ${current} sauvegardée sur cet appareil.`;
}

async function requireReaderUser(){
  return requireUser(`/compte/connexion.html?next=${encodeURIComponent(location.pathname+location.search)}`);
}

async function invokeDelivery(mode){
  await requireReaderUser();
  const {data,error}=await getSupabase().functions.invoke(DELIVERY_FUNCTION,{body:{novel_slug:novelSlug,mode}});
  if(error||!data?.ok||!data?.url)throw new Error(data?.error||'Impossible de préparer l’accès privé.');
  applyMetadata(data);
  return data;
}

async function requestReadingUrl(force=false){
  if(!force&&signedUrl&&Date.now()<refreshAt)return signedUrl;
  if(accessPromise)return accessPromise;
  accessPromise=(async()=>{
    const data=await invokeDelivery('read');
    const ttl=Math.max(60,Math.min(300,Number(data.expires_in)||300));
    signedUrl=String(data.url);
    refreshAt=Date.now()+Math.max(30000,(ttl-45)*1000);
    return signedUrl;
  })();
  try{return await accessPromise;}finally{accessPromise=null;}
}

async function render(forceRefresh=false){
  if(!frame)return;
  setStatus('Préparation de la lecture sécurisée…','info');
  try{
    const url=await requestReadingUrl(forceRefresh);
    frame.src=`${url}#page=${current}&zoom=page-width&view=FitH`;
    updateProgress();
    setStatus('Lecture intégrale autorisée pour ce compte. L’accès signé est temporaire et sera renouvelé au besoin.','success');
  }catch(error){
    frame.removeAttribute('src');
    setStatus(error?.message||'Lecture intégrale indisponible.','error');
  }
}

async function go(pageNumber){
  current=Math.min(totalPages,Math.max(1,Number(pageNumber)||1));
  savePage();
  await render(false);
}

async function downloadBook(button){
  button.disabled=true;
  const previous=button.textContent;
  button.textContent='Préparation…';
  try{
    const data=await invokeDelivery('download');
    location.assign(String(data.url));
  }catch(error){
    setStatus(error?.message||'Téléchargement indisponible.','error');
  }finally{
    button.disabled=false;
    button.textContent=previous;
  }
}

function bind(){
  document.querySelector('[data-private-reader-prev]')?.addEventListener('click',()=>go(current-1));
  document.querySelector('[data-private-reader-next]')?.addEventListener('click',()=>go(current+1));
  input?.addEventListener('change',()=>go(input.value));
  document.querySelector('[data-private-reader-bookmark]')?.addEventListener('click',savePage);
  document.querySelector('[data-private-reader-refresh]')?.addEventListener('click',()=>render(true));
  document.querySelector('[data-private-book-download]')?.addEventListener('click',event=>downloadBook(event.currentTarget));
}

bind();
render().catch(()=>{});
