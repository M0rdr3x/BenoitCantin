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
  if(s.game_slug==='fracture-du-reseau-mere') return `/projets/sinjira/jeux/fracture-du-reseau-mere/fiche-web.html?session=${encodeURIComponent(s.id)}`;
  return s.projects?.public_path||'/compte/bibliotheque.html';
}

async function signup(){
  const form=document.querySelector('[data-signup-form]'); if(!form)return;
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!isSinjiraBackendConfigured()){setStatus(status,'Supabase doit d’abord être configuré.','error');return}
    const d=new FormData(form), pw=String(d.get('password')||''), pw2=String(d.get('password_confirm')||'');
    if(pw.length<10){setStatus(status,'Utilisez un mot de passe d’au moins 10 caractères.','error');return}
    if(pw!==pw2){setStatus(status,'Les mots de passe ne correspondent pas.','error');return}
    const contributor=d.get('initial_contributor_opt_in')==='yes';
    const {data,error}=await getSupabase().auth.signUp({
      email:String(d.get('email')||'').trim(),password:pw,
      options:{
        emailRedirectTo:`${SINJIRA_CONFIG.siteUrl}/compte/index.html`,
        data:{
          pseudo:String(d.get('pseudo')||'').trim(),
          display_name:String(d.get('display_name')||'').trim(),
          initial_contributor_opt_in:contributor,
          initial_share_free_text:contributor&&d.get('share_free_text')==='yes'
        }
      }
    });
    if(error){setStatus(status,error.message,'error');return}
    if(data.session){location.href=nextDestination();return}
    setStatus(status,'Compte créé. Vérifiez votre courriel pour confirmer votre adresse.','success');form.reset();
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
  const [rs,rp,rd,rr]=await Promise.all([
    s.from('game_sessions').select('id,title,status,updated_at,game_slug,projects(name,public_path)').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(6),
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
  box.innerHTML=data.length?data.map(x=>`<article class="account-game-card"><div class="account-game-card-top"><span class="status-badge">${x.status==='finished'?'Terminée':'En cours'}</span><span>${formatDate(x.updated_at)}</span></div><p class="game-kicker">${escapeHtml(x.projects?.name||x.game_slug)}</p><h2>${escapeHtml(x.title||'Partie SINJIRA')}</h2><p>${x.player_count?`${x.player_count} joueurs`:'Nombre de joueurs non indiqué'}${x.duration_minutes?` · ${x.duration_minutes} min`:''}</p><div class="hero-actions"><a class="btn btn-primary" href="${sessionUrl(x)}">${x.status==='finished'?'Voir':'Continuer'}</a>${x.projects?.slug?`<a class="btn btn-secondary" href="/compte/projet.html?slug=${encodeURIComponent(x.projects.slug)}">Projet</a>`:''}</div></article>`).join(''):'<div class="notice"><strong>Aucune partie</strong><p>Choisissez un jeu dans votre bibliothèque.</p></div>';
}
async function profilePage(){
  const user=await requireUser(),p=await profile(user),form=document.querySelector('[data-profile-form]');if(!form)return;
  form.elements.pseudo.value=p.pseudo||'';form.elements.display_name.value=p.display_name||'';form.elements.email.value=user.email||'';
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
    const [a,b,c,d,e,f,g]=await Promise.all([
      s.from('profiles').select('*').eq('user_id',user.id),s.from('game_sessions').select('*').eq('user_id',user.id),
      s.from('player_sheets').select('*').eq('user_id',user.id),s.from('session_feedback').select('*').eq('user_id',user.id),
      s.from('access_requests').select('*').eq('user_id',user.id),s.from('project_access').select('*').eq('user_id',user.id),
      s.from('research_consents').select('*').eq('user_id',user.id)
    ]);
    const blob=new Blob([JSON.stringify({profile:a.data,sessions:b.data,sheets:c.data,feedback:d.data,requests:e.data,access:f.data,consent:g.data},null,2)],{type:'application/json'});
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
(async()=>{try{
  if(page==='signup')await signup();else if(page==='login')await login();else if(page==='forgot')await forgot();else if(page==='reset')await reset();
  else if(page==='dashboard')await dashboard();else if(page==='games')await games();else if(page==='profile')await profilePage();else if(page==='contributions')await contributions();else if(page==='settings')await settings();
}catch(e){if(e?.message!=='Connexion requise')setStatus(status,e?.message||'Une erreur est survenue.','error')}})();
