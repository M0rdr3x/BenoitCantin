(() => {
  const toggle = document.querySelector('[data-menu-toggle]');
  const nav = document.querySelector('[data-main-nav]');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('open', !open);
    });
    nav.addEventListener('click', (event) => {
      if (event.target.closest('a')) {
        toggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('open');
      }
    });
  }

  const core = document.querySelector('[data-core-preview]');
  if (core) {
    const coreImage = core.querySelector('img');
    const nodes = [...document.querySelectorAll('.orbit-node[data-core-src]')];
    const defaultSrc = core.dataset.defaultSrc || coreImage?.getAttribute('src') || '';
    const defaultAlt = core.dataset.defaultAlt || coreImage?.getAttribute('alt') || 'Benoit Cantin';
    let changeTimer = null;

    const swap = (src, alt, active) => {
      if (!coreImage || !src) return;
      if (changeTimer) window.clearTimeout(changeTimer);
      core.classList.toggle('is-project-preview', Boolean(active));
      coreImage.classList.add('is-changing');
      changeTimer = window.setTimeout(() => {
        coreImage.src = src;
        coreImage.alt = alt || '';
        coreImage.classList.remove('is-changing');
      }, 80);
    };

    const showCore = (node) => swap(
      node?.dataset.coreSrc,
      node?.dataset.coreAlt || node?.getAttribute('aria-label') || '',
      true
    );
    const resetCore = () => swap(defaultSrc, defaultAlt, false);

    nodes.forEach((node) => {
      node.addEventListener('pointerenter', () => showCore(node));
      node.addEventListener('pointerleave', resetCore);
      node.addEventListener('focus', () => showCore(node));
      node.addEventListener('blur', resetCore);
    });
  }

  document.querySelectorAll('[data-year]').forEach((node) => {
    node.textContent = new Date().getFullYear();
  });

  document.querySelectorAll('[data-disabled-download]').forEach((link) => {
    link.addEventListener('click', (event) => event.preventDefault());
  });

  document.querySelectorAll('[data-pending-form]').forEach((form) => {
    const action = form.getAttribute('action') || '';
    if (action.startsWith('https://formspree.io/f/')) return;
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      window.alert('Ce formulaire n’est pas encore configuré. Aucune donnée n’a été transmise.');
    }, true);
  });

  const runtimes = [
    ['v2431Runtime','/assets/js/v24-3-1-runtime.js?v=24.4.12'],
    ['v2432Runtime','/assets/js/v24-3-2-runtime.js?v=24.4.12'],
    ['v2433Runtime','/assets/js/v24-3-3-runtime.js?v=24.4.12'],
    ['v2436Runtime','/assets/js/v24-3-6-runtime.js?v=24.4.12']
  ];
  for (const [key, src] of runtimes) {
    const selector = `script[data-${key.replace(/[A-Z]/g,m=>'-'+m.toLowerCase())}]`;
    if (document.querySelector(selector)) continue;
    const runtime = document.createElement('script');
    runtime.type = 'module';
    runtime.src = src;
    runtime.dataset[key] = '';
    document.head.appendChild(runtime);
  }

  // V24.4.21 — diagnostic local et respectueux de la vie privée.
  // Aucun message, stack trace, URL avec query-string ou contenu utilisateur n’est transmis.
  const RUNTIME_VERSION = '24.4.21';
  const requestId = globalThis.crypto?.randomUUID?.()
    || `s-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  const storageKey = 'sinjira-runtime-errors';
  document.documentElement.dataset.runtimeRequestId = requestId;

  const safeSource = (source) => {
    if (!source) return '';
    try {
      const url = new URL(String(source), window.location.href);
      return url.pathname.slice(0, 160);
    } catch {
      return '';
    }
  };

  const readErrors = () => {
    try {
      const parsed = JSON.parse(sessionStorage.getItem(storageKey) || '[]');
      return Array.isArray(parsed) ? parsed.slice(-7) : [];
    } catch {
      return [];
    }
  };

  const recordError = (category, source = '') => {
    const entry = {
      version: RUNTIME_VERSION,
      requestId,
      category,
      source: safeSource(source),
      at: new Date().toISOString()
    };
    const recent = [...readErrors(), entry].slice(-8);
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(recent));
    } catch {
      // Le diagnostic reste facultatif si le stockage de session est bloqué.
    }
    console.warn('[SINJIRA runtime]', {requestId, category, source: entry.source});
  };

  window.addEventListener('error', (event) => {
    recordError('runtime-error', event?.filename || '');
  });
  window.addEventListener('unhandledrejection', () => {
    recordError('unhandled-rejection');
  });

  window.__SINJIRA_RUNTIME__ = Object.freeze({
    version: RUNTIME_VERSION,
    requestId,
    recentErrors: () => readErrors().map((entry) => ({...entry}))
  });
})();
