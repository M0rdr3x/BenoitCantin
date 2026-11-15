(() => {
  'use strict';

  const DEFAULT_DESTINATION = '/compte/index.html';

  function safeLocalDestination(value, fallback = DEFAULT_DESTINATION) {
    const raw = typeof value === 'string' ? value : '';
    // Chaîne vide explicite : sanitizeCurrentNext doit retirer la destination.
    const safeFallback = fallback === '' ? '' : String(fallback || DEFAULT_DESTINATION);
    if (!raw || raw !== raw.trim()) return safeFallback;
    if (!raw.startsWith('/') || raw.startsWith('//') || raw.includes('\\') || /[\u0000-\u0020\u007f]/.test(raw) ||
        /%(?:0[0-9a-f]|1[0-9a-f]|2f|5c|7f)/i.test(raw)) {
      return safeFallback;
    }
    try {
      const url = new URL(raw, location.origin);
      if (url.origin !== location.origin) return safeFallback;
      if (!url.pathname.startsWith('/') || url.username || url.password ||
          url.pathname !== raw.split(/[?#]/, 1)[0]) return safeFallback;
      return `${url.pathname}${url.search}${url.hash}`;
    } catch {
      return safeFallback;
    }
  }

  function next(fallback = DEFAULT_DESTINATION) {
    return safeLocalDestination(new URLSearchParams(location.search).get('next'), fallback);
  }

  function sanitizeCurrentNext() {
    const url = new URL(location.href);
    const raw = url.searchParams.get('next');
    if (raw === null) return;
    const safe = safeLocalDestination(raw, '');
    if (safe) {
      if (safe !== raw) {
        url.searchParams.set('next', safe);
        history.replaceState(history.state, '', `${url.pathname}${url.search}${url.hash}`);
      }
      return;
    }
    url.searchParams.delete('next');
    history.replaceState(history.state, '', `${url.pathname}${url.search}${url.hash}`);
  }

  function enforcePasswordPolicy(event) {
    const form = event.target?.closest?.('[data-reset-form]');
    if (!form) return;
    const password = String(form.elements?.password?.value || '');
    const confirm = String(form.elements?.password_confirm?.value || '');
    if (password.length >= 12 && password === confirm) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const status = document.querySelector('[data-account-status]');
    if (status) {
      status.textContent = 'Les mots de passe doivent correspondre et contenir au moins 12 caractères.';
      status.dataset.statusType = 'error';
      status.hidden = false;
    }
  }

  window.SINJIRA_AUTH_ROUTE = Object.freeze({ safeLocalDestination, next });
  sanitizeCurrentNext();
  document.addEventListener('submit', enforcePasswordPolicy, true);
})();
