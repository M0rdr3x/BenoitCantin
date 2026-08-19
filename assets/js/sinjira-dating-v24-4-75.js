import {getSupabase,escapeHtml,formatDate,setStatus} from './sinjira-supabase.js';
import {requireCommunityUser,avatarUrl} from './sinjira-social-common.js?v=24.4.42';

const s=getSupabase();
const statusNode=document.querySelector('[data-dating-status]');
const statusLabel=document.querySelector('[data-dating-status-label]');
const form=document.querySelector('[data-dating-profile-form]');
const candidatesBox=document.querySelector('[data-dating-candidates]');
const connectionsBox=document.querySelector('[data-dating-connections]');
const conversationZone=document.querySelector('[data-dating-conversation-zone]');
const conversationTitle=document.querySelector('[data-dating-conversation-title]');
const conversationMessages=document.querySelector('[data-dating-conversation-messages]');
const messageForm=document.querySelector('[data-dating-message-form]');
let user=null;
let activeConnection=null;
let lastOverview=[];

const splitTags=value=>[...new Set(String(value||'').split(/[\n,;]+/).map(v=>v.trim()).filter(Boolean).map(v=>v.slice(0,80)))].slice(0,20);
const tagsText=value=>(Array.isArray(value)?value:[]).join(', ');
const checkedValues=name=>[...form.querySelectorAll(`input[name="${name}"]:checked`)].map(node=>node.value);

function containsContactInfo(value){
  const text=String(value||'').toLowerCase();
  if(!text.trim())return false;
  if(/[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}/i.test(text))return true;
  if(/https?:\/\/|www\./i.test(text))return true;
  if(/(^|[^a-z0-9_])@[a-z0-9_.\-]{2,}/i.test(text))return true;
  if(/(^|[^a-z0-9_])([a-z0-9\-]+\.)+(com|ca|net|org|io|me|fr|co|app|gg|social|chat|dev|tv|info|xyz)([^a-z0-9_]|$)/i.test(text))return true;
  if(/(instagram|insta|snapchat|snap|tiktok|telegram|discord|whatsapp|facebook|messenger)\s*[:=]\s*[a-z0-9_.\-]{3,}/i.test(text))return true;
  const phoneCandidates=text.match(/\+?[0-9][0-9 ().\-]{5,}[0-9]/g)||[];
  return phoneCandidates.some(candidate=>(candidate.match(/[0-9]/g)||[]).length>=7);
}

function profileContainsContactInfo(){
  const names=['region','intro','values_tags','interests_tags','lifestyle_tags','communication_tags','goals_tags','wanted_values','wanted_interests','wanted_lifestyle','wanted_communication','wanted_goals','partner_description','dealbreakers'];
  return names.some(name=>containsContactInfo(form.elements[name]?.value));
}

function explainError(error,fallback='Action impossible pour le moment.'){
  const raw=String(error?.message||error||'');
  if(raw.includes('ADULTS_ONLY'))return 'Cette section est strictement réservée aux personnes de 18 ans et plus.';
  if(raw.includes('PROFILE_INCOMPLETE'))return 'Complétez votre présentation et vos préférences avant d’activer les rencontres.';
  if(raw.includes('DATING_NOT_ELIGIBLE'))return 'Votre profil n’est pas admissible actuellement. Vérifiez votre statut célibataire et votre confirmation.';
  if(raw.includes('DATING_CONTACT_INFO_FORBIDDEN_BEFORE_REVEAL'))return 'Pour préserver la rencontre à l’aveugle, les coordonnées directes restent bloquées jusqu’au seuil de 10 messages chacun et au consentement mutuel.';
  if(raw.includes('DATING_CONTACT_INFO_FORBIDDEN'))return 'Retirez le courriel, numéro de téléphone, URL ou identifiant social de votre profil de compatibilité. Ces coordonnées ne doivent pas apparaître avant le dévoilement mutuel.';
  if(raw.includes('DATING_RATE_LIMIT'))return 'Vous envoyez des messages trop rapidement. Réessayez dans un moment.';
  if(raw.includes('CANDIDATE_NOT_AVAILABLE'))return 'Cette proposition n’est plus disponible.';
  if(raw.includes('REQUEST_NOT_AVAILABLE'))return 'Cette proposition de discussion n’est plus disponible.';
  if(raw.includes('CONVERSATION_NOT_AVAILABLE'))return 'Cette conversation n’est pas disponible.';
  if(raw.includes('PHOTO_REVEAL_TOO_EARLY'))return 'Le dévoilement exige au moins 10 messages envoyés par chaque personne.';
  if(raw.includes('REGISTRY_CONSENT_REQUIRED'))return 'Activez d’abord le consentement Registre dans votre profil.';
  if(raw.includes('NO_REGISTRY_SOURCE'))return 'Aucun questionnaire du Registre utilisable n’est associé à ce compte.';
  return fallback;
}

