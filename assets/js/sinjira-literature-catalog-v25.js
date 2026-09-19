import {getSupabase,getCurrentUser,escapeHtml} from './sinjira-supabase.js';

const BOOK_ONE_PRODUCT='sinjira-livre-01-la-cendre-du-jugement';
const PRIVATE_READER='/projets/sinjira/romans/lire-integral.html';

function statusLabel(status){
  return status==='draft'?'Brouillon créateur':status==='published'?'Publié':status==='announced'?'Annoncé':status||'—';
}

async function init(){
  const box=document.querySelector('[data-literature-catalog]');
  if(!box)return;
  const s=getSupabase();
  const user=await getCurrentUser();
  let isOwner=false,entitlements=[];
  if(user){
    const [ownerResult,rightsResult]=await Promise.all([
      s.rpc('is_sinjira_owner',{p_user_id:user.id}),
      s.from('user_entitlements').select('product_id,products(slug,name,product_type,active)').eq('user_id',user.id)
    ]);
    isOwner=!ownerResult.error&&ownerResult.data===true;
    entitlements=Array.isArray(rightsResult.data)?rightsResult.data:[];
  }
  const {data,error}=await s.from('sinjira_novels').select('id,slug,title,subtitle,description,status,cover_url,public_path,demo_path,sort_order').order('sort_order');
  if(error){
    box.innerHTML='<div class="notice"><strong>Catalogue temporairement indisponible.</strong><p>Les fiches détaillées restent accessibles plus bas.</p></div>';
    return;
  }
  const novels=Array.isArray(data)?data:[];
  const hasBookOne=entitlements.some(row=>row.products?.slug===BOOK_ONE_PRODUCT);
  box.innerHTML=novels.map(novel=>{
    const bookOne=novel.slug==='la-cendre-du-jugement';
    const integral=bookOne&&(isOwner||hasBookOne);
    const access=isOwner?'Créateur':integral?'Acheté / droit numérique':novel.status==='published'?'Public':'Annoncé';
    const cover=novel.cover_url||'/assets/media/sinjira-litterature.webp';
    const actions=[
      novel.public_path?`<a class="btn btn-secondary" href="${escapeHtml(novel.public_path)}">Voir la fiche</a>`:'',
      novel.demo_path?`<a class="btn btn-secondary" href="${escapeHtml(novel.demo_path)}">Lire la démo</a>`:'',
      integral?`<a class="btn btn-primary" href="${PRIVATE_READER}">Lire l’intégrale</a>`:''
    ].join('');
    return `<article class="literature-catalog-card"><img src="${escapeHtml(cover)}" alt=""><div><div class="library-project-meta"><span class="status-badge">${escapeHtml(statusLabel(novel.status))}</span><span class="role-chip">${escapeHtml(access)}</span></div><h3>${escapeHtml(novel.title)}</h3>${novel.subtitle?`<p><strong>${escapeHtml(novel.subtitle)}</strong></p>`:''}<p>${escapeHtml(novel.description||'')}</p><div class="hero-actions">${actions}</div></div></article>`;
  }).join('')||'<div class="notice"><strong>Aucun roman disponible pour le moment.</strong></div>';

  const note=document.querySelector('[data-literature-account-note]');
  if(note){
    note.textContent=isOwner
      ?'Mode créateur : les romans en préparation sont visibles ici, sans être rendus publics aux autres comptes.'
      :user
        ?'Catalogue adapté à votre compte : les accès intégraux apparaissent seulement lorsqu’un droit numérique existe.'
        :'Les romans annoncés ou publiés sont visibles ici. Connectez-vous pour voir vos droits de lecture.';
  }
}

init().catch(()=>{});
