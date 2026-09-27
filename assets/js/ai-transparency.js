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
        '<strong>Transparence · Honnêteté · Intégrité</strong>' +
        '<span>Je travaille avec l’aide de l’intelligence artificielle pour structurer, développer, vérifier ou mettre en œuvre certaines parties de mes projets. Les idées, la vision et les décisions finales restent les miennes. <em>L’humain avant tout.</em></span>' +
        '<a href="/transparence-ia.html">Lire ma démarche</a>' +
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
