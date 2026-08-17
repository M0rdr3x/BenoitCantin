from pathlib import Path
root=Path(__file__).resolve().parents[1]
js_path=root/'assets/js/sinjira-assistant.js'
js=js_path.read_text(encoding='utf-8')
js=js.replace("var ASSISTANT_VERSION = '24.4.46';","var ASSISTANT_VERSION = '24.4.48';")
js=js.replace("return text.replace(/[-‐‑‒–—―'’]/g, ' ').replace(/[^a-z0-9\\s]/g, ' ').replace(/\\s+/g, ' ').replace(/^\\s+|\\s+$/g, '');", """text = text.replace(/[-‐‑‒–—―'’]/g, ' ').replace(/[^a-z0-9\\s]/g, ' ').replace(/\\s+/g, ' ').replace(/^\\s+|\\s+$/g, '');
    text = text
      .replace(/\\bpersonage\\b/g, 'personnage')
      .replace(/\\benregister\\b/g, 'enregistrer')
      .replace(/\\bsyncronisation\\b/g, 'synchronisation')
      .replace(/\\bsyncroniser\\b/g, 'synchronisation')
      .replace(/\\bsynchroniser\\b/g, 'synchronisation')
      .replace(/\\bmarche pas\\b/g, 'ne fonctionne pas')
      .replace(/\\bfonctionne plus\\b/g, 'ne fonctionne pas')
      .replace(/\\bresistant\\b/g, 'resistance');
    return text;""")

needle="""  function currentPageContext() {
    var path = String(window.location.pathname || '/').toLowerCase();
    for (var i = 0; i < PAGE_CONTEXTS.length; i += 1) {
      if (PAGE_CONTEXTS[i].match.test(path)) return PAGE_CONTEXTS[i];
    }
    return { label: 'Site Benoit Cantin', answer: 'Vous êtes sur le site officiel de Benoit Cantin. Je peux vous guider vers SINJIRA™, le Registre des Consciences, Projet Nova ou la page Contact.', links: [{ label: 'Accueil', href: '/' }, { label: 'Contact', href: '/contact.html' }] };
  }

"""
insert=needle+"""  var CONTEXT_SUGGESTIONS = {
    'Accueil Benoit Cantin': [
      { label: 'Découvrir SINJIRA™', question: 'C’est quoi SINJIRA™ ?' },
      { label: 'Créer mon personnage', question: 'Comment créer mon personnage ?' },
      { label: 'Découvrir Projet Nova', question: 'C’est quoi Projet Nova ?' }
    ],
    'Registre des Consciences': [
      { label: 'Créer mon personnage', question: 'Comment créer mon personnage ?' },
      { label: 'Enregistré mais non envoyé', question: 'Mon questionnaire est enregistré mais la notification n’a pas été envoyée.' },
      { label: 'Voir mon personnage', question: 'Où voir l’état de mon personnage ?' }
    ],
    'Fracture du Réseau-Mère': [
      { label: 'Voir mon identité', question: 'Comment voir mon identité privée dans Fracture ?' },
      { label: 'Choix qui s’efface', question: 'Mon choix dans un menu Fracture s’efface.' },
      { label: 'Jouer en ligne', question: 'Comment démarrer ou rejoindre une partie Fracture en ligne ?' }
    ],
    'Compte SINJIRA™': [
      { label: 'Synchronisation', question: 'Mon compte reste bloqué en synchronisation.' },
      { label: 'Photo de profil', question: 'Comment changer ma photo de profil ?' },
      { label: 'Accès et licences', question: 'Pourquoi un contenu reste verrouillé ?' }
    ],
    'Mon personnage': [
      { label: 'Vérification interminable', question: 'Mon personnage reste sur Vérification de votre personnage.' },
      { label: 'Questionnaire', question: 'Comment refaire ou compléter mon questionnaire ?' },
      { label: 'Monde parallèle', question: 'Comment mon personnage rejoint le Monde parallèle ?' }
    ],
    'Romans SINJIRA™': [
      { label: 'Lire la démo', question: 'Comment lire ou télécharger la démo du Livre I ?' },
      { label: 'Ma bibliothèque', question: 'Où retrouver mes romans ?' },
      { label: 'Commentaires', question: 'Comment commenter un roman ?' }
    ],
    'Projet Nova': [
      { label: 'Comprendre Nova', question: 'C’est quoi Projet Nova ?' },
      { label: 'Documents', question: 'Où sont les documents de Projet Nova ?' },
      { label: 'Transparence', question: 'Où voir la transparence et la conformité de Projet Nova ?' }
    ]
  };

  function currentSuggestions(context) {
    var items = CONTEXT_SUGGESTIONS[context.label];
    if (items && items.length) return items;
    return [
      { label: 'Aide sur cette page', question: 'Que puis-je faire sur cette page ?' },
      { label: 'Mon compte', question: 'J’ai besoin d’aide avec mon compte.' },
      { label: 'Contacter un humain', question: 'Je veux contacter le support humain.' }
    ];
  }

"""
if needle not in js: raise SystemExit('currentPageContext needle absent')
js=js.replace(needle,insert)

