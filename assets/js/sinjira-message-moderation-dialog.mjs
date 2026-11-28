// Confirmation explicite des actions de modération, sans stockage ni réseau.
export function requestModeration(button,{mode,contact}){
  const dialog=document.querySelector('[data-message-moderation]');
  if(!dialog||typeof dialog.showModal!=='function'){
    if(mode==='block')return Promise.resolve(window.confirm('Bloquer '+contact+' ? Les messages et interactions seront bloqués.')?{confirmed:true}:null);
    const reason=window.prompt('Pourquoi signalez-vous ce message ? Annuler ne transmet rien.');
    return Promise.resolve(reason?.trim()?{reason:reason.trim()}:null);
  }
  if(dialog.open)return Promise.resolve(null);
  const form=dialog.querySelector('form'),reason=form.elements.reason,details=form.elements.details;
  const reportFields=dialog.querySelector('[data-moderation-fields]');
  const submit=form.querySelector('[value="confirm"]');
  const reporting=mode==='report';
  dialog.querySelector('[data-moderation-title]').textContent=reporting?'Signaler un message':'Bloquer ce compte';
  dialog.querySelector('[data-moderation-contact]').textContent=contact;
  dialog.querySelector('[data-moderation-help]').textContent=reporting?
    'Le signalement est transmis à la modération pour examen. Il ne bloque pas automatiquement ce contact.':
    'Les messages et interactions avec ce compte seront bloqués. Vous serez redirigé vers vos blocages et les brouillons de cet onglet seront perdus.';
  reportFields.hidden=!reporting;
  reason.disabled=!reporting;details.disabled=!reporting;
  reason.required=reporting;reason.value='';details.value='';
  submit.textContent=reporting?'Transmettre le signalement':'Confirmer le blocage';
  dialog.returnValue='';
  return new Promise(resolve=>{
    const onClose=()=>{
      const accepted=dialog.returnValue==='confirm'&&(!reporting||!!reason.value);
      const result=accepted?(reporting?{reason:reason.value,details:details.value.trim()||null}:{confirmed:true}):null;
      reason.value='';details.value='';dialog.returnValue='';
      if(button.isConnected&&!button.disabled)button.focus({preventScroll:true});
      else document.querySelector('[data-chat-title]')?.focus({preventScroll:true});
      resolve(result);
    };
    dialog.addEventListener('close',onClose,{once:true});
    try{dialog.showModal()}catch{
      dialog.removeEventListener('close',onClose);resolve(null);
    }
  });
}
