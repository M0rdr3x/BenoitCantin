import {
  getSupabase, requireUser, signOut, formatDate, escapeHtml, setStatus,
  SINJIRA_CONFIG, isSinjiraBackendConfigured, projectStatusLabel
} from './sinjira-supabase.js';

const page=document.body.dataset.accountPage||'';
const status=document.querySelector('[data-account-status]');

function safeLocalHref(value,fallback='/compte/bibliotheque.html'){
  const href=String(value||'').trim();
  return href.startsWith('/')&&!href.startsWith('//')&&!/[\u0000-\u001f\\]/.test(href)?href:fallback;
}
function boundedInt(value,min,max,fallback=null){const n=Number(value);return Number.isInteger(n)&&n>=min&&n<=max?n:fallback}
function ownedAvatarPath(path,userId){const p=String(path||'').trim();return p.startsWith(`${userId}/`)&&!p.includes('..')&&!/[\u0000-\u001f\\]/.test(p)?p:null}
function backendNotice(){
  document.querySelectorAll('[data-backend-state]').forEach(n=>{
    n.textContent=isSinjiraBackendConfigured()?'Service de comptes connecté.':'Configuration Supabase requise avant activation.';
    n.dataset.state=isSinjiraBackendConfigured()?'ready':'pending';
  });
}
async function profile(user){
  const {data,error}=await getSupabase().from('profiles').select('*').eq('user_id',user.id).maybeSingle();
  if(error)throw error;return data||{};
}
async function consent(user){
  const {data,error}=await getSupabase().from('research_consents').select('*').eq('user_id',user.id).maybeSingle();
  if(error)throw error;return data||{participate:false,share_free_text:false};
}
function sessionUrl(s){
  if(s.game_slug==='fracture-du-reseau-mere'){
    return s.party_code?`/projets/sinjira/jeux/fracture-du-reseau-mere/partie.html?code=${encodeURIComponent(s.party_code)}`:'/projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html';
  }
  return safeLocalHref(s.projects?.public_path);
}
function avatarPublicUrl(path,userId){
  const owned=ownedAvatarPath(path,userId);if(!owned)return '../assets/media/sinjira-emblem.webp';
  const {data}=getSupabase().storage.from(SINJIRA_CONFIG.avatarBucket||'sinjira-avatars').getPublicUrl(owned);
  return data?.publicUrl||'../assets/media/sinjira-emblem.webp';
}
async function loadImageFile(file){
  const url=URL.createObjectURL(file);
  try{const image=new Image();image.decoding='async';await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=()=>reject(new Error('Image illisible.'));image.src=url});return image}
  finally{setTimeout(()=>URL.revokeObjectURL(url),0)}
}
async function prepareAvatarBlob(file){
  if(file.size>8*1024*1024)throw new Error('La photo doit faire 8 Mo ou moins.');
  if(file.type&&!file.type.startsWith('image/'))throw new Error('Choisissez un fichier image.');
  let image;try{image=await loadImageFile(file)}catch{throw new Error('Ce format d’image n’est pas lisible par votre navigateur. Essayez une autre image ou convertissez-la en JPG, PNG, WebP ou AVIF.')}
  if(image.naturalWidth<160||image.naturalHeight<160)throw new Error('Choisissez une photo d’au moins 160 × 160 px.');
  const side=Math.min(image.naturalWidth,image.naturalHeight),sx=(image.naturalWidth-side)/2,sy=(image.naturalHeight-side)/2;
  const canvas=document.createElement('canvas');canvas.width=512;canvas.height=512;const ctx=canvas.getContext('2d',{alpha:false});
  if(!ctx)throw new Error('Votre navigateur ne peut pas préparer cette image.');
  ctx.fillStyle='#0b1020';ctx.fillRect(0,0,512,512);ctx.drawImage(image,sx,sy,side,side,0,0,512,512);
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/webp',0.88));if(!blob)throw new Error('Impossible d’optimiser cette photo.');return blob;
}

async function initAdminNavigation(){
  if(!isSinjiraBackendConfigured())return;
  const {data:{user},error:userError}=await getSupabase().auth.getUser();if(userError||!user)return;
  const {data:isAdmin,error}=await getSupabase().rpc('is_sinjira_admin',{p_user_id:user.id});if(error||!isAdmin)return;
  document.querySelectorAll('[data-admin-nav],[data-admin-entry]').forEach(node=>{node.hidden=false});
}

