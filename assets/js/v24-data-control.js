import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';

const status=document.querySelector('[data-account-status]');
const exportButton=document.querySelector('[data-export-data]');
const deleteButton=document.querySelector('[data-delete-account]');
const PAGE_SIZE=1000;

const user=await requireUser();
const s=getSupabase();

function safeError(error){
  const text=String(error?.message||'Erreur serveur').replace(/\s+/g,' ').trim();
  return text.length>180?`${text.slice(0,177)}…`:text;
}

async function fetchAll(label,build){
  const rows=[];
  let from=0;
  for(let page=0;page<100;page++){
    const {data,error}=await build().range(from,from+PAGE_SIZE-1);
    if(error)throw new Error(`${label}: ${safeError(error)}`);
    const batch=data||[];
    rows.push(...batch);
    if(batch.length<PAGE_SIZE)return rows;
    from+=PAGE_SIZE;
  }
  throw new Error(`${label}: export trop volumineux pour le navigateur.`);
}

function queries(uid){
  return {
    profile:()=>s.from('profiles').select('*').eq('user_id',uid),
    safety_profile:()=>s.from('account_safety_profiles').select('*').eq('user_id',uid),
    legacy_preferences:()=>s.from('account_legacy_preferences').select('*').eq('user_id',uid),
    privacy_settings:()=>s.from('privacy_settings').select('*').eq('user_id',uid),
    notification_preferences:()=>s.from('notification_preferences').select('*').eq('user_id',uid),
    research_consent:()=>s.from('research_consents').select('*').eq('user_id',uid),
    access_requests:()=>s.from('access_requests').select('*').eq('user_id',uid),
    project_access:()=>s.from('project_access').select('*,projects(name,slug)').eq('user_id',uid),
    entitlements:()=>s.from('user_entitlements').select('*,products(slug,name)').eq('user_id',uid),
    license_redemptions:()=>s.from('license_redemptions').select('*').eq('user_id',uid),
    notifications:()=>s.from('user_notifications').select('*').eq('user_id',uid),
    playtests:()=>s.from('playtest_participants').select('*,playtests(title,status)').eq('user_id',uid),
    game_sessions:()=>s.from('game_sessions').select('*').eq('user_id',uid),
    player_sheets:()=>s.from('player_sheets').select('*').eq('user_id',uid),
    endgame_sheets:()=>s.from('endgame_sheets').select('*').eq('user_id',uid),
    session_feedback:()=>s.from('session_feedback').select('*').eq('user_id',uid),
    player_reports:()=>s.from('player_reports').select('*').eq('user_id',uid),
    reader_library_legacy:()=>s.from('reader_library').select('*').eq('user_id',uid),
    reader_library:()=>s.from('sinjira_reader_library').select('*,sinjira_novels(title,slug)').eq('user_id',uid),
    novel_comments_legacy:()=>s.from('novel_comments').select('*').eq('user_id',uid),
    novel_comments:()=>s.from('sinjira_novel_comments').select('*').eq('user_id',uid),
    character_submissions:()=>s.from('character_submissions').select('*').eq('user_id',uid),
    characters:()=>s.from('characters').select('*').eq('user_id',uid),
    character_status_events:()=>s.from('character_status_events').select('*').eq('user_id',uid),
    character_applications:()=>s.from('sinjira_character_applications').select('*').eq('user_id',uid),
    reader_character_submissions:()=>s.from('reader_character_submissions').select('*').eq('user_id',uid),
    reader_characters:()=>s.from('reader_characters').select('*').eq('user_id',uid),
    parallel_character_state:()=>s.from('parallel_character_state').select('*').eq('user_id',uid),
    parallel_cycle_responses:()=>s.from('parallel_cycle_responses').select('*').eq('user_id',uid),
    parallel_world_memberships:()=>s.from('parallel_world_memberships').select('*').eq('user_id',uid),
    parallel_group_memberships:()=>s.from('parallel_group_members').select('*').eq('user_id',uid),
    private_family_links:()=>s.from('private_family_links').select('*').or(`owner_user_id.eq.${uid},related_user_id.eq.${uid}`),
    family_relationship_events:()=>s.from('family_relationship_events').select('*').or(`owner_user_id.eq.${uid},related_user_id.eq.${uid}`),
    guardian_links:()=>s.from('guardian_links').select('*').or(`guardian_user_id.eq.${uid},minor_user_id.eq.${uid}`),
    community_rules:()=>s.from('community_rule_acceptances').select('*').eq('user_id',uid),
    social_profile:()=>s.from('social_profiles').select('*').eq('user_id',uid),
    social_blocks_created:()=>s.from('social_blocks').select('*').eq('blocker_user_id',uid),
    social_real_posts:()=>s.from('social_real_posts').select('*').eq('user_id',uid),
    social_real_comments:()=>s.from('social_real_comments').select('*').eq('user_id',uid),
    social_real_messages:()=>s.from('social_real_messages').select('*').or(`sender_user_id.eq.${uid},recipient_user_id.eq.${uid}`),
    social_character_posts:()=>s.from('social_character_posts').select('*').eq('user_id',uid),
    social_character_comments:()=>s.from('social_character_comments').select('*').eq('user_id',uid),
    social_character_messages:()=>s.from('social_character_messages').select('*').or(`sender_user_id.eq.${uid},recipient_user_id.eq.${uid}`),
    orders:()=>s.from('orders').select('*').eq('user_id',uid)
  };
}

