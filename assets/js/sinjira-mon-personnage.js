import {getSupabase,requireUser,escapeHtml,formatDate,isSinjiraOwner} from './sinjira-supabase.js';

const box=document.querySelector('[data-my-character]');
const status=document.querySelector('[data-character-status]');
const labels={submitted:'Questionnaire reçu',ai_draft:'Brouillon IA',author_review:'En préparation',approved:'Approuvé',assigned:'Roman attribué',future:'Futur roman',published:'Publié',refused:'Refusé',archived:'Archivé'};
const list=v=>Array.isArray(v)?v:[];

function portrait(src,name){
  if(!src)return '';
  return `<div class="character-account-portrait"><img src="${escapeHtml(src)}" alt="Portrait du personnage ${escapeHtml(name||'SINJIRA™')}" loading="eager"></div>`;
}
function renderCharacter(ch,events=[]){
  const ready=['approved','assigned','future','published'].includes(ch.status)&&ch.visible_to_user;
  const name=ch.public_name||'Personnage SINJIRA™';
  box.innerHTML=`<article class="character-account-card character-account-card-with-portrait">${portrait(ch.portrait_path,name)}<div class="character-account-copy"><div class="v20-status-line"><span class="v20-status-pill ${ready?'ready':'wait'}">${escapeHtml(labels[ch.status]||ch.status)}</span><span>1 personnage maximum par Compte SINJIRA™</span></div><h1>${escapeHtml(name)}</h1>${ch.public_description?`<p>${escapeHtml(ch.public_description)}</p>`:'<p>Le dossier public du personnage sera complété uniquement avec les informations validées par Benoit Cantin.</p>'}<div class="character-bible"><div><strong>Roman</strong><br>${escapeHtml(ch.novels?.title||ch.novel_note||'À attribuer / futur roman')}</div></div>${events.length?`<div class="v19-timeline">${events.map(e=>`<div class="v19-timeline-item"><strong>${escapeHtml(labels[e.status]||e.status)}</strong><span>${escapeHtml(formatDate(e.created_at))}${e.note?` · ${escapeHtml(e.note)}`:''}</span></div>`).join('')}</div>`:''}${ready?'<div class="hero-actions"><a class="btn btn-primary" href="reseau-personnage.html">Entrer dans le Réseau personnage</a><a class="btn btn-secondary" href="messages-personnage.html">Messages personnage</a></div>':'<div class="v20-character-lock"><p>Le Réseau personnage sera disponible lorsque votre personnage sera approuvé et prêt à être utilisé.</p></div>'}</div></article>`;
}
function renderOwnerFallback(hasSubmission=false){
  renderCharacter({public_name:'AbyssTime',public_description:'',portrait_path:'/assets/media/characters/abysstime.webp',status:'assigned',visible_to_user:true,novel_note:'SINJIRA — Livre II (titre à confirmer)'},[]);
  if(status){
    status.hidden=false;
    status.textContent=hasSubmission?'AbyssTime est reconnu par votre compte. Votre dernier questionnaire restera associé à ce même personnage après la synchronisation serveur.':'AbyssTime est reconnu par votre compte propriétaire. La fiche persistante sera synchronisée côté serveur sans créer de second personnage.';
    status.dataset.statusType='info';
  }
}

(async()=>{try{
  const user=await requireUser('/compte/connexion.html');
  const owner=isSinjiraOwner(user),s=getSupabase();
  if(owner){try{await s.rpc('ensure_sinjira_owner_character')}catch(_){/* fallback local ci-dessous */}}
  const [subRes,charRes,eventRes]=await Promise.all([
    s.from('character_submissions').select('id,status,created_at').eq('user_id',user.id).order('created_at',{ascending:false}).limit(1),
    s.from('characters').select('id,submission_id,public_name,public_description,portrait_path,status,novel_note,visible_to_user,novels(title),updated_at').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(10),
    s.from('character_status_events').select('*').eq('user_id',user.id).order('created_at')
  ]);
  const sub=list(subRes?.data)[0]||null;
  const chars=list(charRes?.data);
  const ch=chars.find(x=>x.status!=='archived'&&x.visible_to_user)||chars.find(x=>x.status!=='archived')||chars[0]||null;
  const events=list(eventRes?.data);
  if(ch){renderCharacter(ch,events);return}
  if(owner){renderOwnerFallback(Boolean(sub));return}
  if(sub){box.innerHTML=`<div class="v20-character-lock"><span class="v20-status-pill wait">${escapeHtml(labels[sub.status]||sub.status)}</span><h2>Votre demande est déjà enregistrée</h2><p>Un Compte SINJIRA™ ne peut avoir qu’un seul personnage. Le questionnaire est conservé pendant la préparation.</p><a class="btn btn-secondary" href="../projets/sinjira/registre/">Voir le Registre</a></div>`;return}
  box.innerHTML='<div class="v20-character-ready"><h2>Vous n’avez pas encore de personnage</h2><p>Votre Compte SINJIRA™ peut recevoir un seul personnage officiel issu du Registre des Consciences.</p><a class="btn btn-primary" href="../projets/sinjira/registre/">Remplir le questionnaire</a></div>';
}catch(e){
  try{
    const user=await requireUser('/compte/connexion.html');
    if(isSinjiraOwner(user)){renderOwnerFallback(false);return}
  }catch(_){/* connexion déjà gérée */}
  if(e?.message!=='Connexion requise'&&status){status.textContent='Impossible de charger le dossier du personnage pour le moment.';status.hidden=false;status.dataset.statusType='error'}
}})();
