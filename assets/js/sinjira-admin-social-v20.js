import './sinjira-admin-parallel-v24.js';
import {getSupabase,escapeHtml} from './sinjira-supabase.js';

const reasonLabels=Object.assign(Object.create(null),{
  harassment:'Harcèlement ou insistance répétée',sexual_content:'Contenu sexuel non désiré',pressure:'Pression pour se dévoiler ou partager des coordonnées',
  scam:'Arnaque, fraude ou sollicitation financière',hate:'Propos haineux ou discriminatoires',threats:'Menaces ou intimidation',
  impersonation:'Usurpation ou identité trompeuse',other:'Autre problème de sécurité'
});

async function call(action,extra={}){
  const {data,error}=await getSupabase().functions.invoke('admin-social-v20',{body:{action,...extra}});
  if(error!==null||data?.ok!==true)throw new Error('Réponse de modération non confirmée');
  return data;
}

function datingEvidence(x){
  const snap=x.snapshot||{},counts=snap.message_counts||{},messages=Array.isArray(snap.messages)?snap.messages:[];
  const transcript=messages.map(m=>`<div class="v20-comment"><strong>${m.side==='reporter'?'Membre signalant':'Personne signalée'}</strong><p>${escapeHtml(m.body||'')}</p><small>${escapeHtml(new Date(m.created_at).toLocaleString('fr-CA'))}</small></div>`).join('');
  return `<div class="notice"><strong>Rencontre privée</strong><p>Statut au moment du signalement : ${escapeHtml(snap.connection_status||'—')} · messages : ${Number(counts.reporter||0)} / ${Number(counts.other||0)}.</p>${snap.details?`<p><b>Détails fournis :</b> ${escapeHtml(snap.details)}</p>`:''}<p><small>La cible réelle est résolue côté serveur. Aucun identifiant utilisateur fourni par le snapshot n’est utilisé pour une sanction.</small></p></div>${transcript?`<div class="v20-comments"><h4>Extrait de preuve — derniers messages</h4>${transcript}</div>`:'<p>Aucun message dans cette rencontre.</p>'}`;
}
function genericEvidence(x){return `<pre>${escapeHtml(JSON.stringify(x.snapshot||{},null,2))}</pre>`}

function decisionInputs(x){
  const reason=reasonLabels[x.reason]||x.reason||'sécurité communautaire';
  const statement='';
  return `<details class="v24-panel" style="margin-top:12px"><summary><strong>Motivation de la décision</strong></summary><div class="account-form" style="margin-top:12px"><div class="field"><label>Règle appliquée</label><input data-policy-rule maxlength="240" value="${escapeHtml(`Règles communautaires SINJIRA™ — ${reason}`)}"></div><div class="field"><label>Exposé des raisons</label><textarea data-statement minlength="20" maxlength="4000" placeholder="Expliquez la mesure après examen humain.">${escapeHtml(statement)}</textarea></div><div class="field"><label>Niveau d’urgence</label><select data-urgency><option value="standard">Standard</option><option value="urgent_harm">Risque urgent de préjudice</option><option value="illegal_content">Contenu potentiellement illégal</option></select></div></div></details>`;
}
function reportCard(x){
  const isDating=x.snapshot?.source==='dating',reason=reasonLabels[x.reason]||x.reason;
  return `<article class="v20-admin-report" data-report="${escapeHtml(x.id)}"><strong>${isDating?'Rencontres SINJIRA™':escapeHtml(x.network)} · ${escapeHtml(reason)}</strong><p>Signalé le ${escapeHtml(new Date(x.created_at).toLocaleString('fr-CA'))}</p>${isDating?datingEvidence(x):genericEvidence(x)}${decisionInputs(x)}<div class="v20-admin-actions"><button class="btn btn-secondary btn-small" data-resolve>Résoudre sans mesure</button>${isDating?'':'<button class="btn btn-primary btn-small" data-restrict>Masquer réversiblement</button>'}<button class="btn btn-secondary btn-small" data-suspend>Suspension 7 jours</button></div></article>`;
}
function reportPayload(card){return {policy_rule:String(card.querySelector('[data-policy-rule]')?.value||'').trim(),statement_of_reasons:String(card.querySelector('[data-statement]')?.value||'').trim(),urgency:String(card.querySelector('[data-urgency]')?.value||'standard')}}

