import {getSupabase,getCurrentUser,isSinjiraOwner} from './sinjira-supabase.js';

const form=document.querySelector('[data-character-form]');
const state=document.querySelector('[data-character-submit-status]');
const ALLOWED_PHOTO_TYPES=new Map([
 ['image/jpeg','jpg'],['image/png','png'],['image/webp','webp'],['image/avif','avif'],['image/gif','gif']
]);
let currentUser=null,currentProfile=null;
let registryReady=false,isSending=false,isOwnerForSubmit=false;
const submitButton=form?.querySelector('button[type="submit"]');
if(submitButton)submitButton.disabled=true;

function setState(msg,type='info'){if(!state)return;state.textContent=msg;state.dataset.statusType=type}
function serialize(formEl){const out={};for(const [k,v] of new FormData(formEl).entries()){if(v instanceof File||k==='reponses_json')continue;if(k in out)out[k]=Array.isArray(out[k])?[...out[k],v]:[out[k],v];else out[k]=v}return out}
function rows(v){return Array.isArray(v)?v:[]}
function installChoiceLimits(){form?.querySelectorAll('[data-max-select]').forEach(group=>{const max=Number(group.dataset.maxSelect||0);if(!max)return;group.addEventListener('change',e=>{if(!(e.target instanceof HTMLInputElement)||e.target.type!=='checkbox')return;const checked=[...group.querySelectorAll('input[type="checkbox"]:checked')];if(checked.length>max){e.target.checked=false;setState(`Choisissez au maximum ${max} réponses dans cette section.`,'error')}})})}
function applyAnswers(payload){if(!payload||typeof payload!=='object')return;for(const [name,value] of Object.entries(payload)){const nodes=[...form.querySelectorAll(`[name="${CSS.escape(name)}"]`)];if(!nodes.length)continue;const values=Array.isArray(value)?value.map(String):[String(value??'')];for(const node of nodes){if(node.type==='file'||node.readOnly)continue;if(node.type==='checkbox'||node.type==='radio')node.checked=values.includes(String(node.value));else if(values.length)node.value=values[0]}}form.dispatchEvent(new Event('change',{bubbles:true}))}
function blockSensitiveForm(message,href='/compte/securite.html',label='Ouvrir Ma sécurité'){
 const submit=form?.querySelector('button[type="submit"]');if(submit)submit.disabled=true;
 form?.querySelectorAll('input,textarea,select,button').forEach(x=>x.disabled=true);
 setState(message,'error');
 if(state&&!state.nextElementSibling?.matches?.('[data-registry-security-link]')){const link=document.createElement('a');link.dataset.registrySecurityLink='';link.className='btn btn-primary';link.href=href;link.textContent=label;state.insertAdjacentElement('afterend',link)}
}
async function ensureSensitiveAccess(){
 // Le Registre privé exige AAL2 même si sensitive_step_up est désactivé.
 // L'Edge Function répète cette vérification avant toute lecture du JSON.
 const {data:aal,error:aalError}=await getSupabase().auth.mfa.getAuthenticatorAssuranceLevel();
 if(aalError||!aal)throw new Error('Impossible de vérifier la double authentification du Registre pour le moment.');
 if(aal.nextLevel!=='aal2'){
   blockSensitiveForm('Pour accéder au Registre des Consciences, activez la double authentification dans Ma sécurité. Cette protection est obligatoire.');
   return false;
 }
 if(aal.currentLevel!=='aal2'){
   const next=location.pathname+location.search+location.hash;
   location.replace(`/compte/mfa.html?next=${encodeURIComponent(next)}`);
   return false;
 }
 const {data,error}=await getSupabase().rpc('security_sensitive_access_status',{p_scope:'registry'});
 if(error)throw new Error('La protection du Registre ne peut pas être vérifiée pour le moment.');
 if(data?.allowed)return true;
 if(data?.setup_required){blockSensitiveForm('La protection renforcée du Registre est active. Configurez d’abord l’authentification à deux facteurs dans Ma sécurité.');return false}
 if(data?.verification_required){const next=location.pathname+location.search+location.hash;location.replace(`/compte/mfa.html?next=${encodeURIComponent(next)}`);return false}
 blockSensitiveForm('Le Registre reste protégé jusqu’à ce que votre identité soit vérifiée.');return false;
}
async function uploadPhoto(user){
 const input=form.querySelector('input[type="file"][name="photo"]'),file=input?.files?.[0];if(!file)return null;
 if(file.size>10*1024*1024)throw new Error('La photo doit faire 10 Mo ou moins.');
 const type=String(file.type||'').toLowerCase();
 if(!ALLOWED_PHOTO_TYPES.has(type))throw new Error('Format de photo non pris en charge. Utilisez JPG, PNG, WebP, AVIF ou GIF.');
 const ext=ALLOWED_PHOTO_TYPES.get(type);
 const path=`${user.id}/${crypto.randomUUID()}.${ext}`;
 const {error}=await getSupabase().storage.from('sinjira-character-sources').upload(path,file,{contentType:type,upsert:false,cacheControl:'3600'});
 if(error)throw error;return path;
}
async function cleanupUploadedPhoto(path){if(!path)return;try{const {error}=await getSupabase().storage.from('sinjira-character-sources').remove([path]);if(error)console.warn('[SINJIRA registre] nettoyage photo temporaire',error)}catch(e){console.warn('[SINJIRA registre] nettoyage photo temporaire impossible',e)}}
// Seul HTTP 409 avec le code métier exact prouve un refus définitif.
// Une erreur de transport, un HTTP 500 ou un 409 non reconnu reste incertain.
async function isConfirmedRegistryDuplicate(error){
 const response=error?.context;
 if(response?.status!==409 || typeof response.json!=='function')return false;
 try{
   const payload=await response.json();
   return payload?.code==='ONE_CHARACTER_PER_ACCOUNT';
 }catch{return false}
}
async function submitToSinjira(user,{updateExisting=false}={}){
 let photo_path=null;
 let invocationStarted=false;
 try{
   photo_path=await uploadPhoto(user);
   const answers=serialize(form);
   invocationStarted=true;
   const {data,error}=await getSupabase().functions.invoke('submit-character-questionnaire',{body:{answers,photo_path,manual_only:true,update_existing:updateExisting}});
   if(error && await isConfirmedRegistryDuplicate(error)){
     // Le POST est explicitement refusé avant écriture. La photo unique
     // téléversée pour CET essai ne référence aucun dossier existant.
     await cleanupUploadedPhoto(photo_path);
     const duplicate=new Error('Ce compte possède déjà une demande ou son personnage unique SINJIRA™. Aucune nouvelle participation n’a été créée. Ouvrez « Mon personnage » pour consulter le dossier existant.');
     duplicate.submissionAlreadyExists=true;
     throw duplicate;
   }
   if(error||!data?.ok||data?.persisted!==true)throw new Error(data?.error||error?.message||'Le serveur n’a pas confirmé la sauvegarde du dossier.');
   return data;
 }catch(e){
   if(e?.submissionAlreadyExists===true)throw e;
   // Après l'envoi HTTP, l'absence d'accusé ne prouve pas l'absence de sauvegarde.
   // Conserver la photo privée: le dossier peut déjà la référencer en base.
   // Sans requête serveur, un fichier temporaire peut en revanche être nettoyé.
   if(!invocationStarted){
     await cleanupUploadedPhoto(photo_path);
     throw e;
   }
   console.warn('[SINJIRA registre] état de sauvegarde incertain; photo conservée');
   // Un échec transport/API après l'invocation peut cacher une écriture réussie.
   // Empêcher tout second POST tant que la personne n'a pas vérifié son dossier.
   const uncertainError=new Error('La réponse du serveur est incertaine. Pour éviter un doublon, vérifiez d’abord « Mon personnage » avant de transmettre à nouveau. Vos réponses restent visibles ici.');
   uncertainError.submissionOutcomeUnknown=true;
   throw uncertainError;
 }
}
async function tryOwnerRepair(user){if(!isSinjiraOwner(user))return;try{await getSupabase().rpc('ensure_sinjira_owner_character')}catch(e){console.info('Owner repair RPC unavailable.',e?.message||e)}}
function successMessage(result){
 const dossier=result.submission_id?` Dossier ${result.submission_id}.`:'';
 const base=result.updated_existing
   ? `Questionnaire mis à jour et enregistré dans SINJIRA™.${dossier}`
   : `Participation enregistrée dans SINJIRA™.${dossier}`;
 const optedIn=form?.querySelector('[name="formspree_receipt_opt_in"]')?.checked===true;
 const adminNotice=result.admin_notification_created===true
   ? ' Avis interne créé.'
   : ' Aucun avis interne confirmé; votre dossier reste enregistré.';
 if(!optedIn)return `${base}${adminNotice} Aucune copie n’a été envoyée à Formspree, conformément à votre choix.`;
 if(result.formspree_notification_sent===true){
   return `${base}${adminNotice} Copie du questionnaire acceptée par Formspree pour notification à SINJIRA™. Un courriel d’accusé de réception sera envoyé si la réponse automatique est activée dans Formspree.`;
 }
 return `${base}${adminNotice} Le service Formspree n’a pas confirmé la réception de la copie. Le questionnaire demeure disponible dans votre dossier SINJIRA™.`;
}

