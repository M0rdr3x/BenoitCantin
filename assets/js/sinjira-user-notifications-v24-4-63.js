import {getSupabase,requireUser,escapeHtml,formatDate,setStatus} from './sinjira-supabase.js';

const s=getSupabase();
const pageStatus=document.querySelector('[data-notifications-status]');
const filter=document.querySelector('[data-notifications-filter]');
let mutationInFlight=false;
let refreshRequired=false;

function applyFilter(){
  const cards=[...document.querySelectorAll('[data-notifications-list] [data-notification-id]')];
  const mode=filter?.value||'all';
  let shown=0;
  for(const card of cards){
    const unread=card.classList.contains('v24-notification-unread');
    card.hidden=mode==='unread'?!unread:mode==='read'?unread:false;
    if(!card.hidden)shown++;
  }
  const summary=document.querySelector('[data-notifications-filter-summary]');
  if(summary)summary.textContent=cards.length?`${shown} avis affiché(s) sur ${cards.length} avis récents.`:'Aucun avis récent.';
  const empty=document.querySelector('[data-notifications-filter-empty]');
  if(empty)empty.hidden=cards.length===0||shown!==0;
}
filter?.addEventListener('change',applyFilter);

function syncReadControls(){
  const locked=mutationInFlight||refreshRequired;
  document.querySelectorAll('[data-notifications-list] [data-notification-read]').forEach(button=>{button.disabled=locked;});
  const all=document.querySelector('[data-notifications-read-all]');
  if(all)all.disabled=locked||all.dataset.hasUnread!=='true';
}
async function runReadAction(user,button,mutate,successMessage,errorMessage){
  if(mutationInFlight||refreshRequired)return;
  const hadFocus=document.activeElement===button;
  mutationInFlight=true;
  syncReadControls();
  let updated=false;
  try{
    await mutate();
    updated=true;
    await loadFullPage(user);
    setStatus(pageStatus,successMessage,'success');
  }catch(_){
    document.querySelector('[data-notifications-list]')?.setAttribute('aria-busy','false');
    refreshRequired=updated;
    setStatus(pageStatus,updated?'Modification enregistrée, mais la liste n’a pas pu être actualisée. Rechargez la page.':errorMessage,'error');
  }finally{
    mutationInFlight=false;
    syncReadControls();
    if(hadFocus&&(!document.activeElement||document.activeElement===document.body||document.activeElement===button&&button.disabled))pageStatus?.focus();
  }
}

const typeLabel=type=>({
  access_request:'Accès',
  novel_comment:'Commentaire',
  character_submission:'Registre',
  character:'Personnage',
  playtest:'Playtest',
  social_real_reply:'Communauté',
  social_character_reply:'Rôle-play',
  dating:'Rencontres'
}[type]||'SINJIRA™');

function safeActionPath(value){
  const path=String(value||'');
  return path.startsWith('/compte/')||path.startsWith('/projets/sinjira/')?path:'';
}

function notificationCard(item,{compact=false}={}){
  const unread=!item.read_at;
  const path=safeActionPath(item.action_path);
  return `<article class="account-card${unread?' v24-notification-unread':''}" data-notification-id="${escapeHtml(item.id)}">
    <div class="account-welcome-strip"><span>${escapeHtml(typeLabel(item.notification_type))}</span><span>${unread?'Non lu':'Lu'}</span></div>
    <h${compact?'3':'2'}>${escapeHtml(item.title||'Avis SINJIRA™')}</h${compact?'3':'2'}>
    <p>${escapeHtml(item.body||'')}</p>
    <small>${escapeHtml(formatDate(item.created_at))}</small>
    <div class="hero-actions">
      ${unread&&!compact?`<button class="btn btn-secondary btn-small" type="button" data-notification-read="${escapeHtml(item.id)}" aria-label="Marquer comme lu : ${escapeHtml(item.title||'Avis SINJIRA™')}">Marquer comme lu</button>`:''}
      ${path?`<a class="btn btn-primary btn-small" data-notification-open="${escapeHtml(item.id)}" href="${escapeHtml(path)}" aria-label="Ouvrir : ${escapeHtml(item.title||'Avis SINJIRA™')}">Ouvrir</a>`:''}
    </div>
  </article>`;
}

async function markRead(user,id){
  const {error}=await s.from('user_notifications')
    .update({read_at:new Date().toISOString()})
    .eq('user_id',user.id)
    .eq('id',id)
    .is('read_at',null);
  if(error)throw error;
}

