import {getSupabase,getCurrentUser,escapeHtml,friendlyBackendMessage} from './sinjira-supabase.js';
const AGENTS={3:1,4:1,5:2,6:2,7:2,8:3,9:3,10:3,11:4,12:4,13:4,14:5,15:5,16:5,17:6,18:6,19:6,20:7};
const status=document.querySelector('[data-fracture-status]');
const accessStatus=document.querySelector('[data-fracture-access-status]');
const show=(m,t='info')=>{if(!status)return;status.hidden=false;status.textContent=friendlyBackendMessage(m,m);status.dataset.type=t};
const mode=h=>h===1?'Solo':h===2?'Duo':'Multijoueur';
const eff=h=>h<=2?3:h;
function normalizeCode(v){v=String(v||'').trim().toUpperCase().replace(/\s+/g,'');if(v&&!v.startsWith('FRM-'))v=`FRM-${v}`;return v.slice(0,10)}
function specific(err){const m=String(err?.message||'');if(/FRACTURE_(?:ACCESS|ENTITLEMENT)_REQUIRED/i.test(m))return 'Votre compte ne possède pas encore de droit d’accès Fracture.';if(/GAME_ALREADY_STARTED/i.test(m))return 'Cette partie a déjà commencé.';if(/PARTY_FULL/i.test(m))return 'Tous les sièges humains sont occupés.';if(/PARTY_NOT_FOUND/i.test(m))return 'Partie introuvable.';if(/SEAT_(?:TAKEN|ALREADY_TAKEN)/i.test(m))return 'Ce siège est déjà occupé.';if(/INVALID_SEAT/i.test(m))return 'Ce numéro de siège n’est pas valide pour cette partie.';if(/SOLO_PARTY_CANNOT_BE_JOINED/i.test(m))return 'Une partie Solo ne peut pas être rejointe par un deuxième compte.';if(/INVALID_PLAYER_COUNT/i.test(m))return 'Le nombre de joueurs doit être compris entre 1 et 20.';return friendlyBackendMessage(m,'Action Fracture impossible.')}
function setFormsEnabled(enabled){document.querySelectorAll('[data-create-party] input,[data-create-party] select,[data-create-party] button,[data-join-party] input,[data-join-party] button').forEach(el=>{el.disabled=!enabled})}
async function verifyRuntime(){
  const s=getSupabase();
  const [{data:engine,error:engineError},{data:access,error:accessError}]=await Promise.all([
    s.rpc('fracture_engine_health'),
    s.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'})
  ]);
  if(engineError){
    setFormsEnabled(false);
    if(accessStatus){accessStatus.textContent=friendlyBackendMessage(engineError.message,'Le moteur Fracture n’est pas disponible.');accessStatus.dataset.statusType='error'}
    return false;
  }
  const tables=engine?.tables||{},functions=engine?.functions||{};
  const missingTables=Object.entries(tables).filter(([,ok])=>ok!==true).map(([name])=>`table:${name}`);
  const missingFunctions=Object.entries(functions).filter(([,ok])=>ok!==true).map(([name])=>`rpc:${name}`);
  const missing=[...missingTables,...missingFunctions];
  if(engine?.ok!==true||missing.length){
    setFormsEnabled(false);
    if(accessStatus){accessStatus.textContent=`Moteur Fracture incomplet${missing.length?` : ${missing.join(', ')}`:''}. Synchronisation Supabase requise.`;accessStatus.dataset.statusType='error'}
    return false;
  }
  if(accessError){
    setFormsEnabled(false);
    if(accessStatus){accessStatus.textContent=friendlyBackendMessage(accessError.message,'Impossible de vérifier votre droit d’accès Fracture.');accessStatus.dataset.statusType='error'}
    return false;
  }
  if(access!==true){
    setFormsEnabled(false);
    if(accessStatus){accessStatus.textContent='Votre compte est connecté, mais aucun droit Fracture du Réseau-Mère n’est actif.';accessStatus.dataset.statusType='warning'}
    return false;
  }
  setFormsEnabled(true);
  if(accessStatus){accessStatus.textContent=`Moteur Fracture ${engine.engine_version||'serveur'} opérationnel · tables et RPC critiques confirmées · droit d’accès confirmé.`;accessStatus.dataset.statusType='success'}
  return true;
}
async function boot(){
 const user=await getCurrentUser(),state=document.querySelector('[data-account-state]'),auth=document.querySelector('[data-lobby-auth]'),guest=document.querySelector('[data-lobby-guest]');
 if(!user){state.textContent='Connexion requise';guest.hidden=false;if(accessStatus)accessStatus.textContent='Connectez-vous pour vérifier le moteur et votre droit d’accès Fracture.';return}
 const {data:p}=await getSupabase().from('profiles').select('pseudo,display_name').eq('user_id',user.id).maybeSingle();state.textContent=`Connecté : ${p?.pseudo||p?.display_name||user.email}`;auth.hidden=false;
 const create=document.querySelector('[data-create-party]'),count=create.elements.human_player_count,round=create.elements.round_count,duo=document.querySelector('[data-duo-first]'),summary=document.querySelector('[data-create-summary]');
 const recalc=()=>{const h=Math.max(1,Math.min(20,Number(count.value)||1));count.value=h;duo.hidden=h!==2;if(h<13&&round.value==='6')round.value='10';[...round.options].forEach(o=>{if(o.value==='6')o.disabled=h<13});const n=eff(h);summary.innerHTML=`<strong>${mode(h)}</strong> · ${n} sièges · ${AGENTS[n]} agent(s) Réseau-Mère · ${Number(round.value)} rondes${h<=2?' · sièges invisibles automatisés':''}.`};
 count.addEventListener('input',recalc);round.addEventListener('change',recalc);recalc();
 setFormsEnabled(false);
 const ready=await verifyRuntime();
 if(!ready)show('La création et la jonction restent bloquées tant que le moteur ou le droit d’accès n’est pas confirmé.','error');
 create.addEventListener('submit',async e=>{e.preventDefault();try{const h=Number(count.value),r=Number(round.value),first=Number(create.elements.duo_first_player_seat.value||1);const {data,error}=await getSupabase().rpc('create_fracture_party',{p_human_player_count:h,p_round_count:r,p_duo_first_player_seat:first});if(error)throw error;const row=Array.isArray(data)?data[0]:data;if(!row?.party_code)throw new Error('Réponse serveur incomplète : code de partie absent.');location.href=`partie.html?code=${encodeURIComponent(row.party_code)}`}catch(err){show(specific(err),'error')}});
 const join=document.querySelector('[data-join-party]');join.addEventListener('submit',async e=>{e.preventDefault();try{const c=normalizeCode(join.elements.party_code.value),seat=Number(join.elements.seat_number.value)||null;if(!/^FRM-[A-Z0-9]{6}$/.test(c))throw new Error('Le code de partie doit avoir le format FRM-ABC123.');const {data,error}=await getSupabase().rpc('join_fracture_party',{p_party_code:c,p_seat_number:seat});if(error)throw error;const row=Array.isArray(data)?data[0]:data;if(!row?.party_code)throw new Error('Réponse serveur incomplète : code de partie absent.');location.href=`partie.html?code=${encodeURIComponent(row.party_code)}`}catch(err){show(specific(err),'error')}});
 const {data:members,error:membersError}=await getSupabase().from('fracture_party_members').select('party_id,seat_number,joined_at').eq('user_id',user.id).order('joined_at',{ascending:false}).limit(12);if(membersError)console.warn('[Fracture lobby memberships]',membersError);if(members?.length){const ids=[...new Set(members.map(x=>x.party_id).filter(Boolean))],{data:parties,error:partiesError}=await getSupabase().from('fracture_parties').select('id,party_code,human_player_count,round_count,status,engine_status,updated_at').in('id',ids);if(partiesError)console.warn('[Fracture lobby parties]',partiesError);const byId=new Map((parties||[]).map(x=>[x.id,x]));const rows=members.map(m=>({m,p:byId.get(m.party_id)})).filter(x=>x.p);if(rows.length){const wrap=document.querySelector('[data-my-parties]'),list=document.querySelector('[data-my-parties-list]');wrap.hidden=false;list.innerHTML=rows.map(({m,p})=>`<article class="fracture-party-row"><div><strong>${escapeHtml(p.party_code)}</strong><span>Siège ${m.seat_number} · ${p.human_player_count} humain(s) · ${escapeHtml(p.engine_status||p.status||'inconnu')}</span></div><a class="btn btn-secondary btn-small" href="partie.html?code=${encodeURIComponent(p.party_code)}">${p.engine_status==='finished'?'Voir':'Continuer'}</a></article>`).join('')}}
}
boot().catch(err=>show(err.message||'Impossible de charger Fracture.','error'));
