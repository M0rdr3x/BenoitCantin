import {getSupabase,requireCommunityUser,escapeHtml,formatDate,avatarUrl,reportContent,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';
import {unreadCounts,markConversationRead} from './sinjira-message-read-state.js?v=24.4.71';

import {requestModeration} from './sinjira-message-moderation-dialog.mjs?v=1.0.0';

const UI_VERSION='24.4.75';
const reporting=new Set();
function syncReportControls(){
  for(const bubble of log.querySelectorAll('[data-message]')){
    const control=bubble.querySelector('[data-report-message]');
    if(control)control.disabled=reporting.has(bubble.dataset.message);
  }
}
const contacts=document.querySelector('[data-contact-list]');
const search=document.querySelector('[data-contact-search]');
const log=document.querySelector('[data-chat-log]');
const form=document.querySelector('[data-chat-form]');
const title=document.querySelector('[data-chat-title]');
const status=document.querySelector('[data-social-status]');
let user,all=[],peer=null,channel=null,unreadByUser=new Map();
let conversationVersion=0,requestVersion=0,sending=false,blocking=false;
// Brouillons propres à chaque conversation, en mémoire de cet onglet uniquement.
const drafts=new Map();
const composer=form.querySelector('textarea[name="body"]');
function rememberDraft(){
  if(!peer)return;
  if(composer.value)drafts.set(peer.user_id,composer.value);
  else drafts.delete(peer.user_id);
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
      return `<button class="v20-contact" data-user="${escapeHtml(item.user_id)}" aria-current="${peer?.user_id===item.user_id?'true':'false'}"><img src="${escapeHtml(avatarUrl(item.avatar_path))}" alt=""><span><strong>${escapeHtml(item.pseudo||item.display_name||'Membre')}</strong><small>Compte réel${unreadLabel}</small></span></button>`;
    })
    .join('')||'<p>Aucun membre trouvé.</p>';
  contacts.querySelectorAll('[data-user]').forEach(button=>{
    button.addEventListener('click',()=>openPeer(button.dataset.user).catch(error=>fail(error,'Impossible d’ouvrir cette conversation.')));
  });
}

async function openPeer(id){
  if(blocking)return;
  if(sending){socialStatus(status,'Envoi en cours. Attendez sa confirmation avant de changer de conversation.','info');return;}
  const next=all.find(item=>item.user_id===id);
  if(!next)return;
  if(peer?.user_id===id){await messages();return;}
  rememberDraft();
  peer=next;
  composer.value=drafts.get(id)||'';
  conversationVersion++;
  log.textContent='Chargement de la conversation…';
  log.setAttribute('aria-busy','true');
  log.scrollTop=0;
  renderContacts();
  history.replaceState({},'',`?user=${encodeURIComponent(id)}`);
  title.innerHTML=`<div class="v20-social-identity"><img class="v20-social-avatar" src="${escapeHtml(avatarUrl(peer.avatar_path))}" alt=""><div><strong>${escapeHtml(peer.pseudo||peer.display_name||'Membre')}</strong><span class="v20-social-time">Conversation compte réel</span></div></div><button class="btn btn-secondary btn-small" data-block-peer>Bloquer</button>`;
  title.querySelector('[data-block-peer]')?.addEventListener('click',event=>blockPeer(event.currentTarget,next).catch(error=>fail(error,'Blocage non confirmé. Vérifiez vos blocages avant de réessayer.')));
  form.hidden=false;
  await messages();
}

