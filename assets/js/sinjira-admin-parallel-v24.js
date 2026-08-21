import {getSupabase,escapeHtml,setStatus} from './sinjira-supabase.js';

const VERSION='24.4.92';
let cycles=[];
let selectedCycleId=null;

function dateTime(value){
  if(!value)return '—';
  try{return new Date(value).toLocaleString('fr-CA',{dateStyle:'medium',timeStyle:'short'})}catch{return String(value)}
}
function inputDateTime(value){
  if(!value)return '';
  const d=new Date(value);if(Number.isNaN(d.getTime()))return '';
  const pad=n=>String(n).padStart(2,'0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function monthValue(value){return value?String(value).slice(0,7):''}
function statusLabel(value){return ({draft:'Brouillon',open:'Ouvert',closed:'Fermé',published:'Publié',archived:'Archivé'})[value]||value||'—'}
function audienceLabel(value){return ({all:'Tous',adult:'Adultes',youth:'Jeunesse'})[value]||value||'—'}
function responseModeLabel(value){return ({solo:'Solo',group:'Groupe',solo_or_group:'Solo ou groupe'})[value]||value||'—'}

async function rpc(name,args={}){
  const {data,error}=await getSupabase().rpc(name,args);
  if(error)throw error;
  if(data&&data.ok===false)throw new Error(data.code||'ADMIN_PARALLEL_ERROR');
  return data||{};
}

function inject(){
  if(document.querySelector('[data-admin-panel="parallel-world"]'))return;
  const tabs=document.querySelector('.admin-console-tabs');
  const main=document.querySelector('main.admin-console-layout');
  if(!tabs||!main)return;

  const button=document.createElement('button');
  button.type='button';button.dataset.adminTab='parallel-world';button.textContent='Monde parallèle';
  tabs.append(button);

  const panel=document.createElement('section');
  panel.className='admin-panel';panel.dataset.adminPanel='parallel-world';panel.hidden=true;
  panel.innerHTML=`
    <article class="account-card">
      <span class="eyebrow">Monde parallèle · administration humaine V${VERSION}</span>
      <h2>Cycles et Chroniques</h2>
      <p>Créer les cycles mensuels, lire les réponses volontaires et publier les Chroniques. Les RPC exigent le rôle administrateur et une session MFA AAL2.</p>
      <div class="account-status" data-parallel-admin-status hidden></div>
      <div class="account-layout" style="margin-top:18px">
        <section>
          <h3>Créer / modifier un cycle brouillon</h3>
          <form class="account-form" data-parallel-cycle-form>
            <input type="hidden" name="cycle_id">
            <div class="field"><label>Mois du cycle</label><input type="month" name="cycle_month" required></div>
            <div class="field"><label>Titre</label><input name="title" maxlength="160" required></div>
            <div class="field"><label>Question mensuelle</label><textarea name="monthly_question" minlength="10" maxlength="1200" required></textarea></div>
            <div class="field-row">
              <div class="field"><label>Mode de réponse</label><select name="response_mode"><option value="solo">Solo</option><option value="group">Groupe</option><option value="solo_or_group">Solo ou groupe</option></select></div>
              <div class="field"><label>Audience</label><select name="audience"><option value="all">Tous</option><option value="adult">Adultes</option><option value="youth">Jeunesse</option></select></div>
            </div>
            <div class="field-row">
              <div class="field"><label>Ouverture</label><input type="datetime-local" name="opens_at" required></div>
              <div class="field"><label>Fermeture</label><input type="datetime-local" name="closes_at" required></div>
            </div>
            <div class="hero-actions"><button class="btn btn-primary" type="submit">Enregistrer le brouillon</button><button class="btn btn-secondary" type="button" data-parallel-cycle-reset>Nouveau cycle</button></div>
          </form>
        </section>
        <aside><h3>Cycles</h3><div class="admin-management-list" data-parallel-cycle-list><p>Chargement…</p></div></aside>
      </div>
    </article>
    <article class="account-card" style="margin-top:18px" data-parallel-cycle-detail hidden>
      <span class="eyebrow">Cycle sélectionné</span><h2 data-parallel-detail-title>Cycle</h2>
      <div class="hero-actions" data-parallel-status-actions></div>
      <div class="account-layout" style="margin-top:18px">
        <section><h3>Réponses reçues</h3><p class="v24-field-help">L’administration voit le nom de l’identité parallèle et le texte envoyé, pas l’identifiant technique privé du compte.</p><div class="admin-management-list" data-parallel-response-list></div></section>
        <aside><h3>Chroniques du cycle</h3><div class="admin-management-list" data-parallel-story-list></div></aside>
      </div>
      <hr style="margin:24px 0">
      <h3>Publier une Chronique</h3>
      <form class="account-form" data-parallel-story-form>
        <div class="field-row"><div class="field"><label>Type</label><select name="story_kind"><option value="collective">Collective</option><option value="individual">Individuelle</option></select></div><div class="field"><label>Audience collective</label><select name="audience"><option value="all">Tous</option><option value="adult">Adultes</option><option value="youth">Jeunesse</option></select></div></div>
        <div class="field" data-parallel-response-picker hidden><label>Réponse source</label><select name="response_id"></select><small class="v24-field-help">Une Chronique individuelle n’est lisible que par le membre concerné selon les politiques RLS existantes.</small></div>
        <div class="field"><label>Titre</label><input name="title" minlength="3" maxlength="200" required></div>
        <div class="field"><label>Texte</label><textarea name="content" minlength="20" maxlength="20000" rows="10" required></textarea></div>
        <button class="btn btn-primary" type="submit">Publier après validation humaine</button>
      </form>
    </article>`;
  main.append(panel);

  button.addEventListener('click',()=>{
    document.querySelectorAll('[data-admin-tab]').forEach(x=>x.removeAttribute('aria-current'));
    button.setAttribute('aria-current','page');
    document.querySelectorAll('[data-admin-panel]').forEach(p=>p.hidden=p.dataset.adminPanel!=='parallel-world');
    loadCycles().catch(showError);
  });

  bind(panel);
}

function showError(error){
  console.error('[SINJIRA admin parallel]',error);
  const box=document.querySelector('[data-parallel-admin-status]');
  if(box)setStatus(box,error?.message||'Administration du Monde parallèle indisponible.','error');
}
function showSuccess(message){const box=document.querySelector('[data-parallel-admin-status]');if(box)setStatus(box,message,'success')}

function bind(panel){
  const cycleForm=panel.querySelector('[data-parallel-cycle-form]');
  cycleForm.addEventListener('submit',async e=>{
    e.preventDefault();
    const f=cycleForm.elements;
    try{
      await rpc('admin_parallel_save_cycle',{
        p_cycle_id:f.cycle_id.value||null,
        p_cycle_month:`${f.cycle_month.value}-01`,
        p_title:f.title.value.trim(),p_monthly_question:f.monthly_question.value.trim(),
        p_response_mode:f.response_mode.value,p_audience:f.audience.value,
        p_opens_at:new Date(f.opens_at.value).toISOString(),p_closes_at:new Date(f.closes_at.value).toISOString()
      });
      showSuccess('Cycle brouillon enregistré.');resetCycleForm();await loadCycles();
    }catch(error){showError(error)}
  });
  panel.querySelector('[data-parallel-cycle-reset]').addEventListener('click',resetCycleForm);

  const storyForm=panel.querySelector('[data-parallel-story-form]');
  const kind=storyForm.elements.story_kind,picker=panel.querySelector('[data-parallel-response-picker]');
  const syncKind=()=>{picker.hidden=kind.value!=='individual';storyForm.elements.response_id.required=kind.value==='individual'};
  kind.addEventListener('change',syncKind);syncKind();
  storyForm.addEventListener('submit',async e=>{
    e.preventDefault();if(!selectedCycleId)return;
    try{
      await rpc('admin_parallel_publish_story',{
        p_cycle_id:selectedCycleId,p_story_kind:storyForm.elements.story_kind.value,
        p_response_id:storyForm.elements.story_kind.value==='individual'?(storyForm.elements.response_id.value||null):null,
        p_title:storyForm.elements.title.value.trim(),p_content:storyForm.elements.content.value.trim(),p_audience:storyForm.elements.audience.value
      });
      storyForm.elements.title.value='';storyForm.elements.content.value='';showSuccess('Chronique publiée.');await loadCycleDetail(selectedCycleId);await loadCycles();
    }catch(error){showError(error)}
  });
}

function resetCycleForm(){
  const form=document.querySelector('[data-parallel-cycle-form]');if(!form)return;
  form.reset();form.elements.cycle_id.value='';
}
function fillCycleForm(cycle){
  const f=document.querySelector('[data-parallel-cycle-form]')?.elements;if(!f||cycle.status!=='draft')return;
  f.cycle_id.value=cycle.id;f.cycle_month.value=monthValue(cycle.cycle_month);f.title.value=cycle.title||'';f.monthly_question.value=cycle.monthly_question||'';
  f.response_mode.value=cycle.response_mode||'solo';f.audience.value=cycle.audience||'all';f.opens_at.value=inputDateTime(cycle.opens_at);f.closes_at.value=inputDateTime(cycle.closes_at);
  document.querySelector('[data-parallel-cycle-form]')?.scrollIntoView({behavior:'smooth',block:'start'});
}

function transitionButtons(cycle){
  const next={draft:[['open','Ouvrir le cycle'],['archived','Archiver']],open:[['closed','Fermer le cycle']],closed:[['published','Publier le cycle'],['archived','Archiver']],published:[['archived','Archiver']],archived:[]}[cycle.status]||[];
  return next.map(([status,label])=>`<button class="btn ${status==='open'||status==='published'?'btn-primary':'btn-secondary'} btn-small" data-cycle-state="${status}">${label}</button>`).join('');
}

async function loadCycles(){
  const data=await rpc('admin_parallel_list_cycles');cycles=Array.isArray(data.cycles)?data.cycles:[];
  const box=document.querySelector('[data-parallel-cycle-list]');if(!box)return;
  box.innerHTML=cycles.map(c=>`<article class="admin-management-row" data-cycle="${escapeHtml(c.id)}"><div><strong>${escapeHtml(c.title||'Cycle')}</strong><span>${escapeHtml(String(c.cycle_month||'').slice(0,7))} · ${escapeHtml(statusLabel(c.status))} · ${escapeHtml(audienceLabel(c.audience))}</span><p>${escapeHtml(c.monthly_question||'')}</p><small>${Number(c.response_count||0)} réponse(s) · ${Number(c.published_story_count||0)} Chronique(s) publiée(s)</small></div><div class="admin-row-actions"><button class="btn btn-secondary btn-small" data-cycle-open>Ouvrir</button>${c.status==='draft'?'<button class="btn btn-secondary btn-small" data-cycle-edit>Modifier</button>':''}</div></article>`).join('')||'<p>Aucun cycle. Créez le premier brouillon.</p>';
  box.querySelectorAll('[data-cycle]').forEach(card=>{
    const cycle=cycles.find(c=>c.id===card.dataset.cycle);if(!cycle)return;
    card.querySelector('[data-cycle-open]').onclick=()=>loadCycleDetail(cycle.id).catch(showError);
    card.querySelector('[data-cycle-edit]')?.addEventListener('click',()=>fillCycleForm(cycle));
  });
  if(selectedCycleId&&cycles.some(c=>c.id===selectedCycleId))await loadCycleDetail(selectedCycleId);
}

async function loadCycleDetail(id){
  selectedCycleId=id;
  const cycle=cycles.find(c=>c.id===id);if(!cycle)return;
  const detail=document.querySelector('[data-parallel-cycle-detail]');detail.hidden=false;
  detail.querySelector('[data-parallel-detail-title]').textContent=`${cycle.title} — ${statusLabel(cycle.status)}`;
  const actions=detail.querySelector('[data-parallel-status-actions]');
  actions.innerHTML=transitionButtons(cycle);
  actions.querySelectorAll('[data-cycle-state]').forEach(b=>b.onclick=async()=>{
    const state=b.dataset.cycleState;
    if(!confirm(`Confirmer la transition vers « ${statusLabel(state)} »?`))return;
    try{await rpc('admin_parallel_set_cycle_status',{p_cycle_id:id,p_status:state});showSuccess(`Cycle : ${statusLabel(state)}.`);await loadCycles()}catch(error){showError(error)}
  });

  const [responsesData,storiesData]=await Promise.all([
    rpc('admin_parallel_list_responses',{p_cycle_id:id}),rpc('admin_parallel_list_stories',{p_cycle_id:id})
  ]);
  const responses=Array.isArray(responsesData.responses)?responsesData.responses:[];
  const stories=Array.isArray(storiesData.stories)?storiesData.stories:[];
  const responseBox=detail.querySelector('[data-parallel-response-list]');
  responseBox.innerHTML=responses.map(r=>`<article class="admin-management-row"><div><strong>${escapeHtml(r.identity_name||'Identité parallèle')}</strong><span>${escapeHtml(responseModeLabel(r.response_kind))} · ${escapeHtml(dateTime(r.submitted_at))}</span><p>${escapeHtml(r.response_text||'')}</p><small>${Number(r.individual_story_count||0)} Chronique(s) individuelle(s)</small></div></article>`).join('')||'<p>Aucune réponse pour ce cycle.</p>';
  const responseSelect=detail.querySelector('[data-parallel-story-form] select[name="response_id"]');
  responseSelect.innerHTML=responses.map(r=>`<option value="${escapeHtml(r.response_id)}">${escapeHtml(r.identity_name||'Identité parallèle')} — ${escapeHtml(dateTime(r.submitted_at))}</option>`).join('');

  const storyBox=detail.querySelector('[data-parallel-story-list]');
  storyBox.innerHTML=stories.map(s=>`<article class="admin-management-row" data-story="${escapeHtml(s.story_id)}"><div><strong>${escapeHtml(s.title||'Chronique')}</strong><span>${s.story_kind==='individual'?`Individuelle · ${escapeHtml(s.identity_name||'Identité parallèle')}`:`Collective · ${escapeHtml(audienceLabel(s.audience))}`} · ${s.published_at?'Publiée':'Retirée'}</span><p>${escapeHtml(String(s.content||'').slice(0,500))}${String(s.content||'').length>500?'…':''}</p><small>${escapeHtml(dateTime(s.created_at))}</small></div>${s.published_at?'<button class="btn btn-secondary btn-small" data-story-retract>Retirer</button>':''}</article>`).join('')||'<p>Aucune Chronique pour ce cycle.</p>';
  storyBox.querySelectorAll('[data-story]').forEach(card=>card.querySelector('[data-story-retract]')?.addEventListener('click',async()=>{
    if(!confirm('Retirer cette Chronique publiée? Le retrait est réversible au niveau des données : la ligne est conservée.'))return;
    try{await rpc('admin_parallel_retract_story',{p_story_id:card.dataset.story});showSuccess('Chronique retirée de la publication.');await loadCycleDetail(id);await loadCycles()}catch(error){showError(error)}
  }));
  detail.scrollIntoView({behavior:'smooth',block:'start'});
}

inject();
