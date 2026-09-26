(function () {
  'use strict';

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    if (document.querySelector('[data-ai-transparency]')) return;

    var notice = document.createElement('aside');
    notice.className = 'ai-transparency-banner';
    notice.setAttribute('data-ai-transparency', '');
    notice.setAttribute('aria-label', "Transparence sur l'utilisation de l'intelligence artificielle");
    notice.innerHTML =
      '<div class="ai-transparency-inner">' +
        '<strong>Transparence IA</strong>' +
        '<span>Idées, vision et décisions&nbsp;: Benoit Cantin. Mise en œuvre assistée par des outils d’intelligence artificielle. Validation finale et responsabilité du contenu&nbsp;: Benoit Cantin.</span>' +
        '<a href="/transparence-ia.html">Comment l’IA est utilisée</a>' +
      '</div>';

    var header = document.querySelector('.site-header');
    if (header && header.parentNode) {
      header.parentNode.insertBefore(notice, header.nextSibling);
      return;
    }

    var main = document.querySelector('main');
    if (main && main.parentNode) {
      main.parentNode.insertBefore(notice, main);
      return;
    }

    document.body.insertBefore(notice, document.body.firstChild);
  });
}());
