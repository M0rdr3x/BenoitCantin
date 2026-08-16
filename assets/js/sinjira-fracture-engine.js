import {getSupabase,requireUser,escapeHtml,friendlyBackendMessage} from './sinjira-supabase.js';

const UI_VERSION='24.4.23';
const code=(new URLSearchParams(location.search).get('code')||'').trim().toUpperCase();
const root=document.querySelector('[data-engine-root]');
const status=document.querySelector('[data-fracture-status]');
let current=null;
let busy=false;
let loading=false;
let timer=null;
let requestSerial=0;
let lastRenderedStateSignature='';
let keepDraft={key:'',selected:new Set()};
let reportDraft={key:'',values:{report:'',suspect:'',proof:''}};
let voteDraft={key:'',selected:new Set()};

const phaseLabels={
  lobby:'Salon',
  choose_keep:'Choisir 2 cartes',
  pick:'Sélection centrale',
  report:'Rapport / Preuve / Soupçon',
  final_vote:'Accusation finale',
  finished:'Partie terminée'
};

const factionMeta=value=>{
  if(value==='R') return {code:'R',label:'Résistance',cardClass:'engine-card--r'};
  if(value==='RM') return {code:'RM',label:'Réseau-Mère',cardClass:'engine-card--rm'};
  return {code:'?',label:'Faction inconnue',cardClass:'engine-card--unknown'};
};

const identityMeta=value=>{
  if(value==='resistance') return {
    code:'R',
    label:'Résistance',
    className:'engine-identity--r',
    description:'Vous appartenez à la Résistance.'
  };
  if(value==='network') return {
    code:'RM',
    label:'Réseau-Mère',
    className:'engine-identity--rm',
    description:'Vous appartenez au Réseau-Mère.'
  };
  return {
    code:'?',
    label:'Identité non attribuée',
    className:'engine-identity--unknown',
    description:'Le serveur n’a pas encore renvoyé votre identité privée.'
  };
};

const identityLabel=value=>identityMeta(value).label;
const winnerLabel=value=>value==='resistance'?'Résistance':value==='network'?'Réseau-Mère':'—';

function draftKey(state,phase=state?.phase){
  return `${state?.party_code||code}|${phase||'unknown'}|${Number(state?.round)||0}|${Number(state?.my_seat)||0}`;
}

function stateSignature(state){
  try{return JSON.stringify(state);}catch{return '';}
}

function isEditingControl(){
  const active=document.activeElement;
  return Boolean(active&&root&&root.contains(active)&&active.matches('select,input,textarea'));
}

function getKeepSelection(state,cards){
  const key=draftKey(state,'choose_keep');
  if(keepDraft.key!==key) keepDraft={key,selected:new Set()};
  const valid=new Set((cards||[]).map(card=>Number(card.id)));
  [...keepDraft.selected].forEach(id=>{if(!valid.has(id)) keepDraft.selected.delete(id);});
  return keepDraft.selected;
}

function getReportValues(state){
  const key=draftKey(state,'report');
  if(reportDraft.key!==key){
    reportDraft={key,values:{report:'',suspect:'',proof:''}};
  }
  return reportDraft.values;
}

function getVoteSelection(state,others){
  const key=draftKey(state,'final_vote');
  if(voteDraft.key!==key) voteDraft={key,selected:new Set()};
  const valid=new Set((others||[]).map(seat=>Number(seat.seat)));
  [...voteDraft.selected].forEach(id=>{if(!valid.has(id)) voteDraft.selected.delete(id);});
  return voteDraft.selected;
}

function show(msg,type='info'){
  if(!status) return;
  status.hidden=false;
  status.textContent=friendlyBackendMessage(msg,msg);
  status.dataset.type=type;
}

function clearShow(){
  if(status) status.hidden=true;
}

function cardHtml(card,selectable=false,selected=false){
  if(!card) return '';
  const meta=factionMeta(card.faction);
  const points=Number(card.points)||0;
  return `<button class="engine-card engine-card--face ${meta.cardClass}${selected?' is-selected':''}" ${selectable?'':'disabled'} type="button" data-card-id="${card.id}" aria-label="Carte ${escapeHtml(meta.label)}, ${points>=0?'+':''}${points} point${Math.abs(points)!==1?'s':''}">
    <span class="engine-card__eyebrow">Carte Opération</span>
    <span class="engine-card__faction">${escapeHtml(meta.label)}</span>
    <strong class="engine-card__points">${points>=0?'+':''}${points}</strong>
    <span class="engine-card__code" aria-hidden="true">${escapeHtml(meta.code)}</span>
  </button>`;
}

