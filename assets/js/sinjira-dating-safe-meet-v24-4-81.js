import {getSupabase,escapeHtml} from './sinjira-supabase.js';

const s=getSupabase();
const connectionsBox=document.querySelector('[data-dating-connections]');
const statusNode=document.querySelector('[data-dating-status]');
const STYLE_ID='sinjira-dating-safe-meet-v24-4-81';
const preferenceOptions=[
  ['coffee','Café / thé'],
  ['brunch','Brunch'],
  ['museum','Musée / exposition'],
  ['bookstore','Librairie'],
  ['board_games','Jeux de société'],
  ['public_market','Marché public'],
  ['culture','Activité culturelle'],
  ['outdoor_walk','Marche publique de jour'],
  ['quiet','Ambiance calme'],
  ['accessible','Accessibilité'],
  ['low_cost','Petit budget'],
  ['alcohol_free','Sans alcool']
];
let overview=[];
let observer=null;
let refreshTimer=null;
let refreshing=false;

function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const link=document.createElement('link');
  link.id=STYLE_ID;link.rel='stylesheet';link.href='../assets/css/sinjira-dating-safe-meet-v24-4-81.css?v=24.4.81';
  document.head.append(link);
}

function announce(text,type='info'){
  if(!statusNode)return;
  statusNode.hidden=false;
  statusNode.className=`account-status ${type==='error'?'error':type==='success'?'success':'info'}`;
  statusNode.textContent=text;
}

function explain(error){
  const raw=String(error?.message||error||'');
  if(raw.includes('DATING_MEET_REVEAL_REQUIRED'))return 'Les suggestions de première rencontre deviennent disponibles seulement après le seuil 10 + 10 et le dévoilement mutuel.';
  if(raw.includes('DATING_MEET_CREDIT_REQUIRED'))return 'La personne qui propose doit avoir au moins 1 Crédit Rencontre disponible.';
  if(raw.includes('DATING_MEET_AREA_REQUIRED'))return 'Indiquez une zone générale de rencontre, par exemple « Montréal — Plateau », jamais une adresse privée.';
  if(raw.includes('DATING_MEET_AREA_MISMATCH'))return 'La zone proposée a changé. Utilisez la même zone générale afin que les deux personnes consentent au même secteur.';
  if(raw.includes('DATING_MEET_PREFERENCE_INVALID'))return 'Une préférence de sortie n’est pas reconnue.';
  if(raw.includes('DATING_CONTACT_INFO_FORBIDDEN'))return 'La zone de rencontre ne doit contenir ni adresse personnelle, téléphone, courriel, URL ou identifiant social.';
  if(raw.includes('DATING_NOT_ELIGIBLE'))return 'Cette rencontre n’est plus admissible. Rencontres est réservé aux adultes célibataires, disponibles et confirmés.';
  if(raw.includes('CONVERSATION_NOT_AVAILABLE'))return 'Cette rencontre n’est plus disponible.';
  if(raw.includes('DATING_MEET_NOT_CANCELLABLE'))return 'Cette proposition ne peut plus être annulée à cette étape.';
  return 'Cette action n’a pas pu être terminée.';
}

function ensureCreditSection(){
  if(document.querySelector('[data-dating-credit-section]')||!connectionsBox)return;
  const currentSection=connectionsBox.closest('section');if(!currentSection)return;
  const section=document.createElement('section');
  section.className='section section-tight';section.dataset.datingCreditSection='';
  section.innerHTML=`<div class="account-shell"><article class="account-card safe-meet-credit-card">
    <div class="account-welcome-strip"><span class="eyebrow">Crédits Rencontre</span><strong data-dating-credit-balance>Chargement…</strong></div>
    <h2>Préparer une première rencontre publique, à deux</h2>
    <p>Après le dévoilement mutuel, l’une des deux personnes peut proposer de chercher des idées de sortie adaptées aux goûts des deux. <strong>La demande coûte 1 Crédit Rencontre au total</strong>, débité à la personne qui lance la proposition seulement lorsque l’autre accepte aussi.</p>
    <div class="safe-meet-principles">
      <span>3 crédits gratuits au départ</span><span>+1 gratuit par mois</span><span>Aucun achat activé</span><span>Aucune IA distante payante</span>
    </div>
    <p><small>SINJIRA™ propose des catégories de lieux publics et une recherche cartographique. Il ne garantit jamais la sécurité d’un établissement. Vérifiez les heures, l’accessibilité et les conditions actuelles avant de vous déplacer.</small></p>
  </article></div>`;
  currentSection.before(section);
}