async function messages(){
  if(!peer)return;
  const version=conversationVersion,request=++requestVersion;
  const selected=peer;
  const nearBottom=log.getAttribute('aria-busy')==='true'||log.scrollHeight-log.scrollTop-log.clientHeight<64;
  const previousTop=log.scrollTop;
  let result;
  try{
  result=await getSupabase().from('social_real_messages')
    .select('*')
    .or(`and(sender_user_id.eq.${user.id},recipient_user_id.eq.${peer.user_id}),and(sender_user_id.eq.${peer.user_id},recipient_user_id.eq.${user.id})`)
    .order('created_at');
  }catch(error){
    if(version!==conversationVersion||request!==requestVersion)return;
    log.setAttribute('aria-busy','false');
    if(log.textContent==='Chargement de la conversation…')log.textContent='Chargement impossible. Sélectionnez de nouveau cette conversation pour réessayer.';
    throw error;
  }
  if(version!==conversationVersion||request!==requestVersion)return;
  log.setAttribute('aria-busy','false');
  const {data,error}=result;
  if(error){
    if(log.textContent==='Chargement de la conversation…')log.textContent='Chargement impossible. Sélectionnez de nouveau cette conversation pour réessayer.';
    throw error;
  }
  const rows=(Array.isArray(data)?data:[]).filter(message=>((message.sender_user_id===user.id&&message.recipient_user_id===selected.user_id)||(message.sender_user_id===selected.user_id&&message.recipient_user_id===user.id)));
  log.innerHTML=rows.map(message=>`<div class="v20-bubble ${message.sender_user_id===user.id?'mine':''}" data-message="${escapeHtml(message.id)}">${escapeHtml(message.body)}<time>${escapeHtml(formatDate(message.created_at))}</time>${message.sender_user_id!==user.id?'<button type="button" class="link-button" data-report-message>Signaler</button>':''}</div>`).join('')||'<p>Commencez la conversation.</p>';
  if(nearBottom)log.scrollTop=log.scrollHeight;
  else log.scrollTop=previousTop;

  syncReportControls();
  log.querySelectorAll('[data-report-message]').forEach(button=>button.addEventListener('click',async()=>{
    const message=rows.find(item=>String(item.id)===button.closest('[data-message]')?.dataset.message);
    if(!message||message.sender_user_id===user.id||reporting.has(String(message.id)))return;
    const id=String(message.id);
    reporting.add(id);
    try{
      const choice=await requestModeration(button,{mode:'report',contact:selected.pseudo||selected.display_name||'Membre'});
      if(!choice||peer?.user_id!==selected.user_id)return;
      syncReportControls();
      const result=await reportContent({network:'real',target_type:'message',target_id:message.id,reason:choice.reason,details:choice.details??null});
      if(result?.ok===false)throw Error('REPORT_UNCONFIRMED');
      socialStatus(status,'Signalement transmis à la modération.','success');
    }catch(error){
      fail(error,'Signalement non confirmé. Vérifiez vos signalements avant de réessayer.');
    }finally{
      reporting.delete(id);
      syncReportControls();
    }
  }));
  // Les commandes de signalement restent actives même si l’état lu échoue.
  if(rows.some(message=>message.recipient_user_id===user.id&&!message.read_at)){
    await markConversationRead('social_real_messages',user.id,{sender_user_id:selected.user_id});
    if(version!==conversationVersion||request!==requestVersion)return;
    unreadByUser.delete(selected.user_id);
    renderContacts();
  }
}

async function blockPeer(button,target){
  if(!target||blocking||sending)return;
  blocking=true;
  try{
    const choice=await requestModeration(button,{mode:'block',contact:target.pseudo||target.display_name||'ce membre'});
    if(!choice?.confirmed||peer?.user_id!==target.user_id)return;
    button.disabled=true;
    const {error}=await getSupabase().from('social_blocks').upsert({blocker_user_id:user.id,blocked_user_id:target.user_id},{onConflict:'blocker_user_id,blocked_user_id'});
    if(error!==null)throw error||Error('BLOCK_UNCONFIRMED');
    location.href='blocages.html';
  }finally{
    blocking=false;
    button.disabled=false;
  }
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
      if(blocking)return;
      const body=String(new FormData(form).get('body')||'').trim();
      if(!body)return;
      const button=form.querySelector('button[type="submit"]');
      sending=true;
      if(button)button.disabled=true;
      const draft=form.querySelector('textarea');
      if(draft)draft.readOnly=true;
      form.setAttribute('aria-busy','true');
      try{
        const {error}=await getSupabase().from('social_real_messages').insert({sender_user_id:user.id,recipient_user_id:peer.user_id,body});
        if(error)return fail(error,'Impossible d’envoyer ce message.');
        drafts.delete(peer.user_id);
        form.reset();
        try{await messages();socialStatus(status,'Message envoyé.','success');}catch(error){socialStatus(status,'Message envoyé, mais actualisation impossible.','error');}
      }catch(error){
        fail(error,'Envoi non confirmé. Vérifiez la conversation avant de réessayer. Votre brouillon est conservé.');
      }finally{
        sending=false;
        form.setAttribute('aria-busy','false');
        if(draft)draft.readOnly=false;
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
