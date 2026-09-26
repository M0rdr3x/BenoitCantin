import {getSupabase,requireUser,setStatus,escapeHtml,formatDate} from './sinjira-supabase.js';

const s=getSupabase();
const status=document.querySelector('[data-junior-status]');
const feed=document.querySelector('[data-junior-feed]');
const form=document.querySelector('[data-junior-post-form]');
let user=null;
const accessNote=document.querySelector('[data-junior-access-note]');
const accessParams=new URLSearchParams(location.search);
if(accessNote&&accessParams.get('from')==='restricted')accessNote.hidden=false;

function setComposerEnabled(enabled){
  form?.querySelectorAll('textarea,button').forEach(node=>{node.disabled=!enabled;});
}
setComposerEnabled(false);

function juniorMessage(error,fallback='Action impossible pour le moment.'){
  const message=String(error?.message||error||'').toUpperCase();
  if(message.includes('JUNIOR_GUARDIAN_CONSENT_REQUIRED'))return 'Ton parent ou tuteur doit d’abord activer la Communauté Junior dans Relations.';
  if(message.includes('JUNIOR_RULES_REQUIRED'))return 'Lis et accepte d’abord les règles de la Communauté Junior.';
  if(message.includes('JUNIOR_COMMUNITY_11_12_ONLY'))return 'La Communauté Junior est réservée aux comptes de 11 et 12 ans.';
  if(message.includes('SINJIRA_JUNIOR_EXTERNAL_CONTACT_FORBIDDEN'))return 'Les liens, coordonnées et comptes externes ne peuvent pas être publiés dans la Communauté Junior.';
  if(message.includes('SINJIRA_JUNIOR_SEXUAL_CONTENT_FORBIDDEN'))return 'Ce contenu n’est pas permis dans la Communauté Junior.';
  if(message.includes('SINJIRA_JUNIOR_MEETUP_OR_SECRECY_FORBIDDEN'))return 'Les invitations à se rencontrer, les adresses et les demandes de garder un secret ne sont pas permises.';
  if(message.includes('SINJIRA_JUNIOR_MONEY_OR_COMMERCE_FORBIDDEN'))return 'Les ventes, paiements et échanges d’argent ne sont pas permis dans la Communauté Junior.';
  if(message.includes('JUNIOR_POST_RATE_LIMIT')||message.includes('JUNIOR_COMMENT_RATE_LIMIT'))return 'Tu as publié plusieurs fois récemment. Attends un peu avant de recommencer.';
  if(message.includes('SOCIAL_SUSPENDED'))return 'L’accès social de ce compte est temporairement limité.';
  return fallback;
}

function disableComposer(message){
  setComposerEnabled(false);
  if(feed)feed.innerHTML='<article class="v20-social-card"><h2>Communauté Junior indisponible</h2><p>'+escapeHtml(message)+'</p></article>';
}

async function refreshFeedAfterAction(successMessage,staleMessage){
  setStatus(status,successMessage,'success');
  try{
    await loadFeed();
    return true;
  }catch{
    setStatus(status,staleMessage,'info');
    return false;
  }
}

async function loadFeed(){
  const {data,error}=await s.rpc('junior_community_feed',{p_limit:30});
  if(error)throw error;
  const posts=Array.isArray(data)?data:[];
  if(!feed)return;
  feed.innerHTML=posts.map(post=>{
    const comments=Array.isArray(post.comments)?post.comments:[];
    const controls=post.mine
      ? '<button class="btn btn-secondary btn-small" type="button" data-junior-delete-post>Supprimer</button>'
      : '<button class="btn btn-secondary btn-small" type="button" data-junior-report-post>Signaler et masquer</button>';
    const commentsHtml=comments.map(comment=>{
      const commentControls=comment.mine
        ? '<button class="link-button" type="button" data-junior-delete-comment>Supprimer</button>'
        : '<button class="link-button" type="button" data-junior-report-comment>Signaler et masquer</button>';
      return '<div class="v20-comment" data-junior-comment="'+escapeHtml(comment.id)+'"><strong>'+escapeHtml(comment.author_alias||'Explorateur')+'</strong><p>'+escapeHtml(comment.body||'')+'</p><small>'+escapeHtml(formatDate(comment.created_at))+'</small>'+commentControls+'</div>';
    }).join('');
    return '<article class="v20-social-card" data-junior-post="'+escapeHtml(post.id)+'"><div class="v20-social-meta"><div class="v20-social-identity"><div><span class="v20-social-name">'+escapeHtml(post.author_alias||'Explorateur')+'</span><time class="v20-social-time">'+escapeHtml(formatDate(post.created_at))+'</time></div></div>'+controls+'</div><p class="v20-social-body">'+escapeHtml(post.body||'')+'</p><div class="v20-comments">'+commentsHtml+'</div><form class="v20-comment-form" data-junior-comment-form><input name="body" maxlength="300" placeholder="Écrire un commentaire…" required><button class="btn btn-secondary btn-small" type="submit">Envoyer</button></form></article>';
  }).join('')||'<article class="v20-social-card"><h2>Bienvenue dans la Communauté Junior</h2><p>Aucune publication pour le moment. Tu peux commencer par une idée, une découverte ou quelque chose que tu aimes dans SINJIRA.</p></article>';
  bindFeed(posts);
}

