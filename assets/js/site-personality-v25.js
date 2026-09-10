(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var VERSION = '25.0.0';

  if (root.getAttribute('data-disable-site-personality') === 'true') return;
  if (root.getAttribute('data-site-personality-version') === VERSION) return;
  root.setAttribute('data-site-personality-version', VERSION);

  var environments = {
    portal: {
      title: 'Avoir la capacité d’agir, sans perdre l’humain.',
      summary: 'Ce portail privilégie l’autonomie, les conséquences à long terme et des choix qui laissent encore une possibilité de comprendre, corriger et avancer.',
      principles: [
        ['Autonomie', 'Donner des moyens d’agir plutôt que créer une dépendance.'],
        ['Long terme', 'Regarder ce qu’une décision construit demain, pas seulement ce qu’elle facilite aujourd’hui.'],
        ['Options ouvertes', 'Préférer les étapes vérifiables et corrigeables quand l’irréversible n’est pas nécessaire.']
      ]
    },
    sinjira: {
      title: 'L’humain avant tout. Protéger sans surveiller.',
      summary: 'SINJIRA doit préserver la liberté, la vie privée et la capacité de chacun à comprendre ce qui lui arrive, sans transformer la protection en contrôle permanent.',
      principles: [
        ['Choix humain', 'Aucune automatisation ne doit effacer la décision de la personne.'],
        ['Vie privée', 'Séparer les identités et minimiser ce qui doit être connu ou conservé.'],
        ['Conséquences', 'Rendre les décisions importantes compréhensibles et éviter l’irréversible par défaut.']
      ]
    },
    nova: {
      title: 'Un pouvoir utile doit rester compréhensible, traçable et corrigeable.',
      summary: 'Projet Nova traduit cette personnalité par la responsabilité, la transparence, l’évaluation des conséquences à long terme et des mécanismes qui empêchent un pouvoir de devenir un chèque en blanc.',
      principles: [
        ['Transparence', 'Pouvoir expliquer qui décide, pourquoi, avec quels moyens et quels résultats.'],
        ['Responsabilité', 'Encadrer le pouvoir par des règles vérifiables et des contrepoids réels.'],
        ['Réversibilité', 'Tester, mesurer et corriger avant de rendre une décision inutilement irréversible.']
      ]
    },
    futurax: {
      title: 'Construire une capacité durable, pas une dépendance de plus.',
      summary: 'Futurax regarde au-delà du prototype immédiat : une technologie utile doit rester compréhensible, adaptable, réparable et réellement augmenter la capacité d’agir.',
      principles: [
        ['Capacité', 'Créer des outils qui rendent leurs utilisateurs plus autonomes.'],
        ['Durabilité', 'Évaluer les coûts, dépendances et conséquences après l’effet de nouveauté.'],
        ['Réparabilité', 'Conserver des chemins de correction, d’évolution et de remplacement.']
      ]
    },
    lumina: {
      title: 'La technologie reste au service de la personne.',
      summary: 'Lumina relie imagination et technologie sans placer le système au-dessus de l’humain : la présence doit rester explicable, respectueuse et soumise au choix de la personne.',
      principles: [
        ['Humain d’abord', 'L’utilité technique ne justifie pas de retirer le choix humain.'],
        ['Clarté', 'Dire ce que le système fait, ce qu’il ne fait pas et où sont ses limites.'],
        ['Respect', 'Ne pas obtenir par friction, surveillance ou confusion ce qui doit relever d’un choix libre.']
      ]
    },
    chroniques: {
      title: 'Des choix qui comptent, sans fermer inutilement toutes les portes.',
      summary: 'Les Chroniques expriment cette personnalité par les conséquences, la responsabilité et la résilience : tomber, apprendre, reconstruire et préserver une possibilité d’agir quand elle peut encore exister.',
      principles: [
        ['Conséquences', 'Les décisions ont un poids réel et façonnent le monde.'],
        ['Liberté', 'Les personnages gardent une capacité de choisir plutôt que suivre une voie imposée.'],
        ['Résilience', 'Une rupture peut devenir un nouveau départ lorsqu’une voie de reconstruction demeure.']
      ]
    }
  };

  function normalizePath() {
    var path = String(window.location.pathname || '/').toLowerCase();
    path = path.replace(/\/{2,}/g, '/').replace(/\/index\.html$/, '/');
    return path.length > 1 ? path.replace(/\/$/, '') : path;
  }

  function environmentFor(path) {
    if (path.indexOf('/projets/projet-nova') === 0) return 'nova';
    if (path.indexOf('/projets/futurax') === 0) return 'futurax';
    if (path.indexOf('/projets/lumina') === 0) return 'lumina';
    if (path.indexOf('/projets/chroniques-des-mondes-fractures') === 0) return 'chroniques';
    if (path.indexOf('/projets/sinjira') === 0 || path === '/compte' || path.indexOf('/compte/') === 0 || path.indexOf('/admin/sinjira') === 0) return 'sinjira';
    return 'portal';
  }

  function addStylesheet() {
    if (doc.querySelector('link[data-site-personality-style]')) return;
    var link = doc.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/assets/css/site-personality-v25.css?v=' + VERSION;
    link.setAttribute('data-site-personality-style', '');
    doc.head.appendChild(link);
  }

  function element(tag, className, text) {
    var node = doc.createElement(tag);
    if (className) node.className = className;
    if (typeof text === 'string') node.textContent = text;
    return node;
  }

  function render() {
    if (doc.querySelector('[data-site-personality]')) return;
    var main = doc.querySelector('main');
    var footer = doc.querySelector('footer');
    if (!main || !footer || !footer.parentNode) return;

    var path = normalizePath();
    var environment = environmentFor(path);
    var config = environments[environment];
    var section = element('section', 'bc-personality-signature');
    var shell = element('div', 'bc-personality-shell');
    var copy = element('div', 'bc-personality-copy');
    var eyebrow = element('span', 'bc-personality-eyebrow', 'Signature de conception');
    var heading = element('h2', 'bc-personality-title', config.title);
    var summary = element('p', 'bc-personality-summary', config.summary);
    var list = element('ul', 'bc-personality-principles');
    var headingId = 'bc-personality-' + environment + '-title';

    section.setAttribute('data-site-personality', environment);
    section.setAttribute('aria-labelledby', headingId);
    heading.id = headingId;

    copy.appendChild(eyebrow);
    copy.appendChild(heading);
    copy.appendChild(summary);
    shell.appendChild(copy);

    for (var i = 0; i < config.principles.length; i += 1) {
      var item = element('li', 'bc-personality-principle');
      item.appendChild(element('strong', '', config.principles[i][0]));
      item.appendChild(element('span', '', config.principles[i][1]));
      list.appendChild(item);
    }

    shell.appendChild(list);
    section.appendChild(shell);
    footer.parentNode.insertBefore(section, footer);
  }

  addStylesheet();
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', render, { once: true });
  else render();
}());
