import {getSupabase,requireUser,escapeHtml,friendlyBackendMessage} from './sinjira-supabase.js';
const code=(new URLSearchParams(location.search).get('code')||'').trim().toUpperCase();
const box=document.querySelector('[data-endgame-workspace]');
const status=document.querySelector('[data-fracture-status]');
function show(msg,type='info'){if(!status)return;status.hidden=false;status.textContent=friendlyBackendMessage(msg,msg);status.dataset.type=type}
const idLabel=v=>v==='resistance'?'Résistance':v==='network'?'Réseau-Mère':'—';
async function boot(){
  await requireUser();
  if(!/^FRM-[A-Z0-9]{6}$/.test(code)){show('Code de partie invalide. Format attendu : FRM-ABC123.','error');return}
  const {data:s,error}=await getSupabase().rpc('fracture_engine_get_state',{p_party_code:code});
  if(error)throw error;
  if(!s||s.ok===false)throw new Error(s?.error||'État de partie invalide.');
  const facts=document.querySelector('[data-party-facts]');
  if(facts)facts.innerHTML=[`Code ${s.party_code||code}`,`${Number(s.human_player_count)||0} humain(s)`,`${Number(s.round_count)||0} rondes`].map(x=>`<span>${escapeHtml(x)}</span>`).join('');
  if(s.phase!=='finished'){
    if(box)box.innerHTML=`<h2>Partie en cours</h2><p>Le résultat final n’est pas encore disponible.</p><a class="btn btn-primary" href="partie.html?code=${encodeURIComponent(code)}">Retourner à la partie</a>`;
    return;
  }
  const score=s.score||{};
  const totalR=Number(score.R||0)+Number(score.R_bonus||0),totalRM=Number(score.RM||0)+Number(score.RM_bonus||0);
  if(box)box.innerHTML=`<span class="eyebrow">Résultat officiel du moteur</span><h2>${idLabel(s.winner)} gagne</h2><div class="engine-score"><article><span>Résistance</span><strong>${totalR}</strong><small>${Number(score.R)||0} + bonus ${Number(score.R_bonus)||0}</small></article><article><span>Réseau-Mère</span><strong>${totalRM}</strong><small>${Number(score.RM)||0} + bonus ${Number(score.RM_bonus)||0}</small></article></div><h3>Rondes</h3><div class="engine-round-history">${(s.rounds||[]).map(r=>`<span>R${Number(r.round)||0}${r.tiebreak?' départage':''} : R ${Number(r.R)||0} — RM ${Number(r.RM)||0}</span>`).join('')||'<span>Aucune ronde enregistrée.</span>'}</div><h3>Accusés finaux</h3><p>${(s.final_accused||[]).map(n=>`#${Number(n)||0}`).join(', ')||'—'}</p><h3>Identités révélées</h3><div class="engine-seats">${(s.seats||[]).map(x=>`<article class="engine-seat"><strong>#${Number(x.seat)||0} ${escapeHtml(x.name)}</strong><span>${idLabel(x.identity)}</span></article>`).join('')}</div><div class="hero-actions"><button class="btn btn-secondary" data-print-result type="button">Imprimer / PDF</button><a class="btn btn-primary" href="jouer.html">Nouvelle partie</a></div>`;
  box?.querySelector('[data-print-result]')?.addEventListener('click',()=>window.print());
}
boot().catch(err=>{console.warn('[Fracture result]',err);show(err.message||'Résultat indisponible.','error')});
