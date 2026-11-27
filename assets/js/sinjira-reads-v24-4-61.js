import {getSupabase,requireUser,escapeHtml,setStatus} from './sinjira-supabase.js';

const status=document.querySelector('[data-v18-status]');
const box=document.querySelector('[data-reader-library]');
const actionSelector='[data-v2461-add-read],[data-v2461-remove-read]';

function progressValue(value){
  if(value===null||value===undefined||value==='')return null;
  const n=Number(value);
  return Number.isFinite(n)?Math.max(0,Math.min(100,n)):null;
}
function progressBar(value){
  return value===null?'':`<progress max="100" value="${value}" aria-label="Progression de lecture">${value}%</progress>`;
}
function requireRows(result){
  if(result.error)throw result.error;
  if(!Array.isArray(result.data))throw new Error('Réponse de collection invalide');
  return result.data;
}
function actionLock(){
  let busy=false,stale=false;
  return {
    blocked:()=>busy||stale,
    start(){if(busy||stale)return false;busy=true;return true;},
    finish(refreshFailed=false){busy=false;stale=refreshFailed;}
  };
}
async function load(){
  if(document.body.dataset.v18Page!=='reads-v24-4-61'||!box)return;
  box.setAttribute('aria-busy','true');
  const user=await requireUser('/compte/connexion.html');
  const s=getSupabase();
  const readLibrary=()=>s.from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent,updated_at').eq('user_id',user.id);
  const [novelsResult,libraryResult]=await Promise.all([
    s.from('sinjira_novels').select('id,slug,title,subtitle,description,status,cover_url,public_path,demo_path,sort_order').in('status',['announced','published']).order('sort_order'),
    readLibrary()
  ]);
  const novels=requireRows(novelsResult);
  let library=requireRows(libraryResult);
  const lock=actionLock();

  function updateControls(){
    box.querySelectorAll(actionSelector).forEach(button=>{button.disabled=lock.blocked();});
  }
  function render(){
    const map=new Map(library.map(item=>[item.novel_id,item]));
    box.innerHTML=novels.map(novel=>{
      const saved=map.get(novel.id),progress=progressValue(saved?.progress_percent);
      const page=Number(saved?.last_page),id=escapeHtml(novel.id);
      const isFirst=novel.slug==='la-cendre-du-jugement';
      return `<article class="reader-book-card" data-v2461-novel="${id}">
        <span class="eyebrow">${escapeHtml(novel.status==='published'?'Roman disponible':'Roman annoncé')}</span>
        <h2>${escapeHtml(novel.title)}</h2>
        ${novel.subtitle?`<p><strong>${escapeHtml(novel.subtitle)}</strong></p>`:''}
        <p>${escapeHtml(novel.description||'')}</p>
        ${saved?progressBar(progress):''}
        <p>${saved?`Dans votre bibliothèque · ${progress===null?'progression indisponible':`progression ${progress}%`}${Number.isSafeInteger(page)&&page>0?` · page ${page}`:''}`:'Pas encore ajouté à votre bibliothèque.'}</p>
        <div class="hero-actions">
          ${isFirst?'<a class="btn btn-primary" href="/projets/sinjira/romans/lire-demo.html">Voir le statut de la démo</a>':novel.demo_path?`<a class="btn btn-primary" href="${escapeHtml(novel.demo_path)}">${saved&&progress>0?'Continuer ma lecture':'Lire la démo'}</a>`:''}${isFirst?'<a class="btn btn-secondary" href="/compte/liseuse.html?edition=integrale">Vérifier mon accès à l’intégrale</a>':''}
          <a class="btn btn-secondary" href="${escapeHtml(novel.public_path||'/projets/sinjira/romans/')}">Page du roman</a>
          ${saved?`<button class="btn btn-secondary" type="button" data-v2461-remove-read="${id}">Retirer de ma bibliothèque</button>`:`<button class="btn btn-secondary" type="button" data-v2461-add-read="${id}">Ajouter à ma bibliothèque</button>`}
        </div>
      </article>`;
    }).join('')||'<div class="notice"><strong>Aucun roman disponible pour le moment.</strong></div>';
    updateControls();
  }
  async function mutate(button,remove){
    if(lock.blocked())return;
    const novelId=remove?button.dataset.v2461RemoveRead:button.dataset.v2461AddRead;
    if(!novels.some(n=>n.id===novelId))return;
    if(remove&&!confirm('Retirer ce roman de votre bibliothèque? Votre progression enregistrée dans cette bibliothèque sera supprimée.'))return;
    if(!lock.start())return;
    const restoreFocus=document.activeElement===button;
    updateControls();box.setAttribute('aria-busy','true');
    let written=false,refreshFailed=false;
    try{
      setStatus(status,remove?'Retrait en cours…':'Ajout en cours…','info');
      const payload={user_id:user.id,novel_id:novelId,last_page:1,progress_percent:0,last_opened_at:new Date().toISOString(),updated_at:new Date().toISOString()};
      const result=remove
        ?await s.from('sinjira_reader_library').delete().eq('user_id',user.id).eq('novel_id',novelId)
        :await s.from('sinjira_reader_library').upsert(payload,{onConflict:'user_id,novel_id',ignoreDuplicates:true});
      if(result.error)throw result.error;
      written=true;
      library=requireRows(await readLibrary());
      render();
      setStatus(status,remove?'Roman retiré de votre bibliothèque.':'Roman ajouté à votre bibliothèque SINJIRA™.','success');
    }catch(error){
      refreshFailed=true;
      setStatus(status,written?'Modification confirmée, mais collection non actualisée. Rechargez la page avant une nouvelle opération.':'Modification non confirmée. Rechargez la page pour vérifier votre collection avant de réessayer.','error');
    }finally{
      lock.finish(refreshFailed);updateControls();box.setAttribute('aria-busy','false');
      if(restoreFocus&&(document.activeElement===document.body||document.activeElement===button)){
        const replacement=Array.from(box.querySelectorAll(actionSelector)).find(b=>(b.dataset.v2461AddRead||b.dataset.v2461RemoveRead)===novelId);
        if(replacement&&!replacement.disabled)replacement.focus();
        else if(status){status.setAttribute('tabindex','-1');status.focus();}
      }
    }
  }
  box.addEventListener('click',event=>{
    const button=event.target.closest(actionSelector);
    if(button&&box.contains(button))void mutate(button,button.hasAttribute('data-v2461-remove-read'));
  });
  render();box.setAttribute('aria-busy','false');
}
load().catch(error=>{
  if(box){box.setAttribute('aria-busy','false');box.textContent='Collection indisponible. Rechargez la page pour réessayer.';}
  if(error?.message!=='Connexion requise')setStatus(status,'Impossible de charger vos lectures pour le moment.','error');
});
