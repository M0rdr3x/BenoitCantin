import {getSupabase} from './sinjira-supabase.js';
import {listMyLiveInvites,respondToLiveInvite} from './sinjira-live-invites-client-v25.js';

function node(tag,className,text){
  const el=document.createElement(tag);
  if(className)el.className=className;
  if(text!==undefined&&text!==null)el.textContent=String(text);
  return el;
}

function button(label,className='btn btn-secondary btn-small'){
  const el=node('button',className,label);
  el.type='button';
  return el;
}

function formatDate(value){
  const date=new Date(value);
  if(Number.isNaN(date.getTime()))return '';
  return new Intl.DateTimeFormat('fr-CA',{dateStyle:'medium',timeStyle:'short'}).format(date);
}

export function createLiveInvitesUi(root,{supabase=getSupabase(),onAccepted=()=>{}}={}){
  if(!(root instanceof Element))throw new Error('SOCIAL_LIVE_INVITES_UI_ROOT_REQUIRED');

  const shell=node('section','v25-live-invites-shell');
  shell.setAttribute('aria-label','Invitations privées En direct');
  const head=node('div','v25-live-invites-head');
  head.append(
    node('span','v25-social-kicker','Accès privé'),
    node('h2','v25-live-invites-title','Invitations reçues'),
    node('p','v25-live-muted','Seules vos invitations privées encore valides sont affichées. Aucun identifiant technique de la personne qui invite n’est montré.')
  );

  const status=node('div','v25-live-invites-status','Chargement…');
  status.setAttribute('role','status');
  status.setAttribute('aria-live','polite');
  status.setAttribute('aria-atomic','true');

  const listHead=node('div','v25-live-invites-list-head');
  listHead.append(node('h3','v25-live-invites-subtitle','En attente'));
  const refreshButton=button('Actualiser');
  listHead.append(refreshButton);

  const list=node('div','v25-live-invites-list');
  list.setAttribute('role','list');
  shell.append(head,status,listHead,list);
  root.replaceChildren(shell);

  let destroyed=false;

  function setStatus(message,type='info'){
    status.textContent=String(message||'');
    status.dataset.statusType=type;
    status.setAttribute('role',type==='error'?'alert':'status');
    status.setAttribute('aria-live',type==='error'?'assertive':'polite');
  }

  function messageForResponse(result,accept){
    if(result.status==='accepted')return ['Invitation acceptée. Le salon privé est maintenant accessible.','success'];
    if(result.status==='declined')return ['Invitation refusée.','success'];
    if(result.status==='expired')return ['Cette invitation venait d’expirer.','info'];
    if(result.status==='unavailable')return ['Cette invitation n’est plus disponible.','info'];
    return [accept?'Impossible d’accepter cette invitation.':'Impossible de refuser cette invitation.','error'];
  }

  function renderInvites(invites){
    list.replaceChildren();
    if(!invites.length){
      list.append(node('p','v25-live-empty','Aucune invitation privée en attente.'));
      return;
    }

    for(const item of invites){
      const card=node('article','v25-live-invite-card');
      card.setAttribute('role','listitem');
      card.append(
        node('strong','v25-live-invite-room',item.roomName),
        node('p','v25-live-muted',`#${item.roomSlug} · Invitation de ${item.inviterLabel}`),
        node('p','v25-live-invite-expiry',item.expiresAt?`Expire ${formatDate(item.expiresAt)}`:'')
      );

      const actions=node('div','v25-live-invite-actions');
      const acceptButton=button('Accepter','btn btn-primary btn-small');
      const declineButton=button('Refuser');
      actions.append(acceptButton,declineButton);
      card.append(actions);

      async function respond(accept){
        acceptButton.disabled=true;
        declineButton.disabled=true;
        setStatus(accept?'Acceptation en cours…':'Refus en cours…');
        try{
          const result=await respondToLiveInvite(item.inviteId,accept,{supabase});
          if(destroyed)return;
          await refreshInvites();
          if(result.status==='accepted')await Promise.resolve(onAccepted(result));
          const [message,type]=messageForResponse(result,accept);
          setStatus(message,type);
        }catch{
          if(!destroyed){
            acceptButton.disabled=false;
            declineButton.disabled=false;
            setStatus('Impossible de traiter cette invitation pour le moment.','error');
          }
        }
      }

      acceptButton.addEventListener('click',()=>respond(true));
      declineButton.addEventListener('click',()=>respond(false));
      list.append(card);
    }
  }

  async function refreshInvites(){
    const invites=await listMyLiveInvites({limit:20,supabase});
    if(!destroyed)renderInvites(invites);
    return invites;
  }

  refreshButton.addEventListener('click',async()=>{
    refreshButton.disabled=true;
    try{
      await refreshInvites();
      setStatus('Invitations actualisées.','success');
    }catch{
      setStatus('Impossible d’actualiser les invitations pour le moment.','error');
    }finally{
      if(!destroyed)refreshButton.disabled=false;
    }
  });

  const ready=refreshInvites()
    .then(()=>{setStatus('Invitations privées prêtes.','success');})
    .catch(error=>{setStatus('Impossible de charger les invitations privées.','error');throw error;});

  return {
    ready,
    refresh:refreshInvites,
    destroy:async()=>{
      destroyed=true;
      root.replaceChildren();
    }
  };
}
