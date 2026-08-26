(function(){
  if(!document.querySelector('link[data-nova-institutionnel]')){
    const polish=document.createElement('link');
    polish.rel='stylesheet';
    polish.href='assets/nova-institutionnel.css?v=2';
    polish.setAttribute('data-nova-institutionnel','');
    document.head.appendChild(polish);
  }
  if(!document.querySelector('link[data-nova-maturite]')){
    const maturity=document.createElement('link');
    maturity.rel='stylesheet';
    maturity.href='assets/nova-maturite.css?v=1';
    maturity.setAttribute('data-nova-maturite','');
    document.head.appendChild(maturity);
  }
})();

(function(){
  function ready(fn){document.readyState !== 'loading' ? fn() : document.addEventListener('DOMContentLoaded', fn);}
  ready(function(){
    const page=document.body.getAttribute('data-page')||'';
    const nav=document.querySelector('[data-main-nav]');

    document.querySelectorAll('.header-project-pro').forEach(el=>el.textContent='Projet Nova');
    document.querySelectorAll('.header-tagline-pro').forEach(el=>el.textContent='Le peuple d’abord — des institutions responsables');

    if(nav){
      const navItems=[
        ['index.html','Accueil'],
        ['comprendre-nova.html','Comprendre Nova'],
        ['programme.html','Programme'],
        ['constitution.html','Constitution'],
        ['documents.html','Documents'],
        ['transparence.html','Transparence'],
        ['recrutement.html','Participer'],
        ['contact.html','Contact']
      ];
      nav.innerHTML=navItems.map(([href,label])=>`<a class="nav-link" href="${href}">${label}</a>`).join('');
    }

    document.querySelectorAll('.main-nav .nav-link').forEach(link=>{
      const href=link.getAttribute('href')||'';
      if(href===page||(page==='index.html'&&href==='index.html')){
        link.classList.add('active');
        link.setAttribute('aria-current','page');
      }
    });

    const toggle=document.querySelector('[data-menu-toggle]');
    if(toggle&&nav){
      const setMenuState=open=>{nav.classList.toggle('open',open);toggle.setAttribute('aria-expanded',open?'true':'false');};
      toggle.addEventListener('click',()=>setMenuState(!nav.classList.contains('open')));
      document.addEventListener('keydown',event=>{if(event.key==='Escape'&&nav.classList.contains('open'))setMenuState(false);});
      document.addEventListener('click',event=>{
        if(window.innerWidth>1100)return;
        if(!nav.contains(event.target)&&!toggle.contains(event.target)&&nav.classList.contains('open'))setMenuState(false);
      });
      nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>setMenuState(false)));
    }

    const footerNav=[...document.querySelectorAll('.footer section')].find(section=>{
      const h=section.querySelector('h3');
      return h&&h.textContent.trim()==='Navigation';
    });
    if(footerNav){
      const list=footerNav.querySelector('ul');
      if(list){
        list.innerHTML=[
          ['index.html','Accueil'],['comprendre-nova.html','Comprendre Nova'],['programme.html','Programme'],
          ['constitution.html','Constitution'],['documents.html','Documents'],['transparence.html','Transparence'],
          ['recrutement.html','Participer'],['equipe.html','Organisation et équipe'],['actualites.html','Actualités'],
          ['presse.html','Centre médias'],['faq.html','FAQ'],['contact.html','Contact']
        ].map(([href,label])=>`<li><a href="${href}">${label}</a></li>`).join('');
      }
    }

    const listEl=document.querySelector('[data-doc-list]');
    if(listEl&&Array.isArray(window.NOVA_DOCUMENTS)){
      const docs=window.NOVA_DOCUMENTS.slice();
      const searchEl=document.querySelector('[data-doc-search]');
      const filterEl=document.querySelector('[data-doc-filter]');
      const sections=[...new Set(docs.map(d=>d.section))];
      if(filterEl){
        if(!filterEl.innerHTML.includes('Toutes les sections'))filterEl.innerHTML='<option value="">Toutes les sections</option>';
        sections.forEach(section=>{const option=document.createElement('option');option.value=section;option.textContent=section;filterEl.appendChild(option);});
      }
      function card(d){
        return `<article class="doc-card"><span class="pill">${d.section}</span><h3>${d.title}</h3><p>${d.description}</p><div class="card-actions"><a class="btn btn-primary" href="visionneuse.html?doc=${encodeURIComponent(d.id)}">Visionner l’archive</a><a class="btn btn-outline" href="${d.path}" download>Télécharger le PDF</a></div></article>`;
      }
      function render(){
        const term=((searchEl&&searchEl.value)||'').toLowerCase().trim();
        const filter=(filterEl&&filterEl.value)||'';
        const filtered=docs.filter(d=>{const hay=[d.order,d.title,d.section,d.description].join(' ').toLowerCase();return(!term||hay.includes(term))&&(!filter||d.section===filter);});
        listEl.innerHTML=filtered.length?filtered.map(card).join(''):'<article class="doc-card"><h3>Aucun résultat</h3><p>Aucun document ne correspond à votre recherche.</p></article>';
      }
      if(searchEl)searchEl.addEventListener('input',render);
      if(filterEl)filterEl.addEventListener('change',render);
      render();
    }
  });
})();

