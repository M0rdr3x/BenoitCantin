import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';

let user,s;

function tableMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||code==='42P01'||/relation .* does not exist|could not find the table .* in the schema cache/i.test(text);
}

function setDisabled(form,disabled){
  for(const el of form.elements){
    if(el.type==='submit'||el.tagName==='BUTTON')el.disabled=disabled;
  }
}

const allowedFields={
  privacy_settings:new Set(['public_profile','show_avatar_public','show_city_to_contacts','show_relationship_status','show_online_status','allow_messages_from']),
  notification_preferences:new Set(['security_email','direct_messages','community_activity','market_activity','parallel_world','digest_frequency'])
};

function formPayload(form,table){
  const payload={};
  for(const el of form.elements){
    if(!el.name||el.disabled||!allowedFields[table].has(el.name))continue;
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
    if(!result||result.error!==null||(result.data!==null&&result.data?.user_id!==user.id))throw result?.error||Error('Réponse non confirmée');
    data=result.data;
  }catch(cause){
    error=cause||{code:'NETWORK'};
  }
  ready=error===null;
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
  let saved=JSON.stringify(formPayload(form,table));
  form.addEventListener('input',()=>{
    if(!busy&&ready)setStatus(status,JSON.stringify(formPayload(form,table))===saved?
      'Aucune modification en attente.':'Modifications non enregistrées.','info');
  });
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(busy)return;
    if(!ready){setStatus(status,'Enregistrement temporairement indisponible tant que le serveur n’est pas synchronisé.','info');return}
    const payload=formPayload(form,table);
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
        if(!probe||probe.error!==null||(probe.data!==null&&probe.data?.user_id!==user.id))throw Error('Vérification non confirmée');
        exists=Boolean(probe.data);recheck=false;
      }
      let result;
      recheck=true;
      if(exists){
        result=await s.from(table).update({...payload,updated_at:new Date().toISOString()}).eq('user_id',user.id).select('user_id').maybeSingle();
      }else{
        result=await s.from(table).insert({user_id:user.id,...payload}).select('user_id').maybeSingle();
      }
      if(!result||result.error!==null||result.data?.user_id!==user.id)throw result?.error||Error('Écriture non confirmée');
      exists=true;recheck=false;saved=snapshot;
      setStatus(status,JSON.stringify(formPayload(form,table))===saved?
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

const sections=[
  ['privacy_settings','[data-privacy-settings-form]','[data-privacy-settings-status]'],
  ['notification_preferences','[data-notification-settings-form]','[data-notification-settings-status]']
];
try{
  user=await requireUser();
  if(typeof user?.id!=='string'||!user.id.trim())throw Error('SESSION_UNCONFIRMED');
  s=getSupabase();
  if(!s)throw Error('BACKEND_UNAVAILABLE');
  await Promise.all(sections.map(section=>bind(...section)));
}catch{
  // Garder les formulaires inactifs si la vérification de session échoue.
  // Ne pas exposer le détail technique ni autoriser une mutation de secours.
  for(const [,formSel,statusSel] of sections){
    const form=document.querySelector(formSel);
    if(form){
      form.inert=true;
      setDisabled(form,true);
      form.setAttribute('aria-busy','false');
    }
    setStatus(document.querySelector(statusSel),'Impossible de vérifier votre session ou vos préférences. Rechargez la page ou reconnectez-vous. Aucun réglage n’a été modifié par cette vérification.','error');
  }
}
