/* Navigation des univers : commandes de défilement pour les rubriques masquées.
 * Aucun suivi, aucune requête réseau ni dépendance externe. */
(function () {
  'use strict';
  function init() {
    document.querySelectorAll('nav.universe-subnav').forEach(function (nav) {
      if (nav.hasAttribute('data-universe-controls-ready')) return;
      var strip = nav.querySelector('.container');
      if (!strip || strip.querySelectorAll('a').length < 2) return;
      nav.setAttribute('data-universe-controls-ready', 'true');

      function arrow(direction, name, glyph) {
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'universe-scroll-button';
        button.setAttribute('aria-label', name);
        button.setAttribute('aria-controls', strip.id);
        button.textContent = glyph;
        button.hidden = true;
        button.addEventListener('click', function () {
          var distance = Math.max(120, Math.round(strip.clientWidth * .75));
          var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
          strip.scrollBy({ left: direction * distance, behavior: reduced ? 'auto' : 'smooth' });
        });
        return button;
      }

      // Une cible stable permet au lecteur d'écran d'associer les boutons au ruban.
      if (!strip.id) strip.id = 'sinjira-universe-links';
      var previous = arrow(-1, 'Rubriques précédentes de SINJIRA', '‹');
      var next = arrow(1, 'Rubriques suivantes de SINJIRA', '›');
      nav.insertBefore(previous, strip);
      nav.appendChild(next);

      function update() {
        var overflow = strip.scrollWidth - strip.clientWidth > 3;
        nav.classList.toggle('has-universe-scroll', overflow);
        previous.hidden = !overflow;
        next.hidden = !overflow;
        if (!overflow) return;
        previous.disabled = strip.scrollLeft <= 3;
        next.disabled = strip.scrollLeft + strip.clientWidth >= strip.scrollWidth - 3;
      }

      function revealActive() {
        var active = strip.querySelector('a[aria-current="page"]');
        if (!active) return;
        var start = active.offsetLeft - strip.offsetLeft;
        var end = start + active.offsetWidth;
        if (start < strip.scrollLeft || end > strip.scrollLeft + strip.clientWidth) {
          strip.scrollLeft = Math.max(0, start - 12);
        }
      }

      strip.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update, { passive: true });
      if (typeof ResizeObserver === 'function') {
        var resizeFrame = null;
        var observer = new ResizeObserver(function () {
          if (resizeFrame !== null) return;
          resizeFrame = window.requestAnimationFrame(function () {
            resizeFrame = null;
            update();
          });
        });
        observer.observe(strip);
      }
      update();
      revealActive();
      update();
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
}());
