import {getSupabase,requireUser} from './sinjira-supabase.js';

const badge=document.querySelector('[data-mobile-notification-count]');
let user=null;

async function refreshNotifications(){
  if(!badge||!user)return;
  const {count,error}=await getSupabase().from('user_notifications')
    .select('id',{count:'exact',head:true})
    .eq('user_id',user.id)
    .is('read_at',null);
  if(error){badge.hidden=true;return}
  const value=Math.max(0,Number(count||0));
  badge.hidden=value===0;
  badge.textContent=value>99?'99+':String(value);
}

async function boot(){
  user=await requireUser();
  await refreshNotifications();
  document.addEventListener('visibilitychange',()=>{
    if(document.visibilityState==='visible')refreshNotifications().catch(()=>{});
  });
}

boot().catch(error=>{
  console.warn('[SINJIRA mobile app]',String(error?.message||'initialisation impossible'));
});
