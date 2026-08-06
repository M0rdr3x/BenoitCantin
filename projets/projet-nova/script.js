(function () {
  'use strict';

  const FORMSPREE_NOVA_ENDPOINT = 'https://formspree.io/f/xkolwjdg';

  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

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

  function configureNovaForm(form) {
    form.action = FORMSPREE_NOVA_ENDPOINT;
    form.method = 'POST';
    form.acceptCharset = 'UTF-8';

    if (form.querySelector('input[type="file"]')) {
      form.enctype = 'multipart/form-data';
    }

    [
      '_template',
      '_next',
      '_captcha',
      '_autoresponse',
      '_cc',
      '_replyto'
    ].forEach((name) => {
      form.querySelectorAll(`input[name="${name}"]`).forEach((field) => field.remove());
    });

    const label =
      form.querySelector('input[name="Formulaire"]')?.value ||
      form.id ||
      document.title ||
      'Formulaire Projet Nova';

    ensureHiddenField(form, '_subject', `Projet Nova — ${label}`);
    ensureHiddenField(form, 'source_site', 'Projet Nova');
    ensureHiddenField(form, 'source_formulaire', label);
    ensureHiddenField(form, 'source_page', window.location.href);

    form.addEventListener('submit', () => {
      const status = form.querySelector('.form-status');
      if (status) {
        status.textContent =
          'Transmission sécurisée en cours… Vous serez dirigé vers la confirmation Formspree.';
      }

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

  function configureNavigation() {
    const page = document.body.getAttribute('data-page') || '';

    document.querySelectorAll('.main-nav .nav-link').forEach((link) => {
      const href = link.getAttribute('href') || '';
      if (href === page || (page === 'index.html' && href === 'index.html')) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      }
    });

    const toggle = document.querySelector('[data-menu-toggle]');
    const nav = document.querySelector('[data-main-nav]');

    if (!toggle || !nav) {
      return;
    }

    const setMenuState = (open) => {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    };

    toggle.addEventListener('click', () => {
      setMenuState(!nav.classList.contains('open'));
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && nav.classList.contains('open')) {
        setMenuState(false);
      }
    });

    document.addEventListener('click', (event) => {
      if (window.innerWidth > 1100) {
        return;
      }

      const clickInsideMenu =
        nav.contains(event.target) || toggle.contains(event.target);

      if (!clickInsideMenu && nav.classList.contains('open')) {
        setMenuState(false);
      }
    });

    nav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => setMenuState(false));
    });
  }

  function configureDocuments() {
    const listEl = document.querySelector('[data-doc-list]');

    if (!listEl || !Array.isArray(window.NOVA_DOCUMENTS)) {
      return;
    }

    const docs = window.NOVA_DOCUMENTS.slice();
    const searchEl = document.querySelector('[data-doc-search]');
    const filterEl = document.querySelector('[data-doc-filter]');
    const sections = [...new Set(docs.map((doc) => doc.section))];

    if (filterEl) {
      const existing = filterEl.innerHTML.trim();

      if (!existing.includes('Toutes les sections')) {
        filterEl.innerHTML = '<option value="">Toutes les sections</option>';
      }

      sections.forEach((section) => {
        const option = document.createElement('option');
        option.value = section;
        option.textContent = section;
        filterEl.appendChild(option);
      });
    }

    function card(doc) {
      return `
        <article class="doc-card">
          <span class="pill">${doc.section}</span>
          <h3>${doc.title}</h3>
          <p>${doc.description}</p>
          <div class="card-actions">
            <a class="btn btn-primary"
               href="visionneuse.html?doc=${encodeURIComponent(doc.id)}">
              Visionner sur le site
            </a>
            <a class="btn btn-outline" href="${doc.path}" download>
              Télécharger le PDF
            </a>
          </div>
        </article>`;
    }

    function render() {
      const term = ((searchEl && searchEl.value) || '').toLowerCase().trim();
      const filter = (filterEl && filterEl.value) || '';

      const filtered = docs.filter((doc) => {
        const haystack = [
          doc.order,
          doc.title,
          doc.section,
          doc.description
        ]
          .join(' ')
          .toLowerCase();

        return (
          (!term || haystack.includes(term)) &&
          (!filter || doc.section === filter)
        );
      });

      listEl.innerHTML = filtered.length
        ? filtered.map(card).join('')
        : '<article class="doc-card"><h3>Aucun résultat</h3><p>Aucun document ne correspond à votre recherche. Modifiez les filtres ou effacez la recherche.</p></article>';
    }

    if (searchEl) {
      searchEl.addEventListener('input', render);
    }

    if (filterEl) {
      filterEl.addEventListener('change', render);
    }

    render();
  }

  function money(number) {
    const value = Number(number || 0);
    return new Intl.NumberFormat('fr-CA', {
      style: 'currency',
      currency: 'CAD'
    }).format(value);
  }

  function text(value) {
    return value === undefined || value === null || value === ''
      ? '—'
      : String(value);
  }

  function configurePublicRegisters() {
    const financeBody = document.querySelector('[data-finance-table]');

    if (financeBody) {
      fetch('data/comptabilite.json', { cache: 'no-store' })
        .then((response) => response.json())
        .then((data) => {
          const entries = Array.isArray(data.entries) ? data.entries : [];
          const income = entries
            .filter((entry) => entry.type === 'revenu')
            .reduce((sum, entry) => sum + Number(entry.montant || 0), 0);
          const expense = entries
            .filter((entry) => entry.type === 'depense')
            .reduce((sum, entry) => sum + Number(entry.montant || 0), 0);

          document
            .querySelectorAll('[data-finance-total="income"]')
            .forEach((element) => {
              element.textContent = money(income);
            });

          document
            .querySelectorAll('[data-finance-total="expense"]')
            .forEach((element) => {
              element.textContent = money(expense);
            });

          document
            .querySelectorAll('[data-finance-total="balance"]')
            .forEach((element) => {
              element.textContent = money(income - expense);
            });

          if (!entries.length) {
            financeBody.innerHTML =
              '<tr><td colspan="7">Aucune entrée publique publiée pour le moment.</td></tr>';
            return;
          }

          financeBody.innerHTML = entries
            .map(
              (entry) =>
                `<tr>
                  <td>${text(entry.date)}</td>
                  <td>${text(entry.type)}</td>
                  <td>${text(entry.categorie)}</td>
                  <td>${text(entry.description)}</td>
                  <td>${text(entry.fournisseur_ou_source)}</td>
                  <td>${money(entry.montant)}</td>
                  <td>${text(entry.statut)}</td>
                </tr>`
            )
            .join('');
        })
        .catch(() => {
          financeBody.innerHTML =
            '<tr><td colspan="7">Registre temporairement indisponible.</td></tr>';
        });
    }

    const meetingsBody = document.querySelector('[data-meetings-table]');
    const meetingCount = document.querySelector('[data-rencontre-count]');

    if (!meetingsBody && !meetingCount) {
      return;
    }

    fetch('data/rencontres.json', { cache: 'no-store' })
      .then((response) => response.json())
      .then((data) => {
        const entries = Array.isArray(data.entries) ? data.entries : [];

        document
          .querySelectorAll('[data-rencontre-count]')
          .forEach((element) => {
            element.textContent = String(entries.length);
          });

        if (!meetingsBody) {
          return;
        }

        if (!entries.length) {
          meetingsBody.innerHTML =
            '<tr><td colspan="7">Aucune rencontre publique publiée pour le moment.</td></tr>';
          return;
        }

        meetingsBody.innerHTML = entries
          .map(
            (entry) =>
              `<tr>
                <td>${text(entry.date)}</td>
                <td>${text(entry.type)}</td>
                <td>${text(entry.sujet)}</td>
                <td>${text(entry.participants_resume)}</td>
                <td>${text(entry.resume_public)}</td>
                <td>${text(entry.suivi)}</td>
                <td>${text(entry.statut_publication)}</td>
              </tr>`
          )
          .join('');
      })
      .catch(() => {
        if (meetingsBody) {
          meetingsBody.innerHTML =
            '<tr><td colspan="7">Registre temporairement indisponible.</td></tr>';
        }
      });
  }

  ready(() => {
    configureNavigation();
    configureDocuments();
    configurePublicRegisters();

    document
      .querySelectorAll('form.nova-online-form')
      .forEach(configureNovaForm);
  });
})();