async function loadFullPage(user){
  const box=document.querySelector('[data-notifications-list]');
  if(!box)return;
  box.setAttribute('aria-busy','true');
  const [recent,countResult]=await Promise.all([
    s.from('user_notifications')
      .select('id,notification_type,title,body,action_path,read_at,created_at')
      .eq('user_id',user.id)
      .order('created_at',{ascending:false})
      .limit(100),
    s.from('user_notifications')
      .select('id',{count:'exact',head:true})
      .eq('user_id',user.id)
      .is('read_at',null)
  ]);
  if(recent.error||countResult.error||!Number.isSafeInteger(countResult.count)||countResult.count<0){
    box.setAttribute('aria-busy','false');
    throw recent.error||countResult.error||new Error('NOTIFICATION_COUNT_UNAVAILABLE');
  }
  const data=recent.data||[];
  const unread=countResult.count;
  const unreadNode=document.querySelector('[data-notifications-unread-count]');
  const totalNode=document.querySelector('[data-notifications-total-count]');
  if(unreadNode)unreadNode.textContent=String(unread);
  if(totalNode)totalNode.textContent=String(data.length);

  box.innerHTML=data.length
    ? data.map(item=>notificationCard(item)).join('')
    : '<div class="notice"><strong>Aucun avis pour le moment.</strong><p>Les changements importants de votre compte apparaîtront ici.</p></div>';

  box.setAttribute('aria-busy','false');
  if(filter)filter.disabled=false;
  applyFilter();
  box.querySelectorAll('[data-notification-read]').forEach(button=>button.addEventListener('click',()=>{
    return runReadAction(user,button,()=>markRead(user,button.dataset.notificationRead),
      'Avis marqué comme lu.','Impossible de modifier cet avis pour le moment.');
  }));

  box.querySelectorAll('[data-notification-open]').forEach(link=>link.addEventListener('click',async event=>{
    // Respecter les usages natifs (nouvel onglet, sélection avec modificateurs).
    if(event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
    const card=link.closest('[data-notification-id]');
    if(!card?.querySelector('[data-notification-read]')||mutationInFlight||refreshRequired)return;
    event.preventDefault();
    mutationInFlight=true;
    syncReadControls();
    // Ne pas bloquer indéfiniment la navigation lorsque le réseau est lent.
    let timeout;
    try{
      await Promise.race([
        markRead(user,link.dataset.notificationOpen),
        new Promise(resolve=>{timeout=setTimeout(resolve,1500);})
      ]);
    }catch(_){}finally{clearTimeout(timeout);}
    location.href=link.href;
  }));

  const all=document.querySelector('[data-notifications-read-all]');
  if(all){
    all.dataset.hasUnread=String(unread>0);
    all.onclick=()=>runReadAction(user,all,async()=>{
      const {error}=await s.from('user_notifications')
        .update({read_at:new Date().toISOString()})
        .eq('user_id',user.id)
        .is('read_at',null);
      if(error)throw error;
    },'Tous les avis sont maintenant marqués comme lus.','Impossible de marquer tous les avis comme lus.');
  }
  syncReadControls();
}

async function loadDashboardPreview(user){
  const box=document.querySelector('[data-notifications-preview]');
  if(!box)return;
  const [recentResult,countResult]=await Promise.all([
    s.from('user_notifications')
      .select('id,notification_type,title,body,action_path,read_at,created_at')
      .eq('user_id',user.id)
      .order('created_at',{ascending:false})
      .limit(3),
    s.from('user_notifications')
      .select('id',{count:'exact',head:true})
      .eq('user_id',user.id)
      .is('read_at',null)
  ]);
  if(recentResult.error||countResult.error){
    box.innerHTML='<p>Les avis privés sont temporairement indisponibles.</p>';
    return;
  }
  const recent=recentResult.data||[];
  const unread=Number(countResult.count||0);
  document.querySelectorAll('[data-notifications-dashboard-count]').forEach(node=>{node.textContent=String(unread)});
  box.innerHTML=recent.length
    ? recent.map(item=>notificationCard(item,{compact:true})).join('')
    : '<p>Aucun nouvel avis. Les changements importants de votre compte apparaîtront ici.</p>';
}

(async()=>{
  if(!document.querySelector('[data-notifications-list],[data-notifications-preview]'))return;
  const user=await requireUser('/compte/connexion.html');
  await Promise.all([
    loadFullPage(user),
    loadDashboardPreview(user)
  ]);
})().catch(error=>{
  const box=document.querySelector('[data-notifications-list]');
  if(box){
    box.setAttribute('aria-busy','false');
    box.textContent='Les avis privés sont indisponibles. Actualisez la page pour réessayer.';
  }
  if(error?.message!=='Connexion requise')setStatus(pageStatus,'Impossible de charger les avis privés pour le moment.','error');
});
