import {
  getSupabase, requireUser, signOut, formatDate, escapeHtml, setStatus,
  SINJIRA_CONFIG, isSinjiraBackendConfigured, projectStatusLabel
} from './sinjira-supabase.js';

const page=document.body.dataset.accountPage||'';
const status=document.querySelector('[data-account-status]');

function nextDestination(def='/compte/index.html'){
  const n=new URLSearchParams(location.search).get('next');
  return n&&n.startsWith('/')?n:def;
}
function backendNotice(){
  document.querySelectorAll('[data-backend-state]').forEach(n=>{
    n.textContent=isSinjiraBackendConfigured()?'Service de comptes connecté.':'Configuration Supabase requise avant activation.';
    n.dataset.state=isSinjiraBackendConfigured()?'ready':'pending';
  });
}
async function profile(user){
  const {data}=await getSupabase().from('profiles').select('*').eq('user_id',user.id).maybeSingle();
  return data||{};
}
async function consent(user){
  const {data}=await getSupabase().from('research_consents').select('*').eq('user_id',user.id).maybeSingle();
  return data||{participate:false,share_free_text:false};
}
function sessionUrl(s){
  if(s.game_slug==='fracture-du-reseau-mere'){
    return s.party_code
      ? `/projets/sinjira/jeux/fracture-du-reseau-mere/partie.html?code=${encodeURIComponent(s.party_code)}`
      : '/projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html';
  }
  return s.projects?.public_path||'/compte/bibliotheque.html';
}
function avatarPublicUrl(path){
  if(!path) return '../assets/media/sinjira-emblem.webp';
  const {data}=getSupabase().storage.from(SINJIRA_CONFIG.avatarBucket||'sinjira-avatars').getPublicUrl(path);
  return data?.publicUrl||'../assets/media/sinjira-emblem.webp';
}
async function loadImageFile(file){
  const url=URL.createObjectURL(file);
  try{
    const image=new Image();
    image.decoding='async';
    await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=()=>reject(new Error('Image illisible.'));image.src=url});
    return image;
  }finally{setTimeout(()=>URL.revokeObjectURL(url),0)}
}
async function prepareAvatarBlob(file){
  if(file.size>8*1024*1024) throw new Error('La photo doit faire 8 Mo ou moins.');
  if(file.type && !file.type.startsWith('image/')) throw new Error('Choisissez un fichier image.');
  let image;
  try{
    image=await loadImageFile(file);
  }catch(_){
    throw new Error('Ce format d’image n’est pas lisible par votre navigateur. Essayez une autre image ou convertissez-la en JPG, PNG, WebP ou AVIF.');
  }
  if(image.naturalWidth<160||image.naturalHeight<160) throw new Error('Choisissez une photo d’au moins 160 × 160 px.');
  const side=Math.min(image.naturalWidth,image.naturalHeight);
  const sx=(image.naturalWidth-side)/2, sy=(image.naturalHeight-side)/2;
  const canvas=document.createElement('canvas'); canvas.width=512; canvas.height=512;
  const ctx=canvas.getContext('2d',{alpha:false});
  ctx.fillStyle='#0b1020';
  ctx.fillRect(0,0,512,512);
  ctx.drawImage(image,sx,sy,side,side,0,0,512,512);
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/webp',0.88));
  if(!blob) throw new Error('Impossible d’optimiser cette photo.');
  return blob;
}


async function initAdminNavigation(){
  if(!isSinjiraBackendConfigured()) return;
  const {data:{user},error:userError}=await getSupabase().auth.getUser();
  if(userError||!user) return;
  const {data:isAdmin,error}=await getSupabase().rpc('is_sinjira_admin',{p_user_id:user.id});
  if(error||!isAdmin) return;
  document.querySelectorAll('[data-admin-nav],[data-admin-entry]').forEach(node=>{node.hidden=false});
}


