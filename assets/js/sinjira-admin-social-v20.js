import {getSupabase,escapeHtml} from './sinjira-supabase.js';

const reasonLabels={
  harassment:'Harcèlement ou insistance répétée',
  sexual_content:'Contenu sexuel non désiré',
  pressure:'Pression pour se dévoiler ou partager des coordonnées',
  scam:'Arnaque, fraude ou sollicitation financière',
  hate:'Propos haineux ou discriminatoires',
  threats:'Menaces ou intimidation',
  impersonation:'Usurpation ou identité trompeuse',
  other:'Autre problème de sécurité'
};

async function call(action,extra={}){
  const {data,error}=await getSupabase().functions.invoke('admin-social-v20',{body:{action,...extra}});
  if(error||!data?.ok)throw new Error(data?.error||error?.message||'Erreur modération sociale');
  return data;
}

function datingEvidence(x){
  const snap=x.snapshot||{};
  const counts=snap.message_counts||{};
  const messages=Array.isArray(snap.messages)?snap.messages:[];
  const transcript=messages.map(m=>`<div class="v20-comment"><strong>${m.side==='reporter'?'Membre signalant':'Personne signalée'}</strong><p>${escapeHtml(m.body||'')}</p><small>${escapeHtml(new Date(m.created_at).toLocaleString('fr-CA'))}</small></div>`).join('');
  return `<div class="notice"><strong>Rencontre privée</strong><p>Statut au moment du signalement : ${escapeHtml(snap.connection_status||'—')} · messages : ${Number(counts.reporter||0)} / ${Number(counts.other||0)}.</p>${snap.details?`<p><b>Détails fournis :</b> ${escapeHtml(snap.details)}</p>`:''}<p><small>La cible réelle est résolue côté serveur depuis le profil dating canonique. Aucun identifiant utilisateur fourni par le snapshot n’est utilisé pour une suspension.</small></p></div>${transcript?`<div class="v20-comments"><h4>Extrait de preuve — derniers messages</h4>${transcript}</div>`:'<p>Aucun message dans cette rencontre.</p>'}`;
}

function genericEvidence(x){
  return `<pre>${escapeHtml(JSON.stringify(x.snapshot||{},null,2))}</pre>`;
}

function reportCard(x){
  const isDating=x.snapshot?.source==='dating';
  const reason=reasonLabels[x.reason]||x.reason;
  return `<article class="v20-admin-report" data-report="${escapeHtml(x.id)}"><strong>${isDating?'Rencontres SINJIRA™':escapeHtml(x.network)} · ${escapeHtml(reason)}</strong><p>Signalé le ${escapeHtml(new Date(x.created_at).toLocaleString('fr-CA'))}</p>${isDating?datingEvidence(x):genericEvidence(x)}<div class="v20-admin-actions"><button class="btn btn-primary btn-small" data-resolve>Résoudre</button>${isDating?'':'<button class="btn btn-secondary btn-small" data-remove>Retirer le contenu signalé</button>'}<button class="btn btn-secondary btn-small" data-suspend>Suspension 7 jours</button></div></article>`;
}

async function load(){
  const d=await call('dashboard');
  document.querySelector('[data-social-report-count]').textContent=String(d.dashboard.open_reports||0);
  document.querySelector('[data-social-suspension-count]').textContent=String(d.dashboard.active_suspensions||0);
  const r=await call('list_reports'),box=document.querySelector('[data-social-report-list]');
  box.innerHTML=(r.reports||[]).map(reportCard).join('')||'<p>Aucun signalement ouvert.</p>';
  box.querySelectorAll('[data-report]').forEach(card=>{
    const id=card.dataset.report;
    card.querySelector('[data-resolve]').onclick=async()=>{await call('resolve_report',{report_id:id});load();};
    const remove=card.querySelector('[data-remove]');
    if(remove)remove.onclick=async()=>{if(confirm('Retirer le contenu signalé lorsque cela est techniquement possible?')){await call('remove_reported_content',{report_id:id});load();}};
    card.querySelector('[data-suspend]').onclick=async()=>{if(confirm('Suspendre socialement le compte visé pendant 7 jours? Cette suspension désactive aussi Rencontres et ferme ses conversations actives.')){await call('suspend_reported_user',{report_id:id,days:7});load();}};
  });
}

(async()=>{try{await load();}catch(e){console.error(e);}})();