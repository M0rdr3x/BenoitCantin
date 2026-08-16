import {getSupabase,requireCommunityUser,escapeHtml,formatDate,reportContent,socialStatus} from './sinjira-social-common.js';

const contacts=document.querySelector('[data-contact-list]');
const search=document.querySelector('[data-contact-search]');
const log=document.querySelector('[data-chat-log]');
const form=document.querySelector('[data-chat-form]');
const title=document.querySelector('[data-chat-title]');
const status=document.querySelector('[data-social-status]');
const lock=document.querySelector('[data-character-message-lock]');
const shell=document.querySelector('.v20-message-shell');
let user,me,all=[],peer=null;

function portrait(profile={}){
  const path=String(profile.portrait_path||'').trim();
  return path.startsWith('/')?path:'/assets/media/sinjira-emblem.webp';
}

function fail(message){socialStatus(status,message,'error')}

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
  renderContacts();
}

function renderContacts(){
  const q=String(search?.value||'').trim().toLowerCase();
  const rows=all.filter(item=>String(item.public_name||'').toLowerCase().includes(q));
  contacts.innerHTML=rows.map(item=>`<button class="v20-contact character" data-character="${escapeHtml(item.character_id)}"><img src="${escapeHtml(portrait(item))}" alt=""><span><strong>${escapeHtml(item.public_name||'Personnage')}</strong><small>Personnage SINJIRA</small></span></button>`).join('')||'<p>Aucun personnage disponible.</p>';
  contacts.querySelectorAll('[data-character]').forEach(button=>{
    button.addEventListener('click',()=>openPeer(button.dataset.character));
  });
}

async function openPeer(id){
  peer=all.find(item=>item.character_id===id)||null;
  if(!peer)return;
  history.replaceState({},'',`?character=${encodeURIComponent(id)}`);
  title.innerHTML=`<div class="v20-social-identity"><img class="v20-social-avatar character" src="${escapeHtml(portrait(peer))}" alt=""><div><strong>${escapeHtml(peer.public_name)}</strong><span class="v20-social-time">Conversation personnage · rôle-play</span></div></div>`;
  form.hidden=false;
  await messages();
}

async function messages(){
  if(!peer)return;
  const s=getSupabase();
  const {data,error}=await s.from('social_character_messages')
    .select('*')
    .or(`and(sender_character_id.eq.${me.character_id},recipient_character_id.eq.${peer.character_id}),and(sender_character_id.eq.${peer.character_id},recipient_character_id.eq.${me.character_id})`)
    .order('created_at');
  if(error)throw error;
  const rows=Array.isArray(data)?data:[];
  log.innerHTML=rows.map(message=>`<div class="v20-bubble character ${message.sender_user_id===user.id?'mine':''}" data-message="${message.id}">${escapeHtml(message.body)}<time>${escapeHtml(formatDate(message.created_at))}</time>${message.sender_user_id!==user.id?'<button class="link-button" data-report-message>Signaler</button>':''}</div>`).join('')||'<p>Commencez le rôle-play. Les échanges ici ne modifient pas le canon officiel.</p>';
  log.scrollTop=log.scrollHeight;
  log.querySelectorAll('[data-report-message]').forEach(button=>button.addEventListener('click',async()=>{
    const element=button.closest('[data-message]');
    const message=rows.find(item=>item.id===element?.dataset.message);
    if(!message)return;
    const reason=prompt('Pourquoi signalez-vous ce message de rôle-play?');
    if(!reason)return;
    try{
      await reportContent({network:'character',target_type:'message',target_id:message.id,reason,snapshot:{body:message.body,sender_character_id:message.sender_character_id,recipient_character_id:message.recipient_character_id}});
      alert('Message signalé à l’administration.');
    }catch(error){fail(error?.message||'Signalement impossible.');}
  }));
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
    await loadContacts();
    search?.addEventListener('input',renderContacts);

    form.addEventListener('submit',async event=>{
      event.preventDefault();
      if(!peer)return;
      const body=String(new FormData(form).get('body')||'').trim();
      if(!body)return;
      const button=form.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      const {error}=await getSupabase().from('social_character_messages').insert({
        sender_user_id:user.id,
        recipient_user_id:peer.user_id,
        sender_character_id:me.character_id,
        recipient_character_id:peer.character_id,
        body
      });
      if(button)button.disabled=false;
      if(error)return fail(error.message);
      form.reset();
      await messages();
    });

    getSupabase().channel(`character-messages-${user.id}`)
      .on('postgres_changes',{event:'INSERT',schema:'public',table:'social_character_messages'},payload=>{
        const message=payload.new;
        if(peer&&((message.sender_character_id===me.character_id&&message.recipient_character_id===peer.character_id)||(message.sender_character_id===peer.character_id&&message.recipient_character_id===me.character_id)))messages().catch(error=>fail(error.message));
      })
      .subscribe();

    const requested=new URLSearchParams(location.search).get('character');
    if(requested&&all.some(item=>item.character_id===requested))await openPeer(requested);
    socialStatus(status,'Messagerie personnage prête · V24.4.20.','success');
  }catch(error){
    console.error('[SINJIRA messages personnage]',error);
    if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise')fail(error?.message||'Erreur de messagerie personnage.');
  }
})();
