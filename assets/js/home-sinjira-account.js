import {getCurrentUser,getSupabase,escapeHtml,isSinjiraBackendConfigured} from './sinjira-supabase.js';
const root=document.querySelector('[data-home-account]');
if(root){
 const guest=root.querySelector('[data-home-account-guest]'),member=root.querySelector('[data-home-account-member]'),name=root.querySelector('[data-home-account-name]'),email=root.querySelector('[data-home-account-email]'),avatar=root.querySelector('[data-home-account-avatar]'),admin=root.querySelector('[data-home-account-admin]'),logout=root.querySelector('[data-home-account-logout]');
 const showGuest=()=>{guest.hidden=false;member.hidden=true};
 const showMember=()=>{guest.hidden=true;member.hidden=false};
 (async()=>{
  try{
   if(!isSinjiraBackendConfigured())return showGuest();
   const user=await getCurrentUser();if(!user)return showGuest();showMember();
   const s=getSupabase();
   const {data:p}=await s.from('profiles').select('pseudo,display_name,avatar_path').eq('user_id',user.id).maybeSingle();
   const label=p?.pseudo||p?.display_name||user.email||'Compte SINJIRA';name.textContent=label;email.textContent=user.email||'';
   if(p?.avatar_path){const {data}=s.storage.from('sinjira-avatars').getPublicUrl(p.avatar_path);if(data?.publicUrl)avatar.src=data.publicUrl}else avatar.src='assets/media/sinjira-emblem.webp';
   try{const {data:isAdmin}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});admin.hidden=!isAdmin}catch{admin.hidden=true}
   logout?.addEventListener('click',async()=>{await s.auth.signOut();location.reload()});
  }catch(e){console.warn('Compte SINJIRA accueil:',e);showGuest()}
 })();
}
