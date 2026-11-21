import {getSupabase,requireUser,escapeHtml,formatDate,friendlyBackendMessage} from './sinjira-supabase.js';
const page=document.body.dataset.v18Page||'',status=document.querySelector('[data-v18-status]');
function st(msg,type='info'){if(!status)return;status.textContent=friendlyBackendMessage(msg);status.dataset.statusType=type;status.setAttribute('role',type==='error'?'alert':'status');status.hidden=false}
const rows=v=>Array.isArray(v)?v:[];
const statusLabel=s=>({submitted:'Questionnaire reçu',ai_draft:'Brouillon IA',author_review:'Révision de Benoit',approved:'Approuvé',assigned:'Roman attribué',future:'En attente d’un futur roman',published:'Publié',refused:'Refusé',archived:'Archivé'})[s]||s||'—';

async function reads(user){
  const s=getSupabase();
  const novelRes=await s.from('novels').select('*').in('status',['demo','announced','published']).order('sort_order');
  if(novelRes.error)throw novelRes.error;
  let libRes=await s.from('reader_library').select('novel_id,last_opened_at,last_page,progress_percent').eq('user_id',user.id);
  if(libRes.error){
    const fallback=await s.from('reader_library').select('novel_id,last_opened_at').eq('user_id',user.id);
    if(fallback.error)throw fallback.error;
    libRes=fallback;
  }
  const novels=rows(novelRes.data),lib=rows(libRes.data),m=new Map(lib.map(x=>[x.novel_id,x]));
  const box=document.querySelector('[data-reader-library]');
  if(!box)return;
  box.innerHTML=novels.map(n=>{const r=m.get(n.id),progress=Number(r?.progress_percent||0);return `<article class="reader-book-card"><span class="eyebrow">${escapeHtml(n.volume_label||'SINJIRA')}</span><h2>${escapeHtml(n.title)}</h2><p>${escapeHtml(n.description||'')}</p><div class="v19-progress-track"><span style="width:${Math.max(0,Math.min(100,progress))}%"></span></div><p>${r?`Progression mémorisée : ${progress}%${r.last_page?` · page ${r.last_page}`:''}`:'Pas encore ouvert avec ce compte.'}</p><div class="hero-actions">${n.demo_path?`<a class="btn btn-primary" href="${escapeHtml(n.demo_path)}">${r?.last_page>1?'Continuer ma lecture':'Lire la démo'}</a>`:''}<a class="btn btn-secondary" href="${escapeHtml(n.public_path||'/projets/sinjira/romans/')}">Page du roman</a></div></article>`}).join('')||'<p>Aucun roman disponible.</p>';
}

async function comments(user){
  const s=getSupabase();
  const load=async()=>{
    const r=await s.from('sinjira_novel_comments').select('id,body,status,spoiler,created_at,sinjira_novels(title)').eq('user_id',user.id).order('created_at',{ascending:false}).limit(100);
    if(r.error)throw r.error;
    const data=rows(r.data),box=document.querySelector('[data-my-comments]');if(!box)return;
    box.innerHTML=data.map(c=>`<article class="reader-comment" data-comment-id="${c.id}"><header><strong>${escapeHtml(c.sinjira_novels?.title||'Roman SINJIRA')}</strong><span class="character-status" data-status="${escapeHtml(c.status)}">${escapeHtml(c.status==='pending'?'En attente':c.status==='approved'?'Publié':c.status==='refused'?'Refusé':c.status)}</span></header><p>${escapeHtml(c.body)}</p>${c.spoiler?'<small>Contient des divulgâcheurs</small>':''}<time>${escapeHtml(formatDate(c.created_at))}</time>${c.status==='pending'?`<div class="hero-actions"><button class="btn btn-secondary btn-small" type="button" data-edit-comment>Modifier</button><button class="btn btn-secondary btn-small" type="button" data-delete-comment>Supprimer</button></div>`:''}</article>`).join('')||'<p>Vous n’avez encore publié aucun commentaire.</p>';
    box.querySelectorAll('[data-edit-comment]').forEach(button=>button.addEventListener('click',()=>{
      const card=button.closest('[data-comment-id]'),entry=data.find(c=>c.id===card?.dataset.commentId);
      if(!card||!entry||card.querySelector('[data-inline-edit]'))return;
      const form=document.createElement('form');
      form.className='reader-comment-inline-edit';
      form.setAttribute('data-inline-edit','');
      form.innerHTML='<label for="comment-edit-'+entry.id+'">Modifier votre commentaire</label><textarea id="comment-edit-'+entry.id+'" name="body" rows="5" minlength="3" maxlength="3000" required></textarea><div class="hero-actions"><button class="btn btn-primary btn-small" type="submit">Enregistrer</button><button class="btn btn-secondary btn-small" type="button" data-cancel-edit>Annuler</button></div>';
      const textarea=form.querySelector('textarea');
      textarea.value=entry.body;
      card.appendChild(form);
      button.disabled=true;
      textarea.focus();
      form.querySelector('[data-cancel-edit]').addEventListener('click',()=>{form.remove();button.disabled=false;button.focus();});
      form.addEventListener('submit',async event=>{
        event.preventDefault();
        const body=textarea.value.trim();
        if(body.length<3||body.length>3000){st('Le commentaire doit contenir entre 3 et 3 000 caractères.','error');return;}
        const submit=form.querySelector('[type="submit"]');
        submit.disabled=true;
        try{
          const {error}=await s.from('sinjira_novel_comments').update({body}).eq('id',entry.id).eq('user_id',user.id).eq('status','pending');
          if(error)throw error;
          st('Votre commentaire en attente a été modifié.','success');
          await load();
        }catch(error){st(error?.message||'Impossible de modifier le commentaire.','error');submit.disabled=false;}
      });
    }));
    box.querySelectorAll('[data-delete-comment]').forEach(b=>b.addEventListener('click',async()=>{const id=b.closest('[data-comment-id]').dataset.commentId;if(!confirm('Supprimer ce commentaire en attente?'))return;const {error}=await s.from('sinjira_novel_comments').delete().eq('id',id).eq('user_id',user.id).eq('status','pending');if(error)return st(error.message,'error');await load()}));
  };
  await load();
}