function ensureAppealUI(){
  const panel=document.querySelector('[data-admin-panel="social-moderation"] article');
  if(!panel)return {count:null,list:null};
  const grid=panel.querySelector('.admin-stat-grid');
  let count=panel.querySelector('[data-social-appeal-count]');
  if(!count&&grid){const stat=document.createElement('div');stat.className='account-stat';stat.innerHTML='<span>Appels en attente</span><strong data-social-appeal-count>—</strong>';grid.append(stat);count=stat.querySelector('[data-social-appeal-count]');}
  let list=panel.querySelector('[data-social-appeal-list]');
  if(!list){const section=document.createElement('section');section.className='section section-tight';section.innerHTML='<div class="section-heading"><span class="eyebrow">Révision humaine obligatoire</span><h3>Appels de modération</h3><p>Chaque appel est gratuit. Une issue finale doit être motivée par une personne administratrice; aucune IA ne tranche automatiquement.</p></div><div class="admin-management-list" data-social-appeal-list></div>';panel.append(section);list=section.querySelector('[data-social-appeal-list]');}
  return {count,list};
}
function appealCard(a){
  const d=a.decision||{};
  return `<article class="v20-admin-report" data-appeal="${escapeHtml(a.id)}"><span class="v24-badge">Appel en attente</span><h3>${escapeHtml(d.action||'Décision de modération')}</h3><p><strong>Règle :</strong> ${escapeHtml(d.policy_rule||'—')}</p><p><strong>Décision initiale :</strong> ${escapeHtml(d.statement_of_reasons||'—')}</p><div class="notice"><strong>Arguments du membre</strong><p>${escapeHtml(a.appeal_text||'')}</p><small>Envoyé le ${escapeHtml(new Date(a.submitted_at).toLocaleString('fr-CA'))}</small></div><div class="field"><label>Motif de la révision humaine</label><textarea data-review-reason minlength="20" maxlength="4000" placeholder="Expliquez pourquoi la décision est maintenue ou renversée."></textarea></div><div class="v20-admin-actions"><button class="btn btn-secondary btn-small" data-uphold>Maintenir la décision</button><button class="btn btn-primary btn-small" data-reverse>Renverser la décision</button></div></article>`;
}

const panel=document.querySelector('[data-admin-panel="social-moderation"]');
const status=panel?.querySelector('[data-social-admin-status]');
const fieldSelectors=['[data-policy-rule]','[data-statement]','[data-urgency]','[data-review-reason]'];
let busy=false,uncertain=false,dirty=new Map();

