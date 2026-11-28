import {requireUser,getSupabase,escapeHtml,setStatus} from './sinjira-supabase.js';

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
    container.textContent='Impossible de charger les projets. Actualisez cette page pour réessayer.';
    container.setAttribute('aria-busy','false');
    setStatus(status,'Les projets associés à votre compte ne peuvent pas être chargés. Les liens publics ci-dessus restent disponibles.','error');
    return;
  }
  const safeLink=value=>{
    const raw=String(value||'');
    if(!raw.startsWith('/')||raw.startsWith('//')||raw.includes('\\'))return null;
    try{const url=new URL(raw,location.origin);return url.origin===location.origin?url.pathname:null}
    catch{return null}
  };
  const [accessResult,pendingResult,ownerResult,adminResult]=await Promise.all([
    s.from('project_access').select('project_id,access_level,expires_at').eq('user_id',user.id),
    s.from('access_requests').select('project_id,status').eq('user_id',user.id).eq('status','pending'),
    s.rpc('is_sinjira_owner',{p_user_id:user.id}),
    s.rpc('is_sinjira_admin',{p_user_id:user.id}),
  ]);
  const accessKnown=[accessResult,pendingResult,ownerResult,adminResult].every(result=>!result.error);
  if(!accessKnown)setStatus(status,'Vos accès ne peuvent pas être vérifiés. Actualisez la page avant de demander un accès testeur.','error');
  const elevated=ownerResult.data===true||adminResult.data===true;
  const access=new Map((accessResult.data||[]).map(x=>[x.project_id,x]));
  const pending=new Set((pendingResult.data||[]).map(x=>x.project_id));
  const projects=Array.isArray(data)?data:[];
  container.innerHTML=projects.map(project=>{
    const path=safeLink(project.public_path)||'/projets/sinjira/jeux/';
    // L'ancien moteur Fracture ne respecte pas encore l'édition Déduction
    // simplifiée : ne jamais présenter son ancien accès comme un jeu jouable.
    const play=project.slug==='fracture-du-reseau-mere'?null:safeLink(project.play_path);
    const grant=access.get(project.id);
    const active=grant&&(!grant.expires_at||Date.parse(grant.expires_at)>Date.now());
    const isTester=elevated||(active&&grant.access_level==='tester');
    const requestAllowed=accessKnown&&project.allow_tester_requests&&!isTester;
    const requested=pending.has(project.id);
    return '<article class="account-card">'+
      '<span class="eyebrow">Projet SINJIRA™</span><h3>'+escapeHtml(project.name)+'</h3>'+
      '<p>'+escapeHtml(project.description||'')+'</p>'+
      '<div class="hero-actions"><a class="btn btn-secondary" href="'+path+'">Voir le projet</a>'+
      (play?'<a class="btn btn-primary" href="'+play+'">Jouer</a>':'')+
      '<a class="btn btn-secondary" href="/compte/projet.html?slug='+encodeURIComponent(project.slug)+'">Mon espace de projet</a>'+
      (requestAllowed?'<button class="btn btn-secondary" type="button" data-request-tester="'+escapeHtml(project.id)+'"'+(requested?' disabled':'')+'>'+(requested?'Demande testeur en attente':'Demander un accès testeur')+'</button>':'')+
      '</div>'+
      (requestAllowed&&!requested?'<form class="account-form library-tester-form" data-tester-form hidden><label>Message de candidature (facultatif)<textarea name="message" maxlength="1500" rows="4"></textarea></label><div class="hero-actions"><button class="btn btn-primary" type="submit">Envoyer la demande</button><button class="btn btn-secondary" type="button" data-tester-cancel>Annuler</button></div><p data-tester-feedback role="status" aria-atomic="true"></p></form>':'')+
      '</article>';
  }).join('')||'<p>Aucun projet de jeu disponible pour le moment.</p>';
  container.setAttribute('aria-busy','false');
  container.querySelectorAll('[data-request-tester]').forEach(button=>{
    const form=button.closest('article')?.querySelector('[data-tester-form]');
    if(!form)return;
    const message=form.elements.message;
    const submit=form.querySelector('[type="submit"]');
    const cancel=form.querySelector('[data-tester-cancel]');
    const feedback=form.querySelector('[data-tester-feedback]');
    let sending=false,finished=false;
    button.setAttribute('aria-expanded','false');
    button.addEventListener('click',()=>{
      if(sending||finished)return;
      form.hidden=!form.hidden;
      button.setAttribute('aria-expanded',String(!form.hidden));
      if(!form.hidden)message.focus();
    });
    cancel.addEventListener('click',()=>{
      if(sending||finished)return;
      form.reset();feedback.textContent='';form.hidden=true;
      button.setAttribute('aria-expanded','false');button.focus();
    });
    form.addEventListener('submit',async event=>{
      event.preventDefault();
      if(sending||finished)return;
      sending=true;button.disabled=true;submit.disabled=true;cancel.disabled=true;message.readOnly=true;
      form.setAttribute('aria-busy','true');
      feedback.textContent='Envoi en cours…';
      try{
        const {error:requestError}=await s.from('access_requests').insert({
          user_id:user.id,project_id:button.dataset.requestTester,requested_level:'tester',
          message:message.value.slice(0,1500),
        });
        if(requestError)throw requestError;
        finished=true;
        button.textContent='Demande testeur en attente';
        form.hidden=true;button.setAttribute('aria-expanded','false');
        setStatus(status,'Demande de testeur transmise.','success');
        status?.focus();
      }catch(_){
        // Le serveur peut avoir reçu l'écriture malgré une réponse perdue.
        finished=true;
        feedback.textContent='Envoi non confirmé. Actualisez la page pour vérifier si la demande a été reçue avant de réessayer.';
        setStatus(status,'Impossible de confirmer la demande de testeur.','error');
        status?.focus();
      }finally{
        sending=false;form.setAttribute('aria-busy','false');
        button.disabled=finished;submit.disabled=finished;cancel.disabled=finished;message.readOnly=finished;
      }
    });
  });
}
init().catch(error=>{
  const container=document.querySelector('[data-library-account-games]');
  if(container){container.setAttribute('aria-busy','false');container.textContent='Les projets privés sont indisponibles. Les liens publics restent accessibles.';}
  if(error?.message!=='Connexion requise'){
    const node=document.querySelector('[data-library-status]');
    if(node)setStatus(node,'Impossible de vérifier votre session pour cette bibliothèque.','error');
  }
});
