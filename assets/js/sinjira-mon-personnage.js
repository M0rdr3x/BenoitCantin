import {getSupabase,requireUser,escapeHtml,formatDate,isSinjiraOwner} from './sinjira-supabase.js';

const UI_VERSION='24.4.60';
const box=document.querySelector('[data-my-character]');
const status=document.querySelector('[data-character-status]');
const labels={submitted:'Questionnaire reçu',ai_draft:'Brouillon IA',author_review:'En préparation',approved:'Approuvé',assigned:'Roman attribué',future:'Futur roman',published:'Publié',refused:'Refusé',archived:'Archivé'};
const canonLabels={PROVISOIRE:'Provisoire',CANON:'Canon',SECRET_AUTEUR:'Secret auteur',A_ARBITRER:'À arbitrer'};
const list=v=>Array.isArray(v)?v:[];

function setStatus(message,type='info'){
  if(!status)return;
  status.hidden=false;
  status.textContent=message;
  status.dataset.statusType=type;
}

function portrait(src,name){
  if(!src)return '';
  return `<div class="character-account-portrait"><img src="${escapeHtml(src)}" alt="Portrait du personnage ${escapeHtml(name||'SINJIRA™')}" loading="eager"></div>`;
}

function timeline(submission,ch){
  const rows=[];
  if(submission?.created_at) rows.push({label:'Questionnaire reçu',date:submission.created_at});
  if(ch?.created_at) rows.push({label:'Personnage créé',date:ch.created_at});
  if(ch?.updated_at) rows.push({label:labels[ch.status]||ch.status||'Mise à jour',date:ch.updated_at});
  const seen=new Set();
  return rows.filter(row=>{
    const key=`${row.label}|${row.date}`;
    if(seen.has(key))return false;
    seen.add(key);return true;
  }).sort((a,b)=>new Date(a.date)-new Date(b.date));
}

function renderCharacter(ch,submission=null){
  const ready=['approved','assigned','future','published'].includes(ch.status)&&ch.visible_to_user!==false;
  const name=ch.public_name||'Personnage SINJIRA™';
  const steps=timeline(submission,ch);
  const canon=canonLabels[ch.canon_status]||ch.canon_status||'Provisoire';
  box.innerHTML=`<article class="character-account-card character-account-card-with-portrait">
    ${portrait(ch.portrait_path,name)}
    <div class="character-account-copy">
      <div class="v20-status-line"><span class="v20-status-pill ${ready?'ready':'wait'}">${escapeHtml(labels[ch.status]||ch.status||'En préparation')}</span><span>1 personnage maximum par Compte SINJIRA™</span></div>
      <h1>${escapeHtml(name)}</h1>
      ${ch.public_description?`<p>${escapeHtml(ch.public_description)}</p>`:'<p>Le dossier public du personnage sera complété uniquement avec les informations validées par Benoit Cantin.</p>'}
      <div class="character-bible">
        <div><strong>Roman</strong><br>${escapeHtml(ch.novels?.title||ch.novel_note||'À attribuer / futur roman')}</div>
        <div><strong>Statut de continuité</strong><br>${escapeHtml(canon)}</div>
      </div>
      ${steps.length?`<div class="v19-timeline">${steps.map(step=>`<div class="v19-timeline-item"><strong>${escapeHtml(step.label)}</strong><span>${escapeHtml(formatDate(step.date))}</span></div>`).join('')}</div>`:''}
      ${ready?'<div class="hero-actions"><a class="btn btn-primary" href="reseau-personnage.html">Entrer dans le Réseau personnage</a><a class="btn btn-secondary" href="messages-personnage.html">Messages personnage</a></div>':'<div class="v20-character-lock"><p>Le Réseau personnage sera disponible lorsque votre personnage sera approuvé et prêt à être utilisé.</p></div>'}
    </div>
  </article>`;
}