async function refreshCredit(){
  const node=document.querySelector('[data-dating-credit-balance]');if(!node)return;
  const {data,error}=await s.rpc('dating_credit_status');
  if(error){node.textContent='Crédits indisponibles';return;}
  const balance=Number(data?.balance||0);
  node.textContent=`${balance} Crédit${balance===1?'':'s'} Rencontre`;
}

function checkboxMarkup(){
  return preferenceOptions.map(([value,label])=>`<label class="safe-meet-chip"><input type="checkbox" name="preferences" value="${escapeHtml(value)}"/> <span>${escapeHtml(label)}</span></label>`).join('');
}

function panelMarkup(connectionId){
  return `<div class="safe-meet-panel" data-safe-meet-panel hidden data-connection-id="${escapeHtml(connectionId)}">
    <div class="safe-meet-panel-head"><div><span class="eyebrow">Première rencontre</span><h3>Suggestions publiques adaptées aux deux</h3></div><button class="btn btn-secondary btn-small" type="button" data-safe-meet-close>Fermer</button></div>
    <div data-safe-meet-body><p>Chargement…</p></div>
  </div>`;
}

function decorateCards(){
  if(!connectionsBox)return;
  observer?.disconnect();
  try{
    for(const row of overview){
      const card=[...connectionsBox.querySelectorAll('[data-dating-connection]')].find(node=>node.dataset.datingConnection===row.connection_id);
      if(!card)continue;
      card.querySelector('[data-safe-meet-toggle]')?.remove();
      card.querySelector('[data-safe-meet-panel]')?.remove();
      if(row.status!=='accepted'||!row.identity_revealed)continue;
      const actions=card.querySelector('.hero-actions');if(!actions)continue;
      const button=document.createElement('button');
      button.type='button';button.className='btn btn-secondary btn-small';button.dataset.safeMeetToggle='';
      button.textContent='Préparer une rencontre publique';
      actions.append(button);
      actions.insertAdjacentHTML('afterend',panelMarkup(row.connection_id));
    }
  }finally{observer?.observe(connectionsBox,{childList:true,subtree:true});}
}

function renderWaiting(state,body){
  const proposed=state.status==='waiting'&&state.meeting_area;
  const readonly=proposed?'readonly':'';
  const areaValue=proposed?`value="${escapeHtml(state.meeting_area)}"`:'';
  const consentText=state.my_consent
    ?'Votre accord est enregistré. Aucun nouveau débit ne sera fait pendant cette attente.'
    :state.other_consent
      ?'L’autre personne a déjà accepté. Votre accord déclenchera la recommandation et le débit de 1 crédit à la personne qui a lancé la demande.'
      :'Le premier accord crée seulement une proposition. Aucun crédit n’est débité avant l’accord des deux.';
  body.innerHTML=`<div class="safe-meet-notice"><strong>Consentement des deux obligatoire</strong><p>${escapeHtml(consentText)}</p></div>
    <form data-safe-meet-form>
      <label><strong>Zone générale proposée</strong><input name="meeting_area" maxlength="120" ${readonly} ${areaValue} placeholder="Ex. Montréal — Plateau" required/><small>Quartier ou secteur général seulement. N’inscrivez jamais votre domicile ou une adresse privée.</small></label>
      <fieldset><legend><strong>Mes goûts pour cette sortie</strong></legend><div class="safe-meet-chips">${checkboxMarkup()}</div></fieldset>
      <div class="safe-meet-safety"><strong>Avant de confirmer</strong><ul><li>Lieu public avec personnel ou passage régulier.</li><li>Chacun garde son propre moyen de retour.</li><li>Une personne de confiance connaît le lieu et l’heure.</li><li>Pas de domicile, hôtel ou endroit isolé comme première rencontre.</li></ul></div>
      <div class="hero-actions"><button class="btn btn-primary btn-small" type="submit">${state.my_consent?'Mettre à jour mes goûts':'Je veux ces suggestions'}</button>${state.status==='waiting'?'<button class="btn btn-secondary btn-small" type="button" data-safe-meet-cancel>Annuler la proposition</button>':''}</div>
    </form>`;
}

