import {getSupabase,getCurrentUser,escapeHtml} from './sinjira-supabase.js';
const form=document.querySelector('[data-character-form]'),state=document.querySelector('[data-character-submit-status]');
let currentUser=null,currentProfile=null;
function setState(msg,type='info'){if(!state)return;state.textContent=msg;state.dataset.statusType=type}
function serialize(form){const out={};for(const [k,v] of new FormData(form).entries()){if(v instanceof File)continue;if(['reponses_json','destination_attendue','source_site','source_formulaire'].includes(k))continue;if(k in out)out[k]=Array.isArray(out[k])?[...out[k],v]:[out[k],v];else out[k]=v}return out}
async function uploadPhoto(user){
  const input=form.querySelector('input[type="file"][name="photo"]'),file=input?.files?.[0];if(!file)return null;
  if(file.size>10*1024*1024)throw new Error('La photo doit faire 10 Mo ou moins.');
  if(file.type&&!file.type.startsWith('image/'))throw new Error('Le fichier joint doit être une image.');
  const ext=(file.name.split('.').pop()||'img').toLowerCase().replace(/[^a-z0-9]/g,'').slice(0,8)||'img';
  const path=`${user.id}/${crypto.randomUUID()}.${ext}`;
  const {error}=await getSupabase().storage.from('sinjira-character-sources').upload(path,file,{contentType:file.type||'application/octet-stream',upsert:false});
  if(error)throw error;return path;
}
async function init(){
  if(!form)return;
  currentUser=await getCurrentUser();
  const login=document.querySelector('[data-registry-login-actions]'),submit=form.querySelector('button[type="submit"]');
  if(!currentUser){login.hidden=false;submit.disabled=true;setState('Connectez-vous à votre Compte SINJIRA avant de transmettre le questionnaire.','error');return}
  const {data:p}=await getSupabase().from('profiles').select('pseudo,display_name').eq('user_id',currentUser.id).maybeSingle();currentProfile=p||{};
  document.querySelector('[data-registry-pseudo]').value=currentProfile.pseudo||currentProfile.display_name||'';
  document.querySelector('[data-registry-email]').value=currentUser.email||'';
  const email=form.querySelector('[name="courriel"]'),withdraw=form.querySelector('[name="courriel_retrait"]');
  if(email&&!email.value)email.value=currentUser.email||'';if(withdraw&&!withdraw.value)withdraw.value=currentUser.email||'';
  setState('Compte associé. Votre dossier et le futur personnage apparaîtront dans « Mes personnages ».','success');
  form.addEventListener('submit',async e=>{
    e.preventDefault();if(!form.checkValidity()){form.reportValidity();return}
    submit.disabled=true;setState('Transmission sécurisée du questionnaire…','info');
    try{
      const photo_path=await uploadPhoto(currentUser);
      const answers=serialize(form);
      const {data,error}=await getSupabase().functions.invoke('submit-character-questionnaire',{body:{answers,photo_path}});
      if(error||!data?.ok)throw new Error(data?.error||error?.message||'Transmission impossible');
      localStorage.removeItem('registre-consciences-draft-v1');
      setState(data.ai_generated?'Questionnaire reçu. Un brouillon de personnage a été généré et attend la validation de Benoit Cantin.':'Questionnaire reçu. Votre dossier attend maintenant son traitement.','success');
      form.querySelectorAll('input,textarea,select,button').forEach(x=>{if(!x.matches('[data-prev],[data-next]'))x.disabled=true});
    }catch(err){setState(err.message||'Transmission impossible.','error');submit.disabled=false}
  },true);
}
init().catch(e=>setState(e.message||'Erreur de liaison au compte.','error'));