(function(){
  function ready(fn){document.readyState !== 'loading' ? fn() : document.addEventListener('DOMContentLoaded', fn);}
  function money(n){return new Intl.NumberFormat('fr-CA',{style:'currency',currency:'CAD'}).format(Number(n||0));}
  function text(v){return(v===undefined||v===null||v==='')?'—':String(v);}
  function formatDate(value){
    if(!value)return '—';
    const d=new Date(value+'T12:00:00');
    return Number.isNaN(d.getTime())?value:new Intl.DateTimeFormat('fr-CA',{year:'numeric',month:'long',day:'numeric'}).format(d);
  }
  ready(function(){
    const financeBody=document.querySelector('[data-finance-table]');
    if(financeBody){
      fetch('data/comptabilite.json',{cache:'no-store'}).then(r=>r.json()).then(data=>{
        const entries=Array.isArray(data.entries)?data.entries:[];
        const income=entries.filter(e=>e.type==='revenu').reduce((s,e)=>s+Number(e.montant||0),0);
        const expense=entries.filter(e=>e.type==='depense').reduce((s,e)=>s+Number(e.montant||0),0);
        document.querySelectorAll('[data-finance-total="income"]').forEach(el=>el.textContent=money(income));
        document.querySelectorAll('[data-finance-total="expense"]').forEach(el=>el.textContent=money(expense));
        document.querySelectorAll('[data-finance-total="balance"]').forEach(el=>el.textContent=money(income-expense));
        if(!entries.length){financeBody.innerHTML='<tr><td colspan="7">Aucune entrée publique publiée pour le moment.</td></tr>';return;}
        financeBody.innerHTML=entries.map(e=>`<tr><td>${text(e.date)}</td><td>${text(e.type)}</td><td>${text(e.categorie)}</td><td>${text(e.description)}</td><td>${text(e.fournisseur_ou_source)}</td><td>${money(e.montant)}</td><td>${text(e.statut)}</td></tr>`).join('');
      }).catch(()=>{financeBody.innerHTML='<tr><td colspan="7">Registre temporairement indisponible.</td></tr>';});
    }

    const meetingsBody=document.querySelector('[data-meetings-table]');
    if(meetingsBody||document.querySelector('[data-rencontre-count]')){
      fetch('data/rencontres.json',{cache:'no-store'}).then(r=>r.json()).then(data=>{
        const entries=Array.isArray(data.entries)?data.entries:[];
        document.querySelectorAll('[data-rencontre-count]').forEach(el=>el.textContent=String(entries.length));
        if(meetingsBody){
          if(!entries.length){meetingsBody.innerHTML='<tr><td colspan="7">Aucune rencontre publique publiée pour le moment.</td></tr>';return;}
          meetingsBody.innerHTML=entries.map(e=>`<tr><td>${text(e.date)}</td><td>${text(e.type)}</td><td>${text(e.sujet)}</td><td>${text(e.participants_resume)}</td><td>${text(e.resume_public)}</td><td>${text(e.suivi)}</td><td>${text(e.statut_publication)}</td></tr>`).join('');
        }
      }).catch(()=>{if(meetingsBody)meetingsBody.innerHTML='<tr><td colspan="7">Registre temporairement indisponible.</td></tr>';});
    }

    const updates=document.querySelector('[data-public-updates]');
    if(updates){
      fetch('data/actualites.json',{cache:'no-store'}).then(r=>r.json()).then(data=>{
        const entries=Array.isArray(data.entries)?data.entries:[];
        const stamp=document.querySelector('[data-updates-date]');
        if(stamp)stamp.textContent=data.updated?formatDate(data.updated):'—';
        if(!entries.length){updates.innerHTML='<article class="timeline-entry"><h2>Aucune mise à jour publiée</h2><p>Le journal public sera complété au fil des changements significatifs.</p></article>';return;}
        updates.innerHTML=entries.map(e=>`<article class="timeline-entry"><div class="timeline-meta"><time datetime="${text(e.date)}">${formatDate(e.date)}</time><span>${text(e.type)}</span></div><h2>${text(e.title)}</h2><p>${text(e.summary)}</p>${e.link?`<a class="text-link" href="${e.link}">${text(e.link_label||'Consulter')}</a>`:''}</article>`).join('');
      }).catch(()=>{updates.innerHTML='<article class="timeline-entry"><h2>Journal temporairement indisponible</h2><p>Les autres pages publiques demeurent accessibles.</p></article>';});
    }
  });
})();

(function(){
  if(document.documentElement.getAttribute('data-disable-sinjira-assistant')==='true')return;
  if(!document.querySelector('link[data-sinjira-assistant-style]')){
    const style=document.createElement('link');style.rel='stylesheet';style.href='/assets/css/sinjira-assistant.css?v=24.4.48';style.setAttribute('data-sinjira-assistant-style','');document.head.appendChild(style);
  }
  if(!document.querySelector('script[data-sinjira-assistant-script]')){
    const script=document.createElement('script');script.src='/assets/js/sinjira-assistant.js?v=24.4.48';script.defer=true;script.setAttribute('data-sinjira-assistant-script','');document.head.appendChild(script);
  }
})();