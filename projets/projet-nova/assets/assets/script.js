(function(){
  function ready(fn){document.readyState !== 'loading' ? fn() : document.addEventListener('DOMContentLoaded', fn);}
  ready(function(){
    const page = document.body.getAttribute('data-page') || '';
    document.querySelectorAll('.main-nav .nav-link').forEach(link=>{
      const href = link.getAttribute('href') || '';
      if(href === page || (page === 'index.html' && href === 'index.html')){
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      }
    });
    const toggle = document.querySelector('[data-menu-toggle]');
    const nav = document.querySelector('[data-main-nav]');
    if(toggle && nav){
      const setMenuState = function(open){
        nav.classList.toggle('open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      };
      toggle.addEventListener('click', function(){
        setMenuState(!nav.classList.contains('open'));
      });
      document.addEventListener('keydown', function(event){
        if(event.key === 'Escape' && nav.classList.contains('open')) setMenuState(false);
      });
      document.addEventListener('click', function(event){
        if(window.innerWidth > 1100) return;
        const clickInsideMenu = nav.contains(event.target) || toggle.contains(event.target);
        if(!clickInsideMenu && nav.classList.contains('open')) setMenuState(false);
      });
    }

    const listEl = document.querySelector('[data-doc-list]');
    if(listEl && Array.isArray(window.NOVA_DOCUMENTS)){
      const docs = window.NOVA_DOCUMENTS.slice();
      const searchEl = document.querySelector('[data-doc-search]');
      const filterEl = document.querySelector('[data-doc-filter]');
      const sections = [...new Set(docs.map(d=>d.section))];
      if(filterEl){
        const existing = filterEl.innerHTML.trim();
        if(!existing.includes('Toutes les sections')) filterEl.innerHTML = '<option value="">Toutes les sections</option>';
        sections.forEach(section=>{
          const option = document.createElement('option');
          option.value = section;
          option.textContent = section;
          filterEl.appendChild(option);
        });
      }
      function card(d){
        return `
          <article class="doc-card">
            <span class="pill">${d.section}</span>
            <h3>${d.title}</h3>
            <p>${d.description}</p>
            <div class="card-actions">
              <a class="btn btn-primary" href="visionneuse.html?doc=${encodeURIComponent(d.id)}">Visionner sur le site</a>
              <a class="btn btn-outline" href="${d.path}" download> Télécharger le PDF </a>
            </div>
          </article>`;
      }
      function render(){
        const term = ((searchEl && searchEl.value) || '').toLowerCase().trim();
        const filter = (filterEl && filterEl.value) || '';
        const filtered = docs.filter(d=>{
          const hay = [d.order,d.title,d.section,d.description].join(' ').toLowerCase();
          return (!term || hay.includes(term)) && (!filter || d.section === filter);
        });
        listEl.innerHTML = filtered.length ? filtered.map(card).join('') : '<article class="doc-card"><h3>Aucun résultat</h3><p>Aucun document ne correspond à votre recherche. Modifiez les filtres ou effacez la recherche.</p></article>';
      }
      if(searchEl) searchEl.addEventListener('input', render);
      if(filterEl) filterEl.addEventListener('change', render);
      render();
    }
  });
})();


// Finition AAA : comportement mobile et formulaires
(function(){
  function onReady(fn){document.readyState !== 'loading' ? fn() : document.addEventListener('DOMContentLoaded', fn);}
  onReady(function(){
    document.querySelectorAll('[data-main-nav] a').forEach(function(a){
      a.addEventListener('click', function(){
        const nav=document.querySelector('[data-main-nav]');
        const toggle=document.querySelector('[data-menu-toggle]');
        if(nav && nav.classList.contains('open')){
          nav.classList.remove('open');
          if(toggle) toggle.setAttribute('aria-expanded','false');
        }
      });
    });
    document.querySelectorAll('form.nova-online-form').forEach(function(form){
      form.addEventListener('submit', function(){
        const emailField=form.querySelector('input[type="email"][name="email"], input[type="email"]');
        const email=emailField ? emailField.value.trim() : '';
        form.querySelectorAll('input[name="_replyto"], input[data-copy-replyto]').forEach(function(i){i.value=email;});
        form.querySelectorAll('input[name="_cc"], input[data-copy-cc]').forEach(function(i){i.value=email;});
      });
    });
  });
})();


// Registres publics : comptabilité et rencontres
(function(){
  function ready(fn){document.readyState !== 'loading' ? fn() : document.addEventListener('DOMContentLoaded', fn);}
  function money(n){
    const value = Number(n || 0);
    return new Intl.NumberFormat('fr-CA', {style:'currency', currency:'CAD'}).format(value);
  }
  function text(v){return (v === undefined || v === null || v === '') ? '—' : String(v);}
  ready(function(){
    const financeBody=document.querySelector('[data-finance-table]');
    if(financeBody){
      fetch('data/comptabilite.json', {cache:'no-store'}).then(r=>r.json()).then(data=>{
        const entries=Array.isArray(data.entries)?data.entries:[];
        const income=entries.filter(e=>e.type==='revenu').reduce((s,e)=>s+Number(e.montant||0),0);
        const expense=entries.filter(e=>e.type==='depense').reduce((s,e)=>s+Number(e.montant||0),0);
        document.querySelectorAll('[data-finance-total="income"]').forEach(el=>el.textContent=money(income));
        document.querySelectorAll('[data-finance-total="expense"]').forEach(el=>el.textContent=money(expense));
        document.querySelectorAll('[data-finance-total="balance"]').forEach(el=>el.textContent=money(income-expense));
        if(!entries.length){financeBody.innerHTML='<tr><td colspan="7">Aucune entrée publique publiée pour le moment.</td></tr>'; return;}
        financeBody.innerHTML=entries.map(e=>`<tr><td>${text(e.date)}</td><td>${text(e.type)}</td><td>${text(e.categorie)}</td><td>${text(e.description)}</td><td>${text(e.fournisseur_ou_source)}</td><td>${money(e.montant)}</td><td>${text(e.statut)}</td></tr>`).join('');
      }).catch(()=>{financeBody.innerHTML='<tr><td colspan="7">Registre temporairement indisponible.</td></tr>';});
    }
    const meetingsBody=document.querySelector('[data-meetings-table]');
    if(meetingsBody || document.querySelector('[data-rencontre-count]')){
      fetch('data/rencontres.json', {cache:'no-store'}).then(r=>r.json()).then(data=>{
        const entries=Array.isArray(data.entries)?data.entries:[];
        document.querySelectorAll('[data-rencontre-count]').forEach(el=>el.textContent=String(entries.length));
        if(meetingsBody){
          if(!entries.length){meetingsBody.innerHTML='<tr><td colspan="7">Aucune rencontre publique publiée pour le moment.</td></tr>'; return;}
          meetingsBody.innerHTML=entries.map(e=>`<tr><td>${text(e.date)}</td><td>${text(e.type)}</td><td>${text(e.sujet)}</td><td>${text(e.participants_resume)}</td><td>${text(e.resume_public)}</td><td>${text(e.suivi)}</td><td>${text(e.statut_publication)}</td></tr>`).join('');
        }
      }).catch(()=>{if(meetingsBody) meetingsBody.innerHTML='<tr><td colspan="7">Registre temporairement indisponible.</td></tr>';});
    }
  });
})();
