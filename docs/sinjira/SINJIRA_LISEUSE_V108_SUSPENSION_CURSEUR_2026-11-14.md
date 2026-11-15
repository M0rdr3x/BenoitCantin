# SINJIRA — V108 : pas de changement de page après interruption du curseur

**14 novembre 2026 (heure du Québec) — candidat de revue #1000, NO-GO production.**

## Correctif

Lorsqu’une personne manipule « Aller à l’écran » en mode texte paginé, le navigateur peut interrompre la manipulation avant son relâchement : changement d’onglet, retour à l’accueil du téléphone, bascule d’application, perte de focus, fermeture de la page. Après V106/V107, la prévisualisation du curseur devait aussi être annulée lors de ces interruptions.

Le module V53 réutilise désormais le gestionnaire d’annulation déjà appelé sur `touchcancel`, `visibilitychange` (onglet caché), `window.blur` et `pagehide` pour marquer la prévisualisation comme obsolète. Si le navigateur envoie un `change` différé au retour, **aucun déplacement de lecture** ni notification `sinjira:reader-screen-turn` n’est déclenché. Une nouvelle manipulation fonctionne normalement.

## Preuves techniques

- Un test Node dans `tests/sinjira-liseuse-reflow-v53.test.mjs` couvre les trois interruptions : perte de focus, arrière-plan de l’onglet et fermeture/navigation, puis une nouvelle sélection normale.
- Le parcours Playwright de la page réelle `tests/e2e/test_sinjira_liseuse_real_page_v57.py` contrôle aussi le `change` tardif après `window.blur`, puis le retour à une navigation normale sur Chromium/WebKit, avec livre synthétique et réseau privé bloqué.
- URL cache V53 alignée sur `53.11.14.108` dans `compte/liseuse.html`, la fixture et les tests responsive.
- Aucune modification des romans, droits d’accès privés, authentification, RLS, migrations ou stockage local du texte.

**Critère GO :** workflows du SHA V108 réussis, puis réception tactile sur iPhone Safari et Android Chrome physiques, VoiceOver/TalkBack, tests des romans autorisés, droits serveur et synchronisation entre appareils, approbation humaine explicite. Les tests automatisés seuls n’autorisent pas la fusion ou le déploiement.

Les taux de maturité globaux du programme restent ceux du bilan du 8 novembre : Nova 47 %, boussole 75 %, sondage 54,5 %, SINJIRA 66,5 % ±10 points ; aucun taux global fiable pour Nova–Sinjira.
