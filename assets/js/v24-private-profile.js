import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';
const form=document.querySelector('[data-private-profile-form]');
const status=document.querySelector('[data-private-profile-status]');
if(form){
  const user=await requireUser();
  const s=getSupabase();
  const {data,error}=await s.from('private_profiles').select('*').eq('user_id',user.id).maybeSingle();
  if(error){setStatus(status,'La migration V24 du profil privé doit être appliquée dans Supabase.','error');}
  const p=data||{};
  for(const el of form.elements){if(!el.name)continue;let v=p[el.name];if(el.name==='languages'&&Array.isArray(v))v=v.join(', ');if(v!==null&&v!==undefined)el.value=v;}
  form.addEventListener('submit',async e=>{
    e.preventDefault();const d=new FormData(form);const languages=String(d.get('languages')||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,12);
    const payload={user_id:user.id,birth_date:d.get('birth_date')||null,gender:String(d.get('gender')||'')||null,languages,residence_city:String(d.get('residence_city')||'').trim()||null,residence_region:String(d.get('residence_region')||'').trim()||null,residence_country:String(d.get('residence_country')||'').trim()||null,origin_city:String(d.get('origin_city')||'').trim()||null,origin_region:String(d.get('origin_region')||'').trim()||null,origin_country:String(d.get('origin_country')||'').trim()||null,relationship_status:String(d.get('relationship_status')||'')||null,relationship_since:d.get('relationship_since')||null,relationship_partner_label:String(d.get('relationship_partner_label')||'').trim()||null};
    const {error:saveError}=await s.from('private_profiles').upsert(payload,{onConflict:'user_id'});setStatus(status,saveError?saveError.message:'Informations privées enregistrées.',saveError?'error':'success');
  });
}
