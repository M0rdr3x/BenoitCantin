/* Projet Nova : consultation fondamentale de 40 questions, version candidate.
 * Aucun stockage local ni envoi tant que la collecte n'est pas validée.
 */
(() => {
  'use strict';
  const COLLECTION_OPEN = false;
  const $ = id => document.getElementById(id);
  const answers = new Map();
  let questions = [];
  let step = 0;
  const options = [
    ['pour','Pour'],
    ['contre','Contre'],
    ['sans_opinion','Sans opinion / passer']
  ];
  const allowed = new Set(options.map(([id])=>id));
  const eligible = () => $('sondage-age').checked && $('sondage-consent').checked;
  function refresh(){
    $('sondage-start').disabled = !eligible() || questions.length !== 40;
  }
  function render(){
    const item = questions[step];
    $('sondage-position').textContent = 'Question '+(step+1)+' sur 40 · '+item.topic;
    $('sondage-progress').value = step;
    $('sondage-progress').max = 40;
    $('sondage-question-heading').textContent = item.text;
    const choices = $('sondage-choices');
    choices.replaceChildren();
    for (const [choice,label] of options){
      const wrapper = document.createElement('label');
      const radio = document.createElement('input');
      radio.type='radio';radio.name='nova40-response';radio.value=choice;
      radio.checked = answers.get(item.id)===choice;
      radio.addEventListener('change',()=>{
        answers.set(item.id,choice);
        $('sondage-next').disabled=false;
        $('sondage-status').textContent='';
      });
      const span=document.createElement('span');span.textContent=label;
      wrapper.append(radio,span);choices.append(wrapper);
    }
    $('sondage-back').disabled=step===0;
    $('sondage-next').disabled=!answers.has(item.id);
    $('sondage-next').textContent=step===39?'Terminer le questionnaire':'Suivant';
    $('sondage-question-heading').setAttribute('tabindex','-1');
    $('sondage-question-heading').focus({preventScroll:true});
  }
  function complete(){
    if (!eligible() || questions.length !== 40 || answers.size!==40) return;
    $('sondage-questionnaire').hidden=true;
    $('sondage-finish').hidden=false;
    $('sondage-recap').textContent='Vous avez répondu à '+(40-[...answers.values()].filter(v=>v==='sans_opinion').length)+
      ' propositions et choisi « Sans opinion » pour '+[...answers.values()].filter(v=>v==='sans_opinion').length+
      ' questions. Aucune réponse n’a été transmise.';
    $('sondage-submit').disabled=true;
    $('sondage-submit-status').textContent='Collecte fermée : aucune donnée enregistrée. Ouverture soumise à la validation juridique et à la protection des données.';
    $('sondage-finish-heading').setAttribute('tabindex','-1');
    $('sondage-finish-heading').focus({preventScroll:true});
  }
  function init(){
    for(const id of ['sondage-age','sondage-consent']){
      $(id).addEventListener('change',refresh);
    }
    $('sondage-start').addEventListener('click',()=>{
      if(!eligible()||questions.length!==40)return;
      $('sondage-introduction').hidden=true;
      $('sondage-questionnaire').hidden=false;
      render();
    });
    $('sondage-next').addEventListener('click',()=>{
      if(!answers.has(questions[step].id))return;
      if(step===39)complete();else{step++;render();}
    });
    $('sondage-back').addEventListener('click',()=>{if(step>0){step--;render();}});
    $('sondage-review').addEventListener('click',()=>{
      $('sondage-finish').hidden=true;
      $('sondage-questionnaire').hidden=false;
      render();
    });
    $('sondage-form').addEventListener('submit',e=>e.preventDefault());
    $('sondage-submit').addEventListener('click',()=>{if(COLLECTION_OPEN) return;});
    fetch('data/consultation-40-v1.json',{cache:'no-store',credentials:'omit'})
      .then(r=>{if(!r.ok)throw Error('HTTP');return r.json();})
      .then(data=>{
        if(data.id!=='nova-orientations-40-v1'||data.minimumAge!==18||
          !Array.isArray(data.questions)||data.questions.length!==40||
          data.collectionOpen!==false)throw Error('MANIFEST');
        const ids=new Set();
        for(let i=0;i<40;i++){
          const q=data.questions[i],id='q'+String(i+1).padStart(2,'0');
          if(q.id!==id||ids.has(q.id)||typeof q.text!=='string'||q.text.length<35)throw Error('QUESTION');
          ids.add(q.id);
        }
        if(data.choices.length!==3||!data.choices.every(v=>allowed.has(v)))throw Error('CHOIX');
        questions=data.questions;refresh();
      }).catch(()=>{
        $('sondage-start').disabled=true;
        const message=document.createElement('p');
        message.setAttribute('role','alert');
        message.textContent='Questions indisponibles : le sondage ne peut pas démarrer.';
        $('sondage-introduction').append(message);
      });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
  else init();
})();
