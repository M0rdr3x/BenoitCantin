/* Résultats collectifs publics Nova — jamais les bulletins individuels.
 * Le snapshot public est à l'état not_open tant que #675 n'est pas approuvée.
 */
(() => {
  'use strict';
  const ROOT = 'data/';
  const SNAPSHOT = ROOT + 'resultats-sondages-publics-v1.json';
  // Ces mentions sont gelées tant qu'aucune revue #675 n'autorise la collecte.
  const CLOSED_SOURCE = "aucune enquête enregistrée ou publiée";
  const CLOSED_NOTES = "Aucun résultat de participation réelle n'est disponible. Les choix de démonstration ne sont ni envoyés ni comptabilisés.";
  const CONFIG = {
    '40': {id:'nova-orientations-40-v1', file:ROOT+'consultation-40-v1.json',
      length:40, name:'Sondage référendaire consultatif — 40 questions',
      options:[['pour','Pour'],['contre','Contre'],['sans_opinion','Sans opinion']]},
    '64': {id:'nova-consultation-64-v1', file:ROOT+'sondage-questions-v1.json',
      length:64, name:'Sondage citoyen — 64 propositions',
      options:[['-3','Tout à fait en désaccord'],['-2','En désaccord'],
        ['-1','Plutôt en désaccord'],['0','Ni d’accord ni en désaccord'],
        ['1','Plutôt d’accord'],['2','D’accord'],['3','Tout à fait d’accord'],
        ['skip','Sans opinion']]}
  };
  const $ = id => document.getElementById(id);
  let current = '40';
  let catalog = null;
  let snapshot = null;
  let loadFailed = false;
  // Pas de nouveaux champs publiés sans révision explicite du contrat.
  function exactKeys(obj, keys) {
    return obj !== null && typeof obj === 'object' && !Array.isArray(obj) &&
      Object.keys(obj).length === keys.length &&
      keys.every(key => Object.prototype.hasOwnProperty.call(obj, key));
  }

  function noIdentityFields(obj) {
    const forbidden = /user|person|email|ipaddress|ip_address|hash|token|session|account|identit|device|timestamp|raw.?vote|individual|participant_id/i;
    return obj && typeof obj === 'object' && !Array.isArray(obj) &&
      Object.keys(obj).every(key => !forbidden.test(key));
  }
  function manifestValid(raw, config) {
    return raw && raw.id === config.id && raw.minimumAge === 18 &&
      Array.isArray(raw.questions) && raw.questions.length === config.length &&
      raw.questions.every((q, i) => q && q.id ===
        'q'+String(i+1).padStart(2,'0') && typeof q.text === 'string' && q.text.length >= 20);
  }
  function validSnapshot(data) {
    if (!exactKeys(data, ['schema','publicationStatus','publicationApproved',
        'privacyReviewApproved','surveys','rules','publishedOn','source','notes']) ||
        !noIdentityFields(data) || data.schema !== 'nova-public-results-v1' ||
        !['not_open','approved_aggregate'].includes(data.publicationStatus) ||
        typeof data.publicationApproved !== 'boolean' ||
        typeof data.privacyReviewApproved !== 'boolean' ||
        !exactKeys(data.surveys, Object.values(CONFIG).map(cfg => cfg.id)) ||
        !exactKeys(data.rules, ['minimumParticipants','minimumNonzeroCell','suppression']) ||
        data.rules.minimumParticipants !== 30 ||
        data.rules.minimumNonzeroCell !== 10 ||
        data.rules.suppression !== 'entire-question' ||
        typeof data.source !== 'string' || !data.source.trim() ||
        data.source.length > 400 || typeof data.notes !== 'string' ||
        !data.notes.trim() || data.notes.length > 400) return false;
    if (data.publicationStatus === 'approved_aggregate') {
      if (!data.publicationApproved || !data.privacyReviewApproved ||
          typeof data.publishedOn !== 'string' ||
          !/^\d{4}-\d{2}-\d{2}$/.test(data.publishedOn) ||
          Number.isNaN(Date.parse(data.publishedOn)) ||
          new Date(data.publishedOn).toISOString().slice(0,10) !== data.publishedOn) return false;
    }
    let publishedSurveys = 0;
    for (const cfg of Object.values(CONFIG)) {
      const entry = data.surveys[cfg.id];
      if (!exactKeys(entry, ['status','questionCount','respondents','questions']) ||
          !noIdentityFields(entry) || entry.questionCount !== cfg.length ||
          !['not_open','approved_aggregate'].includes(entry.status) ||
          !Array.isArray(entry.questions)) return false;
      if (entry.status === 'not_open') {
        if (entry.respondents !== null || entry.questions.length !== 0) return false;
      } else {
        publishedSurveys++;
        if (!data.publicationApproved || !data.privacyReviewApproved ||
            data.publicationStatus !== 'approved_aggregate' ||
            !Number.isSafeInteger(entry.respondents) ||
            entry.respondents < 30 || entry.questions.length !== cfg.length) return false;
        const allKeys = cfg.options.map(item => item[0]);
        for (let i=0; i<cfg.length; i++) {
          const row = entry.questions[i];
          if (!noIdentityFields(row) || row.id !== 'q'+String(i+1).padStart(2,'0')) return false;
          if (row.status === 'suppressed') {
            if (!exactKeys(row, ['id','status'])) return false;
            continue;
          }
          if (row.status !== 'published' ||
              !exactKeys(row, ['id','status','total','counts']) ||
              !exactKeys(row.counts, allKeys) || !noIdentityFields(row.counts) ||
              !Number.isSafeInteger(row.total) ||
              row.total !== entry.respondents || row.total < 30) return false;
          const counts=Object.values(row.counts);
          if (!counts.every(n => Number.isSafeInteger(n) && n >= 0 &&
              (n === 0 || n >= 10)) ||
              counts.reduce((a,b)=>a+b,0) !== row.total) return false;
        }
      }
    }
    if (data.publicationStatus === 'not_open' &&
        (data.publicationApproved || data.privacyReviewApproved ||
         data.publishedOn !== null || publishedSurveys !== 0 ||
         data.source !== CLOSED_SOURCE || data.notes !== CLOSED_NOTES)) return false;
    if (data.publicationStatus === 'approved_aggregate' && publishedSurveys === 0) return false;
    return true;
  }
  async function fetchJSON(path) {
    const response=await fetch(path,{cache:'no-store',credentials:'omit'});
    if (!response.ok) throw Error('UNAVAILABLE');
    return response.json();
  }
  function element(tag, className, value) {
    const item=document.createElement(tag);
    if (className) item.className=className;
    if (typeof value === 'string') item.textContent=value;
    return item;
  }
  function render() {
    const cfg=CONFIG[current];
    const list=$('results-question-list');
    list.replaceChildren();
    $('results-survey-title').textContent=cfg.name;
    $('results-show-40').setAttribute('aria-pressed',String(current==='40'));
    $('results-show-64').setAttribute('aria-pressed',String(current==='64'));
    const questions=catalog?.[current]?.questions;
    const results=snapshot?.surveys?.[cfg.id];
    if (loadFailed) {
      $('results-state').textContent =
        'Données publiques indisponibles ou non validées. Aucun résultat affiché.';
      $('results-explainer').textContent =
        'La vérification a échoué : aucun chiffre ne sera présenté tant que les fichiers publics ne sont pas conformes.';
      list.append(element('li','nova-results-unavailable',
        'Résultats et formulations indisponibles pour le moment.'));
      return;
    }
    const approved=!!(snapshot && snapshot.publicationApproved &&
      snapshot.privacyReviewApproved && results?.status === 'approved_aggregate');
    $('results-state').textContent=approved
      ? 'Résultats agrégés approuvés — aucune réponse individuelle publiée.'
      : 'Aucun résultat publié. La collecte des réponses est fermée; aucun vote de démonstration n’est comptabilisé.';
    $('results-explainer').textContent=approved
      ? 'Réponses admissibles par question : '+results.respondents+'. Pourcentages calculés sur ce total.'
      : 'Vous pouvez lire les questions. Les décomptes seront affichés uniquement après autorisation de collecte et contrôle de confidentialité.';
    if (!Array.isArray(questions)) {
      list.append(element('li','nova-results-empty','Les formulations ne sont pas disponibles pour le moment.'));
      return;
    }
    questions.forEach((q,index)=>{
      const li=element('li','nova-results-item');
      li.append(element('h4','',q.text));
      if (!approved) {
        li.append(element('p','nova-results-unavailable','Aucun résultat publié.'));
      } else {
        const row=results.questions[index];
        if (row.status === 'suppressed') {
          li.append(element('p','nova-results-unavailable',
            'Répartition masquée : effectif insuffisant pour protéger les répondants.'));
          list.append(li);
          return;
        }
        cfg.options.forEach(([key,label])=>{
          const value=row.counts[key];
          const percentage=100*value/row.total;
          const wrapper=element('div','nova-results-bar-item');
          wrapper.append(element('span','',label+' — '+value+' ('+percentage.toFixed(1).replace('.',',')+' %)'));
          const meter=element('div','nova-results-meter');
          meter.setAttribute('role','img');
          meter.setAttribute('aria-label',label+' : '+percentage.toFixed(1)+' pour cent');
          const fill=element('span','nova-results-fill');
          fill.style.width=percentage.toFixed(1)+'%';
          meter.append(fill);
          wrapper.append(meter);
          li.append(wrapper);
        });
      }
      list.append(li);
    });
  }
  async function init() {
    $('results-show-40').addEventListener('click',()=>{current='40';render()});
    $('results-show-64').addEventListener('click',()=>{current='64';render()});
    try {
      const [a,b,publicData]=await Promise.all([
        fetchJSON(CONFIG['40'].file),fetchJSON(CONFIG['64'].file),fetchJSON(SNAPSHOT)]);
      if (!manifestValid(a,CONFIG['40']) || !manifestValid(b,CONFIG['64']) ||
          !validSnapshot(publicData)) throw Error('INVALID_PUBLICATION');
      catalog={'40':a,'64':b};
      snapshot=publicData;
    } catch {
      loadFailed = true;
      catalog = null;
      snapshot = null;
    }
    render();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();