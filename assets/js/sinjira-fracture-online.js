import {getSupabase,getCurrentUser,requireUser,escapeHtml,formatDate} from './sinjira-supabase.js';

const PAGE=document.body.dataset.fracturePage||'';
const status=document.querySelector('[data-fracture-status]');
const AGENTS={3:1,4:1,5:2,6:2,7:2,8:3,9:3,10:3,11:4,12:4,13:4,14:5,15:5,16:5,17:6,18:6,19:6,20:7};

function show(msg,type='info'){if(!status)return;status.hidden=false;status.textContent=msg;status.dataset.type=type}
function friendlyError(err,fallback){const m=String(err?.message||'');if(/party_code.*ambiguous|ambiguous.*party_code/i.test(m))return 'Le correctif Supabase V24.1 de Fracture Online doit être appliqué.';return m||fallback}
function codeFromUrl(){return (new URLSearchParams(location.search).get('code')||'').trim().toUpperCase()}
function effective(h){return h<=2?3:h}
function modeFor(h){return h===1?'solo':h===2?'duo':'multiplayer'}
function agentsForHumans(h){return AGENTS[effective(h)]||1}
function modeLabel(m){return ({solo:'Solo',duo:'Duo',multiplayer:'Multijoueur'})[m]||m}
function normalizeCode(v){v=String(v||'').trim().toUpperCase().replace(/\s+/g,'');if(v&&!v.startsWith('FRM-'))v=`FRM-${v}`;return v.slice(0,10)}
function factsHtml(p,seat){const items=[`Code ${p.party_code}`,`${p.human_player_count} humain${p.human_player_count>1?'s':''}`,`${p.effective_player_count} siège${p.effective_player_count>1?'s':''}`,modeLabel(p.play_mode),`${p.round_count} rondes`,`${AGENTS[p.effective_player_count]} agent${AGENTS[p.effective_player_count]>1?'s':''} Réseau-Mère`];if(seat)items.splice(1,0,`Votre siège : ${seat}`);return items.map(x=>`<span>${escapeHtml(x)}</span>`).join('')}

async function currentMembership(user,code){
  const s=getSupabase();
  const {data:members,error}=await s.from('fracture_party_members').select('party_id,seat_number').eq('user_id',user.id);
  if(error)throw error;
  for(const m of members||[]){
    const {data:p}=await s.from('fracture_parties').select('*').eq('id',m.party_id).eq('party_code',code).maybeSingle();
    if(p)return {party:p,seat:m.seat_number};
  }
  return null;
}
async function profile(user){const {data}=await getSupabase().from('profiles').select('pseudo,display_name').eq('user_id',user.id).maybeSingle();return data||{}}