function say(message,kind){
  status.textContent=message;status.dataset.statusType=kind;status.hidden=false;
}
function cards(){return [...panel.querySelectorAll('[data-report],[data-appeal]')]}
function key(card){return card.hasAttribute('data-report')?'report:'+card.dataset.report:'appeal:'+card.dataset.appeal}
function actionButtons(){return [...panel.querySelectorAll('[data-resolve],[data-restrict],[data-suspend],[data-uphold],[data-reverse]')]}
function warning(e){if(busy||uncertain||dirty.size){e.preventDefault();e.returnValue=''}}
function syncWarning(){
  window.removeEventListener('beforeunload',warning);
  if(busy||uncertain||dirty.size)window.addEventListener('beforeunload',warning);
}
function wireFields(card,index){
  const fields=fieldSelectors.map(s=>card.querySelector(s)).filter(Boolean);
  for(const [j,field] of fields.entries()){
    field.id='moderation-field-'+index+'-'+j;
    const label=field.closest('.field')?.querySelector('label');
    if(label)label.htmlFor=field.id;
    const change=()=>{
      dirty.set(key(card),fieldSelectors.map(s=>card.querySelector(s)?.value??null));
      syncWarning();
      if(!busy&&!uncertain)say('Motivation non enregistrée.','info');
    };
    field.addEventListener('input',change);field.addEventListener('change',change);
  }
  const draft=dirty.get(key(card));
  if(draft){
    fieldSelectors.forEach((s,j)=>{const field=card.querySelector(s);if(field&&draft[j]!==null)field.value=draft[j]});
    const details=card.querySelector('details');if(details)details.open=true;
  }
}
async function execute(card,action,payload,question,validate=()=>true){
  if(busy||uncertain||!card.isConnected||!window.confirm(question))return;
  busy=true;syncWarning();
  const controls=[...panel.querySelectorAll('[data-report] button,[data-appeal] button,[data-report] input,[data-report] textarea,[data-report] select,[data-appeal] textarea')].map(el=>[el,el.disabled]);
  controls.forEach(([el])=>{el.disabled=true});
  panel.setAttribute('aria-busy','true');
  say('Décision en cours de transmission…','info');
  let confirmed=false;
  try{
    const result=await call(action,payload);
    if(!validate(result))throw new Error('DECISION_UNCONFIRMED');
    confirmed=true;
    dirty.delete(key(card));
    const dropped=await load(key(card));
    say('Décision confirmée par le serveur.'+(dropped?' Des brouillons de dossiers devenus indisponibles ont été retirés.':''),'success');
  }catch{
    uncertain=true;
    say(confirmed?'Décision confirmée, mais actualisation indisponible ou dossier toujours ouvert. Vérifiez avant toute autre décision.':
      'Décision non confirmée. La saisie reste disponible. Vérifiez le dossier avant de recharger la page et de réessayer.','error');
  }finally{
    busy=false;panel.setAttribute('aria-busy','false');
    controls.forEach(([el,disabled])=>{if(el.isConnected)el.disabled=disabled});
    if(uncertain)actionButtons().forEach(el=>{el.disabled=true});
    syncWarning();
    if(!panel.hidden){status.focus({preventScroll:true});status.scrollIntoView({block:'nearest',behavior:'instant'})}
  }
}
function validMotivation(card){
  const payload=reportPayload(card);
  if(!payload.policy_rule||payload.policy_rule.length>240||payload.statement_of_reasons.length<20||payload.statement_of_reasons.length>4000||
    !['standard','urgent_harm','illegal_content'].includes(payload.urgency)){
    const details=card.querySelector('details');if(details)details.open=true;
    say('Indiquez la règle et une motivation humaine de 20 à 4 000 caractères.','error');
    card.querySelector(!payload.policy_rule?'[data-policy-rule]':'[data-statement]')?.focus();
    return null;
  }
  return payload;
}
async function load(completedKey){
  const ui=ensureAppealUI();
  const [d,r,a]=await Promise.all([call('dashboard'),call('list_reports'),call('list_appeals')]);
  if(!Array.isArray(r.reports)||!Array.isArray(a.appeals)||!d.dashboard||
     !['open_reports','active_suspensions','pending_appeals'].every(k=>Number.isSafeInteger(d.dashboard[k])&&d.dashboard[k]>=0))throw new Error('READ_UNCONFIRMED');
  if(![r.reports,a.appeals].every(rows=>rows.every(x=>typeof x?.id==='string'&&x.id)&&new Set(rows.map(x=>x.id)).size===rows.length))throw new Error('READ_UNCONFIRMED');
  const keys=new Set([...r.reports.map(x=>'report:'+x.id),...a.appeals.map(x=>'appeal:'+x.id)]);
  if(completedKey&&keys.has(completedKey))throw new Error('STATE_UNCONFIRMED');
  let dropped=0;
  for(const k of dirty.keys())if(!keys.has(k)){dirty.delete(k);dropped++}
  document.querySelector('[data-social-report-count]').textContent=String(d.dashboard.open_reports);
  document.querySelector('[data-social-suspension-count]').textContent=String(d.dashboard.active_suspensions);
  if(ui.count)ui.count.textContent=String(d.dashboard.pending_appeals);
  const box=document.querySelector('[data-social-report-list]');
  box.innerHTML=r.reports.map(reportCard).join('')||'<p>Aucun signalement ouvert.</p>';
  if(ui.list)ui.list.innerHTML=a.appeals.map(appealCard).join('')||'<p>Aucun appel en attente.</p>';
  cards().forEach((card,index)=>wireFields(card,index));
  box.querySelectorAll('[data-report]').forEach(card=>{
    const id=card.dataset.report;
    card.querySelector('[data-resolve]').onclick=()=>execute(card,'resolve_report',{report_id:id},'Clore ce signalement sans mesure ?');
    const restrict=card.querySelector('[data-restrict]');
    if(restrict)restrict.onclick=()=>{
      if(busy||uncertain)return;
      const payload=validMotivation(card);
      if(payload)execute(card,'restrict_reported_content',{report_id:id,...payload},'Masquer ce contenu de façon réversible et notifier le membre ?',r=>typeof r.decision_id==='string'&&Boolean(r.decision_id)&&r.reversible===true);
    };
    card.querySelector('[data-suspend]').onclick=()=>{
      if(busy||uncertain)return;
      const payload=validMotivation(card);
      if(payload)execute(card,'suspend_reported_user',{report_id:id,days:7,...payload},'Suspendre socialement le compte visé pendant 7 jours ? La mesure sera réversible et appelable.',r=>typeof r.decision_id==='string'&&Boolean(r.decision_id)&&r.reversible===true);
    };
  });
  if(ui.list)ui.list.querySelectorAll('[data-appeal]').forEach(card=>{
    const id=card.dataset.appeal;
    const review=outcome=>{
      if(busy||uncertain)return;
      const field=card.querySelector('[data-review-reason]'),reason=field.value.trim();
      if(reason.length<20||reason.length>4000){say('La révision humaine doit être motivée en 20 à 4 000 caractères.','error');field.focus();return}
      const label=outcome==='reversed'?'renverser':'maintenir';
      execute(card,'review_appeal',{appeal_id:id,outcome,review_reason:reason},'Confirmer : '+label+' la décision ?',r=>r.outcome===outcome&&typeof r.decision_id==='string'&&Boolean(r.decision_id));
    };
    card.querySelector('[data-uphold]').onclick=()=>review('upheld');
    card.querySelector('[data-reverse]').onclick=()=>review('reversed');
  });
  return dropped;
}
(async()=>{
  if(!panel||!status)return;
  panel.setAttribute('aria-busy','true');
  try{await load();say('Dossiers de modération chargés.','info')}
  catch{uncertain=true;actionButtons().forEach(el=>{el.disabled=true});say('Chargement non confirmé. Rechargez la page avant toute décision.','error')}
  finally{panel.setAttribute('aria-busy','false')}
})();
