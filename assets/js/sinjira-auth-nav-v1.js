/* SINJIRA : sous-navigation d'authentification progressive et accessible.
 * Aucun contact avec Auth, Supabase, cookie, stockage ou données saisies.
 * Sans JavaScript, les liens restent défilables au doigt et au clavier.
 */
(function () {
  'use strict';
  function initialize() {
    var nav = document.querySelector(
      'body.account-page[data-sinjira-form-ux="v1"] .universe-subnav'
    );
    if (!nav || nav.hasAttribute('data-sinjira-auth-nav-ready')) return;
    var scroll = nav.querySelector('.container');
    if (!scroll || scroll.querySelectorAll('a').length < 2) return;
    if (!scroll.id) scroll.id = 'sinjira-auth-links';
    var back = document.createElement('button');
    var forward = document.createElement('button');
    function setup(button, preceding) {
      button.type = 'button';
      button.className = 'sinjira-auth-nav-arrow';
      button.textContent = preceding ? '‹' : '›';
      button.setAttribute('aria-label', preceding ?
        'Liens précédents de connexion' : 'Liens suivants de connexion');
      button.setAttribute('aria-controls', scroll.id);
      button.hidden = true;
    }
    setup(back, true);
    setup(forward, false);
    nav.insertBefore(back, scroll);
    nav.appendChild(forward);
    nav.setAttribute('data-sinjira-auth-nav-ready', '');
    function refresh() {
      var max = Math.max(0, scroll.scrollWidth - scroll.clientWidth);
      var active = window.matchMedia('(max-width: 680px)').matches && max > 2;
      nav.classList.toggle('is-scrollable', active);
      back.hidden = !active;
      forward.hidden = !active;
      back.disabled = !active || scroll.scrollLeft <= 2;
      forward.disabled = !active || scroll.scrollLeft >= max - 2;
    }
    function revealActive() {
      if (!window.matchMedia('(max-width: 680px)').matches) return;
      var link = scroll.querySelector('a[aria-current="page"]');
      if (!link) return;
      var box = scroll.getBoundingClientRect();
      var tab = link.getBoundingClientRect();
      if (tab.left >= box.left + 2 && tab.right <= box.right - 2) return;
      var max = Math.max(0, scroll.scrollWidth - scroll.clientWidth);
      var center = tab.left - box.left + scroll.scrollLeft -
        (scroll.clientWidth - tab.width) / 2;
      scroll.scrollLeft = Math.max(0, Math.min(max, center));
    }
    function slide(direction) {
      var max = Math.max(0, scroll.scrollWidth - scroll.clientWidth);
      var delta = Math.max(110, Math.round(scroll.clientWidth * .75));
      var target = Math.max(0, Math.min(max, scroll.scrollLeft + delta * direction));
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      scroll.scrollTo({left: target, behavior: reduce ? 'auto' : 'smooth'});
      window.requestAnimationFrame(refresh);
    }
    back.addEventListener('click', function () { slide(-1); });
    forward.addEventListener('click', function () { slide(1); });
    scroll.addEventListener('scroll', refresh, {passive: true});
    function onLayoutChange() {
      refresh();
      window.requestAnimationFrame(function () {
        refresh();
        revealActive();
        refresh();
      });
    }
    window.addEventListener('resize', onLayoutChange);
    if (typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(refresh).observe(scroll);
    }
    onLayoutChange();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize, {once: true});
  } else {
    initialize();
  }
})();
