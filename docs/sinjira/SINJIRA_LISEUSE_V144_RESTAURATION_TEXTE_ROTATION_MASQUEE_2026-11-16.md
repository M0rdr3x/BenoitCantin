# SINJIRA V144 — conserver l'écran du livre après une rotation masquée

**16 novembre 2026 — PR #1000 DRAFT, sans fusion ni publication.**

## Pourquoi intervenir

V143 empêche les rendus PDF retardés pendant une rotation en arrière-plan. Le moteur de **texte paginé V53** possédait toutefois un chemin indépendant : `window.resize`, `orientationchange` ou `visualViewport.resize` appelaient `scheduleLayoutRestore(lastRatio,lastAnchor)`, puis deux `requestAnimationFrame`. Si le livre était masqué entre l'événement et ce rappel, l'ancien code tentait de restaurer son ancre/ratio à partir d'un viewport de hauteur zéro et risquait de replacer la lecture au mauvais écran.

## Correctif

- Si le livre est masqué pendant un `resize`, ne pas exécuter de reflow. Mémoriser **en mémoire seulement** le dernier ratio et la dernière ancre connus avant la suspension.
- Si le document devient masqué entre la programmation d'un reflow et son rappel `requestAnimationFrame`, refuser le calcul sur le viewport nul et reporter cette seule restitution jusqu'à la réouverture.
- À la réouverture, après le délai de stabilisation de l'interface, restituer l'ancre sur le vrai viewport visible; sinon simplement resynchroniser les contrôles.
- L'action volontaire suivante du lecteur (balayage, écran choisi, déplacement tactile) annule aussi la restitution différée : un ancien retour ne doit pas écraser un geste récent.
- Les commandes de disposition plein écran ne capturent plus d'ancre depuis un contenu masqué.
- Aucun texte privé enregistré, aucun changement Auth/RLS, aucune donnée de progrès écrite par ce mécanisme. Cache module V53 aligné sur **53.11.16.144** dans HTML, contrat Node, fixture et test Playwright V58.

## Vérification

Sur `tests/e2e/test_sinjira_liseuse_real_page_v57.py`, commencer une lecture au milieu d'un écran texte, programmer `resize`, masquer le contenu pendant la fenêtre rAF, déclencher une seconde rotation masquée, puis rouvrir la liseuse. Vérifier que la page source reste 3, que le mode demeure paginé et que le défilement reprend près de la position initiale. Réinitialiser le scroll avant les parcours de gestes, puis exécuter Chromium/WebKit et les suites tactiles V64 à V69.

**La CI du commit final doit être vérifiée sur son SHA exact.** Les appareils iPhone/Android/tablettes physiques, VoiceOver/TalkBack, les droits et révocations réels et la synchronisation multiappareils ne sont pas homologués. **NO-GO production** ; les scores Nova/SINJIRA n'évoluent pas sans nouvel audit.
