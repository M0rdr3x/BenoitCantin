import {getSupabase,escapeHtml,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.82';

const reasons=[
  ['minor_safety','Sécurité d’un mineur / situation préoccupante'],
  ['grooming','Grooming, manipulation ou sollicitation d’un mineur'],
  ['off_platform_minor_contact','Tentative de déplacer un mineur hors de SINJIRA™'],
  ['sexual_exploitation','Prostitution, proxénétisme ou exploitation sexuelle'],
  ['human_trafficking','Traite, vente ou achat de personnes'],
  ['paid_sexual_content','Contenu sexuel payant ou promotion type OnlyFans'],
  ['drugs_or_illicit_sales','Vente de drogues ou commerce illicite'],
  ['harassment','Harcèlement ou attaques répétées'],
  ['sexual_content','Contenu sexuel non désiré ou inapproprié'],
  ['pressure','Pression, manipulation ou partage forcé de coordonnées'],
  ['scam','Arnaque, fraude ou sollicitation financière'],
  ['hate','Propos haineux ou discriminatoires'],
  ['threats','Menaces ou intimidation'],
  ['impersonation','Usurpation ou identité trompeuse'],
  ['spam','Spam ou sollicitation répétitive'],
  ['other','Autre problème de sécurité']
];
let dialog=null;
let active=null;

function ensureDialog(){
  if(dialog)return dialog;
  dialog=document.createElement('dialog');
  dialog.className='social-report-dialog';
  dialog.innerHTML=`<form method="dialog" class="social-report-card" data-social-report-form>
    <div class="social-report-head"><div><span class="eyebrow">Sécurité communautaire</span><h2>Signaler un contenu</h2></div><button class="btn btn-secondary btn-small" value="cancel" type="submit" data-social-report-close>Fermer</button></div>
    <p data-social-report-context>Le signalement sera transmis à la modération SINJIRA™.</p>
    <div class="social-report-note"><strong>Protection prioritaire :</strong> les situations impliquant un mineur, l’exploitation sexuelle, la traite de personnes, la prostitution, le contenu sexuel payant et la vente de drogues sont interdites sur SINJIRA™.</div>
    <label><strong>Motif</strong><select name="reason" required><option value="">Choisir…</option>${reasons.map(([value,label])=>`<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`).join('')}</select></label>
    <label><strong>Détails utiles</strong><textarea name="details" maxlength="1200" placeholder="Expliquez brièvement ce qui pose problème. N’ajoutez pas d’informations personnelles inutiles."></textarea></label>
    <label class="social-report-block"><input type="checkbox" name="block"/> Bloquer aussi ce membre. Son contenu disparaîtra de vos espaces sociaux et vos interactions seront coupées.</label>
    <div class="social-report-note">La preuve envoyée à la modération est reconstruite côté serveur à partir du contenu canonique. Le navigateur ne choisit ni l’auteur ni le snapshot utilisé comme preuve.</div>
    <div class="hero-actions"><button class="btn btn-primary" type="button" data-social-report-submit>Envoyer le signalement</button><button class="btn btn-secondary" type="submit" value="cancel">Annuler</button></div>
  </form>`;
  document.body.append(dialog);
  dialog.addEventListener('close',()=>{active=null;dialog.querySelector('form')?.reset();});
  dialog.querySelector('[data-social-report-submit]')?.addEventListener('click',submitReport);
  return dialog;
}

function errorMessage(error){
  const raw=String(error?.message||error||'');
  if(raw.includes('SOCIAL_REPORT_ALREADY_OPEN'))return 'Un signalement ouvert existe déjà pour ce contenu.';
  if(raw.includes('SOCIAL_REPORT_RATE_LIMIT'))return 'Trop de signalements ont été envoyés récemment. Réessayez plus tard.';
  if(raw.includes('SOCIAL_REPORT_SELF_FORBIDDEN'))return 'Vous ne pouvez pas signaler votre propre contenu.';
  if(raw.includes('SOCIAL_REPORT_TARGET_UNAVAILABLE'))return 'Ce contenu n’est plus disponible ou n’est plus accessible depuis votre compte.';
  if(raw.includes('SOCIAL_REPORT_DETAILS_TOO_LONG'))return 'Le détail du signalement est trop long.';
  if(raw.includes('RULES_REQUIRED'))return 'Les règles de la communauté doivent être acceptées avant d’utiliser ce signalement.';
  return 'Le signalement n’a pas pu être transmis.';
}

async function submitReport(){
  if(!active||!dialog)return;
  const current=active;
  const form=dialog.querySelector('[data-social-report-form]');
  const reason=form.elements.reason.value;
  if(!reason){form.elements.reason.reportValidity();return;}
  const details=String(form.elements.details.value||'').trim();
  const block=!!form.elements.block.checked;
  const button=dialog.querySelector('[data-social-report-submit]');if(button)button.disabled=true;
  try{
    const {error}=await getSupabase().rpc('social_report_content',{
      p_network:current.network,
      p_target_type:current.targetType,
      p_target_id:current.targetId,
      p_reason:reason,
      p_details:details||null,
      p_block:block
    });
    if(error)throw error;
    if(dialog.open)dialog.close();else dialog.removeAttribute('open');
    socialStatus(current.statusNode,block?'Signalement transmis. Le membre est aussi bloqué.':'Signalement transmis à la modération SINJIRA™.','success');
    await current.onDone?.({blocked:block});
  }catch(error){socialErrorStatus(current.statusNode,error,errorMessage(error));}
  finally{if(button)button.disabled=false;}
}

export function openSocialReport({network,targetType,targetId,label='ce contenu',statusNode=null,onDone=null}){
  const d=ensureDialog();
  active={network,targetType,targetId,label,statusNode,onDone};
  d.querySelector('[data-social-report-context]').textContent=`Vous signalez ${label}. Choisissez le motif le plus précis possible.`;
  if(typeof d.showModal==='function')d.showModal();
  else d.setAttribute('open','');
}