async function ensureOwnRows(){
  const [profileResult,prefResult]=await Promise.all([
    s.from('dating_profiles').select('*').eq('user_id',user.id).maybeSingle(),
    s.from('dating_preferences').select('*').eq('user_id',user.id).maybeSingle()
  ]);
  if(profileResult.error)throw profileResult.error;
  if(prefResult.error)throw prefResult.error;
  if(!profileResult.data){const {error}=await s.from('dating_profiles').insert({user_id:user.id});if(error)throw error;}
  if(!prefResult.data){const {error}=await s.from('dating_preferences').insert({user_id:user.id});if(error)throw error;}
}

async function loadOwnForm(){
  const [profileResult,prefResult]=await Promise.all([
    s.from('dating_profiles').select('*').eq('user_id',user.id).maybeSingle(),
    s.from('dating_preferences').select('*').eq('user_id',user.id).maybeSingle()
  ]);
  if(profileResult.error||prefResult.error)throw profileResult.error||prefResult.error;
  const p=profileResult.data||{};const d=prefResult.data||{};
  form.elements.gender_identity.value=p.gender_identity||'';
  form.elements.region.value=p.region||'';form.elements.intro.value=p.intro||'';
  form.elements.min_age.value=d.min_age||18;form.elements.max_age.value=d.max_age||99;
  for(const name of ['values_tags','interests_tags','lifestyle_tags','communication_tags','goals_tags'])form.elements[name].value=tagsText(p[name]);
  for(const name of ['wanted_values','wanted_interests','wanted_lifestyle','wanted_communication','wanted_goals'])form.elements[name].value=tagsText(d[name]);
  form.elements.partner_description.value=d.partner_description||'';form.elements.dealbreakers.value=d.dealbreakers||'';
  form.elements.use_registry_answers.checked=!!p.use_registry_answers;
  const seeking=new Set(d.seeking_genders||[]);form.querySelectorAll('input[name="seeking_genders"]').forEach(node=>{node.checked=seeking.has(node.value)});
}

async function saveProfile({silent=false}={}){
  const minAge=Number(form.elements.min_age.value||18);const maxAge=Number(form.elements.max_age.value||99);
  if(minAge>maxAge)throw new Error('AGE_RANGE');
  if(profileContainsContactInfo())throw new Error('DATING_CONTACT_INFO_FORBIDDEN');
  const seeking=checkedValues('seeking_genders');
  const profilePayload={user_id:user.id,gender_identity:form.elements.gender_identity.value||null,region:String(form.elements.region.value||'').trim(),intro:String(form.elements.intro.value||'').trim(),values_tags:splitTags(form.elements.values_tags.value),interests_tags:splitTags(form.elements.interests_tags.value),lifestyle_tags:splitTags(form.elements.lifestyle_tags.value),communication_tags:splitTags(form.elements.communication_tags.value),goals_tags:splitTags(form.elements.goals_tags.value),use_registry_answers:!!form.elements.use_registry_answers.checked};
  const preferencePayload={user_id:user.id,min_age:minAge,max_age:maxAge,seeking_genders:seeking,wanted_values:splitTags(form.elements.wanted_values.value),wanted_interests:splitTags(form.elements.wanted_interests.value),wanted_lifestyle:splitTags(form.elements.wanted_lifestyle.value),wanted_communication:splitTags(form.elements.wanted_communication.value),wanted_goals:splitTags(form.elements.wanted_goals.value),partner_description:String(form.elements.partner_description.value||'').trim(),dealbreakers:String(form.elements.dealbreakers.value||'').trim()};
  const [a,b]=await Promise.all([s.from('dating_profiles').upsert(profilePayload,{onConflict:'user_id'}),s.from('dating_preferences').upsert(preferencePayload,{onConflict:'user_id'})]);
  if(a.error||b.error)throw a.error||b.error;
  if(!silent)setStatus(statusNode,'Profil de compatibilité enregistré.','success');
}

