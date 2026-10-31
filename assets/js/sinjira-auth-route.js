(() => {
  'use strict';

  const DEFAULT_DESTINATION = '/compte/index.html';

  // Les redirections après authentification sont réservées aux pages, jamais
  // aux sources techniques qu'une publication GitHub Pages legacy peut servir.
  function safeLocalDestination(value, fallback = DEFAULT_DESTINATION) {
    const safeFallback = fallback === '' ? '' : String(fallback || DEFAULT_DESTINATION);
    if (typeof value !== 'string' || !value || value !== value.trim()) return safeFallback;
    if (!value.startsWith('/') || value.startsWith('//') ||
        /[\\\u0000-\u001f\u007f]/.test(value)) return safeFallback;
    try {
      const url = new URL(value, location.origin);
      const path = value.split(/[?#]/, 1)[0];
      if (url.origin !== location.origin || url.username || url.password ||
          url.pathname !== path || path.includes('%')) return safeFallback;
      if (/^\/(?:\.git|\.github|\.well-known|supabase|scripts|tests|docs|mobile-native|node_modules|_site)(?:\/|$)/i.test(path) ||
          /\/(?:codex|\.git)(?:\/|$)/i.test(path) ||
          /\/(?:netlify\.toml|_config\.yml|security\.md|upload_github\.md|readme\.md)$/i.test(path) ||
          /\.(?:py|sql|toml|ya?ml|md|tsx?|jsx?|sh|env|lock|css|json|txt|xml|svg|map|webmanifest)(?:$)/i.test(path)) return safeFallback;
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
