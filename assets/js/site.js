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

  // Constellation du portail : l'image centrale représente Benoit Cantin
  // au repos, puis prévisualise chaque univers au survol ou au focus clavier.
  const core = document.querySelector('[data-core-preview]');
  if (core) {
    const coreImage = core.querySelector('img');
    const nodes = [...document.querySelectorAll('.cosmos-card .orbit-node[data-core-src]')];
    const defaultSrc = core.dataset.defaultSrc || coreImage?.getAttribute('src') || '';
    const defaultAlt = core.dataset.defaultAlt || coreImage?.getAttribute('alt') || 'Benoit Cantin';

    const showCore = (node) => {
      if (!coreImage || !node) return;
      const src = node.dataset.coreSrc;
      if (!src) return;
      core.classList.add('is-project-preview');
      coreImage.classList.add('is-changing');
      window.setTimeout(() => {
        coreImage.src = src;
        coreImage.alt = node.dataset.coreAlt || node.getAttribute('aria-label') || '';
        coreImage.classList.remove('is-changing');
      }, 90);
    };

    const resetCore = () => {
      if (!coreImage) return;
      core.classList.remove('is-project-preview');
      coreImage.classList.add('is-changing');
      window.setTimeout(() => {
        coreImage.src = defaultSrc;
        coreImage.alt = defaultAlt;
        coreImage.classList.remove('is-changing');
      }, 90);
    };

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

  // Correctifs cumulatifs V24.3.1 : questionnaire unique, accès Fracture et compatibilité.
  if (!document.querySelector('script[data-v2431-runtime]')) {
    const runtime = document.createElement('script');
    runtime.type = 'module';
    runtime.src = '/assets/js/v24-3-1-runtime.js?v=24.3.1';
    runtime.dataset.v2431Runtime = '';
    document.head.appendChild(runtime);
  }
})();