async function dashboard(){
  const user=await requireUser(),s=getSupabase(),p=await profile(user),c=await consent(user);
  document.querySelectorAll('[data-player-name]').forEach(n=>n.textContent=p.pseudo||p.display_name||user.email||'Joueur SINJIRA');
  document.querySelectorAll('[data-player-email]').forEach(n=>n.textContent=user.email||'—');
  document.querySelectorAll('[data-dashboard-avatar]').forEach(n=>{n.src=avatarPublicUrl(p.avatar_path,user.id);n.alt=`Photo de profil de ${p.pseudo||p.display_name||'joueur'}`});
  const [rs,rp,rd,rr]=await Promise.all([
    s.from('game_sessions').select('id,title,status,updated_at,game_slug,party_code,projects(name,public_path)').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(6),
    s.from('projects').select('id,slug,name,status').order('sort_order'),
    s.from('documents').select('id').eq('status','approved'),
    s.from('access_requests').select('id').eq('user_id',user.id).eq('status','pending')
  ]);
  const queryError=rs.error||rp.error||rd.error||rr.error;if(queryError)throw queryError;
  const sessions=rs.data||[],projects=rp.data||[],docs=rd.data||[],reqs=rr.data||[];
  const set=(sel,v)=>document.querySelector(sel)?.replaceChildren(document.createTextNode(String(v)));
  set('[data-stat-active]',sessions.filter(x=>x.status==='in_progress').length);set('[data-stat-finished]',sessions.filter(x=>x.status==='finished').length);set('[data-stat-projects]',projects.length);set('[data-stat-documents]',docs.length);set('[data-stat-requests]',reqs.length);
  const cs=document.querySelector('[data-contribution-status]');if(cs)cs.textContent=c.participate?'Programme Contributeur activé':'Programme Contributeur désactivé';
  const recent=document.querySelector('[data-recent-sessions]');
  if(recent)recent.innerHTML=sessions.length?sessions.map(x=>`<article class="account-session-row"><div><strong>${escapeHtml(x.title||x.projects?.name||'Partie SINJIRA')}</strong><span>${x.status==='finished'?'Terminée':'En cours'} · ${formatDate(x.updated_at)}</span></div><a class="btn btn-secondary btn-small" href="${sessionUrl(x)}">${x.status==='finished'?'Consulter':'Continuer'}</a></article>`).join(''):'<p>Aucune partie sauvegardée.</p>';
  const mini=document.querySelector('[data-dashboard-projects]');if(mini)mini.innerHTML=projects.slice(0,4).map(x=>`<a class="account-mini-project" href="/compte/projet.html?slug=${encodeURIComponent(x.slug)}"><span>${escapeHtml(x.name)}</span><small>${escapeHtml(projectStatusLabel(x.status))}</small></a>`).join('');
}

