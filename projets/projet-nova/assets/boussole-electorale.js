(() => {
  "use strict";

  const DATA_URL = "data/boussole-electorale-v2.json";
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
    const axis = state.data.axes.find(item => item.id === question.axis);\n    fieldset.innerHTML = `\n      <div class="compass-question-axis">${esc(axis?.title || question.axis)}</div>\n      <legend><span class="compass-question-number">${index + 1}</span>${esc(question.text)}</legend>
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
    const weightMap = state.data.methodology?.importanceWeights || {faible:0.5,normal:1,forte:1.5};
    const axes = new Map(state.data.axes.map(axis => [axis.id, {
      axis, sum:0, max:0, primaryAnswered:0, primaryTotal:0, evidenceWeight:0
    }]));

    state.data.questions.forEach(question => {
      const primary = axes.get(question.axis);
      if(primary) primary.primaryTotal += 1;

      const answer = state.answers.get(question.id);
      if(!answer || answer.value === null) return;
      if(primary) primary.primaryAnswered += 1;

      const userWeight = weightMap[answer.importance] ?? 1;
      const loadings = Array.isArray(question.loadings) && question.loadings.length
        ? question.loadings
        : [{axis:question.axis, weight:1, direction:question.direction}];

      loadings.forEach(loading => {
        const bucket = axes.get(loading.axis);
        if(!bucket) return;
        const loadingWeight = Number(loading.weight) || 0;
        const direction = Number(loading.direction) || 0;
        bucket.sum += answer.value * direction * userWeight * loadingWeight;
        bucket.max += 3 * userWeight * loadingWeight;
        bucket.evidenceWeight += loadingWeight;
      });
    });

    return Array.from(axes.values()).map(bucket => ({
      ...bucket.axis,
      score: bucket.max ? Math.round((bucket.sum / bucket.max) * 100) : null,
      answered: bucket.primaryAnswered,
      total: bucket.primaryTotal,
      coverage: bucket.primaryTotal ? Math.round(bucket.primaryAnswered / bucket.primaryTotal * 100) : 0,
      evidenceWeight: Math.round(bucket.evidenceWeight * 100) / 100
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

  function renderRadar(results){
    const host = $("#compass-radar");
    if(!host) return;
    const valid = results.filter(r => r.score !== null);
    if(valid.length < 3){
      host.innerHTML = "<p>Répondez à davantage de dimensions pour afficher la carte.</p>";
      return;
    }
    const size = 620, center = size / 2, radius = 220;
    const points = valid.map((r, index) => {
      const angle = (-Math.PI / 2) + (index * 2 * Math.PI / valid.length);
      const normalized = (r.score + 100) / 200;
      const rr = radius * normalized;
      return {
        x:center + Math.cos(angle) * rr,
        y:center + Math.sin(angle) * rr,
        lx:center + Math.cos(angle) * (radius + 64),
        ly:center + Math.sin(angle) * (radius + 64),
        sx:center + Math.cos(angle) * radius,
        sy:center + Math.sin(angle) * radius,
        result:r
      };
    });
    const polygon = points.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
    const spokes = points.map(p => `<line x1="${center}" y1="${center}" x2="${p.sx.toFixed(1)}" y2="${p.sy.toFixed(1)}"></line>`).join("");
    const labels = points.map(p => {
      const words = esc(p.result.title).split(" ");
      const short = words.slice(0,3).join(" ");
      return `<text x="${p.lx.toFixed(1)}" y="${p.ly.toFixed(1)}" text-anchor="middle"><tspan>${short}</tspan><tspan x="${p.lx.toFixed(1)}" dy="15">${p.result.score > 0 ? "+" : ""}${p.result.score}</tspan></text>`;
    }).join("");
    host.innerHTML = `
      <svg class="compass-radar-svg" viewBox="0 0 ${size} ${size}" role="img" aria-labelledby="compass-radar-title compass-radar-desc">
        <title id="compass-radar-title">Carte multidimensionnelle de votre profil</title>
        <desc id="compass-radar-desc">Chaque rayon va du pôle négatif au centre vers le pôle positif à l’extérieur. Les scores détaillés restent affichés sous la carte.</desc>
        <circle cx="${center}" cy="${center}" r="${radius}"></circle>
        <circle cx="${center}" cy="${center}" r="${radius * .5}"></circle>
        ${spokes}
        <polygon points="${polygon}"></polygon>
        ${labels}
      </svg>`;
  }

  function showResults(){
    const minimum = Math.ceil(state.data.questions.length * (state.data.methodology?.minimumAnsweredRatio ?? 0.5));
    const answered = Array.from(state.answers.values()).filter(x => x.value !== null).length;
    const status = $("#compass-status");
    if(answered < minimum){
      status.textContent = `Répondez à au moins ${minimum} propositions pour obtenir un profil suffisamment couvert. Vous en avez répondu ${answered}.`;
      status.focus();
      return;
    }
    const results = calculate();
    $("#compass-results-grid").innerHTML = results.map(resultCard).join("");
    renderRadar(results);
    const coverage = Math.round(results.reduce((sum,r)=>sum+r.coverage,0)/results.length);
    $("#compass-summary").textContent = `Profil calculé sur ${state.data.axes.length} dimensions. Couverture moyenne : ${coverage} %. Aucun score global gauche/droite n’est généré.`;
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