async function lobby(){
  const user=await getCurrentUser();
  const state=document.querySelector('[data-account-state]'),auth=document.querySelector('[data-lobby-auth]'),guest=document.querySelector('[data-lobby-guest]');
  if(!user){state.textContent='Mode lecture — connexion requise pour sauvegarder';guest.hidden=false;return}
  const p=await profile(user);state.textContent=`Connecté : ${p.pseudo||p.display_name||user.email}`;auth.hidden=false;
  const create=document.querySelector('[data-create-party]'),count=create.elements.human_player_count,round=create.elements.round_count,duo=document.querySelector('[data-duo-first]'),summary=document.querySelector('[data-create-summary]');
  function recalc(){
    const h=Math.max(1,Math.min(20,Number(count.value)||1));count.value=h;duo.hidden=h!==2;
    if(h<13&&round.value==='6')round.value='10';
    [...round.options].forEach(o=>{if(o.value==='6')o.disabled=h<13});
    const n=effective(h),a=AGENTS[n],r=Number(round.value);
    summary.innerHTML=`<strong>${escapeHtml(modeLabel(modeFor(h)))}</strong> · ${n} sièges actifs · ${a} agent${a>1?'s':''} Réseau-Mère · centre de ronde : ${3*n} cartes · ${r} rondes.`;
  }
  count.addEventListener('input',recalc);round.addEventListener('change',recalc);recalc();
  create.addEventListener('submit',async e=>{
    e.preventDefault();try{
      const h=Number(count.value),r=Number(round.value),first=Number(create.elements.duo_first_player_seat.value||1);
      const {data,error}=await getSupabase().rpc('create_fracture_party',{p_human_player_count:h,p_round_count:r,p_duo_first_player_seat:first});
      if(error)throw error;const row=Array.isArray(data)?data[0]:data;
      location.href=`partie.html?code=${encodeURIComponent(row.party_code)}`;
    }catch(err){show(friendlyError(err,'Création impossible.'),'error')}
  });
  const join=document.querySelector('[data-join-party]');
  join.addEventListener('submit',async e=>{
    e.preventDefault();try{
      const code=normalizeCode(join.elements.party_code.value),seat=Number(join.elements.seat_number.value)||null;
      const {data,error}=await getSupabase().rpc('join_fracture_party',{p_party_code:code,p_seat_number:seat});
      if(error)throw error;const row=Array.isArray(data)?data[0]:data;
      location.href=`partie.html?code=${encodeURIComponent(row.party_code)}`;
    }catch(err){show(friendlyError(err,'Impossible de rejoindre la partie.'),'error')}
  });
  const {data:mine,error}=await getSupabase().from('fracture_party_members').select('party_id,seat_number,joined_at').eq('user_id',user.id).order('joined_at',{ascending:false}).limit(12);
  if(!error&&mine?.length){
    const rows=[];
    for(const m of mine){const {data:party}=await getSupabase().from('fracture_parties').select('*').eq('id',m.party_id).maybeSingle();if(party)rows.push({party,seat:m.seat_number})}
    const wrap=document.querySelector('[data-my-parties]'),list=document.querySelector('[data-my-parties-list]');wrap.hidden=false;
    list.innerHTML=rows.map(({party,seat})=>`<article class="fracture-party-row"><div><strong>${escapeHtml(party.party_code)}</strong><span>Siège ${seat} · ${party.human_player_count} humain${party.human_player_count>1?'s':''} · ${party.round_count} rondes · ${escapeHtml(party.status)}</span></div><a class="btn btn-secondary btn-small" href="partie.html?code=${encodeURIComponent(party.party_code)}">Continuer</a></article>`).join('');
  }
}

