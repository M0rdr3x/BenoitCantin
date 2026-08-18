import {getSupabase,requireUser,escapeHtml,setStatus,roleLabel,formatDate} from './sinjira-supabase.js';

const s=getSupabase();
const status=document.querySelector('[data-library-status]');
const rows=value=>Array.isArray(value)?value:[];

const participantLabel=value=>({
  invited:'Invité',
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
  const canWithdraw=['invited','applied','approved'].includes(participant.status);
  return `<article class="account-game-card" id="${escapeHtml(playtest.id)}">
    <div class="account-game-card-top"><span class="status-badge">${escapeHtml(participantLabel(participant.status))}</span><span>${escapeHtml(playtestLabel(playtest.status))}</span></div>
    <span class="eyebrow">${escapeHtml(playtest.projects?.name||'SINJIRA™')}</span>
    <h2>${escapeHtml(playtest.title)}</h2>
    <p>${escapeHtml(playtest.description||'')}</p>
    <p><strong>Accès requis :</strong> ${escapeHtml(roleLabel(playtest.required_access||'tester'))}<br><strong>Période :</strong> ${escapeHtml(dateRange(playtest))}</p>
    <div class="hero-actions">${playtest.projects?.slug?`<a class="btn btn-secondary" href="/compte/projet.html?slug=${encodeURIComponent(playtest.projects.slug)}">Voir le projet</a>`:''}${canWithdraw?`<button class="btn btn-secondary" type="button" data-withdraw-playtest="${escapeHtml(playtest.id)}">Se retirer du playtest</button>`:''}</div>
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

  const myBox=document.querySelector('[data-my-playtests-list]');
  const openBox=document.querySelector('[data-open-playtests-list]');
  if(myBox)myBox.innerHTML=mine.length
    ? mine.map(item=>myCard(item,participantMap.get(item.id))).join('')
    : '<div class="notice"><strong>Aucune participation enregistrée.</strong><p>Vos candidatures, invitations et anciens playtests apparaîtront ici et resteront visibles après leur fermeture.</p></div>';
  if(openBox)openBox.innerHTML=available.length
    ? available.map(availableCard).join('')
    : '<div class="notice"><strong>Aucun nouveau playtest ouvert pour votre niveau d’accès.</strong></div>';

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
    if(!confirm('Vous retirer de ce playtest? Cette action ne peut pas servir à vous auto-approuver ou à changer un autre statut.'))return;
    button.disabled=true;
    const {error}=await s.from('playtest_participants')
      .update({status:'withdrawn'})
      .eq('playtest_id',button.dataset.withdrawPlaytest)
      .eq('user_id',user.id);
    if(error){
      button.disabled=false;
      setStatus(status,'Le retrait n’a pas pu être enregistré.','error');
      return;
    }
    setStatus(status,'Votre retrait du playtest est enregistré.','success');
    await load(user);
  }));
}

(async()=>{
  if(document.body.dataset.libraryPage!=='playtests-v24-4-64')return;
  const user=await requireUser('/compte/connexion.html');
  await load(user);
})().catch(error=>{
  if(error?.message!=='Connexion requise')setStatus(status,'Impossible de charger les playtests pour le moment.','error');
});
