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
  // Le type réel du champ suffit, dans ces trois formulaires uniquement.
  var fields = Array.from(form.querySelectorAll('input[type="password"]'));
  if (!fields.length) return;

  var toggles = [];

  function setVisibility(item, visible) {
    item.input.type = visible ? 'text' : 'password';
    item.button.setAttribute('aria-pressed', visible ? 'true' : 'false');
    item.button.textContent = visible ? 'Masquer' : 'Afficher';
    item.button.setAttribute('aria-label', (visible ? 'Masquer ' : 'Afficher ') + item.label);
  }

  function concealAll() {
    toggles.forEach(function (item) {
      if (item.input.type !== 'password') setVisibility(item, false);
    });
  }

  fields.forEach(function (input) {
    if (!input.id) return;
    var label = form.querySelector('label[for="' + input.id + '"]');
    var labelText = label ? label.textContent.replace(/\*/g, '').trim().toLowerCase() : '';
    // Le libellé « Confirmer » seul n'identifie pas la commande.
    if (input.name === 'password_confirm' || /confirm/.test(labelText)) {
      labelText = 'la confirmation du mot de passe';
    } else if (/nouveau/.test(labelText)) {
      labelText = 'le nouveau mot de passe';
    } else {
      labelText = 'le mot de passe';
    }
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
    button.addEventListener('click', function () {
      setVisibility(item, input.type === 'password');
    });
  });

  // Échap masque un secret révélé depuis le champ ou sa commande, sans
  // déplacer le focus ni intercepter un autre raccourci ou une composition IME.
  form.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape' || event.isComposing || event.defaultPrevented ||
        event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    var item = toggles.find(function (candidate) {
      return event.target === candidate.input || event.target === candidate.button;
    });
    if (!item || item.input.type !== 'text') return;
    event.preventDefault();
    setVisibility(item, false);
  });

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