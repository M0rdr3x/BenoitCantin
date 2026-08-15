import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';

const form=document.querySelector('[data-private-profile-form]');
const status=document.querySelector('[data-private-profile-status]');

function metadataFallback(user){
  const m=user?.user_metadata||{};
  return {
    birth_date:m.birth_date||null,
    gender:m.gender||null,
    languages:Array.isArray(m.languages)?m.languages:[],
    residence_city:m.residence_city||null,
    residence_region:m.residence_region||null,
    residence_country:m.residence_country||null,
    origin_city:m.origin_city||null,
    origin_region:m.origin_region||null,
    origin_country:m.origin_country||null,
    relationship_status:m.relationship_status||null,
    relationship_since:m.relationship_since||null,
    relationship_partner_label:m.relationship_partner_label||null
  };
}

function fillForm(data){
  for(const el of form.elements){
    if(!el.name)continue;
    let v=data?.[el.name];
    if(el.name==='languages'&&Array.isArray(v))v=v.join(', ');
    if(v!==null&&v!==undefined)el.value=v;
  }
}

function serverMissing(error){
  const text=String(error?.message||'');
  const code=String(error?.code||'');
  return code==='PGRST205'||/private_profiles|relation .* does not exist|schema cache/i.test(text);
}
function setFormReady(ready){
  for(const el of form.elements){if(el.type==='submit'||el.tagName==='BUTTON')el.disabled=!ready}
}

if(form){
  const user=await requireUser();
  const s=getSupabase();
  const {data,error}=await s.from('private_profiles').select('*').eq('user_id',user.id).maybeSingle();
  let serverReady=!error;

  if(error){
    fillForm(metadataFallback(user));
    setFormReady(false);
    setStatus(status,serverMissing(error)?'Les renseignements déjà fournis lors de votre inscription sont affichés en lecture seule. Le coffre privé sera modifiable dès que le serveur SINJIRA™ sera synchronisé.':'Impossible de charger le coffre privé pour le moment. Vos renseignements d’inscription restent liés à votre compte.','info');
  }else{
    fillForm(data||metadataFallback(user));
    setFormReady(true);
  }

  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!serverReady){
      setStatus(status,'Enregistrement temporairement indisponible. Les valeurs provenant de votre inscription restent conservées dans votre compte.','info');
      return;
    }
    const d=new FormData(form);
    const languages=String(d.get('languages')||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,12);
    const payload={
      user_id:user.id,
      birth_date:d.get('birth_date')||null,
      gender:String(d.get('gender')||'')||null,
      languages,
      residence_city:String(d.get('residence_city')||'').trim()||null,
      residence_region:String(d.get('residence_region')||'').trim()||null,
      residence_country:String(d.get('residence_country')||'').trim()||null,
      origin_city:String(d.get('origin_city')||'').trim()||null,
      origin_region:String(d.get('origin_region')||'').trim()||null,
      origin_country:String(d.get('origin_country')||'').trim()||null,
      relationship_status:String(d.get('relationship_status')||'')||null,
      relationship_since:d.get('relationship_since')||null,
      relationship_partner_label:String(d.get('relationship_partner_label')||'').trim()||null
    };
    const {error:saveError}=await s.from('private_profiles').upsert(payload,{onConflict:'user_id'});
    if(saveError&&serverMissing(saveError)){serverReady=false;setFormReady(false)}
    setStatus(status,saveError?'Impossible d’enregistrer le coffre privé pour le moment.':'Informations privées enregistrées.',saveError?'error':'success');
  });
}
