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

function lockForm(){
  for(const el of form.elements){
    if('disabled' in el)el.disabled=true;
    if('readOnly' in el)el.readOnly=true;
  }
  form.setAttribute('aria-readonly','true');
}

if(form){
  const user=await requireUser();
  const s=getSupabase();
  const {data,error}=await s.from('private_profiles').select('*').eq('user_id',user.id).maybeSingle();

  if(error){
    fillForm(metadataFallback(user));
    setStatus(status,serverMissing(error)
      ?'Les renseignements disponibles sont affichés en lecture seule. Aucune modification n’est permise depuis la page Profil.'
      :'Impossible de charger le coffre privé pour le moment. Les renseignements disponibles restent en lecture seule.',
    'info');
  }else{
    fillForm(data||metadataFallback(user));
    setStatus(status,'Informations privées affichées en lecture seule. Aucune modification n’est permise depuis cette page.','info');
  }

  lockForm();
}
