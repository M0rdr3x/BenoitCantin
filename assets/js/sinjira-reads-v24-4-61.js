import {getSupabase,requireUser,escapeHtml,setStatus} from './sinjira-supabase.js';

const status=document.querySelector('[data-v18-status]');
const rows=value=>Array.isArray(value)?value:[];

function normalizeProgress(value){
  if(value===null||value===undefined||value===''||!Number.isFinite(Number(value)))return null;
  return Math.round(Math.max(0,Math.min(100,Number(value)))*10)/10;
}
function progressBar(value){
  if(value===null)return '<p>Progression non disponible.</p>';
  return `<progress class="reading-progress" max="100" value="${value}" aria-label="Progression de lecture">${value}%</progress>`;
}
function confirmRemoval(button,novel){
  const dialog=document.querySelector('[data-reading-remove-dialog]');
  if(!dialog||typeof dialog.showModal!=='function')return Promise.resolve(window.confirm('Retirer « '+novel.title+' » ? Votre progression enregistrée dans cette bibliothèque sera supprimée.'));
  if(dialog.open)return Promise.resolve(false);
  dialog.querySelector('[data-reading-remove-name]').textContent=novel.title||'Ce roman';
  dialog.returnValue='';
  return new Promise(resolve=>{
    const closed=()=>{
      const accepted=dialog.returnValue==='remove';dialog.returnValue='';
      if(button.isConnected)button.focus({preventScroll:true});
      resolve(accepted);
    };
    dialog.addEventListener('close',closed,{once:true});
    try{dialog.showModal()}catch{dialog.removeEventListener('close',closed);resolve(false)}
  });
}

async function load(){
  if(document.body.dataset.v18Page!=='reads-v24-4-61')return;
  const user=await requireUser('/compte/connexion.html');
  const s=getSupabase();
  const [novelsResult,libraryResult]=await Promise.all([
    s.from('sinjira_novels').select('id,slug,title,subtitle,description,status,cover_url,public_path,demo_path,sort_order').in('status',['announced','published']).order('sort_order'),
    s.from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent,updated_at').eq('user_id',user.id)
  ]);
  if(novelsResult.error)throw novelsResult.error;
  if(libraryResult.error)throw libraryResult.error;

  const novels=rows(novelsResult.data);
  let library=rows(libraryResult.data);
  let busy=false,uncertain=false;
  async function refresh(){
    const {data,error}=await s.from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent,updated_at').eq('user_id',user.id);
    if(error)throw error;
    library=rows(data);
  }
  const box=document.querySelector('[data-reader-library]');
  if(!box)return;

  const render=()=>{
    const map=new Map(library.map(item=>[item.novel_id,item]));
    box.innerHTML=novels.map(novel=>{
      const saved=map.get(novel.id);
      const progress=normalizeProgress(saved?.progress_percent);
      const novelId=escapeHtml(novel.id);
      return `<article class="reader-book-card" data-v2461-novel="${novelId}">
        <span class="eyebrow">${escapeHtml(novel.status==='published'?'Roman disponible':'Roman annoncé')}</span>
        <h2>${escapeHtml(novel.title)}</h2>
        ${novel.subtitle?`<p><strong>${escapeHtml(novel.subtitle)}</strong></p>`:''}
        <p>${escapeHtml(novel.description||'')}</p>
        ${saved?progressBar(progress):''}
        <p>${saved?`Dans votre bibliothèque${progress===null?'':` · progression ${progress}%`}${Number.isFinite(Number(saved.last_page))&&Number(saved.last_page)>0?` · page ${Number(saved.last_page)}`:''}`:'Pas encore ajouté à votre bibliothèque.'}</p>
        <div class="hero-actions">
          ${novel.demo_path?`<a class="btn btn-primary" href="${novel.slug==='la-cendre-du-jugement'?'/compte/liseuse.html?edition=demo':escapeHtml(novel.demo_path)}">${saved&&progress>0?'Continuer ma lecture':'Lire la démo'}</a>`:''}${novel.slug==='la-cendre-du-jugement'?'<a class="btn btn-secondary" href="/compte/liseuse.html?edition=integrale">Lire l’intégrale (accès privé)</a>':''}
          <a class="btn btn-secondary" href="${escapeHtml(novel.public_path||'/projets/sinjira/romans/')}">Page du roman</a>
          ${saved?`<button class="btn btn-secondary" type="button" data-v2461-remove-read="${novelId}">Retirer de ma bibliothèque</button>`:`<button class="btn btn-secondary" type="button" data-v2461-add-read="${novelId}">Ajouter à ma bibliothèque</button>`}
        </div>
      </article>`;
    }).join('')||'<div class="notice"><strong>Aucun roman disponible pour le moment.</strong></div>';

    for(const button of box.querySelectorAll('[data-v2461-add-read],[data-v2461-remove-read]')){
      button.disabled=busy||uncertain;
      button.addEventListener('click',async()=>{
        if(busy||uncertain)return;
        const remove=button.hasAttribute('data-v2461-remove-read');
        const novelId=remove?button.dataset.v2461RemoveRead:button.dataset.v2461AddRead;
        const novel=novels.find(item=>String(item.id)===novelId);
        if(!novel)return;
        if(remove&&!await confirmRemoval(button,novel))return;
        if(busy||uncertain)return;
        busy=true;
        box.setAttribute('aria-busy','true');
        box.querySelectorAll('button[data-v2461-add-read],button[data-v2461-remove-read]').forEach(control=>control.disabled=true);
        setStatus(status,remove?'Retrait en cours…':'Ajout en cours…','info');
        try{
          let result;
          if(remove){
            result=await s.from('sinjira_reader_library').delete().eq('user_id',user.id).eq('novel_id',novelId);
          }else{
            const payload={user_id:user.id,novel_id:novelId,last_page:1,progress_percent:0,last_opened_at:new Date().toISOString(),updated_at:new Date().toISOString()};
            // Une ligne créée sur un autre appareil ne doit jamais être écrasée.
            result=await s.from('sinjira_reader_library').upsert(payload,{onConflict:'user_id,novel_id',ignoreDuplicates:true});
          }
          if(result.error)throw result.error;
          await refresh();
          setStatus(status,remove?'Roman retiré de votre bibliothèque.':'Roman présent dans votre bibliothèque SINJIRA™.','success');
        }catch{
          uncertain=true;
          setStatus(status,'Modification ou actualisation non confirmée. Rechargez la page pour vérifier vos lectures avant de réessayer.','error');
        }finally{
          busy=false;
          box.setAttribute('aria-busy','false');
          render();
          const card=[...box.querySelectorAll('[data-v2461-novel]')].find(item=>item.dataset.v2461Novel===novelId);
          const next=card?.querySelector('button:not(:disabled)')||card?.querySelector('a');
          next?.focus({preventScroll:true});
        }
      });
    }
  };

  render();
  box.setAttribute('aria-busy','false');
  setStatus(status,'Vos lectures sont à jour.','info');
}

load().catch(error=>{
  document.querySelector('[data-reader-library]')?.setAttribute('aria-busy','false');
  if(error?.message!=='Connexion requise')setStatus(status,'Impossible de charger vos lectures pour le moment. Rechargez la page pour réessayer.','error');
});
