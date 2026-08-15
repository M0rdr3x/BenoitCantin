import {getSupabase,requireUser,escapeHtml,formatDate,isSinjiraOwner} from './sinjira-supabase.js';

const box=document.querySelector('[data-my-character]');
const status=document.querySelector('[data-character-status]');
const labels={submitted:'Questionnaire reçu',ai_draft:'Brouillon IA',author_review:'En préparation',approved:'Approuvé',assigned:'Roman attribué',future:'Futur roman',published:'Publié',refused:'Refusé',archived:'Archivé'};
const list=v=>Array.isArray(v)?v:[];

function portrait(src,name){
  if(!src)return '';
  const safe=escapeHtml(src);
  return `<div class="character-account-portrait"><img src="${safe}" alt="Portrait du personnage ${escapeHtml(name||'SINJIRA')}" loading="eager"></div>`;
}

(async()=>{try{
  const user=await requireUser('/compte/connexion.html');
  const owner=isSinjiraOwner(user);
  const s=getSupabase();
  const [subRes,charRes,eventRes]=await Promise.all([
    s.from('character_submissions').select('*').eq('user_id',user.id).order('created_at',{ascending:false}).limit(1).maybeSingle(),
    s.from('characters').select('id,submission_id,public_name,public_description,portrait_path,status,novel_note,visible_to_user,novels(title)').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(1).maybeSingle(),
    s.from('character_status_events').select('*').eq('user_id',user.id).order('created_at')
  ]);

  const sub=subRes?.data||null;
  const ch=charRes?.data||null;
  const events=list(eventRes?.data);

  if(ch){
    const ready=['approved','assigned','future','published'].includes(ch.status)&&ch.visible_to_user;
    const name=ch.public_name||'Personnage SINJIRA';
    box.innerHTML=`<article class="character-account-card character-account-card-with-portrait">${portrait(ch.portrait_path,name)}<div class="character-account-copy"><div class="v20-status-line"><span class="v20-status-pill ${ready?'ready':'wait'}">${escapeHtml(labels[ch.status]||ch.status)}</span><span>1 personnage maximum par Compte SINJIRA</span></div><h1>${escapeHtml(name)}</h1><p>${escapeHtml(ch.public_description||'La description officielle sera ajoutée par Benoit Cantin.')}</p><div class="character-bible"><div><strong>Roman</strong><br>${escapeHtml(ch.novels?.title||ch.novel_note||'À attribuer / futur roman')}</div></div>${events.length?`<div class="v19-timeline">${events.map(e=>`<div class="v19-timeline-item"><strong>${escapeHtml(labels[e.status]||e.status)}</strong><span>${escapeHtml(formatDate(e.created_at))}${e.note?` · ${escapeHtml(e.note)}`:''}</span></div>`).join('')}</div>`:''}${ready?'<div class="hero-actions"><a class="btn btn-primary" href="reseau-personnage.html">Entrer dans le Réseau personnage</a><a class="btn btn-secondary" href="messages-personnage.html">Messages personnage</a></div>':'<div class="v20-character-lock"><p>Le Réseau personnage sera disponible lorsque votre personnage sera approuvé et prêt à être utilisé.</p></div>'}</div></article>`;
    return;
  }

  if(owner){
    box.innerHTML=`<div class="v20-character-lock"><span class="v20-status-pill wait">Synchronisation V24.1 requise</span><h2>AbyssTime existe dans la configuration V24, mais Supabase ne l’a pas encore rattaché à ce compte.</h2><p>Le correctif serveur V24.1 restaure automatiquement AbyssTime, son portrait, sa fiche sociale et son attribution au Livre II. Votre questionnaire${sub?' est bien enregistré':' pourra aussi être conservé'} et sera rattaché au personnage pendant cette synchronisation.</p><p><strong>Compte propriétaire :</strong> kingtyrano@gmail.com · accès total SINJIRA™.</p></div>`;
    return;
  }

  if(sub){
    box.innerHTML=`<div class="v20-character-lock"><span class="v20-status-pill wait">${escapeHtml(labels[sub.status]||sub.status)}</span><h2>Votre demande est déjà enregistrée</h2><p>Un Compte SINJIRA ne peut avoir qu’un seul personnage. Le questionnaire est maintenant verrouillé pour ce compte pendant la préparation.</p><a class="btn btn-secondary" href="../projets/sinjira/registre/">Voir le Registre</a></div>`;
    return;
  }

  box.innerHTML='<div class="v20-character-ready"><h2>Vous n’avez pas encore de personnage</h2><p>Votre Compte SINJIRA peut recevoir un seul personnage officiel issu du Registre des Consciences.</p><a class="btn btn-primary" href="../projets/sinjira/registre/">Remplir le questionnaire</a></div>';
}catch(e){
  if(e?.message!=='Connexion requise'){
    if(status){status.textContent=e?.message||'Erreur.';status.hidden=false;}
  }
}})();
