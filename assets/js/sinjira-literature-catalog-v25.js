import {getSupabase,getCurrentUser,escapeHtml} from './sinjira-supabase.js';

const PRIVATE_READER='/projets/sinjira/romans/lire-integral.html';

function statusLabel(status){
  return status==='draft'?'Brouillon créateur':status==='published'?'Publié':status==='announced'?'Annoncé':status||'—';
}

async function init(){
  const box=document.querySelector('[data-literature-catalog]');
  if(!box)return;
  const s=getSupabase();
  const user=await getCurrentUser();
  let isOwner=false,ownerResolved=true,catalogAccessMode='member',catalogAccessResolved=true;
  if(user){
    const [ownerResult,catalogAccessResult]=await Promise.all([
      s.rpc('is_sinjira_owner',{p_user_id:user.id}),
      s.rpc('sinjira_my_catalog_access_mode')
    ]);
    ownerResolved=!ownerResult.error;
    isOwner=ownerResolved&&ownerResult.data===true;
    catalogAccessResolved=!catalogAccessResult.error;
    catalogAccessMode=catalogAccessResolved?String(catalogAccessResult.data||'member'):'member';
  }
  const familyCatalog=catalogAccessMode==='family';
  const result=user?await s.rpc('sinjira_my_novel_catalog'):await s.from('sinjira_novels').select('id,slug,title,subtitle,description,status,cover_url,public_path,demo_path,sort_order').order('sort_order');
  const {data,error}=result;
  if(error){
    box.innerHTML='<div class="notice"><strong>Catalogue temporairement indisponible.</strong><p>Les fiches détaillées restent accessibles plus bas.</p></div>';
    return;
  }
  const novels=Array.isArray(data)?data:[];
  box.innerHTML=novels.map(novel=>{
    const integral=Boolean(novel.full_access);
    const access=(!ownerResolved||!catalogAccessResolved)&&user
      ?(integral?'Accès intégral confirmé':'Rôle du compte non confirmé')
      :isOwner
        ?(integral?'Créateur · intégrale privée':'Créateur · catalogue complet')
        :familyCatalog
          ?(integral?'Famille créateur · intégrale privée':'Famille créateur · catalogue complet')
          :integral?'Acheté / droit numérique':novel.status==='published'?'Public':'Annoncé';
    const cover=novel.cover_url||'/assets/media/sinjira-litterature.webp';
    const actions=[
      novel.public_path?`<a class="btn btn-secondary" href="${escapeHtml(novel.public_path)}">Voir la fiche</a>`:'',
      novel.demo_path?`<a class="btn btn-secondary" href="${escapeHtml(novel.demo_path)}">Lire la démo</a>`:'',
      integral?`<a class="btn btn-primary" href="${PRIVATE_READER}?novel=${encodeURIComponent(novel.slug)}">Lire l’intégrale</a>`:''
    ].join('');
    const privateState=isOwner&&!integral?'<p><small>Manuscrit intégral privé non chargé dans le coffre SINJIRA™.</small></p>':'';
    return `<article class="literature-catalog-card"><img src="${escapeHtml(cover)}" alt=""><div><div class="library-project-meta"><span class="status-badge">${escapeHtml(statusLabel(novel.status))}</span><span class="role-chip">${escapeHtml(access)}</span></div><h3>${escapeHtml(novel.title)}</h3>${novel.subtitle?`<p><strong>${escapeHtml(novel.subtitle)}</strong></p>`:''}<p>${escapeHtml(novel.description||'')}</p>${privateState}<div class="hero-actions">${actions}</div></div></article>`;
  }).join('')||'<div class="notice"><strong>Aucun roman disponible pour le moment.</strong></div>';

  const note=document.querySelector('[data-literature-account-note]');
  if(note){
    note.textContent=user&&(!ownerResolved||!catalogAccessResolved)
      ?'Rôle du compte non confirmé. Le catalogue affiché vient du serveur et aucun accès supplémentaire n’est supposé.'
      :isOwner
        ?'Mode créateur : les romans en préparation sont visibles ici, sans être rendus publics aux autres comptes.'
        :familyCatalog
          ?'Mode famille créateur : toutes les fiches SINJIRA sont visibles; les accès de lecture restent vérifiés côté serveur et selon l’âge.'
          :user
            ?'Catalogue adapté à votre compte : les accès intégraux apparaissent seulement lorsqu’un droit numérique existe.'
            :'Les romans annoncés ou publiés sont visibles ici. Connectez-vous pour voir vos droits de lecture.';
  }
}

init().catch(()=>{
  const box=document.querySelector('[data-literature-catalog]');
  if(box)box.innerHTML='<div class="notice"><strong>Catalogue temporairement indisponible.</strong><p>Les accès n’ont pas pu être vérifiés; aucun droit supplémentaire n’est supposé.</p></div>';
  const note=document.querySelector('[data-literature-account-note]');
  if(note)note.textContent='Impossible de vérifier le catalogue pour le moment.';
});