async function init(){
 if(!form)return;installChoiceLimits();
 currentUser=await getCurrentUser();
 const login=document.querySelector('[data-registry-login-actions]'),submit=form.querySelector('button[type="submit"]');
 if(!currentUser){if(login)login.hidden=false;submit.disabled=true;setState('Connectez-vous à votre Compte SINJIRA™ avant de transmettre le questionnaire.','error');return}
 if(!(await ensureSensitiveAccess()))return;
 const owner=isSinjiraOwner(currentUser);
 if(owner)await tryOwnerRepair(currentUser);
 const [profileResult,submissionResult,characterResult]=await Promise.all([
   getSupabase().from('profiles').select('pseudo,display_name').eq('user_id',currentUser.id).maybeSingle(),
   getSupabase().from('character_submissions').select('id,status,source_payload,photo_path,created_at').eq('user_id',currentUser.id).order('created_at',{ascending:false}).limit(1),
   getSupabase().from('characters').select('id,status,public_name,visible_to_user,updated_at').eq('user_id',currentUser.id).order('updated_at',{ascending:false}).limit(5)
 ]);
 // Refuser l'envoi si l'état distant est inconnu : ne jamais supposer un nouveau dossier.
 const {data:p,error:profileError}=profileResult;
 const {data:submissionRows,error:submissionError}=submissionResult;
 const {data:characterRows,error:characterError}=characterResult;
 if(profileError||submissionError||characterError)throw new Error('Impossible de vérifier votre dossier actuellement. Vos réponses restent dans le formulaire; réessayez après rechargement.');
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
   setState(existingCharacter?'AbyssTime est déjà associé à ce compte. Vous pouvez mettre à jour ce questionnaire sans créer un deuxième personnage.':'Compte propriétaire reconnu. Vous pouvez transmettre ou mettre à jour le dossier source d’AbyssTime.','success');
 }else if(existingSubmission||existingCharacter){
   submit.disabled=true;
   form.querySelectorAll('input,textarea,select,button').forEach(x=>x.disabled=true);
   setState(existingCharacter?`Votre compte possède déjà son unique personnage SINJIRA™${existingCharacter.public_name?` : ${existingCharacter.public_name}`:''}. Le questionnaire est verrouillé.`:`Votre compte a déjà une demande de personnage (${existingSubmission.status}). Le questionnaire est verrouillé jusqu’au traitement de ce dossier.`,'info');
   const link=document.createElement('a');link.className='btn btn-primary';link.href='../../../compte/mon-personnage.html';link.textContent='Ouvrir Mon personnage';state.insertAdjacentElement('afterend',link);return;
 }else setState('Compte associé. Le questionnaire sera enregistré directement dans SINJIRA™.','success');

 registryReady=true;
 isOwnerForSubmit=owner;
 submit.disabled=false;
}
// Toujours intercepter l'envoi HTML avant toute opération asynchrone, même si l'init échoue.
form?.addEventListener('submit',async e=>{
 e.preventDefault();
 if(!registryReady||isSending||!currentUser){
   setState('Le Registre n’est pas prêt. Vérifiez votre connexion, la sécurité du compte et rechargez la page.','error');
   return;
 }
 if(!form.checkValidity()){form.reportValidity();return}
 isSending=true;
 if(submitButton)submitButton.disabled=true;
 setState(isOwnerForSubmit?'Mise à jour sécurisée du dossier…':'Enregistrement sécurisé dans votre Compte SINJIRA™…','info');
 // La session peut changer après le chargement de la page. Aucune photo
 // personnelle ne doit être téléversée avant une nouvelle vérification AAL2.
 let securityCheckedBeforeUpload=false;
 try{
   const activeUser=await getCurrentUser();
   if(!activeUser||activeUser.id!==currentUser.id){
     throw new Error('Votre session SINJIRA™ a changé ou expiré. Reconnectez-vous et rechargez le Registre avant tout envoi.');
   }
   if(!(await ensureSensitiveAccess())){
     registryReady=false;
     return;
   }
   securityCheckedBeforeUpload=true;
   const result=await submitToSinjira(activeUser,{updateExisting:isOwnerForSubmit});
   // Un blocage du stockage local ne doit jamais annuler un succès serveur.
   try{localStorage.removeItem('registre-consciences-draft-v1')}catch{console.warn('[SINJIRA registre] brouillon local inaccessible')}
   setState(successMessage(result),'success');
   state?.scrollIntoView({behavior:'smooth',block:'center'});
   form.querySelectorAll('input,textarea,select,button').forEach(x=>x.disabled=true);
   registryReady=false;
 }catch(err){
   const unknown=err?.submissionOutcomeUnknown===true;
   const duplicate=err?.submissionAlreadyExists===true;
   setState(err?.message||'Transmission impossible. Vos réponses restent visibles; réessayez.','error');
   state?.scrollIntoView({behavior:'smooth',block:'center'});
   if(!securityCheckedBeforeUpload){
     // Aucun POST ni téléversement n'a commencé : bloquer le formulaire
     // jusqu'à une nouvelle visite avec une session réellement vérifiée.
     registryReady=false;
     if(submitButton)submitButton.disabled=true;
   }else if(unknown||duplicate){
     registryReady=false;
     if(submitButton)submitButton.disabled=true;
     // Vérification dans un nouvel onglet pour conserver les réponses visibles.
     if(state&&!document.querySelector('[data-registry-verify-submission]')){
       const link=document.createElement('a');
       link.dataset.registryVerifySubmission='';
       link.className='btn btn-secondary';
       link.href='/compte/mon-personnage.html';
       link.target='_blank';
       link.rel='noopener noreferrer';
       link.textContent='Vérifier mon dossier (nouvel onglet)';
       state.insertAdjacentElement('afterend',link);
     }
   }else if(submitButton)submitButton.disabled=false;
 }finally{isSending=false}
});
init().catch(e=>{
 registryReady=false;
 if(submitButton)submitButton.disabled=true;
 setState(e?.message||'Erreur de liaison au compte. Aucune participation n’a été transmise.','error');
});
