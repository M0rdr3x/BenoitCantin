import {getSupabase,requireUser,setStatus,escapeHtml,isSinjiraOwner,formatDate} from './sinjira-supabase.js';

const missionBox=document.querySelector('[data-parallel-mission]');
const stateBox=document.querySelector('[data-parallel-state]');
const historyBox=document.querySelector('[data-parallel-history]');
const statusBox=document.querySelector('[data-parallel-status]');
const empty=msg=>`<div class="v24-empty">${escapeHtml(msg)}</div>`;

function friendlyDate(value){try{return value?formatDate(value):'—'}catch{return String(value||'—')}}
function stateSummary(state){
  if(!state)return 'La Chronique technique sera créée automatiquement lorsque votre personnage devient admissible.';
  const data=state.state_data&&typeof state.state_data==='object'?state.state_data:{};
  const summary=String(data.summary||data.private_summary||'').trim();
  return summary||'Aucun résumé narratif privé n’a encore été enregistré.';
}

async function load(){
  if(!missionBox||!stateBox)return;
  const user=await requireUser();
  const s=getSupabase();
  const owner=isSinjiraOwner(user);
  if(owner){try{await s.rpc('ensure_sinjira_owner_character')}catch{/* le backend V24 peut déjà être synchronisé */}}

  const {data:characterRows,error:characterError}=await s.from('characters')
    .select('id,public_name,status,visible_to_user,novel_note,updated_at')
    .eq('user_id',user.id)
    .order('updated_at',{ascending:false})
    .limit(10);
  if(characterError)throw characterError;
  const characters=Array.isArray(characterRows)?characterRows:[];
  const character=characters.find(x=>x.status!=='archived'&&x.visible_to_user)||characters.find(x=>x.status!=='archived')||null;
  if(!character){
    missionBox.innerHTML=empty('Votre personnage doit d’abord être approuvé ou assigné avant d’entrer dans le Monde parallèle.');
    stateBox.innerHTML=empty('Aucune Chronique personnelle pour le moment.');
    if(historyBox)historyBox.innerHTML=empty('Aucune histoire liée à votre personnage.');
    return;
  }

  const [membershipRes,stateRes,cycleRes,personalStoriesRes,collectiveStoriesRes]=await Promise.all([
    s.from('parallel_world_memberships').select('pioneer_number,main_canon_eligible,parallel_world_only,status,joined_at').eq('character_id',character.id).maybeSingle(),
    s.from('parallel_character_state').select('life_state,location_name,faction_name,reputation,state_data,updated_at').eq('character_id',character.id).maybeSingle(),
    s.from('parallel_world_cycles').select('id,cycle_month,title,monthly_question,response_mode,opens_at,closes_at,status,audience,published_at').eq('status','open').order('cycle_month',{ascending:false}).limit(1),
    s.from('parallel_story_installments').select('id,title,content,published_at,cycle_id,story_kind').eq('story_kind','individual').eq('character_id',character.id).order('published_at',{ascending:false}).limit(3),
    s.from('parallel_story_installments').select('id,title,content,published_at,cycle_id,story_kind').eq('story_kind','collective').order('published_at',{ascending:false}).limit(3)
  ]);
  const firstError=[membershipRes,stateRes,cycleRes,personalStoriesRes,collectiveStoriesRes].find(x=>x.error)?.error;
  if(firstError)throw firstError;

  const membership=membershipRes.data||null;
  const state=stateRes.data||null;
  const cycles=Array.isArray(cycleRes.data)?cycleRes.data:[];
  const cycle=cycles[0]||null;
  const personalStories=Array.isArray(personalStoriesRes.data)?personalStoriesRes.data:[];
  const collectiveStories=Array.isArray(collectiveStoriesRes.data)?collectiveStoriesRes.data:[];

  if(!membership){
    missionBox.innerHTML=empty(`${character.public_name||'Votre personnage'} est reconnu, mais son adhésion parallèle n’est pas encore active. Elle est créée automatiquement à l’approbation ou à l’assignation.`);
  }else if(!cycle){
    missionBox.innerHTML=`<article><span class="v24-badge live">Adhésion ${escapeHtml(membership.status||'active')}</span><h3>${escapeHtml(character.public_name||'Mon personnage')}</h3><p>Aucun cycle mensuel n’est ouvert actuellement.</p></article>`;
  }else{
    const {data:existingResponse,error:responseError}=await s.from('parallel_cycle_responses')
      .select('id,response_text,submitted_at')
      .eq('cycle_id',cycle.id).eq('user_id',user.id).maybeSingle();
    if(responseError)throw responseError;
    const closes=cycle.closes_at?`Clôture : ${escapeHtml(friendlyDate(cycle.closes_at))}`:'Cycle ouvert';
    missionBox.innerHTML=`<article><span class="v24-badge live">${escapeHtml(cycle.title||'Cycle actif')}</span><h3>${escapeHtml(cycle.monthly_question||'Question mensuelle')}</h3><p>${closes}</p><form data-parallel-response-form><label>Votre réponse<textarea name="response" maxlength="4000" required>${escapeHtml(existingResponse?.response_text||'')}</textarea></label><button class="btn btn-primary" type="submit">${existingResponse?'Mettre à jour ma réponse':'Enregistrer ma réponse'}</button></form>${existingResponse?`<small>Dernier enregistrement : ${escapeHtml(friendlyDate(existingResponse.submitted_at))}</small>`:''}</article>`;
    const responseForm=missionBox.querySelector('[data-parallel-response-form]');
    responseForm?.addEventListener('submit',async e=>{
      e.preventDefault();
      const response=String(new FormData(responseForm).get('response')||'').trim();
      if(!response){setStatus(statusBox,'Écrivez une réponse avant d’enregistrer.','error');return}
      const button=responseForm.querySelector('button[type="submit"]');if(button)button.disabled=true;
      const {error}=await s.from('parallel_cycle_responses').upsert({cycle_id:cycle.id,user_id:user.id,character_id:character.id,group_id:null,response_text:response,response_kind:'solo',submitted_at:new Date().toISOString()},{onConflict:'cycle_id,user_id'});
      if(button)button.disabled=false;
      if(error){setStatus(statusBox,'Impossible d’enregistrer la réponse. Vérifiez votre supervision/MFA et réessayez.','error');return}
      setStatus(statusBox,'Réponse du cycle enregistrée dans votre continuité parallèle.','success');
      button.textContent='Mettre à jour ma réponse';
    });
  }

  const eligibility=membership?(
    membership.pioneer_number?`Pionnier #${membership.pioneer_number} · admissible au canon principal et au Monde parallèle`:
    membership.parallel_world_only?'Personnage du Monde parallèle uniquement':'Accès propriétaire / canon principal + Monde parallèle'
  ):'Adhésion en attente';
  stateBox.innerHTML=`<p><strong>${escapeHtml(character.public_name||'Mon personnage')}</strong></p><p>${escapeHtml(eligibility)}</p>${state?`<p>État : ${escapeHtml(state.life_state||'active')} · Réputation : ${escapeHtml(String(state.reputation??0))}</p>${state.location_name?`<p>Lieu : ${escapeHtml(state.location_name)}</p>`:''}${state.faction_name?`<p>Faction : ${escapeHtml(state.faction_name)}</p>`:''}<p>${escapeHtml(stateSummary(state))}</p><small>Dernière mise à jour : ${escapeHtml(friendlyDate(state.updated_at))}</small>`:'<p>Chronique technique en attente.</p>'}`;

  if(historyBox){
    const renderStory=(x,label)=>`<article class="v24-panel"><span class="v24-badge">${label}</span><h3>${escapeHtml(x.title||'Chronique')}</h3><p>${escapeHtml(String(x.content||'').slice(0,700))}${String(x.content||'').length>700?'…':''}</p><small>${escapeHtml(friendlyDate(x.published_at))}</small></article>`;
    const stories=[...personalStories.map(x=>renderStory(x,'Personnel')),...collectiveStories.map(x=>renderStory(x,'Collectif'))];
    historyBox.innerHTML=stories.length?stories.join(''):empty('Aucune histoire publiée pour le moment. Les futures chroniques apparaîtront ici.');
  }
}

load().catch(error=>{
  console.error('[SINJIRA Monde parallèle]',error);
  if(missionBox)missionBox.innerHTML=empty('Le Monde parallèle n’a pas pu charger le cycle actuel.');
  if(stateBox)stateBox.innerHTML=empty('La Chronique n’a pas pu être chargée.');
  if(historyBox)historyBox.innerHTML=empty('Historique temporairement indisponible.');
  setStatus(statusBox,'Monde parallèle temporairement indisponible. Réessayez plus tard.','error');
});