async function reportAndBlock(type,id){
  const details=prompt('Décris brièvement ce qui pose problème. N’ajoute pas de renseignements personnels.');
  if(details===null)return;
  const {error}=await s.rpc('junior_community_report_content',{
    p_target_type:type,
    p_target_id:id,
    p_reason:'other',
    p_details:String(details||'').trim().slice(0,1200)||null,
    p_block:true
  });
  if(error)throw error;
  const refreshed=await refreshFeedAfterAction(
    'Signalement enregistré. Cette personne est maintenant masquée de ton fil.',
    'Signalement enregistré et personne masquée. Le fil est temporairement fermé jusqu’à son prochain rafraîchissement.'
  );
  if(!refreshed&&feed){
    feed.innerHTML='<article class="v20-social-card"><h2>Fil temporairement masqué</h2><p>Ton signalement a bien été enregistré. Le fil reste masqué ici pour ne pas réafficher un contenu ou une personne que tu viens de bloquer. Recharge la page plus tard.</p></article>';
  }
}

function bindFeed(posts){
  feed?.querySelectorAll('[data-junior-post]').forEach(card=>{
    const postId=card.dataset.juniorPost;
    const post=posts.find(item=>item.id===postId);

    card.querySelector('[data-junior-delete-post]')?.addEventListener('click',async()=>{
      if(!confirm('Supprimer cette publication?'))return;
      const {error}=await s.rpc('junior_community_delete_post',{p_post_id:postId});
      if(error){setStatus(status,juniorMessage(error,'Suppression impossible.'),'error');return;}
      await refreshFeedAfterAction(
        'Publication supprimée.',
        'Publication supprimée, mais le fil ne peut pas être rafraîchi pour le moment.'
      );
    });

    card.querySelector('[data-junior-report-post]')?.addEventListener('click',async()=>{
      try{await reportAndBlock('post',postId);}catch(error){setStatus(status,juniorMessage(error,'Signalement impossible.'),'error');}
    });

    card.querySelector('[data-junior-comment-form]')?.addEventListener('submit',async event=>{
      event.preventDefault();
      const commentForm=event.currentTarget;
      const body=String(new FormData(commentForm).get('body')||'').trim();
      if(!body)return;
      const button=commentForm.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      try{
        const {error}=await s.rpc('junior_community_create_comment',{p_post_id:postId,p_body:body});
        if(error){setStatus(status,juniorMessage(error,'Commentaire impossible.'),'error');return;}
        commentForm.reset();
        await refreshFeedAfterAction(
          'Commentaire ajouté au fil Junior.',
          'Commentaire ajouté, mais le fil ne peut pas être rafraîchi pour le moment.'
        );
      }finally{if(button)button.disabled=false;}
    });

    card.querySelectorAll('[data-junior-comment]').forEach(commentCard=>{
      const commentId=commentCard.dataset.juniorComment;
      const comment=(post?.comments||[]).find(item=>item.id===commentId);
      commentCard.querySelector('[data-junior-delete-comment]')?.addEventListener('click',async()=>{
        if(!confirm('Supprimer ce commentaire?'))return;
        const {error}=await s.rpc('junior_community_delete_comment',{p_comment_id:commentId});
        if(error){setStatus(status,juniorMessage(error,'Suppression impossible.'),'error');return;}
        await refreshFeedAfterAction(
          'Commentaire supprimé.',
          'Commentaire supprimé, mais le fil ne peut pas être rafraîchi pour le moment.'
        );
      });
      commentCard.querySelector('[data-junior-report-comment]')?.addEventListener('click',async()=>{
        if(!comment)return;
        try{await reportAndBlock('comment',commentId);}catch(error){setStatus(status,juniorMessage(error,'Signalement impossible.'),'error');}
      });
    });
  });
}

(async()=>{
  try{
    user=await requireUser('/compte/connexion.html');
    const {data:capabilities,error:capabilityError}=await s.rpc('sinjira_my_account_capabilities');
    if(capabilityError||!capabilities)throw capabilityError||new Error('ACCOUNT_CAPABILITIES_UNAVAILABLE');
    if(capabilities.child_11_12!==true){
      location.replace('/compte/communaute.html');
      return;
    }

    if(capabilities.junior_community_enabled!==true){
      const message='Ton parent ou tuteur doit activer la Communauté Junior dans Relations avant que tu puisses entrer ici.';
      disableComposer(message);
      setStatus(status,message,'info');
      return;
    }

    if(capabilities.junior_rules_accepted!==true){
      location.replace('/compte/regles-communaute-junior.html?next=%2Fcompte%2Fcommunaute-junior.html');
      return;
    }

    setComposerEnabled(true);

    form?.addEventListener('submit',async event=>{
      event.preventDefault();
      const body=String(new FormData(form).get('body')||'').trim();
      if(!body)return;
      const button=form.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      try{
        const {error}=await s.rpc('junior_community_create_post',{p_body:body});
        if(error){setStatus(status,juniorMessage(error,'Publication impossible.'),'error');return;}
        form.reset();
        await refreshFeedAfterAction(
          'Publication ajoutée au fil Junior.',
          'Publication ajoutée, mais le fil ne peut pas être rafraîchi pour le moment.'
        );
      }finally{if(button)button.disabled=false;}
    });

    await loadFeed();
    setStatus(status,'Communauté Junior prête. Ton identité affichée est un pseudonyme protégé.','success');
  }catch(error){
    if(error?.message!=='Connexion requise')setStatus(status,juniorMessage(error,'La Communauté Junior n’a pas pu terminer sa vérification.'),'error');
  }
})();