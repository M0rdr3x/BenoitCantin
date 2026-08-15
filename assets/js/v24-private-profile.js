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

function migrationMissing(error){
  const text=String(error?.message||'');
  const code=String(error?.code||'');
  return code==='PGRST205'||/private_profiles|relation .* does not exist|schema cache/i.test(text);
}

if(form){
  const user=await requireUser();
  const s=getSupabase();
  const {data,error}=await s.from('private_profiles').select('*').eq('user_id',user.id).maybeSingle();
  let serverReady=!error;

  if(error){
    if(migrationMissing(error)){
      fillForm(metadataFallback(user));
      setStatus(status,'Vos renseignements d’inscription sont affichés temporairement depuis votre Compte SINJIRA™. Le coffre privé sera modifiable dès que la migration serveur V24 sera appliquée dans Supabase.','error');
    }else{
      setStatus(status,'Impossible de charger le coffre privé pour le moment. Réessayez plus tard.','error');
    }
  }else{
    fillForm(data||metadataFallback(user));
  }

  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!serverReady){
      setStatus(status,'Enregistrement temporairement bloqué : la table privée V24 n’est pas encore disponible dans Supabase. Les données affichées ne seront pas perdues si elles proviennent de votre inscription.','error');
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
    if(saveError&&migrationMissing(saveError))serverReady=false;
    setStatus(status,saveError?'Impossible d’enregistrer le coffre privé tant que la migration Supabase n’est pas appliquée.':'Informations privées enregistrées.',saveError?'error':'success');
  });
}
