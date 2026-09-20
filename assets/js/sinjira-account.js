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
  const {data,error}=await getSupabase().from('profiles').select('*').eq('user_id',user.id).maybeSingle();
  if(error)throw error;
  return data||{};
}
async function consent(user){
  const {data,error}=await getSupabase().from('research_consents').select('*').eq('user_id',user.id).maybeSingle();
  if(error)throw error;
  return data||{participate:false,share_free_text:false};
}
function setFormEnabled(form,enabled){
  for(const field of form?.elements||[])field.disabled=!enabled;
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

const CHILD_11_12_ALLOWED_ROUTES=new Set([
  'index.html',
  'bibliotheque.html',
  'documents.html',
  'projet.html',
  'blocages.html',
  'communaute-junior.html',
  'confidentialite-joueur.html',
  'histoire-de-vie.html',
  'moderation.html',
  'mon-personnage.html',
  'mes-personnages.html',
  'notifications.html',
  'parametres.html',
  'profil.html',
  'registre-personnel.html',
  'regles-communaute-junior.html',
  'relations.html',
  'securite.html',
  'vie-privee.html',
  'connexion.html',
  'inscription.html',
  'mot-de-passe-oublie.html',
  'reinitialiser-mot-de-passe.html',
  'mfa.html'
]);

const CHILD_11_12_ROUTE_REDIRECTS=new Map([
  ['communaute.html','/compte/communaute-junior.html'],
  ['regles-communaute.html','/compte/regles-communaute-junior.html']
]);

function accountRouteLeaf(pathname=location.pathname){
  if(/\/compte\/?$/.test(pathname))return 'index.html';
  return pathname.split('/').filter(Boolean).pop()||'index.html';
}

function postNativeChildAccess(state){
  try{
    const bridge=window.ReactNativeWebView;
    if(!bridge||typeof bridge.postMessage!=='function')return;
    const normalized=state==='child'?'child':state==='nonchild'?'nonchild':'unknown';
    bridge.postMessage(JSON.stringify({type:'sinjira:child-access',state:normalized}));
  }catch{}
}

async function initAgeAccessNavigation(){
  if(!isSinjiraBackendConfigured()) return;
  const {data:{user},error:userError}=await getSupabase().auth.getUser();
  if(userError||!user) return;
  const {data:capabilities,error}=await getSupabase().rpc('sinjira_my_account_capabilities');
  if(error||!capabilities){postNativeChildAccess('unknown');return}
  const accountMode=String(capabilities.account_mode||'restricted');
  const childAccount=accountMode==='child'&&capabilities.child_11_12===true;
  postNativeChildAccess(childAccount?'child':accountMode==='standard'?'nonchild':'unknown');
  if(!childAccount) return;

  const currentLeaf=accountRouteLeaf();
  const directRedirect=CHILD_11_12_ROUTE_REDIRECTS.get(currentLeaf);
  if(directRedirect){
    location.replace(directRedirect);
    return;
  }
  if(location.pathname.startsWith('/compte/')&&!CHILD_11_12_ALLOWED_ROUTES.has(currentLeaf)){
    const next=new URL('/compte/communaute-junior.html',location.origin);
    next.searchParams.set('from','restricted');
    next.searchParams.set('module',currentLeaf);
    location.replace(next.pathname+next.search);
    return;
  }

  document.querySelectorAll('.account-nav a').forEach(link=>{
    const href=(link.getAttribute('href')||'').split('?')[0].split('#')[0];
    const leaf=accountRouteLeaf(href);
    const redirect=CHILD_11_12_ROUTE_REDIRECTS.get(leaf);
    if(redirect){
      link.href=redirect;
      link.textContent=leaf==='regles-communaute.html'?'Règles Junior':'Communauté Junior';
      return;
    }
    if(!CHILD_11_12_ALLOWED_ROUTES.has(leaf))link.hidden=true;
  });

  document.querySelectorAll('[data-contribution-status]').forEach(node=>{
    node.textContent='Programme Contributeur indisponible pour les comptes de 11–12 ans.';
  });
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
    if(a.length<12||a!==b){setStatus(status,'Les mots de passe doivent correspondre et contenir au moins 12 caractères.','error');return}
    const {error}=await getSupabase().auth.updateUser({password:a});
    setStatus(status,error?error.message:'Mot de passe mis à jour.',error?'error':'success');
  });
}
async function dashboard(){
  const user=await requireUser(),s=getSupabase(),p=await profile(user),c=await consent(user);
  document.querySelectorAll('[data-player-name]').forEach(n=>n.textContent=p.pseudo||p.display_name||user.email||'Joueur SINJIRA');
  document.querySelectorAll('[data-player-email]').forEach(n=>n.textContent=user.email||'—');
  document.querySelectorAll('[data-dashboard-avatar]').forEach(n=>{n.src=avatarPublicUrl(p.avatar_path);n.alt=`Photo de profil de ${p.pseudo||p.display_name||'joueur'}`});
  const [rs,rr]=await Promise.all([
    s.from('game_sessions').select('id,title,status,updated_at,game_slug,party_code,projects(name,public_path)').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(6),
    s.from('access_requests').select('id').eq('user_id',user.id).eq('status','pending')
  ]);
  const sessionsResolved=!rs.error,requestsResolved=!rr.error,sessions=rs.data||[],reqs=rr.data||[];
  const set=(sel,v)=>document.querySelector(sel)?.replaceChildren(document.createTextNode(String(v)));
  set('[data-stat-active]',sessionsResolved?sessions.filter(x=>x.status==='in_progress').length:'—');
  set('[data-stat-finished]',sessionsResolved?sessions.filter(x=>x.status==='finished').length:'—');
  set('[data-stat-requests]',requestsResolved?reqs.length:'—');
  const cs=document.querySelector('[data-contribution-status]');if(cs)cs.textContent=c.participate?'Programme Contributeur activé':'Programme Contributeur désactivé';
  const recent=document.querySelector('[data-recent-sessions]');
  if(recent)recent.innerHTML=!sessionsResolved
    ?'<p>Parties récentes temporairement indisponibles. Aucune absence de sauvegarde n’est déduite.</p>'
    :sessions.length?sessions.map(x=>`<article class="account-session-row"><div><strong>${escapeHtml(x.title||x.projects?.name||'Partie SINJIRA')}</strong><span>${x.status==='finished'?'Terminée':'En cours'} · ${formatDate(x.updated_at)}</span></div><a class="btn btn-secondary btn-small" href="${sessionUrl(x)}">${x.status==='finished'?'Consulter':'Continuer'}</a></article>`).join(''):'<p>Aucune partie sauvegardée.</p>';
  if(!sessionsResolved||!requestsResolved)setStatus(status,'Certaines informations du tableau de bord n’ont pas pu être vérifiées. Aucun état vide n’est supposé.','error');

}
async function games(){
  const user=await requireUser(),s=getSupabase();
  const {data=[],error}=await s.from('game_sessions').select('*,projects(name,slug,public_path,play_path)').eq('user_id',user.id).order('updated_at',{ascending:false});
  if(error){setStatus(status,error.message,'error');return}
  const box=document.querySelector('[data-sessions-list]');
  box.innerHTML=data.length?data.map(x=>`<article class="account-game-card"><div class="account-game-card-top"><span class="status-badge">${x.status==='finished'?'Terminée':'En cours'}</span><span>${formatDate(x.updated_at)}</span></div><p class="game-kicker">${escapeHtml(x.projects?.name||x.game_slug)}</p><h2>${escapeHtml(x.title||'Partie SINJIRA')}</h2><p>${x.player_count?`${x.player_count} joueurs`:'Nombre de joueurs non indiqué'}${x.duration_minutes?` · ${x.duration_minutes} min`:''}</p><div class="hero-actions"><a class="btn btn-primary" href="${sessionUrl(x)}">${x.status==='finished'?'Voir':'Continuer'}</a>${x.projects?.slug?`<a class="btn btn-secondary" href="/compte/projet.html?slug=${encodeURIComponent(x.projects.slug)}">Projet</a>`:''}<button class="btn btn-secondary" type="button" data-export-session="${x.id}">Exporter</button></div></article>`).join(''):'<div class="notice"><strong>Aucune partie</strong><p>Choisissez un jeu dans votre bibliothèque.</p></div>';
  box.querySelectorAll('[data-export-session]').forEach(b=>b.addEventListener('click',async()=>{const id=b.dataset.exportSession;const session=data.find(x=>x.id===id);const [sheets,endgame]=await Promise.all([s.from('player_sheets').select('*').eq('session_id',id).eq('user_id',user.id),s.from('endgame_sheets').select('*').eq('session_id',id).eq('user_id',user.id)]);if(sheets.error||endgame.error){setStatus(status,'Export interrompu : les fiches de cette partie n’ont pas toutes pu être vérifiées. Aucun fichier incomplet n’a été généré.','error');return}const payload={format:'SINJIRA_GAME_SAVE_V1',exported_at:new Date().toISOString(),session,player_sheets:sheets.data||[],endgame_sheets:endgame.data||[]};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`sinjira-partie-${session.party_code||id}.json`;a.click();URL.revokeObjectURL(url)}));
  const input=document.querySelector('[data-import-session]'),button=document.querySelector('[data-import-session-button]');button?.addEventListener('click',async()=>{const file=input?.files?.[0];if(!file)return setStatus(status,'Choisissez un fichier JSON de sauvegarde.','error');try{const payload=JSON.parse(await file.text());if(payload.format!=='SINJIRA_GAME_SAVE_V1'||!payload.session)throw new Error('Format de sauvegarde incompatible.');const src=payload.session;const clone={user_id:user.id,game_slug:src.game_slug,title:`${src.title||'Partie SINJIRA'} — importée`,status:'in_progress',player_count:src.player_count,human_player_count:src.human_player_count,effective_player_count:src.effective_player_count,play_mode:src.play_mode,duration_minutes:src.duration_minutes,party_code:`IMP-${Date.now().toString(36).toUpperCase()}`};const {data:newSession,error}=await s.from('game_sessions').insert(clone).select('id').single();if(error)throw error;const importedSheets=(payload.player_sheets||[]).map(sh=>({session_id:newSession.id,user_id:user.id,sheet_key:sh.sheet_key,sheet_label:sh.sheet_label,fields:sh.fields||{}}));if(importedSheets.length){const {error:sheetError}=await s.from('player_sheets').insert(importedSheets);if(sheetError){setStatus(status,'La partie a été créée, mais ses fiches n’ont pas pu être importées. Aucun succès complet n’est annoncé.','error');return}}setStatus(status,'Sauvegarde importée comme nouvelle partie privée.','success');setTimeout(()=>location.reload(),800)}catch(e){setStatus(status,e.message||'Import impossible.','error')}});
}
async function profilePage(){
  const form=document.querySelector('[data-profile-form]');if(!form)return;
  setFormEnabled(form,false);
  const user=await requireUser();
  let p;
  try{p=await profile(user)}catch(error){setStatus(status,'Impossible de charger le profil. Le formulaire reste verrouillé pour éviter d’écraser des données non chargées.','error');return}
  form.elements.pseudo.value=p.pseudo||'';form.elements.display_name.value=p.display_name||'';form.elements.email.value=user.email||'';
  setFormEnabled(form,true);
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
  form.addEventListener('submit',async e=>{e.preventDefault();const d=new FormData(form),s=getSupabase(),pseudo=String(d.get('pseudo')||'').trim(),displayName=String(d.get('display_name')||'').trim(),email=String(d.get('email')||'').trim().toLowerCase();if(!pseudo||!displayName||!email){setStatus(status,'Complétez le pseudonyme, le nom affiché et le courriel.','error');return}const {error:profileError}=await s.from('profiles').update({pseudo,display_name:displayName}).eq('user_id',user.id);if(profileError){setStatus(status,profileError.message||'Impossible de mettre le profil à jour.','error');return}if(email!==String(user.email||'').toLowerCase()){const {error:emailError}=await s.auth.updateUser({email},{emailRedirectTo:`${location.origin}/compte/profil.html`});if(emailError){setStatus(status,emailError.message||'Le profil a été enregistré, mais le changement de courriel n’a pas pu être lancé.','error');return}setStatus(status,'Profil enregistré. Confirmez le changement de courriel avec les messages de sécurité envoyés par SINJIRA™.','success');return}setStatus(status,'Profil mis à jour.','success')});
}
async function contributions(){
  const form=document.querySelector('[data-contribution-form]');if(!form)return;
  setFormEnabled(form,false);
  const user=await requireUser();
  let c;
  try{c=await consent(user)}catch(error){setStatus(status,'Impossible de vérifier vos choix de contribution. Le formulaire reste verrouillé et aucun consentement n’est supposé.','error');return}
  form.elements.participate.checked=!!c.participate;form.elements.share_free_text.checked=!!c.share_free_text;
  setFormEnabled(form,true);
  form.addEventListener('submit',async e=>{
    e.preventDefault();const participate=form.elements.participate.checked,free=participate&&form.elements.share_free_text.checked,s=getSupabase();
    const {error}=await s.from('research_consents').upsert({user_id:user.id,participate,share_free_text:free,consent_version:SINJIRA_CONFIG.contributionConsentVersion,consented_at:participate?new Date().toISOString():null,revoked_at:participate?null:new Date().toISOString()},{onConflict:'user_id'});
    if(error){setStatus(status,error.message,'error');return}
    if(!participate&&form.elements.remove_previous.checked){const r=await s.functions.invoke('revoke-my-contributions',{body:{all:true}});if(r.error){setStatus(status,'Consentement retiré, mais suppression des contributions précédentes impossible.','error');return}}
    setStatus(status,participate?'Programme Contributeur activé.':'Programme Contributeur désactivé.','success');
  });
}
async function settings(){
  await requireUser();
}

