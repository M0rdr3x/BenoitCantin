import {getSupabase,requireUser,setStatus,escapeHtml,formatDate} from './sinjira-supabase.js';

const UI_VERSION='24.4.88';
const missionBox=document.querySelector('[data-parallel-mission]');
const stateBox=document.querySelector('[data-parallel-state]');
const historyBox=document.querySelector('[data-parallel-history]');
const statusBox=document.querySelector('[data-parallel-status]');
const empty=msg=>`<div class="v24-empty">${escapeHtml(msg)}</div>`;

function friendlyDate(value){try{return value?formatDate(value):'—'}catch{return String(value||'—')}}
function stateSummary(state){
  if(!state)return 'La Chronique technique sera créée automatiquement lorsque votre continuité devient admissible.';
  const data=state.state_data&&typeof state.state_data==='object'?state.state_data:{};
  const summary=String(data.summary||data.private_summary||'').trim();
  return summary||'Aucun résumé narratif privé n’a encore été enregistré.';
}

async function load(){
  if(!missionBox||!stateBox)return;
  await requireUser();
  const s=getSupabase();

  // V24.4.88: le navigateur ne lit plus public.characters ni les clés techniques
  // de continuité. Le serveur résout le lien privé compte <-> personnage.
  const {data:context,error:contextError}=await s.rpc('parallel_my_context');
  if(contextError)throw contextError;
  if(!context?.ok){
    missionBox.innerHTML=empty('Votre identité du Monde parallèle n’est pas encore prête.');
    stateBox.innerHTML=empty('Aucune Chronique personnelle pour le moment.');
    if(historyBox)historyBox.innerHTML=empty('Aucune histoire liée à votre continuité.');
    return;
  }

  const identity=context.identity||{};
  const parallelName=String(identity.public_name||'Identité parallèle').trim()||'Identité parallèle';
  const parallelBio=String(identity.public_bio||'').trim();
  const membership=context.membership||null;
  const state=context.state||null;
  const cycle=context.cycle||null;
  const existingResponse=context.existing_response||null;
  const personalStories=Array.isArray(context.personal_stories)?context.personal_stories:[];
  const collectiveStories=Array.isArray(context.collective_stories)?context.collective_stories:[];

  if(!membership){
    missionBox.innerHTML=empty(`${parallelName} est reconnu dans le Monde parallèle, mais son adhésion n’est pas encore active.`);
  }else if(!cycle){
    missionBox.innerHTML=`<article><span class="v24-badge live">Adhésion ${escapeHtml(membership.status||'active')}</span><h3>${escapeHtml(parallelName)}</h3><p>Aucun cycle mensuel n’est ouvert actuellement.</p></article>`;
  }else{
    const closes=cycle.closes_at?`Clôture : ${escapeHtml(friendlyDate(cycle.closes_at))}`:'Cycle ouvert';
    missionBox.innerHTML=`<article><span class="v24-badge live">${escapeHtml(cycle.title||'Cycle actif')}</span><p><strong>Personnage : ${escapeHtml(parallelName)}</strong></p><h3>${escapeHtml(cycle.monthly_question||'Question mensuelle')}</h3><p>${closes}</p><form data-parallel-response-form><label>Votre réponse<textarea name="response" maxlength="4000" required>${escapeHtml(existingResponse?.response_text||'')}</textarea></label><button class="btn btn-primary" type="submit">${existingResponse?'Mettre à jour ma réponse':'Enregistrer ma réponse'}</button></form>${existingResponse?`<small>Dernier enregistrement : ${escapeHtml(friendlyDate(existingResponse.submitted_at))}</small>`:''}</article>`;
    const responseForm=missionBox.querySelector('[data-parallel-response-form]');
    responseForm?.addEventListener('submit',async e=>{
      e.preventDefault();
      const response=String(new FormData(responseForm).get('response')||'').trim();
      if(!response){setStatus(statusBox,'Écrivez une réponse avant d’enregistrer.','error');return}
      const button=responseForm.querySelector('button[type="submit"]');if(button)button.disabled=true;
      const {data:saved,error}=await s.rpc('parallel_save_cycle_response',{p_cycle_id:cycle.id,p_response_text:response});
      if(button)button.disabled=false;
      if(error||!saved?.ok){setStatus(statusBox,'Impossible d’enregistrer la réponse. Vérifiez votre supervision/MFA et réessayez.','error');return}
      setStatus(statusBox,'Réponse du cycle enregistrée dans votre continuité parallèle.','success');
      button.textContent='Mettre à jour ma réponse';
    });
  }

  const eligibility=membership?(
    membership.pioneer_number?`Pionnier #${membership.pioneer_number} · admissible au canon principal et au Monde parallèle`:
    membership.parallel_world_only?'Continuité du Monde parallèle uniquement':'Accès propriétaire / canon principal + Monde parallèle'
  ):'Adhésion en attente';
  stateBox.innerHTML=`<p><strong>${escapeHtml(parallelName)}</strong></p><p><small>Identité de personnage — séparée de l’identifiant privé du compte.</small></p>${parallelBio?`<p>${escapeHtml(parallelBio)}</p>`:''}<p>${escapeHtml(eligibility)}</p>${state?`<p>État : ${escapeHtml(state.life_state||'active')} · Réputation : ${escapeHtml(String(state.reputation??0))}</p>${state.location_name?`<p>Lieu : ${escapeHtml(state.location_name)}</p>`:''}${state.faction_name?`<p>Faction : ${escapeHtml(state.faction_name)}</p>`:''}<p>${escapeHtml(stateSummary(state))}</p><small>Dernière mise à jour : ${escapeHtml(friendlyDate(state.updated_at))}</small>`:'<p>Chronique technique en attente.</p>'}`;

  if(historyBox){
    const renderStory=(x,label)=>`<article class="v24-panel"><span class="v24-badge">${label}</span><h3>${escapeHtml(x.title||'Chronique')}</h3><p>${escapeHtml(String(x.content||'').slice(0,700))}${String(x.content||'').length>700?'…':''}</p><small>${escapeHtml(friendlyDate(x.published_at))}</small></article>`;
    const stories=[...personalStories.map(x=>renderStory(x,'Personnel')),...collectiveStories.map(x=>renderStory(x,'Collectif'))];
    historyBox.innerHTML=stories.length?stories.join(''):empty('Aucune histoire publiée pour le moment. Les futures chroniques apparaîtront ici.');
  }
}

load().catch(error=>{
  console.error(`[SINJIRA Monde parallèle ${UI_VERSION}]`,error);
  if(missionBox)missionBox.innerHTML=empty('Le Monde parallèle n’a pas pu charger le cycle actuel.');
  if(stateBox)stateBox.innerHTML=empty('La Chronique n’a pas pu être chargée.');
  if(historyBox)historyBox.innerHTML=empty('Historique temporairement indisponible.');
  setStatus(statusBox,'Monde parallèle temporairement indisponible. Réessayez plus tard.','error');
});
