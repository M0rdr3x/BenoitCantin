(function () {
  'use strict';

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  function loadPublicAssistant() {
    var path = String(window.location.pathname || '/').toLowerCase();
    var isPrivateSurface =
      path === '/compte' ||
      path.indexOf('/compte/') === 0 ||
      path === '/admin' ||
      path.indexOf('/admin/') === 0;
    var robots = document.querySelector('meta[name="robots"]');
    var robotsContent = robots ? String(robots.getAttribute('content') || '').toLowerCase() : '';
    var isNoindexSurface = /(^|[,\s])noindex([,\s]|$)/.test(robotsContent);

    if (isPrivateSurface || isNoindexSurface) return;
    if (document.querySelector('script[data-bubblav-widget]')) return;

    var script = document.createElement('script');
    script.src = 'https://www.bubblav.com/widget.js';
    script.defer = true;
    script.setAttribute('data-site-id', 'ca77cd98-bd32-459c-ad55-fdad4fb85316');
    script.setAttribute('data-bubblav-widget', '');
    document.head.appendChild(script);
  }

  ready(function () {
    loadPublicAssistant();
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