async function characters(user){
  const s=getSupabase();
  const [sr,cr,er]=await Promise.all([
    s.from('character_submissions').select('id,status,created_at').eq('user_id',user.id).order('created_at',{ascending:false}),
    s.from('characters').select('id,submission_id,public_name,public_description,status,novel_note,visible_to_user,novels(title)').eq('user_id',user.id).eq('visible_to_user',true).order('updated_at',{ascending:false}),
    s.from('character_status_events').select('submission_id,status,note,created_at').eq('user_id',user.id).order('created_at',{ascending:true})
  ]);
  if(sr.error||cr.error||er.error)throw sr.error||cr.error||er.error;
  const subs=rows(sr.data),chars=rows(cr.data),events=rows(er.data);
  const timeline=id=>{const e=events.filter(x=>x.submission_id===id);return e.length?`<div class="v19-timeline">${e.map(x=>`<div class="v19-timeline-item"><strong>${escapeHtml(statusLabel(x.status))}</strong><span>${escapeHtml(formatDate(x.created_at))}${x.note?` · ${escapeHtml(x.note)}`:''}</span></div>`).join('')}</div>`:''};
  const box=document.querySelector('[data-my-characters]');if(!box)return;
  let html=chars.map(c=>`<article class="character-account-card"><span class="character-status" data-status="${escapeHtml(c.status)}">${escapeHtml(statusLabel(c.status))}</span><h2>${escapeHtml(c.public_name||'Personnage SINJIRA')}</h2><p>${escapeHtml(c.public_description||'La description officielle sera ajoutée après validation.')}</p><div class="character-bible"><div><strong>Roman</strong><br>${escapeHtml(c.novels?.title||c.novel_note||'À attribuer / futur roman')}</div></div>${timeline(c.submission_id)}</article>`).join('');
  if(!html&&subs.length)html=subs.map(x=>`<article class="character-account-card"><span class="character-status" data-status="${escapeHtml(x.status)}">${escapeHtml(statusLabel(x.status))}</span><h2>Dossier de personnage</h2><p>Soumis le ${escapeHtml(formatDate(x.created_at))}. Votre personnage apparaîtra ici lorsqu’il aura été préparé.</p>${timeline(x.id)}</article>`).join('');
  box.innerHTML=html||'<article class="character-account-card"><h2>Aucun dossier</h2><p>Remplissez le questionnaire du Registre des Consciences pour commencer.</p></article>';
}

(async()=>{try{const user=await requireUser('/compte/connexion.html');if(page==='reads')await reads(user);if(page==='comments')await comments(user);if(page==='characters')await characters(user)}catch(e){if(e?.message!=='Connexion requise')st(e?.message||'Erreur du compte.','error')}})();
