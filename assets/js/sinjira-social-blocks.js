import {getSupabase,requireCommunityUser,escapeHtml,avatarUrl,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';

const box=document.querySelector('[data-block-list]');
const status=document.querySelector('[data-social-status]');

function fail(error,fallback='Action impossible dans la gestion des blocages.'){
  socialErrorStatus(status,error,fallback);
}

(async()=>{
  try{
    const user=await requireCommunityUser();
    const {data:blockData,error}=await getSupabase()
      .from('social_blocks')
      .select('blocked_user_id,created_at')
      .eq('blocker_user_id',user.id)
      .order('created_at',{ascending:false});
    if(error)throw error;
    const blocks=Array.isArray(blockData)?blockData:[];
    const ids=blocks.map(item=>item.blocked_user_id);
    const profileResult=ids.length
      ?await getSupabase().from('social_profiles').select('*').in('user_id',ids)
      :{data:[],error:null};
    if(profileResult.error)throw profileResult.error;
    const profiles=Array.isArray(profileResult.data)?profileResult.data:[];
    const map=new Map(profiles.map(item=>[item.user_id,item]));

    box.innerHTML=blocks.map(block=>{
      const profile=map.get(block.blocked_user_id)||{};
      return `<article class="v20-social-card" data-blocked="${escapeHtml(block.blocked_user_id)}"><div class="v20-social-identity"><img class="v20-social-avatar" src="${escapeHtml(avatarUrl(profile.avatar_path))}" alt=""><strong>${escapeHtml(profile.pseudo||profile.display_name||'Compte bloqué')}</strong></div><button class="btn btn-secondary" data-unblock>Débloquer</button></article>`;
    }).join('')||'<p>Vous n’avez bloqué aucun compte.</p>';

    box.querySelectorAll('[data-unblock]').forEach(button=>button.addEventListener('click',async()=>{
      const id=button.closest('[data-blocked]')?.dataset.blocked;
      if(!id)return;
      button.disabled=true;
      try{
        const {error:deleteError}=await getSupabase().from('social_blocks').delete().eq('blocker_user_id',user.id).eq('blocked_user_id',id);
        if(deleteError)return fail(deleteError,'Impossible de débloquer ce compte.');
        location.reload();
      }finally{
        button.disabled=false;
      }
    }));

    socialStatus(status,'Gestion des blocages prête · V24.4.42.','success');
  }catch(error){
    if(error?.message!=='RULES_REQUIRED'&&error?.message!=='Connexion requise'){
      fail(error,'La liste des blocages n’a pas pu être chargée.');
    }
  }
})();
