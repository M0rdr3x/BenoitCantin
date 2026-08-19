import {getSupabase,escapeHtml} from './sinjira-supabase.js';

const s=getSupabase();
const connectionsBox=document.querySelector('[data-dating-connections]');
const conversationZone=document.querySelector('[data-dating-conversation-zone]');
const statusLabel=document.querySelector('[data-dating-status-label]');
const THRESHOLD=10;
const prompts=[
  'Qu’est-ce qui compte le plus pour toi pour construire une relation durable?',
  'Quand un désaccord arrive, qu’est-ce qui t’aide à garder une discussion respectueuse?',
  'À quoi ressemble pour toi une semaine équilibrée entre travail, proches et temps personnel?',
  'Quel projet de vie aimerais-tu pouvoir construire à deux sans perdre ton autonomie?',
  'Quelle qualité relationnelle te fait sentir réellement écouté ou écoutée?',
  'Qu’est-ce qui te donne confiance progressivement chez une personne?',
  'Quelle place la famille, les amis et les passions occupent-ils dans ta vie?',
  'Après cette conversation, qu’est-ce qui te donne envie de continuer à découvrir l’autre personne?'
];
let lastOverview=[];
let openedConnection=null;
let refreshTimer=null;
let refreshing=false;
let promptIndex=0;
let connectionsObserver=null;

const clampCount=value=>Math.max(0,Number(value||0));
const percent=value=>Math.min(100,Math.round((clampCount(value)/THRESHOLD)*100));
const escapeSelector=value=>globalThis.CSS?.escape?CSS.escape(String(value)):String(value).replace(/[^a-zA-Z0-9_-]/g,'\\$&');

function stageFor(row){
  if(row.identity_revealed)return 3;
  const mine=clampCount(row.my_message_count);const theirs=clampCount(row.their_message_count);
  if(mine>=THRESHOLD&&theirs>=THRESHOLD)return 2;
  if(mine>=5&&theirs>=5)return 1;
  return 0;
}

function progressPanel(row){
  const mine=clampCount(row.my_message_count);const theirs=clampCount(row.their_message_count);const stage=stageFor(row);
  const stageLabels=['Découverte','Approfondissement','Dévoilement possible','Identité dévoilée'];
  let note='Les premières conversations restent anonymes. Le but est de découvrir la personne avant son apparence.';
  if(stage===1)note='Vous avez dépassé les premiers échanges. Continuez sur les valeurs, les projets et la façon de communiquer.';
  if(stage===2&&!row.my_photo_consent)note='Le minimum 10 + 10 est atteint. Le dévoilement reste facultatif : votre identité ne sera montrée que si les deux personnes consentent.';
  if(stage===2&&row.my_photo_consent&&!row.identity_revealed)note='Votre consentement est enregistré. L’identité reste cachée tant que l’autre personne n’a pas aussi accepté.';
  if(stage===3)note='Le dévoilement mutuel est actif. Seuls le pseudo et la photo de profil existante sont révélés; aucune galerie privée n’est ouverte automatiquement.';
  return `<div class="dating-progress-panel" data-dating-progress-panel><div class="dating-progress-head"><strong>${escapeHtml(stageLabels[stage])}</strong><span>Minimum avant dévoilement : ${THRESHOLD} messages chacun</span></div><div class="dating-progress-grid"><div class="dating-progress-item"><small><span>Vous</span><strong>${mine}/${THRESHOLD}</strong></small><div class="dating-progress-track" role="progressbar" aria-label="Vos messages avant dévoilement" aria-valuemin="0" aria-valuemax="${THRESHOLD}" aria-valuenow="${Math.min(mine,THRESHOLD)}"><span class="dating-progress-fill" style="--dating-progress:${percent(mine)}%"></span></div></div><div class="dating-progress-item"><small><span>Autre personne</span><strong>${theirs}/${THRESHOLD}</strong></small><div class="dating-progress-track" role="progressbar" aria-label="Messages de l’autre personne avant dévoilement" aria-valuemin="0" aria-valuemax="${THRESHOLD}" aria-valuenow="${Math.min(theirs,THRESHOLD)}"><span class="dating-progress-fill" style="--dating-progress:${percent(theirs)}%"></span></div></div></div><div class="dating-stage-list">${stageLabels.map((label,index)=>`<div class="dating-stage ${index<stage?'is-done':index===stage?'is-current':''}">${index+1}. ${escapeHtml(label)}</div>`).join('')}</div><p class="dating-reveal-note">${escapeHtml(note)}</p></div>`;
}

