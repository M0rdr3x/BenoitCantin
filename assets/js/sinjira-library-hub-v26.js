import {requireUser,getSupabase,escapeHtml,setStatus} from './sinjira-supabase.js';

/* L'affichage des catégories ne confère aucun droit d'accès :
   les autorisations restent contrôlées par Supabase et les Edge Functions. */
async function init(){
  const user=await requireUser('/compte/connexion.html');
  const container=document.querySelector('[data-library-account-games]');
  if(!container)return;
  const status=document.querySelector('[data-library-status]');
  const {data,error}=await getSupabase().from('projects')
    .select('name,description,slug,public_path,play_path,status')
    .in('slug',['fracture-du-reseau-mere','reseau-mere-resistance'])
    .order('sort_order');
  if(error){
    setStatus(status,'Les projets associés à votre compte ne peuvent pas être chargés. Les liens publics ci-dessus restent disponibles.','error');
    return;
  }
  const safeLink=value=>{
    const raw=String(value||'');
    if(!raw.startsWith('/')||raw.startsWith('//')||raw.includes('\\'))return null;
    try{const url=new URL(raw,location.origin);return url.origin===location.origin?url.pathname:null}
    catch{return null}
  };
  const projects=Array.isArray(data)?data:[];
  container.innerHTML=projects.map(project=>{
    const path=safeLink(project.public_path)||'/projets/sinjira/jeux/';
    const play=safeLink(project.play_path);
    return '<article class="account-card">'+
      '<span class="eyebrow">Projet SINJIRA™</span><h3>'+escapeHtml(project.name)+'</h3>'+
      '<p>'+escapeHtml(project.description||'')+'</p>'+
      '<div class="hero-actions"><a class="btn btn-secondary" href="'+path+'">Voir le projet</a>'+
      (play?'<a class="btn btn-primary" href="'+play+'">Jouer</a>':'')+'</div></article>';
  }).join('');
}
init().catch(error=>{
  if(error?.message!=='Connexion requise'){
    const node=document.querySelector('[data-library-status]');
    if(node)setStatus(node,'Impossible de vérifier votre session pour cette bibliothèque.','error');
  }
});
