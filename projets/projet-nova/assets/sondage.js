/* Consultation Nova v1.0 : 64 questions figées, 18+ et consentement.
 * Les réponses restent uniquement dans la mémoire du navigateur avant
 * l'envoi volontaire. Aucune écriture ni statistique simulée.
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

  const SURVEY_ID = 'nova-consultation-64-v1';
  // Empreinte approuvée des octets du questionnaire 64 questions (UTF-8).
  // Un JSON modifié dans un cache/CDN est refusé avant tout affichage.
  const APPROVED_MANIFEST_SHA256 = '67df5052a3a09f23ecfa43e2882dcf7a0b6f1a85f1aad4e2f4159aab06570738';
  const APPROVED_COMPASS_SHA256 = '5d65a6067142fbba59a81edeaac49dc1befd82aa281c6e11e2f2509a1aee9109';
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
    // Retirer l'accord ou l'attestation 18+ pendant une démonstration
    // supprime immédiatement les choix sensibles encore en mémoire.
    if (!eligible() && !COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED &&
        (!$('sondage-questionnaire').hidden || !$('sondage-finish').hidden)) {
      clearLocalDemo();
      $('sondage-titre').focus({preventScroll:true});
      return;
    }
    $('sondage-start').disabled = !eligible() || questions.length !== 64;
  }
  function renderQuestion() {
    if (!eligible() || questions.length !== 64 || step < 0 || step >= 64) return;
    const question = questions[step];
    $('sondage-position').textContent = 'Question ' + (step + 1) + ' sur ' + questions.length;
    $('sondage-progress').value = step + 1;
    $('sondage-progress').max = questions.length;
    $('sondage-answered').textContent = selections.size + ' question(s) avec un choix sur 64';
    $('sondage-question-heading').querySelector('[data-sondage-question-focus]').textContent = question.text;
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
    // Firefox ne garantit pas focus() sur <legend> : cibler l'enfant focalisable.
    $('sondage-question-heading').querySelector('[data-sondage-question-focus]').focus({ preventScroll: true });
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
    // Supprimer immédiatement les opinions lorsqu'on quitte la page :
    // un onglet placé en cache arrière/avant ne doit pas conserver la démo.
    window.addEventListener('pagehide', () => {
      if (!COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED) clearLocalDemo();
    });
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
    // Éviter un écran de démarrage bloqué si l'un des deux corpus n'arrive pas.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    try {
      const [response, compassResponse] = await Promise.all([
        fetch('data/sondage-questions-v1.json', { cache: 'no-store', credentials: 'omit', signal: controller.signal }),
        fetch('data/boussole-electorale-v2.json', { cache: 'no-store', credentials: 'omit', signal: controller.signal }),
      ]);
      if (!response.ok || !compassResponse.ok) throw new Error('HTTP');
      // Même exigence d'intégrité que la consultation de 40 questions.
      // Aucune tolérance silencieuse si Web Crypto n'est pas disponible.
      if (!globalThis.crypto?.subtle) throw new Error('NO_CRYPTO');
      const [manifestBytes,compassBytes] = await Promise.all([
        readBoundedManifest(response,controller),
        readBoundedManifest(compassResponse,controller)
      ]);
      const [digest,compassDigest]=await Promise.all([
        globalThis.crypto.subtle.digest('SHA-256', manifestBytes),
        globalThis.crypto.subtle.digest('SHA-256',compassBytes)
      ]);
      const hex = bytes => Array.from(new Uint8Array(bytes),
        byte=>byte.toString(16).padStart(2,'0')).join('');
      const observed=hex(digest);
      if(observed !== APPROVED_MANIFEST_SHA256 ||
         hex(compassDigest)!==APPROVED_COMPASS_SHA256) throw new Error('CORPUS_INTEGRITY');
      const decoder=new TextDecoder('utf-8', { fatal: true });
      const manifest=JSON.parse(decoder.decode(manifestBytes));
      const compass=JSON.parse(decoder.decode(compassBytes));
      if (!validManifest(manifest) || !sameSourceQuestions(manifest,compass)) throw new Error('CONTRACT');
      questions = manifest.questions;
      // Le chargement des deux corpus et leurs empreintes sont confirmés.
      $('sondage-start').dataset.ready = 'true';
      refreshStart();
    } catch {
      $('sondage-start').disabled = true;
      const warning = document.createElement('p');
      warning.setAttribute('role','alert');
      warning.textContent = 'Les questions ne sont pas disponibles actuellement. Aucun renseignement n’a été envoyé.';
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'btn btn-outline';
      retry.id = 'sondage-retry';
      retry.textContent = 'Réessayer le chargement des questions';
      retry.addEventListener('click', () => window.location.reload());
      $('sondage-introduction').append(warning, retry);
    } finally {
      clearTimeout(timeoutId);
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
