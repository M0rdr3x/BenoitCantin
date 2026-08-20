import {getSupabase,requireUser,escapeHtml,formatDate} from './sinjira-supabase.js';

const blocksBox=document.querySelector('[data-social-blocks]');
const reportsBox=document.querySelector('[data-social-reports]');
const statusNode=document.querySelector('[data-social-safety-status]');
const reasonLabels={
  minor_safety:'Sécurité d’un mineur',
  grooming:'Grooming ou sollicitation d’un mineur',
  off_platform_minor_contact:'Tentative de déplacer un mineur hors plateforme',
  sexual_exploitation:'Prostitution, proxénétisme ou exploitation sexuelle',
  human_trafficking:'Traite, vente ou achat de personnes',
  paid_sexual_content:'Contenu sexuel payant',
  drugs_or_illicit_sales:'Vente de drogues ou commerce illicite',
  harassment:'Harcèlement',sexual_content:'Contenu sexuel',pressure:'Pression ou manipulation',scam:'Arnaque ou fraude',hate:'Propos haineux',threats:'Menaces',impersonation:'Usurpation',spam:'Spam',other:'Autre'
};
const sourceLabels={community:'Communauté',dating:'Rencontres',real:'Communauté',character:'Réseau personnage'};

function status(text,type='info'){
  if(!statusNode)return;
  statusNode.hidden=false;
  statusNode.dataset.statusType=type;
  statusNode.textContent=text;
}

function reportStatusLabel(value){
  return {open:'En cours',resolved:'Traité',dismissed:'Classé sans suite'}[value]||value||'—';
}

async function loadBlocks(){
  if(!blocksBox)return;
  const {data=[],error}=await getSupabase().rpc('social_my_blocks');
  if(error)throw error;
  blocksBox.innerHTML=data.length?data.map(row=>`<div class="social-safety-row" data-blocked-user="${escapeHtml(row.blocked_user_id)}"><div><strong>${escapeHtml(row.display_label||'Membre SINJIRA™')}</strong><p>Bloqué le ${escapeHtml(formatDate(row.blocked_at))}</p></div><button class="btn btn-secondary btn-small" type="button" data-unblock>Débloquer</button></div>`).join(''):'<p>Aucun membre bloqué actuellement.</p>';
  blocksBox.querySelectorAll('[data-blocked-user]').forEach(row=>{
    row.querySelector('[data-unblock]')?.addEventListener('click',async()=>{
      if(!confirm('Débloquer ce membre? Son contenu pourra réapparaître dans vos espaces communautaires si les autres règles de visibilité le permettent.'))return;
      const button=row.querySelector('[data-unblock]');if(button)button.disabled=true;
      try{
        const {error:unblockError}=await getSupabase().rpc('social_unblock_user',{p_blocked_user_id:row.dataset.blockedUser});
        if(unblockError)throw unblockError;
        status('Membre débloqué.','success');
        await loadBlocks();
      }catch(error){console.error(error);status('Impossible de débloquer ce membre pour le moment.','error');}
      finally{if(button)button.disabled=false;}
    });
  });
}

async function loadReports(){
  if(!reportsBox)return;
  const {data=[],error}=await getSupabase().rpc('social_my_reports',{p_limit:20});
  if(error)throw error;
  reportsBox.innerHTML=data.length?data.map(row=>`<div class="social-safety-row"><div><strong>${escapeHtml(sourceLabels[row.source]||row.source||'Communauté')} · ${escapeHtml(reasonLabels[row.reason]||row.reason||'Signalement')}</strong><p>${escapeHtml(row.target_type||'contenu')} · ${escapeHtml(formatDate(row.created_at))}</p></div><span class="social-report-status ${escapeHtml(row.status||'open')}">${escapeHtml(reportStatusLabel(row.status))}</span></div>`).join(''):'<p>Aucun signalement récent depuis ce compte.</p>';
}

(async()=>{
  try{
    await requireUser('/compte/connexion.html');
    await Promise.all([loadBlocks(),loadReports()]);
  }catch(error){
    console.error(error);
    status('Le centre de sécurité communautaire n’a pas pu charger vos données.','error');
  }
})();
