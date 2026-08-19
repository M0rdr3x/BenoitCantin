import {getSupabase,requireCommunityUser,escapeHtml,avatarUrl,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';

const UI_VERSION='24.4.74';
const form=document.querySelector('[data-dating-form]');
const eligibilityNode=document.querySelector('[data-dating-eligibility]');
const recommendationsNode=document.querySelector('[data-dating-recommendations]');
const introductionsNode=document.querySelector('[data-dating-introductions]');
const statusNode=document.querySelector('[data-dating-status]');
const pauseButton=document.querySelector('[data-dating-pause]');
const deleteButton=document.querySelector('[data-dating-delete]');
let user=null;
let eligibility=null;
let ownProfile=null;

function fail(error,fallback='Action impossible dans Rencontres SINJIRA™.'){
  const code=String(error?.message||error||'');
  const map={
    DATING_NOT_ELIGIBLE:'Votre compte ne remplit plus les conditions de la section Rencontres.',
    DATING_PAIR_NOT_ALLOWED:'Cette présentation n’est plus disponible selon les critères actuels des deux personnes.',
    DATING_RECOMMENDATION_EXPIRED:'Cette proposition anonyme a expiré. Actualisez les compatibilités pour en obtenir une nouvelle.',
    SERIOUS_INTENT_REQUIRED:'Confirmez votre intention de rechercher une relation sérieuse avant d’activer le profil.',
    INVALID_AGE_RANGE:'Vérifiez la tranche d’âge recherchée.',
    TOO_MANY_PREFERENCES:'Vous avez sélectionné trop de préférences dans une catégorie.',
    INTRO_ALREADY_EXISTS:'Une présentation existe déjà avec cette personne.',
    INTRO_RESPONSE_NOT_ALLOWED:'Cette présentation ne peut pas être traitée depuis votre compte.',
    PHOTO_THRESHOLD_NOT_MET:'La photo reste verrouillée jusqu’à 10 messages envoyés par chaque personne.',
    ACCEPTED_INTRO_REQUIRED:'La révélation de photo nécessite une présentation acceptée.'
  };
  const known=Object.entries(map).find(([key])=>code.includes(key));
  if(known){socialStatus(statusNode,known[1],'error');return;}
  socialErrorStatus(statusNode,error,fallback);
}

function checkedValues(name){return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map(input=>input.value);}
function setCheckedValues(name,values=[]){const selected=new Set(Array.isArray(values)?values:[]);form.querySelectorAll(`input[name="${name}"]`).forEach(input=>{input.checked=selected.has(input.value);});}
function setField(name,value){const input=form.elements.namedItem(name);if(input&&!('length' in input&&input.tagName===undefined))input.value=value??'';}

function fillProfile(profile){
  ownProfile=profile||null;
  if(!profile)return;
  setField('preferred_age_min',profile.preferred_age_min??18);
  setField('preferred_age_max',profile.preferred_age_max??80);
  setField('communication_style',profile.communication_style||'balanced');
  setField('life_rhythm',profile.life_rhythm||'balanced');
  setField('social_energy',profile.social_energy||'balanced');
  setField('distance_scope',profile.distance_scope||'same_region');
  setCheckedValues('preferred_partner_genders',profile.preferred_partner_genders);
  setCheckedValues('values_sought',profile.values_sought);
  setCheckedValues('interests',profile.interests);
  form.elements.namedItem('questionnaire_opt_in').checked=!!profile.questionnaire_opt_in;
  form.elements.namedItem('serious_intent_confirmed').checked=!!profile.serious_intent_confirmed;
  form.elements.namedItem('active').checked=!!profile.active;
}

function profilePayload(activeOverride=null){
  return {
    preferred_age_min:Number(form.elements.namedItem('preferred_age_min').value||18),
    preferred_age_max:Number(form.elements.namedItem('preferred_age_max').value||80),
    preferred_partner_genders:checkedValues('preferred_partner_genders'),
    values_sought:checkedValues('values_sought'),interests:checkedValues('interests'),
    communication_style:String(form.elements.namedItem('communication_style').value||'balanced'),
    life_rhythm:String(form.elements.namedItem('life_rhythm').value||'balanced'),
    social_energy:String(form.elements.namedItem('social_energy').value||'balanced'),
    distance_scope:String(form.elements.namedItem('distance_scope').value||'same_region'),
    questionnaire_opt_in:!!form.elements.namedItem('questionnaire_opt_in').checked,
    serious_intent_confirmed:!!form.elements.namedItem('serious_intent_confirmed').checked,
    active:activeOverride===null?!!form.elements.namedItem('active').checked:!!activeOverride
  };
}

function eligibilityText(info){
  const reason=info?.reason||'unknown';
  if(reason==='eligible')return {ok:true,title:'Accès autorisé',body:'Votre compte est admissible à Rencontres SINJIRA™. Vous choisissez vous-même si votre profil est actif.'};
  if(reason==='adult_only')return {ok:false,title:'Section réservée aux adultes',body:'Rencontres SINJIRA™ est strictement réservé aux personnes dont l’âge serveur est confirmé à 18 ans ou plus.'};
  if(reason==='single_status_required')return {ok:false,title:'Statut relationnel non admissible',body:'La section accepte uniquement les statuts Célibataire, Divorcé(e) ou Veuf / veuve. Modifiez votre coffre privé dans Profil si votre situation réelle a changé.',link:'profil.html'};
  if(reason==='community_rules_required')return {ok:false,title:'Règles de communauté requises',body:'Acceptez d’abord les règles de la Communauté SINJIRA™.',link:'regles-communaute.html'};
  if(reason==='community_suspended')return {ok:false,title:'Accès communautaire suspendu',body:'La section Rencontres est indisponible pendant une suspension communautaire.'};
  return {ok:false,title:'Admissibilité à compléter',body:'La vérification de votre âge ou de votre situation relationnelle est incomplète.',link:'profil.html'};
}

function renderEligibility(info){
  const copy=eligibilityText(info);
  eligibilityNode.innerHTML=`<div class="dating-status-line"><span class="dating-dot ${copy.ok?'ok':'warn'}"></span><div><strong>${escapeHtml(copy.title)}</strong><p class="dating-help">${escapeHtml(copy.body)}</p>${copy.link?`<a href="${escapeHtml(copy.link)}">Ouvrir la page concernée</a>`:''}</div></div>`;
  form.classList.toggle('dating-disabled',!copy.ok);
  [...form.elements].forEach(control=>{control.disabled=!copy.ok;});
  if(pauseButton)pauseButton.disabled=!copy.ok;
}

async function loadEligibility(){const {data,error}=await getSupabase().rpc('dating_my_eligibility');if(error)throw error;eligibility=data||{eligible:false,reason:'unknown'};renderEligibility(eligibility);return eligibility;}
async function loadOwnProfile(){const {data,error}=await getSupabase().from('dating_profiles').select('*').eq('user_id',user.id).maybeSingle();if(error)throw error;fillProfile(data);}
function listMarkup(items,emptyLabel){const list=Array.isArray(items)?items.filter(Boolean):[];return list.length?`<ul>${list.map(item=>`<li>${escapeHtml(item)}</li>`).join('')}</ul>`:`<p class="dating-help">${escapeHtml(emptyLabel)}</p>`;}

async function requestIntroduction(recommendationToken,button){
  button.disabled=true;
  try{
    const {error}=await getSupabase().rpc('dating_request_introduction',{p_recommendation_token:recommendationToken});
    if(error)throw error;
    socialStatus(statusNode,'Présentation demandée. Les identités restent anonymisées jusqu’à l’acceptation mutuelle.','success');
    await Promise.all([loadRecommendations(),loadIntroductions()]);
  }catch(error){fail(error,'Impossible de demander cette présentation.');}
  finally{button.disabled=false;}
}

async function loadRecommendations(){
  if(!eligibility?.eligible||!ownProfile?.active){recommendationsNode.innerHTML='<div class="dating-empty">Activez votre profil de rencontre pour recevoir des propositions compatibles.</div>';return;}
  const {data,error}=await getSupabase().rpc('dating_recommendations',{p_limit:8});
  if(error)throw error;
  const rows=Array.isArray(data)?data:[];
  recommendationsNode.innerHTML=rows.map((row,index)=>`<article class="dating-candidate" data-dating-candidate="${escapeHtml(row.recommendation_token)}"><div class="dating-candidate-head"><div><span class="dating-badge">Proposition anonyme · 24 h</span><h3>Compatibilité proposée ${index+1}</h3><p class="dating-help">Ni pseudo, ni identifiant communautaire, ni photo ne sont révélés avant une présentation mutuellement acceptée.</p></div><div class="dating-score"><strong>${Number(row.compatibility_score)||0}%</strong><span>compatibilité</span></div></div><div class="dating-points"><section><h4>Points communs</h4>${listMarkup(row.strengths,'Critères de base compatibles.')}</section><section><h4>À découvrir ensemble</h4>${listMarkup(row.explore,'Aucun contraste important détecté dans les critères utilisés.')}</section></div><button class="btn btn-primary btn-small" data-request-intro type="button">Demander une présentation anonyme</button></article>`).join('')||'<div class="dating-empty">Aucune nouvelle proposition ne correspond actuellement aux critères mutuels. Le système n’affiche jamais des profils simplement pour remplir la liste.</div>';
  recommendationsNode.querySelectorAll('[data-dating-candidate]').forEach(card=>{const button=card.querySelector('[data-request-intro]');button?.addEventListener('click',()=>requestIntroduction(card.dataset.datingCandidate,button));});
}

function introductionStatusLabel(row){if(row.status==='accepted')return 'Présentation acceptée';if(row.status==='declined')return 'Présentation fermée';if(row.status==='closed')return 'Conversation fermée';return row.requested_by_me?'En attente de réponse':'À vous de décider';}

async function photoGate(row,node){
  if(row.status!=='accepted')return;
  const {data,error}=await getSupabase().rpc('dating_photo_reveal_status',{p_introduction_id:row.id});
  if(error){node.innerHTML='<p class="dating-help">État de révélation indisponible pour le moment.</p>';return;}
  const sent=Number(data?.sent_count||0),received=Number(data?.received_count||0),threshold=Number(data?.threshold||10);
  const progress=Math.min(100,Math.round((Math.min(sent,threshold)+Math.min(received,threshold))/(threshold*2)*100));
  const unlocked=!!data?.unlocked,canConsent=sent>=threshold&&received>=threshold;
  node.innerHTML=`<div class="dating-photo-gate"><div><strong>Photo : ${unlocked?'déverrouillée':'verrouillée'}</strong><p class="dating-help">Vous : ${sent}/${threshold} messages · ${escapeHtml(row.other_pseudo||'Autre personne')} : ${received}/${threshold} messages. ${data?.my_consent?'Votre accord est donné.':'Votre accord n’est pas encore donné.'} ${data?.other_consent?'L’autre personne a aussi donné son accord.':'L’accord de l’autre personne reste privé tant qu’il n’est pas donné.'}</p><div class="dating-progress" aria-label="Progression vers le seuil de discussion"><span style="width:${progress}%"></span></div></div>${unlocked&&data?.other_avatar_path?`<img class="dating-revealed-avatar" src="${escapeHtml(avatarUrl(data.other_avatar_path))}" alt="Photo de profil révélée par consentement mutuel">`:''}</div><div class="dating-actions">${!data?.my_consent&&canConsent?'<button class="btn btn-secondary btn-small" data-photo-consent type="button">Autoriser la révélation de ma photo</button>':''}${data?.my_consent?'<button class="btn btn-secondary btn-small" data-photo-revoke type="button">Retirer mon accord photo</button>':''}</div>`;
  node.querySelector('[data-photo-consent]')?.addEventListener('click',async event=>{event.currentTarget.disabled=true;try{const {error:rpcError}=await getSupabase().rpc('dating_request_photo_reveal',{p_introduction_id:row.id});if(rpcError)throw rpcError;await photoGate(row,node);}catch(err){fail(err,'Impossible d’enregistrer votre accord photo.');}});
  node.querySelector('[data-photo-revoke]')?.addEventListener('click',async event=>{event.currentTarget.disabled=true;try{const {error:rpcError}=await getSupabase().rpc('dating_revoke_photo_reveal',{p_introduction_id:row.id});if(rpcError)throw rpcError;await photoGate(row,node);}catch(err){fail(err,'Impossible de retirer votre accord photo.');}});
}

async function respondIntroduction(id,accept,button){button.disabled=true;try{const {error}=await getSupabase().rpc('dating_respond_introduction',{p_introduction_id:id,p_accept:accept});if(error)throw error;socialStatus(statusNode,accept?'Présentation acceptée. Les pseudos sont maintenant révélés et vous pouvez commencer à discuter.':'Présentation refusée et fermée.','success');await loadIntroductions();}catch(error){fail(error,'Impossible de répondre à cette présentation.');}finally{button.disabled=false;}}
async function closeIntroduction(id,button){if(!confirm('Fermer cette présentation? Les messages communautaires déjà échangés ne seront pas supprimés.'))return;button.disabled=true;try{const {error}=await getSupabase().rpc('dating_close_introduction',{p_introduction_id:id});if(error)throw error;await loadIntroductions();}catch(error){fail(error,'Impossible de fermer cette présentation.');}finally{button.disabled=false;}}

async function loadIntroductions(){
  const {data,error}=await getSupabase().rpc('dating_my_introductions');if(error)throw error;
  const rows=Array.isArray(data)?data:[];
  introductionsNode.innerHTML=rows.map(row=>`<article class="dating-intro" data-introduction="${escapeHtml(row.id)}"><div class="dating-intro-head"><div><span class="dating-badge ${row.status==='accepted'?'accepted':'requested'}">${escapeHtml(introductionStatusLabel(row))}</span><h3>${escapeHtml(row.status==='accepted'?(row.other_pseudo||'Membre SINJIRA'):'Membre compatible')}</h3></div></div>${row.status==='requested'&&!row.requested_by_me?'<p class="dating-help">L’identité communautaire de la personne reste masquée. Accepter révèle les pseudos aux deux personnes et ouvre la possibilité de discuter.</p><div class="dating-actions"><button class="btn btn-primary btn-small" data-intro-accept type="button">Accepter la présentation</button><button class="btn btn-secondary btn-small" data-intro-decline type="button">Refuser</button></div>':''}${row.status==='requested'&&row.requested_by_me?'<p class="dating-help">La personne a reçu une notification anonyme. Aucun pseudo, message ou photo n’est ouvert tant qu’elle n’a pas accepté.</p>':''}${row.status==='accepted'&&row.other_user_id?`<div class="dating-actions"><a class="btn btn-primary btn-small" href="messages-reels.html?user=${encodeURIComponent(row.other_user_id)}">Écrire un message</a><button class="btn btn-secondary btn-small" data-intro-close type="button">Fermer la présentation</button></div><div data-photo-gate></div>`:''}${['declined','closed'].includes(row.status)?'<p class="dating-help">Cette présentation n’est plus active.</p>':''}</article>`).join('')||'<div class="dating-empty">Aucune présentation pour le moment.</div>';
  rows.forEach(row=>{const card=introductionsNode.querySelector(`[data-introduction="${CSS.escape(row.id)}"]`);if(!card)return;card.querySelector('[data-intro-accept]')?.addEventListener('click',event=>respondIntroduction(row.id,true,event.currentTarget));card.querySelector('[data-intro-decline]')?.addEventListener('click',event=>respondIntroduction(row.id,false,event.currentTarget));card.querySelector('[data-intro-close]')?.addEventListener('click',event=>closeIntroduction(row.id,event.currentTarget));const gate=card.querySelector('[data-photo-gate]');if(gate)photoGate(row,gate).catch(error=>console.error('[SINJIRA dating photo gate]',error));});
}

async function saveProfile(activeOverride=null){
  if(!eligibility?.eligible)return;
  const payload=profilePayload(activeOverride);
  if(payload.preferred_age_min>payload.preferred_age_max){socialStatus(statusNode,'L’âge minimum ne peut pas dépasser l’âge maximum.','error');return;}
  const {data,error}=await getSupabase().rpc('dating_save_profile',{p_input:payload});if(error)throw error;
  await loadOwnProfile();socialStatus(statusNode,activeOverride===false?'Profil de rencontre mis en pause.':data?.active?'Profil de rencontre actif et enregistré.':'Profil enregistré en mode pause.','success');await Promise.all([loadRecommendations(),loadIntroductions()]);
}

async function deleteProfile(){
  if(!confirm('Supprimer votre profil de rencontre? Vos préférences de rencontre, présentations et consentements photo seront retirés. Votre Compte SINJIRA™ et vos messages communautaires resteront intacts.'))return;
  const {error}=await getSupabase().rpc('dating_delete_my_profile');if(error)throw error;
  ownProfile=null;form.reset();setField('preferred_age_min',18);setField('preferred_age_max',80);setField('communication_style','balanced');setField('life_rhythm','balanced');setField('social_energy','balanced');setField('distance_scope','same_region');socialStatus(statusNode,'Votre profil de rencontre a été supprimé.','success');await Promise.all([loadRecommendations(),loadIntroductions()]);
}

(async()=>{
  try{
    user=await requireCommunityUser();await loadEligibility();await loadOwnProfile();
    form?.addEventListener('submit',async event=>{event.preventDefault();const button=form.querySelector('button[type="submit"]');if(button)button.disabled=true;try{await saveProfile();}catch(error){fail(error,'Impossible d’enregistrer votre profil de rencontre.');}finally{if(button)button.disabled=false;}});
    pauseButton?.addEventListener('click',async()=>{pauseButton.disabled=true;try{await saveProfile(false);if(form.elements.namedItem('active'))form.elements.namedItem('active').checked=false;}catch(error){fail(error,'Impossible de mettre le profil en pause.');}finally{pauseButton.disabled=false;}});
    deleteButton?.addEventListener('click',async()=>{deleteButton.disabled=true;try{await deleteProfile();}catch(error){fail(error,'Impossible de supprimer votre profil de rencontre.');}finally{deleteButton.disabled=false;}});
    await Promise.all([loadRecommendations(),loadIntroductions()]);socialStatus(statusNode,`Rencontres prêtes · interface ${UI_VERSION}.`,'success');
  }catch(error){if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise')fail(error,'Rencontres SINJIRA™ n’a pas pu terminer sa vérification.');}
})();
