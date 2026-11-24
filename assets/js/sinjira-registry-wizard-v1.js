/* SINJIRA — Questionnaire du Registre, navigation progressive et privée.
 * Ne persiste aucune réponse, ne modifie ni payload ni les règles Auth/AAL2.
 */
(function () {
  'use strict';

  var form = document.querySelector('form[data-character-form]');
  if (!form || typeof HTMLFieldSetElement === 'undefined') return;

  var steps = Array.from(form.querySelectorAll(':scope > fieldset.v24-fieldset'));
  var consent = Array.from(form.querySelectorAll(':scope > label.account-check'));
  var submit = form.querySelector(':scope > button[type="submit"]');
  var legal = form.querySelector(':scope > p.legal-note');
  if (steps.length !== 9 || consent.length !== 2 || !submit || !legal) return;

  var header = document.createElement('div');
  header.className = 'registry-wizard-header';
  header.dataset.registryWizard = '';
  header.setAttribute('aria-label', 'Progression du questionnaire');

  var title = document.createElement('p');
  title.className = 'registry-wizard-step';
  title.id = 'registry-wizard-stage';
  title.setAttribute('role', 'status');
  title.setAttribute('aria-live', 'polite');

  var progress = document.createElement('progress');
  progress.className = 'registry-wizard-progress';
  progress.max = steps.length;
  progress.value = 1;
  progress.setAttribute('aria-labelledby', title.id);

  var intro = document.createElement('p');
  intro.className = 'registry-wizard-hint';
  intro.textContent = 'Les réponses restent sur cette page jusqu’à votre envoi sécurisé. Rien n’est enregistré dans le navigateur par ce parcours.';

  header.appendChild(title);
  header.appendChild(progress);
  header.appendChild(intro);
  form.insertBefore(header, steps[0]);

  var controls = document.createElement('nav');
  controls.className = 'registry-wizard-controls';
  controls.setAttribute('aria-label', 'Navigation du questionnaire');

  var back = document.createElement('button');
  back.type = 'button';
  back.dataset.registryWizardBack = '';
  back.className = 'btn btn-secondary';
  back.textContent = 'Étape précédente';

  var next = document.createElement('button');
  next.type = 'button';
  next.dataset.registryWizardNext = '';
  next.className = 'btn btn-primary';
  next.textContent = 'Étape suivante';

  var message = document.createElement('p');
  message.className = 'registry-wizard-error';
  message.dataset.registryWizardError = '';
  message.setAttribute('role', 'alert');
  message.hidden = true;

  controls.appendChild(back);
  controls.appendChild(next);
  steps[steps.length - 1].insertAdjacentElement('afterend', controls);
  controls.insertAdjacentElement('afterend', message);

  var current = 0;
  var invalidQueued = false;
  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  steps.forEach(function (fieldset, i) {
    var legend = fieldset.querySelector(':scope > legend');
    fieldset.dataset.registryWizardStep = String(i + 1);
    if (legend) legend.setAttribute('tabindex', '-1');
  });

  function show(index, moveFocus) {
    current = Math.max(0, Math.min(steps.length - 1, index));
    steps.forEach(function (fieldset, i) {
      fieldset.hidden = i !== current;
    });
    var last = current === steps.length - 1;
    consent.forEach(function (label) { label.hidden = !last; });
    submit.hidden = !last;
    legal.hidden = !last;
    back.hidden = current === 0;
    next.hidden = last;
    title.textContent = 'Étape ' + (current + 1) + ' sur ' + steps.length +
      ' — ' + ((steps[current].querySelector('legend') || {}).textContent || '').trim();
    progress.value = current + 1;
    message.hidden = true;
    message.textContent = '';

    if (moveFocus) {
      var legend = steps[current].querySelector(':scope > legend');
      if (legend) {
        try { legend.focus({ preventScroll: true }); }
        catch (_) { legend.focus(); }
      }
      header.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    }
  }

  function refuse(text, field) {
    message.textContent = text;
    message.hidden = false;
    if (field) {
      field.focus();
      if (typeof field.reportValidity === 'function') field.reportValidity();
    }
  }

  function validateCurrent() {
    var invalid = Array.from(steps[current].querySelectorAll('input,select,textarea'))
      .find(function (field) { return !field.disabled && !field.checkValidity(); });
    if (invalid) {
      refuse('Veuillez remplir les champs obligatoires de cette étape.', invalid);
      return false;
    }
    var file = steps[current].querySelector('input[name="photo"][type="file"]');
    if (file && file.files && file.files[0] && file.files[0].size > 10 * 1024 * 1024) {
      refuse('La photo ne doit pas dépasser 10 Mo.', file);
      return false;
    }
    var groups = steps[current].querySelectorAll('[data-max-select]');
    for (var i = 0; i < groups.length; i += 1) {
      var limit = Number(groups[i].getAttribute('data-max-select'));
      var selected = groups[i].querySelectorAll('input[type="checkbox"]:checked').length;
      if (Number.isInteger(limit) && limit > 0 && selected > limit) {
        refuse('Choisissez au maximum ' + limit + ' réponses dans ce groupe.',
          groups[i].querySelector('input[type="checkbox"]:checked'));
        return false;
      }
    }
    return true;
  }

  back.addEventListener('click', function () { show(current - 1, true); });
  next.addEventListener('click', function () {
    if (validateCurrent()) show(current + 1, true);
  });

  // Si une réponse obligatoire d'une étape précédente est effacée
  // (restauration navigateur, script ou navigation arrière), le navigateur
  // doit pouvoir montrer et cibler son champ avant toute soumission.
  form.addEventListener('invalid', function (event) {
    var fieldset = event.target && event.target.closest('fieldset[data-registry-wizard-step]');
    if (!fieldset || !fieldset.hidden || invalidQueued) return;
    invalidQueued = true;
    var index = steps.indexOf(fieldset);
    window.queueMicrotask(function () {
      invalidQueued = false;
      if (index >= 0) show(index, true);
    });
  }, true);

  form.addEventListener('submit', function (event) {
    // L'événement de l'ancien module métier reste intact UNIQUEMENT
    // lorsque l'utilisateur est à la dernière étape et valide.
    // preventDefault seul n'arrêterait pas les listeners suivants :
    // stopImmediatePropagation empêche l'envoi RPC prématuré.
    if (current !== steps.length - 1) {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (validateCurrent()) show(current + 1, true);
      return;
    }
    if (!validateCurrent()) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);

  // Active seulement après avoir construit les commandes, afin que l'absence
  // de JavaScript laisse le formulaire entier disponible à la consultation.
  form.classList.add('sinjira-registry-wizard');
  show(0, false);
})();