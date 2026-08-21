import {getSupabase,requireUser,setStatus,escapeHtml,formatDate} from './sinjira-supabase.js';

const list=document.querySelector('[data-moderation-list]');
const status=document.querySelector('[data-moderation-status]');

const actionLabels={hide_content:'Contenu masqué',suspend_social:'Suspension sociale',disable_dating:'Rencontres désactivées',no_action:'Aucune mesure'};
const appealLabels={pending:'Appel en attente',upheld:'Décision maintenue',reversed:'Décision renversée',withdrawn:'Appel retiré'};
const scopeLabels={real:'Communauté',character:'Réseau personnage',dating:'Rencontres',account:'Compte'};

function date(value){
  try{return value?formatDate(value):'—'}catch{return String(value||'—')}
}

function decisionCard(d){
  const action=actionLabels[d.action]||d.action;
  const scope=scopeLabels[d.network]||d.network;
  const appeal=d.appeal_status?`<div class="notice"><strong>${escapeHtml(appealLabels[d.appeal_status]||d.appeal_status)}</strong>${d.appeal_submitted_at?`<p>Envoyé le ${escapeHtml(date(d.appeal_submitted_at))}.</p>`:''}${d.appeal_reviewed_at?`<p>Révision humaine terminée le ${escapeHtml(date(d.appeal_reviewed_at))}.</p>`:''}${d.review_reason?`<p>${escapeHtml(d.review_reason)}</p>`:''}</div>`:'';
  const form=d.can_appeal?`<form class="account-form" data-appeal-form data-decision-id="${escapeHtml(d.decision_id)}"><div class="field"><label>Pourquoi cette décision devrait-elle être réexaminée?</label><textarea name="appeal_text" minlength="20" maxlength="4000" required placeholder="Expliquez les faits, le contexte ou l’erreur que vous souhaitez faire revoir."></textarea><small class="v24-field-help">20 à 4000 caractères. Aucun Point SINJIRA™ ni paiement n’est requis.</small></div><button class="btn btn-primary" type="submit">Envoyer mon appel gratuit</button></form>`:'';
  return `<article class="account-card" data-moderation-decision="${escapeHtml(d.decision_id)}"><div class="documents-toolbar"><div><span class="v24-badge">${escapeHtml(scope)}</span><h2>${escapeHtml(action)}</h2></div><span>${escapeHtml(date(d.decided_at))}</span></div><p><strong>Règle appliquée :</strong> ${escapeHtml(d.policy_rule||'—')}</p><p><strong>Raisons :</strong> ${escapeHtml(d.statement_of_reasons||'—')}</p>${d.ends_at?`<p><strong>Fin prévue :</strong> ${escapeHtml(date(d.ends_at))}</p>`:''}<p><strong>Date limite d’appel :</strong> ${escapeHtml(date(d.appeal_deadline))}</p><p><small>Source de décision : examen humain. Urgence : ${escapeHtml(d.urgency||'standard')}.</small></p>${appeal}${form}</article>`;
}

async function load(){
  await requireUser();
  const {data,error}=await getSupabase().rpc('moderation_my_decisions',{p_limit:50});
  if(error)throw error;
  const decisions=Array.isArray(data?.decisions)?data.decisions:[];
  if(!list)return;
  list.innerHTML=decisions.length?decisions.map(decisionCard).join(''):'<div class="notice"><strong>Aucune décision de modération</strong><p>Vous n’avez actuellement aucune mesure de modération enregistrée dans ce centre.</p></div>';
  list.querySelectorAll('[data-appeal-form]').forEach(form=>{
    form.addEventListener('submit',async e=>{
      e.preventDefault();
      const decisionId=form.dataset.decisionId;
      const text=String(new FormData(form).get('appeal_text')||'').trim();
      if(text.length<20){setStatus(status,'Expliquez votre contestation en au moins 20 caractères.','error');return}
      const button=form.querySelector('button[type="submit"]');if(button)button.disabled=true;
      const {data:result,error:appealError}=await getSupabase().rpc('moderation_submit_appeal',{p_decision_id:decisionId,p_appeal_text:text});
      if(button)button.disabled=false;
      if(appealError||!result?.ok){
        const raw=String(appealError?.message||'');
        const message=/APPEAL_ALREADY_EXISTS/i.test(raw)?'Un appel existe déjà pour cette décision.':/APPEAL_DEADLINE_PASSED/i.test(raw)?'La date limite d’appel est dépassée.':'Impossible d’envoyer l’appel pour le moment.';
        setStatus(status,message,'error');return;
      }
      setStatus(status,'Appel envoyé. Il sera examiné humainement sans frais.','success');
      await load();
    });
  });
}

load().catch(error=>{
  console.error('[SINJIRA moderation appeals]',error);
  if(list)list.innerHTML='<div class="v24-empty">Impossible de charger les décisions de modération.</div>';
  setStatus(status,'Centre des appels temporairement indisponible.','error');
});
