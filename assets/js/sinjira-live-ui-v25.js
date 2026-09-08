import {getSupabase} from './sinjira-supabase.js';
import {socialErrorMessage} from './sinjira-social-common.js?v=24.4.79';
import {openSocialReport} from './sinjira-social-safety-v24-4-79.js?v=24.4.79';
import {
  executeLiveInput,
  loadLiveInvites,
  loadLiveMessages,
  openLiveRealtimeSession,
  respondLiveInvite
} from './sinjira-live-runtime-v25.js';
import {
  liveCommandHelp,
  livePresenceLabel,
  liveRoomAccessLabel,
  liveUiErrorMessage,
  normalizeLiveInvites,
  normalizeLiveMe,
  normalizeLiveRooms
} from './sinjira-live-ui-model-v25.js';

function node(tag,className,text){
  const el=document.createElement(tag);
  if(className)el.className=className;
  if(text!==undefined&&text!==null)el.textContent=String(text);
  return el;
}

function button(label,className='btn btn-secondary'){
  const el=node('button',className,label);
  el.type='button';
  return el;
}

function formatTime(value){
  const date=new Date(value);
  if(Number.isNaN(date.getTime()))return '';
  return new Intl.DateTimeFormat('fr-CA',{hour:'2-digit',minute:'2-digit'}).format(date);
}

function formatDate(value){
  const date=new Date(value);
  if(Number.isNaN(date.getTime()))return '';
  return new Intl.DateTimeFormat('fr-CA',{dateStyle:'medium',timeStyle:'short'}).format(date);
}

function renderMessage(message,{onReport=()=>{}}={}){
  const article=node('article',`v25-live-message${message?.own?' is-own':''}`);
  article.dataset.messageId=String(message?.id||'');
  const head=node('div','v25-live-message-head');
  const identity=node('div','v25-live-message-identity');
  identity.append(node('strong','',String(message?.author_label||'Membre SINJIRA')));
  const time=node('time','',formatTime(message?.created_at));
  if(message?.created_at)time.dateTime=String(message.created_at);
  identity.append(time);
  head.append(identity);
  if(message?.own!==true){
    const report=button('Signaler','v25-live-message-report');
    report.setAttribute('aria-label',`Signaler le message de ${String(message?.author_label||'ce membre')}`);
    report.addEventListener('click',()=>onReport(message));
    head.append(report);
  }
  const body=node('p','v25-live-message-body',String(message?.body||''));
  article.append(head,body);
  return article;
}