function backHtml(card,enabled){
  const position=Number(card?.position)||0;
  return `<button class="engine-card engine-card--back" type="button" data-center-card="${card.id}" ${enabled?'':'disabled'} aria-label="Carte face cachée, position ${position}">
    <span class="sr-only">Fracture du Réseau-Mère — carte face cachée</span>
    <span class="engine-card__position" aria-hidden="true">${position}</span>
  </button>`;
}

function identityHtml(state){
  const meta=identityMeta(state?.my_identity);
  const ready=state?.my_identity==='resistance'||state?.my_identity==='network';
  const privacyText=ready
    ? 'Visible uniquement sur votre écran. Les identités des autres joueurs restent cachées jusqu’à la fin officielle de la partie.'
    : 'Votre identité devrait être attribuée dès le démarrage. Si ce message persiste, rechargez la partie.';
  return `<aside class="engine-identity ${meta.className}" data-private-identity-card data-private-identity-status="${ready?'ready':'missing'}" aria-live="polite" aria-label="Carte d’identité secrète : ${escapeHtml(meta.label)}">
    <div class="engine-identity__mark" aria-hidden="true">${escapeHtml(meta.code)}</div>
    <div class="engine-identity__content">
      <span class="engine-identity__eyebrow">Carte d’identité secrète · vous seul</span>
      <span class="engine-identity__role-label">Votre faction pour cette partie</span>
      <strong>${escapeHtml(meta.label)}</strong>
      <small>${escapeHtml(meta.description)} ${escapeHtml(privacyText)}</small>
    </div>
    <div class="engine-identity__privacy" aria-hidden="true">NE PAS MONTRER AUX AUTRES JOUEURS</div>
  </aside>`;
}

async function privacyHealth(){
  const {data,error}=await getSupabase().rpc('fracture_engine_privacy_health');
  if(error) throw error;
  if(!data?.ok||data?.privacy_version!=='24.4.15'){
    throw new Error('La protection de confidentialité Fracture V24.4.15 n’est pas active sur le serveur.');
  }
  return data;
}

async function stateRpc(){
  const {data,error}=await getSupabase().rpc('fracture_engine_get_state_safe',{p_party_code:code});
  if(error) throw error;
  return data;
}

async function edgeErrorMessage(error){
  try{
    const response=error?.context;
    if(response&&typeof response.clone==='function'){
      const payload=await response.clone().json();
      if(payload?.error) return payload.error;
    }
  }catch{}
  return error?.message||'Action refusée par le moteur de jeu.';
}

async function gatewayAction(name,args={}){
  const {data,error}=await getSupabase().functions.invoke('fracture-engine-gateway',{
    body:{action:name,args}
  });
  if(error) throw new Error(await edgeErrorMessage(error));
  if(data?.ok===false) throw new Error(data.error||'Action refusée par le moteur de jeu.');
  return data;
}

function scoreHtml(score){
  return `<div class="engine-score">
    <article class="engine-score--r"><span>Résistance</span><strong>${Number(score?.R||0)+Number(score?.R_bonus||0)}</strong><small>${Number(score?.R||0)} + bonus ${Number(score?.R_bonus||0)}</small></article>
    <article class="engine-score--rm"><span>Réseau-Mère</span><strong>${Number(score?.RM||0)+Number(score?.RM_bonus||0)}</strong><small>${Number(score?.RM||0)} + bonus ${Number(score?.RM_bonus||0)}</small></article>
  </div>`;
}

/**
 * Avant la fin, la liste des sièges ne montre aucune identité, même celle du
 * joueur local. La seule identité visible pendant la partie est la carte privée
 * rendue par identityHtml(). Les identités de tous les sièges sont révélées
 * uniquement sur l’écran final.
 */
