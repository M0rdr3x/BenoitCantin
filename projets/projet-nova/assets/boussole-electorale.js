(() => {
  "use strict";

  const DATA_URL = "data/boussole-electorale-v1.json";
  const RESPONSES = [
    {value:-3,label:"Tout à fait en désaccord"},
    {value:-2,label:"En désaccord"},
    {value:-1,label:"Plutôt en désaccord"},
    {value:0,label:"Neutre / partagé"},
    {value:1,label:"Plutôt d’accord"},
    {value:2,label:"D’accord"},
    {value:3,label:"Tout à fait d’accord"}
  ];
  const WEIGHTS = [
    {value:"faible",label:"Importance faible"},
    {value:"normal",label:"Importance normale"},
    {value:"forte",label:"Importance forte"}
  ];

  const state = {data:null, answers:new Map()};

  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function esc(value){
    return String(value).replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch]));
  }

  function renderQuestion(question, index){
    const fieldset = document.createElement("fieldset");
    fieldset.className = "compass-question";
    fieldset.dataset.questionId = question.id;
    fieldset.innerHTML = `
      <legend><span class="compass-question-number">${index + 1}</span>${esc(question.text)}</legend>
      <div class="compass-response-grid" role="radiogroup" aria-label="Réponse à la proposition ${index + 1}">
        ${RESPONSES.map(r => `<label><input type="radio" name="${question.id}" value="${r.value}"><span>${esc(r.label)}</span></label>`).join("")}
        <label class="compass-skip"><input type="radio" name="${question.id}" value="skip"><span>Sans opinion / passer</span></label>
      </div>
      <label class="compass-importance">Importance de cette proposition
        <select data-importance>
          ${WEIGHTS.map(w => `<option value="${w.value}"${w.value==="normal"?" selected":""}>${esc(w.label)}</option>`).join("")}
        </select>
      </label>
    `;
    return fieldset;
  }

  function updateProgress(){
    const total = state.data.questions.length;
    const answered = state.answers.size;
    const pct = total ? Math.round(answered / total * 100) : 0;
    const bar = $("#compass-progress-bar");
    if(bar) bar.style.width = pct + "%";
    const text = $("#compass-progress-text");
    if(text) text.textContent = `${answered} / ${total} propositions répondues (${pct} %)`;
  }

  function bindQuestion(fieldset, question){
    fieldset.addEventListener("change", event => {
      if(event.target.matches('input[type="radio"]')){
        const raw = event.target.value;
        const previous = state.answers.get(question.id) || {importance:"normal"};
        state.answers.set(question.id, {
          value: raw === "skip" ? null : Number(raw),
          importance: previous.importance || "normal"
        });
        updateProgress();
      }
      if(event.target.matches("[data-importance]")){
        const previous = state.answers.get(question.id);
        if(previous){
          previous.importance = event.target.value;
          state.answers.set(question.id, previous);
        }
      }
    });
  }

  function calculate(){
    const weightMap = state.data.importanceWeights;
    const axes = new Map(state.data.axes.map(axis => [axis.id, {axis, sum:0, max:0, answered:0, total:0}]));
    state.data.questions.forEach(question => {
      const bucket = axes.get(question.axis);
      bucket.total += 1;
      const answer = state.answers.get(question.id);
      if(!answer || answer.value === null) return;
      const weight = weightMap[answer.importance] ?? 1;
      bucket.sum += answer.value * question.direction * weight;
      bucket.max += 3 * weight;
      bucket.answered += 1;
    });
    return Array.from(axes.values()).map(bucket => ({
      ...bucket.axis,
      score: bucket.max ? Math.round((bucket.sum / bucket.max) * 100) : null,
      answered: bucket.answered,
      total: bucket.total,
      coverage: Math.round(bucket.answered / bucket.total * 100)
    }));
  }

  function resultCard(result){
    const score = result.score;
    const label = score === null ? "Non calculé" : (score === 0 ? "Équilibre" : score < 0 ? result.negative : result.positive);
    const position = score === null ? 50 : Math.max(0, Math.min(100, (score + 100) / 2));
    const signed = score === null ? "—" : (score > 0 ? "+" + score : String(score));
    return `
      <article class="compass-result-card">
        <div class="compass-result-head">
          <div><h3>${esc(result.title)}</h3><p>${esc(label)}</p></div>
          <strong aria-label="Score ${signed} sur une échelle de moins 100 à plus 100">${signed}</strong>
        </div>
        <div class="compass-axis-labels"><span>${esc(result.negative)}</span><span>${esc(result.positive)}</span></div>
        <div class="compass-axis-track" aria-hidden="true"><span class="compass-axis-mid"></span><i style="left:${position}%"></i></div>
        <div class="compass-result-meta">Couverture : ${result.answered}/${result.total} réponses (${result.coverage} %)</div>
      </article>
    `;
  }

  function showResults(){
    const minimum = Math.ceil(state.data.questions.length * 0.5);
    const answered = Array.from(state.answers.values()).filter(x => x.value !== null).length;
    const status = $("#compass-status");
    if(answered < minimum){
      status.textContent = `Répondez à au moins ${minimum} propositions pour obtenir un profil suffisamment couvert. Vous en avez répondu ${answered}.`;
      status.focus();
      return;
    }
    const results = calculate();
    $("#compass-results-grid").innerHTML = results.map(resultCard).join("");
    const coverage = Math.round(results.reduce((sum,r)=>sum+r.coverage,0)/results.length);
    $("#compass-summary").textContent = `Profil calculé sur 10 axes. Couverture moyenne : ${coverage} %. Aucun score global gauche/droite n’est généré.`;
    $("#compass-results").hidden = false;
    status.textContent = "Votre profil multidimensionnel a été calculé localement dans votre navigateur.";
    $("#compass-results").scrollIntoView({behavior:"smooth", block:"start"});
  }

  function reset(){
    state.answers.clear();
    $$("#compass-form input[type=radio]").forEach(el => {el.checked=false;});
    $$("#compass-form select[data-importance]").forEach(el => {el.value="normal";});
    $("#compass-results").hidden = true;
    $("#compass-status").textContent = "Questionnaire réinitialisé.";
    updateProgress();
  }

  async function init(){
    const mount = $("#compass-questions");
    if(!mount) return;
    try{
      const response = await fetch(DATA_URL, {cache:"no-store"});
      if(!response.ok) throw new Error("HTTP " + response.status);
      state.data = await response.json();
      state.data.questions.forEach((question,index) => {
        const fieldset = renderQuestion(question,index);
        bindQuestion(fieldset,question);
        mount.appendChild(fieldset);
      });
      $("#compass-axis-count").textContent = state.data.axes.length;
      $("#compass-question-count").textContent = state.data.questions.length;
      updateProgress();
      $("#compass-calculate").disabled = false;
      $("#compass-reset").disabled = false;
    }catch(error){
      $("#compass-status").textContent = "Impossible de charger la boussole. Rechargez la page ou réessayez plus tard.";
      console.error("Boussole électorale Nova:", error);
    }
    $("#compass-calculate")?.addEventListener("click", showResults);
    $("#compass-reset")?.addEventListener("click", reset);
  }

  document.addEventListener("DOMContentLoaded", init);
})();