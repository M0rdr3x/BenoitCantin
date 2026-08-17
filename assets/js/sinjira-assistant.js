(function () {
  'use strict';

  var doc = document;
  var ASSISTANT_VERSION = '24.4.45';
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

  var PAGE_CONTEXTS = [
    { match: /^\/$/, label: 'Accueil Benoit Cantin', answer: 'Vous êtes sur le portail principal. Les trois accès mis de l’avant sont SINJIRA™, le Registre des Consciences et Projet Nova.', links: [{ label: 'SINJIRA™', href: '/projets/sinjira/' }, { label: 'Registre', href: '/projets/sinjira/registre/' }, { label: 'Projet Nova', href: '/projets/projet-nova/' }] },
    { match: /^\/projets\/sinjira\/registre\//, label: 'Registre des Consciences', answer: 'Vous êtes dans le Registre des Consciences. Le questionnaire fournit la base humaine de votre personnage SINJIRA™. Les données de compte restent distinctes de la fiche publique du personnage.', links: [{ label: 'Mon personnage', href: '/compte/mon-personnage.html' }, { label: 'Mon compte', href: '/compte/' }] },
    { match: /^\/projets\/sinjira\/romans\//, label: 'Romans SINJIRA™', answer: 'Vous êtes dans l’espace Romans de SINJIRA™. Vous pouvez y consulter les œuvres disponibles et poursuivre votre parcours de lecture.', links: [{ label: 'Voir les romans', href: '/projets/sinjira/romans/' }, { label: 'Ma bibliothèque', href: '/compte/bibliotheque.html' }] },
    { match: /^\/projets\/sinjira\/jeux\/fracture-du-reseau-mere\//, label: 'Fracture du Réseau-Mère', answer: 'Vous êtes dans Fracture du Réseau-Mère. Votre identité de faction est privée pendant la partie; les identités des autres joueurs restent cachées jusqu’au moment prévu par les règles.', links: [{ label: 'Accueil Fracture', href: '/projets/sinjira/jeux/fracture-du-reseau-mere/' }, { label: 'Mes parties', href: '/compte/mes-parties.html' }] },
    { match: /^\/projets\/sinjira\/jeux\//, label: 'Jeux SINJIRA™', answer: 'Vous êtes dans la porte Jeux de SINJIRA™. Cette section regroupe les expériences interactives disponibles et leurs accès de partie.', links: [{ label: 'Voir les jeux', href: '/projets/sinjira/jeux/' }, { label: 'Mes parties', href: '/compte/mes-parties.html' }] },
    { match: /^\/projets\/sinjira\/communaute\//, label: 'Communauté SINJIRA™', answer: 'Vous êtes dans la Communauté SINJIRA™. Cet espace concerne les échanges entre membres réels, distincts du Réseau des personnages qui est réservé au rôle-play.', links: [{ label: 'Communauté', href: '/projets/sinjira/communaute/' }, { label: 'Réseau personnage', href: '/compte/reseau-personnage.html' }] },
    { match: /^\/projets\/sinjira\/monde-parallele\//, label: 'Monde parallèle', answer: 'Vous êtes dans le Monde parallèle de SINJIRA™, l’espace persistant lié à la continuité narrative des personnages lorsqu’un accès correspondant est disponible.', links: [{ label: 'Monde parallèle', href: '/projets/sinjira/monde-parallele/' }, { label: 'Mon personnage', href: '/compte/mon-personnage.html' }] },
    { match: /^\/projets\/sinjira\//, label: 'Portail SINJIRA™', answer: 'Vous êtes dans SINJIRA™, l’univers narratif et interactif de Benoit Cantin. Le portail relie les romans, les jeux, le Registre des Consciences et les espaces communautaires.', links: [{ label: 'Romans', href: '/projets/sinjira/romans/' }, { label: 'Jeux', href: '/projets/sinjira/jeux/' }, { label: 'Registre', href: '/projets/sinjira/registre/' }] },
    { match: /^\/projets\/projet-nova\//, label: 'Projet Nova', answer: 'Vous êtes dans Projet Nova, la section publique consacrée à la démarche citoyenne de Benoit Cantin. Vous pouvez y consulter la présentation, les documents publics, la transparence et les pages de participation.', links: [{ label: 'Accueil Nova', href: '/projets/projet-nova/' }, { label: 'Documents Nova', href: '/projets/projet-nova/documents.html' }] },
    { match: /^\/compte\/mon-personnage\.html$/, label: 'Mon personnage', answer: 'Cette page présente l’état de votre personnage. L’assistant peut expliquer le parcours général, mais il ne lit ni ne copie les données privées affichées dans votre compte.', links: [{ label: 'Registre', href: '/projets/sinjira/registre/' }, { label: 'Réseau personnage', href: '/compte/reseau-personnage.html' }] },
    { match: /^\/compte\/reseau-personnage\.html$/, label: 'Réseau des personnages', answer: 'Vous êtes dans le réseau rôle-play. Vous publiez sous l’identité de votre personnage; votre courriel et votre identité réelle ne sont pas affichés dans ce réseau. Les publications rôle-play ne deviennent pas automatiquement canoniques.', links: [{ label: 'Mon personnage', href: '/compte/mon-personnage.html' }, { label: 'Règles', href: '/compte/regles-communaute.html' }] },
    { match: /^\/compte\/(messages|messages-reels|messages-personnage)\.html$/, label: 'Messages SINJIRA™', answer: 'Vous êtes dans la messagerie. Les espaces réels et personnage sont séparés afin de ne pas mélanger votre identité de compte et votre identité fictive.', links: [{ label: 'Communauté', href: '/compte/communaute.html' }, { label: 'Réseau personnage', href: '/compte/reseau-personnage.html' }] },
    { match: /^\/compte\/bibliotheque\.html$/, label: 'Ma bibliothèque', answer: 'Votre bibliothèque rassemble les romans et contenus de lecture disponibles pour votre compte.', links: [{ label: 'Romans', href: '/projets/sinjira/romans/' }, { label: 'Mon espace', href: '/compte/' }] },
    { match: /^\/compte\/licences\.html$/, label: 'Licences', answer: 'Cette page regroupe les licences et droits d’accès associés à votre compte. Une licence valide ne doit jamais exiger que vous transmettiez votre mot de passe.', links: [{ label: 'Mon espace', href: '/compte/' }, { label: 'Mes achats', href: '/compte/mes-achats.html' }] },
    { match: /^\/compte\/relations\.html$/, label: 'Relations', answer: 'Cette page regroupe les relations autorisées de votre compte et les liens familiaux lorsque ces fonctions sont disponibles.', links: [{ label: 'Mon espace', href: '/compte/' }, { label: 'Sécurité', href: '/compte/securite.html' }] },
    { match: /^\/compte\/monde-parallele\.html$/, label: 'Monde parallèle — compte', answer: 'Cette page relie votre personnage au Monde parallèle persistant lorsque votre accès est actif.', links: [{ label: 'Mon personnage', href: '/compte/mon-personnage.html' }, { label: 'Réseau personnage', href: '/compte/reseau-personnage.html' }] },
    { match: /^\/compte\/mes-parties\.html$/, label: 'Mes parties', answer: 'Cette page regroupe les parties liées à votre compte, notamment les expériences de jeu qui enregistrent un état serveur.', links: [{ label: 'Jeux', href: '/projets/sinjira/jeux/' }, { label: 'Fracture', href: '/projets/sinjira/jeux/fracture-du-reseau-mere/' }] },
    { match: /^\/compte\/(mes-achats|marche|jetons)\.html$/, label: 'Achats, marché et jetons', answer: 'Cette zone concerne les éléments économiques du compte. Vérifiez toujours le détail affiché avant une transaction. L’assistant ne peut ni acheter, ni dépenser, ni transférer à votre place.', links: [{ label: 'Mes achats', href: '/compte/mes-achats.html' }, { label: 'Licences', href: '/compte/licences.html' }] },
    { match: /^\/compte\/(securite|parametres|profil)\.html$/, label: 'Réglages du compte', answer: 'Vous êtes dans les réglages du Compte SINJIRA™. Je peux expliquer où aller, mais je ne lis pas vos identifiants, mots de passe ni données privées.', links: [{ label: 'Sécurité', href: '/compte/securite.html' }, { label: 'Paramètres', href: '/compte/parametres.html' }] },
    { match: /^\/compte\//, label: 'Compte SINJIRA™', answer: 'Vous êtes dans l’espace Compte SINJIRA™. Il centralise votre profil, votre bibliothèque, vos personnages, vos parties et vos réglages. L’assistant ne lit pas vos données privées ni vos identifiants.', links: [{ label: 'Mon espace', href: '/compte/' }, { label: 'Sécurité', href: '/compte/securite.html' }] }
  ];

  function currentPageContext() {
    var path = String(window.location.pathname || '/').toLowerCase();
    for (var i = 0; i < PAGE_CONTEXTS.length; i += 1) {
      if (PAGE_CONTEXTS[i].match.test(path)) return PAGE_CONTEXTS[i];
    }
    return { label: 'Site Benoit Cantin', answer: 'Vous êtes sur le site officiel de Benoit Cantin. Je peux vous guider vers SINJIRA™, le Registre des Consciences, Projet Nova ou la page Contact.', links: [{ label: 'Accueil', href: '/' }, { label: 'Contact', href: '/contact.html' }] };
  }

  var INTENTS = [
    { id: 'sinjira', label: 'Découvrir SINJIRA™', keywords: ['sinjira', 'univers', 'science fiction', 'saga', 'plateforme', 'c est quoi', 'quest ce que'], answer: 'SINJIRA™ est l’univers narratif et interactif de Benoit Cantin. Le portail réunit notamment les romans, les jeux, le Registre des Consciences, la Communauté et le Monde parallèle.', links: [{ label: 'Ouvrir SINJIRA™', href: '/projets/sinjira/' }, { label: 'Voir les romans', href: '/projets/sinjira/romans/' }], youthSafe: true },
    { id: 'registre', label: 'Créer mon personnage', keywords: ['registre', 'conscience', 'personnage', 'creer personnage', 'creer mon personnage', 'comment creer mon personnage', 'nouveau personnage', 'creation personnage', 'questionnaire', 'fan', 'apparence', 'personnalite'], answer: 'Le Registre des Consciences vous permet de remplir un questionnaire lié à votre Compte SINJIRA™. Il sert de base humaine à votre personnage original. Les choix sont volontairement simples et la photo source facultative reste une référence de travail privée.', links: [{ label: 'Ouvrir le Registre', href: '/projets/sinjira/registre/' }, { label: 'Voir mon personnage', href: '/compte/mon-personnage.html' }], youthSafe: true },
    { id: 'character-status', label: 'État de mon personnage', keywords: ['mon personnage', 'personnage approuve', 'personnage actif', 'personnage invisible', 'personnage absent', 'abysstime'], answer: 'La page Mon personnage affiche l’état actuellement associé à votre compte. Si la fiche semble absente ou ancienne, rechargez d’abord la page; le parcours propriétaire et les profils approuvés disposent aussi de mécanismes de réparation serveur.', links: [{ label: 'Mon personnage', href: '/compte/mon-personnage.html' }, { label: 'Registre', href: '/projets/sinjira/registre/' }], youthSafe: true },
    { id: 'romans', label: 'Lire les romans', keywords: ['roman', 'romans', 'livre', 'livres', 'lecture', 'lire', 'bibliotheque', 'cendre', 'jugement'], answer: 'La section Romans regroupe la lecture disponible de SINJIRA™. Votre bibliothèque de compte sert à retrouver les contenus auxquels vous avez accès.', links: [{ label: 'Ouvrir les romans', href: '/projets/sinjira/romans/' }, { label: 'Ma bibliothèque', href: '/compte/bibliotheque.html' }], youthSafe: true },
    { id: 'jeux', label: 'Trouver un jeu', keywords: ['jeu', 'jeux', 'jouer', 'partie', 'parties', 'game'], answer: 'La porte Jeux rassemble les expériences interactives de SINJIRA™. Les parties liées au compte sont regroupées dans Mes parties.', links: [{ label: 'Ouvrir les jeux', href: '/projets/sinjira/jeux/' }, { label: 'Mes parties', href: '/compte/mes-parties.html' }], youthSafe: true },
    { id: 'fracture', label: 'Aide pour Fracture', keywords: ['fracture', 'reseau mere', 'resistance', 'identite', 'accusation', 'carte', 'cartes', 'rapport', 'soupcon', 'preuve'], answer: 'Dans Fracture du Réseau-Mère, votre identité est privée pendant la partie et les identités des autres sièges restent cachées. Les cartes révélées indiquent explicitement leur faction. Rapport, soupçon privé et preuve sont des choix de manche; l’accusation finale intervient à la fin selon l’état serveur.', links: [{ label: 'Ouvrir Fracture', href: '/projets/sinjira/jeux/fracture-du-reseau-mere/' }, { label: 'Voir mes parties', href: '/compte/mes-parties.html' }], youthSafe: true },
    { id: 'fracture-identity', label: 'Identité secrète Fracture', keywords: ['ma carte identite', 'mon identite', 'voir identite', 'identite cachee', 'identite des autres', 'resistant ou reseau mere'], answer: 'Pendant une partie Fracture, seule votre propre identité doit être visible dans votre zone privée. Vous ne devez pas voir l’identité des autres joueurs avant la révélation de fin de partie.', links: [{ label: 'Ouvrir Fracture', href: '/projets/sinjira/jeux/fracture-du-reseau-mere/' }], youthSafe: true },
    { id: 'fracture-controls', label: 'Choix et menus Fracture', keywords: ['menu fracture', 'selection fracture', 'choix efface', 'liste efface', 'rapport annonce', 'soupcon prive', 'preuve facultative'], answer: 'Les sélections de Fracture doivent rester stables pendant les synchronisations serveur. Si un choix disparaît, rechargez la partie une fois; si le problème persiste, utilisez Contact en indiquant le code de partie sans partager d’information privée.', links: [{ label: 'Mes parties', href: '/compte/mes-parties.html' }, { label: 'Contact', href: '/contact.html' }], youthSafe: true },
    { id: 'compte', label: 'Aide avec mon compte', keywords: ['compte', 'connexion', 'connecter', 'login', 'profil', 'espace', 'pseudo', 'deconnexion'], answer: 'Le Compte SINJIRA™ centralise votre profil, votre bibliothèque, vos personnages, vos parties et vos réglages. Je peux vous guider vers la bonne page, mais je ne peux pas lire vos données privées ni vos identifiants.', links: [{ label: 'Ouvrir mon espace', href: '/compte/' }, { label: 'Se connecter', href: '/compte/connexion.html' }], youthSafe: true },
    { id: 'password', label: 'Mot de passe ou connexion', keywords: ['mot de passe', 'password', 'oublie', 'oublier', 'recuperer', 'reinitialiser', 'reinitialisation', 'connexion impossible'], answer: 'Je ne peux jamais voir votre mot de passe. Si vous ne pouvez plus vous connecter, utilisez le parcours officiel de récupération du compte. Ne communiquez jamais un mot de passe, un code de récupération ou une clé secrète dans cette fenêtre.', links: [{ label: 'Récupérer mon compte', href: '/compte/mot-de-passe-oublie.html' }, { label: 'Sécurité du compte', href: '/compte/securite.html' }], youthSafe: true },
    { id: 'licenses', label: 'Licences et accès', keywords: ['licence', 'licences', 'code licence', 'acces produit', 'debloquer', 'contenu verrouille'], answer: 'Les licences et droits d’accès associés à votre compte sont visibles dans la page Licences. Si un accès attendu manque, vérifiez d’abord cette page puis votre session de connexion.', links: [{ label: 'Licences', href: '/compte/licences.html' }, { label: 'Mon espace', href: '/compte/' }], youthSafe: true },
    { id: 'purchases', label: 'Achats, marché et jetons', keywords: ['achat', 'achats', 'marche', 'jeton', 'jetons', 'prix', 'payer', 'paiement', 'transaction'], answer: 'Les pages Mes achats, Marché et Jetons sont séparées du reste du compte. L’assistant peut expliquer où aller, mais il ne peut pas effectuer une transaction, dépenser des jetons ou confirmer un achat à votre place.', links: [{ label: 'Mes achats', href: '/compte/mes-achats.html' }, { label: 'Marché', href: '/compte/marche.html' }, { label: 'Jetons', href: '/compte/jetons.html' }], youthSafe: true },
    { id: 'community', label: 'Communauté et rôle-play', keywords: ['communaute', 'reseau personnage', 'social', 'publication', 'role play', 'roleplay', 'canon'], answer: 'SINJIRA™ sépare la Communauté du membre réel et le Réseau des personnages. Une publication de personnage reste du rôle-play et ne devient pas canonique automatiquement.', links: [{ label: 'Communauté', href: '/compte/communaute.html' }, { label: 'Réseau personnage', href: '/compte/reseau-personnage.html' }, { label: 'Règles', href: '/compte/regles-communaute.html' }], youthSafe: true },
    { id: 'messages', label: 'Messages', keywords: ['message', 'messages', 'messagerie', 'ecrire a', 'conversation', 'contact personnage'], answer: 'Les messages réels et les messages personnage sont séparés. Utilisez la messagerie correspondant à l’identité avec laquelle vous souhaitez interagir.', links: [{ label: 'Messages', href: '/compte/messages.html' }, { label: 'Réseau personnage', href: '/compte/reseau-personnage.html' }], youthSafe: true },
    { id: 'moderation', label: 'Blocage et signalement', keywords: ['bloquer', 'blocage', 'signaler', 'signalement', 'harcelement', 'abus', 'moderation'], answer: 'Si une interaction pose problème, utilisez les outils de blocage ou de signalement disponibles dans l’espace concerné. N’incluez pas de mot de passe ou de secret dans un signalement.', links: [{ label: 'Comptes bloqués', href: '/compte/blocages.html' }, { label: 'Règles', href: '/compte/regles-communaute.html' }], youthSafe: true },
    { id: 'parallel', label: 'Monde parallèle', keywords: ['monde parallele', 'univers persistant', 'continuite', 'canon eligible', 'monde persistant'], answer: 'Le Monde parallèle est l’espace persistant lié aux personnages. Il reste distinct du canon officiel des romans; l’éligibilité ou une interaction sociale ne transforme pas automatiquement un événement en fait canonique.', links: [{ label: 'Monde parallèle', href: '/compte/monde-parallele.html' }, { label: 'Mon personnage', href: '/compte/mon-personnage.html' }], youthSafe: true },
    { id: 'youth', label: 'Compte jeunesse et tuteur', keywords: ['jeunesse', 'jeune', 'mineur', 'enfant', 'tuteur', 'parent', 'guardian', 'autorisation'], answer: 'Les parcours jeunesse utilisent des protections et permissions séparées. Lorsqu’un lien de tuteur est requis, utilisez uniquement les écrans officiels du Compte SINJIRA™ et ne partagez pas de mot de passe entre comptes.', links: [{ label: 'Sécurité', href: '/compte/securite.html' }, { label: 'Règles', href: '/compte/regles-communaute.html' }], youthSafe: true },
    { id: 'browser', label: 'Navigateur ou affichage', keywords: ['navigateur', 'chrome', 'firefox', 'safari', 'edge', 'webkit', 'mobile', 'affichage', 'cache', 'ancienne version', 'recharger'], answer: 'Le site est testé sur les moteurs Chromium, Firefox et WebKit ainsi que sur mobile. Si une ancienne interface reste affichée après une mise à jour, effectuez un rechargement complet de la page avant de réessayer.', links: [{ label: 'Accueil', href: '/' }, { label: 'Contact', href: '/contact.html' }], youthSafe: true },
    { id: 'accessibility', label: 'Accessibilité', keywords: ['accessibilite', 'clavier', 'lecteur ecran', 'focus', 'zoom', 'contraste', 'animation'], answer: 'Les parcours critiques sont conçus pour le clavier, le focus visible, la réduction des animations et les technologies d’assistance. Si un contrôle reste inaccessible, indiquez la page et le navigateur via Contact.', links: [{ label: 'Contact', href: '/contact.html' }], youthSafe: true },
    { id: 'nova', label: 'Découvrir Projet Nova', keywords: ['nova', 'projet nova', 'citoyen', 'citoyenne', 'proposition', 'propositions', 'programme'], answer: 'Projet Nova est l’espace consacré à la démarche citoyenne de Benoit Cantin. Il présente la démarche, les propositions et les documents publics dans une section distincte de SINJIRA™.', links: [{ label: 'Ouvrir Projet Nova', href: '/projets/projet-nova/' }, { label: 'Documents', href: '/projets/projet-nova/documents.html' }], youthSafe: true },
    { id: 'nova-transparency', label: 'Transparence Projet Nova', keywords: ['transparence nova', 'comptabilite nova', 'conformite nova', 'registre rencontres', 'audit citoyen', 'documents nova'], answer: 'Projet Nova publie des pages distinctes pour les documents, la transparence, la comptabilité, les rencontres et la conformité. Les documents peuvent être préparatoires; leur statut doit être lu sur la page concernée.', links: [{ label: 'Transparence', href: '/projets/projet-nova/transparence.html' }, { label: 'Documents', href: '/projets/projet-nova/documents.html' }], youthSafe: true },
    { id: 'privacy', label: 'Vie privée et sécurité', keywords: ['confidentialite', 'vie privee', 'prive', 'donnee', 'donnees', 'securite', 'trace', 'conversation', 'stocke'], answer: 'Cet assistant fonctionne localement dans votre navigateur. Votre texte n’est pas envoyé à un fournisseur d’IA externe et la conversation de cette fenêtre n’est pas enregistrée par l’assistant. Pour les règles générales du site, consultez Confidentialité.', links: [{ label: 'Lire Confidentialité', href: '/confidentialite.html' }, { label: 'Sécurité du compte', href: '/compte/securite.html' }], youthSafe: true },
    { id: 'assistant', label: 'Comment fonctionne cette aide', keywords: ['assistant ia', 'aide ia', 'intelligence artificielle', 'comment tu fonctionne', 'mode local', 'ia locale'], answer: 'Cette version de l’assistant est une aide contextuelle locale. Elle classe votre question dans une base d’aide embarquée dans le site; elle n’envoie pas votre texte à un modèle externe et n’invente pas une réponse lorsqu’aucun sujet fiable ne correspond.', links: [{ label: 'Confidentialité', href: '/confidentialite.html' }], youthSafe: true },
    { id: 'contact', label: 'Contacter Benoit Cantin', keywords: ['contact', 'contacter', 'humain', 'aide humaine', 'support', 'courriel', 'email', 'question autre'], answer: 'Pour une question qui demande une intervention humaine ou qui dépasse l’aide du site, utilisez la page Contact officielle.', links: [{ label: 'Ouvrir Contact', href: '/contact.html' }], youthSafe: true }
  ];

  function isPageHelpQuery(query) {
    var q = normalize(query);
    var patterns = ['cette page', 'sur cette page', 'faire ici', 'aide ici', 'aide page', 'ou suis je', 'je suis ou', 'quoi faire ici', 'comment utiliser cette page'];
    for (var i = 0; i < patterns.length; i += 1) if (q.indexOf(patterns[i]) !== -1) return true;
    return q === 'ici' || q === 'aide';
  }

  function isSensitiveQuery(query) {
    var q = normalize(query);
    var sensitive = ['mon mot de passe est', 'voici mon mot de passe', 'code de recuperation', 'service role key', 'api key', 'cle api', 'token secret'];
    for (var i = 0; i < sensitive.length; i += 1) if (q.indexOf(sensitive[i]) !== -1) return true;
    return false;
  }

  function scoreIntent(intent, query, tokens) {
    var normalizedQuery = normalize(query);
    var score = 0;
    for (var i = 0; i < intent.keywords.length; i += 1) {
      var keyword = normalize(intent.keywords[i]);
      if (!keyword) continue;
      if (normalizedQuery === keyword) score += 10;
      else if (normalizedQuery.indexOf(keyword) !== -1) score += keyword.indexOf(' ') !== -1 ? 6 : 3;
      var keywordTokens = tokenize(keyword);
      for (var k = 0; k < keywordTokens.length; k += 1) if (tokens.indexOf(keywordTokens[k]) !== -1) score += 1;
    }
    return score;
  }

  function getReply(query) {
    var context = currentPageContext();
    if (isSensitiveQuery(query)) {
      return { id: 'sensitive', answer: 'N’envoyez pas de mot de passe, code de récupération, clé API ou autre secret dans l’assistant. Si vous avez commencé à saisir un secret, effacez-le et utilisez plutôt la page Sécurité du compte.', links: [{ label: 'Sécurité', href: '/compte/securite.html' }] };
    }
    if (isPageHelpQuery(query)) return { id: 'page-context', answer: context.answer, links: context.links };
    var tokens = tokenize(query);
    var youth = isYouthContext();
    var best = null;
    var bestScore = 0;
    for (var i = 0; i < INTENTS.length; i += 1) {
      var intent = INTENTS[i];
      if (youth && intent.youthSafe !== true) continue;
      var score = scoreIntent(intent, query, tokens);
      if (score > bestScore) { best = intent; bestScore = score; }
    }
    if (!best || bestScore < 3) {
      return { id: 'fallback', answer: 'Je n’ai pas une réponse assez précise pour inventer. ' + context.answer + ' Vous pouvez aussi demander de l’aide sur SINJIRA™, le Registre, les romans, Fracture, votre compte, la communauté, Projet Nova, la confidentialité ou le contact humain.', links: context.links };
    }
    return best;
  }

  function el(tag, className, text) {
    var node = doc.createElement(tag);
    if (className) node.className = className;
    if (typeof text === 'string') node.textContent = text;
    return node;
  }

  var pageContext = currentPageContext();
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

  var intro = el('p', 'sinjira-assistant-intro', 'Vous êtes dans « ' + pageContext.label + ' ». Posez une question sur le site; je vous guide sans envoyer votre message à un service d’IA externe.');
  var suggestions = el('div', 'sinjira-assistant-suggestions');
  suggestions.setAttribute('aria-label', 'Questions suggérées');
  var pageSuggestion = el('button', 'sinjira-assistant-chip', 'Aide sur cette page');
  pageSuggestion.type = 'button';
  pageSuggestion.setAttribute('data-assistant-question', 'Que puis-je faire sur cette page ?');
  suggestions.appendChild(pageSuggestion);
  var suggestedIntentIds = ['registre', 'fracture', 'compte'];
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
  input.placeholder = 'Ex. Que puis-je faire sur cette page ?';
  input.setAttribute('autocomplete', 'off');
  input.setAttribute('spellcheck', 'true');
  var submit = el('button', 'sinjira-assistant-send', 'Envoyer');
  submit.type = 'submit';
  form.appendChild(label); form.appendChild(input); form.appendChild(submit);
  var privacy = el('p', 'sinjira-assistant-privacy', 'Mode V24.4.45 : conversation éphémère dans cet onglet, sans fournisseur d’IA externe. L’assistant utilise seulement une base d’aide locale et le chemin de la page. Ne saisissez jamais un mot de passe, un code de récupération ou une information très sensible.');
  privacy.id = 'sinjira-assistant-privacy';
  panel.appendChild(header); panel.appendChild(intro); panel.appendChild(suggestions); panel.appendChild(log); panel.appendChild(form); panel.appendChild(privacy);
  root.appendChild(toggle); root.appendChild(panel); doc.body.appendChild(root);

  function appendMessage(role, text, links) {
    var item = el('article', 'sinjira-assistant-message sinjira-assistant-message-' + role);
    item.appendChild(el('strong', 'sinjira-assistant-message-role', role === 'user' ? 'Vous' : 'Assistant SINJIRA'));
    item.appendChild(el('p', '', text));
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
    if (!log.children.length) appendMessage('assistant', 'Bonjour. Je peux vous aider avec « ' + pageContext.label + ' » ou vous guider vers une autre section du site. Que cherchez-vous ?');
    window.setTimeout(function () { input.focus(); }, 0);
  }

  function closePanel() {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    root.className = 'sinjira-assistant';
    toggle.focus();
  }

  toggle.addEventListener('click', function () { if (panel.hidden) openPanel(); else closePanel(); });
  close.addEventListener('click', closePanel);
  suggestions.addEventListener('click', function (event) {
    var target = event.target;
    if (!target || target.tagName !== 'BUTTON') return;
    ask(target.getAttribute('data-assistant-question') || target.textContent || '');
  });
  form.addEventListener('submit', function (event) { event.preventDefault(); var question = input.value; input.value = ''; ask(question); });
  input.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); if (form.requestSubmit) form.requestSubmit(); else submit.click(); }
  });
  doc.addEventListener('keydown', function (event) { if (event.key === 'Escape' && !panel.hidden) closePanel(); });

  var publicApi = {
    version: ASSISTANT_VERSION,
    providerMode: PROVIDER_MODE,
    externalProviderEnabled: EXTERNAL_PROVIDER_ENABLED,
    privacy: 'ephemeral-memory-only',
    contextLabel: pageContext.label,
    intentCount: INTENTS.length,
    open: openPanel
  };
  window.__SINJIRA_ASSISTANT__ = Object.freeze ? Object.freeze(publicApi) : publicApi;
}());