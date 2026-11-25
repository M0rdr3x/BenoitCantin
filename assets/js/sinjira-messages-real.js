import {getSupabase,requireCommunityUser,escapeHtml,formatDate,avatarUrl,reportContent,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';
import {unreadCounts,markConversationRead} from './sinjira-message-read-state.js?v=24.4.71';

import {requestModeration} from './sinjira-message-moderation-dialog.mjs?v=1.0.0';

const UI_VERSION='24.4.73';
const contacts=document.querySelector('[data-contact-list]');
const search=document.querySelector('[data-contact-search]');
const log=document.querySelector('[data-chat-log]');
const form=document.querySelector('[data-chat-form]');
const title=document.querySelector('[data-chat-title]');
const status=document.querySelector('[data-social-status]');
let user,all=[],peer=null,channel=null,unreadByUser=new Map();
const drafts=new Map();
const composer=form.querySelector('textarea[name="body"]');
const sendButton=form.querySelector('button[type="submit"]');
let requestVersion=0,sending=false;
const reporting=new Set();
const blocking=new Set();


function rememberDraft(){
  if(!peer)return;
  if(composer.value)drafts.set(peer.user_id,composer.value);
  else drafts.delete(peer.user_id);
}
function syncSendButton(){
  if(sendButton)sendButton.disabled=sending;
}


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
  const selected=all.find(item=>item.user_id===id);
  if(!selected)return;
  if(peer?.user_id===id){await messages();return;}
  rememberDraft();
  peer=selected;
  requestVersion++;
  log.textContent='Chargement de la conversation…';
  log.setAttribute('aria-busy','true');
  composer.value=drafts.get(id)||'';
  syncSendButton();
  history.replaceState({},'',`?user=${encodeURIComponent(id)}`);
  title.innerHTML=`<div class="v20-social-identity"><img class="v20-social-avatar" src="${escapeHtml(avatarUrl(peer.avatar_path))}" alt=""><div><strong>${escapeHtml(peer.pseudo||peer.display_name||'Membre')}</strong><span class="v20-social-time">Conversation compte réel</span></div></div><button class="btn btn-secondary btn-small" data-block-peer>Bloquer</button>`;
  title.querySelector('[data-block-peer]')?.addEventListener('click',event=>blockPeer(event.currentTarget,selected).catch(error=>fail(error,'Impossible de bloquer ce compte.')));
  form.hidden=false;
  await messages();
}

async function messages(){
  if(!peer)return;
  const target=peer,version=++requestVersion;
  const current=()=>version===requestVersion&&peer?.user_id===target.user_id;
  const wasLoading=log.getAttribute('aria-busy')==='true';
  const atBottom=wasLoading||log.scrollHeight-log.clientHeight-log.scrollTop<=48;
  const previousTop=log.scrollTop;
  
  let result;
  try{
    result=await getSupabase().from('social_real_messages')
      .select('*')
      .or(`and(sender_user_id.eq.${user.id},recipient_user_id.eq.${target.user_id}),and(sender_user_id.eq.${target.user_id},recipient_user_id.eq.${user.id})`)
      .order('created_at');
  }catch(error){
    if(!current())return;
    log.setAttribute('aria-busy','false');
    if(wasLoading)log.textContent='Impossible de charger la conversation. Sélectionnez le contact pour réessayer.';
    throw error;
  }
  if(!current())return;
  log.setAttribute('aria-busy','false');
  const {data,error}=result;
  if(error){
    if(wasLoading)log.textContent='Impossible de charger la conversation. Sélectionnez le contact pour réessayer.';
    throw error;
  }
  const rows=(Array.isArray(data)?data:[]).filter(message=>((message.sender_user_id===user.id&&message.recipient_user_id===target.user_id)||(message.sender_user_id===target.user_id&&message.recipient_user_id===user.id)));
  log.innerHTML=rows.map(message=>`<div class="v20-bubble ${message.sender_user_id===user.id?'mine':''}" data-message="${escapeHtml(message.id)}">${escapeHtml(message.body)}<time>${escapeHtml(formatDate(message.created_at))}</time>${message.sender_user_id!==user.id?'<button type="button" class="link-button" data-report-message'+(reporting.has(message.id)?' disabled':'')+'>Signaler</button>':''}</div>`).join('')||'<p>Commencez la conversation.</p>';
  log.scrollTop=atBottom?log.scrollHeight:previousTop;

  log.querySelectorAll('[data-report-message]').forEach(button=>button.addEventListener('click',async()=>{
    const element=button.closest('[data-message]');
    const message=rows.find(item=>item.id===element?.dataset.message);
    if(!message||reporting.has(message.id))return;
    reporting.add(message.id);
    try{
      const choice=await requestModeration(button,{mode:'report',contact:target.pseudo||target.display_name||'Membre'});
      if(!choice){reporting.delete(message.id);return;}
      button.disabled=true;
      await reportContent({network:'real',target_type:'message',target_id:message.id,reason:choice.reason,details:choice.details??null,snapshot:{body:message.body,sender_user_id:message.sender_user_id,recipient_user_id:message.recipient_user_id}});
      socialStatus(status,'Message signalé à l’administration.','success');
    }catch(error){
      reporting.delete(message.id);
      button.disabled=false;
      fail(error,'Signalement non confirmé. Vérifiez vos signalements avant de réessayer.');
    }
  }));
  if(current()&&rows.some(message=>message.recipient_user_id===user.id&&!message.read_at)){
    try{
      await markConversationRead('social_real_messages',user.id,{sender_user_id:target.user_id});
      unreadByUser.delete(target.user_id);
      renderContacts();
    }catch(error){
      if(current())throw error;
    }
  }
}

async function blockPeer(button,target){
  if(!target||blocking.has(target.user_id))return;
  blocking.add(target.user_id);
  try{
    const choice=await requestModeration(button,{mode:'block',contact:target.pseudo||target.display_name||'ce membre'});
    if(!choice?.confirmed)return;
    button.disabled=true;
    const {error}=await getSupabase().from('social_blocks').upsert({blocker_user_id:user.id,blocked_user_id:target.user_id},{onConflict:'blocker_user_id,blocked_user_id'});
    if(error)throw error;
    location.href='blocages.html';
  }finally{blocking.delete(target.user_id);button.disabled=false;}
}

(async()=>{
  try{
    user=await requireCommunityUser();
    await Promise.all([loadContacts(),loadUnread()]);
    renderContacts();
    search?.addEventListener('input',renderContacts);

    form.addEventListener('submit',async event=>{
      event.preventDefault();
      if(!peer||sending)return;
      const target=peer,id=target.user_id,raw=composer.value;
      const body=raw.trim();
      if(!body)return;
      sending=true;
      syncSendButton();
      form.setAttribute('aria-busy','true');
      try{
        const {error}=await getSupabase().from('social_real_messages').insert({sender_user_id:user.id,recipient_user_id:target.user_id,body});
        if(error)throw error;
        if(drafts.get(id)===raw)drafts.delete(id);
        if(peer?.user_id===id&&composer.value===raw)composer.value='';
        socialStatus(status,'Message envoyé.','success');
        if(peer?.user_id===id){
          try{await messages()}catch(error){fail(error,'Message envoyé, mais actualisation impossible.');}
        }
      }catch(error){
        fail(error,'Envoi non confirmé. Vérifiez la conversation avant de réessayer. Votre brouillon est conservé.');
      }finally{
        sending=false;
        syncSendButton();
        form.setAttribute('aria-busy','false');
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
