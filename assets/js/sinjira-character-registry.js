import {getSupabase,getCurrentUser,isSinjiraOwner} from './sinjira-supabase.js';

const form=document.querySelector('[data-character-form]');
const state=document.querySelector('[data-character-submit-status]');
let currentUser=null,currentProfile=null;

function setState(msg,type='info'){if(!state)return;state.textContent=msg;state.dataset.statusType=type}
function serialize(formEl){const out={};for(const [k,v] of new FormData(formEl).entries()){if(v instanceof File||k==='reponses_json')continue;if(k in out)out[k]=Array.isArray(out[k])?[...out[k],v]:[out[k],v];else out[k]=v}return out}
function rows(v){return Array.isArray(v)?v:[]}
function installChoiceLimits(){form?.querySelectorAll('[data-max-select]').forEach(group=>{const max=Number(group.dataset.maxSelect||0);if(!max)return;group.addEventListener('change',e=>{if(!(e.target instanceof HTMLInputElement)||e.target.type!=='checkbox')return;const checked=[...group.querySelectorAll('input[type="checkbox"]:checked')];if(checked.length>max){e.target.checked=false;setState(`Choisissez au maximum ${max} réponses dans cette section.`,'error')}})})}
function applyAnswers(payload){if(!payload||typeof payload!=='object')return;for(const [name,value] of Object.entries(payload)){const nodes=[...form.querySelectorAll(`[name="${CSS.escape(name)}"]`)];if(!nodes.length)continue;const values=Array.isArray(value)?value.map(String):[String(value??'')];for(const node of nodes){if(node.type==='file'||node.readOnly)continue;if(node.type==='checkbox'||node.type==='radio')node.checked=values.includes(String(node.value));else if(values.length)node.value=values[0]}}form.dispatchEvent(new Event('change',{bubbles:true}))}
async function uploadPhoto(user){const input=form.querySelector('input[type="file"][name="photo"]'),file=input?.files?.[0];if(!file)return null;if(file.size>10*1024*1024)throw new Error('La photo doit faire 10 Mo ou moins.');if(file.type&&!file.type.startsWith('image/'))throw new Error('Le fichier joint doit être une image.');const ext=(file.name.split('.').pop()||'img').toLowerCase().replace(/[^a-z0-9]/g,'').slice(0,8)||'img';const path=`${user.id}/${crypto.randomUUID()}.${ext}`;const {error}=await getSupabase().storage.from('sinjira-character-sources').upload(path,file,{contentType:file.type||'application/octet-stream',upsert:false});if(error)throw error;return path}
async function cleanupUploadedPhoto(path){if(!path)return;try{const {error}=await getSupabase().storage.from('sinjira-character-sources').remove([path]);if(error)console.warn('[SINJIRA registre] nettoyage photo temporaire',error)}catch(e){console.warn('[SINJIRA registre] nettoyage photo temporaire impossible',e)}}
async function submitToSinjira(user,{updateExisting=false}={}){let photo_path=null;try{photo_path=await uploadPhoto(user);const answers=serialize(form);const {data,error}=await getSupabase().functions.invoke('submit-character-questionnaire',{body:{answers,photo_path,manual_only:true,update_existing:updateExisting}});if(error||!data?.ok)throw new Error(data?.error||error?.message||'Le dossier n’a pas pu être enregistré dans SINJIRA™.');return data}catch(e){await cleanupUploadedPhoto(photo_path);throw e}}
async function tryOwnerRepair(user){if(!isSinjiraOwner(user))return;try{await getSupabase().rpc('ensure_sinjira_owner_character')}catch(e){console.info('Owner repair RPC not installed yet.',e?.message||e)}}

