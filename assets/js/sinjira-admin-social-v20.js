import './sinjira-admin-parallel-v24.js';
import {getSupabase,escapeHtml} from './sinjira-supabase.js';

const reasonLabels={
  harassment:'Harcèlement ou insistance répétée',sexual_content:'Contenu sexuel non désiré',pressure:'Pression pour se dévoiler ou partager des coordonnées',
  scam:'Arnaque, fraude ou sollicitation financière',hate:'Propos haineux ou discriminatoires',threats:'Menaces ou intimidation',
  impersonation:'Usurpation ou identité trompeuse',other:'Autre problème de sécurité'
};

async function call(action,extra={}){
  const {data,error}=await getSupabase().functions.invoke('admin-social-v20',{body:{action,...extra}});
  if(error||!data?.ok)throw new Error(data?.error||error?.message||'Erreur modération sociale');
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
  const statement=`Après examen humain du signalement, la mesure est appliquée pour le motif « ${reason} ». La décision est réversible et peut faire l’objet d’un appel interne gratuit.`;
  return `<details class="v24-panel" style="margin-top:12px"><summary><strong>Motivation de la décision</strong></summary><div class="account-form" style="margin-top:12px"><div class="field"><label>Règle appliquée</label><input data-policy-rule maxlength="240" value="${escapeHtml(`Règles communautaires SINJIRA™ — ${reason}`)}"></div><div class="field"><label>Exposé des raisons</label><textarea data-statement minlength="20" maxlength="4000">${escapeHtml(statement)}</textarea></div><div class="field"><label>Niveau d’urgence</label><select data-urgency><option value="standard">Standard</option><option value="urgent_harm">Risque urgent de préjudice</option><option value="illegal_content">Contenu potentiellement illégal</option></select></div></div></details>`;
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
  if(!count&&grid){const stat=document.createElement('div');stat.className='account-stat';stat.innerHTML='<span>Appels en attente</span><strong data-social-appeal-count>0</strong>';grid.append(stat);count=stat.querySelector('[data-social-appeal-count]');}
  let list=panel.querySelector('[data-social-appeal-list]');
  if(!list){const section=document.createElement('section');section.className='section section-tight';section.innerHTML='<div class="section-heading"><span class="eyebrow">Révision humaine obligatoire</span><h3>Appels de modération</h3><p>Chaque appel est gratuit. Une issue finale doit être motivée par une personne administratrice; aucune IA ne tranche automatiquement.</p></div><div class="admin-management-list" data-social-appeal-list></div>';panel.append(section);list=section.querySelector('[data-social-appeal-list]');}
  return {count,list};
}
function appealCard(a){
  const d=a.decision||{};
  return `<article class="v20-admin-report" data-appeal="${escapeHtml(a.id)}"><span class="v24-badge">Appel en attente</span><h3>${escapeHtml(d.action||'Décision de modération')}</h3><p><strong>Règle :</strong> ${escapeHtml(d.policy_rule||'—')}</p><p><strong>Décision initiale :</strong> ${escapeHtml(d.statement_of_reasons||'—')}</p><div class="notice"><strong>Arguments du membre</strong><p>${escapeHtml(a.appeal_text||'')}</p><small>Envoyé le ${escapeHtml(new Date(a.submitted_at).toLocaleString('fr-CA'))}</small></div><div class="field"><label>Motif de la révision humaine</label><textarea data-review-reason minlength="20" maxlength="4000" placeholder="Expliquez pourquoi la décision est maintenue ou renversée."></textarea></div><div class="v20-admin-actions"><button class="btn btn-secondary btn-small" data-uphold>Maintenir la décision</button><button class="btn btn-primary btn-small" data-reverse>Renverser la décision</button></div></article>`;
}

async function load(){
  const ui=ensureAppealUI();
  const [d,r,a]=await Promise.all([call('dashboard'),call('list_reports'),call('list_appeals')]);
  document.querySelector('[data-social-report-count]').textContent=String(d.dashboard.open_reports||0);
  document.querySelector('[data-social-suspension-count]').textContent=String(d.dashboard.active_suspensions||0);
  if(ui.count)ui.count.textContent=String(d.dashboard.pending_appeals||0);
  const box=document.querySelector('[data-social-report-list]');
  box.innerHTML=(r.reports||[]).map(reportCard).join('')||'<p>Aucun signalement ouvert.</p>';
  box.querySelectorAll('[data-report]').forEach(card=>{
    const id=card.dataset.report;
    card.querySelector('[data-resolve]').onclick=async()=>{await call('resolve_report',{report_id:id});await load();};
    const restrict=card.querySelector('[data-restrict]');
    if(restrict)restrict.onclick=async()=>{if(confirm('Masquer ce contenu de façon réversible et notifier le membre?')){await call('restrict_reported_content',{report_id:id,...reportPayload(card)});await load();}};
    card.querySelector('[data-suspend]').onclick=async()=>{if(confirm('Suspendre socialement le compte visé pendant 7 jours? La mesure sera réversible et appelable.')){await call('suspend_reported_user',{report_id:id,days:7,...reportPayload(card)});await load();}};
  });
  if(ui.list){
    ui.list.innerHTML=(a.appeals||[]).map(appealCard).join('')||'<p>Aucun appel en attente.</p>';
    ui.list.querySelectorAll('[data-appeal]').forEach(card=>{
      const id=card.dataset.appeal;
      const review=async outcome=>{
        const reviewReason=String(card.querySelector('[data-review-reason]')?.value||'').trim();
        if(reviewReason.length<20){alert('La révision humaine doit être motivée en au moins 20 caractères.');return}
        const label=outcome==='reversed'?'renverser':'maintenir';
        if(confirm(`Confirmer : ${label} la décision?`)){await call('review_appeal',{appeal_id:id,outcome,review_reason:reviewReason});await load();}
      };
      card.querySelector('[data-uphold]').onclick=()=>review('upheld');
      card.querySelector('[data-reverse]').onclick=()=>review('reversed');
    });
  }
}

(async()=>{try{await load();}catch(e){console.error('[SINJIRA admin moderation]',e);}})();