marker="""    { id: 'privacy', label: 'Vie privée et sécurité', keywords: ['confidentialite', 'vie privee', 'prive', 'donnee', 'donnees', 'securite', 'trace', 'conversation', 'stocke'], answer: 'Cet assistant fonctionne localement dans votre navigateur. Votre texte n’est pas envoyé à un fournisseur d’IA externe et la conversation de cette fenêtre n’est pas enregistrée par l’assistant. Pour les règles générales du site, consultez Confidentialité.', links: [{ label: 'Lire Confidentialité', href: '/confidentialite.html' }, { label: 'Sécurité du compte', href: '/compte/securite.html' }], youthSafe: true },
"""
new_intents="""    { id: 'registre-delivery', label: 'Questionnaire enregistré mais notification échouée', keywords: ['questionnaire enregistre mais notification', 'enregistre mais pas envoye', 'enregistre mais non envoye', 'n a pas pu etre envoye', 'pas pu etre envoye', 'notification questionnaire', 'courriel questionnaire', 'formulaire enregistre'], answer: 'Si le Registre confirme que le questionnaire a été enregistré, la sauvegarde SINJIRA™ est l’étape importante. Une notification ou un courriel peut échouer séparément sans annuler le dossier. Vérifiez ensuite Mon personnage; si le dossier n’apparaît toujours pas après reconnexion, utilisez Contact sans renvoyer de données sensibles.', links: [{ label: 'Mon personnage', href: '/compte/mon-personnage.html' }, { label: 'Contact', href: '/contact.html' }], youthSafe: true },
    { id: 'sync-status', label: 'Synchronisation ou chargement bloqué', keywords: ['supabase', 'synchronisation', 'compte bloque', 'reste bloque', 'chargement infini', 'verification de votre personnage', 'verification personnage', 'ne fonctionne pas serveur', 'erreur serveur', 'service indisponible'], answer: 'Pour un écran bloqué en synchronisation, commencez par vérifier que votre session est toujours connectée, puis rechargez une seule fois la page. Si le même état revient, n’envoyez pas plusieurs fois le même formulaire: notez la page et le message affiché, puis utilisez Contact. Les opérations importantes doivent être confirmées par le serveur avant d’être considérées comme terminées.', links: [{ label: 'Mon espace', href: '/compte/' }, { label: 'Sécurité', href: '/compte/securite.html' }, { label: 'Contact', href: '/contact.html' }], youthSafe: true },
    { id: 'admin-access', label: 'Accès administrateur', keywords: ['administrateur', 'administration', 'menu admin', 'menu administrateur', 'acces admin', 'panneau admin'], answer: 'Les fonctions d’administration ne doivent apparaître que pour un compte autorisé par le serveur. Si vous êtes censé avoir ce rôle mais que le menu n’apparaît pas, reconnectez-vous puis vérifiez votre espace de compte. L’assistant public ne fournit jamais de raccourci permettant de contourner les contrôles d’autorisation.', links: [{ label: 'Mon espace', href: '/compte/' }, { label: 'Sécurité', href: '/compte/securite.html' }], youthSafe: true },
    { id: 'avatar', label: 'Photo de profil', keywords: ['photo de profil', 'avatar', 'image profil', 'changer photo', 'televerser photo', '512 512', 'webp profil'], answer: 'La photo de profil est préparée pour un affichage carré. Le site peut recadrer et optimiser une image compatible vers 512 × 512 px avant l’enregistrement. Si l’envoi échoue, vérifiez votre connexion puis réessayez avec une image standard JPEG, PNG ou WebP.', links: [{ label: 'Profil', href: '/compte/profil.html' }, { label: 'Sécurité', href: '/compte/securite.html' }], youthSafe: true },
    { id: 'roman-demo', label: 'Démo du Livre I', keywords: ['demo livre', 'demo roman', 'lire demo', 'telecharger demo', 'cendre du jugement demo', 'extrait roman'], answer: 'La démo de La Cendre du Jugement peut être lue depuis la section Romans et conservée lorsque le bouton de téléchargement est proposé. La version intégrale, lorsqu’elle est protégée, doit passer par les droits de la bibliothèque plutôt que par un lien public direct.', links: [{ label: 'Romans SINJIRA™', href: '/projets/sinjira/romans/' }, { label: 'Ma bibliothèque', href: '/compte/bibliotheque.html' }], youthSafe: true },
    { id: 'roman-comments', label: 'Commentaires sur les romans', keywords: ['commentaire roman', 'commenter roman', 'laisser commentaire', 'avis roman', 'mes commentaires'], answer: 'Les commentaires de lecture sont liés au Compte SINJIRA™. Selon la page, un commentaire peut être soumis puis attendre une modération avant publication. Vos commentaires et votre progression restent distincts du personnage fictif.', links: [{ label: 'Romans', href: '/projets/sinjira/romans/' }, { label: 'Mon espace', href: '/compte/' }], youthSafe: true },
    { id: 'fracture-access', label: 'Démarrer Fracture Online', keywords: ['jouer fracture en ligne', 'fracture online', 'demarrer partie fracture', 'creer partie fracture', 'rejoindre partie fracture', 'code partie fracture', 'solo fracture', 'duo fracture'], answer: 'Fracture Online utilise une partie serveur liée au Compte SINJIRA™. Vous pouvez créer une partie ou rejoindre un code lorsque votre accès au jeu est actif. En Solo, les sièges invisibles sont gérés par le moteur; en Duo, un siège invisible complète la table; à 3 joueurs ou plus, chaque personne utilise son propre compte.', links: [{ label: 'Fracture du Réseau-Mère', href: '/projets/sinjira/jeux/fracture-du-reseau-mere/' }, { label: 'Mes parties', href: '/compte/mes-parties.html' }, { label: 'Licences', href: '/compte/licences.html' }], youthSafe: true },
"""
if marker not in js: raise SystemExit('privacy marker absent')
js=js.replace(marker,new_intents+marker)

