import {getSupabase,requireCommunityUser,escapeHtml,formatDate,avatarUrl,reportContent,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';

const UI_VERSION='24.4.42';
const feed=document.querySelector('[data-real-feed]');
const form=document.querySelector('[data-real-post-form]');
const status=document.querySelector('[data-social-status]');
const identity=document.querySelector('[data-real-identity]');
let user,me;

function fail(error,fallback='Action impossible dans la Communauté.'){
  socialErrorStatus(status,error,fallback);
}

async function profileMap(ids){
  if(!ids.length)return new Map();
  const {data,error}=await getSupabase().from('social_profiles').select('*').in('user_id',[...new Set(ids)]);
  if(error)throw error;
  const rows=Array.isArray(data)?data:[];
  return new Map(rows.map(row=>[row.user_id,row]));
}

async function load(){
  const s=getSupabase();
  const {data:postData,error}=await s.from('social_real_posts').select('*').order('created_at',{ascending:false}).limit(60);
  if(error)throw error;
  const posts=Array.isArray(postData)?postData:[];
  const postIds=posts.map(row=>row.id);
  const userIds=posts.map(row=>row.user_id);
  const [commentsResult,likesResult]=await Promise.all([
    postIds.length?s.from('social_real_comments').select('*').in('post_id',postIds).order('created_at'):Promise.resolve({data:[],error:null}),
    postIds.length?s.from('social_real_likes').select('*').in('post_id',postIds):Promise.resolve({data:[],error:null})
  ]);
  if(commentsResult.error)throw commentsResult.error;
  if(likesResult.error)throw likesResult.error;
  const comments=Array.isArray(commentsResult.data)?commentsResult.data:[];
  const likes=Array.isArray(likesResult.data)?likesResult.data:[];
  userIds.push(...comments.map(row=>row.user_id));
  const profiles=await profileMap(userIds);

  feed.innerHTML=posts.map(post=>{
    const profile=profiles.get(post.user_id)||{};
    const postComments=comments.filter(row=>row.post_id===post.id);
    const postLikes=likes.filter(row=>row.post_id===post.id);
    const liked=postLikes.some(row=>row.user_id===user.id);
    return `<article class="v20-social-card" data-post="${post.id}">
      <div class="v20-social-meta"><div class="v20-social-identity"><img class="v20-social-avatar" src="${escapeHtml(avatarUrl(profile.avatar_path))}" alt=""><div><span class="v20-social-name">${escapeHtml(profile.pseudo||profile.display_name||'Membre SINJIRA')}</span><time class="v20-social-time">${escapeHtml(formatDate(post.created_at))}</time></div></div>${post.user_id===user.id?'<button class="btn btn-secondary btn-small" data-delete>Supprimer</button>':'<button class="btn btn-secondary btn-small" data-report>Signaler</button>'}</div>
      <p class="v20-social-body">${escapeHtml(post.body)}</p>
      <div class="v20-social-actions"><button class="btn btn-secondary btn-small" data-like>${liked?'♥':'♡'} ${postLikes.length}</button><span>${postComments.length} commentaire(s)</span></div>
      <div class="v20-comments">${postComments.slice(-4).map(comment=>{const cp=profiles.get(comment.user_id)||{};return `<div class="v20-comment"><strong>${escapeHtml(cp.pseudo||cp.display_name||'Membre')}</strong><p>${escapeHtml(comment.body)}</p></div>`}).join('')}</div>
      <form class="v20-comment-form" data-comment-form><input name="body" maxlength="1000" placeholder="Écrire un commentaire…" required><button class="btn btn-secondary btn-small" type="submit">Envoyer</button></form>
    </article>`;
  }).join('')||'<article class="v20-social-card"><h2>Bienvenue dans la Communauté SINJIRA</h2><p>Soyez la première personne à publier.</p></article>';
  bind(posts);
}

function bind(posts){
  feed.querySelectorAll('[data-post]').forEach(card=>{
    const id=card.dataset.post;
    const post=posts.find(row=>row.id===id);

    card.querySelector('[data-delete]')?.addEventListener('click',async()=>{
      if(!confirm('Supprimer cette publication?'))return;
      const {error}=await getSupabase().from('social_real_posts').delete().eq('id',id);
      if(error)return fail(error,'Suppression impossible pour le moment.');
      await load();
    });

    card.querySelector('[data-report]')?.addEventListener('click',async()=>{
      const reason=prompt('Pourquoi signalez-vous cette publication?');
      if(!reason||!post)return;
      try{
        await reportContent({network:'real',target_type:'post',target_id:id,reason,snapshot:{body:post.body,user_id:post.user_id}});
        alert('Signalement transmis à l’administration.');
      }catch(error){fail(error,'Signalement impossible pour le moment.');}
    });

    card.querySelector('[data-like]')?.addEventListener('click',async()=>{
      const s=getSupabase();
      const {data,error:readError}=await s.from('social_real_likes').select('post_id').eq('post_id',id).eq('user_id',user.id).maybeSingle();
      if(readError)return fail(readError,'Impossible de vérifier votre réaction.');
      const result=data
        ?await s.from('social_real_likes').delete().eq('post_id',id).eq('user_id',user.id)
        :await s.from('social_real_likes').insert({post_id:id,user_id:user.id});
      if(result.error)return fail(result.error,'Impossible d’enregistrer votre réaction.');
      await load();
    });

    card.querySelector('[data-comment-form]')?.addEventListener('submit',async event=>{
      event.preventDefault();
      const commentForm=event.currentTarget;
      const body=String(new FormData(commentForm).get('body')||'').trim();
      if(!body)return;
      const button=commentForm.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      try{
        const {error}=await getSupabase().from('social_real_comments').insert({post_id:id,user_id:user.id,body});
        if(error)return fail(error,'Impossible de publier ce commentaire.');
        commentForm.reset();
        await load();
      }finally{
        if(button)button.disabled=false;
      }
    });
  });
}

(async()=>{
  try{
    user=await requireCommunityUser();
    const {data,error}=await getSupabase().from('social_profiles').select('*').eq('user_id',user.id).maybeSingle();
    if(error)throw error;
    me=data||{};
    if(identity)identity.innerHTML=`<strong>Mode compte réel — ${escapeHtml(me.pseudo||me.display_name||'Compte SINJIRA')}</strong><p>Vos publications utilisent votre pseudo de compte. Votre personnage n’est jamais utilisé dans cet espace.</p>`;

    form.addEventListener('submit',async event=>{
      event.preventDefault();
      const body=String(new FormData(form).get('body')||'').trim();
      if(!body)return;
      const button=form.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      try{
        const {error:insertError}=await getSupabase().from('social_real_posts').insert({user_id:user.id,body});
        if(insertError)return fail(insertError,'Impossible de publier dans la Communauté pour le moment.');
        form.reset();
        await load();
        socialStatus(status,`Publication enregistrée · interface ${UI_VERSION}.`,'success');
      }finally{
        if(button)button.disabled=false;
      }
    });

    await load();
    socialStatus(status,`Communauté prête · interface ${UI_VERSION}.`,'success');
  }catch(error){
    if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise'){
      fail(error,'La Communauté n’a pas pu terminer sa vérification. Rechargez la page pour réessayer.');
    }
  }
})();
