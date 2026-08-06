(() => {
  const FORMSPREE_ERE_ENDPOINT = 'https://formspree.io/f/xdenkzrv';

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

  function ensureHiddenField(form, name, value) {
    let field = form.querySelector(`input[type="hidden"][name="${name}"]`);
    if (!field) {
      field = document.createElement('input');
      field.type = 'hidden';
      field.name = name;
      form.prepend(field);
    }
    field.value = value;
  }

  function configureFormspree(form, endpoint, subject) {
    form.action = endpoint;
    form.method = 'POST';
    form.acceptCharset = 'UTF-8';
    form.removeAttribute('data-pending-form');

    if (form.querySelector('input[type="file"]')) {
      form.enctype = 'multipart/form-data';
    }

    ensureHiddenField(form, '_subject', subject);
    ensureHiddenField(form, 'source_site', 'L’Ère des Consciences');
    ensureHiddenField(form, 'source_page', window.location.href);

    const legalNote = form.querySelector('.legal-note');
    if (legalNote) {
      legalNote.textContent =
        'La participation sera transmise de façon sécurisée par Formspree à l’équipe de L’Ère des Consciences.';
    }

    form.addEventListener('submit', () => {
      const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.setAttribute('aria-disabled', 'true');
        if (submitButton.tagName === 'BUTTON') {
          submitButton.dataset.originalText = submitButton.textContent;
          submitButton.textContent = 'Transmission en cours…';
        }
      }
    });
  }

  const isEreDesConsciences =
    window.location.pathname.includes('/projets/ere-des-consciences/');

  document.querySelectorAll('form[data-pending-form]').forEach((form) => {
    if (isEreDesConsciences) {
      const formName =
        form.getAttribute('name') ||
        form.id ||
        document.title ||
        'Formulaire de L’Ère des Consciences';

      configureFormspree(
        form,
        FORMSPREE_ERE_ENDPOINT,
        `L’Ère des Consciences — ${formName}`
      );
      return;
    }

    form.addEventListener(
      'submit',
      (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();
        window.alert(
          'Ce formulaire n’est pas encore configuré. Aucune donnée n’a été transmise.'
        );
      },
      true
    );
  });
})();
