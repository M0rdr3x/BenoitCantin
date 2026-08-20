import {getSupabase,escapeHtml} from './sinjira-supabase.js';

const s=getSupabase();
const box=document.querySelector('[data-dating-connections]');
const statusNode=document.querySelector('[data-dating-status]');
let observer=null;

const reasons=[
  ['minor_safety','Âge trompeur ou sécurité potentielle d’un mineur'],
  ['grooming','Grooming, manipulation ou sollicitation visant un mineur'],
  ['sexual_exploitation','Prostitution, proxénétisme ou exploitation sexuelle'],
  ['human_trafficking','Traite, vente ou achat de personnes'],
  ['paid_sexual_content','Contenu sexuel payant ou promotion type OnlyFans'],
  ['drugs_or_illicit_sales','Vente de drogues ou commerce illicite'],
  ['harassment','Harcèlement ou insistance répétée'],
  ['sexual_content','Contenu sexuel non désiré'],
  ['pressure','Pression pour se dévoiler ou partager des coordonnées'],
  ['scam','Arnaque, fraude ou sollicitation financière'],
  ['hate','Propos haineux ou discriminatoires'],
  ['threats','Menaces ou intimidation'],
  ['impersonation','Usurpation ou identité trompeuse'],
  ['other','Autre problème de sécurité']
];

function installSafetyNotice(){
  if(document.querySelector('[data-dating-v82-safety]'))return;
  const anchor=document.querySelector('[data-dating-adult-zone]');
  if(!anchor)return;
  const section=document.createElement('section');
  section.className='section section-tight';
  section.dataset.datingV82Safety='';
  section.innerHTML=`<div class="account-shell"><article class="account-card"><span class="eyebrow">Protection renforcée</span><h2>Rencontres SINJIRA™ est strictement 18+</h2><p><strong>Les personnes de 17 ans et moins ne peuvent pas utiliser Rencontres SINJIRA™.</strong> L’âge est vérifié côté serveur et un compte mineur ne peut pas créer de profil Rencontres.</p><div class="notice"><strong>Tolérance zéro</strong><p>La prostitution, le proxénétisme, l’exploitation sexuelle, la traite ou la vente de personnes, la vente de drogues et la promotion ou vente de contenu sexuel payant — y compris les offres de type OnlyFans — sont interdits. Signalez immédiatement toute tentative de ce type.</p></div></article></div>`;
  anchor.before(section);
}

function announce(text,type='info'){
  if(!statusNode)return;
  statusNode.hidden=false;
  statusNode.className=`account-status ${type==='error'?'error':type==='success'?'success':'info'}`;
  statusNode.textContent=text;
}

function explain(error){
  const raw=String(error?.message||error||'');
  if(raw.includes('ADULTS_ONLY'))return 'Rencontres SINJIRA™ est strictement réservé aux personnes de 18 ans et plus.';
  if(raw.includes('SINJIRA_CONTENT_POLICY_PAID_SEXUAL_CONTENT'))return 'La promotion ou la vente de contenu sexuel payant est interdite.';
  if(raw.includes('SINJIRA_CONTENT_POLICY_SEXUAL_EXPLOITATION'))return 'La prostitution, le proxénétisme et la vente de services sexuels sont interdits.';
  if(raw.includes('SINJIRA_CONTENT_POLICY_HUMAN_TRAFFICKING'))return 'La traite, la vente ou l’achat de personnes sont strictement interdits.';
  if(raw.includes('SINJIRA_CONTENT_POLICY_ILLICIT_DRUG_SALES'))return 'La vente ou la sollicitation commerciale de drogues est interdite.';
  if(raw.includes('DATING_REPORT_ALREADY_OPEN'))return 'Un signalement ouvert existe déjà pour cette rencontre.';
  if(raw.includes('DATING_REPORT_RATE_LIMIT'))return 'Trop de signalements ont été envoyés récemment. Réessayez plus tard.';
  if(raw.includes('DATING_REPORT_REASON_INVALID'))return 'Choisissez un motif de signalement valide.';
  if(raw.includes('DATING_REPORT_DETAILS_TOO_LONG'))return 'Le détail du signalement est trop long.';
  if(raw.includes('CONVERSATION_NOT_AVAILABLE'))return 'Cette rencontre ne peut plus être signalée depuis ce compte.';
  return 'Le signalement n’a pas pu être transmis.';
}