function renderGenerated(state,body){
  const rec=state.recommendation||{};
  const places=Array.isArray(rec.places)?rec.places:[];
  const cards=places.map(place=>{
    const query=encodeURIComponent(String(place.search_query||`${place.title||''} ${state.meeting_area||''}`).trim());
    const href=`https://www.openstreetmap.org/search?query=${query}`;
    return `<article class="safe-meet-result"><span class="eyebrow">Idée publique</span><h4>${escapeHtml(place.title||'Sortie publique')}</h4><p>${escapeHtml(place.why||'')}</p><p><small>${escapeHtml(place.detail||'')}</small></p><a class="btn btn-secondary btn-small" href="${href}" target="_blank" rel="noopener noreferrer">Chercher dans OpenStreetMap</a></article>`;
  }).join('');
  const checklist=(Array.isArray(rec.checklist)?rec.checklist:[]).map(item=>`<li>${escapeHtml(item)}</li>`).join('');
  body.innerHTML=`<div class="safe-meet-generated"><div class="account-welcome-strip"><strong>Suggestions prêtes</strong><span>${escapeHtml(state.meeting_area||rec.area||'Zone convenue')}</span></div><p>Les goûts des deux ont été combinés sans dévoiler les préférences brutes de l’autre personne. Le Crédit Rencontre a été débité une seule fois à la personne qui a lancé la demande.</p><div class="safe-meet-results">${cards||'<p>Aucune suggestion disponible.</p>'}</div><div class="safe-meet-safety"><strong>Checklist de première rencontre</strong><ul>${checklist}</ul></div><p><small>${escapeHtml(rec.safety_notice||'Vérifiez toujours le lieu et les conditions actuelles vous-mêmes.')}</small></p></div>`;
}

async function loadPanel(panel){
  const id=panel.dataset.connectionId;const body=panel.querySelector('[data-safe-meet-body]');if(!body)return;
  body.innerHTML='<p>Chargement…</p>';
  const {data,error}=await s.rpc('dating_safe_meet_status',{p_connection_id:id});
  if(error){body.innerHTML=`<p>${escapeHtml(explain(error))}</p>`;return;}
  if(!data?.identity_revealed){body.innerHTML='<p>Cette option devient disponible après le dévoilement mutuel.</p>';return;}
  if(data.status==='generated')renderGenerated(data,body);else renderWaiting(data,body);
}

async function refreshOverview(){
  if(refreshing||!connectionsBox)return;refreshing=true;
  try{
    const {data=[],error}=await s.rpc('dating_connections_overview');
    if(!error){overview=data;decorateCards();}
    await refreshCredit();
  }finally{refreshing=false;}
}

connectionsBox?.addEventListener('click',async event=>{
  const toggle=event.target.closest('[data-safe-meet-toggle]');
  if(toggle){
    const card=toggle.closest('[data-dating-connection]');const panel=card?.querySelector('[data-safe-meet-panel]');if(!panel)return;
    panel.hidden=!panel.hidden;if(!panel.hidden)await loadPanel(panel);return;
  }
  const close=event.target.closest('[data-safe-meet-close]');if(close){close.closest('[data-safe-meet-panel]').hidden=true;return;}
  const cancel=event.target.closest('[data-safe-meet-cancel]');
  if(cancel){
    const panel=cancel.closest('[data-safe-meet-panel]');if(!panel)return;cancel.disabled=true;
    const {error}=await s.rpc('dating_safe_meet_cancel',{p_connection_id:panel.dataset.connectionId});
    cancel.disabled=false;
    if(error){announce(explain(error),'error');return;}
    announce('Proposition de rencontre annulée. Aucun crédit n’a été débité.','success');await loadPanel(panel);await refreshCredit();
  }
});

connectionsBox?.addEventListener('submit',async event=>{
  const form=event.target.closest('[data-safe-meet-form]');if(!form)return;
  event.preventDefault();
  const panel=form.closest('[data-safe-meet-panel]');const area=String(form.elements.meeting_area?.value||'').trim();
  const prefs=[...form.querySelectorAll('input[name="preferences"]:checked')].map(input=>input.value);
  const submit=form.querySelector('button[type="submit"]');if(submit)submit.disabled=true;
  try{
    const {data,error}=await s.rpc('dating_safe_meet_opt_in',{p_connection_id:panel.dataset.connectionId,p_preferences:prefs,p_meeting_area:area});
    if(error)throw error;
    if(data?.status==='generated')announce('Vous avez tous les deux accepté : les suggestions de première rencontre sont prêtes.','success');
    else announce('Votre accord est enregistré. Aucun crédit ne sera débité avant l’accord de l’autre personne.','success');
    await loadPanel(panel);await refreshCredit();
  }catch(error){announce(explain(error),'error');}
  finally{if(submit)submit.disabled=false;}
});

function scheduleRefresh(){clearTimeout(refreshTimer);refreshTimer=setTimeout(()=>refreshOverview().catch(()=>{}),140);}

ensureStyle();ensureCreditSection();
if(connectionsBox){observer=new MutationObserver(scheduleRefresh);observer.observe(connectionsBox,{childList:true,subtree:true});}
document.addEventListener('visibilitychange',()=>{if(!document.hidden)scheduleRefresh();});
scheduleRefresh();