function inputVal(el){return el.type==='checkbox'?el.checked:el.value}
function setInput(el,v){if(!el)return;if(el.type==='checkbox')el.checked=Boolean(v);else el.value=v??''}
function formDataObject(form){const o={};form.querySelectorAll('[name]').forEach(el=>{o[el.name]=inputVal(el)});return o}
function fillForm(form,data){for(const [k,v] of Object.entries(data||{}))setInput(form.elements[k],v)}
function accusationHtml(count,seat,prefix='accusation'){return Array.from({length:count},(_,i)=>`<label>${i+1}<input name="${prefix}_${i+1}" type="number" min="1" max="20" data-accusation data-self-seat="${seat||''}"></label>`).join('')}
function validateAccusations(form,count,seat){
  const vals=[...form.querySelectorAll('[data-accusation]')].map(x=>Number(x.value)).filter(Boolean);
  if(vals.length&&vals.length!==count)throw new Error(`L’accusation finale doit contenir exactement ${count} numéro${count>1?'s':''}.`);
  if(new Set(vals).size!==vals.length)throw new Error('Les numéros de l’accusation finale doivent être distincts.');
  if(seat&&vals.includes(seat))throw new Error('Vous ne pouvez pas vous accuser vous-même.');
}
function personalSheet(party,seat,profile){
  const a=AGENTS[party.effective_player_count];
  const rows=Array.from({length:party.round_count},(_,i)=>{const n=i+1;return `<tr><td>${n}</td><td><input name="r${n}_card1" placeholder="R/RM + pts"></td><td><input name="r${n}_card2" placeholder="R/RM + pts"></td><td><select name="r${n}_report"><option value="">—</option><option>R</option><option>RM</option><option>ÉQ</option></select></td><td><input class="fracture-proof" name="r${n}_proof" type="checkbox"></td><td><input name="r${n}_suspect" type="number" min="1" max="${party.effective_player_count}"></td></tr>`}).join('');
  return `<form class="fracture-sheet" data-private-doc data-document-key="seat_${seat}_self" data-document-type="player">
    <div class="fracture-sheet-head"><div><span class="eyebrow">Fiche joueur privée</span><h2>Joueur ${seat}</h2><p>${escapeHtml(profile.pseudo||profile.display_name||'Compte SINJIRA')} · ${a} accusation${a>1?'s':''} requise${a>1?'s':''} en fin de partie.</p></div><span class="fracture-save-state" data-save-state>Prêt</span></div>
    <div class="fracture-sheet-meta"><label>Nom / pseudo<input name="display_name" value="${escapeHtml(profile.pseudo||profile.display_name||'')}"></label><label>N° joueur<input name="seat_number" value="${seat}" readonly></label><label>Identité — révélation finale<input name="final_identity" placeholder="À remplir seulement à la fin"></label></div>
    <div class="fracture-sheet-table-wrap"><table class="fracture-sheet-table"><thead><tr><th>Tour</th><th>Carte 1<br>R/RM + pts</th><th>Carte 2<br>R/RM + pts</th><th>Rapport<br>R/RM/ÉQ</th><th>Preuve</th><th>Suspect<br>N° joueur</th></tr></thead><tbody>${rows}</tbody></table></div>
    <h3>Accusation finale — exactement ${a} numéro${a>1?'s':''}</h3><div class="fracture-accusations">${accusationHtml(a,seat)}</div>
    <div class="fracture-endgame-actions"><button class="btn btn-secondary" type="button" data-save-now>Sauvegarder maintenant</button><button class="btn btn-secondary" type="button" data-print-sheet>Imprimer / enregistrer en PDF</button></div>
  </form>`;
}
function invisibleSheet(party,seat){
  const a=AGENTS[party.effective_player_count],first=party.duo_first_player_seat||1;
  const rows=Array.from({length:party.round_count},(_,i)=>{const n=i+1,controller=((n%2===1)?first:(first===1?2:1)),mine=controller===seat;return `<tr><td>${n}</td><td><input name="r${n}_control" value="${mine?'Oui':'Non'}" readonly></td><td><input name="r${n}_card1" placeholder="R/RM + pts"></td><td><input name="r${n}_card2" placeholder="R/RM + pts"></td><td><select name="r${n}_report"><option value="">—</option><option>R</option><option>RM</option><option>ÉQ</option></select></td><td><input class="fracture-proof" name="r${n}_proof" type="checkbox"></td><td><input name="r${n}_suspect" type="number" min="1" max="3"></td></tr>`}).join('');
  return `<form class="fracture-sheet" data-private-doc data-document-key="seat_${seat}_invisible_3" data-document-type="invisible3">
    <div class="fracture-sheet-head"><div><span class="eyebrow">Fiche privée — Joueur invisible 3</span><h2>Copie privée du Joueur ${seat}</h2><p>L’identité du siège 3 ne doit jamais être regardée avant la révélation finale.</p></div><span class="fracture-save-state" data-save-state>Prêt</span></div>
    <div class="fracture-warning">Le Joueur invisible 3 ne dépose pas de vote final. Le champ final ci-dessous est une hypothèse privée de votre fiche et ne compte jamais dans le vote officiel.</div>
    <div class="fracture-sheet-table-wrap"><table class="fracture-sheet-table"><thead><tr><th>Tour</th><th>Contrôle ce tour?</th><th>Carte 1</th><th>Carte 2</th><th>Rapport</th><th>Preuve</th><th>Suspect / hypothèse</th></tr></thead><tbody>${rows}</tbody></table></div>
    <h3>Hypothèse finale privée — ${a} numéro${a>1?'s':''}</h3><div class="fracture-accusations">${accusationHtml(a,null,'hypothese')}</div>
    <div class="fracture-endgame-actions"><button class="btn btn-secondary" type="button" data-save-now>Sauvegarder maintenant</button><button class="btn btn-secondary" type="button" data-print-sheet>Imprimer / enregistrer en PDF</button></div>
  </form>`;
}
function soloSheet(party,seat){
  const rows=Array.from({length:party.round_count},(_,i)=>{const n=i+1;return `<tr><td>${n}</td><td><textarea name="r${n}_seat1" placeholder="C1 / C2 / rapport"></textarea></td><td><textarea name="r${n}_invisible2" placeholder="C1 / C2 / rapport"></textarea></td><td><textarea name="r${n}_invisible3" placeholder="C1 / C2 / rapport"></textarea></td><td><textarea name="r${n}_notes" placeholder="Notes / hypothèses"></textarea></td></tr>`}).join('');
  return `<form class="fracture-sheet" data-private-doc data-document-key="solo_combined" data-document-type="solo">
    <div class="fracture-sheet-head"><div><span class="eyebrow">Fiche Solo — 3 sièges</span><h2>Joueur 1 + Invisibles 2 et 3</h2><p>Dans chaque case : Carte 1 / Carte 2 / Rapport. Ajoutez * si la Preuve du siège a été utilisée.</p></div><span class="fracture-save-state" data-save-state>Prêt</span></div>
    <div class="fracture-sheet-table-wrap"><table class="fracture-sheet-table fracture-solo-table"><thead><tr><th>Tour</th><th>Joueur 1</th><th>Invisible 2</th><th>Invisible 3</th><th>Notes / hypothèses</th></tr></thead><tbody>${rows}</tbody></table></div>
    <div class="fracture-sheet-meta"><label>Identité Joueur 1<input name="final_identity_1" placeholder="Révélation finale"></label><label>Identité Invisible 2<input name="final_identity_2" placeholder="Révélation finale"></label><label>Identité Invisible 3<input name="final_identity_3" placeholder="Révélation finale"></label></div>
    <h3>Accusation du joueur humain — 1 numéro</h3><div class="fracture-accusations">${accusationHtml(1,1)}</div>
    <div class="fracture-endgame-actions"><button class="btn btn-secondary" type="button" data-save-now>Sauvegarder maintenant</button><button class="btn btn-secondary" type="button" data-print-sheet>Imprimer / enregistrer en PDF</button></div>
  </form>`;
}
async function loadDoc(user,party,form){
  const key=form.dataset.documentKey;
  const {data,error}=await getSupabase().from('fracture_player_documents').select('fields').eq('party_id',party.id).eq('user_id',user.id).eq('document_key',key).maybeSingle();
  if(error)throw error;if(data?.fields)fillForm(form,data.fields);
}
async function saveDoc(user,party,seat,form){
  const state=form.querySelector('[data-save-state]');try{
    if(form.dataset.documentType==='player')validateAccusations(form,AGENTS[party.effective_player_count],seat);
    state.textContent='Sauvegarde…';
    const {error}=await getSupabase().from('fracture_player_documents').upsert({
      party_id:party.id,user_id:user.id,document_key:form.dataset.documentKey,document_type:form.dataset.documentType,seat_number:seat,fields:formDataObject(form)
    },{onConflict:'party_id,user_id,document_key'});
    if(error)throw error;state.textContent=`Sauvegardé ${new Date().toLocaleTimeString('fr-CA',{hour:'2-digit',minute:'2-digit'})}`;
  }catch(e){state.textContent='Erreur';show(e.message||'Sauvegarde impossible.','error')}
}
function bindAutosave(user,party,seat,form){
  let timer=null;form.addEventListener('input',()=>{form.querySelector('[data-save-state]').textContent='Modifications…';clearTimeout(timer);timer=setTimeout(()=>saveDoc(user,party,seat,form),900)});
  form.querySelector('[data-save-now]')?.addEventListener('click',()=>saveDoc(user,party,seat,form));
  form.querySelector('[data-print-sheet]')?.addEventListener('click',()=>window.print());
}
async function partyPage(){
  const user=await requireUser('/compte/connexion.html'),code=codeFromUrl();if(!code){location.href='jouer.html';return}
  const membership=await currentMembership(user,code);if(!membership){show('Votre compte ne fait pas partie de cette partie. Rejoignez-la avec son code.','error');return}
  const {party,seat}=membership,p=await profile(user);
  document.querySelector('[data-party-heading]').textContent=`Partie ${party.party_code}`;
  document.querySelector('[data-party-summary]').textContent=party.play_mode==='solo'?'Mode Solo officiel — 1 humain, 3 sièges.':party.play_mode==='duo'?'Mode Duo officiel — 2 humains + Joueur invisible 3.':`Partie à ${party.human_player_count} joueurs humains.`;
  document.querySelectorAll('[data-party-facts]').forEach(n=>n.innerHTML=factsHtml(party,seat));
  const end=document.querySelector('[data-endgame-link]');end.href=`fin-de-partie.html?code=${encodeURIComponent(code)}`;if(user.id!==party.owner_user_id){end.textContent='Voir la fin de partie'}
  document.querySelector('[data-copy-party-code]')?.addEventListener('click',async()=>{await navigator.clipboard.writeText(party.party_code);show('Code copié.','success')});
  const workspace=document.querySelector('[data-player-workspace]');
  if(party.play_mode==='solo')workspace.innerHTML=soloSheet(party,seat);
  else if(party.play_mode==='duo')workspace.innerHTML=`<div class="fracture-tabs"><button type="button" aria-selected="true" data-tab="self">Ma fiche</button><button type="button" aria-selected="false" data-tab="inv">Ma fiche du Joueur invisible 3</button></div><div class="fracture-tab-panel" data-panel="self">${personalSheet(party,seat,p)}</div><div class="fracture-tab-panel" data-panel="inv" hidden>${invisibleSheet(party,seat)}</div>`;
  else workspace.innerHTML=personalSheet(party,seat,p);
  workspace.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{workspace.querySelectorAll('[data-tab]').forEach(x=>x.setAttribute('aria-selected',x===b?'true':'false'));workspace.querySelectorAll('[data-panel]').forEach(x=>x.hidden=x.dataset.panel!==b.dataset.tab)}));
  for(const form of workspace.querySelectorAll('[data-private-doc]')){await loadDoc(user,party,form);bindAutosave(user,party,seat,form)}
}
function endgameRows(party){return Array.from({length:party.round_count},(_,i)=>{const n=i+1;return `<tr><td>${n}</td><td><input name="r${n}_resistance" type="number" min="0"></td><td><input name="r${n}_network" type="number" min="0"></td><td><select name="r${n}_winner"><option value="">—</option><option value="R">R</option><option value="RM">RM</option><option value="EQ">ÉQ</option></select></td><td><input name="r${n}_notes" maxlength="300"></td></tr>`}).join('')}
function endgameForm(party,editable){
  return `<form data-endgame-form>
    ${editable?'':'<div class="fracture-warning">Vous pouvez consulter cette fin de partie, mais seul le créateur de la partie peut la modifier et la transmettre à SINJIRA.</div>'}
    <div class="fracture-sheet-table-wrap"><table class="fracture-sheet-table"><thead><tr><th>Tour</th><th>Points Résistance</th><th>Points Réseau-Mère</th><th>Gagnant R / RM / ÉQ</th><th>Notes</th></tr></thead><tbody>${endgameRows(party)}</tbody></table></div>
    <div class="fracture-endgame-summary">
      <label>Agents Réseau-Mère<input name="network_agents" type="number" readonly value="${AGENTS[party.effective_player_count]}"></label>
      <label>Bonus Résistance<input name="bonus_resistance" type="number" min="0" value="0"></label>
      <label>Bonus Réseau-Mère<input name="bonus_network" type="number" min="0" value="0"></label>
      <label>Rondes gagnées R<input name="rounds_resistance" readonly></label>
      <label>Total final R<input name="total_resistance" readonly></label>
      <label>Total final RM<input name="total_network" readonly></label>
      <label>Rondes gagnées RM<input name="rounds_network" readonly></label>
      <label>Égalités<input name="rounds_tied" readonly></label>
      <label>Gagnant<input name="winner_final" readonly></label>
      <label>Départage requis?<input name="tiebreak_required" readonly></label>
    </div>
    <div class="fracture-endgame-actions">
      ${editable?'<button class="btn btn-secondary" type="button" data-save-endgame>Sauvegarder la fin de partie</button><button class="btn btn-primary" type="button" data-submit-endgame>Terminer et transmettre uniquement cette fin de partie à SINJIRA</button>':''}
      <button class="btn btn-secondary" type="button" data-print-endgame>Imprimer / enregistrer en PDF</button>
    </div>
  </form>`;
}
function calculateEndgame(form,party){
  let rp=0,np=0,rr=0,nr=0,tied=0;
  for(let n=1;n<=party.round_count;n++){rp+=Number(form.elements[`r${n}_resistance`].value)||0;np+=Number(form.elements[`r${n}_network`].value)||0;const w=form.elements[`r${n}_winner`].value;if(w==='R')rr++;else if(w==='RM')nr++;else if(w==='EQ')tied++}
  const tr=rp+(Number(form.elements.bonus_resistance.value)||0),tn=np+(Number(form.elements.bonus_network.value)||0);
  form.elements.rounds_resistance.value=rr;form.elements.rounds_network.value=nr;form.elements.rounds_tied.value=tied;form.elements.total_resistance.value=tr;form.elements.total_network.value=tn;
  let winner='',tb='NON';if(tr>tn)winner='Résistance';else if(tn>tr)winner='Réseau-Mère';else if(rr>nr)winner='Résistance';else if(nr>rr)winner='Réseau-Mère';else{winner='Égalité';tb='OUI'}
  form.elements.winner_final.value=winner;form.elements.tiebreak_required.value=tb;
}
async function endgamePage(){
  const user=await requireUser('/compte/connexion.html'),code=codeFromUrl();if(!code){document.querySelector('[data-endgame-workspace]').innerHTML='<p>Ouvrez la Feuille de fin de partie depuis votre partie active.</p><a class="btn btn-primary" href="jouer.html">Mes parties</a>';return}
  const membership=await currentMembership(user,code);if(!membership){show('Votre compte ne fait pas partie de cette partie.','error');return}
  const {party}=membership,editable=user.id===party.owner_user_id,workspace=document.querySelector('[data-endgame-workspace]');
  document.querySelectorAll('[data-party-facts]').forEach(n=>n.innerHTML=factsHtml(party,membership.seat));
  workspace.innerHTML=endgameForm(party,editable);const form=workspace.querySelector('[data-endgame-form]');
  const {data:existing,error}=await getSupabase().from('fracture_endgame_reports').select('fields,submitted_at').eq('party_id',party.id).maybeSingle();if(error)throw error;if(existing?.fields)fillForm(form,existing.fields);
  calculateEndgame(form,party);
  form.addEventListener('input',()=>calculateEndgame(form,party));
  if(!editable)form.querySelectorAll('input,select,textarea').forEach(x=>x.disabled=true);
  async function save(){
    calculateEndgame(form,party);
    const {error}=await getSupabase().from('fracture_endgame_reports').upsert({party_id:party.id,owner_user_id:user.id,fields:formDataObject(form)},{onConflict:'party_id'});
    if(error)throw error;show('Feuille de fin de partie sauvegardée.','success')
  }
  workspace.querySelector('[data-save-endgame]')?.addEventListener('click',async()=>{try{await save()}catch(e){show(e.message||'Sauvegarde impossible.','error')}});
  workspace.querySelector('[data-submit-endgame]')?.addEventListener('click',async()=>{
    if(!confirm('Confirmer la transmission à SINJIRA? Seule cette feuille de fin de partie sera envoyée. Aucune fiche privée de joueur ne sera incluse.'))return;
    try{await save();const {data,error}=await getSupabase().functions.invoke('submit-fracture-endgame',{body:{party_code:party.party_code}});if(error||!data?.ok)throw new Error(data?.error||error?.message||'Transmission impossible');show(data.email_sent?'Fin de partie transmise à SINJIRA et courriel envoyé.':'Fin de partie transmise à SINJIRA. Le rapport est disponible dans l’administration; le service courriel n’est pas encore actif.','success')}catch(e){show(e.message||'Transmission impossible.','error')}
  });
  workspace.querySelector('[data-print-endgame]')?.addEventListener('click',()=>window.print());
}
(async()=>{try{if(PAGE==='lobby')await lobby();else if(PAGE==='party')await partyPage();else if(PAGE==='endgame')await endgamePage()}catch(e){show(e?.message||'Une erreur est survenue.','error')}})();
