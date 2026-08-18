import {getSupabase,requireUser,escapeHtml,setStatus,roleLabel,formatDate} from './sinjira-supabase.js';

const s=getSupabase();
const status=document.querySelector('[data-library-status]');
const adminStatus=document.querySelector('[data-admin-invite-status]');
const rows=value=>Array.isArray(value)?value:[];

const participantLabel=value=>({
  invited:'Invitation reçue',
  applied:'Candidature envoyée',
  approved:'Participation approuvée',
  refused:'Candidature refusée',
  completed:'Playtest complété',
  withdrawn:'Retiré volontairement'
}[value]||value||'—');

const playtestLabel=value=>({
  draft:'Brouillon',
  open:'Candidatures ouvertes',
  active:'En cours',
  closed:'Fermé',
  archived:'Archivé'
}[value]||value||'—');

const invitationErrorLabel=code=>({
  AUTH_REQUIRED:'Connexion requise.',
  ADMIN_REQUIRED:'Accès administrateur requis.',
  INVALID_ARGUMENT:'Choisissez un playtest et un compte.',
  PLAYTEST_NOT_FOUND:'Ce playtest n’existe plus.',
  PLAYTEST_NOT_INVITABLE:'Ce playtest n’accepte plus d’invitations.',
  SAFETY_PROFILE_REQUIRED:'Ce compte ne peut pas encore être invité : son profil de sécurité doit être complété.',
  ACCOUNT_INACTIVE:'Ce compte n’est pas actif.',
  AGE_INELIGIBLE:'Ce compte n’est pas admissible à ce playtest.',
  GUARDIAN_REQUIRED:'Ce compte jeunesse n’est pas admissible tant que sa supervision requise n’est pas vérifiée.',
  PARTICIPATION_EXISTS:'Ce compte possède déjà une participation active à ce playtest.'
}[code]||'Invitation impossible pour le moment.');

const acceptErrorLabel=code=>({
  AUTH_REQUIRED:'Connexion requise.',
  INVITATION_NOT_FOUND:'Cette invitation n’est plus disponible.',
  PLAYTEST_CLOSED:'Ce playtest est fermé; l’invitation ne peut plus être acceptée.',
  SAFETY_PROFILE_REQUIRED:'Votre profil de sécurité doit être complété avant d’accepter cette invitation.',
  ACCOUNT_INACTIVE:'Votre compte n’est pas actif.',
  AGE_INELIGIBLE:'Votre compte n’est pas admissible à ce playtest.',
  GUARDIAN_REQUIRED:'La supervision requise de votre compte jeunesse doit être vérifiée avant d’accepter.'
}[code]||'Impossible d’accepter cette invitation pour le moment.');

function dateRange(playtest){
  const start=playtest.starts_at?formatDate(playtest.starts_at):'';
  const end=playtest.ends_at?formatDate(playtest.ends_at):'';
  if(start&&end)return `${start} → ${end}`;
  return start||end||'Dates à confirmer';
}

function setCount(selector,value){
  const node=document.querySelector(selector);
  if(node)node.textContent=String(value);
}

function myCard(playtest,participant){
  const invited=participant.status==='invited';
  const canWithdraw=['invited','applied','approved'].includes(participant.status);
  return `<article class="account-game-card" id="${escapeHtml(playtest.id)}">
    <div class="account-game-card-top"><span class="status-badge">${escapeHtml(participantLabel(participant.status))}</span><span>${escapeHtml(playtestLabel(playtest.status))}</span></div>
    <span class="eyebrow">${escapeHtml(playtest.projects?.name||'SINJIRA™')}</span>
    <h2>${escapeHtml(playtest.title)}</h2>
    <p>${escapeHtml(playtest.description||'')}</p>
    <p><strong>Accès requis :</strong> ${escapeHtml(roleLabel(playtest.required_access||'tester'))}<br><strong>Période :</strong> ${escapeHtml(dateRange(playtest))}</p>
    ${invited?'<p><strong>Invitation interne :</strong> vous pouvez l’accepter ou la décliner. L’acceptation attribue l’accès testeur au projet lié, après les contrôles de sécurité serveur.</p>':''}
    <div class="hero-actions">
      ${invited&&['open','active'].includes(playtest.status)?`<button class="btn btn-primary" type="button" data-accept-playtest="${escapeHtml(playtest.id)}">Accepter l’invitation</button>`:''}
      ${playtest.projects?.slug?`<a class="btn btn-secondary" href="/compte/projet.html?slug=${encodeURIComponent(playtest.projects.slug)}">Voir le projet</a>`:''}
      ${canWithdraw?`<button class="btn btn-secondary" type="button" data-withdraw-playtest="${escapeHtml(playtest.id)}">${invited?'Décliner l’invitation':'Se retirer du playtest'}</button>`:''}
    </div>
  </article>`;
}