old_suggestions="""  var suggestions = el('div', 'sinjira-assistant-suggestions');
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
"""
new_suggestions="""  var suggestions = el('div', 'sinjira-assistant-suggestions');
  suggestions.setAttribute('aria-label', 'Questions suggérées');
  var pageSuggestions = currentSuggestions(pageContext);
  for (var s = 0; s < pageSuggestions.length; s += 1) {
    var suggestion = el('button', 'sinjira-assistant-chip', pageSuggestions[s].label);
    suggestion.type = 'button';
    suggestion.setAttribute('data-assistant-question', pageSuggestions[s].question);
    suggestions.appendChild(suggestion);
  }
"""
if old_suggestions not in js: raise SystemExit('suggestions block absent')
js=js.replace(old_suggestions,new_suggestions)
js=js.replace('Mode V24.4.46 : conversation éphémère','Mode V24.4.48 : conversation éphémère')
js_path.write_text(js,encoding='utf-8')

for rel in ['assets/js/site.js','projets/projet-nova/script.js','tests/e2e/test_public_site.py','scripts/validate_sinjira_assistant.py','docs/SINJIRA_ASSISTANT.md']:
    p=root/rel
    txt=p.read_text(encoding='utf-8').replace('24.4.46','24.4.48')
    p.write_text(txt,encoding='utf-8')

