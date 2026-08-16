(() => {
  'use strict';

  const DEFAULT_DESTINATION = '/compte/index.html';

  function safeLocalDestination(value, fallback = DEFAULT_DESTINATION) {
    const raw = String(value || '').trim();
    const safeFallback = String(fallback || DEFAULT_DESTINATION);
    if (!raw) return safeFallback;
    if (!raw.startsWith('/') || raw.startsWith('//') || raw.includes('\\') || /[\u0000-\u001f\u007f]/.test(raw)) {
      return safeFallback;
    }
    try {
      const url = new URL(raw, location.origin);
      if (url.origin !== location.origin) return safeFallback;
      if (!url.pathname.startsWith('/') || url.username || url.password) return safeFallback;
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

  window.SINJIRA_AUTH_ROUTE = Object.freeze({ safeLocalDestination, next });
  sanitizeCurrentNext();
})();