function observeConnections(){
  if(!connectionsBox)return;
  if(!connectionsObserver)connectionsObserver=new MutationObserver(scheduleRefresh);
  connectionsObserver.observe(connectionsBox,{childList:true,subtree:true});
}

function decorateCards(){
  if(!connectionsBox)return;
  connectionsObserver?.disconnect();
  try{
    for(const row of lastOverview){
      const card=connectionsBox.querySelector(`[data-dating-connection="${escapeSelector(row.connection_id)}"]`);
      if(!card)continue;
      card.querySelector('[data-dating-progress-panel]')?.remove();
      const actions=card.querySelector('.hero-actions');
      if(actions)actions.insertAdjacentHTML('beforebegin',progressPanel(row));
      else card.insertAdjacentHTML('beforeend',progressPanel(row));
    }
  }finally{observeConnections();}
}

function ensurePromptBox(){
  if(!conversationZone||conversationZone.hidden)return;
  let box=conversationZone.querySelector('[data-dating-prompt-box]');
  if(!box){
    const messages=conversationZone.querySelector('[data-dating-conversation-messages]');
    if(!messages)return;
    box=document.createElement('div');box.className='dating-prompt-box';box.dataset.datingPromptBox='';
    box.innerHTML='<div><strong>Question pour aller au-delà de l’apparence</strong><p data-dating-prompt></p></div><button class="btn btn-secondary btn-small" type="button" data-dating-next-prompt>Autre question</button>';
    messages.before(box);
    box.querySelector('[data-dating-next-prompt]')?.addEventListener('click',()=>{promptIndex=(promptIndex+1)%prompts.length;renderPrompt();});
  }
  renderPrompt();
}

function renderPrompt(){
  const node=conversationZone?.querySelector('[data-dating-prompt]');if(!node)return;
  const row=lastOverview.find(item=>item.connection_id===openedConnection);const stage=row?stageFor(row):0;
  const offset=stage===0?0:stage===1?2:stage===2?5:7;
  node.textContent=prompts[(offset+promptIndex)%prompts.length];
}

async function decorateStatus(){
  if(!statusLabel)return;
  const {data,error}=await s.rpc('dating_self_status');if(error||!data?.eligible||!data.single_confirmed_at)return;
  const confirmed=new Date(data.single_confirmed_at);const expires=new Date(confirmed.getTime()+90*86400000);const days=Math.max(0,Math.ceil((expires-Date.now())/86400000));
  const strip=statusLabel.closest('.account-welcome-strip');if(!strip)return;
  let node=strip.querySelector('[data-dating-expiry]');if(!node){node=document.createElement('span');node.className='dating-expiry';node.dataset.datingExpiry='';strip.append(node);}
  node.textContent=days>1?`Confirmation à renouveler dans ${days} jours`:days===1?'Confirmation à renouveler demain':'Confirmation à renouveler aujourd’hui';
}

async function refreshOverview(){
  if(refreshing)return;refreshing=true;
  try{const {data=[],error}=await s.rpc('dating_connections_overview');if(error)return;lastOverview=data;decorateCards();ensurePromptBox();await decorateStatus();}
  finally{refreshing=false;}
}

function scheduleRefresh(){clearTimeout(refreshTimer);refreshTimer=setTimeout(()=>refreshOverview().catch(()=>{}),120);}

connectionsBox?.addEventListener('click',event=>{
  const button=event.target.closest('[data-dating-open]');if(!button)return;
  openedConnection=button.closest('[data-dating-connection]')?.dataset.datingConnection||null;promptIndex=0;setTimeout(()=>{ensurePromptBox();scheduleRefresh();},180);
});

observeConnections();
if(conversationZone)new MutationObserver(()=>{if(!conversationZone.hidden){ensurePromptBox();scheduleRefresh();}}).observe(conversationZone,{attributes:true,attributeFilter:['hidden']});

document.addEventListener('visibilitychange',()=>{if(!document.hidden)scheduleRefresh();});
setInterval(()=>{if(!document.hidden)scheduleRefresh();},30000);
scheduleRefresh();