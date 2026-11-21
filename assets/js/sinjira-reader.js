import {getSupabase,getCurrentUser,escapeHtml,formatDate,friendlyBackendMessage} from './sinjira-supabase.js';
import {startDemoNavigation} from './sinjira-demo-navigation-v1.mjs';

const page=document.body.dataset.readerPage||'';
const slug=document.body.dataset.novelSlug||'';
const status=document.querySelector('[data-reader-status]');
const configuredTotalPages=Number(document.body.dataset.readerTotalPages||82);
const totalPages=Number.isFinite(configuredTotalPages)&&configuredTotalPages>0?Math.floor(configuredTotalPages):82;

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
  const {error}=await getSupabase().from('reader_library').upsert(payload,{onConflict:'user_id,novel_id'});
  if(error)throw error;
}


function spoiler(c,index){
  const body=`<p data-spoiler-content>${escapeHtml(c.body)}</p>`;
  // Le contenu sensible reste absent de la lecture et de la navigation
  // tant que la personne n'a pas expressément choisi de le dévoiler.
  if(!c.spoiler)return body;
  const id=`sinjira-divulgacheur-${index}`;
  return `<div class="v19-spoiler"><button class="btn btn-secondary btn-small" type="button" data-reveal-spoiler aria-controls="${id}" aria-expanded="false">Afficher le divulgâcheur</button><p id="${id}" data-spoiler-content hidden>${escapeHtml(c.body)}</p></div>`;
}

async function comments(){
  const s=getSupabase();
  const list=document.querySelector('[data-novel-comments]');
  const account=document.querySelector('[data-comment-account]');
  const form=document.querySelector('[data-comment-form]');
  if(!list||!account||!form)return;
  const {data:novel,error:novelError}=await s.from('sinjira_novels').select('id,comments_enabled').eq('slug',slug).maybeSingle();
  if(novelError)throw novelError;
  if(!novel||!novel.comments_enabled){
    list.textContent='Les commentaires ne sont pas disponibles pour cette œuvre.';
    return;
  }

  // RPC SECURITY INVOKER : seuls les commentaires approuvés et les pseudonymes
  // publics figés par la base sont retournés. Ne pas interroger profiles en public.
  const {data,error}=await s.rpc('list_sinjira_novel_comments',{p_novel_slug:slug});
  if(error)throw error;
  const rows=Array.isArray(data)?data.slice(0,100):[];
  list.innerHTML=rows.length?rows.map((c,index)=>`<article class="reader-comment"><header><strong>${escapeHtml(c.pseudo||'Lecteur SINJIRA')}</strong><time>${escapeHtml(formatDate(c.created_at))}</time></header>${spoiler(c,index)}</article>`).join(''):'<p>Aucun commentaire publié pour le moment. Soyez la première personne à participer.</p>';
  list.querySelectorAll('[data-reveal-spoiler]').forEach(button=>button.addEventListener('click',()=>{
    const item=button.closest('.v19-spoiler');
    const content=item?.querySelector('[data-spoiler-content]');
    if(!content)return;
    const revealed=content.hidden;
    content.hidden=!revealed;
    item.classList.toggle('is-revealed',revealed);
    button.textContent=revealed?'Masquer le divulgâcheur':'Afficher le divulgâcheur';
    button.setAttribute('aria-expanded',String(revealed));
  }));

  const user=await getCurrentUser();
  if(!user){
    account.innerHTML='<div class="reader-login-note">Connectez-vous à votre Compte SINJIRA™ pour laisser un commentaire. <a href="/compte/connexion.html?next=%2Fprojets%2Fsinjira%2Fromans%2F%23commentaires">Se connecter</a></div>';
    return;
  }
  const {data:profile}=await s.from('profiles').select('pseudo,display_name').eq('user_id',user.id).maybeSingle();
  account.innerHTML=`<div class="reader-login-note">Commentaire associé au compte <strong>${escapeHtml(profile?.pseudo||profile?.display_name||'Lecteur SINJIRA')}</strong>. Publication après modération.</div>`;
  form.hidden=false;
  const textarea=form.elements.namedItem('body');
  const counter=form.querySelector('[data-comment-count]');
  const updateCount=()=>{
    if(!textarea||!counter)return;
    const length=textarea.value.length;
    counter.textContent=`${length.toLocaleString('fr-CA')} / 3 000 caractères`;
    counter.classList.toggle('near-limit',length>=2700);
  };
  textarea?.addEventListener('input',updateCount);
  updateCount();
  const submit=form.querySelector('button[type="submit"]');
  let submitting=false;
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    if(submitting)return;
    const fd=new FormData(form);
    const body=String(fd.get('body')||'').trim();
    if(body.length<3||body.length>3000){
      setStatus('Votre commentaire doit contenir entre 3 et 3 000 caractères.','error');
      form.elements.namedItem('body')?.focus();
      return;
    }
    submitting=true;
    if(submit){submit.disabled=true;submit.textContent='Envoi en cours…';}
    try{
      // La base fixe le statut pending et les informations publiques de l'auteur.
      // Ne jamais transmettre une approbation/modération depuis le navigateur.
      const {error:insertError}=await s.from('sinjira_novel_comments').insert({
        novel_id:novel.id,user_id:user.id,body,
        spoiler:fd.get('contains_spoilers')==='yes'
      });
      if(insertError)throw insertError;
      form.reset();
      updateCount();
      setStatus('Commentaire reçu. Il sera visible après modération.','success');
    }catch(err){
      setStatus(friendlyBackendMessage(err?.message,'Impossible d’envoyer le commentaire pour le moment.'),'error');
    }finally{
      submitting=false;
      if(submit){submit.disabled=false;submit.textContent='Envoyer pour modération';}
    }
  });
}

async function demo(){
  const frame=document.querySelector('[data-pdf-reader]');
  if(!frame)return;
  let user=null;
  let novel=null;

  // Initialiser la lecture locale immédiatement, sans dépendre d'un serveur.
  const reader=startDemoNavigation({
    document,frame,slug,totalPages,
    onBookmark:async pageNumber=>{
      if(!user||!novel)return false;
      await markReading(user,novel,pageNumber);
      return true;
    }
  });

  // La reprise multiappareil est un enrichissement : une panne d'authentification
  // ou de base ne doit pas bloquer la lecture de la démonstration publique.
  try{
    user=await getCurrentUser();
    if(!user)return;
    novel=await getNovel();
    if(!novel)return;
    const {data,error}=await getSupabase().from('reader_library')
      .select('last_page').eq('user_id',user.id).eq('novel_id',novel.id)
      .maybeSingle();
    if(!error&&data?.last_page)reader.restoreRemotePage(data.last_page);
  }catch(_){
    // La navigation et les marque-pages locaux restent opérationnels.
  }
}

(async()=>{
  try{
    if(!slug)return;
    if(page==='novel')await comments();
    if(page==='demo')await demo();
  }catch(e){
    if(page==='novel'){
      const list=document.querySelector('[data-novel-comments]');
      if(list)list.textContent='Les commentaires sont temporairement indisponibles.';
    }
    setStatus(friendlyBackendMessage(e?.message,'Le contenu ne peut pas être chargé pour le moment.'),'error');
  }
})();
