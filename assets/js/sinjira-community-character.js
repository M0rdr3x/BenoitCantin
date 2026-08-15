import {getSupabase,requireCommunityUser,escapeHtml,formatDate,reportContent,socialStatus} from './sinjira-social-common.js';

const feed=document.querySelector('[data-character-feed]');
const form=document.querySelector('[data-character-post-form]');
const status=document.querySelector('[data-social-status]');
const identity=document.querySelector('[data-character-identity]');
const lock=document.querySelector('[data-character-network-lock]');
let user,me;

function portrait(profile={}){
  const p=String(profile.portrait_path||'').trim();
  return p.startsWith('/')?p:'/assets/media/sinjira-emblem.webp';
}

async function charMap(ids){
  if(!ids.length)return new Map();
  const {data}=await getSupabase().from('character_social_profiles').select('*').in('character_id',[...new Set(ids)]);
  const rows=Array.isArray(data)?data:[];
  return new Map(rows.map(x=>[x.character_id,x]));
}

async function load(){
  const s=getSupabase();
  const {data:postData,error}=await s.from('social_character_posts').select('*').order('created_at',{ascending:false}).limit(60);
  if(error)throw error;
  const posts=Array.isArray(postData)?postData:[];
  const postIds=posts.map(x=>x.id);
  const charIds=posts.map(x=>x.character_id);
  const [cr,lr]=await Promise.all([
    postIds.length?s.from('social_character_comments').select('*').in('post_id',postIds).order('created_at'):{data:[]},
    postIds.length?s.from('social_character_likes').select('*').in('post_id',postIds):{data:[]}
  ]);
  const comments=Array.isArray(cr.data)?cr.data:[];
  const likes=Array.isArray(lr.data)?lr.data:[];
  charIds.push(...comments.map(x=>x.character_id));
  const cmap=await charMap(charIds);

  feed.innerHTML=posts.map(p=>{
    const cp=cmap.get(p.character_id)||{};
    const cs=comments.filter(c=>c.post_id===p.id);
    const ls=likes.filter(l=>l.post_id===p.id);
    const liked=ls.some(l=>l.user_id===user.id);
    return `<article class="v20-social-card" data-post="${p.id}">
      <div class="v20-social-meta"><div class="v20-social-identity"><img class="v20-social-avatar character" src="${escapeHtml(portrait(cp))}" alt=""><div><span class="v20-social-name">${escapeHtml(cp.public_name||'Personnage SINJIRA')}</span><time class="v20-social-time">${escapeHtml(formatDate(p.created_at))} · rôle-play</time></div></div>${p.user_id===user.id?'<button class="btn btn-secondary btn-small" data-delete>Supprimer</button>':'<button class="btn btn-secondary btn-small" data-report>Signaler</button>'}</div>
      <p class="v20-social-body">${escapeHtml(p.body)}</p>
      <div class="v20-social-actions"><button class="btn btn-secondary btn-small" data-like>${liked?'♥':'♡'} ${ls.length}</button><span>${cs.length} commentaire(s)</span></div>
      <div class="v20-comments">${cs.slice(-4).map(c=>{const cc=cmap.get(c.character_id)||{};return `<div class="v20-comment"><strong>${escapeHtml(cc.public_name||'Personnage')}</strong><p>${escapeHtml(c.body)}</p></div>`}).join('')}</div>
      <form class="v20-comment-form" data-comment-form><input name="body" maxlength="1000" placeholder="Répondre en personnage…" required><button class="btn btn-secondary btn-small" type="submit">Envoyer</button></form>
    </article>`;
  }).join('')||'<article class="v20-social-card"><h2>Le Réseau des personnages est prêt</h2><p>Les personnages approuvés peuvent commencer à interagir ici.</p></article>';
  bind(posts);
}