async function loadSelfStatus(){
  const {data,error}=await s.rpc('dating_self_status');if(error)throw error;const state=data||{};
  document.querySelectorAll('[data-dating-adult-zone]').forEach(node=>{node.hidden=state.adult===false});
  if(state.adult===false){if(statusLabel)statusLabel.textContent='Accès refusé · 18+ uniquement';setStatus(statusNode,'Les rencontres SINJIRA™ sont strictement réservées aux adultes.','error');return state;}
  if(statusLabel)statusLabel.textContent=state.eligible?`Profil actif · ${state.age||'18+'} ans · célibataire confirmé`:state.enabled?'Profil à reconfirmer ou incomplet':'Profil non actif';
  return state;
}

function candidateCard(item){
  const reasons=(item.reasons||[]).map(reason=>`<li>${escapeHtml(reason)}</li>`).join('');
  return `<article class="account-card" data-dating-candidate="${escapeHtml(item.profile_id)}"><div class="account-welcome-strip"><strong>${escapeHtml(item.blind_alias)}</strong><span>${escapeHtml(String(item.compatibility_score))}% compatible</span></div><h3>${escapeHtml(item.age_band)} · ${escapeHtml(item.region||'Région non précisée')}</h3><p>${escapeHtml(item.intro||'Présentation à découvrir par la conversation.')}</p><ul>${reasons||'<li>Compatibilité globale selon vos critères.</li>'}</ul><div class="hero-actions"><button class="btn btn-primary btn-small" type="button" data-dating-request>Proposer une discussion</button></div></article>`;
}

async function loadCandidates(state){
  if(!candidatesBox)return;if(!state?.eligible){candidatesBox.innerHTML='<p>Activez et confirmez votre profil pour recevoir des propositions anonymes.</p>';return;}
  const {data=[],error}=await s.rpc('dating_compatibility_candidates',{p_limit:8});if(error)throw error;
  candidatesBox.innerHTML=data.length?data.map(candidateCard).join(''):'<p>Aucune compatibilité assez forte n’est disponible actuellement. Le système ne remplit pas artificiellement la liste.</p>';
  candidatesBox.querySelectorAll('[data-dating-candidate]').forEach(card=>{card.querySelector('[data-dating-request]')?.addEventListener('click',async()=>{const button=card.querySelector('[data-dating-request]');button.disabled=true;const {error:requestError}=await s.rpc('dating_request_conversation',{p_candidate_profile_id:card.dataset.datingCandidate});if(requestError){button.disabled=false;setStatus(statusNode,explainError(requestError,'Impossible de proposer cette discussion.'),'error');return;}setStatus(statusNode,'Proposition de discussion envoyée sans dévoiler votre identité.','success');await refreshAll();});});
}

function connectionCard(item){
  const statusText={pending:'En attente',accepted:'Discussion ouverte',declined:'Terminée',closed:'Fermée'}[item.status]||item.status;
  const identity=item.identity_revealed?`<div class="v20-social-identity"><img class="v20-social-avatar" src="${escapeHtml(avatarUrl(item.revealed_avatar_path))}" alt="Photo de profil dévoilée avec consentement mutuel"><div><strong>${escapeHtml(item.revealed_name||'Membre SINJIRA™')}</strong><p>Identité dévoilée par consentement mutuel.</p></div></div>`:`<strong>${escapeHtml(item.blind_alias)}</strong>`;
  let actions='';
  if(item.status==='pending'&&item.direction==='incoming')actions='<button class="btn btn-primary btn-small" data-dating-accept type="button">Accepter la discussion</button> <button class="btn btn-secondary btn-small" data-dating-decline type="button">Refuser</button> <button class="btn btn-secondary btn-small" data-dating-block type="button">Bloquer</button>';
  if(item.status==='pending'&&item.direction==='outgoing')actions='<span>Votre proposition attend une réponse.</span> <button class="btn btn-secondary btn-small" data-dating-close type="button">Retirer la proposition</button> <button class="btn btn-secondary btn-small" data-dating-block type="button">Bloquer</button>';
  if(item.status==='accepted'){actions='<button class="btn btn-primary btn-small" data-dating-open type="button">Ouvrir la discussion</button>';if(item.photo_unlock_available&&!item.my_photo_consent)actions+=' <button class="btn btn-secondary btn-small" data-dating-reveal type="button">Autoriser le dévoilement</button>';else if(item.my_photo_consent&&!item.identity_revealed)actions+=' <span>Votre consentement est donné · attente de l’autre personne.</span>';actions+=' <button class="btn btn-secondary btn-small" data-dating-close type="button">Fermer cette rencontre</button> <button class="btn btn-secondary btn-small" data-dating-block type="button">Bloquer</button>';}
  return `<article class="account-card" data-dating-connection="${escapeHtml(item.connection_id)}"><div class="account-welcome-strip">${identity}<span>${escapeHtml(statusText)}</span></div><p>${escapeHtml(item.intro||'')}</p><p><small>${escapeHtml(item.region||'Région non précisée')} · Vous : ${Number(item.my_message_count||0)}/10 · Autre personne : ${Number(item.their_message_count||0)}/10 avant dévoilement</small></p><div class="hero-actions">${actions}</div></article>`;
}

