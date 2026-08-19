import {getSupabase,escapeHtml} from './sinjira-supabase.js';

const s=getSupabase();
const candidatesBox=document.querySelector('[data-dating-candidates]');
let observer=null;

const clampScore=value=>Math.max(0,Math.min(100,Math.round(Number(value)||0)));

function detailMarkup(data){
  const dimensions=Array.isArray(data?.dimensions)?data.dimensions:[];
  const rows=dimensions.map(item=>{
    const score=clampScore(item.score);const weight=Math.max(0,Number(item.weight)||0);
    return `<div class="dating-dimension"><span>${escapeHtml(item.label||item.key||'Dimension')}</span><div class="dating-dimension-track" aria-hidden="true"><span class="dating-dimension-fill" style="--dating-score:${score}%"></span></div><strong>${score}%</strong><span class="sr-only">Poids ${weight}%</span></div>`;
  }).join('');
  const registry=data?.registry_context?.used
    ? `<span class="dating-registry-chip">Registre volontaire · ${clampScore(data.registry_context.score)}% · poids ${Number(data.registry_context.weight)||5}%</span>`
    : '<span class="dating-registry-chip">Registre non utilisé pour cette proposition</span>';
  return `<div class="dating-detail-head"><div><strong>Pourquoi cette proposition?</strong><p>Les pourcentages sont des proximités de critères déclarés, pas une prédiction de réussite amoureuse.</p></div><strong>${clampScore(data?.overall)}% global</strong></div><div class="dating-dimensions">${rows}</div>${registry}<p class="dating-detail-foot">Calcul local explicable. Aucune réponse brute du Registre ni préférence brute de l’autre personne n’est affichée. Aucune IA distante n’a été utilisée.</p>`;
}

async function toggleDetail(card,button){
  let detail=card.querySelector('[data-dating-detail]');
  if(!detail){
    detail=document.createElement('div');detail.className='dating-detail';detail.dataset.datingDetail='';detail.hidden=true;
    card.querySelector('.hero-actions')?.insertAdjacentElement('beforebegin',detail);
  }
  if(detail.dataset.loaded==='true'){
    detail.hidden=!detail.hidden;
    button.textContent=detail.hidden?'Comprendre cette compatibilité':'Masquer le détail';
    return;
  }
  const profileId=card.dataset.datingCandidate;if(!profileId)return;
  button.disabled=true;const initial=button.textContent;button.textContent='Analyse…';
  try{
    const {data,error}=await s.rpc('dating_compatibility_detail',{p_candidate_profile_id:profileId});
    if(error)throw error;
    detail.innerHTML=detailMarkup(data||{});detail.dataset.loaded='true';detail.hidden=false;button.textContent='Masquer le détail';
  }catch(error){
    detail.innerHTML='<p>Le détail de cette compatibilité n’est pas disponible pour le moment. La proposition anonyme reste utilisable.</p>';detail.hidden=false;button.textContent=initial;
    console.warn('SINJIRA dating compatibility detail unavailable',error?.message||error);
  }finally{button.disabled=false;}
}

function decorateCandidates(){
  if(!candidatesBox)return;
  observer?.disconnect();
  try{
    candidatesBox.querySelectorAll('[data-dating-candidate]').forEach(card=>{
      const actions=card.querySelector('.hero-actions');if(!actions||card.querySelector('[data-dating-detail-toggle]'))return;
      const button=document.createElement('button');button.type='button';button.className='btn btn-secondary btn-small';button.dataset.datingDetailToggle='';button.textContent='Comprendre cette compatibilité';
      button.addEventListener('click',()=>toggleDetail(card,button));actions.append(button);
    });
  }finally{observe();}
}

function observe(){
  if(!candidatesBox)return;
  if(!observer)observer=new MutationObserver(decorateCandidates);
  observer.observe(candidatesBox,{childList:true,subtree:true});
}

observe();decorateCandidates();