async function signup(){
  const form=document.querySelector('[data-signup-form]'); if(!form)return;
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!isSinjiraBackendConfigured()){setStatus(status,'Supabase doit d’abord être configuré.','error');return}
    const d=new FormData(form), pw=String(d.get('password')||''), pw2=String(d.get('password_confirm')||'');
    if(pw.length<12){setStatus(status,'Utilisez un mot de passe d’au moins 12 caractères.','error');return}
    if(pw!==pw2){setStatus(status,'Les mots de passe ne correspondent pas.','error');return}
    const contributor=d.get('initial_contributor_opt_in')==='yes';
    const fillCharacter=d.get('fill_character_now')==='yes';
    const languages=String(d.get('languages')||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,12);
    const quickQuestionnaire=fillCharacter?{
      sociability:String(d.get('q_sociability')||''),decision_style:String(d.get('q_decision')||''),danger_style:String(d.get('q_danger')||''),social_group:String(d.get('q_social_group')||''),conflict_style:String(d.get('q_conflict')||''),trust_style:String(d.get('q_trust')||''),natural_role:String(d.get('q_role')||''),pressure_style:String(d.get('q_pressure')||''),core_value:String(d.get('q_value')||''),main_strength:String(d.get('q_strength')||''),main_weakness:String(d.get('q_weakness')||''),archetype:String(d.get('q_archetype')||''),notes:String(d.get('q_notes')||'')
    }:null;
    const metadata={
      pseudo:String(d.get('pseudo')||'').trim(),display_name:String(d.get('display_name')||'').trim(),
      birth_date:String(d.get('birth_date')||''),gender:String(d.get('gender')||''),languages,
      residence_city:String(d.get('residence_city')||'').trim(),residence_region:String(d.get('residence_region')||'').trim(),residence_country:String(d.get('residence_country')||'').trim(),
      origin_city:String(d.get('origin_city')||'').trim(),origin_region:String(d.get('origin_region')||'').trim(),origin_country:String(d.get('origin_country')||'').trim(),
      relationship_status:String(d.get('relationship_status')||''),relationship_since:String(d.get('relationship_since')||''),relationship_partner_label:String(d.get('relationship_partner_label')||'').trim(),
      fill_character_now:fillCharacter,quick_character_questionnaire:quickQuestionnaire,
      initial_contributor_opt_in:contributor,initial_share_free_text:contributor&&d.get('share_free_text')==='yes'
    };
    const {data,error}=await getSupabase().auth.signUp({
      email:String(d.get('email')||'').trim(),password:pw,
      options:{emailRedirectTo:`${SINJIRA_CONFIG.siteUrl}/compte/index.html`,data:metadata}
    });
    if(error){setStatus(status,error.message,'error');return}
    if(data.session){location.href=nextDestination();return}
    setStatus(status,fillCharacter?'Compte créé. Vérifiez votre courriel. Votre questionnaire rapide a été conservé comme brouillon privé dans le compte.':'Compte créé. Vérifiez votre courriel pour confirmer votre adresse.','success');form.reset();
  });
}
async function login(){
  const form=document.querySelector('[data-login-form]');if(!form)return;
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!isSinjiraBackendConfigured()){setStatus(status,'Supabase doit d’abord être configuré.','error');return}
    const d=new FormData(form);
    const {error}=await getSupabase().auth.signInWithPassword({
      email:String(d.get('email')||'').trim(),password:String(d.get('password')||'')
    });
    if(error){setStatus(status,'Connexion impossible. Vérifiez vos informations et la confirmation du courriel.','error');return}
    location.href=nextDestination();
  });
}
async function forgot(){
  const form=document.querySelector('[data-forgot-form]');if(!form)return;
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    const email=String(new FormData(form).get('email')||'').trim();
    const {error}=await getSupabase().auth.resetPasswordForEmail(email,{redirectTo:`${SINJIRA_CONFIG.siteUrl}/compte/reinitialiser-mot-de-passe.html`});
    setStatus(status,error?error.message:'Si le compte existe, un lien a été envoyé.',error?'error':'success');
  });
}
async function reset(){
  const form=document.querySelector('[data-reset-form]');if(!form)return;
  form.addEventListener('submit',async e=>{
    e.preventDefault();const d=new FormData(form),a=String(d.get('password')||''),b=String(d.get('password_confirm')||'');
    if(a.length<10||a!==b){setStatus(status,'Les mots de passe doivent correspondre et contenir au moins 10 caractères.','error');return}
    const {error}=await getSupabase().auth.updateUser({password:a});
    setStatus(status,error?error.message:'Mot de passe mis à jour.',error?'error':'success');
  });
}
async function dashboard(){
  const user=await requireUser(),s=getSupabase(),p=await profile(user),c=await consent(user);
  document.querySelectorAll('[data-player-name]').forEach(n=>n.textContent=p.pseudo||p.display_name||user.email||'Joueur SINJIRA');
  document.querySelectorAll('[data-player-email]').forEach(n=>n.textContent=user.email||'—');
  document.querySelectorAll('[data-dashboard-avatar]').forEach(n=>{n.src=avatarPublicUrl(p.avatar_path);n.alt=`Photo de profil de ${p.pseudo||p.display_name||'joueur'}`});
  const [rs,rp,rd,rr]=await Promise.all([
    s.from('game_sessions').select('id,title,status,updated_at,game_slug,party_code,projects(name,public_path)').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(6),
    s.from('projects').select('id,slug,name,status').order('sort_order'),
    s.from('documents').select('id').eq('status','approved'),
    s.from('access_requests').select('id').eq('user_id',user.id).eq('status','pending')
  ]);
  const sessions=rs.data||[],projects=rp.data||[],docs=rd.data||[],reqs=rr.data||[];
  const set=(sel,v)=>document.querySelector(sel)?.replaceChildren(document.createTextNode(String(v)));
  set('[data-stat-active]',sessions.filter(x=>x.status==='in_progress').length);
  set('[data-stat-finished]',sessions.filter(x=>x.status==='finished').length);
  set('[data-stat-projects]',projects.length);set('[data-stat-documents]',docs.length);set('[data-stat-requests]',reqs.length);
  const cs=document.querySelector('[data-contribution-status]');if(cs)cs.textContent=c.participate?'Programme Contributeur activé':'Programme Contributeur désactivé';
  const recent=document.querySelector('[data-recent-sessions]');
  if(recent)recent.innerHTML=sessions.length?sessions.map(x=>`<article class="account-session-row"><div><strong>${escapeHtml(x.title||x.projects?.name||'Partie SINJIRA')}</strong><span>${x.status==='finished'?'Terminée':'En cours'} · ${formatDate(x.updated_at)}</span></div><a class="btn btn-secondary btn-small" href="${sessionUrl(x)}">${x.status==='finished'?'Consulter':'Continuer'}</a></article>`).join(''):'<p>Aucune partie sauvegardée.</p>';
  const mini=document.querySelector('[data-dashboard-projects]');
  if(mini)mini.innerHTML=projects.slice(0,4).map(x=>`<a class="account-mini-project" href="/compte/projet.html?slug=${encodeURIComponent(x.slug)}"><span>${escapeHtml(x.name)}</span><small>${escapeHtml(projectStatusLabel(x.status))}</small></a>`).join('');
}
async function games(){
  const user=await requireUser(),s=getSupabase();
  const {data=[],error}=await s.from('game_sessions').select('*,projects(name,slug,public_path,play_path)').eq('user_id',user.id).order('updated_at',{ascending:false});
  if(error){setStatus(status,error.message,'error');return}
  const box=document.querySelector('[data-sessions-list]');
  box.innerHTML=data.length?data.map(x=>`<article class="account-game-card"><div class="account-game-card-top"><span class="status-badge">${x.status==='finished'?'Terminée':'En cours'}</span><span>${formatDate(x.updated_at)}</span></div><p class="game-kicker">${escapeHtml(x.projects?.name||x.game_slug)}</p><h2>${escapeHtml(x.title||'Partie SINJIRA')}</h2><p>${x.player_count?`${x.player_count} joueurs`:'Nombre de joueurs non indiqué'}${x.duration_minutes?` · ${x.duration_minutes} min`:''}</p><div class="hero-actions"><a class="btn btn-primary" href="${sessionUrl(x)}">${x.status==='finished'?'Voir':'Continuer'}</a>${x.projects?.slug?`<a class="btn btn-secondary" href="/compte/projet.html?slug=${encodeURIComponent(x.projects.slug)}">Projet</a>`:''}<button class="btn btn-secondary" type="button" data-export-session="${x.id}">Exporter</button></div></article>`).join(''):'<div class="notice"><strong>Aucune partie</strong><p>Choisissez un jeu dans votre bibliothèque.</p></div>';
  box.querySelectorAll('[data-export-session]').forEach(b=>b.addEventListener('click',async()=>{const id=b.dataset.exportSession;const session=data.find(x=>x.id===id);const [sheets,endgame]=await Promise.all([s.from('player_sheets').select('*').eq('session_id',id).eq('user_id',user.id),s.from('endgame_sheets').select('*').eq('session_id',id).eq('user_id',user.id)]);const payload={format:'SINJIRA_GAME_SAVE_V1',exported_at:new Date().toISOString(),session,player_sheets:sheets.data||[],endgame_sheets:endgame.data||[]};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`sinjira-partie-${session.party_code||id}.json`;a.click();URL.revokeObjectURL(url)}));
  const input=document.querySelector('[data-import-session]'),button=document.querySelector('[data-import-session-button]');button?.addEventListener('click',async()=>{const file=input?.files?.[0];if(!file)return setStatus(status,'Choisissez un fichier JSON de sauvegarde.','error');try{const payload=JSON.parse(await file.text());if(payload.format!=='SINJIRA_GAME_SAVE_V1'||!payload.session)throw new Error('Format de sauvegarde incompatible.');const src=payload.session;const clone={user_id:user.id,game_slug:src.game_slug,title:`${src.title||'Partie SINJIRA'} — importée`,status:'in_progress',player_count:src.player_count,human_player_count:src.human_player_count,effective_player_count:src.effective_player_count,play_mode:src.play_mode,duration_minutes:src.duration_minutes,party_code:`IMP-${Date.now().toString(36).toUpperCase()}`};const {data:newSession,error}=await s.from('game_sessions').insert(clone).select('id').single();if(error)throw error;for(const sh of payload.player_sheets||[]){await s.from('player_sheets').insert({session_id:newSession.id,user_id:user.id,sheet_key:sh.sheet_key,sheet_label:sh.sheet_label,fields:sh.fields||{}})}setStatus(status,'Sauvegarde importée comme nouvelle partie privée.','success');setTimeout(()=>location.reload(),800)}catch(e){setStatus(status,e.message||'Import impossible.','error')}});
}
async function profilePage(){
  const user=await requireUser(),p=await profile(user),form=document.querySelector('[data-profile-form]');if(!form)return;
  form.elements.pseudo.value=p.pseudo||'';form.elements.display_name.value=p.display_name||'';form.elements.email.value=user.email||'';
  const input=document.querySelector('[data-avatar-input]'),preview=document.querySelector('[data-profile-avatar]'),choose=document.querySelector('[data-avatar-choose]'),save=document.querySelector('[data-avatar-save]'),remove=document.querySelector('[data-avatar-remove]'),avatarState=document.querySelector('[data-avatar-state]');
  let selectedFile=null;
  const currentPath=()=>preview.dataset.avatarPath||'';
  const showStored=()=>{
    preview.src=avatarPublicUrl(p.avatar_path);preview.dataset.avatarPath=p.avatar_path||'';
    preview.alt=`Photo de profil de ${p.pseudo||p.display_name||'joueur'}`;
    remove.hidden=!p.avatar_path;save.hidden=true;selectedFile=null;
  };
  showStored();
  choose?.addEventListener('click',()=>input?.click());
  input?.addEventListener('change',async()=>{
    const file=input.files?.[0];if(!file)return;
    try{
      const blob=await prepareAvatarBlob(file);selectedFile=blob;
      preview.src=URL.createObjectURL(blob);save.hidden=false;avatarState.textContent='Aperçu prêt. Cliquez sur « Enregistrer la photo ».';
    }catch(e){setStatus(status,e.message||'Photo invalide.','error');input.value=''}
  });
  save?.addEventListener('click',async()=>{
    if(!selectedFile)return;
    save.disabled=true;choose.disabled=true;avatarState.textContent='Téléversement de la photo…';
    const path=`${user.id}/avatar.webp`;
    const {error:uploadError}=await getSupabase().storage.from(SINJIRA_CONFIG.avatarBucket||'sinjira-avatars').upload(path,selectedFile,{upsert:true,contentType:'image/webp',cacheControl:'3600'});
    if(uploadError){
      const msg=/row-level security|RLS/i.test(uploadError.message||'')
        ? 'La sécurité du stockage a refusé le téléversement. Rechargez la page pour renouveler votre session puis réessayez.'
        : (uploadError.message||'Téléversement impossible.');
      setStatus(status,msg,'error');save.disabled=false;choose.disabled=false;return
    }
    const {error:updateError}=await getSupabase().from('profiles').update({avatar_path:path}).eq('user_id',user.id);
    if(updateError){setStatus(status,updateError.message,'error');save.disabled=false;choose.disabled=false;return}
    p.avatar_path=path;preview.src=`${avatarPublicUrl(path)}?v=${Date.now()}`;preview.dataset.avatarPath=path;selectedFile=null;input.value='';save.hidden=true;save.disabled=false;choose.disabled=false;remove.hidden=false;avatarState.textContent='Photo de profil enregistrée.';setStatus(status,'Photo de profil mise à jour.','success');
  });
  remove?.addEventListener('click',async()=>{
    if(!p.avatar_path||!confirm('Retirer votre photo de profil?'))return;
    remove.disabled=true;
    const {error:storageError}=await getSupabase().storage.from(SINJIRA_CONFIG.avatarBucket||'sinjira-avatars').remove([p.avatar_path]);
    if(storageError){setStatus(status,storageError.message,'error');remove.disabled=false;return}
    const {error:updateError}=await getSupabase().from('profiles').update({avatar_path:null}).eq('user_id',user.id);
    if(updateError){setStatus(status,updateError.message,'error');remove.disabled=false;return}
    p.avatar_path=null;remove.disabled=false;showStored();avatarState.textContent='Photo retirée. Vous pouvez en ajouter une nouvelle.';setStatus(status,'Photo de profil retirée.','success');
  });
  form.addEventListener('submit',async e=>{e.preventDefault();const d=new FormData(form);const {error}=await getSupabase().from('profiles').update({pseudo:String(d.get('pseudo')||'').trim(),display_name:String(d.get('display_name')||'').trim()}).eq('user_id',user.id);setStatus(status,error?error.message:'Profil mis à jour.',error?'error':'success')});
}
async function contributions(){
  const user=await requireUser(),c=await consent(user),form=document.querySelector('[data-contribution-form]');if(!form)return;
  form.elements.participate.checked=!!c.participate;form.elements.share_free_text.checked=!!c.share_free_text;
  form.addEventListener('submit',async e=>{
    e.preventDefault();const participate=form.elements.participate.checked,free=participate&&form.elements.share_free_text.checked,s=getSupabase();
    const {error}=await s.from('research_consents').upsert({user_id:user.id,participate,share_free_text:free,consent_version:SINJIRA_CONFIG.contributionConsentVersion,consented_at:participate?new Date().toISOString():null,revoked_at:participate?null:new Date().toISOString()},{onConflict:'user_id'});
    if(error){setStatus(status,error.message,'error');return}
    if(!participate&&form.elements.remove_previous.checked){const r=await s.functions.invoke('revoke-my-contributions',{body:{all:true}});if(r.error){setStatus(status,'Consentement retiré, mais suppression des contributions précédentes impossible.','error');return}}
    setStatus(status,participate?'Programme Contributeur activé.':'Programme Contributeur désactivé.','success');
  });
}
async function settings(){
  const user=await requireUser(),s=getSupabase();
  document.querySelector('[data-export-data]')?.addEventListener('click',async()=>{
    const queries={
      profile:s.from('profiles').select('*').eq('user_id',user.id),
      private_profile:s.from('private_profiles').select('*').eq('user_id',user.id),
      relationships:s.from('family_relationships').select('*').eq('owner_user_id',user.id),
      privacy:s.from('privacy_settings').select('*').eq('user_id',user.id),
      notifications:s.from('notification_preferences').select('*').eq('user_id',user.id),
      questionnaire_draft:s.from('character_questionnaire_drafts').select('*').eq('user_id',user.id),
      sessions:s.from('game_sessions').select('*').eq('user_id',user.id),
      sheets:s.from('player_sheets').select('*').eq('user_id',user.id),
      feedback:s.from('session_feedback').select('*').eq('user_id',user.id),
      requests:s.from('access_requests').select('*').eq('user_id',user.id),
      access:s.from('project_access').select('*').eq('user_id',user.id),
      consent:s.from('research_consents').select('*').eq('user_id',user.id),
      market:s.from('market_listings').select('*').eq('seller_user_id',user.id),
      tokens:s.from('token_ledger').select('*').eq('user_id',user.id),
      parallel_responses:s.from('parallel_responses').select('*').eq('user_id',user.id),
      parallel_state:s.from('parallel_character_state').select('*').eq('user_id',user.id),
      entitlements:s.from('user_entitlements').select('*,products(slug,name)').eq('user_id',user.id)
    };
    const entries=await Promise.all(Object.entries(queries).map(async([k,q])=>{try{const r=await q;return [k,r.data||[]]}catch{return [k,[]]}}));
    const payload=Object.fromEntries(entries);payload.exported_at=new Date().toISOString();payload.format='SINJIRA_USER_EXPORT_V24';
    const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`sinjira-mes-donnees-${new Date().toISOString().slice(0,10)}.json`;link.click();URL.revokeObjectURL(url);
  });
  document.querySelector('[data-delete-account]')?.addEventListener('click',async()=>{
    if(prompt('Pour supprimer définitivement votre compte, écrivez SUPPRIMER.')!=='SUPPRIMER')return;
    const {error}=await s.functions.invoke('delete-player-account',{body:{confirm:'SUPPRIMER'}});
    if(error){setStatus(status,'Suppression impossible.','error');return}
    await s.auth.signOut();location.href='/compte/connexion.html?deleted=1';
  });
}
document.querySelectorAll('[data-logout]').forEach(b=>b.addEventListener('click',signOut));
backendNotice();
initAdminNavigation().catch(()=>{});
(async()=>{try{
  if(page==='signup')await signup();else if(page==='login')await login();else if(page==='forgot')await forgot();else if(page==='reset')await reset();
  else if(page==='dashboard')await dashboard();else if(page==='games')await games();else if(page==='profile')await profilePage();else if(page==='contributions')await contributions();else if(page==='settings')await settings();
}catch(e){if(e?.message!=='Connexion requise')setStatus(status,e?.message||'Une erreur est survenue.','error')}})();
