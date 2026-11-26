/* Compte SINJIRA : révélation volontaire des mots de passe.
 * Aucun secret lu, enregistré, transmis ni inscrit dans les journaux.
 * Le comportement Auth/Supabase existant est préservé.
 */
(function () {
  'use strict';
  function initialize() {
  var form = document.querySelector('form[data-login-form], form[data-signup-form], form[data-reset-form]');
  if (!form) return;
  // Les attributs autocomplete indiquent l'intention au navigateur, mais
  // certains moteurs ne les exposent pas uniformément en propriété JS.
  // Le type réel du champ suffit, dans ces deux formulaires uniquement.
  var fields = Array.from(form.querySelectorAll('input[type="password"]'));
  if (!fields.length) return;

  var toggles = [];

  function conceal(item) {
    if (item.input.type !== 'password') item.input.type = 'password';
    item.button.setAttribute('aria-pressed', 'false');
    item.button.textContent = 'Afficher';
    item.button.setAttribute('aria-label', 'Afficher ' + item.label);
  }
  function concealAll() {
    toggles.forEach(conceal);
  }

  function syncDisabled(item) {
    // :disabled couvre aussi un champ placé dans un fieldset désactivé.
    var disabled = item.input.matches(':disabled');
    if (item.button.disabled !== disabled) item.button.disabled = disabled;
    if (disabled) conceal(item);
  }

  fields.forEach(function (input) {
    if (!input.id) return;
    var label = form.querySelector('label[for="' + input.id + '"]');
    var labelText = label ? label.textContent.replace(/\*/g, '').trim().toLowerCase() : 'le mot de passe';
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'password-visibility-toggle';
    button.dataset.passwordVisibility = '';
    button.setAttribute('aria-controls', input.id);
    button.setAttribute('aria-pressed', 'false');
    button.setAttribute('aria-label', 'Afficher ' + labelText);
    button.textContent = 'Afficher';
    input.insertAdjacentElement('afterend', button);

    var item = {input: input, button: button, label: labelText};
    toggles.push(item);
    syncDisabled(item);
    button.addEventListener('click', function () {
      if (input.matches(':disabled')) {
        syncDisabled(item);
        return;
      }
      var visible = input.type === 'password';
      input.type = visible ? 'text' : 'password';
      button.textContent = visible ? 'Masquer' : 'Afficher';
      button.setAttribute('aria-pressed', visible ? 'true' : 'false');
      button.setAttribute('aria-label', (visible ? 'Masquer ' : 'Afficher ') + labelText);
    });
  });

  // Le module de récupération peut verrouiller les champs après son
  // contrôle asynchrone. La commande de révélation suit le même état.
  if (typeof MutationObserver !== 'undefined') {
    new MutationObserver(function () {
      toggles.forEach(syncDisabled);
    }).observe(form, {subtree: true, attributes: true, attributeFilter: ['disabled']});
  }

  // Un changement d'onglet, un verrouillage ou une soumission masque les
  // mots de passe sans toucher à leurs valeurs ni aux processus Auth.
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) concealAll();
  });
  window.addEventListener('pagehide', concealAll);
  form.addEventListener('submit', concealAll, true);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize, {once: true});
  } else {
    initialize();
  }
})();