async function loadConnections(){
  if(!connectionsBox)return;const {data=[],error}=await s.rpc('dating_connections_overview');if(error)throw error;lastOverview=data;
  connectionsBox.innerHTML=data.length?data.map(connectionCard).join(''):'<p>Aucune proposition ou conversation pour le moment.</p>';
  connectionsBox.querySelectorAll('[data-dating-connection]').forEach(card=>{const id=card.dataset.datingConnection;card.querySelector('[data-dating-accept]')?.addEventListener('click',()=>respondConnection(id,true));card.querySelector('[data-dating-decline]')?.addEventListener('click',()=>respondConnection(id,false));card.querySelector('[data-dating-open]')?.addEventListener('click',()=>openConversation(id));card.querySelector('[data-dating-close]')?.addEventListener('click',()=>closeConnection(id));card.querySelector('[data-dating-block]')?.addEventListener('click',()=>blockConnection(id));card.querySelector('[data-dating-reveal]')?.addEventListener('click',async()=>{const {error:revealError}=await s.rpc('dating_set_photo_consent',{p_connection_id:id,p_consent:true});if(revealError){setStatus(statusNode,explainError(revealError,'Impossible d’enregistrer votre consentement.'),'error');return;}setStatus(statusNode,'Consentement au dévoilement enregistré. Le profil restera caché tant que l’autre personne n’aura pas aussi accepté.','success');await loadConnections();});});
}

async function respondConnection(id,accept){const {error}=await s.rpc('dating_respond_connection',{p_connection_id:id,p_accept:accept});if(error){setStatus(statusNode,explainError(error,'Impossible de répondre à cette proposition.'),'error');return;}setStatus(statusNode,accept?'Discussion anonyme ouverte.':'Proposition refusée.','success');await refreshAll();}
async function closeConnection(id){if(!confirm('Fermer définitivement cette rencontre? Cette personne ne sera plus reproposée dans ce lien de compatibilité.'))return;const {error}=await s.rpc('dating_close_connection',{p_connection_id:id});if(error){setStatus(statusNode,explainError(error,'Impossible de fermer cette rencontre.'),'error');return;}if(activeConnection===id){activeConnection=null;conversationZone.hidden=true;}setStatus(statusNode,'Rencontre fermée. Aucun consentement de dévoilement n’est conservé.','success');await refreshAll();}
async function blockConnection(id){if(!confirm('Bloquer cette personne? Son identité restera cachée, la rencontre sera fermée et ce compte sera ajouté à vos blocages communautaires.'))return;const {error}=await s.rpc('dating_block_connection',{p_connection_id:id});if(error){setStatus(statusNode,explainError(error,'Impossible de bloquer cette personne.'),'error');return;}if(activeConnection===id){activeConnection=null;conversationZone.hidden=true;}setStatus(statusNode,'Personne bloquée et rencontre fermée.','success');await refreshAll();}

async function openConversation(id){
  activeConnection=id;const info=lastOverview.find(row=>row.connection_id===id);if(conversationTitle)conversationTitle.textContent=info?.identity_revealed?`Discussion avec ${info.revealed_name}`:`Discussion avec ${info?.blind_alias||'un profil compatible'}`;
  const {data=[],error}=await s.rpc('dating_conversation',{p_connection_id:id});if(error){setStatus(statusNode,explainError(error,'Impossible de charger cette conversation.'),'error');return;}
  conversationMessages.innerHTML=data.length?data.map(message=>`<div class="v20-comment"><strong>${message.sender_is_me?'Vous':'Autre personne'}</strong><p>${escapeHtml(message.body)}</p><small>${escapeHtml(formatDate(message.created_at))}</small></div>`).join(''):'<p>Aucun message. Commencez par une vraie question sur la personne, pas sur son apparence.</p>';
  conversationZone.hidden=false;conversationZone.scrollIntoView({behavior:'smooth',block:'start'});
}