async function init(){
 if(!form)return;installChoiceLimits();
 currentUser=await getCurrentUser();
 const login=document.querySelector('[data-registry-login-actions]'),submit=form.querySelector('button[type="submit"]');
 if(!currentUser){if(login)login.hidden=false;submit.disabled=true;setState('Connectez-vous à votre Compte SINJIRA™ avant de transmettre le questionnaire.','error');return}
 const owner=isSinjiraOwner(currentUser);
 if(owner)await tryOwnerRepair(currentUser);
 const [{data:p},{data:submissionRows},{data:characterRows}]=await Promise.all([
   getSupabase().from('profiles').select('pseudo,display_name').eq('user_id',currentUser.id).maybeSingle(),
   getSupabase().from('character_submissions').select('id,status,source_payload,photo_path,created_at').eq('user_id',currentUser.id).order('created_at',{ascending:false}).limit(1),
   getSupabase().from('characters').select('id,status,public_name,visible_to_user,updated_at').eq('user_id',currentUser.id).order('updated_at',{ascending:false}).limit(5)
 ]);
 currentProfile=p||{};
 const existingSubmission=rows(submissionRows)[0]||null;
 const existingCharacter=rows(characterRows).find(x=>x.status!=='archived')||rows(characterRows)[0]||null;
 const pseudo=currentProfile.pseudo||currentProfile.display_name||'';
 document.querySelector('[data-registry-pseudo]').value=pseudo;
 document.querySelector('[data-registry-email]').value=currentUser.email||'';
 document.querySelector('[data-form-account-pseudo]').value=pseudo;
 document.querySelector('[data-form-account-email]').value=currentUser.email||'';

 if(owner){
   if(existingSubmission?.source_payload)applyAnswers(existingSubmission.source_payload);
   setState(existingCharacter?`AbyssTime est déjà associé à ce compte. Vous pouvez mettre à jour ce questionnaire sans créer un deuxième personnage.`:`Compte propriétaire reconnu. Vous pouvez transmettre ou mettre à jour le dossier source d’AbyssTime.`,'success');
 }else if(existingSubmission||existingCharacter){
   submit.disabled=true;
   form.querySelectorAll('input,textarea,select,button').forEach(x=>x.disabled=true);
   setState(existingCharacter?`Votre compte possède déjà son unique personnage SINJIRA™${existingCharacter.public_name?` : ${existingCharacter.public_name}`:''}. Le questionnaire est verrouillé.`:`Votre compte a déjà une demande de personnage (${existingSubmission.status}). Le questionnaire est verrouillé jusqu’au traitement de ce dossier.`,'info');
   const link=document.createElement('a');link.className='btn btn-primary';link.href='../../../compte/mon-personnage.html';link.textContent='Ouvrir Mon personnage';state.insertAdjacentElement('afterend',link);return;
 }else setState('Compte associé. Le questionnaire sera enregistré directement dans SINJIRA™.','success');

 form.addEventListener('submit',async e=>{
   if(e.defaultPrevented)return;
   e.preventDefault();
   if(!form.checkValidity()){form.reportValidity();return}
   submit.disabled=true;setState(owner?'Mise à jour sécurisée du dossier AbyssTime…':'Enregistrement sécurisé dans votre Compte SINJIRA™…','info');
   try{
     const result=await submitToSinjira(currentUser,{updateExisting:owner});
     localStorage.removeItem('registre-consciences-draft-v1');
     setState(result.updated_existing?'Questionnaire d’AbyssTime mis à jour dans SINJIRA™. Le personnage existant est conservé.':result.notification_sent?'Participation enregistrée dans SINJIRA™ et avis courriel envoyé à Benoit Cantin.':'Participation enregistrée dans SINJIRA™. Elle est visible dans l’administration; aucun courriel externe n’est nécessaire pour conserver le dossier.','success');
     form.querySelectorAll('input,textarea,select,button').forEach(x=>x.disabled=true);
   }catch(err){setState(err.message||'Transmission impossible. Aucune participation n’a été confirmée.','error');submit.disabled=false}
 });
}
init().catch(e=>setState(e.message||'Erreur de liaison au compte.','error'));
