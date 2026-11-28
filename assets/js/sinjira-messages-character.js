import {getSupabase,requireCommunityUser,escapeHtml,formatDate,reportContent,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';
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
const lock=document.querySelector('[data-character-message-lock]');
const shell=document.querySelector('.v20-message-shell');
let user,me,all=[],peer=null,channel=null,unreadByCharacter=new Map();
let conversationVersion=0,requestVersion=0,sending=false;
// Brouillons propres à chaque conversation, en mémoire de cet onglet uniquement.
const drafts=new Map();
const composer=form.querySelector('textarea[name="body"]');
function rememberDraft(){
  if(!peer)return;
  if(composer.value)drafts.set(peer.character_id,composer.value);
  else drafts.delete(peer.character_id);
}

function portrait(profile={}){
  const path=String(profile.portrait_path||'').trim();
  return path.startsWith('/')?path:'/assets/media/sinjira-emblem.webp';
}

function fail(error,fallback='Action impossible dans la messagerie personnage.'){
  socialErrorStatus(status,error,fallback);
}

async function getMyCharacter(){
  const {data,error}=await getSupabase()
    .from('character_social_profiles')
    .select('character_id,user_id,public_name,public_description,portrait_path,status')
    .eq('user_id',user.id)
    .maybeSingle();
  if(error)throw error;
  return data||null;
}

async function repairOwnerIfNeeded(){
  if(String(user?.email||'').trim().toLowerCase()!=='kingtyrano@gmail.com')return false;
  const {data,error}=await getSupabase().rpc('ensure_sinjira_owner_character');
  if(error)throw error;
  return data?.ok===true;
}

async function loadContacts(){
  const {data,error}=await getSupabase()
    .from('character_social_profiles')
    .select('character_id,user_id,public_name,portrait_path,status')
    .neq('user_id',user.id)
    .order('public_name');
  if(error)throw error;
  all=Array.isArray(data)?data:[];
}

async function loadUnread(){
  unreadByCharacter=await unreadCounts('social_character_messages',user.id,'sender_character_id');
}

function renderContacts(){
  const q=String(search?.value||'').trim().toLowerCase();
  const rows=all.filter(item=>String(item.public_name||'').toLowerCase().includes(q));
  contacts.innerHTML=rows.map(item=>{
    const unread=unreadByCharacter.get(item.character_id)||0;
    const unreadLabel=unread?` · ${unread} non lu${unread>1?'s':''}`:'';
    return `<button class="v20-contact character" data-character="${escapeHtml(item.character_id)}" aria-current="${peer?.character_id===item.character_id?'true':'false'}"><img src="${escapeHtml(portrait(item))}" alt=""><span><strong>${escapeHtml(item.public_name||'Personnage')}</strong><small>Personnage SINJIRA${unreadLabel}</small></span></button>`;
  }).join('')||'<p>Aucun personnage disponible.</p>';
  contacts.querySelectorAll('[data-character]').forEach(button=>{
    button.addEventListener('click',()=>openPeer(button.dataset.character).catch(error=>fail(error,'Impossible d’ouvrir cette conversation.')));
  });
}

async function openPeer(id){
  if(sending){socialStatus(status,'Envoi en cours. Attendez sa confirmation avant de changer de conversation.','info');return;}
  const next=all.find(item=>item.character_id===id);
  if(!next)return;
  if(peer?.character_id===id){await messages();return;}
  rememberDraft();
  peer=next;
  composer.value=drafts.get(id)||'';
  conversationVersion++;
  log.textContent='Chargement de la conversation…';
  log.setAttribute('aria-busy','true');
  log.scrollTop=0;
  renderContacts();
  history.replaceState({},'',`?character=${encodeURIComponent(id)}`);
  title.innerHTML=`<div class="v20-social-identity"><img class="v20-social-avatar character" src="${escapeHtml(portrait(peer))}" alt=""><div><strong>${escapeHtml(peer.public_name)}</strong><span class="v20-social-time">Conversation personnage · rôle-play</span></div></div>`;
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
  const s=getSupabase();
  result=await s.from('social_character_messages')
    .select('*')
    .or(`and(sender_character_id.eq.${me.character_id},recipient_character_id.eq.${peer.character_id}),and(sender_character_id.eq.${peer.character_id},recipient_character_id.eq.${me.character_id})`)
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
  const rows=(Array.isArray(data)?data:[]).filter(message=>((message.sender_character_id===me.character_id&&message.recipient_character_id===selected.character_id&&message.sender_user_id===user.id&&message.recipient_user_id===selected.user_id)||(message.sender_character_id===selected.character_id&&message.recipient_character_id===me.character_id&&message.sender_user_id===selected.user_id&&message.recipient_user_id===user.id)));
  log.innerHTML=rows.map(message=>`<div class="v20-bubble character ${message.sender_user_id===user.id?'mine':''}" data-message="${escapeHtml(message.id)}">${escapeHtml(message.body)}<time>${escapeHtml(formatDate(message.created_at))}</time>${message.sender_user_id!==user.id?'<button type="button" class="link-button" data-report-message>Signaler</button>':''}</div>`).join('')||'<p>Commencez le rôle-play. Les échanges ici ne modifient pas le canon officiel.</p>';
  if(nearBottom)log.scrollTop=log.scrollHeight;
  else log.scrollTop=previousTop;

  syncReportControls();
  log.querySelectorAll('[data-report-message]').forEach(button=>button.addEventListener('click',async()=>{
    const message=rows.find(item=>String(item.id)===button.closest('[data-message]')?.dataset.message);
    if(!message||message.sender_user_id===user.id||reporting.has(String(message.id)))return;
    const id=String(message.id);
    reporting.add(id);
    try{
      const choice=await requestModeration(button,{mode:'report',contact:selected.public_name||'Personnage'});
      if(!choice||peer?.character_id!==selected.character_id)return;
      syncReportControls();
      const result=await reportContent({network:'character',target_type:'message',target_id:message.id,reason:choice.reason,details:choice.details??null});
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
    await markConversationRead('social_character_messages',user.id,{sender_character_id:selected.character_id});
    if(version!==conversationVersion||request!==requestVersion)return;
    unreadByCharacter.delete(selected.character_id);
    renderContacts();
  }
}

function showLocked(owner){
  if(shell)shell.hidden=true;
  if(lock){
    lock.hidden=false;
    lock.innerHTML=owner
      ?'<div class="v20-character-lock"><h2>Synchronisation AbyssTime interrompue</h2><p>La réparation automatique V24.4.20 n’a pas pu confirmer le profil social de votre personnage. Rechargez la page; si le problème persiste, les contrôles de production le signaleront.</p><a class="btn btn-primary" href="mon-personnage.html">Voir Mon personnage</a></div>'
      :'<div class="v20-character-lock"><h2>Messagerie personnage verrouillée</h2><p>Votre unique personnage doit d’abord être approuvé et visible.</p><a class="btn btn-primary" href="mon-personnage.html">Voir Mon personnage</a></div>';
  }
}

(async()=>{
  try{
    user=await requireCommunityUser();
    const owner=String(user?.email||'').trim().toLowerCase()==='kingtyrano@gmail.com';
    me=await getMyCharacter();
    if(!me&&owner){
      const repaired=await repairOwnerIfNeeded();
      if(repaired)me=await getMyCharacter();
    }
    if(!me){showLocked(owner);return;}

    if(shell)shell.hidden=false;
    if(lock)lock.hidden=true;
    await Promise.all([loadContacts(),loadUnread()]);
    renderContacts();
    search?.addEventListener('input',renderContacts);

    form.addEventListener('submit',async event=>{
      event.preventDefault();
      if(!peer||sending)return;
      const body=String(new FormData(form).get('body')||'').trim();
      if(!body)return;
      const button=form.querySelector('button[type="submit"]');
      sending=true;
      if(button)button.disabled=true;
      const draft=form.querySelector('textarea');
      if(draft)draft.readOnly=true;
      form.setAttribute('aria-busy','true');
      try{
        const {error}=await getSupabase().from('social_character_messages').insert({
          sender_user_id:user.id,
          recipient_user_id:peer.user_id,
          sender_character_id:me.character_id,
          recipient_character_id:peer.character_id,
          body
        });
        if(error)return fail(error,'Impossible d’envoyer ce message personnage.');
        drafts.delete(peer.character_id);
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

    channel=getSupabase().channel(`character-messages-${user.id}`)
      .on('postgres_changes',{event:'INSERT',schema:'public',table:'social_character_messages'},payload=>{
        const message=payload.new;
        const currentPeer=peer?.character_id;
        const belongsToOpenPeer=currentPeer&&((message.sender_character_id===me.character_id&&message.recipient_character_id===currentPeer)||(message.sender_character_id===currentPeer&&message.recipient_character_id===me.character_id));
        if(belongsToOpenPeer){
          messages().catch(error=>fail(error,'Impossible d’actualiser la conversation.'));
        }else if(message.recipient_user_id===user.id){
          loadUnread().then(renderContacts).catch(error=>fail(error,'Impossible d’actualiser les messages non lus.'));
        }
      })
      .subscribe();

    const requested=new URLSearchParams(location.search).get('character');
    if(requested&&all.some(item=>item.character_id===requested))await openPeer(requested);
    socialStatus(status,`Messagerie personnage prête · V${UI_VERSION}.`,'success');
  }catch(error){
    if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise'){
      fail(error,'La messagerie personnage n’a pas pu terminer sa vérification.');
    }
  }
})();
