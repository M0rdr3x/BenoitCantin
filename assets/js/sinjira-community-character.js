import {getSupabase,requireCommunityUser,escapeHtml,formatDate,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.79';
import {editOwnContent,deleteOwnContent,editedSuffix} from './sinjira-social-self-content.js?v=24.4.72';
import {openSocialReport} from './sinjira-social-safety-v24-4-79.js?v=24.4.79';

const UI_VERSION='24.4.79';
const feed=document.querySelector('[data-character-feed]');
const form=document.querySelector('[data-character-post-form]');
const status=document.querySelector('[data-social-status]');
const identity=document.querySelector('[data-character-identity]');
const lock=document.querySelector('[data-character-network-lock]');
let user,me;

function portrait(profile={}){
  const path=String(profile.portrait_path||'').trim();
  return path.startsWith('/')?path:'/assets/media/sinjira-emblem.webp';
}

function fail(error,fallback='Action impossible dans le Réseau personnage.'){
  socialErrorStatus(status,error,fallback);
}

async function charMap(ids){
  if(!ids.length)return new Map();
  const {data,error}=await getSupabase()
    .from('character_social_profiles')
    .select('character_id,public_name,portrait_path,status')
    .in('character_id',[...new Set(ids)]);
  if(error)throw error;
  const rows=Array.isArray(data)?data:[];
  return new Map(rows.map(row=>[row.character_id,row]));
}

async function load(){
  const s=getSupabase();
  const {data:postData,error}=await s.from('social_character_posts').select('*').order('created_at',{ascending:false}).limit(60);
  if(error)throw error;
  const posts=Array.isArray(postData)?postData:[];
  const postIds=posts.map(row=>row.id);
  const charIds=posts.map(row=>row.character_id);
  const [commentsResult,likesResult]=await Promise.all([
    postIds.length?s.from('social_character_comments').select('*').in('post_id',postIds).order('created_at'):Promise.resolve({data:[],error:null}),
    postIds.length?s.from('social_character_likes').select('*').in('post_id',postIds):Promise.resolve({data:[],error:null})
  ]);
  if(commentsResult.error)throw commentsResult.error;
  if(likesResult.error)throw likesResult.error;
  const comments=Array.isArray(commentsResult.data)?commentsResult.data:[];
  const likes=Array.isArray(likesResult.data)?likesResult.data:[];
  charIds.push(...comments.map(row=>row.character_id));
  const cmap=await charMap(charIds);

  feed.innerHTML=posts.map(post=>{
    const profile=cmap.get(post.character_id)||{};
    const postComments=comments.filter(row=>row.post_id===post.id);
    const postLikes=likes.filter(row=>row.post_id===post.id);
    const liked=postLikes.some(row=>row.user_id===user.id);
    const ownPost=post.user_id===user.id;
    const postControls=ownPost
      ?'<span><button class="btn btn-secondary btn-small" data-edit>Modifier</button> <button class="btn btn-secondary btn-small" data-delete>Supprimer</button></span>'
      :'<button class="btn btn-secondary btn-small" data-report>Signaler</button>';
    const commentHtml=postComments.slice(-4).map(comment=>{
      const cp=cmap.get(comment.character_id)||{};
      const ownComment=comment.user_id===user.id;
      const controls=ownComment
        ?'<span><button class="link-button" data-edit-comment>Modifier</button> <button class="link-button" data-delete-comment>Supprimer</button></span>'
        :'<button class="link-button" data-report-comment>Signaler</button>';
      return `<div class="v20-comment" data-comment="${escapeHtml(comment.id)}"><strong>${escapeHtml(cp.public_name||'Personnage')}</strong><p>${escapeHtml(comment.body)}</p><small>${escapeHtml(formatDate(comment.created_at)+editedSuffix(comment))}</small>${controls}</div>`;
    }).join('');
    return `<article class="v20-social-card" data-post="${escapeHtml(post.id)}">
      <div class="v20-social-meta"><div class="v20-social-identity"><img class="v20-social-avatar character" src="${escapeHtml(portrait(profile))}" alt=""><div><span class="v20-social-name">${escapeHtml(profile.public_name||'Personnage SINJIRA')}</span><time class="v20-social-time">${escapeHtml(formatDate(post.created_at)+editedSuffix(post))} · rôle-play</time></div></div>${postControls}</div>
      <p class="v20-social-body">${escapeHtml(post.body)}</p>
      <div class="v20-social-actions"><button class="btn btn-secondary btn-small" data-like>${liked?'♥':'♡'} ${postLikes.length}</button><span>${postComments.length} commentaire(s)</span></div>
      <div class="v20-comments">${commentHtml}</div>
      <form class="v20-comment-form" data-comment-form><input name="body" maxlength="1000" placeholder="Répondre en personnage…" required><button class="btn btn-secondary btn-small" type="submit">Envoyer</button></form>
    </article>`;
  }).join('')||'<article class="v20-social-card"><h2>Le Réseau des personnages est prêt</h2><p>Les personnages approuvés peuvent commencer à interagir ici.</p></article>';
  bind(posts,comments);
}

function reportTarget({targetType,targetId,label}){
  openSocialReport({
    network:'character',targetType,targetId,label,statusNode:status,
    onDone:async({blocked})=>{if(blocked)await load();}
  });
}

function bind(posts,comments){
  feed.querySelectorAll('[data-post]').forEach(card=>{
    const id=card.dataset.post;
    const post=posts.find(row=>row.id===id);

    card.querySelector('[data-edit]')?.addEventListener('click',async()=>{
      if(!post)return;
      try{
        if(await editOwnContent({table:'social_character_posts',id,current:post.body,max:3000,label:'cette publication de votre personnage'})){
          await load();
          socialStatus(status,`Publication personnage modifiée · interface ${UI_VERSION}.`,'success');
        }
      }catch(error){fail(error,'Modification impossible pour le moment.');}
    });

    card.querySelector('[data-delete]')?.addEventListener('click',async()=>{
      try{
        if(await deleteOwnContent({table:'social_character_posts',id,label:'cette publication de votre personnage'}))await load();
      }catch(error){fail(error,'Suppression impossible pour le moment.');}
    });

    card.querySelector('[data-report]')?.addEventListener('click',()=>{
      if(post)reportTarget({targetType:'post',targetId:id,label:'cette publication en personnage'});
    });

    card.querySelector('[data-like]')?.addEventListener('click',async()=>{
      const s=getSupabase();
      const {data,error:readError}=await s.from('social_character_likes').select('post_id').eq('post_id',id).eq('user_id',user.id).maybeSingle();
      if(readError)return fail(readError,'Impossible de vérifier votre réaction.');
      const result=data
        ?await s.from('social_character_likes').delete().eq('post_id',id).eq('user_id',user.id)
        :await s.from('social_character_likes').insert({post_id:id,user_id:user.id,character_id:me.character_id});
      if(result.error)return fail(result.error,'Impossible d’enregistrer votre réaction.');
      await load();
    });

    card.querySelectorAll('[data-comment]').forEach(commentCard=>{
      const comment=comments.find(row=>row.id===commentCard.dataset.comment);
      commentCard.querySelector('[data-edit-comment]')?.addEventListener('click',async()=>{
        if(!comment)return;
        try{
          if(await editOwnContent({table:'social_character_comments',id:comment.id,current:comment.body,max:1000,label:'ce commentaire de votre personnage'}))await load();
        }catch(error){fail(error,'Modification du commentaire impossible.');}
      });
      commentCard.querySelector('[data-delete-comment]')?.addEventListener('click',async()=>{
        if(!comment)return;
        try{
          if(await deleteOwnContent({table:'social_character_comments',id:comment.id,label:'ce commentaire de votre personnage'}))await load();
        }catch(error){fail(error,'Suppression du commentaire impossible.');}
      });
      commentCard.querySelector('[data-report-comment]')?.addEventListener('click',()=>{
        if(comment)reportTarget({targetType:'comment',targetId:comment.id,label:'ce commentaire en personnage'});
      });
    });

    card.querySelector('[data-comment-form]')?.addEventListener('submit',async event=>{
      event.preventDefault();
      const commentForm=event.currentTarget;
      const body=String(new FormData(commentForm).get('body')||'').trim();
      if(!body)return;
      const button=commentForm.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      try{
        const {error}=await getSupabase().from('social_character_comments').insert({post_id:id,user_id:user.id,character_id:me.character_id,body});
        if(error)return fail(error,'Impossible de publier ce commentaire.');
        commentForm.reset();
        await load();
      }finally{
        if(button)button.disabled=false;
      }
    });
  });
}

async function getMyCharacter(){
  const {data,error}=await getSupabase().from('character_social_profiles').select('character_id,user_id,public_name,public_description,portrait_path,status').eq('user_id',user.id).maybeSingle();
  if(error)throw error;
  return data||null;
}

async function tryOwnerRepair(){
  if(String(user?.email||'').trim().toLowerCase()!=='kingtyrano@gmail.com')return null;
  const {data,error}=await getSupabase().rpc('ensure_sinjira_owner_character');
  if(error)throw error;
  if(!data?.ok)throw new Error(data?.code||'OWNER_CHARACTER_REPAIR_FAILED');
  return data;
}

function showLocked(owner){
  form.hidden=true;
  lock.hidden=false;
  identity.innerHTML=owner
    ?'<strong>Mode personnage — synchronisation indisponible</strong><p>AbyssTime est reconnu par votre compte, mais le profil social n’a pas pu être confirmé.</p>'
    :'<strong>Mode personnage — verrouillé</strong><p>Votre personnage doit être approuvé et visible avant d’utiliser ce réseau.</p>';
  lock.innerHTML=owner
    ?'<div class="v20-character-lock"><h2>Synchronisation AbyssTime interrompue</h2><p>La réparation automatique V24.4.20 couvre la fiche personnage, le profil social et le Monde parallèle. Rechargez la page; si le problème persiste, l’état serveur sera signalé par les contrôles de production.</p><a class="btn btn-primary" href="mon-personnage.html">Voir Mon personnage</a></div>'
    :'<div class="v20-character-lock"><h2>Réseau personnage verrouillé</h2><p>Vous devez d’abord avoir votre unique personnage SINJIRA approuvé et visible dans votre compte.</p><a class="btn btn-primary" href="mon-personnage.html">Voir Mon personnage</a></div>';
}

(async()=>{
  try{
    user=await requireCommunityUser();
    const owner=String(user?.email||'').trim().toLowerCase()==='kingtyrano@gmail.com';
    me=await getMyCharacter();
    let repair=null;
    if(!me&&owner){repair=await tryOwnerRepair();me=await getMyCharacter();}
    if(!me){showLocked(owner);return;}

    identity.innerHTML=`<strong>Mode personnage — ${escapeHtml(me.public_name)}</strong><p>Ici vous écrivez uniquement en tant que votre personnage SINJIRA. Cet espace est du rôle-play et ne modifie jamais le canon officiel.${repair?.repair_version?` Synchronisation ${escapeHtml(repair.repair_version)} confirmée.`:''}</p>`;
    form.hidden=false;
    lock.hidden=true;

    form.addEventListener('submit',async event=>{
      event.preventDefault();
      const body=String(new FormData(form).get('body')||'').trim();
      if(!body)return;
      const button=form.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      try{
        const {error}=await getSupabase().from('social_character_posts').insert({user_id:user.id,character_id:me.character_id,body});
        if(error)return fail(error,'Impossible de publier en personnage pour le moment.');
        form.reset();
        await load();
        socialStatus(status,`Publication enregistrée · interface ${UI_VERSION}.`,'success');
      }finally{
        if(button)button.disabled=false;
      }
    });

    await load();
    socialStatus(status,`Réseau personnage prêt · interface ${UI_VERSION}.`,'success');
  }catch(error){
    if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise'){
      fail(error,'Le Réseau personnage n’a pas pu terminer sa vérification. Rechargez la page pour réessayer.');
      if(identity)identity.innerHTML='<strong>Mode personnage — indisponible</strong><p>Le service personnage n’a pas pu terminer la vérification.</p>';
    }
  }
})();
