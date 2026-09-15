import {getSupabase,requireUser} from './sinjira-supabase.js';

const READER_FUNCTION='get-private-book-reading-url';
const DOWNLOAD_FUNCTION='get-private-book-url';
const STORAGE_KEY='sinjira-reader-full-la-cendre-du-jugement-v1';
const body=document.body;
const totalPages=Math.max(1,Number(body.dataset.readerTotalPages)||1);
const frame=document.querySelector('[data-private-pdf-reader]');
const status=document.querySelector('[data-private-reader-status]');
const input=document.querySelector('[data-private-reader-page]');
const progress=document.querySelector('[data-private-reader-progress]');
const bar=document.querySelector('[data-private-reader-progress-bar]');
const resume=document.querySelector('[data-private-reader-resume]');
let current=Math.min(totalPages,Math.max(1,Number(localStorage.getItem(STORAGE_KEY))||1));
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
  const percent=Math.round((current/totalPages)*100);
  if(input)input.value=String(current);
  if(progress){progress.value=current;progress.max=totalPages;progress.textContent=`${current} sur ${totalPages}`;}
  if(bar)bar.style.width=`${percent}%`;
  if(resume)resume.textContent=`Page ${current} · ${percent} %`;
}

function savePage(){
  localStorage.setItem(STORAGE_KEY,String(current));
  updateProgress();
  if(resume)resume.textContent=`Page ${current} sauvegardée sur cet appareil.`;
}

async function requireReaderUser(){
  return requireUser('/compte/connexion.html');
}

async function requestReadingUrl(force=false){
  if(!force&&signedUrl&&Date.now()<refreshAt)return signedUrl;
  if(accessPromise)return accessPromise;
  accessPromise=(async()=>{
    await requireReaderUser();
    const {data,error}=await getSupabase().functions.invoke(READER_FUNCTION);
    if(error||!data?.ok||!data?.url)throw new Error(data?.error||'Impossible de préparer la lecture privée.');
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
    await requireReaderUser();
    const {data,error}=await getSupabase().functions.invoke(DOWNLOAD_FUNCTION);
    if(error||!data?.ok||!data?.url)throw new Error(data?.error||'Téléchargement indisponible.');
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
