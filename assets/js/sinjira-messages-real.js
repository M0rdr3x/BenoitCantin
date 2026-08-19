import {getSupabase,requireCommunityUser,escapeHtml,formatDate,avatarUrl,reportContent,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';
import {unreadCounts,markConversationRead} from './sinjira-message-read-state.js?v=24.4.71';

const UI_VERSION='24.4.74';
const contacts=document.querySelector('[data-contact-list]');
const search=document.querySelector('[data-contact-search]');
const log=document.querySelector('[data-chat-log]');
const form=document.querySelector('[data-chat-form]');
const title=document.querySelector('[data-chat-title]');
const status=document.querySelector('[data-social-status]');
let user,all=[],peer=null,channel=null,unreadByUser=new Map();
let datingPrivacyUnavailable=false;
const datingLockedUsers=new Set();
const datingIntroByUser=new Map();
const datingAvatarByUser=new Map();

function fail(error,fallback='Action impossible dans la messagerie.'){
  socialErrorStatus(status,error,fallback);
}

function placeholderAvatar(label='M'){
  const letter=String(label||'M').trim().slice(0,1).toUpperCase()||'M';
  return `<span class="v20-social-avatar v20-avatar-placeholder" aria-hidden="true">${escapeHtml(letter)}</span>`;
}

function peerAvatarMarkup(item){
  if(!item)return placeholderAvatar('M');
  if(datingLockedUsers.has(item.user_id))return '<span class="v20-social-avatar v20-avatar-placeholder" aria-hidden="true">🔒</span>';
  const path=datingAvatarByUser.get(item.user_id)||item.avatar_path;
  return path?`<img class="v20-social-avatar" src="${escapeHtml(avatarUrl(path))}" alt="">`:placeholderAvatar(item.pseudo||item.display_name||'M');
}

async function loadDatingPrivacy(){
  datingLockedUsers.clear();
  datingIntroByUser.clear();
  datingAvatarByUser.clear();
  datingPrivacyUnavailable=false;

  const {data,error}=await getSupabase().rpc('dating_my_introductions');
  if(error){
    const message=String(error.message||'');
    // Avant le déploiement V24.4.74, l'absence du RPC ne doit pas casser la messagerie existante.
    // Si le RPC existe mais échoue, on masque tous les avatars par prudence.
    if(/dating_my_introductions|function .* does not exist|PGRST202|404/i.test(message))return;
    datingPrivacyUnavailable=true;
    return;
  }

  const accepted=(Array.isArray(data)?data:[]).filter(row=>row?.status==='accepted'&&row?.other_user_id);
  for(const row of accepted){
    datingIntroByUser.set(row.other_user_id,row);
    const {data:photo,error:photoError}=await getSupabase().rpc('dating_photo_reveal_status',{p_introduction_id:row.id});
    if(photoError||!photo?.unlocked){
      datingLockedUsers.add(row.other_user_id);
      continue;
    }
    if(photo.other_avatar_path)datingAvatarByUser.set(row.other_user_id,photo.other_avatar_path);
  }
}

async function loadContacts(){
  // Le premier chargement exclut volontairement avatar_path afin qu'un contact Rencontres
  // verrouillé ne soit jamais reçu par le navigateur avant la vérification 10+10 + consentements.
  const {data,error}=await getSupabase().from('social_profiles').select('user_id,pseudo,display_name').neq('user_id',user.id).order('pseudo');
  if(error)throw error;
  all=Array.isArray(data)?data:[];

  if(datingPrivacyUnavailable)return;
  const visibleIds=all.filter(item=>!datingLockedUsers.has(item.user_id)).map(item=>item.user_id);
  if(!visibleIds.length)return;

  const avatarMap=new Map();
  for(let offset=0;offset<visibleIds.length;offset+=50){
    const chunk=visibleIds.slice(offset,offset+50);
    const {data:avatars,error:avatarError}=await getSupabase().from('social_profiles').select('user_id,avatar_path').in('user_id',chunk);
    if(avatarError)throw avatarError;
    (avatars||[]).forEach(row=>avatarMap.set(row.user_id,row.avatar_path||null));
  }
  all=all.map(item=>({...item,avatar_path:avatarMap.get(item.user_id)||null}));
}

async function refreshDatingStateForPeer(peerId){
  const intro=datingIntroByUser.get(peerId);
  if(!intro)return;
  const {data,error}=await getSupabase().rpc('dating_photo_reveal_status',{p_introduction_id:intro.id});
  if(error){
    datingLockedUsers.add(peerId);
    datingAvatarByUser.delete(peerId);
    return;
  }
  if(data?.unlocked){
    datingLockedUsers.delete(peerId);
    if(data.other_avatar_path)datingAvatarByUser.set(peerId,data.other_avatar_path);
  }else{
    datingLockedUsers.add(peerId);
    datingAvatarByUser.delete(peerId);
  }
}

async function loadUnread(){
  unreadByUser=await unreadCounts('social_real_messages',user.id,'sender_user_id');
}

function renderContacts(){
  const q=String(search?.value||'').trim().toLowerCase();
  contacts.innerHTML=all
    .filter(item=>String(item.pseudo||item.display_name||'').toLowerCase().includes(q))
    .map(item=>{
      const unread=unreadByUser.get(item.user_id)||0;
      const unreadLabel=unread?` · ${unread} non lu${unread>1?'s':''}`:'';
      const datingLabel=datingLockedUsers.has(item.user_id)?' · photo Rencontres verrouillée':'';
      return `<button class="v20-contact" data-user="${escapeHtml(item.user_id)}">${peerAvatarMarkup(item)}<span><strong>${escapeHtml(item.pseudo||item.display_name||'Membre')}</strong><small>Compte réel${unreadLabel}${datingLabel}</small></span></button>`;
    })
    .join('')||'<p>Aucun membre trouvé.</p>';
  contacts.querySelectorAll('[data-user]').forEach(button=>{
    button.addEventListener('click',()=>openPeer(button.dataset.user).catch(error=>fail(error,'Impossible d’ouvrir cette conversation.')));
  });
}

function chatSubtitle(item){
  const intro=datingIntroByUser.get(item.user_id);
  if(!intro)return 'Conversation compte réel';
  if(datingLockedUsers.has(item.user_id))return 'Présentation Rencontres · photo verrouillée jusqu’à 10+10 messages et double consentement';
  return 'Présentation Rencontres · photo révélée par consentement mutuel';
}

async function openPeer(id){
  peer=all.find(item=>item.user_id===id)||null;
  if(!peer)return;
  if(datingIntroByUser.has(id))await refreshDatingStateForPeer(id);
  history.replaceState({},'',`?user=${encodeURIComponent(id)}`);
  const datingAction=datingIntroByUser.has(id)?'<a class="btn btn-secondary btn-small" href="rencontres.html">Gérer Rencontres</a>':'';
  title.innerHTML=`<div class="v20-social-identity">${peerAvatarMarkup(peer)}<div><strong>${escapeHtml(peer.pseudo||peer.display_name||'Membre')}</strong><span class="v20-social-time">${escapeHtml(chatSubtitle(peer))}</span></div></div><div class="dating-actions">${datingAction}<button class="btn btn-secondary btn-small" data-block-peer>Bloquer</button></div>`;
  title.querySelector('[data-block-peer]')?.addEventListener('click',()=>blockPeer().catch(error=>fail(error,'Impossible de bloquer ce compte.')));
  form.hidden=false;
  await messages();
}

async function messages(){
  if(!peer)return;
  const {data,error}=await getSupabase().from('social_real_messages')
    .select('*')
    .or(`and(sender_user_id.eq.${user.id},recipient_user_id.eq.${peer.user_id}),and(sender_user_id.eq.${peer.user_id},recipient_user_id.eq.${user.id})`)
    .order('created_at');
  if(error)throw error;
  const rows=Array.isArray(data)?data:[];
  log.innerHTML=rows.map(message=>`<div class="v20-bubble ${message.sender_user_id===user.id?'mine':''}" data-message="${message.id}">${escapeHtml(message.body)}<time>${escapeHtml(formatDate(message.created_at))}</time>${message.sender_user_id!==user.id?'<button class="link-button" data-report-message>Signaler</button>':''}</div>`).join('')||'<p>Commencez la conversation.</p>';
  log.scrollTop=log.scrollHeight;

  if(rows.some(message=>message.recipient_user_id===user.id&&!message.read_at)){
    await markConversationRead('social_real_messages',user.id,{sender_user_id:peer.user_id});
    unreadByUser.delete(peer.user_id);
    renderContacts();
  }

  if(datingIntroByUser.has(peer.user_id)){
    await refreshDatingStateForPeer(peer.user_id);
    const datingAction='<a class="btn btn-secondary btn-small" href="rencontres.html">Gérer Rencontres</a>';
    title.innerHTML=`<div class="v20-social-identity">${peerAvatarMarkup(peer)}<div><strong>${escapeHtml(peer.pseudo||peer.display_name||'Membre')}</strong><span class="v20-social-time">${escapeHtml(chatSubtitle(peer))}</span></div></div><div class="dating-actions">${datingAction}<button class="btn btn-secondary btn-small" data-block-peer>Bloquer</button></div>`;
    title.querySelector('[data-block-peer]')?.addEventListener('click',()=>blockPeer().catch(error=>fail(error,'Impossible de bloquer ce compte.')));
    renderContacts();
  }

  log.querySelectorAll('[data-report-message]').forEach(button=>button.addEventListener('click',async()=>{
    const element=button.closest('[data-message]');
    const message=rows.find(item=>item.id===element?.dataset.message);
    if(!message)return;
    const reason=prompt('Pourquoi signalez-vous ce message?');
    if(!reason)return;
    try{
      await reportContent({network:'real',target_type:'message',target_id:message.id,reason,snapshot:{body:message.body,sender_user_id:message.sender_user_id,recipient_user_id:message.recipient_user_id}});
      alert('Message signalé à l’administration.');
    }catch(error){fail(error,'Signalement impossible pour le moment.');}
  }));
}

async function blockPeer(){
  if(!peer||!confirm(`Bloquer ${peer.pseudo||peer.display_name||'ce membre'}? Les messages et interactions seront bloqués.`))return;
  const {error}=await getSupabase().from('social_blocks').upsert({blocker_user_id:user.id,blocked_user_id:peer.user_id},{onConflict:'blocker_user_id,blocked_user_id'});
  if(error)return fail(error,'Impossible de bloquer ce compte.');
  location.href='blocages.html';
}

(async()=>{
  try{
    user=await requireCommunityUser();
    await loadDatingPrivacy();
    await Promise.all([loadContacts(),loadUnread()]);
    renderContacts();
    search?.addEventListener('input',renderContacts);

    form.addEventListener('submit',async event=>{
      event.preventDefault();
      if(!peer)return;
      const body=String(new FormData(form).get('body')||'').trim();
      if(!body)return;
      const button=form.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      try{
        const {error}=await getSupabase().from('social_real_messages').insert({sender_user_id:user.id,recipient_user_id:peer.user_id,body});
        if(error)return fail(error,'Impossible d’envoyer ce message.');
        form.reset();
        await messages();
      }finally{
        if(button)button.disabled=false;
      }
    });

    channel=getSupabase().channel(`real-messages-${user.id}`)
      .on('postgres_changes',{event:'INSERT',schema:'public',table:'social_real_messages'},payload=>{
        const message=payload.new;
        const currentPeer=peer?.user_id;
        const belongsToOpenPeer=currentPeer&&((message.sender_user_id===user.id&&message.recipient_user_id===currentPeer)||(message.sender_user_id===currentPeer&&message.recipient_user_id===user.id));
        if(belongsToOpenPeer){
          messages().catch(error=>fail(error,'Impossible d’actualiser la conversation.'));
        }else if(message.recipient_user_id===user.id){
          loadUnread().then(renderContacts).catch(error=>fail(error,'Impossible d’actualiser les messages non lus.'));
        }
      })
      .subscribe();

    const requested=new URLSearchParams(location.search).get('user');
    if(requested&&all.some(item=>item.user_id===requested))await openPeer(requested);
    socialStatus(status,`Messagerie prête · V${UI_VERSION}.`,'success');
  }catch(error){
    if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise'){
      fail(error,'La messagerie n’a pas pu terminer sa vérification.');
    }
  }
})();
