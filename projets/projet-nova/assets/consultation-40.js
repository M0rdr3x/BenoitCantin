/* Projet Nova — consultation civique, référendaire et orientations (40 questions).
 * Parcours non officiel, sans enregistrement ni stockage navigateur avant autorisation.
 * Le corpus approuvé et son ordre restent intégralement dans consultation-40-v1.json.
 */
(() => {
  'use strict';
  // Appliquer la borne avant d'allouer le JSON complet; SHA-256 reste sur les octets exacts.
  async function readBoundedManifest(response,controller){
    const declared=response.headers.get('content-length');
    if(declared!==null && (!/^[0-9]+$/.test(declared) || Number(declared)>65536)) throw Error('SIZE');
    if(!response.body?.getReader) throw Error('STREAM');
    const reader=response.body.getReader();
    const chunks=[];
    let total=0;
    try{
      for(;;){
        const {done,value}=await reader.read();
        if(done) break;
        if(!ArrayBuffer.isView(value)||value.BYTES_PER_ELEMENT!==1) throw Error('STREAM');
        total+=value.byteLength;
        if(total>65536){controller.abort();throw Error('SIZE');}
        chunks.push(value);
      }
    }finally{reader.releaseLock();}
    if(!total) throw Error('SIZE');
    const result=new Uint8Array(total);
    let offset=0;
    for(const part of chunks){result.set(part,offset);offset+=part.byteLength;}
    return result.buffer;
  }

  // Empreinte SHA-256 du questionnaire officiel figé 40 questions.
  // Empêche un CDN/cache modifié d'afficher une autre formulation aux visiteurs.
  const APPROVED_MANIFEST_SHA256 = '5eece3aacaff678fd6f514d2ca5c4a158da9afb2dd3c5d6fb3c7849ac2cecfac';
  // La case d'accord de démonstration n'autorise PAS une collecte future.
  // Avant toute activation : nouvel avis, nouveau consentement explicite et revue #675.
  const COLLECTION_OPEN = false;
  // Verrou indépendant : l'accord de démonstration ne constitue pas le consentement au traitement.
  // Une activation future exige un parcours de consentement nouveau, dédié et approuvé (#675).
  const LIVE_OPINION_CONSENT_GRANTED = false;
  const SURVEY_ID = 'nova-orientations-40-v1';
  const $ = id => document.getElementById(id);
  const answers = new Map();
  let questions = [];
  let step = 0;
  let editingReview = false;
  let submitting = false;
  let recorded = false;
  const options = [
    ['pour', 'Pour'],
    ['contre', 'Contre'],
    ['sans_opinion', 'Sans opinion']
  ];
  const allowed = new Set(options.map(([id]) => id));
  const choiceNames = new Map(options);
  const eligible = () => $('sondage-age').checked && $('sondage-consent').checked;

  function show(which) {
    $('sondage-introduction').hidden = which !== 'introduction';
    $('sondage-questionnaire').hidden = which !== 'questionnaire';
    $('sondage-finish').hidden = which !== 'finish';
  }
  function refresh() {
    // Un retrait de l'accord ou de l'attestation d'âge en cours de parcours
    // efface aussitôt toute opinion locale, sans attendre la navigation.
    if (!eligible() && !COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED &&
        (!$('sondage-questionnaire').hidden || !$('sondage-finish').hidden)) {
      clearLocalDemo();
      $('sondage-titre').focus({preventScroll:true});
      return;
    }
    $('sondage-start').disabled = !eligible() || questions.length !== 40;
  }
  function render() {
    if (!eligible() || questions.length !== 40 || step < 0 || step >= 40) return;
    const item = questions[step];
    $('sondage-position').textContent = 'Question ' + (step + 1) + ' sur 40 · ' + item.topic;
    $('sondage-answered').textContent = answers.size + ' question(s) avec un choix sur 40';
    $('sondage-progress').value = step + 1;
    $('sondage-progress').max = 40;
    $('sondage-question-heading').textContent = item.text;
    $('sondage-context').textContent = step === 0
      ? 'Question de consultation sur une éventuelle indépendance : cette réponse ne constitue pas un vote référendaire officiel.'
      : 'Proposition de politique publique : choisissez librement, y compris « Sans opinion ».';
    const choices = $('sondage-choices');
    choices.replaceChildren();
    for (const [choice, label] of options) {
      const wrapper = document.createElement('label');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'nova40-response';
      radio.autocomplete = 'off';
      radio.value = choice;
      radio.checked = answers.get(item.id) === choice;
      radio.addEventListener('change', () => {
        answers.set(item.id, choice);
        $('sondage-next').disabled = false;
        $('sondage-answered').textContent = answers.size + ' question(s) avec un choix sur 40';
        $('sondage-status').textContent = '';
      });
      const span = document.createElement('span');
      span.textContent = label;
      wrapper.append(radio, span);
      choices.append(wrapper);
    }
    $('sondage-back').disabled = !editingReview && step === 0;
    $('sondage-back').textContent = editingReview ? 'Retour au récapitulatif' : 'Précédent';
    $('sondage-next').disabled = !answers.has(item.id);
    $('sondage-next').textContent = editingReview ? 'Enregistrer la modification'
      : (step === 39 ? 'Voir le récapitulatif' : 'Suivant');
    $('sondage-question-heading').setAttribute('tabindex', '-1');
    $('sondage-question-heading').focus({ preventScroll: true });
  }
  function complete() {
    if (!eligible() || questions.length !== 40 || answers.size!==40) return;
    editingReview = false;
    show('finish');
    const withoutOpinion = [...answers.values()].filter(value => value === 'sans_opinion').length;
    $('sondage-recap').textContent = '40 choix effectués : ' +
      (40 - withoutOpinion) + ' réponses Pour/Contre et ' + withoutOpinion +
      ' réponse(s) « Sans opinion ». Aucune donnée transmise.';
    const list = $('sondage-review-list');
    list.replaceChildren();
    questions.forEach((item, i) => {
      const li = document.createElement('li');
      const detail = document.createElement('div');
      const heading = document.createElement('strong');
      heading.textContent = 'Question ' + (i + 1) + ' — ' + item.topic;
      const questionText = document.createElement('p');
      questionText.textContent = item.text;
      const response = document.createElement('p');
      response.className = 'nova-survey-review-choice';
      response.textContent = 'Votre choix : ' + choiceNames.get(answers.get(item.id));
      detail.append(heading, questionText, response);
      const modify = document.createElement('button');
      modify.type = 'button';
      modify.className = 'btn btn-outline nova-survey-review-edit';
      modify.textContent = 'Modifier';
      modify.setAttribute('aria-label', 'Modifier la réponse à la question ' + (i + 1));
      modify.addEventListener('click', () => {
        step = i;
        editingReview = true;
        show('questionnaire');
        render();
      });
      li.append(detail, modify);
      list.append(li);
    });
    $('sondage-submit').disabled=true;
    $('sondage-submit-status').textContent =
      'Collecte fermée : aucune réponse enregistrée. Une ouverture distincte exige une validation de confidentialité et une approbation.';
    $('sondage-finish-heading').setAttribute('tabindex', '-1');
    $('sondage-finish-heading').focus({ preventScroll: true });
  }
  function clearLocalDemo() {
    // Même un retour depuis le cache arrière/avant ne rétablit ni âge ni opinions.
    answers.clear();
    step = 0;
    editingReview = false;
    submitting = false;
    $('sondage-age').checked = false;
    $('sondage-consent').checked = false;
    $('sondage-review-list').replaceChildren();
    $('sondage-status').textContent = '';
    $('sondage-submit-status').textContent = '';
    show('introduction');
    $('sondage-choices').replaceChildren();
    $('sondage-next').disabled = true;
    refresh();
  }
  function resetSurvey() {
    if (!window.confirm('Effacer tous vos choix et recommencer ce questionnaire?')) return;
    clearLocalDemo();
    $('sondage-titre').focus();
  }
  function init() {
    clearLocalDemo();
    // pageshow se déclenche même lorsqu'un navigateur restaure un formulaire après DOMContentLoaded.
    // Supprimer immédiatement les opinions lorsqu'on quitte la page :
    // un onglet placé en cache arrière/avant ne doit pas conserver la démo.
    window.addEventListener('pagehide', () => {
      if (!COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED) clearLocalDemo();
    });
    window.addEventListener('pageshow', () => {
      if (!COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED) clearLocalDemo();
    });
    for (const id of ['sondage-age', 'sondage-consent']) {
      $(id).addEventListener('change', refresh);
    }
    $('sondage-start').addEventListener('click', () => {
      if (!eligible() || questions.length !== 40) return;
      show('questionnaire');
      render();
    });
    $('sondage-next').addEventListener('click', () => {
      if (!eligible() || !questions[step] || !answers.has(questions[step].id)) return;
      if (editingReview || step === 39) complete();
      else { step++; render(); }
    });
    $('sondage-back').addEventListener('click', () => {
      if (editingReview) complete();
      else if (step > 0) { step--; render(); }
    });
    $('sondage-review').addEventListener('click', () => {
      step = 0;
      editingReview = false;
      show('questionnaire');
      render();
    });
    for (const id of ['sondage-reset-question', 'sondage-reset-finish']) {
      $(id).addEventListener('click', resetSurvey);
    }
    $('sondage-form').addEventListener('submit', e => e.preventDefault());
    $('sondage-submit').addEventListener('click', async () => {
      if (!COLLECTION_OPEN || !LIVE_OPINION_CONSENT_GRANTED || !eligible() || answers.size!==40 || submitting || recorded) return;
      const payload = { survey: SURVEY_ID, age18Confirmed:true,
        explicitConsent:LIVE_OPINION_CONSENT_GRANTED, answers:Object.fromEntries(answers) };
      if (Object.keys(payload.answers).length !== 40 ||
          !Object.values(payload.answers).every(value => allowed.has(value))) return;
      submitting = true;
      $('sondage-submit').disabled = true;
      $('sondage-submit-status').textContent = 'Transmission en cours…';
      try {
        const { getSupabase } = await import('../../../assets/js/sinjira-supabase.js');
        const client = getSupabase();
        const { data:auth, error:authError } = await client.auth.getUser();
        if (authError || !auth?.user) {
          $('sondage-submit-status').textContent = 'Un compte connecté est nécessaire.';
          return;
        }
        const { data, error } = await client.functions.invoke('nova-consultation40-submit', { body:payload });
        if (!error && data?.ok === true && data.code === 'RECORDED' && data.survey === SURVEY_ID) {
          recorded = true;
          $('sondage-submit-status').textContent = 'Participation enregistrée. Merci.';
        } else {
          let code = data?.code;
          if (error?.context?.json) { try { code = (await error.context.json()).code; } catch {} }
          if (code === 'ALREADY_SUBMITTED') {
            recorded = true;
            $('sondage-submit-status').textContent = 'Une participation existe déjà pour ce compte.';
          } else {
            $('sondage-submit-status').textContent = 'Enregistrement non confirmé. Aucun résultat affiché.';
          }
        }
      } catch {
        $('sondage-submit-status').textContent = 'Service temporairement indisponible.';
      } finally {
        submitting = false;
        $('sondage-submit').disabled = recorded || !COLLECTION_OPEN || !LIVE_OPINION_CONSENT_GRANTED || !eligible();
      }
    });
    // Une connexion qui ne répond jamais doit revenir à un état bloqué lisible.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    fetch('data/consultation-40-v1.json', {
      cache:'no-store', credentials:'omit', signal:controller.signal
    })
      .then(async r => {
        if (!r.ok) throw Error('HTTP');
        // La vérification est faite sur les octets bruts, AVANT JSON.parse.
        // Le mode non sécurisé (crypto.subtle absent) doit échouer fermé.
        if (!globalThis.crypto?.subtle) throw Error('NO_CRYPTO');
        const manifestBytes = await readBoundedManifest(r,controller);
        const hash = await crypto.subtle.digest('SHA-256', manifestBytes);
        const actual = Array.from(new Uint8Array(hash),
          value => value.toString(16).padStart(2, '0')).join('');
        if (actual !== APPROVED_MANIFEST_SHA256) throw Error('MANIFEST_INTEGRITY');
        return JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(manifestBytes));
      })
      .then(data => {
        if (data.id !== SURVEY_ID || data.version !== '1.0.0' ||
            data.type !== 'consultation_volontaire_non_representative' ||
            data.minimumAge !== 18 ||
            !Array.isArray(data.questions) || data.questions.length!==40 ||
            data.collectionOpen !== false) throw Error('MANIFEST');
        const ids = new Set();
        for (let i = 0; i < 40; i++) {
          const q = data.questions[i], id = 'q' + String(i + 1).padStart(2, '0');
          if (!q || q.id !== id || ids.has(q.id) ||
              typeof q.text !== 'string' || q.text.length < 35 ||
              typeof q.topic !== 'string') throw Error('QUESTION');
          ids.add(q.id);
        }
        if (!Array.isArray(data.choices) || data.choices.length !== 3 ||
            data.choices.join(',') !== 'pour,contre,sans_opinion') throw Error('CHOIX');
        questions = data.questions;
        refresh();
      }).catch(() => {
        $('sondage-start').disabled = true;
        const message = document.createElement('p');
        message.setAttribute('role', 'alert');
        message.textContent = 'Questions indisponibles : le sondage ne peut pas démarrer. Aucun choix n’a été transmis.';
        const retry = document.createElement('button');
        retry.type = 'button';
        retry.className = 'btn btn-outline';
        retry.id = 'sondage-retry';
        retry.textContent = 'Réessayer le chargement des questions';
        retry.addEventListener('click', () => window.location.reload());
        $('sondage-introduction').append(message, retry);
      }).finally(() => clearTimeout(timeoutId));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
