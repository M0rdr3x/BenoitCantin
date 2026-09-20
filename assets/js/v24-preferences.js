import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';

const user=await requireUser();
const s=getSupabase();

function tableMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||/relation .* does not exist|schema cache|privacy_settings|notification_preferences/i.test(text);
}

function createFormLock(form){
  const permanentlyDisabled=new Set([...form.elements].filter(el=>el.disabled));
  return locked=>{
    for(const el of form.elements){
      if(permanentlyDisabled.has(el)){el.disabled=true;continue}
      el.disabled=locked;
    }
  };
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
  const setLocked=createFormLock(form);
  setLocked(true);
  const {data,error}=await s.from(table).select('*').eq('user_id',user.id).maybeSingle();
  let ready=!error;
  let exists=Boolean(data);
  if(error){
    setStatus(status,tableMissing(error)?'Cette section attend la synchronisation du serveur SINJIRA™. Vos réglages actuels ne sont pas modifiés.':'Impossible de charger ces préférences pour le moment. Réessayez plus tard.','info');
  }else{
    const row=data||{};
    for(const el of form.elements){
      if(!el.name)continue;
      if(el.type==='checkbox')el.checked=!!row[el.name];
      else if(row[el.name]!=null)el.value=row[el.name];
    }
    if(table==='privacy_settings'&&form.elements.allow_ai_personal_data){
      form.elements.allow_ai_personal_data.checked=false;
    }
    setLocked(false);
  }
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!ready){setStatus(status,'Enregistrement temporairement indisponible tant que le serveur n’est pas synchronisé.','info');return}
    const payload=formPayload(form);
    if(table==='privacy_settings')payload.allow_ai_personal_data=false;
    let result;
    if(exists){
      result=await s.from(table).update({...payload,updated_at:new Date().toISOString()}).eq('user_id',user.id);
    }else{
      result=await s.from(table).insert({user_id:user.id,...payload});
    }
    const save=result.error;
    if(save&&tableMissing(save)){ready=false;setLocked(true)}
    if(!save)exists=true;
    setStatus(status,save?'Impossible d’enregistrer ces préférences pour le moment.':'Préférences enregistrées dans votre compte.',save?'error':'success');
  });
}

await bind('privacy_settings','[data-privacy-settings-form]','[data-privacy-settings-status]');
await bind('notification_preferences','[data-notification-settings-form]','[data-notification-settings-status]');