export function createLiveUi(root,{supabase=getSupabase()}={}){
  if(!(root instanceof Element))throw new Error('SOCIAL_LIVE_UI_ROOT_REQUIRED');

  const shell=node('section','v25-live-shell');
  shell.setAttribute('aria-label','En direct SINJIRA');

  const roomsPanel=node('aside','v25-live-rooms');
  roomsPanel.setAttribute('aria-label','Salons En direct');
  const roomsHead=node('div','v25-live-panel-head');
  roomsHead.append(node('span','v25-social-kicker','Salons'),node('p','v25-live-muted','Visibles selon votre compte et vos règles de sécurité.'));
  const roomsList=node('div','v25-live-room-list');
  roomsList.setAttribute('role','list');
  const refreshButton=button('Actualiser les salons','btn btn-secondary btn-small');
  refreshButton.dataset.liveRefresh='';
  roomsPanel.append(roomsHead,roomsList,refreshButton);

  const main=node('section','v25-live-main');
  const liveHead=node('header','v25-live-head');
  const titleWrap=node('div','');
  const title=node('h2','v25-live-title','En direct');
  const access=node('p','v25-live-muted','Aucun salon sélectionné');
  titleWrap.append(title,access);
  const presence=node('span','v25-live-presence',livePresenceLabel(0));
  liveHead.append(titleWrap,presence);

  const status=node('div','v25-live-status-line','Prêt à charger les salons.');
  status.setAttribute('role','status');
  status.setAttribute('aria-live','polite');
  status.setAttribute('aria-atomic','true');

  const log=node('div','v25-live-log');
  log.setAttribute('role','log');
  log.setAttribute('aria-live','polite');
  log.setAttribute('aria-relevant','additions text');
  log.setAttribute('aria-label','Messages du salon');
  log.tabIndex=0;

  const composer=node('form','v25-live-composer');
  const input=document.createElement('textarea');
  input.name='live-input';
  input.maxLength=2000;
  input.rows=2;
  input.placeholder='Écrire un message ou une commande…';
  input.setAttribute('aria-label','Message ou commande En direct');
  const composerMeta=node('div','v25-live-composer-meta');
  const help=node('span','v25-live-help',liveCommandHelp());
  const send=button('Envoyer','btn btn-primary');
  send.type='submit';
  composerMeta.append(help,send);
  composer.append(input,composerMeta);
  main.append(liveHead,status,log,composer);

  const mePanel=node('aside','v25-live-me');
  mePanel.setAttribute('aria-label','Mon état et mes invitations En direct');
  const meKicker=node('span','v25-social-kicker','Mon état');
  const meLabel=node('strong','v25-live-me-label','Membre SINJIRA');
  const meCounts=node('p','v25-live-muted','0 salon créé · 0 salon rejoint');
  const inviteDivider=node('div','v25-live-divider');
  const inviteHead=node('div','v25-live-invite-head');
  inviteHead.append(node('span','v25-social-kicker','Invitations'),node('p','v25-live-muted','Salons privés qui vous sont proposés.'));
  const invitesList=node('div','v25-live-invite-list');
  invitesList.setAttribute('role','list');
  const inviteRefresh=button('Actualiser les invitations','btn btn-secondary btn-small');
  mePanel.append(meKicker,meLabel,meCounts,inviteDivider,inviteHead,invitesList,inviteRefresh);

  shell.append(roomsPanel,main,mePanel);
  root.replaceChildren(shell);

  let rooms=[];
  let invites=[];
  let currentRoom=null;
  let session=null;
  const seenMessageIds=new Set();
  let destroyed=false;

  function setStatus(message,type='info'){
    status.textContent=String(message||'');
    status.dataset.statusType=type;
    status.setAttribute('role',type==='error'?'alert':'status');
    status.setAttribute('aria-live',type==='error'?'assertive':'polite');
  }

  function safeError(error,fallback='Action En direct impossible pour le moment.'){
    return liveUiErrorMessage(error)||socialErrorMessage(error,fallback);
  }

  async function refreshCurrentMessages(){
    if(!currentRoom)return;
    const messages=await loadLiveMessages(currentRoom.roomId,{supabase});
    renderMessages(messages);
  }

  function reportMessage(message){
    if(message?.own===true)return;
    openSocialReport({
      network:'live',
      targetType:'message',
      targetId:String(message?.id||''),
      label:'ce message En direct',
      statusNode:status,
      onDone:async({blocked})=>{
        if(blocked)await refreshCurrentMessages();
      }
    });
  }

  function appendMessage(message,{focus=false}={}){
    const id=String(message?.id||'');
    if(id&&seenMessageIds.has(id))return;
    if(id)seenMessageIds.add(id);
    const element=renderMessage(message,{onReport:reportMessage});
    log.append(element);
    while(log.children.length>120){
      const first=log.firstElementChild;
      if(first?.dataset.messageId)seenMessageIds.delete(first.dataset.messageId);
      first?.remove();
    }
    log.scrollTop=log.scrollHeight;
    if(focus)element.tabIndex=-1;
  }

  function renderMessages(messages){
    seenMessageIds.clear();
    log.replaceChildren();
    const rows=Array.isArray(messages)?messages:[];
    if(!rows.length){
      log.append(node('p','v25-live-empty','Aucun message visible dans ce salon.'));
      return;
    }
    for(const message of rows)appendMessage(message);
  }

  function updateMe(payload){
    const me=normalizeLiveMe(payload);
    meLabel.textContent=me.profileLabel;
    meCounts.textContent=`${me.ownedRooms} salon${me.ownedRooms===1?'':'s'} créé${me.ownedRooms===1?'':'s'} · ${me.joinedRooms} salon${me.joinedRooms===1?'':'s'} rejoint${me.joinedRooms===1?'':'s'}`;
  }

  function renderRooms(){
    roomsList.replaceChildren();
    if(!rooms.length){
      roomsList.append(node('p','v25-live-empty','Aucun salon disponible.'));
      return;
    }
    for(const room of rooms){
      const row=node('div','v25-live-room-row');
      row.setAttribute('role','listitem');
      const open=button(room.name,'v25-live-room-button');
      open.dataset.roomId=room.roomId;
      open.setAttribute('aria-pressed',currentRoom?.roomId===room.roomId?'true':'false');
      const meta=node('span','v25-live-room-meta',`${room.visibility==='private'?'Privé':'Public'}${room.joined?' · rejoint':''}`);
      open.append(meta);
      open.addEventListener('click',()=>openRoom(room).catch(error=>setStatus(safeError(error),'error')));
      row.append(open);
      roomsList.append(row);
    }
  }

  function renderInvites(){
    invitesList.replaceChildren();
    if(!invites.length){
      invitesList.append(node('p','v25-live-empty','Aucune invitation en attente.'));
      return;
    }
    for(const invite of invites){
      const card=node('article','v25-live-invite-card');
      card.setAttribute('role','listitem');
      const name=node('strong','',invite.roomName);
      const from=node('p','v25-live-muted',`Invité par ${invite.inviterLabel}`);
      const expiry=node('p','v25-live-invite-expiry',invite.expiresAt?`Expire ${formatDate(invite.expiresAt)}`:'');
      const actions=node('div','v25-live-invite-actions');
      const accept=button('Accepter','btn btn-primary btn-small');
      const decline=button('Refuser','btn btn-secondary btn-small');
      const respond=async shouldAccept=>{
        accept.disabled=true;decline.disabled=true;
        try{
          const result=await respondLiveInvite(invite.inviteId,shouldAccept,{supabase});
          if(result?.status==='accepted'){
            await Promise.all([refreshRooms(),refreshMe(),refreshInvites()]);
            const roomId=String(result.room_id||invite.roomId);
            const room=rooms.find(item=>item.roomId===roomId);
            if(room)await connectRoom(room);
            else setStatus('Invitation acceptée. Le salon sera visible après actualisation.','success');
          }else if(result?.status==='declined'){
            await refreshInvites();
            setStatus('Invitation refusée.','success');
          }else{
            await refreshInvites();
            setStatus('Cette invitation n’est plus disponible.','error');
          }
        }catch(error){
          setStatus(safeError(error),'error');
        }finally{
          accept.disabled=false;decline.disabled=false;
        }
      };
      accept.addEventListener('click',()=>respond(true));
      decline.addEventListener('click',()=>respond(false));
      actions.append(accept,decline);
      card.append(name,from,expiry,actions);
      invitesList.append(card);
    }
  }

  async function refreshRooms(){
    const result=await executeLiveInput('/rooms',{supabase});
    rooms=normalizeLiveRooms(result.data);
    renderRooms();
    return rooms;
  }

  async function refreshMe(){
    const result=await executeLiveInput('/me',{supabase});
    updateMe(result.data);
  }

  async function refreshInvites(){
    const result=await loadLiveInvites({supabase});
    invites=normalizeLiveInvites(result);
    renderInvites();
    return invites;
  }

  async function closeSession(){
    const old=session;
    session=null;
    if(old)await old.close().catch(()=>{});
    presence.textContent=livePresenceLabel(0);
  }

  async function connectRoom(room){
    await closeSession();
    if(destroyed)return;
    currentRoom=room;
    title.textContent=room.name;
    access.textContent=liveRoomAccessLabel(room);
    renderRooms();
    setStatus('Connexion au salon…');
    const opened=await openLiveRealtimeSession({
      roomId:room.roomId,
      supabase,
      onMessage:message=>appendMessage(message),
      onPresence:event=>{presence.textContent=livePresenceLabel(event?.count);},
      onStatus:event=>{
        if(event?.state==='message_error')setStatus(safeError(event.error,'Un message En direct n’a pas pu être relu.'),'error');
      }
    });
    if(destroyed){await opened.close().catch(()=>{});return;}
    session=opened;
    renderMessages(opened.initialMessages);
    setStatus(`Connecté à #${room.slug}.`,'success');
  }

  async function openRoom(room){
    let target=room;
    if(!room.joined){
      if(room.visibility!=='public'){
        setStatus('Ce salon privé nécessite une invitation acceptée.','error');
        return;
      }
      setStatus(`Adhésion à #${room.slug}…`);
      const joined=await executeLiveInput(`/join ${room.slug}`,{supabase});
      await Promise.all([refreshRooms(),refreshMe()]);
      const roomId=String(joined.data?.room?.room_id||room.roomId);
      target=rooms.find(item=>item.roomId===roomId)||{...room,joined:true};
    }
    await connectRoom(target);
  }

  async function handleResult(result,rawInput){
    if(result?.kind==='message'){
      const empty=log.querySelector('.v25-live-empty');
      empty?.remove();
      appendMessage(result.message);
      setStatus('Message envoyé.','success');
      return;
    }
    const command=String(rawInput||'').trim().split(/\s+/,1)[0].toLowerCase();
    if(command==='/rooms'){
      rooms=normalizeLiveRooms(result.data);
      renderRooms();
      setStatus(`${rooms.length} salon${rooms.length===1?'':'s'} visible${rooms.length===1?'':'s'}.`,'success');
      return;
    }
    if(command==='/me'){
      updateMe(result.data);
      setStatus('Votre état En direct a été actualisé.','success');
      return;
    }
    if(command==='/join'){
      await Promise.all([refreshRooms(),refreshMe()]);
      const roomId=String(result.data?.room?.room_id||'');
      const room=rooms.find(item=>item.roomId===roomId);
      if(room)await connectRoom(room);
      else setStatus('Salon rejoint. Utilisez /rooms pour actualiser la liste.','success');
    }
  }

  composer.addEventListener('submit',async event=>{
    event.preventDefault();
    const raw=input.value;
    if(!String(raw||'').trim())return;
    send.disabled=true;
    try{
      const result=await executeLiveInput(raw,{roomId:currentRoom?.roomId||null,supabase});
      input.value='';
      await handleResult(result,raw);
    }catch(error){
      setStatus(safeError(error),'error');
    }finally{
      send.disabled=false;
      input.focus();
    }
  });

  refreshButton.addEventListener('click',async()=>{
    refreshButton.disabled=true;
    try{
      await Promise.all([refreshRooms(),refreshMe()]);
      setStatus('Salons actualisés.','success');
    }catch(error){setStatus(safeError(error),'error');}
    finally{refreshButton.disabled=false;}
  });

  inviteRefresh.addEventListener('click',async()=>{
    inviteRefresh.disabled=true;
    try{
      await refreshInvites();
      setStatus('Invitations actualisées.','success');
    }catch(error){setStatus(safeError(error),'error');}
    finally{inviteRefresh.disabled=false;}
  });

  const ready=Promise.all([refreshRooms(),refreshMe(),refreshInvites()])
    .then(()=>{setStatus('En direct prêt. Choisissez un salon.','success');})
    .catch(error=>{setStatus(safeError(error),'error');throw error;});

  return {
    ready,
    destroy:async()=>{
      destroyed=true;
      await closeSession();
      root.replaceChildren();
    },
    refresh:async()=>Promise.all([refreshRooms(),refreshMe(),refreshInvites()])
  };
}
