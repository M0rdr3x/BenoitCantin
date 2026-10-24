/* Consultation Nova v1.0 : 64 questions figées, 18+ et consentement.
 * Les réponses restent uniquement dans la mémoire du navigateur avant
 * l'envoi volontaire. Aucune écriture ni statistique simulée.
 */
(() => {
  'use strict';
  const SURVEY_ID = 'nova-consultation-64-v1';
  // L'activation nécessite une décision distincte de confidentialité,
  // la migration SQL, l'Edge Function et une validation HTTPS de bout en bout.
  // L'accord de démonstration ne vaut PAS consentement à la collecte d'opinions.
  // Avant toute activation : nouvel avis, nouveau consentement et revue #675.
  const COLLECTION_OPEN = false;
  // Verrou indépendant : la case de démonstration ne vaut aucun consentement à la collecte.
  // Ne modifier qu'après ajout et revue d'un consentement réel et distinct (#675).
  const LIVE_OPINION_CONSENT_GRANTED = false;
  const ANSWERS = [
    ['-3', 'Tout à fait en désaccord'],
    ['-2', 'En désaccord'],
    ['-1', 'Plutôt en désaccord'],
    ['0', 'Ni d’accord ni en désaccord'],
    ['1', 'Plutôt d’accord'],
    ['2', 'D’accord'],
    ['3', 'Tout à fait d’accord'],
    ['skip', 'Sans opinion / passer cette question']
  ];
  const $ = id => document.getElementById(id);
  const choiceNames = new Map(ANSWERS);
  const selections = new Map();
  let questions = [];
  let step = 0;
  let editingReview = false;
  let submitting = false;
  let recorded = false;

  function eligible() {
    return $('sondage-age').checked && $('sondage-consent').checked;
  }
  function validManifest(data) {
    if (!data || data.id !== SURVEY_ID || data.minimumAge !== 18 ||
        !Array.isArray(data.questions) || data.questions.length !== 64 ||
        data.sourceVersion !== '2.2.0') return false;
    const seen = new Set();
    return data.questions.every((q, index) => {
      const expected = 'q' + String(index + 1).padStart(2, '0');
      if (!q || q.id !== expected || seen.has(q.id) ||
          typeof q.text !== 'string' || q.text.trim().length < 30) return false;
      seen.add(q.id);
      return true;
    });
  }
  function sameSourceQuestions(survey, compass) {
    return compass && compass.version === survey.sourceVersion &&
      Array.isArray(compass.questions) && compass.questions.length === 64 &&
      survey.questions.every((q,i) => q.id === compass.questions[i]?.id &&
        q.axis === compass.questions[i]?.axis &&
        q.text === compass.questions[i]?.text);
  }
  function setStatus(text, target = 'sondage-status') {
    $(target).textContent = text;
  }
  function refreshStart() {
    $('sondage-start').disabled = !eligible() || questions.length !== 64;
  }
  function renderQuestion() {
    if (!eligible() || questions.length !== 64 || step < 0 || step >= 64) return;
    const question = questions[step];
    $('sondage-position').textContent = 'Question ' + (step + 1) + ' sur ' + questions.length;
    $('sondage-progress').value = step + 1;
    $('sondage-progress').max = questions.length;
    $('sondage-answered').textContent = selections.size + ' question(s) avec un choix sur 64';
    $('sondage-question-heading').textContent = question.text;
    const area = $('sondage-choices');
    area.replaceChildren();
    const existing = selections.get(question.id);
    for (const [value, label] of ANSWERS) {
      const wrapper = document.createElement('label');
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = 'sondage-reponse';
      input.autocomplete = 'off';
      input.value = value;
      input.checked = existing === value;
      input.addEventListener('change', () => {
        selections.set(question.id, value);
        $('sondage-answered').textContent = selections.size + ' question(s) avec un choix sur 64';
        $('sondage-next').disabled = false;
        setStatus('');
      });
      const text = document.createElement('span');
      text.textContent = label;
      wrapper.append(input, text);
      area.append(wrapper);
    }
    $('sondage-back').disabled = !editingReview && step === 0;
    $('sondage-back').textContent = editingReview ? 'Retour au récapitulatif' : 'Précédent';
    $('sondage-next').disabled = !selections.has(question.id);
    $('sondage-next').textContent = editingReview ? 'Enregistrer la modification' :
      (step === questions.length - 1 ? 'Voir le récapitulatif' : 'Suivant');
    setStatus('');
    $('sondage-question-heading').setAttribute('tabindex', '-1');
    $('sondage-question-heading').focus({ preventScroll: true });
  }
  function finish() {
    if (selections.size !== questions.length || !eligible()) {
      setStatus('Toutes les questions nécessitent une réponse ou « Sans opinion ».');
      return;
    }
    editingReview = false;
    $('sondage-questionnaire').hidden = true;
    $('sondage-finish').hidden = false;
    const actual = [...selections.values()].filter(value => value !== 'skip').length;
    $('sondage-recap').textContent = actual + ' réponse(s) d’opinion et ' +
      (questions.length - actual) + ' question(s) « Sans opinion », sur 64. Aucune donnée transmise.';
    const list = $('sondage-review-list');
    list.replaceChildren();
    questions.forEach((question, index) => {
      const li = document.createElement('li');
      const detail = document.createElement('div');
      const heading = document.createElement('strong');
      heading.textContent = 'Question ' + (index + 1);
      const questionText = document.createElement('p');
      questionText.textContent = question.text;
      const answer = document.createElement('p');
      answer.className = 'nova-survey-review-choice';
      answer.textContent = 'Votre choix : ' + choiceNames.get(selections.get(question.id));
      detail.append(heading, questionText, answer);
      const edit = document.createElement('button');
      edit.type = 'button';
      edit.className = 'btn btn-outline nova-survey-review-edit';
      edit.textContent = 'Modifier';
      edit.setAttribute('aria-label', 'Modifier la réponse à la question ' + (index + 1));
      edit.addEventListener('click', () => {
        if (recorded || !eligible()) return;
        step = index;
        editingReview = true;
        $('sondage-finish').hidden = true;
        $('sondage-questionnaire').hidden = false;
        renderQuestion();
      });
      li.append(detail, edit);
      list.append(li);
    });
    $('sondage-submit').disabled = !COLLECTION_OPEN || !LIVE_OPINION_CONSENT_GRANTED || recorded;
    setStatus(COLLECTION_OPEN && LIVE_OPINION_CONSENT_GRANTED ?
      'Si vous souhaitez participer, confirmez l’envoi avec votre compte connecté.' :
      'Collecte non ouverte : aucune réponse n’a été envoyée. La publication attend la validation de confidentialité.',
      'sondage-submit-status');
    $('sondage-finish-heading').setAttribute('tabindex', '-1');
    $('sondage-finish-heading').focus({ preventScroll: true });
  }
  function payload() {
    if (!eligible() || selections.size !== 64) throw new Error('INCOMPLETE');
    if (!LIVE_OPINION_CONSENT_GRANTED) throw new Error('LIVE_CONSENT_REQUIRED');
    const answers = Object.create(null);
    for (const question of questions) {
      const value = selections.get(question.id);
      if (!ANSWERS.some(item => item[0] === value)) throw new Error('INVALID_ANSWER');
      answers[question.id] = value;
    }
    return {
      survey: SURVEY_ID,
      age18Confirmed: true,
      explicitConsent: LIVE_OPINION_CONSENT_GRANTED,
      answers
    };
  }
  async function submit() {
    if (!COLLECTION_OPEN || !LIVE_OPINION_CONSENT_GRANTED || recorded || submitting || !eligible()) return;
    let request;
    try { request = payload(); }
    catch { setStatus('Questionnaire incomplet ou admissibilité non confirmée.', 'sondage-submit-status'); return; }
    submitting = true;
    $('sondage-submit').disabled = true;
    setStatus('Transmission sécurisée en cours…', 'sondage-submit-status');
    try {
      const { getSupabase } = await import('../../../assets/js/sinjira-supabase.js');
      const client = getSupabase();
      const { data: profile, error: authError } = await client.auth.getUser();
      if (authError || !profile?.user) {
        setStatus('Connectez-vous à votre compte avant de transmettre votre participation.',
          'sondage-submit-status');
        return;
      }
      const { data, error } = await client.functions.invoke('nova-survey-submit',
        { body: request });
      if (error || data?.ok !== true || data.code !== 'RECORDED' || data.survey !== SURVEY_ID) {
        let code = data?.code;
        if (error?.context && typeof error.context.json === 'function') {
          try { code = (await error.context.json()).code; } catch { /* réponse réseau indisponible */ }
        }
        if (code === 'ALREADY_SUBMITTED') {
          recorded = true;
          setStatus('Une participation est déjà enregistrée pour ce compte. Aucun doublon ajouté.',
            'sondage-submit-status');
        } else if (code === 'COLLECTION_NOT_ENABLED') {
          setStatus('La collecte n’est pas encore ouverte. Rien n’a été enregistré.',
            'sondage-submit-status');
        } else {
          setStatus('Envoi non confirmé : vos réponses restent dans cette page. Réessayez si la collecte est ouverte.',
            'sondage-submit-status');
        }
        return;
      }
      recorded = true;
      setStatus('Participation enregistrée. Merci! Les résultats ne seront diffusés que sous forme agrégée et accompagnés de la méthode.',
        'sondage-submit-status');
    } catch {
      setStatus('Service indisponible : aucune confirmation d’enregistrement. Les réponses restent sur cette page.',
        'sondage-submit-status');
    } finally {
      submitting = false;
      $('sondage-submit').disabled = recorded || !COLLECTION_OPEN || !LIVE_OPINION_CONSENT_GRANTED || !eligible();
    }
  }
  function clearLocalDemo() {
    // Ne conserver ni opinions ni confirmation 18+ après retour d'historique/rechargement.
    selections.clear();
    step = 0;
    editingReview = false;
    $('sondage-review-list').replaceChildren();
    $('sondage-age').checked = false;
    $('sondage-consent').checked = false;
    $('sondage-questionnaire').hidden = true;
    $('sondage-finish').hidden = true;
    $('sondage-introduction').hidden = false;
    $('sondage-choices').replaceChildren();
    $('sondage-next').disabled = true;
    setStatus('');
    setStatus('', 'sondage-submit-status');
    refreshStart();
  }
  function resetSurvey() {
    // Effacer les choix locaux ne retire pas une contribution déjà agrégée.
    if (submitting) return;
    if (!window.confirm('Effacer toutes les réponses locales et retirer votre consentement pour cette visite?')) return;
    clearLocalDemo();
    $('sondage-titre').focus();
  }
  async function init() {
    clearLocalDemo();
    // Les navigateurs peuvent restaurer des cases cochées après DOMContentLoaded.
    window.addEventListener('pageshow', () => {
      if (!COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED) clearLocalDemo();
    });
    for (const id of ['sondage-age', 'sondage-consent']) {
      $(id).addEventListener('change', refreshStart);
    }
    $('sondage-start').addEventListener('click', () => {
      if (!eligible() || questions.length !== 64) return;
      $('sondage-introduction').hidden = true;
      $('sondage-questionnaire').hidden = false;
      renderQuestion();
    });
    $('sondage-next').addEventListener('click', () => {
      if (!eligible() || !questions[step] || !selections.has(questions[step].id)) return;
      if (editingReview || step + 1 === questions.length) finish();
      else { step++; renderQuestion(); }
    });
    $('sondage-back').addEventListener('click', () => {
      if (editingReview) finish();
      else if (step > 0) { step--; renderQuestion(); }
    });
    $('sondage-form').addEventListener('submit', e => e.preventDefault());
    $('sondage-review').addEventListener('click', () => {
      if (recorded) return;
      if (!eligible()) return;
      step = 0;
      editingReview = false;
      $('sondage-finish').hidden = true;
      $('sondage-questionnaire').hidden = false;
      renderQuestion();
    });
    $('sondage-submit').addEventListener('click', submit);
    for (const id of ['sondage-reset-question', 'sondage-reset-finish']) {
      $(id).addEventListener('click', resetSurvey);
    }
    try {
      const [response, compassResponse] = await Promise.all([
        fetch('data/sondage-questions-v1.json', { cache: 'no-store', credentials: 'omit' }),
        fetch('data/boussole-electorale-v2.json', { cache: 'no-store', credentials: 'omit' }),
      ]);
      if (!response.ok || !compassResponse.ok) throw new Error('HTTP');
      const [manifest, compass] = await Promise.all([response.json(), compassResponse.json()]);
      if (!validManifest(manifest) || !sameSourceQuestions(manifest,compass)) throw new Error('CONTRACT');
      questions = manifest.questions;
      refreshStart();
    } catch {
      $('sondage-start').disabled = true;
      const warning = document.createElement('p');
      warning.setAttribute('role','alert');
      warning.textContent = 'Les questions ne sont pas disponibles actuellement. Aucun renseignement n’a été envoyé.';
      $('sondage-introduction').append(warning);
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
