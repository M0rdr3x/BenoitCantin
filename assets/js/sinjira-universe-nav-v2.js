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
          if (reduced) {
            strip.scrollLeft += direction * distance;
          } else {
            strip.scrollBy({ left: direction * distance, behavior: 'smooth' });
          }
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
        // Mesurer dans le même repère, même lorsque la grille des flèches
        // décale le ruban ou qu'un ancêtre devient son offsetParent.
        var bounds = strip.getBoundingClientRect();
        var link = active.getBoundingClientRect();
        var left = bounds.left + strip.clientLeft;
        var right = left + strip.clientWidth;
        if (link.width > strip.clientWidth || link.left < left || link.right > right) {
          // Si le libellé dépasse le ruban (très petit écran), montrer son début.
          strip.scrollLeft += link.left - left;
        }
      }

      strip.addEventListener('scroll', update, { passive: true });
      var lastViewportWidth = window.innerWidth;
      window.addEventListener('resize', function () {
        update();
        if (window.innerWidth === lastViewportWidth) return;
        lastViewportWidth = window.innerWidth;
        revealActive();
        update();
      }, { passive: true });
      if (typeof ResizeObserver === 'function') {
        var observer = new ResizeObserver(update);
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