function renderOwnerFallback(message='AbyssTime est reconnu par votre Compte SINJIRA™.'){
  renderCharacter({
    public_name:'AbyssTime',
    public_description:'',
    portrait_path:'/assets/media/characters/abysstime.webp',
    status:'assigned',
    canon_status:'PROVISOIRE',
    visible_to_user:true,
    novel_note:'SINJIRA — Livre II : Le Sang du Sauveur'
  });
  setStatus(message,'success');
}

async function ensureOwnerCharacter(owner){
  if(!owner)return null;
  const {data,error}=await getSupabase().rpc('ensure_sinjira_owner_character');
  if(error)throw error;
  if(!data?.ok)throw new Error(data?.code||'OWNER_CHARACTER_REPAIR_FAILED');
  return data;
}

async function loadCharacter(user){
  const s=getSupabase();
  const [submissionResult,characterResult]=await Promise.all([
    s.from('character_submissions')
      .select('id,status,created_at,updated_at')
      .eq('user_id',user.id)
      .order('created_at',{ascending:false})
      .limit(1),
    s.from('characters')
      .select('id,submission_id,public_name,public_description,portrait_path,status,canon_status,novel_note,visible_to_user,novels(title),created_at,updated_at')
      .eq('user_id',user.id)
      .order('updated_at',{ascending:false})
      .limit(10)
  ]);

  if(submissionResult.error)throw submissionResult.error;
  if(characterResult.error)throw characterResult.error;

  const submission=list(submissionResult.data)[0]||null;
  const chars=list(characterResult.data);
  const character=chars.find(item=>item.status!=='archived'&&item.visible_to_user!==false)
    ||chars.find(item=>item.status!=='archived')
    ||chars[0]
    ||null;
  return {submission,character};
}

(async()=>{
  try{
    const user=await requireUser('/compte/connexion.html');
    const owner=isSinjiraOwner(user);
    if(owner)renderOwnerFallback('Vérification de la fiche persistante d’AbyssTime…');
    const repair=await ensureOwnerCharacter(owner);

    const {submission,character}=await loadCharacter(user);
    if(character){
      renderCharacter(character,submission);
      setStatus(owner
        ?`AbyssTime est synchronisé avec sa fiche persistante, son profil social et le Monde parallèle (interface ${UI_VERSION}${repair?.repair_version?` · serveur ${repair.repair_version}`:''}).`
        :'Votre personnage est synchronisé avec votre Compte SINJIRA™.','success');
      return;
    }

    if(owner){
      renderOwnerFallback('AbyssTime reste disponible. La fiche persistante sera réparée lors de la prochaine synchronisation serveur.');
      return;
    }

    if(submission){
      box.innerHTML=`<div class="v20-character-lock"><span class="v20-status-pill wait">${escapeHtml(labels[submission.status]||submission.status)}</span><h2>Votre demande est déjà enregistrée</h2><p>Un Compte SINJIRA™ ne peut avoir qu’un seul personnage. Le questionnaire reste lié à votre compte pendant sa préparation.</p><a class="btn btn-secondary" href="../projets/sinjira/registre/">Voir le Registre</a></div>`;
      setStatus('Votre dossier est enregistré et attend la préparation du personnage.','info');
      return;
    }

    box.innerHTML='<div class="v20-character-ready"><h2>Vous n’avez pas encore de personnage</h2><p>Votre Compte SINJIRA™ peut recevoir un seul personnage officiel issu du Registre des Consciences.</p><a class="btn btn-primary" href="../projets/sinjira/registre/">Remplir le questionnaire</a></div>';
    setStatus('Aucun dossier de personnage n’est encore associé à ce compte.','info');
  }catch(error){
    console.error('[SINJIRA mon personnage]',error);
    try{
      const user=await requireUser('/compte/connexion.html');
      if(isSinjiraOwner(user)){
        renderOwnerFallback('AbyssTime est disponible, mais le serveur n’a pas pu confirmer la dernière synchronisation.');
        return;
      }
    }catch{}
    setStatus('Impossible de charger le dossier du personnage pour le moment.','error');
  }
})();
