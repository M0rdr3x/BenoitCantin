import {getSupabase,requireUser,escapeHtml,formatDate,setStatus} from './sinjira-supabase.js';

const s=getSupabase();
const pageStatus=document.querySelector('[data-notifications-status]');

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
      ${unread?`<button class="btn btn-secondary btn-small" type="button" data-notification-read="${escapeHtml(item.id)}">Marquer comme lu</button>`:''}
      ${path?`<a class="btn btn-primary btn-small" data-notification-open="${escapeHtml(item.id)}" href="${escapeHtml(path)}">Ouvrir</a>`:''}
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
  const all=document.querySelector('[data-notifications-read-all]');
  const unreadNode=document.querySelector('[data-notifications-unread-count]');
  const totalNode=document.querySelector('[data-notifications-total-count]');
  if(all)all.disabled=true;
  box.setAttribute('aria-busy','true');
  let data,unread;
  try{
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
    if(recent.error||countResult.error||!Array.isArray(recent.data)||
       !Number.isSafeInteger(countResult.count)||countResult.count<0){
      throw new Error('Notifications indisponibles');
    }
    data=recent.data;
    unread=countResult.count;
  }catch(error){
    if(unreadNode)unreadNode.textContent='—';
    if(totalNode)totalNode.textContent='—';
    box.innerHTML='<div class="notice"><strong>Les avis sont temporairement indisponibles.</strong><p>Rechargez la page pour réessayer.</p></div>';
    throw error;
  }finally{
    box.setAttribute('aria-busy','false');
  }
  if(unreadNode)unreadNode.textContent=String(unread);
  if(totalNode)totalNode.textContent=String(data.length);

  box.innerHTML=data.length
    ? data.map(item=>notificationCard(item)).join('')
    : '<div class="notice"><strong>Aucun avis pour le moment.</strong><p>Les changements importants de votre compte apparaîtront ici.</p></div>';

  box.querySelectorAll('[data-notification-read]').forEach(button=>button.addEventListener('click',async()=>{
    button.disabled=true;
    try{
      await markRead(user,button.dataset.notificationRead);
    }catch(_){
      button.disabled=false;
      setStatus(pageStatus,'Impossible de modifier cet avis pour le moment.','error');
      return;
    }
    try{
      await loadFullPage(user);
      setStatus(pageStatus,'Avis marqué comme lu.','success');
    }catch(_){
      setStatus(pageStatus,'Avis marqué comme lu, mais actualisation indisponible. Rechargez la page.','error');
    }
  }));

  box.querySelectorAll('[data-notification-open]').forEach(link=>link.addEventListener('click',async event=>{
    const id=link.dataset.notificationOpen;
    const card=link.closest('[data-notification-id]');
    if(!card?.querySelector('[data-notification-read]'))return;
    event.preventDefault();
    try{await markRead(user,id)}catch(_){}
    location.href=link.href;
  }));

  if(all){
    all.disabled=unread===0;
    all.onclick=async()=>{
      all.disabled=true;
      try{
        const {error:updateError}=await s.from('user_notifications')
          .update({read_at:new Date().toISOString()})
          .eq('user_id',user.id)
          .is('read_at',null);
        if(updateError)throw updateError;
      }catch(_){
        all.disabled=false;
        setStatus(pageStatus,'Impossible de marquer tous les avis comme lus.','error');
        return;
      }
      try{
        await loadFullPage(user);
        setStatus(pageStatus,'Marquage terminé. Le compteur a été actualisé.','success');
      }catch(_){
        setStatus(pageStatus,'Marquage effectué, mais actualisation indisponible. Rechargez la page.','error');
      }
    };
  }
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
  if(error?.message!=='Connexion requise')setStatus(pageStatus,'Impossible de charger les avis privés pour le moment.','error');
});