function seatsHtml(state,{revealAll=false}={}){
  return `<div class="engine-seats">${(state.seats||[]).map(seat=>{
    const visibleIdentity=revealAll?seat.identity:null;
    return `<article class="engine-seat${seat.seat===state.turn_seat?' is-turn':''}${seat.seat===state.my_seat?' is-me':''}">
      <strong>#${seat.seat} ${escapeHtml(seat.name)}</strong>
      <span>${seat.kind==='bot'?'Moteur tactique':'Humain'}</span>
      ${visibleIdentity?`<em>${escapeHtml(identityLabel(visibleIdentity))}</em>`:''}
      ${!revealAll&&seat.seat===state.my_seat?'<small>Votre siège · identité dans votre carte privée</small>':''}
    </article>`;
  }).join('')}</div>`;
}

function reportsHtml(state){
  if(!(state.reports||[]).length) return '<p class="fracture-muted">Aucun rapport annoncé pour cette ronde.</p>';
  return `<div class="engine-reports">${state.reports.map(report=>{
    const proof=report.proof;
    const proofMeta=proof?factionMeta(proof.faction):null;
    return `<article>
      <strong>Joueur ${report.seat}</strong>
      <span>Rapport : ${escapeHtml(report.report)}</span>
      ${report.suspect!=null?`<span>Votre soupçon privé : #${escapeHtml(report.suspect)}</span>`:''}
      ${proof?`<b>Preuve : ${escapeHtml(proofMeta.label)} ${Number(proof.points)>=0?'+':''}${Number(proof.points)||0}</b>`:''}
    </article>`;
  }).join('')}</div>`;
}

function roundsHtml(state){
  if(!(state.rounds||[]).length) return '';
  return `<div class="engine-round-history"><h3>Historique des rondes</h3>${state.rounds.map(round=>`<span>R${round.round}${round.tiebreak?' (départage)':''} : Résistance ${Number(round.R)||0} — Réseau-Mère ${Number(round.RM)||0}</span>`).join('')}</div>`;
}

function eventsHtml(state){
  return `<div class="engine-events"><h3>Journal public</h3>${(state.events||[]).slice(0,20).map(event=>`<p><small>${event.round?`R${event.round} · `:''}</small>${escapeHtml(event.message)}</p>`).join('')||'<p>Aucun événement.</p>'}</div>`;
}