async function games(){
  const user=await requireUser(),s=getSupabase();
  const {data=[],error}=await s.from('game_sessions').select('*,projects(name,slug,public_path,play_path)').eq('user_id',user.id).order('updated_at',{ascending:false});
  if(error){setStatus(status,error.message,'error');return}
  const box=document.querySelector('[data-sessions-list]');if(!box)return;
  box.innerHTML=data.length?data.map(x=>`<article class="account-game-card"><div class="account-game-card-top"><span class="status-badge">${x.status==='finished'?'Terminée':'En cours'}</span><span>${formatDate(x.updated_at)}</span></div><p class="game-kicker">${escapeHtml(x.projects?.name||x.game_slug)}</p><h2>${escapeHtml(x.title||'Partie SINJIRA')}</h2><p>${x.player_count?`${x.player_count} joueurs`:'Nombre de joueurs non indiqué'}${x.duration_minutes?` · ${x.duration_minutes} min`:''}</p><div class="hero-actions"><a class="btn btn-primary" href="${sessionUrl(x)}">${x.status==='finished'?'Voir':'Continuer'}</a>${x.projects?.slug?`<a class="btn btn-secondary" href="/compte/projet.html?slug=${encodeURIComponent(x.projects.slug)}">Projet</a>`:''}<button class="btn btn-secondary" type="button" data-export-session="${x.id}">Exporter</button></div></article>`).join(''):'<div class="notice"><strong>Aucune partie</strong><p>Choisissez un jeu dans votre bibliothèque.</p></div>';
  box.querySelectorAll('[data-export-session]').forEach(b=>b.addEventListener('click',async()=>{
    const id=b.dataset.exportSession,session=data.find(x=>x.id===id);if(!session)return;
    const [sheets,endgame]=await Promise.all([s.from('player_sheets').select('*').eq('session_id',id).eq('user_id',user.id),s.from('endgame_sheets').select('*').eq('session_id',id).eq('user_id',user.id)]);
    if(sheets.error||endgame.error){setStatus(status,'La sauvegarde ne peut pas être exportée complètement pour le moment.','error');return}
    const payload={format:'SINJIRA_GAME_SAVE_V1',exported_at:new Date().toISOString(),session,player_sheets:sheets.data||[],endgame_sheets:endgame.data||[]};
    const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`sinjira-partie-${session.party_code||id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),0);
  }));
  const input=document.querySelector('[data-import-session]'),button=document.querySelector('[data-import-session-button]');
  button?.addEventListener('click',async()=>{
    const file=input?.files?.[0];if(!file)return setStatus(status,'Choisissez un fichier JSON de sauvegarde.','error');if(file.size>2*1024*1024)return setStatus(status,'La sauvegarde dépasse 2 Mo et ne peut pas être importée.','error');
    let newSessionId=null;
    try{
      const payload=JSON.parse(await file.text());if(payload.format!=='SINJIRA_GAME_SAVE_V1'||!payload.session)throw new Error('Format de sauvegarde incompatible.');
      const src=payload.session,gameSlug=String(src.game_slug||'').trim();if(!/^[a-z0-9-]{1,80}$/.test(gameSlug))throw new Error('Projet de sauvegarde invalide.');
      const {data:project,error:projectError}=await s.from('projects').select('slug').eq('slug',gameSlug).maybeSingle();if(projectError)throw projectError;if(!project)throw new Error('Ce projet n’est pas disponible pour votre compte.');
      const clone={user_id:user.id,game_slug:gameSlug,title:`${String(src.title||'Partie SINJIRA').slice(0,160)} — importée`,status:'in_progress',player_count:boundedInt(src.player_count,1,20),human_player_count:boundedInt(src.human_player_count,1,20),effective_player_count:boundedInt(src.effective_player_count,1,20),play_mode:['solo','duo','multiplayer'].includes(src.play_mode)?src.play_mode:null,duration_minutes:boundedInt(src.duration_minutes,0,1440),party_code:`IMP-${crypto.randomUUID().slice(0,8).toUpperCase()}`};
      const {data:newSession,error:sessionError}=await s.from('game_sessions').insert(clone).select('id').single();if(sessionError)throw sessionError;newSessionId=newSession.id;
      const sourceSheets=Array.isArray(payload.player_sheets)?payload.player_sheets.slice(0,50):[];
      const rows=sourceSheets.map(sh=>({session_id:newSession.id,user_id:user.id,sheet_key:String(sh?.sheet_key||'self').slice(0,80),sheet_label:String(sh?.sheet_label||'Fiche joueur').slice(0,160),fields:sh?.fields&&typeof sh.fields==='object'&&!Array.isArray(sh.fields)?sh.fields:{}}));
      if(new TextEncoder().encode(JSON.stringify(rows)).byteLength>500_000)throw new Error('Les fiches de cette sauvegarde sont trop volumineuses.');
      if(rows.length){const {error:sheetError}=await s.from('player_sheets').insert(rows);if(sheetError)throw sheetError}
      setStatus(status,'Sauvegarde importée comme nouvelle partie privée.','success');setTimeout(()=>location.reload(),800);
    }catch(e){if(newSessionId)await s.from('game_sessions').delete().eq('id',newSessionId).eq('user_id',user.id);setStatus(status,e.message||'Import impossible.','error')}
  });
}

async function profilePage(){
  const user=await requireUser(),p=await profile(user),form=document.querySelector('[data-profile-form]');if(!form)return;
  form.elements.pseudo.value=p.pseudo||'';form.elements.display_name.value=p.display_name||'';form.elements.email.value=user.email||'';
  const input=document.querySelector('[data-avatar-input]'),preview=document.querySelector('[data-profile-avatar]'),choose=document.querySelector('[data-avatar-choose]'),save=document.querySelector('[data-avatar-save]'),remove=document.querySelector('[data-avatar-remove]'),avatarState=document.querySelector('[data-avatar-state]');
  let selectedFile=null;
  const showStored=()=>{preview.src=avatarPublicUrl(p.avatar_path,user.id);preview.dataset.avatarPath=ownedAvatarPath(p.avatar_path,user.id)||'';preview.alt=`Photo de profil de ${p.pseudo||p.display_name||'joueur'}`;remove.hidden=!ownedAvatarPath(p.avatar_path,user.id);save.hidden=true;selectedFile=null};
  showStored();choose?.addEventListener('click',()=>input?.click());
  input?.addEventListener('change',async()=>{const file=input.files?.[0];if(!file)return;try{const blob=await prepareAvatarBlob(file);selectedFile=blob;preview.src=URL.createObjectURL(blob);save.hidden=false;avatarState.textContent='Aperçu prêt. Cliquez sur « Enregistrer la photo ».'}catch(e){setStatus(status,e.message||'Photo invalide.','error');input.value=''}});
  save?.addEventListener('click',async()=>{
    if(!selectedFile)return;save.disabled=true;choose.disabled=true;avatarState.textContent='Téléversement de la photo…';const path=`${user.id}/avatar.webp`,bucket=SINJIRA_CONFIG.avatarBucket||'sinjira-avatars';
    const {error:uploadError}=await getSupabase().storage.from(bucket).upload(path,selectedFile,{upsert:true,contentType:'image/webp',cacheControl:'3600'});
    if(uploadError){const msg=/row-level security|RLS/i.test(uploadError.message||'')?'La sécurité du stockage a refusé le téléversement. Rechargez la page pour renouveler votre session puis réessayez.':(uploadError.message||'Téléversement impossible.');setStatus(status,msg,'error');save.disabled=false;choose.disabled=false;return}
    const {error:updateError}=await getSupabase().from('profiles').update({avatar_path:path}).eq('user_id',user.id);
    if(updateError){await getSupabase().storage.from(bucket).remove([path]);setStatus(status,updateError.message,'error');save.disabled=false;choose.disabled=false;return}
    p.avatar_path=path;preview.src=`${avatarPublicUrl(path,user.id)}?v=${Date.now()}`;preview.dataset.avatarPath=path;selectedFile=null;input.value='';save.hidden=true;save.disabled=false;choose.disabled=false;remove.hidden=false;avatarState.textContent='Photo de profil enregistrée.';setStatus(status,'Photo de profil mise à jour.','success');
  });
  remove?.addEventListener('click',async()=>{
    const path=ownedAvatarPath(p.avatar_path,user.id);if(!path||!confirm('Retirer votre photo de profil?'))return;remove.disabled=true;
    const {error:storageError}=await getSupabase().storage.from(SINJIRA_CONFIG.avatarBucket||'sinjira-avatars').remove([path]);if(storageError){setStatus(status,storageError.message,'error');remove.disabled=false;return}
    const {error:updateError}=await getSupabase().from('profiles').update({avatar_path:null}).eq('user_id',user.id);if(updateError){setStatus(status,updateError.message,'error');remove.disabled=false;return}
    p.avatar_path=null;remove.disabled=false;showStored();avatarState.textContent='Photo retirée. Vous pouvez en ajouter une nouvelle.';setStatus(status,'Photo de profil retirée.','success');
  });
  form.addEventListener('submit',async e=>{e.preventDefault();const d=new FormData(form),pseudo=String(d.get('pseudo')||'').trim().slice(0,80),display_name=String(d.get('display_name')||'').trim().slice(0,160);if(!pseudo)return setStatus(status,'Le pseudo est requis.','error');const {error}=await getSupabase().from('profiles').update({pseudo,display_name}).eq('user_id',user.id);setStatus(status,error?error.message:'Profil mis à jour.',error?'error':'success')});
}

async function contributions(){
  const user=await requireUser(),c=await consent(user),form=document.querySelector('[data-contribution-form]');if(!form)return;
  form.elements.participate.checked=!!c.participate;form.elements.share_free_text.checked=!!c.share_free_text;
  form.addEventListener('submit',async e=>{
    e.preventDefault();const participate=form.elements.participate.checked,free=participate&&form.elements.share_free_text.checked,s=getSupabase();
    const {error}=await s.from('research_consents').upsert({user_id:user.id,participate,share_free_text:free,consent_version:SINJIRA_CONFIG.contributionConsentVersion,consented_at:participate?new Date().toISOString():null,revoked_at:participate?null:new Date().toISOString()},{onConflict:'user_id'});if(error){setStatus(status,error.message,'error');return}
    if(!participate&&form.elements.remove_previous.checked){const r=await s.functions.invoke('revoke-my-contributions',{body:{all:true}});if(r.error||r.data?.ok===false){setStatus(status,r.data?.error||'Consentement retiré, mais suppression des contributions précédentes impossible.','error');return}}
    setStatus(status,participate?'Programme Contributeur activé.':'Programme Contributeur désactivé.','success');
  });
}

async function settings(){
  const user=await requireUser(),s=getSupabase();
  document.querySelector('[data-export-data]')?.addEventListener('click',async()=>{
    const queries={
      profile:s.from('profiles').select('*').eq('user_id',user.id),private_profile:s.from('private_profiles').select('*').eq('user_id',user.id),relationships:s.from('family_relationships').select('*').eq('owner_user_id',user.id),privacy:s.from('privacy_settings').select('*').eq('user_id',user.id),notifications:s.from('notification_preferences').select('*').eq('user_id',user.id),questionnaire_draft:s.from('character_questionnaire_drafts').select('*').eq('user_id',user.id),
      sessions:s.from('game_sessions').select('*').eq('user_id',user.id),sheets:s.from('player_sheets').select('*').eq('user_id',user.id),feedback:s.from('session_feedback').select('*').eq('user_id',user.id),requests:s.from('access_requests').select('*').eq('user_id',user.id),access:s.from('project_access').select('*').eq('user_id',user.id),consent:s.from('research_consents').select('*').eq('user_id',user.id),
      reader_library:s.from('reader_library').select('*').eq('user_id',user.id),novel_comments:s.from('novel_comments').select('*').eq('user_id',user.id),character_submissions:s.from('character_submissions').select('*').eq('user_id',user.id),characters:s.from('characters').select('*').eq('user_id',user.id),
      social_profile:s.from('social_profiles').select('*').eq('user_id',user.id),social_posts:s.from('social_real_posts').select('*').eq('user_id',user.id),social_comments:s.from('social_real_comments').select('*').eq('user_id',user.id),social_messages:s.from('social_real_messages').select('*').or(`sender_user_id.eq.${user.id},recipient_user_id.eq.${user.id}`),social_connections:s.from('social_connections').select('*').or(`requester_user_id.eq.${user.id},recipient_user_id.eq.${user.id}`),social_blocks:s.from('social_blocks').select('*').eq('blocker_user_id',user.id),social_reports:s.from('social_reports').select('*').eq('reporter_user_id',user.id),
      character_social_profile:s.from('character_social_profiles').select('*').eq('user_id',user.id),character_posts:s.from('social_character_posts').select('*').eq('user_id',user.id),character_comments:s.from('social_character_comments').select('*').eq('user_id',user.id),character_messages:s.from('social_character_messages').select('*').or(`sender_user_id.eq.${user.id},recipient_user_id.eq.${user.id}`),
      market:s.from('market_listings').select('*').eq('seller_user_id',user.id),tokens:s.from('token_ledger').select('*').eq('user_id',user.id),parallel_responses:s.from('parallel_responses').select('*').eq('user_id',user.id),parallel_state:s.from('parallel_character_state').select('*').eq('user_id',user.id),entitlements:s.from('user_entitlements').select('*,products(slug,name)').eq('user_id',user.id)
    };
    const entries=await Promise.all(Object.entries(queries).map(async([key,query])=>{const result=await query;return {key,data:result.data||[],error:result.error}}));
    const failed=entries.filter(x=>x.error);if(failed.length){console.warn('[SINJIRA export]',failed.map(x=>[x.key,x.error?.message]));setStatus(status,`Export incomplet : ${failed.map(x=>x.key).join(', ')}. Aucune archive partielle n’a été créée.`,'error');return}
    const payload=Object.fromEntries(entries.map(x=>[x.key,x.data]));payload.exported_at=new Date().toISOString();payload.format='SINJIRA_USER_EXPORT_V24_4_11';
    const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`sinjira-mes-donnees-${new Date().toISOString().slice(0,10)}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),0);setStatus(status,'Export complet généré sur votre appareil.','success');
  });
  document.querySelector('[data-delete-account]')?.addEventListener('click',async()=>{
    if(prompt('Pour supprimer définitivement votre compte, écrivez SUPPRIMER.')!=='SUPPRIMER')return;
    const result=await s.functions.invoke('delete-player-account',{body:{confirm:'SUPPRIMER'}});if(result.error||result.data?.ok!==true){setStatus(status,result.data?.error||'Suppression impossible.','error');return}
    await s.auth.signOut();location.href='/compte/connexion.html?deleted=1';
  });
}

document.querySelectorAll('[data-logout]').forEach(b=>b.addEventListener('click',signOut));
backendNotice();
initAdminNavigation().catch(()=>{});
(async()=>{try{
  if(page==='dashboard')await dashboard();else if(page==='games')await games();else if(page==='profile')await profilePage();else if(page==='contributions')await contributions();else if(page==='settings')await settings();
}catch(e){if(e?.message!=='Connexion requise')setStatus(status,e?.message||'Une erreur est survenue.','error')}})();
