import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';

const user=await requireUser();
const s=getSupabase();

function tableMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||/relation .* does not exist|schema cache|privacy_settings|notification_preferences/i.test(text);
}

function setDisabled(form,disabled){
  for(const el of form.elements){
    if(el.type==='submit'||el.tagName==='BUTTON')el.disabled=disabled;
  }
}

function formPayload(form){
  const payload={};
  for(const el of form.elements){
    if(!el.name||el.disabled)continue;
    payload[el.name]=el.type==='checkbox'?el.checked:el.value;
  }
  return payload;
}

async function bind(table,formSel,statusSel){
  const form=document.querySelector(formSel),status=document.querySelector(statusSel);
  if(!form)return;
  let ready=false,busy=false,recheck=false;
  let data=null,error=null;
  form.inert=true;
  setDisabled(form,true);
  form.setAttribute('aria-busy','true');
  try{
    const result=await s.from(table).select('*').eq('user_id',user.id).maybeSingle();
    data=result.data;error=result.error;
  }catch{
    error={code:'NETWORK'};
  }
  ready=!error;
  let exists=Boolean(data);
  if(error){
    setDisabled(form,true);
    setStatus(status,tableMissing(error)?'Cette section attend la synchronisation du serveur SINJIRA™. Vos réglages actuels ne sont pas modifiés.':'Impossible de charger ces préférences pour le moment. Réessayez plus tard.','info');
  }else{
    const row=data||{};
    for(const el of form.elements){
      if(!el.name)continue;
      if(el.name==='allow_ai_personal_data'){el.checked=false;continue}
      if(el.type==='checkbox')el.checked=!!row[el.name];
      else if(row[el.name]!=null)el.value=row[el.name];
    }
  }
  form.setAttribute('aria-busy','false');
  form.inert=!ready;
  setDisabled(form,!ready);
  if(ready)setStatus(status,'Préférences chargées.','info');
  let saved=JSON.stringify(formPayload(form));
  form.addEventListener('input',()=>{
    if(!busy&&ready)setStatus(status,JSON.stringify(formPayload(form))===saved?
      'Aucune modification en attente.':'Modifications non enregistrées.','info');
  });
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(busy)return;
    if(!ready){setStatus(status,'Enregistrement temporairement indisponible tant que le serveur n’est pas synchronisé.','info');return}
    const payload=formPayload(form);
    const snapshot=JSON.stringify(payload);
    busy=true;
    setDisabled(form,true);
    form.setAttribute('aria-busy','true');
    setStatus(status,'Enregistrement en cours…','info');
    try{
      // Après un échec d'insertion, vérifier si le serveur a néanmoins créé la ligne.
      // Ne pas relancer de mutation automatiquement.
      if(recheck){
        const probe=await s.from(table).select('user_id').eq('user_id',user.id).maybeSingle();
        if(probe.error)throw probe.error;
        exists=Boolean(probe.data);recheck=false;
      }
      let result;
      if(exists){
        result=await s.from(table).update({...payload,updated_at:new Date().toISOString()}).eq('user_id',user.id);
      }else{
        recheck=true;
        result=await s.from(table).insert({user_id:user.id,...payload});
      }
      if(result.error)throw result.error;
      exists=true;recheck=false;saved=snapshot;
      setStatus(status,JSON.stringify(formPayload(form))===saved?
        'Préférences enregistrées dans votre compte.':
        'Sauvegarde terminée. Des modifications plus récentes restent non enregistrées.','success');
    }catch(error){
      if(tableMissing(error)){ready=false;form.inert=true}
      setStatus(status,ready?
        'Impossible de confirmer l’enregistrement. Votre saisie est conservée dans cet onglet; réessayez.':
        'Enregistrement indisponible. Votre saisie est conservée dans cet onglet.','error');
    }finally{
      busy=false;
      form.setAttribute('aria-busy','false');
      setDisabled(form,!ready);
    }
  });
}

await Promise.all([
  bind('privacy_settings','[data-privacy-settings-form]','[data-privacy-settings-status]'),
  bind('notification_preferences','[data-notification-settings-form]','[data-notification-settings-status]')
]);