async function refreshAll(){const state=await loadSelfStatus();if(state.adult!==false)await Promise.all([loadCandidates(state),loadConnections()]);}

form?.addEventListener('submit',async event=>{event.preventDefault();try{await saveProfile();await refreshAll();}catch(error){setStatus(statusNode,error?.message==='AGE_RANGE'?'La plage d’âge recherchée est invalide.':explainError(error,'Impossible d’enregistrer ce profil.'),'error');}});
document.querySelector('[data-dating-confirm]')?.addEventListener('click',async()=>{try{await saveProfile({silent:true});const {error}=await s.rpc('dating_confirm_single_and_serious');if(error)throw error;setStatus(statusNode,'Profil activé : vous confirmez être majeur, célibataire, disponible et à la recherche d’une relation sérieuse.','success');await refreshAll();}catch(error){setStatus(statusNode,explainError(error,'Impossible d’activer le profil.'),'error');}});
document.querySelector('[data-dating-pause]')?.addEventListener('click',async()=>{const {error}=await s.rpc('dating_pause_profile',{});if(error){setStatus(statusNode,explainError(error,'Impossible de mettre le profil en pause.'),'error');return;}setStatus(statusNode,'Profil de rencontres en pause. Vous ne recevez plus de nouvelles propositions.','success');await refreshAll();});
document.querySelector('[data-dating-partnered]')?.addEventListener('click',async()=>{if(!confirm('Confirmer que vous êtes maintenant en couple ou indisponible? Les discussions de rencontres actives seront fermées.'))return;const {error}=await s.rpc('dating_pause_profile',{p_relationship_status:'partnered'});if(error){setStatus(statusNode,explainError(error,'Impossible de mettre à jour votre disponibilité.'),'error');return;}setStatus(statusNode,'Votre profil de rencontres est désactivé et vos discussions de rencontres actives sont fermées.','success');await refreshAll();});
document.querySelector('[data-dating-import-registry]')?.addEventListener('click',async()=>{try{form.elements.use_registry_answers.checked=true;await saveProfile({silent:true});const {data,error}=await s.rpc('dating_import_registry_traits');if(error)throw error;setStatus(statusNode,`${Array.isArray(data)?data.length:0} repère(s) non sensible(s) du Registre importé(s).`,'success');await refreshAll();}catch(error){setStatus(statusNode,explainError(error,'Impossible d’importer les repères du Registre.'),'error');}});
document.querySelector('[data-dating-refresh]')?.addEventListener('click',()=>refreshAll().catch(error=>setStatus(statusNode,explainError(error,'Actualisation impossible.'),'error')));
document.querySelector('[data-dating-close-conversation]')?.addEventListener('click',()=>{activeConnection=null;conversationZone.hidden=true;});

messageForm?.addEventListener('submit',async event=>{
  event.preventDefault();if(!activeConnection)return;const body=String(new FormData(messageForm).get('body')||'').trim();if(!body)return;
  const info=lastOverview.find(row=>row.connection_id===activeConnection);
  if(!info?.identity_revealed&&containsContactInfo(body)){setStatus(statusNode,'Les coordonnées directes restent bloquées pendant la phase anonyme. Continuez la conversation ici jusqu’au seuil 10/10 et au consentement mutuel.','error');return;}
  const button=messageForm.querySelector('button[type="submit"]');if(button)button.disabled=true;
  try{const {error}=await s.rpc('dating_send_message',{p_connection_id:activeConnection,p_body:body});if(error)throw error;messageForm.reset();await Promise.all([openConversation(activeConnection),loadConnections()]);}catch(error){setStatus(statusNode,explainError(error,'Impossible d’envoyer ce message.'),'error');}finally{if(button)button.disabled=false;}
});

(async()=>{try{user=await requireCommunityUser(location.pathname+location.search);await ensureOwnRows();await loadOwnForm();await refreshAll();}catch(error){if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise')setStatus(statusNode,explainError(error,'Le module Rencontres n’a pas pu être chargé.'),'error');}})();
