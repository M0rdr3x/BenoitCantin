import {getSupabase,requireUser,setStatus,escapeHtml,isSinjiraOwner} from './sinjira-supabase.js';

const missionBox=document.querySelector('[data-parallel-mission]');
const stateBox=document.querySelector('[data-parallel-state]');
const status=document.querySelector('[data-parallel-status]');
const empty=msg=>`<div class="v24-empty">${escapeHtml(msg)}</div>`;

function serverMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||/parallel_missions|parallel_character_state|parallel_responses|relation .* does not exist|schema cache/i.test(text);
}

if(missionBox&&stateBox){
  try{
    const user=await requireUser(),s=getSupabase(),owner=isSinjiraOwner(user);
    if(owner){
      try{await s.rpc('ensure_sinjira_owner_character')}catch(_){/* la page garde un état local propre */}
    }
    const {data:characters,error:ce}=await s.from('characters').select('id,public_name,status,visible_to_user,updated_at').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(10);
    if(ce){
      if(owner&&serverMissing(ce)){
        missionBox.innerHTML='<div class="v2433-server-note"><strong>AbyssTime reconnu</strong><br>Le Monde parallèle est prêt côté interface. La Chronique persistante sera activée dès que le serveur narratif sera synchronisé.</div>';
        stateBox.innerHTML=empty('Aucune Chronique persistante chargée pour le moment.');
        setStatus(status,'Votre personnage reste reconnu; seule la persistance serveur du Monde parallèle est en attente.','info');
      }else throw ce;
    }else{
      const rows=Array.isArray(characters)?characters:[];
      const character=rows.find(x=>x.status!=='archived'&&x.visible_to_user)||rows.find(x=>x.status!=='archived')||null;
      if(!character){
        missionBox.innerHTML=owner?'<div class="v2433-server-note"><strong>AbyssTime reconnu</strong><br>La fiche persistante du personnage doit encore être synchronisée avant d’activer les missions.</div>':empty('Votre personnage doit d’abord être créé ou approuvé.');
        stateBox.innerHTML=empty('Aucune Chronique personnelle pour le moment.');
      }else{
        const [missionRes,stateRes]=await Promise.all([
          s.from('parallel_missions').select('id,title,prompt,cycle_id,closes_at,parallel_cycles(title,status)').eq('status','open').order('created_at',{ascending:false}).limit(1),
          s.from('parallel_character_state').select('*').eq('character_id',character.id).maybeSingle()
        ]);
        if(missionRes.error||stateRes.error){
          const err=missionRes.error||stateRes.error;
          if(serverMissing(err)){
            missionBox.innerHTML='<div class="v2433-server-note"><strong>Monde parallèle en préparation</strong><br>Votre personnage est reconnu, mais les cycles et la Chronique persistante attendent encore la synchronisation du serveur.</div>';
            stateBox.innerHTML=empty('Aucune Chronique persistante chargée pour le moment.');
            setStatus(status,'Le Monde parallèle reste accessible en mode préparation. Aucune réponse ne peut être perdue car les missions ne sont pas encore ouvertes.','info');
          }else throw err;
        }else{
          const missions=Array.isArray(missionRes.data)?missionRes.data:[];
          const m=missions[0];
          const state=stateRes.data;
          missionBox.innerHTML=m?`<article><span class="v24-badge live">${escapeHtml(m.parallel_cycles?.title||'Cycle actif')}</span><h3>${escapeHtml(m.title)}</h3><p>${escapeHtml(m.prompt)}</p><form data-parallel-response-form><label>Votre réponse<textarea name="response" maxlength="4000" required></textarea></label><button class="btn btn-primary" type="submit">Enregistrer ma réponse</button></form></article>`:empty('Aucune mission ouverte actuellement.');
          stateBox.innerHTML=state?`<p><strong>${escapeHtml(character.public_name||'Mon personnage')}</strong></p><p>Dernière mise à jour : ${escapeHtml(state.updated_at||'—')}</p><p>${escapeHtml(state.private_summary||'Aucun résumé privé encore enregistré.')}</p>`:empty('La Chronique sera créée lors de votre première participation.');
          const responseForm=missionBox.querySelector('[data-parallel-response-form]');
          responseForm?.addEventListener('submit',async e=>{
            e.preventDefault();
            const response=String(new FormData(responseForm).get('response')||'').trim();
            if(!response){setStatus(status,'Écrivez une réponse avant d’enregistrer.','error');return}
            const {error}=await s.from('parallel_responses').upsert({mission_id:m.id,user_id:user.id,character_id:character.id,response_text:response},{onConflict:'mission_id,user_id'});
            setStatus(status,error?'Impossible d’enregistrer cette réponse pour le moment.':'Réponse enregistrée. Elle reste liée à ce cycle et à votre personnage.',error?'error':'success');
          });
        }
      }
    }
  }catch(e){
    missionBox.innerHTML=empty('Le Monde parallèle n’a pas pu charger les données.');
    stateBox.innerHTML=empty('Aucune donnée chargée.');
    setStatus(status,'Monde parallèle temporairement indisponible. Réessayez plus tard.','error');
  }
}
