(() => {
  "use strict";

  const DATA_URL = "data/boussole-electorale-v2.json";
  const PARTY_DATA_URL = "data/boussole-partis-2026.json";
  const PARTY_SOURCE_DATA_URL = "data/boussole-sources-partis-2026.json";
  const EVIDENCE_DATA_URL = "data/boussole-preuves-2026.json";
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

  function renderPartyRegistry(corpus,evidenceCorpus){
    const host = $("#compass-parties");
    if(!host) return;
    const parties = Array.isArray(corpus.parties) ? [...corpus.parties] : [];
    const matrixQuestions = Array.isArray(evidenceCorpus?.questions) ? evidenceCorpus.questions : [];
    const totalQuestions = matrixQuestions.length || 64;
    const finalizedByParty = new Map(parties.map(party => [party.id,0]));
    for(const question of matrixQuestions){
      const statuses = question.statuses || {};
      for(const party of parties){
        if((statuses[party.id] || "unknown") !== "unknown"){
          finalizedByParty.set(party.id,(finalizedByParty.get(party.id) || 0) + 1);
        }
      }
    }

    const sortByName = list => list.sort((a,b) => String(a.name).localeCompare(String(b.name), "fr-CA"));
    const currentParties = sortByName(parties.filter(party => party.entityType === "authorized_provincial_party"));
    const traceabilityParties = sortByName(parties.filter(party => party.entityType !== "authorized_provincial_party"));
    const expectedCurrent = Number.isInteger(corpus.registryEvidence?.currentlyAuthorizedProvincialPartyCount)
      ? corpus.registryEvidence.currentlyAuthorizedProvincialPartyCount
      : currentParties.length;
    const expectedElectionEntries = Number.isInteger(corpus.registryEvidence?.officialElectionPartyEntries)
      ? corpus.registryEvidence.officialElectionPartyEntries
      : parties.filter(party => party.election2026Listed === true && party.entityType !== "future_party_project").length;
    const listedElectionEntries = parties.filter(party => party.election2026Listed === true && party.entityType !== "future_party_project").length;
    const listComplete = currentParties.length === expectedCurrent && listedElectionEntries === expectedElectionEntries;

    const renderCard = party => {
      const isFuture = party.entityType === "future_party_project";
      const isWithdrawn = party.entityType === "authorization_withdrawn_2026";
      const status = isFuture
        ? "Futur parti — non autorisé actuellement"
        : isWithdrawn
          ? "Autorisation retirée en 2026"
          : "Parti provincial actuellement autorisé";
      const candidateCount = Number.isInteger(party.candidateCount2026) ? party.candidateCount2026 : null;
      const participation = isFuture
        ? "Non inscrit à la liste officielle des candidatures 2026"
        : candidateCount === 0
          ? "0 candidature acceptée au scrutin provincial 2026"
          : `${candidateCount} candidature${candidateCount === 1 ? "" : "s"} acceptée${candidateCount === 1 ? "" : "s"} en 2026`;
      const finalized = finalizedByParty.get(party.id) || 0;
      const documentary = `${finalized}/${totalQuestions} fiche${finalized === 1 ? "" : "s"} documentaire${finalized === 1 ? "" : "s"} finalisée${finalized === 1 ? "" : "s"}`;
      const comparison = party.comparisonEligible
        ? "Comparaison publique activée"
        : "Comparaison publique non activée";
      return `<article class="compass-party-card"><h3>${esc(party.name)}</h3><p>${esc(status)}</p><span class="compass-party-participation">${esc(participation)}</span><span class="compass-party-documentary">${esc(documentary)}</span><span class="compass-party-comparison">${esc(comparison)}</span></article>`;
    };

    host.innerHTML = `
      <div class="compass-party-completeness" role="status" aria-live="polite">
        <strong>${listComplete ? "Liste officielle 2026 complète." : "Vérification de la liste officielle requise."}</strong>
        <span>${currentParties.length}/${expectedCurrent} partis actuellement autorisés affichés · ${listedElectionEntries}/${expectedElectionEntries} entrées de partis du scrutin 2026 suivies.</span>
      </div>
      <div class="compass-party-group-title"><strong>Partis actuellement autorisés</strong><span>${currentParties.length} formation${currentParties.length === 1 ? "" : "s"}</span></div>
      ${currentParties.map(renderCard).join("")}
      ${traceabilityParties.length ? `<div class="compass-party-group-title compass-party-group-title-secondary"><strong>Traçabilité et projet futur</strong><span>Ces entrées sont séparées des partis actuellement autorisés.</span></div>${traceabilityParties.map(renderCard).join("")}` : ""}
    `;
  }

  const DOCUMENTARY_STATUS_LABELS = {
    documented_support:"Appui documenté",
    documented_opposition:"Opposition documentée",
    documented_mixed_or_conditional:"Position mixte ou conditionnelle",
    ambiguous:"Position indéterminée — source ambiguë",
    contradictory:"Sources contradictoires"
  };

  const CONFIDENCE_LABELS = {low:"Faible",medium:"Moyenne",high:"Élevée"};

  function renderEvidenceExplorer(questionCorpus, partyCorpus, evidenceCorpus){
    const select = $("#compass-evidence-question");
    const filter = $("#compass-evidence-only-documented");
    const host = $("#compass-evidence-question-results");
    const status = $("#compass-evidence-question-status");
    if(!select || !filter || !host || !status) return;

    const questions = Array.isArray(questionCorpus.questions) ? questionCorpus.questions : [];
    const parties = Array.isArray(partyCorpus.parties) ? [...partyCorpus.parties] : [];
    parties.sort((a,b) => String(a.name).localeCompare(String(b.name),"fr-CA"));
    const records = Array.isArray(evidenceCorpus.evidenceRecords)
      ? evidenceCorpus.evidenceRecords.filter(record => record.finalizable === true && record.secondIndependentReview?.status === "completed")
      : [];
    const matrixQuestions = Array.isArray(evidenceCorpus.questions) ? evidenceCorpus.questions : [];
    const matrixByQuestion = new Map(matrixQuestions.map(row => [row.questionId,row.statuses || {}]));
    const recordByKey = new Map(records.map(record => [`${record.questionId}::${record.partyId}`,record]));
    const recordsByQuestion = new Map();
    for(const record of records){
      if(!recordsByQuestion.has(record.questionId)) recordsByQuestion.set(record.questionId,[]);
      recordsByQuestion.get(record.questionId).push(record);
    }

    select.innerHTML = questions.map((question,index) => {
      const count = (recordsByQuestion.get(question.id) || []).length;
      return `<option value="${esc(question.id)}">Q${String(index + 1).padStart(2,"0")} · ${esc(question.text)} · ${count} preuve${count > 1 ? "s" : ""}</option>`;
    }).join("");

    // Les raccourcis sont dérivés du corpus finalisé : aucune question figée.
    // Une preuve unique ne doit jamais être interprétée comme une comparaison.
    const priorities = $("#compass-evidence-priorities");
    const priorityLinks = $("#compass-evidence-priority-links");
    if(priorities && priorityLinks){
      const limitedQuestions = questions
        .map((question,index) => ({question,index,count:(recordsByQuestion.get(question.id) || []).length}))
        .filter(item => item.count === 1);
      priorities.hidden = limitedQuestions.length === 0;
      priorityLinks.innerHTML = limitedQuestions.map(({question,index}) =>
        `<button type="button" data-compass-priority="${esc(question.id)}" aria-controls="compass-evidence-question-results">Q${String(index + 1).padStart(2,"0")} — ${esc(question.text)}</button>`
      ).join("");
      priorityLinks.addEventListener("click",event => {
        const button = event.target.closest("button[data-compass-priority]");
        if(!button || !priorityLinks.contains(button)) return;
        const questionId = button.dataset.compassPriority;
        if(!limitedQuestions.some(item => item.question.id === questionId)) return;
        select.value = questionId;
        renderSelected();
        select.focus();
      });
    }

    function renderSelected(){
      const question = questions.find(item => item.id === select.value) || questions[0];
      if(!question){
        status.textContent = "Aucune proposition disponible.";
        host.innerHTML = '<p class="compass-evidence-empty">Aucune proposition disponible.</p>';
        return;
      }

      const matrixStatuses = matrixByQuestion.get(question.id) || {};
      const documentedCount = parties.filter(party => (matrixStatuses[party.id] || "unknown") !== "unknown").length;
      const unknownCount = parties.length - documentedCount;
      const indeterminateCount = parties.filter(party => ["ambiguous","contradictory"].includes(matrixStatuses[party.id])).length;
      const visibleParties = filter.checked
        ? parties.filter(party => (matrixStatuses[party.id] || "unknown") !== "unknown")
        : parties;

      status.textContent = `${documentedCount} fiche${documentedCount > 1 ? "s" : ""} documentaire${documentedCount > 1 ? "s" : ""} finalisée${documentedCount > 1 ? "s" : ""}, dont ${indeterminateCount} sans direction certaine; ${unknownCount} formation${unknownCount > 1 ? "s" : ""} non documentée${unknownCount > 1 ? "s" : ""} pour cette proposition; ${visibleParties.length}/${parties.length} formations affichées.${documentedCount === 1 ? " Couverture documentaire limitée : une seule formation dispose d’une preuve finalisée. Cela ne suffit pas pour comparer les formations." : ""} Une fiche finalisée peut conclure à une position indéterminée.`;

      host.innerHTML = visibleParties.map(party => {
        const matrixStatus = matrixStatuses[party.id] || "unknown";
        const record = recordByKey.get(`${question.id}::${party.id}`);
        if(matrixStatus === "unknown"){
          return `
            <article class="compass-evidence-record compass-evidence-record-unknown">
              <h4>${esc(party.name)}</h4>
              <span class="compass-evidence-unknown-label">Non documentée</span>
              <p>Aucune preuve finalisée ne permet de coder cette formation pour cette proposition. Cela ne signifie ni appui, ni opposition, ni neutralité.</p>
            </article>
          `;
        }
        if(!record){
          return `
            <article class="compass-evidence-record compass-evidence-record-unknown">
              <h4>${esc(party.name)}</h4>
              <span class="compass-evidence-unknown-label">Donnée indisponible</span>
              <p>Le statut documentaire existe dans la matrice, mais sa fiche de preuve n’a pas pu être chargée. La CI doit empêcher cet état avant publication.</p>
            </article>
          `;
        }
        const sourceDate = record.sourceDate || "Date non indiquée dans la source";
        const checkedAt = record.checkedAt || "Date de vérification non indiquée";
        const secondReviewDate = record.secondIndependentReview?.reviewedAt || "Date de révision non indiquée";
        const label = DOCUMENTARY_STATUS_LABELS[record.proposedStatus] || record.proposedStatus;
        const confidence = CONFIDENCE_LABELS[record.confidence] || record.confidence;
        return `
          <article class="compass-evidence-record">
            <h4>${esc(party.name)}</h4>
            <dl>
              <div><dt>Conclusion documentaire</dt><dd>${esc(label)}</dd></div>
              <div><dt>Confiance</dt><dd>${esc(confidence)}</dd></div>
              <div><dt>Date source</dt><dd>${esc(sourceDate)}</dd></div>
              <div><dt>Vérifiée le</dt><dd>${esc(checkedAt)}</dd></div>
              <div><dt>Deuxième révision</dt><dd>${esc(secondReviewDate)}</dd></div>
            </dl>
            <p><strong>Éléments retenus :</strong> ${esc(record.evidenceSummary)}</p>
            <p><strong>Justification du codage :</strong> ${esc(record.rationale)}</p>
            <p><a href="${esc(record.sourceUrl)}" target="_blank" rel="noopener noreferrer">Consulter la source officielle ↗</a></p>
          </article>
        `;
      }).join("");
    }

    select.addEventListener("change",renderSelected);
    filter.addEventListener("change",renderSelected);
    const firstWithEvidence = questions.find(question => (recordsByQuestion.get(question.id) || []).length > 0);
    if(firstWithEvidence) select.value = firstWithEvidence.id;
    renderSelected();
  }

  function renderDocumentaryStatus(partyCorpus, sourceCorpus, evidenceCorpus){
    const summary = $("#compass-evidence-summary");
    const host = $("#compass-evidence-parties");
    if(!summary || !host) return;

    const parties = Array.isArray(partyCorpus.parties) ? [...partyCorpus.parties] : [];
    const sources = Array.isArray(sourceCorpus.parties) ? sourceCorpus.parties : [];
    const records = Array.isArray(evidenceCorpus.evidenceRecords) ? evidenceCorpus.evidenceRecords : [];
    const researchCoverage = Array.isArray(evidenceCorpus.researchCoverage) ? evidenceCorpus.researchCoverage : [];
    const sourceByParty = new Map(sources.map(row => [row.id,row]));
    const recordsByParty = new Map();

    for(const record of records){
      if(!recordsByParty.has(record.partyId)) recordsByParty.set(record.partyId,[]);
      recordsByParty.get(record.partyId).push(record);
    }

    const matrixQuestions = Array.isArray(evidenceCorpus.questions) ? evidenceCorpus.questions : [];
    const researchedQuestionIds = new Set(
      researchCoverage.flatMap(batch => Array.isArray(batch.questionIds) ? batch.questionIds : [])
    );
    const coveredQuestionCount = researchedQuestionIds.size;
    const totalQuestionCount = matrixQuestions.length;
    const candidateQuestionIds = new Set();
    for(const batch of researchCoverage){
      const batchQuestionIds = Array.isArray(batch.questionIds) ? batch.questionIds : [];
      const candidateCounts = batch?.candidateCountByQuestion || {};
      for(const questionId of batchQuestionIds){
        if(Number(candidateCounts[questionId]) > 0) candidateQuestionIds.add(questionId);
      }
    }
    const candidateQuestionCount = candidateQuestionIds.size;
    const noCandidateQuestionCount = Math.max(0,coveredQuestionCount - candidateQuestionCount);
    const singleProofQuestionCount = matrixQuestions.filter(question =>
      Object.values(question?.statuses || {}).filter(value => value !== "unknown").length === 1
    ).length;
    const secondReviewed = records.filter(record => record.secondIndependentReview?.status === "completed").length;
    const pendingSecond = records.filter(record => record.secondIndependentReview?.status === "pending").length;
    const finalizedByParty = new Map(parties.map(party => [party.id,0]));
    const indeterminateByParty = new Map(parties.map(party => [party.id,0]));
    let finalizedCount = 0;
    let indeterminateCount = 0;
    let directPositionCount = 0;

    for(const question of matrixQuestions){
      const statuses = question?.statuses || {};
      for(const [partyId,statusValue] of Object.entries(statuses)){
        if(statusValue === "unknown") continue;
        finalizedCount += 1;
        finalizedByParty.set(partyId,(finalizedByParty.get(partyId) || 0) + 1);
        if(statusValue === "ambiguous" || statusValue === "contradictory"){
          indeterminateCount += 1;
          indeterminateByParty.set(partyId,(indeterminateByParty.get(partyId) || 0) + 1);
        }
        if(statusValue === "documented_support" || statusValue === "documented_opposition") directPositionCount += 1;
      }
    }

    summary.innerHTML = [
      ["Formations suivies",parties.length],
      ["Questions recherchées",`${coveredQuestionCount}/${totalQuestionCount}`],
      ["Questions avec preuve",`${candidateQuestionCount}/${totalQuestionCount}`],
      ["Questions à preuve unique",singleProofQuestionCount],
      ["Preuves candidates",records.length],
      ["Deuxième révision terminée",secondReviewed],
      ["Fiches finalisées",finalizedCount],
      ["Sans direction certaine",indeterminateCount],
      ["Appuis et oppositions documentés",directPositionCount]
    ].map(([label,value]) => `<article><strong>${esc(value)}</strong><span>${esc(label)}</span></article>`).join("");

    parties.sort((a,b) => String(a.name).localeCompare(String(b.name),"fr-CA"));
    host.innerHTML = parties.map(party => {
      const source = sourceByParty.get(party.id) || {};
      const partyRecords = recordsByParty.get(party.id) || [];
      const reviewed = partyRecords.filter(record => record.secondIndependentReview?.status === "completed").length;
      const finalized = finalizedByParty.get(party.id) || 0;
      const indeterminate = indeterminateByParty.get(party.id) || 0;
      const sourceLabel = source.usableForPositionCoding
        ? "Source politique vérifiée pour le codage"
        : source.officialSite
          ? "Site officiel vérifié — corpus politique à compléter"
          : "Registre officiel seulement — source politique à vérifier";
      return `
        <article class="compass-evidence-card">
          <h3>${esc(party.name)}</h3>
          <p class="compass-evidence-source">${esc(sourceLabel)}</p>
          <dl>
            <div><dt>Preuves candidates</dt><dd>${partyRecords.length}</dd></div>
            <div><dt>2e révision terminée</dt><dd>${reviewed}</dd></div>
            <div><dt>Fiches finalisées</dt><dd>${finalized}</dd></div>
            <div><dt>Sans direction certaine</dt><dd>${indeterminate}</dd></div>
          </dl>
        </article>
      `;
    }).join("");

    const status = $("#compass-evidence-status");
    if(status){
      status.textContent = `${coveredQuestionCount}/${totalQuestionCount} questions recherchées; ${candidateQuestionCount}/${totalQuestionCount} avec au moins une preuve candidate; ${noCandidateQuestionCount} encore sans preuve candidate suffisamment exacte; ${singleProofQuestionCount} avec une seule fiche finalisée. L’absence de preuve candidate ne signifie pas absence de position réelle. ${records.length} preuve${records.length > 1 ? "s" : ""} candidate${records.length > 1 ? "s" : ""}; ${pendingSecond} encore en attente d’une deuxième révision indépendante; ${finalizedCount} fiche${finalizedCount > 1 ? "s" : ""} finalisée${finalizedCount > 1 ? "s" : ""}, dont ${indeterminateCount} sans direction certaine et ${directPositionCount} appuis ou oppositions documentés. Les positions mixtes ou conditionnelles sont distinctes des appuis et oppositions explicites. Une preuve révisée ne permet pas toujours de conclure à la position exacte d’un parti. Aucun de ces nombres ne modifie le poids d’un parti dans la boussole.`;
    }
  }

  async function loadPoliticalRegistryAndEvidence(){
    const partyHost = $("#compass-parties");
    const evidenceHost = $("#compass-evidence-parties");
    try{
      const [partyResponse,sourceResponse,evidenceResponse,questionResponse] = await Promise.all([
        fetch(PARTY_DATA_URL,{cache:"no-store"}),
        fetch(PARTY_SOURCE_DATA_URL,{cache:"no-store"}),
        fetch(EVIDENCE_DATA_URL,{cache:"no-store"}),
        fetch(DATA_URL,{cache:"no-store"})
      ]);
      for(const response of [partyResponse,sourceResponse,evidenceResponse,questionResponse]){
        if(!response.ok) throw new Error("HTTP " + response.status);
      }
      const [partyCorpus,sourceCorpus,evidenceCorpus,questionCorpus] = await Promise.all([
        partyResponse.json(),sourceResponse.json(),evidenceResponse.json(),questionResponse.json()
      ]);
      renderPartyRegistry(partyCorpus,evidenceCorpus);
      renderDocumentaryStatus(partyCorpus,sourceCorpus,evidenceCorpus);
      renderEvidenceExplorer(questionCorpus,partyCorpus,evidenceCorpus);
    }catch(error){
      if(partyHost) partyHost.innerHTML = "<p>Impossible de charger le registre des formations pour le moment.</p>";
      if(evidenceHost) evidenceHost.innerHTML = "<p>Impossible de charger l’état documentaire pour le moment.</p>";
      const explorerHost = $("#compass-evidence-question-results");
      if(explorerHost) explorerHost.innerHTML = '<p class="compass-evidence-empty">Impossible de charger l’explorateur des preuves pour le moment.</p>';
      console.error("Boussole électorale Nova — registre documentaire:",error);
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
    loadPoliticalRegistryAndEvidence();
  });
})();
