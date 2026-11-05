// Frontière de confiance : les fichiers JSON publics contiennent du texte,
// jamais du HTML ou des liens exécutables, même si leur source est altérée.
const NOVA_SAFE_DOM=Object.freeze({
  escape(value){
    const entities={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
    return String(value??'').replace(/[&<>"']/g,ch=>entities[ch]);
  },
  pageHref(value){
    const link=String(value??'');
    return /^[a-z0-9][a-z0-9._-]*\.html$/i.test(link)&&!link.includes('..')?link:'';
  },
  pdfHref(value){
    const link=String(value??'');
    return /^documents\/[a-z0-9][a-z0-9._-]*\.pdf$/i.test(link)&&!link.includes('..')?link:'';
  }
});

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
        ['boussole-electorale.html','Boussole électorale'],
        ['constitution.html','Constitution'],
        ['documents.html','Documents'],
        ['transparence.html','Transparence'],
        ['recrutement.html','Participer'],
        ['contact.html','Contact']
      ];
      nav.innerHTML=navItems.map(([href,label])=>{
        const boussoleClass=href==='boussole-electorale.html'?' nav-link-boussole':'';
        return `<a class="nav-link${boussoleClass}" href="${href}">${label}</a>`;
      }).join('');
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
      // Un même contrat d'accessibilité pour les pages Nova et le portail.
      // Conserver le menu utilisable sans souris, y compris après un resize.
      if(!nav.id)nav.id='navigation-principale';
      toggle.setAttribute('aria-controls',nav.id);
      const setMenuState=open=>{
        nav.classList.toggle('open',open);
        toggle.setAttribute('aria-expanded',open?'true':'false');
        toggle.setAttribute('aria-label',open?'Fermer le menu':'Ouvrir le menu');
      };
      setMenuState(false);
      toggle.addEventListener('click',()=>setMenuState(!nav.classList.contains('open')));
      document.addEventListener('keydown',event=>{
        if(event.key!=='Escape'||!nav.classList.contains('open'))return;
        setMenuState(false);
        toggle.focus();
      });
      // Sur Safari tactile, le click synthétique peut arriver tard.
      // pointerdown ferme immédiatement; click couvre aussi les activations
      // au clavier et les environnements sans Pointer Events.
      const closeOnOutside=event=>{
        if(window.innerWidth>1100||!nav.classList.contains('open'))return;
        if(!nav.contains(event.target)&&!toggle.contains(event.target))setMenuState(false);
      };
      document.addEventListener('pointerdown',closeOnOutside);
      document.addEventListener('click',closeOnOutside);
      window.addEventListener('resize',()=>{
        if(window.innerWidth>1100&&nav.classList.contains('open'))setMenuState(false);
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
        const safe=NOVA_SAFE_DOM.escape;
        const pdf=NOVA_SAFE_DOM.pdfHref(d.path);
        const download=pdf?`<a class="btn btn-outline" href="${pdf}" download>Télécharger le PDF</a>`:'<span class="btn btn-outline">Document non approuvé</span>';
        return `<article class="doc-card"><span class="pill">${safe(d.section)}</span><h3>${safe(d.title)}</h3><p>${safe(d.description)}</p><div class="card-actions"><a class="btn btn-primary" href="visionneuse.html?doc=${encodeURIComponent(String(d.id??''))}">Visionner l’archive</a>${download}</div></article>`;
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
        financeBody.innerHTML=entries.map(e=>`<tr><td>${NOVA_SAFE_DOM.escape(text(e.date))}</td><td>${NOVA_SAFE_DOM.escape(text(e.type))}</td><td>${NOVA_SAFE_DOM.escape(text(e.categorie))}</td><td>${NOVA_SAFE_DOM.escape(text(e.description))}</td><td>${NOVA_SAFE_DOM.escape(text(e.fournisseur_ou_source))}</td><td>${money(e.montant)}</td><td>${NOVA_SAFE_DOM.escape(text(e.statut))}</td></tr>`).join('');
      }).catch(()=>{financeBody.innerHTML='<tr><td colspan="7">Registre temporairement indisponible.</td></tr>';});
    }

    const meetingsBody=document.querySelector('[data-meetings-table]');
    if(meetingsBody||document.querySelector('[data-rencontre-count]')){
      fetch('data/rencontres.json',{cache:'no-store'}).then(r=>r.json()).then(data=>{
        const entries=Array.isArray(data.entries)?data.entries:[];
        document.querySelectorAll('[data-rencontre-count]').forEach(el=>el.textContent=String(entries.length));
        if(meetingsBody){
          if(!entries.length){meetingsBody.innerHTML='<tr><td colspan="7">Aucune rencontre publique publiée pour le moment.</td></tr>';return;}
          meetingsBody.innerHTML=entries.map(e=>`<tr><td>${NOVA_SAFE_DOM.escape(text(e.date))}</td><td>${NOVA_SAFE_DOM.escape(text(e.type))}</td><td>${NOVA_SAFE_DOM.escape(text(e.sujet))}</td><td>${NOVA_SAFE_DOM.escape(text(e.participants_resume))}</td><td>${NOVA_SAFE_DOM.escape(text(e.resume_public))}</td><td>${NOVA_SAFE_DOM.escape(text(e.suivi))}</td><td>${NOVA_SAFE_DOM.escape(text(e.statut_publication))}</td></tr>`).join('');
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
        updates.innerHTML=entries.map(e=>{
          const safe=NOVA_SAFE_DOM.escape;
          const link=NOVA_SAFE_DOM.pageHref(e.link);
          const linkHtml=link?`<a class="text-link" href="${link}">${safe(text(e.link_label||'Consulter'))}</a>`:'';
          return `<article class="timeline-entry"><div class="timeline-meta"><time datetime="${safe(text(e.date))}">${safe(formatDate(e.date))}</time><span>${safe(text(e.type))}</span></div><h2>${safe(text(e.title))}</h2><p>${safe(text(e.summary))}</p>${linkHtml}</article>`;
        }).join('');
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