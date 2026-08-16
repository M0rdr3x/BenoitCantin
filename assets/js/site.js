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

  // V24.4.11 — l'accueil personnel reste volontairement simple :
  // SINJIRA™ et Projet Nova seulement. Les sous-univers SINJIRA vivent dans leur propre portail.
  if (document.body.classList.contains('home-page')) {
    const cosmos = document.querySelector('.cosmos-card[data-home-focus], .cosmos-card');
    if (cosmos && !cosmos.dataset.homeFocusApplied) {
      cosmos.dataset.homeFocusApplied = 'true';
      cosmos.classList.remove('v20-six-portals');
      cosmos.classList.add('v24-home-two-portals');
      cosmos.setAttribute('aria-label', 'Accès interactif à SINJIRA™ et Projet Nova');
      cosmos.querySelectorAll('.orbit-node').forEach(node => node.remove());
      const label = cosmos.querySelector('.cosmos-label');
      const sinjira = document.createElement('a');
      sinjira.className = 'orbit-node node-sinjira-home';
      sinjira.href = '/projets/sinjira/';
      sinjira.setAttribute('aria-label', 'SINJIRA™');
      sinjira.dataset.coreSrc = '/assets/media/sinjira-emblem.webp';
      sinjira.dataset.coreAlt = 'Emblème officiel SINJIRA™';
      sinjira.innerHTML = '<img alt="" class="orbit-logo" src="/assets/media/sinjira-emblem.webp"><span>SINJIRA™</span>';
      const nova = document.createElement('a');
      nova.className = 'orbit-node node-nova-home';
      nova.href = '/projets/projet-nova/';
      nova.setAttribute('aria-label', 'Projet Nova');
      nova.dataset.coreSrc = '/assets/media/nova-logo.webp';
      nova.dataset.coreAlt = 'Logo officiel de Projet Nova';
      nova.innerHTML = '<img alt="" class="orbit-logo" src="/assets/media/nova-logo.webp"><span>Projet Nova</span>';
      if (label) {
        cosmos.insertBefore(sinjira, label);
        cosmos.insertBefore(nova, label);
        label.textContent = 'Deux univers · une même signature';
      } else {
        cosmos.append(sinjira, nova);
      }
    }

    const heroActions = document.querySelector('.hero .hero-actions');
    if (heroActions) {
      heroActions.innerHTML = '<a class="btn btn-primary" href="/projets/sinjira/">Entrer dans SINJIRA™ <span aria-hidden="true">→</span></a><a class="btn btn-secondary" href="/projets/projet-nova/">Découvrir Projet Nova</a>';
    }

    const sectionHead = document.querySelector('#univers .section-head');
    if (sectionHead) sectionHead.innerHTML = '<div><span class="eyebrow">Mes projets</span><h2>Deux univers au premier plan.</h2></div><p>SINJIRA™ regroupe maintenant ses romans, jeux, personnages, communauté et Monde parallèle dans son propre portail. Projet Nova conserve son espace indépendant.</p>';

    const grid = document.querySelector('#univers .project-grid-compact');
    if (grid) {
      grid.classList.add('v24-home-projects-two');
      grid.innerHTML = '<a class="project-card" href="/projets/sinjira/" style="--card-glow:rgba(255,112,89,.24)"><img alt="Emblème officiel SINJIRA™" class="project-icon project-icon-logo" loading="lazy" src="/assets/media/sinjira-emblem.webp"><small>Univers narratif et interactif</small><h3>SINJIRA™</h3><p>Romans, jeux, Registre des Consciences, Communauté, Monde parallèle et identité narrative réunis dans un seul univers.</p><span class="arrow">Entrer dans SINJIRA™ →</span></a><a class="project-card" href="/projets/projet-nova/" style="--card-glow:rgba(51,216,232,.24)"><img alt="Logo officiel de Projet Nova" class="project-icon project-icon-logo" loading="lazy" src="/assets/media/nova-logo.webp"><small>Projet citoyen</small><h3>Projet Nova</h3><p>Le projet citoyen indépendant, ses documents, ses propositions et sa démarche publique.</p><span class="arrow">Accéder à Projet Nova →</span></a>';
    }
  }

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

  document.querySelectorAll('[data-year]').forEach((node) => { node.textContent = new Date().getFullYear(); });
  document.querySelectorAll('[data-disabled-download]').forEach((link) => { link.addEventListener('click', (event) => event.preventDefault()); });
  document.querySelectorAll('[data-pending-form]').forEach((form) => {
    const action = form.getAttribute('action') || '';
    if (action.startsWith('https://formspree.io/f/')) return;
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      window.alert('Ce formulaire n’est pas encore configuré. Aucune donnée n’a été transmise.');
    }, true);
  });

  if (!document.querySelector('script[data-v2431-runtime]')) {
    const runtime = document.createElement('script');runtime.type = 'module';runtime.src = '/assets/js/v24-3-1-runtime.js?v=24.4.11';runtime.dataset.v2431Runtime = '';document.head.appendChild(runtime);
  }
  if (!document.querySelector('script[data-v2432-runtime]')) {
    const runtime = document.createElement('script');runtime.type = 'module';runtime.src = '/assets/js/v24-3-2-runtime.js?v=24.4.11';runtime.dataset.v2432Runtime = '';document.head.appendChild(runtime);
  }
  if (!document.querySelector('script[data-v2433-runtime]')) {
    const runtime = document.createElement('script');runtime.type = 'module';runtime.src = '/assets/js/v24-3-3-runtime.js?v=24.4.11';runtime.dataset.v2433Runtime = '';document.head.appendChild(runtime);
  }
  if (!document.querySelector('script[data-v2436-runtime]')) {
    const runtime = document.createElement('script');runtime.type = 'module';runtime.src = '/assets/js/v24-3-6-runtime.js?v=24.4.11';runtime.dataset.v2436Runtime = '';document.head.appendChild(runtime);
  }
})();