function bind(posts){
  feed.querySelectorAll('[data-post]').forEach(card=>{
    const id=card.dataset.post;
    const post=posts.find(x=>x.id===id);
    card.querySelector('[data-delete]')?.addEventListener('click',async()=>{
      if(confirm('Supprimer cette publication de votre personnage?')){
        const {error}=await getSupabase().from('social_character_posts').delete().eq('id',id);
        if(error)alert(error.message);else load();
      }
    });
    card.querySelector('[data-report]')?.addEventListener('click',async()=>{
      const reason=prompt('Pourquoi signalez-vous cette publication de rôle-play?');
      if(!reason)return;
      await reportContent({network:'character',target_type:'post',target_id:id,reason,snapshot:{body:post.body,character_id:post.character_id}});
      alert('Signalement transmis à l’administration.');
    });
    card.querySelector('[data-like]')?.addEventListener('click',async()=>{
      const s=getSupabase();
      const {data}=await s.from('social_character_likes').select('post_id').eq('post_id',id).eq('user_id',user.id).maybeSingle();
      if(data)await s.from('social_character_likes').delete().eq('post_id',id).eq('user_id',user.id);
      else await s.from('social_character_likes').insert({post_id:id,user_id:user.id,character_id:me.character_id});
      load();
    });
    card.querySelector('[data-comment-form]')?.addEventListener('submit',async e=>{
      e.preventDefault();
      const body=String(new FormData(e.currentTarget).get('body')||'').trim();
      if(!body)return;
      const {error}=await getSupabase().from('social_character_comments').insert({post_id:id,user_id:user.id,character_id:me.character_id,body});
      if(error)alert(error.message);else load();
    });
  });
}

async function getMyCharacter(){
  const {data,error}=await getSupabase().from('character_social_profiles').select('*').eq('user_id',user.id).maybeSingle();
  if(error)throw error;
  return data||null;
}

async function tryOwnerRepair(){
  if(String(user?.email||'').trim().toLowerCase()!=='kingtyrano@gmail.com')return false;
  try{
    const {data,error}=await getSupabase().rpc('ensure_sinjira_owner_character');
    return !error&&data?.ok===true;
  }catch(_){
    return false;
  }
}

function showLocked(owner){
  form.hidden=true;
  lock.hidden=false;
  identity.innerHTML=owner
    ?'<strong>Mode personnage — synchronisation serveur requise</strong><p>AbyssTime est reconnu comme votre personnage propriétaire, mais la fiche sociale Supabase n’est pas encore disponible.</p>'
    :'<strong>Mode personnage — verrouillé</strong><p>Votre personnage doit être approuvé et visible avant d’utiliser ce réseau.</p>';
  lock.innerHTML=owner
    ?'<div class="v20-character-lock"><h2>Synchronisation AbyssTime requise</h2><p>Le correctif automatique est déjà prévu dans V24.3.1. Dès que les migrations V24 → V24.1 → V24.3.1 sont appliquées à Supabase, cette page recréera la fiche sociale et se déverrouillera automatiquement.</p><a class="btn btn-primary" href="mon-personnage.html">Voir Mon personnage</a></div>'
    :'<div class="v20-character-lock"><h2>Réseau personnage verrouillé</h2><p>Vous devez d’abord avoir votre unique personnage SINJIRA approuvé et visible dans votre compte.</p><a class="btn btn-primary" href="mon-personnage.html">Voir Mon personnage</a></div>';
}

(async()=>{
  try{
    user=await requireCommunityUser();
    const owner=String(user?.email||'').trim().toLowerCase()==='kingtyrano@gmail.com';
    me=await getMyCharacter();

    if(!me&&owner){
      const repaired=await tryOwnerRepair();
      if(repaired)me=await getMyCharacter();
    }

    if(!me){
      showLocked(owner);
      return;
    }

    identity.innerHTML=`<strong>Mode personnage — ${escapeHtml(me.public_name)}</strong><p>Ici vous écrivez uniquement en tant que votre personnage SINJIRA. Cet espace est du rôle-play et ne modifie jamais le canon officiel.</p>`;
    form.hidden=false;
    lock.hidden=true;
    form.addEventListener('submit',async e=>{
      e.preventDefault();
      const body=String(new FormData(form).get('body')||'').trim();
      if(!body)return;
      const {error}=await getSupabase().from('social_character_posts').insert({user_id:user.id,character_id:me.character_id,body});
      if(error)return socialStatus(status,error.message,'error');
      form.reset();
      await load();
    });
    await load();
  }catch(e){
    if(e?.message!=='RULES_REQUIRED'&&e?.message!=='Connexion requise'){
      socialStatus(status,e.message||'Erreur du Réseau personnage.','error');
      if(identity)identity.innerHTML='<strong>Mode personnage — indisponible</strong><p>Le service personnage n’a pas pu terminer la vérification.</p>';
    }
  }
})();
