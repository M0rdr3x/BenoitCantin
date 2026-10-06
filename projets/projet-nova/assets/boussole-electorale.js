(() => {
  "use strict";

  const DATA_URL = "data/boussole-electorale-v2.json";
  const PARTY_DATA_URL = "data/boussole-partis-2026.json";
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

  const state = {
    data:null,
    answers:new Map(),
    importance:new Map(),
    currentIndex:0,
    started:false,
    results:null
  };

  const $ = (sel, root=document) => root.querySelector(sel);
  const esc = value => String(value).replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch]));

  function currentQuestion(){
    return state.data?.questions?.[state.currentIndex] || null;
  }

  function renderQuestion(question, index){
    const fieldset = document.createElement("fieldset");
    fieldset.className = "compass-question compass-question-single";
    fieldset.dataset.questionId = question.id;
    const axis = state.data.axes.find(item => item.id === question.axis);
    const saved = state.answers.get(question.id);
    const savedImportance = state.importance.get(question.id) || saved?.importance || "normal";

    fieldset.innerHTML = `
      <div class="compass-question-meta">
        <span class="compass-question-axis">${esc(axis?.title || question.axis)}</span>
        <span class="compass-question-counter">Question ${index + 1} sur ${state.data.questions.length}</span>
      </div>
      <legend>${esc(question.text)}</legend>
      <div class="compass-response-grid compass-response-stack" role="radiogroup" aria-label="Réponse à la proposition ${index + 1}">
        ${RESPONSES.map(r => `<label><input type="radio" name="${question.id}" value="${r.value}"${saved?.value === r.value ? " checked" : ""}><span>${esc(r.label)}</span></label>`).join("")}
        <label class="compass-skip"><input type="radio" name="${question.id}" value="skip"${saved && saved.value === null ? " checked" : ""}><span>Sans opinion / passer</span></label>
      </div>
      <label class="compass-importance">Importance de cette proposition
        <select data-importance>
          ${WEIGHTS.map(w => `<option value="${w.value}"${w.value === savedImportance ? " selected" : ""}>${esc(w.label)}</option>`).join("")}
        </select>
      </label>
    `;

    fieldset.addEventListener("change", event => {
      if(event.target.matches('input[type="radio"]')){
        const raw = event.target.value;
        const importance = state.importance.get(question.id) || fieldset.querySelector("[data-importance]")?.value || "normal";
        state.answers.set(question.id, {
          value: raw === "skip" ? null : Number(raw),
          importance
        });
        updateStepControls();
        updateProgress();
        $("#compass-status").textContent = raw === "skip"
          ? "Question marquée « Sans opinion / passer ». Vous pouvez continuer."
          : "Réponse enregistrée localement. Vous pouvez continuer.";
      }
      if(event.target.matches("[data-importance]")){
        state.importance.set(question.id, event.target.value);
        const savedAnswer = state.answers.get(question.id);
        if(savedAnswer){
          savedAnswer.importance = event.target.value;
          state.answers.set(question.id, savedAnswer);
        }
      }
    });

    return fieldset;
  }

  function renderCurrentQuestion(){
    const question = currentQuestion();
    const stage = $("#compass-question-stage");
    if(!question || !stage) return;
    stage.replaceChildren(renderQuestion(question, state.currentIndex));
    updateProgress();
    updateStepControls();
    const legend = stage.querySelector("legend");
    if(legend){
      legend.setAttribute("tabindex","-1");
      legend.focus({preventScroll:true});
    }
  }

  function updateProgress(){
    if(!state.data) return;
    const total = state.data.questions.length;
    const step = Math.min(total, state.currentIndex + 1);
    const decided = state.answers.size;
    const pct = total ? Math.round(step / total * 100) : 0;
    const bar = $("#compass-progress-bar");
    if(bar) bar.style.width = pct + "%";
    const text = $("#compass-progress-text");
    if(text) text.textContent = `Question ${step} sur ${total} — ${decided} réponse${decided > 1 ? "s" : ""} enregistrée${decided > 1 ? "s" : ""}`;
  }

  function updateStepControls(){
    if(!state.data) return;
    const question = currentQuestion();
    const prev = $("#compass-prev");
    const next = $("#compass-next");
    if(prev) prev.disabled = state.currentIndex === 0;
    if(next){
      next.disabled = !question || !state.answers.has(question.id);
      next.textContent = state.currentIndex === state.data.questions.length - 1
        ? "Consulter mes résultats"
        : "Suivant";
    }
  }

  function startQuestionnaire(){
    if(!state.data) return;
    state.started = true;
    state.currentIndex = 0;
    $("#compass-start-panel").hidden = true;
    $("#compass-stepper").hidden = false;
    $("#compass-results").hidden = true;
    $("#compass-status").textContent = "Questionnaire commencé. Choisissez une réponse pour continuer.";
    renderCurrentQuestion();
    $("#compass-stepper").scrollIntoView({behavior:"smooth",block:"start"});
  }

  function goPrevious(){
    if(state.currentIndex <= 0) return;
    state.currentIndex -= 1;
    renderCurrentQuestion();
  }

  function goNext(){
    const question = currentQuestion();
    const status = $("#compass-status");
    if(!question || !state.answers.has(question.id)){
      status.textContent = "Choisissez une réponse ou « Sans opinion / passer » avant de continuer.";
      status.focus();
      return;
    }
    if(state.currentIndex >= state.data.questions.length - 1){
      showResults();
      return;
    }
    state.currentIndex += 1;
    renderCurrentQuestion();
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
    const label = score === null ? "Données insuffisantes" : (score === 0 ? "Équilibre" : score < 0 ? result.negative : result.positive);
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
      host.innerHTML = "<p>Il n’y a pas encore assez de dimensions répondues pour afficher la carte complète.</p>";
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
      const short = esc(p.result.title).split(" ").slice(0,3).join(" ");
      return `<text x="${p.lx.toFixed(1)}" y="${p.ly.toFixed(1)}" text-anchor="middle"><tspan>${short}</tspan><tspan x="${p.lx.toFixed(1)}" dy="15">${p.result.score > 0 ? "+" : ""}${p.result.score}</tspan></text>`;
    }).join("");
    host.innerHTML = `
      <svg class="compass-radar-svg" viewBox="0 0 ${size} ${size}" role="img" aria-labelledby="compass-radar-title compass-radar-desc">
        <title id="compass-radar-title">Carte multidimensionnelle de votre profil</title>
        <desc id="compass-radar-desc">Chaque rayon représente une dimension et sa position calculée selon vos réponses.</desc>
        <circle cx="${center}" cy="${center}" r="${radius}"></circle>
        <circle cx="${center}" cy="${center}" r="${radius * .5}"></circle>
        ${spokes}
        <polygon points="${polygon}"></polygon>
        ${labels}
      </svg>`;
  }

  function coveragePercent(results){
    return Math.round(results.reduce((sum,result) => sum + result.coverage, 0) / Math.max(1,results.length));
  }

  function buildResultText(results, compact=false){
    const valid = results.filter(r => r.score !== null);
    const coverage = coveragePercent(results);
    const lines = valid
      .slice()
      .sort((a,b) => Math.abs(b.score) - Math.abs(a.score))
      .map(r => `${r.title}: ${r.score > 0 ? "+" : ""}${r.score} — ${r.score === 0 ? "Équilibre" : r.score < 0 ? r.negative : r.positive}`);
    const selected = compact ? lines.slice(0,5) : lines;
    return [
      "Mon profil — Boussole électorale Nova",
      `Couverture moyenne : ${coverage} %`,
      "",
      ...(selected.length ? selected : ["Aucune dimension calculable."]),
      "",
      compact && lines.length > selected.length ? "Consultez la page pour le détail des 16 dimensions." : "",
      "Ce résultat décrit mes réponses et ne constitue pas une recommandation de vote."
    ].filter(Boolean).join("\n");
  }

  function configureSharing(results){
    const pageUrl = window.location.href.split("#")[0];
    const compact = buildResultText(results,true);
    const full = buildResultText(results,false);
    const subject = "Mon résultat — Boussole électorale Nova";

    const email = $("#compass-share-email");
    const emailInput = $("#compass-email-recipient");
    const updateEmailLink = () => {
      if(!email) return;
      const recipient = emailInput?.value?.trim() || "";
      const target = recipient ? encodeURIComponent(recipient) : "";
      email.href = `mailto:${target}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(full + "\n\n" + pageUrl)}`;
    };
    updateEmailLink();
    if(emailInput) emailInput.oninput = updateEmailLink;

    const facebook = $("#compass-share-facebook");
    if(facebook){
      const base = facebook.getAttribute("href").split("?")[0];
      facebook.href = `${base}?u=${encodeURIComponent(pageUrl)}&quote=${encodeURIComponent(compact)}`;
    }

    const x = $("#compass-share-x");
    if(x){
      const base = x.getAttribute("href").split("?")[0];
      x.href = `${base}?text=${encodeURIComponent(compact)}&url=${encodeURIComponent(pageUrl)}`;
    }

    const linkedin = $("#compass-share-linkedin");
    if(linkedin){
      const base = linkedin.getAttribute("href").split("?")[0];
      linkedin.href = `${base}?url=${encodeURIComponent(pageUrl)}`;
    }

    $("#compass-share-native")?.addEventListener("click", async () => {
      if(navigator.share){
        try{
          await navigator.share({title:subject,text:compact,url:pageUrl});
          $("#compass-status").textContent = "Menu de partage ouvert.";
        }catch(error){
          if(error?.name !== "AbortError") $("#compass-status").textContent = "Le partage n’a pas pu être ouvert. Vous pouvez copier le résumé.";
        }
      }else{
        await copyText(compact + "\n" + pageUrl);
        $("#compass-status").textContent = "Le partage natif n’est pas disponible; le résumé a été copié.";
      }
    }, {once:true});

    $("#compass-copy-result")?.addEventListener("click", async () => {
      await copyText(full + "\n\n" + pageUrl);
      $("#compass-status").textContent = "Résumé copié dans le presse-papiers.";
    }, {once:true});
  }

  async function copyText(text){
    if(navigator.clipboard?.writeText){
      await navigator.clipboard.writeText(text);
      return;
    }
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly","");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }

  function showResults(){
    const answered = Array.from(state.answers.values()).filter(x => x.value !== null).length;
    if(answered === 0){
      $("#compass-status").textContent = "Vous avez passé toutes les questions. Répondez à au moins une proposition pour obtenir un profil.";
      $("#compass-status").focus();
      return;
    }

    const results = calculate();
    state.results = results;
    $("#compass-results-grid").innerHTML = results.map(resultCard).join("");
    renderRadar(results);

    const minimum = Math.ceil(state.data.questions.length * (state.data.methodology?.minimumAnsweredRatio ?? 0.5));
    const coverage = coveragePercent(results);
    const partial = answered < minimum;
    $("#compass-summary").textContent = partial
      ? `Profil partiel : ${answered} propositions répondues sur ${state.data.questions.length}; couverture moyenne ${coverage} %. Les dimensions peu couvertes doivent être interprétées avec prudence.`
      : `Profil calculé sur ${state.data.axes.length} dimensions; couverture moyenne ${coverage} %. Aucun score global gauche/droite n’est généré.`;

    $("#compass-results").hidden = false;
    configureSharing(results);
    $("#compass-status").textContent = "Votre résultat a été calculé localement dans votre navigateur.";
    $("#compass-results").scrollIntoView({behavior:"smooth",block:"start"});
  }

  function reset(){
    state.answers.clear();
    state.importance.clear();
    state.currentIndex = 0;
    state.started = false;
    state.results = null;
    $("#compass-results").hidden = true;
    $("#compass-stepper").hidden = true;
    $("#compass-start-panel").hidden = false;
    $("#compass-status").textContent = "Questionnaire réinitialisé. Vous pouvez recommencer quand vous voulez.";
    updateProgress();
    $("#compass-start")?.focus();
  }

  function renderPartyRegistry(corpus){
    const host = $("#compass-parties");
    if(!host) return;
    const parties = Array.isArray(corpus.parties) ? [...corpus.parties] : [];
    parties.sort((a,b) => String(a.name).localeCompare(String(b.name), "fr-CA"));
    host.innerHTML = parties.map(party => {
      const isFuture = party.entityType === "future_party_project";
      const isWithdrawn = party.entityType === "authorization_withdrawn_2026";
      const status = isFuture
        ? "Futur parti — non autorisé actuellement"
        : isWithdrawn
          ? "Autorisation retirée en 2026"
          : "Parti provincial actuellement autorisé";
      return `<article class="compass-party-card"><h3>${esc(party.name)}</h3><p>${esc(status)}</p><span>${party.comparisonEligible ? "Comparaison activée" : "Comparaison non activée — données à sourcer"}</span></article>`;
    }).join("");
  }

  async function loadPartyRegistry(){
    const host = $("#compass-parties");
    if(!host) return;
    try{
      const response = await fetch(PARTY_DATA_URL,{cache:"no-store"});
      if(!response.ok) throw new Error("HTTP " + response.status);
      renderPartyRegistry(await response.json());
    }catch(error){
      host.innerHTML = "<p>Impossible de charger le registre des formations pour le moment.</p>";
      console.error("Boussole électorale Nova — formations:",error);
    }
  }

  async function init(){
    try{
      const response = await fetch(DATA_URL,{cache:"no-store"});
      if(!response.ok) throw new Error("HTTP " + response.status);
      state.data = await response.json();
      $("#compass-axis-count").textContent = state.data.axes.length;
      $("#compass-question-count").textContent = state.data.questions.length;
      $("#compass-start").disabled = false;
      $("#compass-status").textContent = "La boussole est prête. Vos réponses resteront dans ce navigateur.";
    }catch(error){
      $("#compass-status").textContent = "Impossible de charger la boussole. Rechargez la page ou réessayez plus tard.";
      console.error("Boussole électorale Nova:",error);
    }

    $("#compass-start")?.addEventListener("click",startQuestionnaire);
    $("#compass-prev")?.addEventListener("click",goPrevious);
    $("#compass-next")?.addEventListener("click",goNext);
    $("#compass-reset")?.addEventListener("click",reset);
  }

  document.addEventListener("DOMContentLoaded",() => {
    init();
    loadPartyRegistry();
  });
})();
