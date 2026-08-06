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
})();
