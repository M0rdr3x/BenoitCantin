/* Verrou de présentation par formulaire. Aucun stockage ni appel réseau. */
export function createAdminSaveGuard(form){
  const status=form.querySelector('[data-admin-save-status]');
  const submit=form.querySelector('button[type="submit"]');
  let dirty=false,busy=false,uncertain=false;
  const say=(message,kind)=>{
    status.textContent=message;status.dataset.statusType=kind;status.hidden=false;
  };
  const warn=event=>{if(dirty||busy||uncertain){event.preventDefault();event.returnValue='';}};
  function syncWarning(){
    window.removeEventListener('beforeunload',warn);
    if(dirty||busy||uncertain)window.addEventListener('beforeunload',warn);
  }
  const change=()=>{dirty=true;syncWarning();if(!busy&&!uncertain)say('Modifications non enregistrées.','info')};
  form.addEventListener('input',change);
  form.addEventListener('change',change);
  submit.disabled=false;
  return {
    canStart(){return !busy&&!uncertain&&!submit.disabled},
    notice:say,
    canReplace(){
      if(busy||uncertain)return false;
      return !dirty||window.confirm('Remplacer les modifications non enregistrées de ce formulaire ?');
    },
    markClean(){dirty=false;status.hidden=true;syncWarning()},
    async run(save,refresh,message,expectedId,onUncertain){
      if(busy||uncertain||submit.disabled)return false;
      busy=true;syncWarning();
      const states=[...form.elements].filter(el=>'disabled' in el).map(el=>[el,el.disabled]);
      states.forEach(([el])=>{el.disabled=true});
      form.setAttribute('aria-busy','true');
      say('Enregistrement en cours…','info');
      try{
        let row;
        try{
          row=await save();
          if(!row||typeof row!=='object'||Array.isArray(row)||
            typeof row.id!=='string'||!row.id.trim()||(expectedId&&row.id!==expectedId))throw new Error('UNCONFIRMED');
        }catch{
          uncertain=true;
          say(typeof onUncertain==='function'?onUncertain():'Enregistrement non confirmé. Votre saisie est conservée. Vérifiez le résultat avant de recharger et de réessayer.','error');
          return false;
        }
        form.reset();dirty=false;
        try{
          await refresh();
          say(message,'success');
        }catch{
          uncertain=true;
          say(message+' Actualisation indisponible : rechargez la page avant une autre sauvegarde.','info');
        }
        return true;
      }finally{
        busy=false;form.setAttribute('aria-busy','false');
        states.forEach(([el,disabled])=>{el.disabled=disabled});
        submit.disabled=uncertain;
        syncWarning();
      }
    }
  };
}
