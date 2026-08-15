import {getSupabase,requireUser,setStatus,escapeHtml,isSinjiraOwner} from './sinjira-supabase.js';
const missionBox=document.querySelector('[data-parallel-mission]'),stateBox=document.querySelector('[data-parallel-state]'),status=document.querySelector('[data-parallel-status]');
function empty(msg){return `<div class="v24-empty">${escapeHtml(msg)}</div>`}
if(missionBox&&stateBox){try{
  const user=await requireUser(),s=getSupabase(),owner=isSinjiraOwner(user);
  if(owner){try{await s.rpc('ensure_sinjira_owner_character')}catch(e){console.info('V24.3 owner repair RPC not installed yet.',e?.message||e)}}
  const {data:characters,error:ce}=await s.from('characters').select('id,public_name,status,visible_to_user,updated_at').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(10);if(ce)throw ce;
  const rows=Array.isArray(characters)?characters:[];const character=rows.find(x=>x.status!=='archived'&&x.visible_to_user)||rows.find(x=>x.status!=='archived')||null;
  if(!character){missionBox.innerHTML=empty(owner?'AbyssTime est reconnu par le site. Appliquez le correctif Supabase V24.3 pour activer sa Chronique persistante.':'Votre personnage doit d’abord être créé ou approuvé.');stateBox.innerHTML=empty('Aucune Chronique personnelle pour le moment.');}
  else{
    const [{data:missions,error:me},{data:state,error:se}]=await Promise.all([
      s.from('parallel_missions').select('id,title,prompt,cycle_id,closes_at,parallel_cycles(title,status)').eq('status','open').order('created_at',{ascending:false}).limit(1),
      s.from('parallel_character_state').select('*').eq('character_id',character.id).maybeSingle()
    ]);if(me||se)throw me||se;
    const mr=Array.isArray(missions)?missions:[],m=mr[0];
    missionBox.innerHTML=m?`<article><span class="v24-badge live">${escapeHtml(m.parallel_cycles?.title||'Cycle actif')}</span><h3>${escapeHtml(m.title)}</h3><p>${escapeHtml(m.prompt)}</p><form data-parallel-response-form><label>Votre réponse<textarea name="response" maxlength="4000" required></textarea></label><button class="btn btn-primary" type="submit">Enregistrer ma réponse</button></form></article>`:empty('Aucune mission ouverte actuellement.');
    stateBox.innerHTML=state?`<p><strong>${escapeHtml(character.public_name||'Mon personnage')}</strong></p><p>Dernière mise à jour : ${escapeHtml(state.updated_at||'—')}</p><p>${escapeHtml(state.private_summary||'Aucun résumé privé encore enregistré.')}</p>`:empty('La Chronique sera créée lors de votre première participation.');
    const responseForm=missionBox.querySelector('[data-parallel-response-form]');responseForm?.addEventListener('submit',async e=>{e.preventDefault();const response=String(new FormData(responseForm).get('response')||'').trim();const {error}=await s.from('parallel_responses').upsert({mission_id:m.id,user_id:user.id,character_id:character.id,response_text:response},{onConflict:'mission_id,user_id'});setStatus(status,error?error.message:'Réponse enregistrée. Elle reste liée à ce cycle et à votre personnage.',error?'error':'success')});
  }
}catch(e){missionBox.innerHTML=empty('Le Monde parallèle n’a pas pu charger les données.');stateBox.innerHTML=empty('Aucune donnée chargée.');setStatus(status,e.message||'Monde parallèle indisponible.','error')}}