function renderLobby(state){
  const ready=state.ready_to_start;
  root.innerHTML=`<section class="fracture-online-card engine-panel">
    <span class="eyebrow">Salon ${escapeHtml(state.party_code)}</span>
    <h2>Préparer la partie</h2>
    <p>${Number(state.member_count)||0}/${Number(state.human_player_count)||0} joueur(s) humain(s) connecté(s). ${state.human_player_count<=2?'Les sièges invisibles seront joués automatiquement par le moteur tactique SINJIRA™.':''}</p>
    <div class="engine-member-list">${(state.members||[]).map(member=>`<span>#${member.seat} ${escapeHtml(member.name)}</span>`).join('')}</div>
    ${state.owner?`<button class="btn btn-primary" data-start-game ${ready?'':'disabled'}>${ready?'Démarrer la partie':'En attente des autres joueurs'}</button>`:'<p class="fracture-muted">Le créateur de la partie démarrera lorsque tous les humains seront présents.</p>'}
  </section>`;
  root.querySelector('[data-start-game]')?.addEventListener('click',()=>act('fracture_engine_start',{p_party_code:code}));
}

function renderKeep(state){
  const cards=state.hand||[];
  const selected=getKeepSelection(state,cards);
  if(state.keep_submitted) selected.clear();
  root.innerHTML=`${headerGame(state)}
    <section class="fracture-online-card engine-panel">
      <span class="eyebrow">Ronde ${state.round}</span>
      <h2>Choisissez 2 cartes à conserver</h2>
      <p>Vous voyez seulement vos 3 cartes. Chaque carte indique clairement sa faction et sa valeur. Sélectionnez-en exactement 2; la troisième est défaussée. Vos 2 cartes rejoignent ensuite le centre et cessent de vous appartenir.</p>
      ${state.keep_submitted
        ? '<div class="v24-callout">Choix enregistré. Attente des autres joueurs…</div>'
        : `<div class="engine-cards" data-hand>${cards.map(card=>cardHtml(card,true,selected.has(Number(card.id)))).join('')}</div><button class="btn btn-primary" data-submit-keep ${selected.size===2?'':'disabled'}>Confirmer mes 2 cartes</button>`}
    </section>
    ${reportsHtml(state)}${roundsHtml(state)}${eventsHtml(state)}`;

  if(!state.keep_submitted){
    const button=root.querySelector('[data-submit-keep]');
    root.querySelectorAll('[data-card-id]').forEach(cardButton=>cardButton.addEventListener('click',()=>{
      const id=Number(cardButton.dataset.cardId);
      selected.has(id)?selected.delete(id):selected.size<2&&selected.add(id);
      cardButton.classList.toggle('is-selected',selected.has(id));
      if(button) button.disabled=selected.size!==2;
    }));
    button?.addEventListener('click',()=>act('fracture_engine_submit_keep',{p_party_code:code,p_card_ids:[...selected]}));
  }
}

function renderPick(state){
  const mine=state.turn_seat===state.my_seat;
  root.innerHTML=`${headerGame(state)}
    <section class="fracture-online-card engine-panel">
      <span class="eyebrow">Passage ${state.pick_pass}/2</span>
      <h2>${mine?'À vous de choisir':'Sélection en cours'}</h2>
      <p>${mine?'Choisissez une carte face cachée du centre. Le dos officiel Fracture masque complètement sa faction et sa valeur jusqu’à votre sélection.':`Tour du siège #${state.turn_seat}. La page se synchronise automatiquement.`}</p>
      <div class="engine-center">${(state.center||[]).map(card=>backHtml(card,mine)).join('')}</div>
      ${state.my_picks?.length?`<h3>Vos cartes récupérées</h3><div class="engine-cards">${state.my_picks.map(card=>cardHtml(card,false)).join('')}</div>`:''}
    </section>
    ${reportsHtml(state)}${roundsHtml(state)}${eventsHtml(state)}`;

  if(mine){
    root.querySelectorAll('[data-center-card]').forEach(button=>button.addEventListener('click',()=>act('fracture_engine_pick',{
      p_party_code:code,
      p_card_id:Number(button.dataset.centerCard)
    })));
  }
}

function renderReport(state){
  const submitted=state.report_submitted;
  const picks=state.my_picks||[];
  const seats=(state.seats||[]).filter(seat=>seat.seat!==state.my_seat);
  const values=getReportValues(state);
  if(state.my_proof_used) values.proof='';
  if(submitted){
    values.report='';
    values.suspect='';
    values.proof='';
  }
  root.innerHTML=`${headerGame(state)}
    <section class="fracture-online-card engine-panel">
      <span class="eyebrow">Ronde ${state.round}</span>
      <h2>Rapport, Preuve et soupçon</h2>
      <h3>Vos 2 cartes</h3>
      <div class="engine-cards">${picks.map(card=>cardHtml(card,false)).join('')}</div>
      ${submitted
        ? '<div class="v24-callout">Votre rapport est enregistré. Attente des autres joueurs…</div>'
        : `<form data-report-form class="engine-form" autocomplete="off">
            <label>Rapport annoncé
              <select name="report" required>
                <option value="">Choisir…</option>
                <option value="R">Avantage Résistance</option>
                <option value="RM">Avantage Réseau-Mère</option>
                <option value="EQ">Équilibré</option>
              </select>
            </label>
            <label>Soupçon privé
              <select name="suspect" required>
                <option value="">Choisir un siège…</option>
                ${seats.map(seat=>`<option value="${seat.seat}">#${seat.seat} ${escapeHtml(seat.name)}</option>`).join('')}
              </select>
              <small>Votre soupçon n’est pas montré aux autres joueurs.</small>
            </label>
            <label>Preuve — facultatif
              <select name="proof" ${state.my_proof_used?'disabled':''}>
                <option value="">Aucune</option>
                ${!state.my_proof_used?picks.map(card=>`<option value="${card.id}">${escapeHtml(factionMeta(card.faction).label)} ${Number(card.points)>=0?'+':''}${Number(card.points)||0}</option>`).join(''):''}
              </select>
              <small>${state.my_proof_used?'Votre Preuve a déjà été utilisée dans cette partie.':'Une seule Preuve par siège et par partie.'}</small>
            </label>
            <button class="btn btn-primary">Envoyer mon rapport</button>
          </form>`}
    </section>
    <section class="fracture-online-card engine-panel"><h2>Rapports annoncés</h2>${reportsHtml(state)}</section>
    ${roundsHtml(state)}${eventsHtml(state)}`;

  const form=root.querySelector('[data-report-form]');
  if(form){
    ['report','suspect','proof'].forEach(name=>{
      const field=form.elements[name];
      if(!field||field.disabled) return;
      const wanted=values[name]||'';
      if([...field.options].some(option=>option.value===wanted)) field.value=wanted;
    });
    form.addEventListener('change',event=>{
      const field=event.target;
      if(!field?.matches?.('select[name]')) return;
      if(Object.prototype.hasOwnProperty.call(values,field.name)) values[field.name]=field.value;
    });
    form.addEventListener('submit',event=>{
      event.preventDefault();
      values.report=form.report.value;
      values.suspect=form.suspect.value;
      values.proof=form.proof.value;
      if(!values.report||!values.suspect){
        show('Choisissez votre rapport annoncé et votre soupçon privé avant l’envoi.','error');
        return;
      }
      act('fracture_engine_submit_report',{
        p_party_code:code,
        p_report:values.report,
        p_suspect_seat:Number(values.suspect),
        p_proof_card_id:values.proof?Number(values.proof):null
      });
    });
  }
}

function renderFinalVote(state){
  const count=Number(state.agents)||0;
  const others=(state.seats||[]).filter(seat=>seat.seat!==state.my_seat);
  const selected=getVoteSelection(state,others);
  if(state.voted) selected.clear();
  root.innerHTML=`${headerGame(state)}
    <section class="fracture-online-card engine-panel">
      <span class="eyebrow">Accusation finale</span>
      <h2>Identifiez ${count} agent${count>1?'s':''} du Réseau-Mère</h2>
      <p>Choisissez exactement ${count} siège${count>1?'s':''} distinct${count>1?'s':''}. Les sièges contrôlés par le moteur ne votent pas.</p>
      ${state.voted
        ? '<div class="v24-callout">Votre accusation définitive est enregistrée. Elle ne peut plus être modifiée. Attente des autres humains…</div>'
        : `<div class="engine-accusation" data-accusation>${others.map(seat=>`<label><input type="checkbox" value="${seat.seat}" ${selected.has(Number(seat.seat))?'checked':''}> #${seat.seat} ${escapeHtml(seat.name)}</label>`).join('')}</div><button class="btn btn-primary" data-submit-vote disabled>Confirmer l’accusation définitive</button>`}
    </section>
    ${roundsHtml(state)}${eventsHtml(state)}`;

  if(!state.voted){
    const checks=[...root.querySelectorAll('[data-accusation] input')];
    const button=root.querySelector('[data-submit-vote]');
    const sync=()=>{
      const selectedCount=checks.filter(input=>input.checked).length;
      checks.forEach(input=>{input.disabled=!input.checked&&selectedCount>=count;});
      if(button) button.disabled=selectedCount!==count;
    };
    checks.forEach(input=>input.addEventListener('change',()=>{
      const seat=Number(input.value);
      input.checked?selected.add(seat):selected.delete(seat);
      sync();
    }));
    sync();
    button?.addEventListener('click',()=>act('fracture_engine_submit_accusation',{
      p_party_code:code,
      p_accused_seats:checks.filter(input=>input.checked).map(input=>Number(input.value))
    }));
  }
}

function renderFinished(state){
  const totalsR=Number(state.score?.R||0)+Number(state.score?.R_bonus||0);
  const totalsN=Number(state.score?.RM||0)+Number(state.score?.RM_bonus||0);
  root.innerHTML=`${headerGame(state)}
    <section class="fracture-online-card engine-panel engine-finish">
      <span class="eyebrow">Partie terminée</span>
      <h2>${winnerLabel(state.winner)} remporte la partie</h2>
      <p>Score final : Résistance <strong>${totalsR}</strong> — Réseau-Mère <strong>${totalsN}</strong>.</p>
      <p>Accusés finaux : ${(state.final_accused||[]).map(seat=>`#${seat}`).join(', ')||'—'}</p>
      <h3>Révélation des identités</h3>
      ${seatsHtml(state,{revealAll:true})}
      <div class="hero-actions"><a class="btn btn-primary" href="jouer.html">Nouvelle partie</a><a class="btn btn-secondary" href="fin-de-partie.html?code=${encodeURIComponent(code)}">Feuille de fin de partie</a></div>
    </section>
    ${roundsHtml(state)}${eventsHtml(state)}`;
}

function headerGame(state){
  return `<section class="fracture-online-card engine-panel engine-overview">
      <div>
        <span class="eyebrow">${escapeHtml(phaseLabels[state.phase]||state.phase)} · ronde ${state.round||0}</span>
        <h2>${escapeHtml(state.party_code)}</h2>
        <p>Votre siège : #${state.my_seat}${state.tiebreak?' · départage':''}</p>
      </div>
      ${scoreHtml(state.score)}
    </section>
    ${identityHtml(state)}
    ${seatsHtml(state)}`;
}

function render(state,{force=false}={}){
  if(!state||state.ok===false) throw new Error(state?.error||'État de partie invalide.');
  current=state;
  const signature=stateSignature(state);
  if(!force&&signature&&signature===lastRenderedStateSignature&&root?.children?.length) return;
  lastRenderedStateSignature=signature;
  clearShow();

  const heading=document.querySelector('[data-party-heading]');
  const summary=document.querySelector('[data-party-summary]');
  if(heading) heading.textContent=`Partie ${state.party_code||code}`;
  if(summary) summary.textContent=state.phase==='lobby'?'Salon en attente':`${phaseLabels[state.phase]||state.phase}${state.round?` — ronde ${state.round}`:''}`;

  const facts=document.querySelector('[data-party-facts]');
  if(facts){
    facts.innerHTML=[
      `${Number(state.human_player_count)||0} humain(s)`,
      `${Number(state.effective_player_count)||0} sièges`,
      `${Number(state.agents)||0} agent(s) Réseau-Mère`,
      `${Number(state.round_count)||0} rondes`
    ].map(item=>`<span>${escapeHtml(item)}</span>`).join('');
  }

  if(state.phase==='lobby') return renderLobby(state);
  if(state.phase==='choose_keep') return renderKeep(state);
  if(state.phase==='pick') return renderPick(state);
  if(state.phase==='report') return renderReport(state);
  if(state.phase==='final_vote') return renderFinalVote(state);
  if(state.phase==='finished') return renderFinished(state);
  throw new Error(`Phase moteur inconnue : ${String(state.phase||'absente')}`);
}

async function load(){
  if(!/^FRM-[A-Z0-9]{6}$/.test(code)){
    show('Code de partie invalide. Format attendu : FRM-ABC123.','error');
    return;
  }
  if(loading||busy||document.hidden||isEditingControl()) return;
  const serial=++requestSerial;
  loading=true;
  try{
    const state=await stateRpc();
    if(serial===requestSerial) render(state);
  }catch(error){
    if(serial===requestSerial){
      console.warn('[Fracture engine]',error);
      show(error.message||'Impossible de charger la partie.','error');
    }
  }finally{
    loading=false;
  }
}

async function act(name,args){
  if(busy) return;
  busy=true;
  const serial=++requestSerial;
  show('Synchronisation…','info');
  try{
    const state=await gatewayAction(name,args);
    if(serial===requestSerial) render(state,{force:true});
  }catch(error){
    if(serial===requestSerial){
      console.warn(`[Fracture ${name}]`,error);
      show(error.message||'Action refusée.','error');
    }
  }finally{
    busy=false;
    loading=false;
  }
}

async function boot(){
  await requireUser();
  await privacyHealth();
  if(!/^FRM-[A-Z0-9]{6}$/.test(code)){
    show('Code de partie invalide. Format attendu : FRM-ABC123.','error');
    return;
  }
  document.documentElement.dataset.fractureUiVersion=UI_VERSION;
  document.querySelector('[data-copy-party-code]')?.addEventListener('click',async()=>{
    try{
      await navigator.clipboard.writeText(code);
      show('Code copié.','success');
    }catch{
      show(`Code : ${code}`,'info');
    }
  });
  root?.addEventListener('focusout',()=>{
    setTimeout(()=>{
      if(!busy&&!loading&&!document.hidden&&current?.phase!=='finished') load();
    },180);
  });
  await load();
  timer=setInterval(()=>{
    if(!busy&&!loading&&!document.hidden&&!isEditingControl()&&current?.phase!=='finished') load();
  },2200);
  addEventListener('visibilitychange',()=>{
    if(!document.hidden&&!busy&&!isEditingControl()&&current?.phase!=='finished') load();
  });
  addEventListener('beforeunload',()=>clearInterval(timer),{once:true});
}

boot().catch(error=>show(error.message||'Connexion requise.','error'));
