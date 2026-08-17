(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;

  function hasClass(node, className) {
    return node && (' ' + (node.className || '') + ' ').indexOf(' ' + className + ' ') !== -1;
  }

  function addClass(node, className) {
    if (!node || hasClass(node, className)) return;
    node.className = ((node.className || '') + ' ' + className).replace(/^\s+|\s+$/g, '');
  }

  function removeClass(node, className) {
    if (!node) return;
    node.className = (' ' + (node.className || '') + ' ')
      .replace(' ' + className + ' ', ' ')
      .replace(/^\s+|\s+$/g, '');
  }

  function closestAnchor(node, boundary) {
    while (node && node !== boundary) {
      if (String(node.tagName || '').toLowerCase() === 'a') return node;
      node = node.parentNode;
    }
    return null;
  }

  function appendCompatStylesheet() {
    if (doc.querySelector('link[data-sinjira-browser-compat]')) return;
    var link = doc.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/assets/css/browser-compat-v24-4-22.css?v=24.4.22';
    link.setAttribute('data-sinjira-browser-compat', '');
    doc.head.appendChild(link);
  }

  function appendAssistantAssets() {
    if (root.getAttribute('data-disable-sinjira-assistant') === 'true') return;
    if (!doc.querySelector('link[data-sinjira-assistant-style]')) {
      var assistantStyle = doc.createElement('link');
      assistantStyle.rel = 'stylesheet';
      assistantStyle.href = '/assets/css/sinjira-assistant.css?v=24.4.40';
      assistantStyle.setAttribute('data-sinjira-assistant-style', '');
      doc.head.appendChild(assistantStyle);
    }
    if (!doc.querySelector('script[data-sinjira-assistant-script]')) {
      var assistantScript = doc.createElement('script');
      assistantScript.src = '/assets/js/sinjira-assistant.js?v=24.4.40';
      assistantScript.defer = true;
      assistantScript.setAttribute('data-sinjira-assistant-script', '');
      doc.head.appendChild(assistantScript);
    }
  }

  appendCompatStylesheet();
  appendAssistantAssets();

  var toggle = doc.querySelector('[data-menu-toggle]');
  var nav = doc.querySelector('[data-main-nav]');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', open ? 'false' : 'true');
      if (open) removeClass(nav, 'open');
      else addClass(nav, 'open');
    });

    nav.addEventListener('click', function (event) {
      if (closestAnchor(event.target, nav)) {
        toggle.setAttribute('aria-expanded', 'false');
        removeClass(nav, 'open');
      }
    });
  }

  var core = doc.querySelector('[data-core-preview]');
  if (core) {
    var coreImage = core.querySelector('img');
    var nodeList = doc.querySelectorAll('.orbit-node[data-core-src]');
    var nodes = Array.prototype.slice.call(nodeList);
    var defaultSrc = core.getAttribute('data-default-src') || (coreImage ? coreImage.getAttribute('src') : '') || '';
    var defaultAlt = core.getAttribute('data-default-alt') || (coreImage ? coreImage.getAttribute('alt') : '') || 'Benoit Cantin';
    var changeTimer = null;

    function swap(src, alt, active) {
      if (!coreImage || !src) return;
      if (changeTimer) window.clearTimeout(changeTimer);
      if (active) addClass(core, 'is-project-preview');
      else removeClass(core, 'is-project-preview');
      addClass(coreImage, 'is-changing');
      changeTimer = window.setTimeout(function () {
        coreImage.src = src;
        coreImage.alt = alt || '';
        removeClass(coreImage, 'is-changing');
      }, 80);
    }

    function showCore(node) {
      swap(
        node ? node.getAttribute('data-core-src') : '',
        (node && (node.getAttribute('data-core-alt') || node.getAttribute('aria-label'))) || '',
        true
      );
    }

    function resetCore() {
      swap(defaultSrc, defaultAlt, false);
    }

    var supportsPointer = 'onpointerenter' in window;
    for (var i = 0; i < nodes.length; i += 1) {
      (function (node) {
        node.addEventListener(supportsPointer ? 'pointerenter' : 'mouseenter', function () { showCore(node); });
        node.addEventListener(supportsPointer ? 'pointerleave' : 'mouseleave', resetCore);
        node.addEventListener('focus', function () { showCore(node); });
        node.addEventListener('blur', resetCore);
      }(nodes[i]));
    }
  }

  var yearNodes = doc.querySelectorAll('[data-year]');
  for (var y = 0; y < yearNodes.length; y += 1) {
    yearNodes[y].textContent = new Date().getFullYear();
  }

  var disabledDownloads = doc.querySelectorAll('[data-disabled-download]');
  for (var d = 0; d < disabledDownloads.length; d += 1) {
    disabledDownloads[d].addEventListener('click', function (event) {
      event.preventDefault();
    });
  }

  var pendingForms = doc.querySelectorAll('[data-pending-form]');
  for (var f = 0; f < pendingForms.length; f += 1) {
    (function (form) {
      var action = form.getAttribute('action') || '';
      if (action.indexOf('https://formspree.io/f/') === 0) return;
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        if (event.stopImmediatePropagation) event.stopImmediatePropagation();
        window.alert('Ce formulaire n’est pas encore configuré. Aucune donnée n’a été transmise.');
      }, true);
    }(pendingForms[f]));
  }

  var moduleProbe = doc.createElement('script');
  var supportsModules = 'noModule' in moduleProbe;
  if (supportsModules) {
    var runtimes = [
      ['v2431Runtime', '/assets/js/v24-3-1-runtime.js?v=24.4.12'],
      ['v2432Runtime', '/assets/js/v24-3-2-runtime.js?v=24.4.12'],
      ['v2433Runtime', '/assets/js/v24-3-3-runtime.js?v=24.4.12'],
      ['v2436Runtime', '/assets/js/v24-3-6-runtime.js?v=24.4.12']
    ];

    function runtimeSelector(key) {
      return 'script[data-' + key.replace(/[A-Z]/g, function (match) {
        return '-' + match.toLowerCase();
      }) + ']';
    }

    for (var r = 0; r < runtimes.length; r += 1) {
      var key = runtimes[r][0];
      var src = runtimes[r][1];
      if (doc.querySelector(runtimeSelector(key))) continue;
      var runtime = doc.createElement('script');
      runtime.type = 'module';
      runtime.src = src;
      runtime.setAttribute('data-' + key.replace(/[A-Z]/g, function (match) {
        return '-' + match.toLowerCase();
      }), '');
      doc.head.appendChild(runtime);
    }
  } else {
    addClass(root, 'sinjira-legacy-browser');
  }

  // V24.4.22 — diagnostic local, privé et compatible avec des moteurs plus anciens.
  // Aucun message utilisateur, stack trace, query-string ni contenu de formulaire n’est transmis.
  var RUNTIME_VERSION = '24.4.22';
  var cryptoObject = window.crypto || window.msCrypto;
  var requestId = cryptoObject && typeof cryptoObject.randomUUID === 'function'
    ? cryptoObject.randomUUID()
    : 's-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
  var storageKey = 'sinjira-runtime-errors';
  root.setAttribute('data-runtime-request-id', requestId);

  function safeSource(source) {
    if (!source) return '';
    try {
      if (typeof window.URL === 'function') {
        return new window.URL(String(source), window.location.href).pathname.slice(0, 160);
      }
      var parser = doc.createElement('a');
      parser.href = String(source);
      return (parser.pathname || '').slice(0, 160);
    } catch (error) {
      return '';
    }
  }

  function readErrors() {
    try {
      var parsed = JSON.parse(window.sessionStorage.getItem(storageKey) || '[]');
      return Array.isArray(parsed) ? parsed.slice(-7) : [];
    } catch (error) {
      return [];
    }
  }

  function recordError(category, source) {
    var entry = {
      version: RUNTIME_VERSION,
      requestId: requestId,
      category: category,
      source: safeSource(source || ''),
      at: new Date().toISOString()
    };
    var recent = readErrors();
    recent.push(entry);
    recent = recent.slice(-8);
    try {
      window.sessionStorage.setItem(storageKey, JSON.stringify(recent));
    } catch (error) {
      // Le diagnostic reste facultatif si le stockage de session est bloqué.
    }
    if (window.console && typeof window.console.warn === 'function') {
      window.console.warn('[SINJIRA runtime]', {
        requestId: requestId,
        category: category,
        source: entry.source
      });
    }
  }

  window.addEventListener('error', function (event) {
    recordError('runtime-error', event && event.filename ? event.filename : '');
  });
  window.addEventListener('unhandledrejection', function () {
    recordError('unhandled-rejection');
  });

  var runtimeApi = {
    version: RUNTIME_VERSION,
    requestId: requestId,
    recentErrors: function () {
      var source = readErrors();
      var copy = [];
      for (var i = 0; i < source.length; i += 1) {
        copy.push({
          version: source[i].version,
          requestId: source[i].requestId,
          category: source[i].category,
          source: source[i].source,
          at: source[i].at
        });
      }
      return copy;
    }
  };
  window.__SINJIRA_RUNTIME__ = Object.freeze ? Object.freeze(runtimeApi) : runtimeApi;
}());