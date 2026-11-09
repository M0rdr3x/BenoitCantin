import {requireUser,getSupabase,escapeHtml,setStatus} from './sinjira-supabase.js';

function safeLibraryHref(value){
  // Des attributs HTML échappés n'empêchent pas les protocoles javascript:.
  if(typeof value!=='string'||value.length>2048||!value.startsWith('/')||
     value.startsWith('//')||/[\u0000-\u0020\u007f\\]/.test(value))return '';
  try{
    const target=new URL(value,location.origin);
    const rawPath=value.split(/[?#]/,1)[0];
    // Refuser /../ et ses variantes percent-encodées, normalisées par URL.
    if(target.origin!==location.origin||target.pathname!==rawPath||
       target.username||target.password)return '';
    return target.pathname+target.search+target.hash;
  }catch{return ''}
}

/* L'affichage des catégories ne confère aucun droit d'accès :
   les autorisations restent contrôlées par Supabase et les Edge Functions. */
async function init(){
  const user=await requireUser('/compte/connexion.html');
  const container=document.querySelector('[data-library-account-games]');
  if(!container)return;
  const status=document.querySelector('[data-library-status]');
  const s=getSupabase();
  const {data,error}=await s.from('projects')
    .select('id,name,description,slug,public_path,play_path,status,allow_tester_requests')
    .in('slug',['fracture-du-reseau-mere','reseau-mere-resistance'])
    .order('sort_order');
  if(error){
    setStatus(status,'Les projets associés à votre compte ne peuvent pas être chargés. Les liens publics ci-dessus restent disponibles.','error');
    return;
  }
  const [accessResult,pendingResult,ownerResult,adminResult]=await Promise.all([
    s.from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id),
    s.from('access_requests').select('project_id,status').eq('user_id',user.id).eq('status','pending'),
    s.rpc('is_sinjira_owner',{p_user_id:user.id}),
    s.rpc('is_sinjira_admin',{p_user_id:user.id}),
  ]);
  const elevated=ownerResult.data===true||adminResult.data===true;
  const access=new Map((accessResult.data||[]).map(x=>[x.project_id,x]));
  const pending=new Set((pendingResult.data||[]).map(x=>x.project_id));
  const projects=Array.isArray(data)?data:[];
  container.innerHTML=projects.map(project=>{
    const path=safeLibraryHref(project.public_path)||'/projets/sinjira/jeux/';
    // L'ancien moteur Fracture ne respecte pas encore l'édition Déduction
    // simplifiée : ne jamais présenter son ancien accès comme un jeu jouable.
    const play=project.slug==='fracture-du-reseau-mere'?null:safeLibraryHref(project.play_path);
    const grant=access.get(project.id);
    const active=grant&&(!grant.expires_at||Date.parse(grant.expires_at)>Date.now());
    const isTester=elevated||(active&&grant.access_level==='tester');
    const requestAllowed=project.allow_tester_requests&&!isTester;
    const requested=pending.has(project.id);
    return '<article class="account-card">'+
      '<span class="eyebrow">Projet SINJIRA™</span><h3>'+escapeHtml(project.name)+'</h3>'+
      '<p>'+escapeHtml(project.description||'')+'</p>'+
      '<div class="hero-actions"><a class="btn btn-secondary" href="'+escapeHtml(path)+'">Voir le projet</a>'+
      (play?'<a class="btn btn-primary" href="'+escapeHtml(play)+'">Jouer</a>':'')+
      '<a class="btn btn-secondary" href="/compte/projet.html?slug='+encodeURIComponent(project.slug)+'">Mon espace de projet</a>'+
      (requestAllowed?'<button class="btn btn-secondary" type="button" data-request-tester="'+escapeHtml(project.id)+'"'+(requested?' disabled':'')+'>'+(requested?'Demande testeur en attente':'Demander un accès testeur')+'</button>':'')+
      '</div></article>';
  }).join('');
  container.querySelectorAll('[data-request-tester]').forEach(button=>button.addEventListener('click',async()=>{
    const message=prompt('Votre message de candidature (facultatif)')||'';
    button.disabled=true;
    const {error:requestError}=await s.from('access_requests').insert({
      user_id:user.id,project_id:button.dataset.requestTester,requested_level:'tester',
      message:message.slice(0,1500),
    });
    if(requestError){button.disabled=false;setStatus(status,'Impossible de transmettre votre demande de testeur.','error');return;}
    button.textContent='Demande testeur en attente';
    setStatus(status,'Demande de testeur transmise.','success');
  }));
}
init().catch(error=>{
  if(error?.message!=='Connexion requise'){
    const node=document.querySelector('[data-library-status]');
    if(node)setStatus(node,'Impossible de vérifier votre session pour cette bibliothèque.','error');
  }
});
