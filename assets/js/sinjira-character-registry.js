import {getSupabase,getCurrentUser} from './sinjira-supabase.js';
const form=document.querySelector('[data-character-form]'),state=document.querySelector('[data-character-submit-status]');
let currentUser=null,currentProfile=null;
function setState(msg,type='info'){if(!state)return;state.textContent=msg;state.dataset.statusType=type}
function serialize(form){const out={};for(const [k,v] of new FormData(form).entries()){if(v instanceof File)continue;if(k in out)out[k]=Array.isArray(out[k])?[...out[k],v]:[out[k],v];else out[k]=v}return out}
function installChoiceLimits(){form?.querySelectorAll('[data-max-select]').forEach(group=>{const max=Number(group.dataset.maxSelect||0);if(!max)return;group.addEventListener('change',e=>{if(!(e.target instanceof HTMLInputElement)||e.target.type!=='checkbox')return;const checked=[...group.querySelectorAll('input[type="checkbox"]:checked')];if(checked.length>max){e.target.checked=false;setState(`Choisissez au maximum ${max} réponses dans cette section.`,'error')}})})}
async function uploadPhoto(user){const input=form.querySelector('input[type="file"][name="photo"]'),file=input?.files?.[0];if(!file)return null;if(file.size>10*1024*1024)throw new Error('La photo doit faire 10 Mo ou moins.');if(file.type&&!file.type.startsWith('image/'))throw new Error('Le fichier joint doit être une image.');const ext=(file.name.split('.').pop()||'img').toLowerCase().replace(/[^a-z0-9]/g,'').slice(0,8)||'img';const path=`${user.id}/${crypto.randomUUID()}.${ext}`;const {error}=await getSupabase().storage.from('sinjira-character-sources').upload(path,file,{contentType:file.type||'application/octet-stream',upsert:false});if(error)throw error;return path}
async function submitToSinjira(user){const photo_path=await uploadPhoto(user);const answers=serialize(form);const {data,error}=await getSupabase().functions.invoke('submit-character-questionnaire',{body:{answers,photo_path,manual_only:true}});if(error||!data?.ok)throw new Error(data?.error||error?.message||'Le dossier n’a pas pu être enregistré dans SINJIRA.');return data}
async function init(){
 if(!form)return;installChoiceLimits();
 currentUser=await getCurrentUser();
 const login=document.querySelector('[data-registry-login-actions]'),submit=form.querySelector('button[type="submit"]');
 if(!currentUser){if(login)login.hidden=false;submit.disabled=true;setState('Connectez-vous à votre Compte SINJIRA avant de transmettre le questionnaire.','error');return}
 const [{data:p},{data:existingSubmission},{data:existingCharacter}]=await Promise.all([
   getSupabase().from('profiles').select('pseudo,display_name').eq('user_id',currentUser.id).maybeSingle(),
   getSupabase().from('character_submissions').select('id,status').eq('user_id',currentUser.id).order('created_at',{ascending:false}).limit(1).maybeSingle(),
   getSupabase().from('characters').select('id,status,public_name').eq('user_id',currentUser.id).limit(1).maybeSingle()
 ]);
 currentProfile=p||{};
 if(existingSubmission||existingCharacter){
   submit.disabled=true;
   form.querySelectorAll('input,textarea,select,button').forEach(x=>x.disabled=true);
   setState(existingCharacter?`Votre compte possède déjà son unique personnage SINJIRA™${existingCharacter.public_name?` : ${existingCharacter.public_name}`:''}. Le questionnaire est verrouillé.`:`Votre compte a déjà une demande de personnage (${existingSubmission.status}). Le questionnaire est verrouillé jusqu’au traitement de ce dossier.`,'info');
   const link=document.createElement('a');link.className='btn btn-primary';link.href='../../../compte/mon-personnage.html';link.textContent='Ouvrir Mon personnage';state.insertAdjacentElement('afterend',link);return;
 }
 const pseudo=currentProfile.pseudo||currentProfile.display_name||'';
 document.querySelector('[data-registry-pseudo]').value=pseudo;
 document.querySelector('[data-registry-email]').value=currentUser.email||'';
 document.querySelector('[data-form-account-pseudo]').value=pseudo;
 document.querySelector('[data-form-account-email]').value=currentUser.email||'';
 setState('Compte associé. Le questionnaire sera enregistré directement dans SINJIRA™.','success');
 form.addEventListener('submit',async e=>{
   e.preventDefault();e.stopImmediatePropagation();
   if(!form.checkValidity()){form.reportValidity();return}
   submit.disabled=true;setState('Enregistrement sécurisé dans votre Compte SINJIRA™…','info');
   try{
     const result=await submitToSinjira(currentUser);
     localStorage.removeItem('registre-consciences-draft-v1');
     if(result.notification_sent){setState('Participation enregistrée dans SINJIRA™ et avis courriel envoyé à Benoit Cantin.','success')}
     else{setState('Participation enregistrée dans SINJIRA™. Elle est visible dans l’administration. Le courriel externe n’est pas nécessaire pour conserver le dossier.','success')}
     form.querySelectorAll('input,textarea,select,button').forEach(x=>x.disabled=true);
   }catch(err){setState(err.message||'Transmission impossible. Aucune participation n’a été confirmée.','error');submit.disabled=false}
 },true);
}
init().catch(e=>setState(e.message||'Erreur de liaison au compte.','error'));
