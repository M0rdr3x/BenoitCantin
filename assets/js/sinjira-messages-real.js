import {getSupabase,requireCommunityUser,escapeHtml,formatDate,avatarUrl,reportContent,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';
import {unreadCounts,markConversationRead} from './sinjira-message-read-state.js?v=24.4.71';

const UI_VERSION='24.4.71';
const contacts=document.querySelector('[data-contact-list]');
const search=document.querySelector('[data-contact-search]');
const log=document.querySelector('[data-chat-log]');
const form=document.querySelector('[data-chat-form]');
const title=document.querySelector('[data-chat-title]');
const status=document.querySelector('[data-social-status]');
let user,all=[],peer=null,channel=null,unreadByUser=new Map();

function fail(error,fallback='Action impossible dans la messagerie.'){
  socialErrorStatus(status,error,fallback);
}

async function loadContacts(){
  const {data,error}=await getSupabase().from('social_profiles').select('*').neq('user_id',user.id).order('pseudo');
  if(error)throw error;
  all=Array.isArray(data)?data:[];
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
      return `<button class="v20-contact" data-user="${escapeHtml(item.user_id)}"><img src="${escapeHtml(avatarUrl(item.avatar_path))}" alt=""><span><strong>${escapeHtml(item.pseudo||item.display_name||'Membre')}</strong><small>Compte réel${unreadLabel}</small></span></button>`;
    })
    .join('')||'<p>Aucun membre trouvé.</p>';
  contacts.querySelectorAll('[data-user]').forEach(button=>{
    button.addEventListener('click',()=>openPeer(button.dataset.user).catch(error=>fail(error,'Impossible d’ouvrir cette conversation.')));
  });
}

async function openPeer(id){
  peer=all.find(item=>item.user_id===id)||null;
  if(!peer)return;
  history.replaceState({},'',`?user=${encodeURIComponent(id)}`);
  title.innerHTML=`<div class="v20-social-identity"><img class="v20-social-avatar" src="${escapeHtml(avatarUrl(peer.avatar_path))}" alt=""><div><strong>${escapeHtml(peer.pseudo||peer.display_name||'Membre')}</strong><span class="v20-social-time">Conversation compte réel</span></div></div><button class="btn btn-secondary btn-small" data-block-peer>Bloquer</button>`;
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