function refreshAccountNavGroups(){
  document.querySelectorAll('.account-nav-group').forEach(group=>{
    const visible=[...group.querySelectorAll('a')].some(link=>!link.hidden);
    group.hidden=!visible;
  });
}

function normalizeAccountHeaderNavigation(){
  document.querySelectorAll('.account-page .site-header .main-nav').forEach(nav=>{
    if(nav.dataset.accountHeaderNormalized==='true')return;
    nav.dataset.accountHeaderNormalized='true';
    nav.setAttribute('aria-label','Navigation principale');
    const universe=document.createElement('a');
    universe.href='/projets/sinjira/';
    universe.textContent='Univers SINJIRA™';
    nav.replaceChildren(universe);
  });
}

function enhanceAccountNavigation(){
  document.querySelectorAll('.account-nav').forEach(nav=>{
    if(nav.dataset.grouped==='true')return;
    nav.dataset.grouped='true';
    nav.classList.add('account-nav--grouped');
    const nodes=[...nav.children];
    const leaf=node=>String(node?.getAttribute?.('href')||'').split('?')[0].split('#')[0].split('/').pop();
    const take=leaves=>nodes.filter(node=>node.tagName==='A'&&leaves.includes(leaf(node)));
    const used=new Set();
    const appendGroup=(label,leaves)=>{
      const links=take(leaves);
      if(!links.length)return;
      links.forEach(link=>used.add(link));
      const details=document.createElement('details');details.className='account-nav-group';
      const summary=document.createElement('summary');summary.textContent=label;
      if(links.some(link=>link.getAttribute('aria-current')==='page')){
        details.classList.add('is-current');
        details.open=true;
      }
      const panel=document.createElement('div');panel.className='account-nav-panel';
      links.forEach(link=>panel.append(link));details.append(summary,panel);nav.append(details);
    };
    const home=nodes.find(node=>node.tagName==='A'&&leaf(node)==='index.html');
    const logout=nodes.find(node=>node.matches?.('[data-logout]'));
    const admin=nodes.find(node=>node.matches?.('[data-admin-nav]'));
    nav.replaceChildren();
    if(home){used.add(home);home.textContent='Mon espace';home.classList.add('account-nav-home');nav.append(home);}
    appendGroup('Bibliothèque',['bibliotheque.html','projet.html','mes-lectures.html','mes-commentaires.html','licences.html','mes-achats.html','marche.html','jetons.html','documents.html','playtests.html','contributions.html']);
    appendGroup('Univers',['mon-personnage.html','mes-personnages.html','monde-parallele.html','mes-parties.html','registre-personnel.html','histoire-de-vie.html','signaler-deces.html']);
    appendGroup('Communauté',['communaute.html','communaute-junior.html','regles-communaute.html','regles-communaute-junior.html','moderation.html','relations.html','rencontres.html','reseau-personnage.html','messages.html','messages-reels.html','messages-personnage.html','notifications.html']);
    appendGroup('Compte',['profil.html','securite.html','parametres.html','confidentialite-joueur.html','vie-privee.html','blocages.html','emploi.html','mon-ia.html']);
    const leftovers=nodes.filter(node=>node.tagName==='A'&&!used.has(node)&&node!==admin);
    if(leftovers.length){
      const details=document.createElement('details');details.className='account-nav-group';
      const summary=document.createElement('summary');summary.textContent='Plus';
      const panel=document.createElement('div');panel.className='account-nav-panel';leftovers.forEach(link=>panel.append(link));details.append(summary,panel);nav.append(details);
    }
    if(admin)nav.append(admin);
    if(logout)nav.append(logout);
    nav.addEventListener('toggle',event=>{if(event.target.open)nav.querySelectorAll('details[open]').forEach(other=>{if(other!==event.target)other.removeAttribute('open')})},true);
  });
  refreshAccountNavGroups();
}
document.querySelectorAll('[data-logout]').forEach(b=>b.addEventListener('click',async()=>{postNativeChildAccess('unknown');await signOut()}));
backendNotice();
normalizeAccountHeaderNavigation();
enhanceAccountNavigation();
initAdminNavigation().catch(()=>{});
initAgeAccessNavigation().then(refreshAccountNavGroups).catch(()=>{});
(async()=>{try{
  if(page==='signup')await signup();else if(page==='login')await login();else if(page==='forgot')await forgot();else if(page==='reset')await reset();
  else if(page==='dashboard')await dashboard();else if(page==='games')await games();else if(page==='profile')await profilePage();else if(page==='contributions')await contributions();else if(page==='settings')await settings();
}catch(e){if(e?.message!=='Connexion requise')setStatus(status,e?.message||'Une erreur est survenue.','error')}})();