async function exportData(){
  if(!exportButton)return;
  exportButton.disabled=true;
  setStatus(status,'Préparation de votre export privé…','info');
  const sections={};
  const errors=[];
  const entries=Object.entries(queries(user.id));
  for(let i=0;i<entries.length;i++){
    const [label,build]=entries[i];
    exportButton.textContent=`Export ${i+1}/${entries.length}`;
    try{sections[label]=await fetchAll(label,build)}
    catch(error){errors.push({section:label,error:safeError(error)})}
  }
  const payload={
    format:'SINJIRA_USER_EXPORT_V24_4_70',
    exported_at:new Date().toISOString(),
    complete:errors.length===0,
    account:{id:user.id,email:user.email||null,created_at:user.created_at||null,last_sign_in_at:user.last_sign_in_at||null},
    sections,
    errors
  };
  const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const link=document.createElement('a');
  link.href=url;
  link.download=`sinjira-mes-donnees-${new Date().toISOString().slice(0,10)}.json`;
  link.click();
  setTimeout(()=>URL.revokeObjectURL(url),0);
  exportButton.textContent='Télécharger mes données';
  exportButton.disabled=false;
  if(errors.length){
    setStatus(status,`Export partiel téléchargé : ${errors.length} section(s) n’ont pas pu être lues. Le fichier contient la liste exacte des erreurs.`,'error');
  }else{
    setStatus(status,`Export complet téléchargé : ${entries.length} section(s) vérifiées.`,'success');
  }
}

async function deleteAccount(){
  if(!deleteButton)return;
  const phrase=prompt('Cette action est irréversible. Pour continuer, écrivez exactement : SUPPRIMER MON COMPTE');
  if(phrase!=='SUPPRIMER MON COMPTE')return;
  if(!confirm('Dernière confirmation : supprimer définitivement ce compte SINJIRA™ et ses données personnelles associées?'))return;
  deleteButton.disabled=true;
  setStatus(status,'Vérification de sécurité et suppression en cours…','info');
  try{
    const {data,error}=await s.functions.invoke('delete-player-account',{body:{confirm:'SUPPRIMER MON COMPTE'}});
    if(error)throw error;
    if(!data?.ok){
      if(data?.code==='OWNER_OR_ADMIN_DELETE_BLOCKED'){
        setStatus(status,'Un compte propriétaire ou administrateur ne peut pas être supprimé depuis cette page.','error');
      }else if(data?.code==='MFA_REQUIRED'){
        location.href=`/compte/mfa.html?next=${encodeURIComponent('/compte/parametres.html')}`;
        return;
      }else{
        setStatus(status,data?.error||'Suppression impossible.','error');
      }
      deleteButton.disabled=false;
      return;
    }
    await s.auth.signOut({scope:'local'}).catch(()=>{});
    location.replace('/compte/connexion.html?deleted=1');
  }catch(error){
    console.warn('[SINJIRA delete account]',error);
    setStatus(status,'Suppression impossible pour le moment. Aucune suppression supplémentaire n’a été demandée depuis cette page.','error');
    deleteButton.disabled=false;
  }
}

exportButton?.addEventListener('click',exportData);
deleteButton?.addEventListener('click',deleteAccount);
