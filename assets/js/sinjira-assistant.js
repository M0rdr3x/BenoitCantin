(function () {
  'use strict';

  var doc = document;
  var ASSISTANT_VERSION = '24.4.39';
  var PROVIDER_MODE = 'local';
  var EXTERNAL_PROVIDER_ENABLED = false;
  var MAX_MESSAGE_LENGTH = 500;
  var MAX_HISTORY = 20;
  var history = [];
  var lastSubmitAt = 0;

  if (doc.querySelector('[data-sinjira-assistant-root]')) return;

  function normalize(value) {
    var text = String(value || '').toLowerCase();
    if (text.normalize) text = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    return text.replace(/[^a-z0-9\s'-]/g, ' ').replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, '');
  }

  function tokenize(value) {
    var text = normalize(value);
    return text ? text.split(' ') : [];
  }

  function isYouthContext() {
    var path = String(window.location.pathname || '').toLowerCase();
    var body = doc.body;
    return /\/(jeunesse|jeune|enfant|guardian|tuteur)\//.test(path) ||
      Boolean(body && (
        body.getAttribute('data-youth-mode') === 'true' ||
        body.getAttribute('data-account-age-group') === 'youth' ||
        body.getAttribute('data-sinjira-audience') === 'youth'
      ));
  }

  var INTENTS = [
    {
      id: 'sinjira',
      label: 'Découvrir SINJIRA™',
      keywords: ['sinjira', 'univers', 'science fiction', 'saga', 'plateforme', 'c est quoi', 'quest ce que'],
      answer: 'SINJIRA™ est l’univers narratif et interactif de Benoit Cantin. Le portail réunit notamment les romans, les jeux, le Registre des Consciences, la Communauté et le Monde parallèle.',
      links: [
        { label: 'Ouvrir SINJIRA™', href: '/projets/sinjira/' },
        { label: 'Voir les romans', href: '/projets/sinjira/romans/' }
      ],
      youthSafe: true
    },
    {
      id: 'registre',
      label: 'Créer mon personnage',
      keywords: ['registre', 'conscience', 'personnage', 'creer personnage', 'creation personnage', 'questionnaire', 'fan'],
      answer: 'Le Registre des Consciences vous permet de remplir un questionnaire simple lié à votre Compte SINJIRA™. Il sert de base humaine pour préparer votre personnage original et suivre ensuite son état depuis votre compte.',
      links: [
        { label: 'Ouvrir le Registre', href: '/projets/sinjira/registre/' },
        { label: 'Voir mon personnage', href: '/compte/mon-personnage.html' }
      ],
      youthSafe: true
    },
    {
      id: 'romans',
      label: 'Lire les romans',
      keywords: ['roman', 'romans', 'livre', 'livres', 'lecture', 'lire', 'cendre', 'jugement'],
      answer: 'La section Romans regroupe la lecture disponible de SINJIRA™, la progression du lecteur et l’accès aux contenus littéraires publiés sur le site.',
      links: [
        { label: 'Ouvrir les romans', href: '/projets/sinjira/romans/' },
        { label: 'Ma bibliothèque', href: '/compte/bibliotheque.html' }
      ],
      youthSafe: true
    },
    {
      id: 'jeux',
      label: 'Trouver un jeu',
      keywords: ['jeu', 'jeux', 'jouer', 'partie', 'parties', 'game'],
      answer: 'La porte Jeux rassemble les expériences interactives de SINJIRA™. Vous pouvez y voir les jeux disponibles et rejoindre les parcours prévus par chaque titre.',
      links: [
        { label: 'Ouvrir les jeux', href: '/projets/sinjira/jeux/' },
        { label: 'Mes parties', href: '/compte/mes-parties.html' }
      ],
      youthSafe: true
    },
    {
      id: 'fracture',
      label: 'Aide pour Fracture',
      keywords: ['fracture', 'reseau mere', 'resistance', 'identite', 'accusation', 'carte', 'cartes'],
      answer: 'Fracture du Réseau-Mère est une expérience de déduction sociale de SINJIRA™. Le moteur protège les identités cachées pendant la partie et révèle les informations prévues au moment approprié.',
      links: [
        { label: 'Ouvrir Fracture', href: '/projets/sinjira/jeux/fracture-du-reseau-mere/' },
        { label: 'Voir mes parties', href: '/compte/mes-parties.html' }
      ],
      youthSafe: true
    },
    {
      id: 'compte',
      label: 'Aide avec mon compte',
      keywords: ['compte', 'connexion', 'connecter', 'login', 'profil', 'espace', 'pseudo', 'deconnexion'],
      answer: 'Le Compte SINJIRA™ centralise votre profil, votre bibliothèque, vos personnages, vos parties et vos réglages. Je peux vous guider vers la bonne page, mais je ne peux pas lire vos données privées ni vos identifiants.',
      links: [
        { label: 'Ouvrir mon espace', href: '/compte/' },
        { label: 'Se connecter', href: '/compte/connexion.html' }
      ],
      youthSafe: true
    },
    {
      id: 'password',
      label: 'Mot de passe ou connexion',
      keywords: ['mot de passe', 'password', 'oublie', 'oublier', 'recuperer', 'reinitialiser', 'reinitialisation', 'connexion impossible'],
      answer: 'Je ne peux jamais voir votre mot de passe. Si vous ne pouvez plus vous connecter, utilisez le parcours officiel de récupération du compte. Ne communiquez jamais votre mot de passe dans cette fenêtre.',
      links: [
        { label: 'Récupérer mon compte', href: '/compte/mot-de-passe-oublie.html' },
        { label: 'Sécurité du compte', href: '/compte/securite.html' }
      ],
      youthSafe: true
    },
    {
      id: 'community',
      label: 'Communauté et Monde parallèle',
      keywords: ['communaute', 'monde parallele', 'reseau personnage', 'social', 'message', 'messages', 'transmission', 'canal'],
      answer: 'SINJIRA™ sépare les espaces du membre réel et ceux du personnage. La Communauté sert aux échanges du membre; le Réseau personnage et le Monde parallèle servent à la continuité narrative du personnage lorsque l’accès correspondant est disponible.',
      links: [
        { label: 'Voir la Communauté', href: '/projets/sinjira/communaute/' },
        { label: 'Monde parallèle', href: '/projets/sinjira/monde-parallele/' }
      ],
      youthSafe: true
    },
    {
      id: 'nova',
      label: 'Découvrir Projet Nova',
      keywords: ['nova', 'projet nova', 'citoyen', 'citoyenne', 'proposition', 'propositions'],
      answer: 'Projet Nova est l’espace consacré au projet citoyen indépendant de Benoit Cantin. Il présente sa démarche, ses propositions et ses documents dans une section distincte de SINJIRA™.',
      links: [
        { label: 'Ouvrir Projet Nova', href: '/projets/projet-nova/' }
      ],
      youthSafe: true
    },
    {
      id: 'privacy',
      label: 'Vie privée et sécurité',
      keywords: ['confidentialite', 'vie privee', 'prive', 'donnee', 'donnees', 'securite', 'trace', 'conversation', 'stocke'],
      answer: 'Cet assistant fonctionne localement dans votre navigateur. Votre texte n’est pas envoyé à un fournisseur d’IA externe et la conversation de cette fenêtre n’est pas enregistrée par l’assistant. Pour les règles générales du site, consultez la page Confidentialité.',
      links: [
        { label: 'Lire Confidentialité', href: '/confidentialite.html' },
        { label: 'Sécurité du compte', href: '/compte/securite.html' }
      ],
      youthSafe: true
    },
    {
      id: 'contact',
      label: 'Contacter Benoit Cantin',
      keywords: ['contact', 'contacter', 'humain', 'aide humaine', 'support', 'courriel', 'email', 'question autre'],
      answer: 'Pour une question qui demande une intervention humaine ou qui dépasse l’aide du site, utilisez la page Contact officielle.',
      links: [
        { label: 'Ouvrir Contact', href: '/contact.html' }
      ],
      youthSafe: true
    }
  ];

  function scoreIntent(intent, query, tokens) {
    var normalizedQuery = normalize(query);
    var score = 0;
    for (var i = 0; i < intent.keywords.length; i += 1) {
      var keyword = normalize(intent.keywords[i]);
      if (!keyword) continue;
      if (normalizedQuery === keyword) score += 10;
      else if (normalizedQuery.indexOf(keyword) !== -1) score += keyword.indexOf(' ') !== -1 ? 6 : 3;
      var keywordTokens = tokenize(keyword);
      for (var k = 0; k < keywordTokens.length; k += 1) {
        if (tokens.indexOf(keywordTokens[k]) !== -1) score += 1;
      }
    }
    return score;
  }

  function getReply(query) {
    var tokens = tokenize(query);
    var youth = isYouthContext();
    var best = null;
    var bestScore = 0;

    for (var i = 0; i < INTENTS.length; i += 1) {
      var intent = INTENTS[i];
      if (youth && intent.youthSafe !== true) continue;
      var score = scoreIntent(intent, query, tokens);
      if (score > bestScore) {
        best = intent;
        bestScore = score;
      }
    }

    if (!best || bestScore < 3) {
      return {
        id: 'fallback',
        answer: 'Je suis l’assistant intelligent local du site. Je peux vous guider dans SINJIRA™, le Registre des Consciences, les romans, les jeux, votre compte, Projet Nova, la confidentialité ou la page Contact. Essayez de préciser ce que vous cherchez.',
        links: [
          { label: 'Accueil', href: '/' },
          { label: 'SINJIRA™', href: '/projets/sinjira/' },
          { label: 'Contact', href: '/contact.html' }
        ]
      };
    }
    return best;
  }

  function el(tag, className, text) {
    var node = doc.createElement(tag);
    if (className) node.className = className;
    if (typeof text === 'string') node.textContent = text;
    return node;
  }

  var root = el('div', 'sinjira-assistant');
  root.setAttribute('data-sinjira-assistant-root', '');

  var toggle = el('button', 'sinjira-assistant-toggle', 'Aide IA');
  toggle.type = 'button';
  toggle.setAttribute('aria-expanded', 'false');
  toggle.setAttribute('aria-controls', 'sinjira-assistant-panel');
  toggle.setAttribute('aria-label', 'Ouvrir l’assistant intelligent SINJIRA');

  var panel = el('section', 'sinjira-assistant-panel');
  panel.id = 'sinjira-assistant-panel';
  panel.hidden = true;
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-modal', 'false');
  panel.setAttribute('aria-labelledby', 'sinjira-assistant-title');
  panel.setAttribute('aria-describedby', 'sinjira-assistant-privacy');

  var header = el('div', 'sinjira-assistant-header');
  var headingWrap = el('div', 'sinjira-assistant-heading');
  var eyebrow = el('span', 'sinjira-assistant-eyebrow', 'Assistant local · privé');
  var title = el('h2', '', 'Assistant SINJIRA');
  title.id = 'sinjira-assistant-title';
  headingWrap.appendChild(eyebrow);
  headingWrap.appendChild(title);
  var close = el('button', 'sinjira-assistant-close', '×');
  close.type = 'button';
  close.setAttribute('aria-label', 'Fermer l’assistant');
  header.appendChild(headingWrap);
  header.appendChild(close);

  var intro = el('p', 'sinjira-assistant-intro', 'Posez une question sur le site. Je vous guide sans envoyer votre message à un service d’IA externe.');

  var suggestions = el('div', 'sinjira-assistant-suggestions');
  suggestions.setAttribute('aria-label', 'Questions suggérées');
  var suggestedIntentIds = ['sinjira', 'registre', 'compte', 'nova'];
  for (var s = 0; s < suggestedIntentIds.length; s += 1) {
    for (var si = 0; si < INTENTS.length; si += 1) {
      if (INTENTS[si].id !== suggestedIntentIds[s]) continue;
      var suggestion = el('button', 'sinjira-assistant-chip', INTENTS[si].label);
      suggestion.type = 'button';
      suggestion.setAttribute('data-assistant-question', INTENTS[si].keywords[0]);
      suggestions.appendChild(suggestion);
    }
  }

  var log = el('div', 'sinjira-assistant-log');
  log.setAttribute('role', 'log');
  log.setAttribute('aria-live', 'polite');
  log.setAttribute('aria-relevant', 'additions text');
  log.setAttribute('aria-label', 'Conversation avec l’assistant');

  var form = el('form', 'sinjira-assistant-form');
  form.setAttribute('data-sinjira-assistant-form', '');
  var label = el('label', 'sinjira-assistant-sr', 'Votre question');
  label.setAttribute('for', 'sinjira-assistant-input');
  var input = doc.createElement('textarea');
  input.id = 'sinjira-assistant-input';
  input.className = 'sinjira-assistant-input';
  input.name = 'question';
  input.rows = 2;
  input.maxLength = MAX_MESSAGE_LENGTH;
  input.placeholder = 'Ex. Comment créer mon personnage ?';
  input.setAttribute('autocomplete', 'off');
  input.setAttribute('spellcheck', 'true');
  var submit = el('button', 'sinjira-assistant-send', 'Envoyer');
  submit.type = 'submit';
  form.appendChild(label);
  form.appendChild(input);
  form.appendChild(submit);

  var privacy = el('p', 'sinjira-assistant-privacy', 'Mode V24.4.39 : conversation éphémère dans cet onglet, sans fournisseur d’IA externe. Ne saisissez jamais un mot de passe ou une information très sensible.');
  privacy.id = 'sinjira-assistant-privacy';

  panel.appendChild(header);
  panel.appendChild(intro);
  panel.appendChild(suggestions);
  panel.appendChild(log);
  panel.appendChild(form);
  panel.appendChild(privacy);
  root.appendChild(toggle);
  root.appendChild(panel);
  doc.body.appendChild(root);

  function appendMessage(role, text, links) {
    var item = el('article', 'sinjira-assistant-message sinjira-assistant-message-' + role);
    var roleLabel = el('strong', 'sinjira-assistant-message-role', role === 'user' ? 'Vous' : 'Assistant SINJIRA');
    var body = el('p', '', text);
    item.appendChild(roleLabel);
    item.appendChild(body);

    if (links && links.length) {
      var linkWrap = el('div', 'sinjira-assistant-links');
      for (var i = 0; i < links.length; i += 1) {
        var link = el('a', 'sinjira-assistant-link', links[i].label);
        link.href = links[i].href;
        linkWrap.appendChild(link);
      }
      item.appendChild(linkWrap);
    }

    log.appendChild(item);
    while (log.children.length > MAX_HISTORY) log.removeChild(log.firstChild);
    log.scrollTop = log.scrollHeight;
  }

  function ask(rawQuestion) {
    var question = String(rawQuestion || '').replace(/^\s+|\s+$/g, '').slice(0, MAX_MESSAGE_LENGTH);
    if (!question) return;
    var now = Date.now();
    if (now - lastSubmitAt < 350) return;
    lastSubmitAt = now;

    appendMessage('user', question);
    history.push({ role: 'user', text: question });
    var reply = getReply(question);
    history.push({ role: 'assistant', intent: reply.id || 'matched' });
    if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
    appendMessage('assistant', reply.answer, reply.links || []);
  }

  function openPanel() {
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    root.className = 'sinjira-assistant is-open';
    if (!log.children.length) {
      appendMessage('assistant', 'Bonjour. Je peux vous aider à trouver une section du site ou à comprendre les principaux parcours SINJIRA™. Que cherchez-vous ?');
    }
    window.setTimeout(function () { input.focus(); }, 0);
  }

  function closePanel() {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    root.className = 'sinjira-assistant';
    toggle.focus();
  }

  toggle.addEventListener('click', function () {
    if (panel.hidden) openPanel();
    else closePanel();
  });
  close.addEventListener('click', closePanel);

  suggestions.addEventListener('click', function (event) {
    var target = event.target;
    if (!target || target.tagName !== 'BUTTON') return;
    var question = target.getAttribute('data-assistant-question') || target.textContent || '';
    ask(question);
  });

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var question = input.value;
    input.value = '';
    ask(question);
  });

  input.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (form.requestSubmit) form.requestSubmit();
      else submit.click();
    }
  });

  doc.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && !panel.hidden) closePanel();
  });

  var publicApi = {
    version: ASSISTANT_VERSION,
    providerMode: PROVIDER_MODE,
    externalProviderEnabled: EXTERNAL_PROVIDER_ENABLED,
    privacy: 'ephemeral-memory-only',
    open: openPanel
  };
  window.__SINJIRA_ASSISTANT__ = Object.freeze ? Object.freeze(publicApi) : publicApi;
}());