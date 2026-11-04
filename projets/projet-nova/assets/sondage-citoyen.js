(() => {
  "use strict";
  const VERSION = "nova-consultation-v1";
  const API = "https://gpvivleexywljowcqkru.supabase.co/functions/v1/nova-civic-poll";
  const VALUES = [-2,-1,0,1,2,9];
  const MIN_NONZERO_CELL = 5;
  const LABELS = {
    "-2":"Tout à fait en désaccord",
    "-1":"Plutôt en désaccord",
    "0":"Ni d’accord ni en désaccord",
    "1":"Plutôt d’accord",
    "2":"Tout à fait d’accord",
    "9":"Sans opinion / passer"
  };
  const $ = id => document.getElementById(id);
  let questions = [];
  let localCorpus = null;
  let open = false;
  let captchaToken = "";
  let siteKey = "";
  let captchaRendered = false;
  let sending = false;
  let sessionToken = "";
  const storageKey = "nova_poll_ballot_token_v1";
  const votedKey = "nova_poll_sent_v1";
  function stored(key) {try { return localStorage.getItem(key); }catch { return null; }}
  function save(key,value) {try { localStorage.setItem(key,value); }catch { /* Private mode: session fallback */ }}
  function setStatus(text) { $("poll-live-status").textContent = text; }
  function randomToken() {
    if(sessionToken) return sessionToken;
    const old = stored(storageKey);
    if(old && /^[0-9a-f]{48}$/.test(old)) return sessionToken=old;
    const bytes = new Uint8Array(24); crypto.getRandomValues(bytes);
    sessionToken = Array.from(bytes,b=>b.toString(16).padStart(2,"0")).join("");
    save(storageKey,sessionToken);
    return sessionToken;
  }
  function optionLabel(question,option) {
    const label = document.createElement("label");
    label.className = "poll-choice";
    const input = document.createElement("input");
    input.type="radio"; input.name=question.id; input.value=String(option);
    input.required = true;
    input.disabled=!open || stored(votedKey)==="yes";
    const span = document.createElement("span");
    span.textContent=LABELS[String(option)];
    label.append(input,span); return label;
  }
  function renderForm() {
    const host=$("poll-questions"); host.replaceChildren();
    for(const question of questions) {
      const fieldset=document.createElement("fieldset"); fieldset.className="poll-question";
      const legend=document.createElement("legend");
      legend.textContent=question.ordinal+". "+question.text;
      fieldset.append(legend);
      const options=document.createElement("div"); options.className="poll-choice-grid";
      for(const value of VALUES) options.append(optionLabel(question,value));
      fieldset.append(options);host.append(fieldset);
    }
    if(!questions.length) host.textContent="Le questionnaire est temporairement indisponible.";
    updateButton();
  }
  function updateButton(){
    const btn=$("poll-send");
    const already=stored(votedKey)==="yes";
    const selections=questions.every(q=>!!document.querySelector('input[name="'+q.id+'"]:checked'));
    const consent=$("poll-adult").checked && $("poll-agree").checked;
    btn.disabled=!open || already || sending || !selections || !consent || !captchaToken;
    if(already) {
      btn.textContent="Participation enregistrée dans ce navigateur";
    } else {
      btn.textContent=sending?"Envoi en cours…":"Envoyer mes réponses";
    }
  }
  function paragraph(text) {
    const p=document.createElement("p");p.textContent=text;return p;
  }
  function renderResults(data){
    const host=$("poll-results");host.replaceChildren();
    if(!validatedPublicResponse(data)) {
      $("poll-results-status").textContent="Les résultats publics ne sont pas disponibles.";
      return;
    }
    const ready=data.resultsVisible === true;
    $("poll-results-status").textContent=ready
      ? "Participations comprises dans la dernière publication : "+data.ballots+". Résultats publiés par lots, sans informations sur les personnes."+ (data.publishedAt ? " Dernière publication : "+new Date(data.publishedAt).toLocaleString("fr-CA")+".":"")
      : "Les répartitions restent masquées jusqu’à "+(data.minPublicBallots || 10)+" participations. Les mises à jour n’interviennent que par lots de dix nouveaux bulletins et au plus une fois toutes les six heures.";
    for(const q of data.questions) {
      const article=document.createElement("article");article.className="poll-result-card";
      const h=document.createElement("h3");h.textContent=q.ordinal+". "+q.text;article.append(h);
      if(ready && q.counts) {
        const answered=VALUES.reduce((sum,v)=>sum+Math.max(0,Number(q.counts[String(v)])||0),0);
        for(const value of VALUES) {
          const n=Math.max(0,Number(q.counts[String(value)])||0);
          const percent=answered?Math.round(n/answered*1000)/10:0;
          const row=document.createElement("div");row.className="poll-result-row";
          const labels=document.createElement("div");labels.className="poll-result-labels";
          const name=document.createElement("span");name.textContent=LABELS[String(value)];
          const amount=document.createElement("strong");amount.textContent=n+" ("+percent.toLocaleString("fr-CA")+" %)";
          const track=document.createElement("div");track.className="poll-result-track";
          track.setAttribute("role","meter");track.setAttribute("aria-label",LABELS[String(value)]);
          track.setAttribute("aria-valuemin","0");track.setAttribute("aria-valuemax","100");
          track.setAttribute("aria-valuenow",String(percent));
          const bar=document.createElement("span");bar.style.width=percent+"%";track.append(bar);
          labels.append(name,amount);row.append(labels,track);article.append(row);
        }
      } else article.append(paragraph("Résultats non publiés : seuil minimal de confidentialité non atteint."));
      host.append(article);
    }
  }
  async function fetchJson(url,opts) {
    const response=await fetch(url,{cache:"no-store",...opts});
    if(!response.ok) throw new Error("HTTP "+response.status);
    return response.json();
  }
  // Vérifier aussi dans le navigateur les lots publics avant de dessiner
  // des pourcentages. Les résultats peuvent être corrompus en transit ou
  // mélangés par un intermédiaire : mieux vaut afficher « indisponible ».
  function validatedPublicResponse(data){
    if(!localCorpus || localCorpus.version!==VERSION || typeof localCorpus.published!=="boolean"
       || !data || typeof data!=="object" || Array.isArray(data)
       || data.version!==VERSION || typeof data.open!=="boolean"
       || (data.open && localCorpus.published!==true)
       || data.minPublicBallots!==10
       || !Array.isArray(data.questions) || questions.length!==8
       || data.questions.length!==questions.length
       || data.questions.some((q,i)=>!q || q.id!==questions[i].id
         || q.ordinal!==questions[i].ordinal || q.text!==questions[i].text)){
      return false;
    }
    if(data.resultsVisible===false){
      return data.ballots===null && data.publishedAt===null
        && data.questions.every(q=>q.counts===null);
    }
    if(data.resultsVisible!==true || !Number.isSafeInteger(data.ballots) || data.ballots<10){
      return false;
    }
    const keys=VALUES.map(String);
    return data.questions.every(q=>{
      if(!q.counts || typeof q.counts!=="object" || Array.isArray(q.counts)
         || Object.keys(q.counts).length!==keys.length) return false;
      let total=0;
      for(const key of keys){
        const n=q.counts[key];
        if(typeof n!=="number" || !Number.isSafeInteger(n) || n<0 || (n>0 && n<MIN_NONZERO_CELL)) return false;
        total+=n;
        if(!Number.isSafeInteger(total)) return false;
      }
      return total===data.ballots;
    });
  }
  async function refreshResults(){
    try {
      const data=await fetchJson(API,{mode:"cors"});
      if(!validatedPublicResponse(data)) throw new Error("public_snapshot_invalid");
      // Une fermeture serveur constatée en direct ferme aussi la soumission
      // du navigateur, même si la page avait été ouverte auparavant.
      if(open && !data.open){
        open=false;captchaToken="";
        setStatus("La consultation vient de fermer. Aucun nouveau vote ne peut être envoyé.");
        updateButton();
      }
      renderResults(data);
      return data;
    }catch{
      open=false;captchaToken="";updateButton();
      renderResults(null);
      return null;
    }
  }
  function loadTurnstile(){
    if(captchaRendered || !open || !siteKey) return;
    const script=document.createElement("script");
    script.src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    script.async=true;script.defer=true;
    script.onload=()=>{
      if(!window.turnstile) {
        $("poll-feedback").textContent="Vérification anti-robots indisponible.";
        return;
      }
      window.turnstile.render("#poll-captcha",{
        sitekey:siteKey,
        action:"nova_poll_vote",
        callback:(token)=>{captchaToken=token;updateButton();},
        "expired-callback":()=>{captchaToken="";updateButton();},
        "error-callback":()=>{captchaToken="";$("poll-feedback").textContent="Vérification anti-robots échouée.";updateButton();}
      });
      captchaRendered=true;
    };
    script.onerror=()=>{$("poll-feedback").textContent="Le module anti-robots ne peut pas être chargé. Vérifiez votre bloqueur de contenu.";};
    document.head.append(script);
  }
  async function loadPoll(){
    // Le corpus embarqué provient exclusivement du JSON public versionné.
    // Sur Pages legacy, le fichier data/*.json retourne 404 ; ne pas
    // confondre cette erreur d'hébergement avec une consultation ouverte.
    let local=window.__NOVA_POLL_PUBLIC_CORPUS;
    if(!local){
      try { local=await fetchJson("data/sondage-citoyen-v1.json"); }
      catch { local={questions:[]}; }
    }
    localCorpus=local;
    questions=(local.questions||[]).filter(q=>/^q[0-9]{2}$/.test(q.id));
    try {
      const remote=await fetchJson(API,{mode:"cors"});
      if(!validatedPublicResponse(remote)) {
        throw new Error("Questionnaire ou résultats publics non concordants");
      }
      open=local.published===true && remote.open===true && typeof remote.siteKey==="string" && !!remote.siteKey;
      siteKey=remote.siteKey||"";
      setStatus(open?"La consultation est ouverte aux personnes de 18 ans et plus."
        :"La consultation est en préparation. Les questions et la méthode peuvent être consultées, mais aucun vote ne peut encore être envoyé.");
      renderResults(remote);
    }catch{
      open=false;
      setStatus("La consultation n'est pas ouverte : service de vote indisponible ou données non concordantes. Aucun vote n'est accepté.");
      await refreshResults();
    }
    renderForm(); if(open) loadTurnstile();
  }
  async function submit(event){
    event.preventDefault();
    if(!open || sending || stored(votedKey)==="yes") return;
    if(!$("poll-adult").checked || !$("poll-agree").checked) {
      $("poll-feedback").textContent="Confirmez votre âge et votre compréhension du sondage.";return;
    }
    const answers={};
    for(const q of questions) {
      const radio=document.querySelector('input[name="'+q.id+'"]:checked');
      if(!radio || !VALUES.includes(Number(radio.value))) {
        $("poll-feedback").textContent="Choisissez une réponse ou « Sans opinion / passer » pour chaque proposition.";
        return;
      }
      answers[q.id]=Number(radio.value);
    }
    if(!captchaToken) {$("poll-feedback").textContent="Effectuez la vérification anti-robots.";return;}
    sending=true; updateButton();
    try {
      const response=await fetch(API,{
        method:"POST",mode:"cors",cache:"no-store",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({version:VERSION,ageConfirmed:true,ballotToken:randomToken(),captchaToken,answers})
      });
      const result=await response.json();
      if(response.status===201 && result.status==="accepted") {
        save(votedKey,"yes");
        $("poll-feedback").textContent="Participation prise en compte. Merci. Seuls des totaux seront rendus publics.";
        await refreshResults(); renderForm();
      }else if(response.status===409) {
        save(votedKey,"yes");
        $("poll-feedback").textContent="Un bulletin associé à ce navigateur a déjà été enregistré.";renderForm();
      }else {
        $("poll-feedback").textContent="Votre bulletin n'a pas été confirmé ("+(result.error||"erreur")+"). Vérifiez le service et réessayez.";
      }
    }catch {
      $("poll-feedback").textContent="Connexion indisponible. L'envoi n'a pas été confirmé; vous pouvez réessayer.";
    }finally{
      sending=false;captchaToken="";
      if(window.turnstile && captchaRendered) window.turnstile.reset();
      updateButton();
    }
  }
  document.addEventListener("DOMContentLoaded",()=>{
    $("poll-form").addEventListener("change",updateButton);
    $("poll-form").addEventListener("submit",submit);
    $("poll-refresh").addEventListener("click",refreshResults);
    loadPoll();
  });
})();