function panel(connectionId){
  const options=reasons.map(([value,label])=>`<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`).join('');
  return `<div class="dating-report-panel" data-dating-report-panel hidden>
    <div class="dating-report-head"><strong>Signaler cette rencontre</strong><button class="btn btn-secondary btn-small" type="button" data-dating-report-cancel>Annuler</button></div>
    <p>Le signalement est transmis à la modération SINJIRA™. Un extrait limité des derniers messages est conservé comme preuve, sans révéler l’identité cachée dans votre interface.</p>
    <p><strong>Priorité sécurité :</strong> signalez sans attendre toute suspicion concernant un mineur, la prostitution, le proxénétisme, la traite de personnes, la vente de drogues ou la vente de contenu sexuel.</p>
    <form data-dating-report-form data-connection-id="${escapeHtml(connectionId)}">
      <label><strong>Motif</strong><select name="reason" required><option value="">Choisir…</option>${options}</select></label>
      <label><strong>Détails utiles à la modération</strong><textarea name="details" maxlength="1200" placeholder="Décrivez brièvement ce qui s’est passé. N’ajoutez pas d’informations personnelles inutiles."></textarea></label>
      <label class="dating-report-block"><input type="checkbox" name="block"/> Bloquer aussi cette personne et fermer immédiatement la rencontre.</label>
      <div class="hero-actions"><button class="btn btn-primary btn-small" type="submit">Envoyer le signalement</button></div>
    </form>
  </div>`;
}

function decorate(){
  if(!box)return;
  observer?.disconnect();
  try{
    box.querySelectorAll('[data-dating-connection]').forEach(card=>{
      if(card.querySelector('[data-dating-report-toggle]'))return;
      const id=card.dataset.datingConnection;
      const actions=card.querySelector('.hero-actions');
      if(!actions||!id)return;
      const button=document.createElement('button');
      button.type='button';button.className='btn btn-secondary btn-small';button.dataset.datingReportToggle='';button.textContent='Signaler';
      actions.append(button);
      actions.insertAdjacentHTML('afterend',panel(id));
    });
  }finally{observer?.observe(box,{childList:true,subtree:true});}
}

box?.addEventListener('click',event=>{
  const toggle=event.target.closest('[data-dating-report-toggle]');
  if(toggle){
    const card=toggle.closest('[data-dating-connection]');
    const p=card?.querySelector('[data-dating-report-panel]');
    if(p)p.hidden=!p.hidden;
    return;
  }
  const cancel=event.target.closest('[data-dating-report-cancel]');
  if(cancel){const p=cancel.closest('[data-dating-report-panel]');if(p)p.hidden=true;}
});

box?.addEventListener('submit',async event=>{
  const form=event.target.closest('[data-dating-report-form]');if(!form)return;
  event.preventDefault();
  const fd=new FormData(form);const reason=String(fd.get('reason')||'');const details=String(fd.get('details')||'').trim();const block=fd.get('block')==='on';
  const submit=form.querySelector('button[type="submit"]');if(submit)submit.disabled=true;
  try{
    const {error}=await s.rpc('dating_report_connection',{p_connection_id:form.dataset.connectionId,p_reason:reason,p_details:details||null,p_block:block});
    if(error)throw error;
    form.reset();form.closest('[data-dating-report-panel]').hidden=true;
    announce(block?'Signalement transmis. La personne est bloquée et la rencontre est fermée.':'Signalement transmis à la modération SINJIRA™.','success');
    document.querySelector('[data-dating-refresh]')?.click();
  }catch(error){announce(explain(error),'error');}
  finally{if(submit)submit.disabled=false;}
});

installSafetyNotice();
if(box){observer=new MutationObserver(decorate);observer.observe(box,{childList:true,subtree:true});decorate();}
