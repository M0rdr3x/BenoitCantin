import {getSupabase} from './sinjira-supabase.js';
import {executeLiveInput} from './sinjira-live-runtime-v25.js';
import {normalizeLiveRooms} from './sinjira-live-ui-model-v25.js';
import {
  createLiveShareCode,
  listLiveShareCodes,
  redeemLiveShareCode,
  revokeLiveShareCode
} from './sinjira-live-share-codes-client-v25.js';

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

function statusLabel(value){
  if(value==='active')return 'Actif';
  if(value==='used')return 'Utilisé';
  if(value==='revoked')return 'Révoqué';
  return 'Expiré';
}

export function createLiveShareCodesUi(root,{supabase=getSupabase(),onJoined=()=>{}}={}){
  if(!(root instanceof Element))throw new Error('SOCIAL_LIVE_SHARE_CODE_UI_ROOT_REQUIRED');

  const shell=node('section','v25-live-share-shell');
  shell.setAttribute('aria-label','Codes privés En direct');
  const head=node('div','v25-live-share-head');
  head.append(
    node('span','v25-social-kicker','Accès privé'),
    node('h2','v25-live-share-title','Codes de partage'),
    node('p','v25-live-muted','Un code expire après 24 heures et ne fonctionne qu’une seule fois. Le secret n’est affiché qu’au moment de sa création.')
  );

  const status=node('div','v25-live-share-status','Prêt.');
  status.setAttribute('role','status');
  status.setAttribute('aria-live','polite');
  status.setAttribute('aria-atomic','true');

  const createSection=node('section','v25-live-share-section');
  createSection.setAttribute('aria-label','Créer un code de partage');
  createSection.append(node('h3','v25-live-share-subtitle','Créer un code'));
  const roomLabel=node('label','v25-live-share-label','Salon privé que vous possédez');
  const roomSelect=document.createElement('select');
  roomSelect.setAttribute('aria-label','Salon privé pour le code de partage');
  roomSelect.autocomplete='off';
  roomLabel.append(roomSelect);
  const createButton=button('Créer un code','btn btn-primary btn-small');
  createButton.disabled=true;
  createSection.append(roomLabel,createButton);

  const reveal=node('div','v25-live-share-reveal');
  reveal.hidden=true;
  const revealText=node('p','v25-live-muted','Copiez ce code maintenant. Il sera masqué dès que vous le demanderez ou que la page sera cachée.');
  const secret=node('code','v25-live-share-secret');
  secret.setAttribute('aria-label','Code de partage affiché une seule fois');
  const expires=node('p','v25-live-share-expiry');
  const revealActions=node('div','v25-live-share-actions');
  const copyButton=button('Copier');
  const hideButton=button('Masquer');
  revealActions.append(copyButton,hideButton);
  reveal.append(revealText,secret,expires,revealActions);
  createSection.append(reveal);

  const redeemSection=node('section','v25-live-share-section');
  redeemSection.setAttribute('aria-label','Rejoindre avec un code');
  redeemSection.append(
    node('h3','v25-live-share-subtitle','Rejoindre avec un code'),
    node('p','v25-live-muted','Collez le code reçu. Il n’est ni ajouté à une URL, ni conservé dans l’historique des commandes.')
  );
  const redeemForm=node('form','v25-live-share-redeem');
  const codeLabel=node('label','v25-live-share-label','Code privé');
  const codeInput=document.createElement('input');
  codeInput.type='password';
  codeInput.maxLength=64;
  codeInput.autocomplete='off';
  codeInput.autocapitalize='off';
  codeInput.spellcheck=false;
  codeInput.inputMode='text';
  codeInput.setAttribute('aria-label','Code privé En direct');
  codeLabel.append(codeInput);
  const redeemButton=button('Rejoindre','btn btn-primary btn-small');
  redeemButton.type='submit';
  redeemForm.append(codeLabel,redeemButton);
  redeemSection.append(redeemForm);

  const listSection=node('section','v25-live-share-section');
  listSection.setAttribute('aria-label','Mes codes de partage');
  const listHead=node('div','v25-live-share-list-head');
  listHead.append(node('h3','v25-live-share-subtitle','Mes codes récents'));
  const refreshButton=button('Actualiser');
  listHead.append(refreshButton);
  const codeList=node('div','v25-live-share-list');
  codeList.setAttribute('role','list');
  listSection.append(listHead,codeList);

  shell.append(head,status,createSection,redeemSection,listSection);
  root.replaceChildren(shell);

  let destroyed=false;

  function setStatus(message,type='info'){
    status.textContent=String(message||'');
    status.dataset.statusType=type;
    status.setAttribute('role',type==='error'?'alert':'status');
    status.setAttribute('aria-live',type==='error'?'assertive':'polite');
  }

  function clearSecret(){
    secret.textContent='';
    expires.textContent='';
    reveal.hidden=true;
  }

  function onVisibilityChange(){
    if(document.hidden)clearSecret();
  }

  function renderCreated(result){
    clearSecret();
    secret.textContent=result.code;
    expires.textContent=result.expiresAt?`Expire ${formatDate(result.expiresAt)}`:'Expire dans moins de 24 heures.';
    reveal.hidden=false;
    secret.focus?.();
  }

  async function refreshOwnedRooms(){
    const result=await executeLiveInput('/rooms',{supabase});
    const rooms=normalizeLiveRooms(result.data).filter(room=>room.visibility==='private'&&room.owned===true);
    roomSelect.replaceChildren();
    if(!rooms.length){
      const option=document.createElement('option');
      option.value='';
      option.textContent='Aucun salon privé possédé';
      roomSelect.append(option);
      roomSelect.disabled=true;
      createButton.disabled=true;
      return rooms;
    }
    roomSelect.disabled=false;
    for(const room of rooms){
      const option=document.createElement('option');
      option.value=room.roomId;
      option.textContent=`${room.name} (#${room.slug})`;
      roomSelect.append(option);
    }
    createButton.disabled=false;
    return rooms;
  }

  function renderCodes(codes){
    codeList.replaceChildren();
    if(!codes.length){
      codeList.append(node('p','v25-live-empty','Aucun code récent.'));
      return;
    }
    for(const item of codes){
      const card=node('article','v25-live-share-card');
      card.setAttribute('role','listitem');
      const title=node('strong','',item.roomName);
      const meta=node('p','v25-live-muted',`#${item.roomSlug} · ${statusLabel(item.status)}`);
      const timing=node('p','v25-live-share-expiry',item.expiresAt?`Expire ${formatDate(item.expiresAt)}`:'');
      card.append(title,meta,timing);
      if(item.status==='active'){
        const revoke=button('Révoquer');
        revoke.addEventListener('click',async()=>{
          revoke.disabled=true;
          try{
            const changed=await revokeLiveShareCode(item.codeId,{supabase});
            await refreshCodes();
            setStatus(changed?'Code révoqué.':'Ce code n’était plus actif.',changed?'success':'info');
          }catch{
            setStatus('Impossible de révoquer ce code pour le moment.','error');
          }finally{
            revoke.disabled=false;
          }
        });
        card.append(revoke);
      }
      codeList.append(card);
    }
  }

  async function refreshCodes(){
    const codes=await listLiveShareCodes({supabase,limit:20});
    renderCodes(codes);
    return codes;
  }

  createButton.addEventListener('click',async()=>{
    const roomId=roomSelect.value;
    if(!roomId)return;
    clearSecret();
    createButton.disabled=true;
    try{
      const result=await createLiveShareCode(roomId,{supabase});
      if(destroyed)return;
      renderCreated(result);
      await refreshCodes();
      setStatus('Code créé. Copiez-le avant de le masquer.','success');
    }catch{
      setStatus('Impossible de créer un code pour ce salon.','error');
    }finally{
      if(!destroyed)createButton.disabled=roomSelect.disabled;
    }
  });

  copyButton.addEventListener('click',async()=>{
    const value=secret.textContent;
    if(!value)return;
    if(!navigator.clipboard?.writeText){
      setStatus('Copie automatique indisponible. Sélectionnez le code et copiez-le manuellement.','info');
      return;
    }
    try{
      await navigator.clipboard.writeText(value);
      setStatus('Code copié dans le presse-papiers.','success');
    }catch{
      setStatus('La copie automatique a été refusée par le navigateur.','error');
    }
  });

  hideButton.addEventListener('click',()=>{
    clearSecret();
    setStatus('Code masqué. Il ne peut pas être réaffiché depuis SINJIRA.','success');
  });

  redeemForm.addEventListener('submit',async event=>{
    event.preventDefault();
    if(!codeInput.value.trim())return;
    redeemButton.disabled=true;
    try{
      const pending=redeemLiveShareCode(codeInput.value,{supabase});
      codeInput.value='';
      const result=await pending;
      await refreshOwnedRooms();
      await Promise.resolve(onJoined(result));
      setStatus(result.status==='already_member'?'Vous étiez déjà membre de ce salon.':'Salon privé rejoint avec le code.','success');
    }catch{
      codeInput.value='';
      setStatus('Ce code privé n’est pas disponible.','error');
    }finally{
      redeemButton.disabled=false;
      codeInput.focus();
    }
  });

  refreshButton.addEventListener('click',async()=>{
    refreshButton.disabled=true;
    try{
      await Promise.all([refreshOwnedRooms(),refreshCodes()]);
      setStatus('Codes actualisés.','success');
    }catch{
      setStatus('Impossible d’actualiser les codes pour le moment.','error');
    }finally{
      refreshButton.disabled=false;
    }
  });

  document.addEventListener('visibilitychange',onVisibilityChange);
  const ready=Promise.all([refreshOwnedRooms(),refreshCodes()])
    .then(()=>{setStatus('Codes privés prêts.','success');})
    .catch(error=>{setStatus('Impossible de charger les codes privés.','error');throw error;});

  return {
    ready,
    clearSecret,
    refresh:async()=>Promise.all([refreshOwnedRooms(),refreshCodes()]),
    destroy:async()=>{
      destroyed=true;
      clearSecret();
      codeInput.value='';
      document.removeEventListener('visibilitychange',onVisibilityChange);
      root.replaceChildren();
    }
  };
}
