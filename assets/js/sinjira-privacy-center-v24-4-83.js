import {getSupabase,requireUser,escapeHtml,formatDate} from './sinjira-supabase.js';

const form=document.querySelector('[data-privacy-request-form]');
const list=document.querySelector('[data-privacy-requests]');
const statusNode=document.querySelector('[data-privacy-status]');
const labels={access:'Accès',portability:'Copie / portabilité',rectification:'Rectification',deletion:'Suppression',consent_withdrawal:'Retrait de consentement',objection:'Opposition',complaint:'Plainte',other:'Autre'};
const statusLabels={open:'Ouverte',identity_check:'Vérification d’identité',in_review:'En révision',waiting_user:'Information demandée',completed:'Terminée',refused:'Refusée / limitée',cancelled:'Annulée'};

function showStatus(message,type='info'){
  if(!statusNode)return;
  statusNode.hidden=false;
  statusNode.dataset.statusType=type;
  statusNode.textContent=message;
}

function render(rows){
  if(!list)return;
  if(!rows.length){list.innerHTML='<p>Aucune demande enregistrée pour ce compte.</p>';return;}
  list.innerHTML=rows.map(row=>`<article class="v24-panel"><h3>${escapeHtml(labels[row.request_type]||row.request_type)}</h3><p><strong>${escapeHtml(statusLabels[row.status]||row.status)}</strong> · créée le ${escapeHtml(formatDate(row.created_at))}</p><p>Échéance interne cible : ${escapeHtml(formatDate(row.due_at))}</p>${row.response_note?`<p><strong>Réponse :</strong> ${escapeHtml(row.response_note)}</p>`:''}</article>`).join('');
}

async function loadRequests(){
  const {data=[],error}=await getSupabase().rpc('privacy_my_requests',{p_limit:20});
  if(error)throw error;
  render(data);
}

(async()=>{
  try{
    await requireUser('/compte/connexion.html');
    await loadRequests();
  }catch(error){
    console.error(error);
    showStatus('Le Centre Vie privée ne peut pas charger vos demandes pour le moment.','error');
  }
})();

form?.addEventListener('submit',async event=>{
  event.preventDefault();
  const button=form.querySelector('button[type="submit"]');
  if(button)button.disabled=true;
  try{
    const fd=new FormData(form);
    const requestType=String(fd.get('request_type')||'').trim();
    const details=String(fd.get('details')||'').trim();
    if(!requestType)throw new Error('Choisissez un type de demande.');
    const {error}=await getSupabase().rpc('privacy_create_request',{p_request_type:requestType,p_details:details||null});
    if(error)throw error;
    form.reset();
    showStatus('Votre demande a été enregistrée. Elle apparaît maintenant dans votre suivi.','success');
    await loadRequests();
  }catch(error){
    console.error(error);
    const msg=String(error?.message||'');
    if(msg.includes('PRIVACY_REQUEST_OPEN_LIMIT'))showStatus('Vous avez déjà plusieurs demandes ouvertes. Terminez leur suivi avant d’en créer une nouvelle.','error');
    else if(msg.includes('PRIVACY_REQUEST_DETAILS_TOO_LONG'))showStatus('Les précisions sont trop longues.','error');
    else showStatus('Impossible d’enregistrer la demande pour le moment.','error');
  }finally{if(button)button.disabled=false;}
});
