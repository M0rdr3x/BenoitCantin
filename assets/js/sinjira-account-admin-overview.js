import {getSupabase} from './sinjira-supabase.js';
(async()=>{
  const entry=document.querySelector('[data-admin-entry]');
  const pending=document.querySelector('[data-admin-pending-count]');
  const reports=document.querySelector('[data-admin-report-count]');
  const active=document.querySelector('[data-admin-active-count]');
  try{
    const s=getSupabase();
    const {data:{user},error:userError}=await s.auth.getUser();
    if(userError||!user)return;
    const {data:isAdmin,error:roleError}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});
    if(roleError||!isAdmin)return;
    const [adminResult,reportResult]=await Promise.all([
      s.functions.invoke('admin-console',{body:{action:'dashboard'}}),
      s.functions.invoke('admin-reports',{body:{action:'dashboard'}})
    ]);
    if(!adminResult.error&&adminResult.data?.ok){
      if(pending)pending.textContent=String(adminResult.data.dashboard?.pending_requests??0);
      if(!reportResult.error&&reportResult.data?.ok){
        if(reports)reports.textContent=String(reportResult.data.dashboard?.game_reports??0);
        if(active)active.textContent=String(reportResult.data.dashboard?.active_parties??0);
      }
      if(entry)entry.hidden=false;
    }
  }catch(_){}
})();