p=root/'scripts/validate_sinjira_assistant.py'
txt=p.read_text(encoding='utf-8')
txt=txt.replace("require(len(intent_blocks) >= 20, \"la base d’aide doit couvrir au moins 20 intentions fiables\")", "require(len(intent_blocks) >= 27, \"la base d’aide doit couvrir au moins 27 intentions fiables\")")
txt=txt.replace("\"'nova-transparency'\", \"'assistant'\",", "\"'nova-transparency'\", \"'registre-delivery'\", \"'sync-status'\", \"'admin-access'\",\n    \"'avatar'\", \"'roman-demo'\", \"'roman-comments'\", \"'fracture-access'\", \"'assistant'\",")
txt=txt.replace("require(\"function isPageHelpQuery(query)\" in js, \"intention d’aide sur la page absente\")", "require(\"function isPageHelpQuery(query)\" in js, \"intention d’aide sur la page absente\")\nrequire(\"var CONTEXT_SUGGESTIONS = {\" in js and \"function currentSuggestions(context)\" in js, \"suggestions contextuelles V24.4.48 absentes\")\nfor marker in (\"Enregistré mais non envoyé\", \"Voir mon identité\", \"Synchronisation\", \"Lire la démo\"):\n    require(marker in js, f\"suggestion contextuelle absente: {marker}\")")
p.write_text(txt,encoding='utf-8')

p=root/'tests/e2e/test_public_site.py'
txt=p.read_text(encoding='utf-8')
needle="""            assert_true("seule votre propre identité" in log_text, f"{BROWSER_NAME}: garde-fou identité Fracture absent")

            page.wait_for_timeout(400)
            question.fill("voici mon mot de passe est test-seulement")
"""
rep="""            assert_true("seule votre propre identité" in log_text, f"{BROWSER_NAME}: garde-fou identité Fracture absent")

            page.wait_for_timeout(400)
            question.fill("Mon questionnaire est enregistré mais la notification n’a pas été envoyée")
            question.press("Enter")
            log_text = page.locator(".sinjira-assistant-log").inner_text().lower()
            assert_true("sans annuler le dossier" in log_text, f"{BROWSER_NAME}: dépannage notification Registre absent")

            page.wait_for_timeout(400)
            question.fill("Mon compte reste bloqué en synchronisation")
            question.press("Enter")
            log_text = page.locator(".sinjira-assistant-log").inner_text().lower()
            assert_true("session est toujours connectée" in log_text, f"{BROWSER_NAME}: dépannage synchronisation absent")

            page.wait_for_timeout(400)
            question.fill("voici mon mot de passe est test-seulement")
"""
if needle not in txt: raise SystemExit('E2E insertion needle absent')
txt=txt.replace(needle,rep)
p.write_text(txt,encoding='utf-8')

p=root/'docs/SINJIRA_ASSISTANT.md'
txt=p.read_text(encoding='utf-8')
anchor='- aide contextuelle pour SINJIRA™, le Registre des Consciences, les romans, Fracture, le Compte SINJIRA™, la Communauté, le Monde parallèle et Projet Nova.\n'
extra=anchor+'- suggestions adaptées à la page visitée plutôt qu’une liste générique identique partout;\n- dépannage local des cas fréquents: questionnaire enregistré mais notification échouée, synchronisation bloquée, accès administrateur, avatar, démo/lecture, commentaires et démarrage Fracture Online;\n- normalisation de quelques fautes de frappe fréquentes sans envoyer le texte hors du navigateur.\n'
txt=txt.replace(anchor,extra)
p.write_text(txt,encoding='utf-8')
print('upgrade complete')
