import {getSupabase,getCurrentUser,escapeHtml,formatDate} from './sinjira-supabase.js';

const page=document.body.dataset.readerPage||'';
const slug=document.body.dataset.novelSlug||'';
const status=document.querySelector('[data-reader-status]');
const configuredTotalPages=Number(document.body.dataset.readerTotalPages||84);
const totalPages=Number.isFinite(configuredTotalPages)&&configuredTotalPages>0?Math.floor(configuredTotalPages):84;

function setStatus(msg,type='info'){
  if(!status)return;
  status.textContent=msg;
  status.dataset.statusType=type;
  status.hidden=false;
}

async function getNovel(){
  const {data,error}=await getSupabase().from('novels').select('*').eq('slug',slug).maybeSingle();
  if(error)throw error;
  return data;
}

async function markReading(user,novel,lastPage){
  if(!user||!novel)return;
  const payload={user_id:user.id,novel_id:novel.id,last_opened_at:new Date().toISOString()};
  if(lastPage){
    const safePage=Math.min(totalPages,Math.max(1,Number(lastPage)||1));
    payload.last_page=safePage;
    payload.progress_percent=Math.round((safePage/totalPages)*100);
  }
  await getSupabase().from('reader_library').upsert(payload,{onConflict:'user_id,novel_id'});
}

function spoiler(c){
  const body=`<p data-spoiler-content>${escapeHtml(c.body)}</p>`;
  return c.contains_spoilers?`<div class="v19-spoiler"><button class="btn btn-secondary btn-small" type="button" data-reveal-spoiler>Afficher le divulgâcheur</button>${body}</div>`:body;
}

async function comments(){
  const s=getSupabase(),novel=await getNovel(),user=await getCurrentUser();
  if(user)await markReading(user,novel);
  const {data=[],error}=await s.from('novel_comments').select('id,body,display_name_snapshot,created_at,contains_spoilers').eq('novel_id',novel.id).eq('status','approved').order('created_at',{ascending:false}).limit(100);
  if(error)throw error;
  const rows=Array.isArray(data)?data:[];
  const list=document.querySelector('[data-novel-comments]');
  list.innerHTML=rows.length?rows.map(c=>`<article class="reader-comment"><header><strong>${escapeHtml(c.display_name_snapshot||'Lecteur SINJIRA')}</strong><time>${escapeHtml(formatDate(c.created_at))}</time></header>${spoiler(c)}</article>`).join(''):'<p>Aucun commentaire publié pour le moment.</p>';
  list.querySelectorAll('[data-reveal-spoiler]').forEach(b=>b.addEventListener('click',()=>{
    const x=b.closest('.v19-spoiler');
    x.classList.toggle('is-revealed');
    b.textContent=x.classList.contains('is-revealed')?'Masquer le divulgâcheur':'Afficher le divulgâcheur';
  }));
  const account=document.querySelector('[data-comment-account]'),form=document.querySelector('[data-comment-form]');
  if(!user){
    account.innerHTML='<div class="reader-login-note">Connectez-vous à votre Compte SINJIRA pour laisser un commentaire. <a href="../../../compte/connexion.html?next=/projets/sinjira/romans/index.html%23commentaires">Connexion</a></div>';
    return;
  }
  const {data:p}=await s.from('profiles').select('pseudo,display_name').eq('user_id',user.id).maybeSingle();
  account.innerHTML=`<div class="reader-login-note">Commentaire associé au compte <strong>${escapeHtml(p?.pseudo||p?.display_name||user.email||'Lecteur SINJIRA')}</strong>. Il sera publié après modération.</div>`;
  form.hidden=false;
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    const fd=new FormData(form),body=String(fd.get('body')||'').trim();
    if(body.length<3)return setStatus('Le commentaire est trop court.','error');
    const {error}=await s.from('novel_comments').insert({novel_id:novel.id,user_id:user.id,display_name_snapshot:p?.pseudo||p?.display_name||'Lecteur SINJIRA',body,contains_spoilers:fd.get('contains_spoilers')==='yes',status:'pending'});
    if(error)return setStatus(error.message,'error');
    form.reset();
    setStatus('Commentaire envoyé. Il apparaîtra après approbation.','success');
  });
}

async function demo(){
  const frame=document.querySelector('[data-pdf-reader]');
  if(!frame)return;
  const input=document.querySelector('[data-reader-page-number]');
  const bar=document.querySelector('[data-reader-progress-bar]');
  const progress=document.querySelector('[data-reader-progress-native]');
  const resume=document.querySelector('[data-reader-resume]');
  const storageKey=`sinjira-reader-${slug}`;
  const clampPage=(value)=>{
    const number=Number(value);
    return Number.isFinite(number)?Math.min(totalPages,Math.max(1,Math.floor(number))):1;
  };

  // Le PDF démo est public : ne pas bloquer la lecture sur le réseau Supabase.
  let saved=1;
  try{saved=clampPage(localStorage.getItem(storageKey)||1);}
  catch(_storageError){setStatus('Lecture disponible; mémorisation locale indisponible.','info');}

  let user=null,novel=null;
  try{
    user=await getCurrentUser();
    if(user)novel=await getNovel();
  }catch(_networkError){
    user=null;
    novel=null;
    setStatus('Lecture gratuite disponible sans connexion au compte.','info');
  }
  if(user&&novel){
    try{
      const {data}=await getSupabase().from('reader_library').select('last_page')
        .eq('user_id',user.id).eq('novel_id',novel.id).maybeSingle();
      if(data?.last_page)saved=clampPage(data.last_page);
    }catch(_networkError){
      setStatus('Progression distante indisponible; reprise locale utilisée.','info');
    }
  }

  let current=clampPage(saved);
  const render=()=>{
    const percent=Math.round(current/totalPages*100);
    if(input){input.max=String(totalPages);input.value=current;}
    if(bar)bar.style.width=`${percent}%`;
    if(progress){
      progress.max=totalPages;
      progress.value=current;
      progress.textContent=`${current} sur ${totalPages}`;
    }
    if(resume)resume.textContent=`Page mémorisée : ${current} · ${percent} %`;
    frame.src=`../documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf#page=${current}&zoom=page-width&view=FitH`;
  };
  const save=async()=>{
    let localSaved=false;
    try{
      localStorage.setItem(storageKey,String(current));
      localSaved=true;
    }catch(_storageError){
      setStatus('Mémorisation locale indisponible dans ce navigateur.','info');
    }
    if(user&&novel){
      try{await markReading(user,novel,current);}
      catch(_networkError){
        setStatus('Progression distante indisponible; lecture maintenue.','info');
      }
    }
    if(localSaved&&resume)resume.textContent=`Page ${current} sauvegardée.`;
  };
  document.querySelector('[data-reader-prev]')?.addEventListener('click',()=>{
    current=clampPage(current-1);render();
  });
  document.querySelector('[data-reader-next]')?.addEventListener('click',()=>{
    current=clampPage(current+1);render();
  });
  input?.addEventListener('change',()=>{
    current=clampPage(input.value);render();
  });
  document.querySelector('[data-reader-bookmark]')?.addEventListener('click',()=>{
    save().catch(()=>setStatus('Sauvegarde indisponible; lecture maintenue.','info'));
  });
  render();
  if(user&&novel){
    try{await markReading(user,novel,current);}
    catch(_networkError){
      setStatus('Progression distante indisponible; lecture maintenue.','info');
    }
  }
}

(async()=>{
  try{
    if(!slug)return;
    if(page==='novel')await comments();
    if(page==='demo')await demo();
  }catch(e){
    setStatus(e?.message||'Erreur lecteur.','error');
  }
})();