function availableCard(playtest){
  return `<article class="account-game-card" id="${escapeHtml(playtest.id)}">
    <div class="account-game-card-top"><span class="status-badge">Candidatures ouvertes</span><span>${escapeHtml(playtest.projects?.name||'SINJIRA™')}</span></div>
    <h2>${escapeHtml(playtest.title)}</h2>
    <p>${escapeHtml(playtest.description||'')}</p>
    <p><strong>Accès requis :</strong> ${escapeHtml(roleLabel(playtest.required_access||'tester'))}<br><strong>Période :</strong> ${escapeHtml(dateRange(playtest))}${playtest.max_participants?`<br><strong>Places prévues :</strong> ${Number(playtest.max_participants)}`:''}</p>
    <div class="hero-actions"><button class="btn btn-primary" type="button" data-apply-playtest="${escapeHtml(playtest.id)}">Poser ma candidature</button>${playtest.projects?.slug?`<a class="btn btn-secondary" href="/compte/projet.html?slug=${encodeURIComponent(playtest.projects.slug)}">Voir le projet</a>`:''}</div>
  </article>`;
}

async function loadAdminInvites(user,playtests){
  const panel=document.querySelector('[data-admin-playtest-invites]');
  const form=document.querySelector('[data-admin-invite-form]');
  if(!panel||!form)return;

  const {data:isAdmin,error:adminError}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});
  if(adminError||!isAdmin)return;

  const {data:usersData,error:usersError}=await s.functions.invoke('admin-users',{body:{action:'list_users'}});
  if(usersError||!usersData?.ok){
    panel.hidden=false;
    setStatus(adminStatus,'La liste des comptes n’est pas disponible pour le moment.','error');
    return;
  }

  const invitables=playtests.filter(item=>['open','active'].includes(item.status));
  const users=rows(usersData.users).filter(item=>item.id&&item.id!==user.id);
  const playtestSelect=form.querySelector('[data-admin-invite-playtest]');
  const userSelect=form.querySelector('[data-admin-invite-user]');

  playtestSelect.innerHTML=invitables.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)} · ${escapeHtml(playtestLabel(item.status))}</option>`).join('');
  userSelect.innerHTML=users.map(item=>{
    const label=item.pseudo||item.display_name||item.email||'Compte SINJIRA™';
    const email=item.email&&item.email!==label?` · ${item.email}`:'';
    return `<option value="${escapeHtml(item.id)}">${escapeHtml(label+email)}</option>`;
  }).join('');

  panel.hidden=false;
  const submit=form.querySelector('button[type="submit"]');
  if(submit)submit.disabled=!invitables.length||!users.length;

  if(!form.dataset.bound){
    form.dataset.bound='1';
    form.addEventListener('submit',async event=>{
      event.preventDefault();
      const playtestId=playtestSelect.value;
      const targetUserId=userSelect.value;
      if(!playtestId||!targetUserId){
        setStatus(adminStatus,'Choisissez un playtest et un compte.','error');
        return;
      }
      if(submit)submit.disabled=true;
      const {data,error}=await s.rpc('invite_sinjira_playtest_participant',{
        p_playtest_id:playtestId,
        p_target_user_id:targetUserId
      });
      if(error||!data?.ok){
        if(submit)submit.disabled=false;
        setStatus(adminStatus,invitationErrorLabel(data?.code),'error');
        return;
      }
      setStatus(adminStatus,data.code==='ALREADY_INVITED'?'Ce compte possède déjà cette invitation.':'Invitation interne créée. Le membre la verra dans ses playtests et ses notifications.','success');
      if(submit)submit.disabled=false;
    });
  }
}

async function load(user){
  const [playtestsResult,participantsResult]=await Promise.all([
    s.from('playtests').select('id,title,description,status,starts_at,ends_at,max_participants,required_access,created_at,projects(name,slug)').order('created_at',{ascending:false}),
    s.from('playtest_participants').select('playtest_id,status,created_at,updated_at').eq('user_id',user.id).order('updated_at',{ascending:false})
  ]);
  if(playtestsResult.error)throw playtestsResult.error;
  if(participantsResult.error)throw participantsResult.error;

  const playtests=rows(playtestsResult.data);
  const participants=rows(participantsResult.data);
  const participantMap=new Map(participants.map(item=>[item.playtest_id,item]));
  const mine=playtests.filter(item=>participantMap.has(item.id));
  const available=playtests.filter(item=>item.status==='open'&&!participantMap.has(item.id));

  setCount('[data-playtest-my-count]',mine.length);
  setCount('[data-playtest-open-count]',available.length);
  setCount('[data-playtest-approved-count]',participants.filter(item=>item.status==='approved').length);
  setCount('[data-playtest-invite-count]',participants.filter(item=>item.status==='invited').length);

  const myBox=document.querySelector('[data-my-playtests-list]');
  const openBox=document.querySelector('[data-open-playtests-list]');
  if(myBox)myBox.innerHTML=mine.length
    ? mine.map(item=>myCard(item,participantMap.get(item.id))).join('')
    : '<div class="notice"><strong>Aucune participation enregistrée.</strong><p>Vos candidatures, invitations et anciens playtests apparaîtront ici et resteront visibles après leur fermeture.</p></div>';
  if(openBox)openBox.innerHTML=available.length
    ? available.map(availableCard).join('')
    : '<div class="notice"><strong>Aucun nouveau playtest ouvert pour votre niveau d’accès.</strong></div>';

  document.querySelectorAll('[data-accept-playtest]').forEach(button=>button.addEventListener('click',async()=>{
    button.disabled=true;
    const {data,error}=await s.rpc('accept_sinjira_playtest_invitation',{p_playtest_id:button.dataset.acceptPlaytest});
    if(error||!data?.ok){
      button.disabled=false;
      setStatus(status,acceptErrorLabel(data?.code),'error');
      return;
    }
    setStatus(status,'Invitation acceptée. Votre accès testeur au projet lié est maintenant activé.','success');
    await load(user);
  }));

  document.querySelectorAll('[data-apply-playtest]').forEach(button=>button.addEventListener('click',async()=>{
    const message=prompt('Message de candidature (facultatif).')||'';
    button.disabled=true;
    const {error}=await s.from('playtest_participants').insert({
      playtest_id:button.dataset.applyPlaytest,
      user_id:user.id,
      status:'applied',
      application_message:message.slice(0,1500)
    });
    if(error){
      button.disabled=false;
      setStatus(status,'La candidature n’a pas pu être transmise. Vérifiez que le playtest est encore ouvert et que votre niveau d’accès est suffisant.','error');
      return;
    }
    setStatus(status,'Candidature transmise. Elle n’accorde aucun accès avant approbation.','success');
    await load(user);
  }));

  document.querySelectorAll('[data-withdraw-playtest]').forEach(button=>button.addEventListener('click',async()=>{
    const participant=participantMap.get(button.dataset.withdrawPlaytest);
    const invited=participant?.status==='invited';
    if(!confirm(invited?'Décliner cette invitation au playtest?':'Vous retirer de ce playtest? Cette action ne peut pas servir à vous auto-approuver ou à changer un autre statut.'))return;
    button.disabled=true;
    const {error}=await s.from('playtest_participants')
      .update({status:'withdrawn'})
      .eq('playtest_id',button.dataset.withdrawPlaytest)
      .eq('user_id',user.id);
    if(error){
      button.disabled=false;
      setStatus(status,invited?'L’invitation n’a pas pu être déclinée.':'Le retrait n’a pas pu être enregistré.','error');
      return;
    }
    setStatus(status,invited?'Invitation déclinée.':'Votre retrait du playtest est enregistré.','success');
    await load(user);
  }));

  await loadAdminInvites(user,playtests);
}

(async()=>{
  if(document.body.dataset.libraryPage!=='playtests-v24-4-65')return;
  const user=await requireUser('/compte/connexion.html');
  await load(user);
})().catch(error=>{
  if(error?.message!=='Connexion requise')setStatus(status,'Impossible de charger les playtests pour le moment.','error');
});
