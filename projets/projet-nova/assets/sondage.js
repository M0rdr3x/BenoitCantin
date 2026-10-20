/* Consultation Nova v1.0 : 64 questions figées, 18+ et consentement.
 * Les réponses restent uniquement dans la mémoire du navigateur avant
 * l'envoi volontaire. Aucune écriture ni statistique simulée.
 */
(() => {
  'use strict';
  const SURVEY_ID = 'nova-consultation-64-v1';
  // L'activation nécessite une décision distincte de confidentialité,
  // la migration SQL, l'Edge Function et une validation HTTPS de bout en bout.
  const COLLECTION_OPEN = false;
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
  const selections = new Map();
  let questions = [];
  let step = 0;
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
  function setStatus(text, target = 'sondage-status') {
    $(target).textContent = text;
  }
  function refreshStart() {
    $('sondage-start').disabled = !eligible() || questions.length !== 64;
  }
  function renderQuestion() {
    const question = questions[step];
    $('sondage-position').textContent = 'Question ' + (step + 1) + ' sur ' + questions.length;
    $('sondage-progress').value = step;
    $('sondage-progress').max = questions.length;
    $('sondage-question-heading').textContent = question.text;
    const area = $('sondage-choices');
    area.replaceChildren();
    const existing = selections.get(question.id);
    for (const [value, label] of ANSWERS) {
      const wrapper = document.createElement('label');
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = 'sondage-reponse';
      input.value = value;
      input.checked = existing === value;
      input.addEventListener('change', () => {
        selections.set(question.id, value);
        $('sondage-next').disabled = false;
        setStatus('');
      });
      const text = document.createElement('span');
      text.textContent = label;
      wrapper.append(input, text);
      area.append(wrapper);
    }
    $('sondage-back').disabled = step === 0;
    $('sondage-next').disabled = !selections.has(question.id);
    $('sondage-next').textContent =
      step === questions.length - 1 ? 'Terminer le questionnaire' : 'Suivant';
    setStatus('');
    $('sondage-question-heading').setAttribute('tabindex', '-1');
    $('sondage-question-heading').focus({ preventScroll: true });
  }
  function finish() {
    if (selections.size !== questions.length || !eligible()) {
      setStatus('Toutes les questions nécessitent une réponse ou « Sans opinion ».');
      return;
    }
    $('sondage-questionnaire').hidden = true;
    $('sondage-finish').hidden = false;
    const actual = [...selections.values()].filter(value => value !== 'skip').length;
    $('sondage-recap').textContent = actual + ' réponse(s) d’opinion et ' +
      (questions.length - actual) + ' question(s) passées, sur 64.';
    $('sondage-submit').disabled = !COLLECTION_OPEN;
    setStatus(COLLECTION_OPEN ?
      'Si vous souhaitez participer, confirmez l’envoi avec votre compte connecté.' :
      'Collecte non ouverte : aucune réponse n’a été envoyée. La publication attend la validation de confidentialité.',
      'sondage-submit-status');
    $('sondage-finish-heading').setAttribute('tabindex', '-1');
    $('sondage-finish-heading').focus({ preventScroll: true });
  }
  function payload() {
    if (!eligible() || selections.size !== 64) throw new Error('INCOMPLETE');
    const answers = Object.create(null);
    for (const question of questions) {
      const value = selections.get(question.id);
      if (!ANSWERS.some(item => item[0] === value)) throw new Error('INVALID_ANSWER');
      answers[question.id] = value;
    }
    return {
      survey: SURVEY_ID,
      age18Confirmed: true,
      explicitConsent: true,
      answers
    };
  }
  async function submit() {
    if (!COLLECTION_OPEN || recorded || submitting || !eligible()) return;
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
      if (error || data?.ok !== true) {
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
      $('sondage-submit').disabled = recorded || !COLLECTION_OPEN || !eligible();
    }
  }
  function resetSurvey() {
    // L'effacement local n'est pas un retrait des agrégats d'une soumission déjà enregistrée.
    if (submitting) return;
    if (!window.confirm('Effacer toutes les réponses locales et retirer votre consentement pour cette visite?')) return;
    selections.clear();
    step = 0;
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
    $('sondage-titre').focus();
  }
  async function init() {
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
      if (!selections.has(questions[step].id)) return;
      if (step + 1 === questions.length) finish();
      else { step++; renderQuestion(); }
    });
    $('sondage-back').addEventListener('click', () => {
      if (step > 0) { step--; renderQuestion(); }
    });
    $('sondage-form').addEventListener('submit', e => e.preventDefault());
    $('sondage-review').addEventListener('click', () => {
      if (recorded) return;
      $('sondage-finish').hidden = true;
      $('sondage-questionnaire').hidden = false;
      renderQuestion();
    });
    $('sondage-submit').addEventListener('click', submit);
    for (const id of ['sondage-reset-question', 'sondage-reset-finish']) {
      $(id).addEventListener('click', resetSurvey);
    }
    try {
      const response = await fetch('data/sondage-questions-v1.json',
        { cache: 'no-store', credentials: 'omit' });
      if (!response.ok) throw new Error('HTTP');
      const manifest = await response.json();
      if (!validManifest(manifest)) throw new Error('CONTRACT');
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
