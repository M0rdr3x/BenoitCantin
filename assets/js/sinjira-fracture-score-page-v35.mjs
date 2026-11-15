import {fractureConfiguration,fractureScore} from './sinjira-fracture-score-v35.mjs';

/* Outil d'arbitrage local d'une partie PHYSIQUE. Aucune lecture/écriture
   Supabase, aucun stockage, aucune donnée de compte, aucun joueur identifié. */
const $=id=>document.getElementById(id);
const tbody=$('fracture-rounds-body');
const configForm=$('fracture-score-config');
const scoreForm=$('fracture-score-form');
const finalPanel=$('fracture-final-panel');
let active=null;

function say(text,kind='info'){
  const node=$('fracture-score-status');
  node.hidden=false;
  node.textContent=text;
  node.dataset.type=kind;
}
function node(tag,text){
  const el=document.createElement(tag);
  if(text!==undefined)el.textContent=String(text);
  return el;
}
function numericInput(round,camp,max){
  const el=node('input');
  el.type='number';el.inputMode='numeric';el.min='0';el.max=String(max);
  el.step='1';el.autocomplete='off';
  el.name='round_'+round+'_'+camp;
  el.dataset.round=String(round);el.dataset.camp=camp;
  el.setAttribute('aria-label','Ronde '+round+' — points '+
    (camp==='resistance'?'Résistance':'Réseau-Mère'));
  el.addEventListener('input',update);
  return el;
}
function build(config){
  active=config;
  tbody.replaceChildren();
  for(let round=1;round<=config.rounds;round++){
    const row=node('tr');
    const head=node('th',round);
    head.scope='row';
    const resistance=node('td');
    const reseau=node('td');
    resistance.append(numericInput(round,'resistance',config.maxRoundPoints));
    reseau.append(numericInput(round,'reseau',config.maxRoundPoints));
    row.append(head,resistance,reseau);
    tbody.append(row);
  }
  $('fracture-correct').value='';
  $('fracture-incorrect').value='';
  finalPanel.hidden=true;
  $('fracture-score-rules').textContent=config.humans+' humain(s) · '+
    config.seats+' sièges · '+config.agents+' agent(s) Réseau-Mère · '+
    config.rounds+' rondes'+(config.express?' (Express)':'')+
    ' · '+config.centralCards+' cartes au centre par ronde · '+
    config.ballots+' accusations finales humaines.';
  $('fracture-score-range').textContent='Pour '+config.centralCards+
    ' cartes récupérées : total de '+config.minRoundPoints+
    ' à '+config.maxRoundPoints+' points par ronde.';
  update();
}
function hasEnteredScores(){
  return [...tbody.querySelectorAll('input')].some(el=>el.value!=='')||
    $('fracture-correct').value!==''||$('fracture-incorrect').value!=='';
}
function collect(){
  return [...tbody.querySelectorAll('tr')].map(row=>{
    const [r,m]=row.querySelectorAll('input');
    if(r.value===''&&m.value==='')return null;
    if(r.value===''||m.value===''){
      throw new RangeError('Complétez les deux scores de la ronde '+row.querySelector('th').textContent+'.');
    }
    return {resistance:r.value,reseau:m.value};
  });
}
function update(){
  if(!active)return;
  try{
    const rounds=collect();
    const ready=rounds.every(x=>x!==null);
    finalPanel.hidden=!ready;
    const correct=$('fracture-correct').value;
    const incorrect=$('fracture-incorrect').value;
    if((correct!==''||incorrect!=='')&&!ready){
      throw new RangeError('Complétez les rondes avant de saisir les accusations finales.');
    }
    if((correct==='')!==(incorrect==='')){
      throw new RangeError('Saisissez les accusations correctes et erronées ensemble.');
    }
    const result=fractureScore({
      humans:active.humans,express:active.express,rounds,
      correct:correct===''?null:correct,incorrect:incorrect===''?null:incorrect
    });
    $('fracture-progress').textContent=result.played+' / '+active.rounds+' rondes';
    $('fracture-total-r').textContent=String(result.operation.resistance);
    $('fracture-total-m').textContent=String(result.operation.reseau);
    $('fracture-wins-r').textContent=String(result.roundWins.resistance);
    $('fracture-wins-m').textContent=String(result.roundWins.reseau);
    $('fracture-bonus-r').textContent=result.bonus===null?'—':String(result.bonus.resistance);
    $('fracture-bonus-m').textContent=result.bonus===null?'—':String(result.bonus.reseau);
    $('fracture-final-r').textContent=result.totals===null?'—':String(result.totals.resistance);
    $('fracture-final-m').textContent=result.totals===null?'—':String(result.totals.reseau);
    const conclusion=$('fracture-conclusion');
    if(result.status==='incomplete'){
      conclusion.textContent='Partie en cours. Complétez les '+active.rounds+' rondes pour accéder aux accusations finales.';
    }else if(result.status==='awaiting-accusations'){
      conclusion.textContent='Rondes terminées. Renseignez les '+active.ballots+
        ' accusations humaines (correctes + erronées) après révélation des identités.';
    }else if(result.status==='tie-breaker'){
      conclusion.textContent='Égalité après les points et les rondes remportées : jouez une ronde de départage selon les règles officielles, sans nouveau bonus d’accusation.';
    }else{
      conclusion.textContent='Camp gagnant : '+(result.winner==='resistance'?'Résistance':'Réseau-Mère')+'.';
    }
    say('Feuille calculée localement. Aucune donnée transmise ou sauvegardée.', 'success');
  }catch(error){
    $('fracture-conclusion').textContent='Corrigez les scores pour obtenir un résultat valide.';
    $('fracture-final-r').textContent='—';
    $('fracture-final-m').textContent='—';
    say(error?.message||'Données invalides.', 'warning');
  }
}
configForm.addEventListener('submit',event=>{
  event.preventDefault();
  try{
    const humans=$('fracture-humans').value;
    const express=$('fracture-express').checked;
    const next=fractureConfiguration(humans,{express});
    if(active&&hasEnteredScores()&&!window.confirm('Recréer la feuille effacera les scores de cette session. Continuer ?'))return;
    build(next);
  }catch(error){say(error.message,'warning')}
});
scoreForm.addEventListener('submit',event=>event.preventDefault());
$('fracture-correct').addEventListener('input',update);
$('fracture-incorrect').addEventListener('input',update);
$('fracture-reset').addEventListener('click',()=>{
  if(hasEnteredScores()&&!window.confirm('Effacer les scores de cette session ?'))return;
  build(active);
});
$('fracture-print').addEventListener('click',()=>window.print());
$('fracture-humans').addEventListener('input',()=>{
  const count=Number($('fracture-humans').value);
  if(count<13)$('fracture-express').checked=false;
  $('fracture-express').disabled=count<13||count>20||!Number.isInteger(count);
});
build(fractureConfiguration(3));
