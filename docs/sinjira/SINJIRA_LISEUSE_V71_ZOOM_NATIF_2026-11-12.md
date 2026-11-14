# SINJIRA™ — V71 : préserver le zoom tactile natif sur la liseuse mobile

**Périmètre :** PR d'intégration mobile #1000, sans modification de schéma, comptes, Auth, droits d'accès, texte privé ou progression cloud.

## Défaut ciblé

Le `VisualViewport.scale` d'un navigateur peut augmenter après un pincement, **même si** le `scrollWidth` du lecteur semble inchangé. Dans cette situation, un déplacement latéral d'un seul doigt sert à parcourir la page agrandie. Les contrôleurs V52 (pages PDF) et V53 (écrans de texte reflow) risquaient de l'interpréter comme une demande de changer de page.

## Comportement V71

- Si `window.visualViewport.scale > 1.01`, laisser le geste au navigateur sans cliquer sur Suivante/Précédente, ni appeler `preventDefault` dans le mode paginé.
- Vérifier l'échelle **au début, pendant et à la fin** du contact : une activation de zoom après le premier doigt annule aussi le tournage accidentel.
- À l'échelle normale ou si l'API `visualViewport` est indisponible, conserver les gestes gauche/droite et les boutons tactiles accessibles.
- Préserver le rejet V70 des glissements sur contenu plus large que l'écran et la protection V67 des gestes système aux bords de l'appareil.

## Contrats de test

Cinq régressions Node ciblent les deux moteurs, avec une comparaison des états zoom/normale et l'activation du zoom pendant un contact. À vérifier via `node --test tests/sinjira-liseuse-touch-v52.test.mjs tests/sinjira-liseuse-reflow-v53.test.mjs`, puis Chromium/WebKit et le site complet en CI sur le **SHA exact**.

## Réception manuelle exigée avant publication

Sur iPhone Safari et Android Chrome **réels**, ouvrir la démo, essayer l'affichage PDF puis le mode pages d'écran : pincer à 150–200 %, glisser horizontalement, vérifier l'absence de changement de page, revenir à 100 %, glisser gauche puis droite, vérifier la pagination et la position de lecture. Répéter avec VoiceOver/TalkBack si possible. Un moteur automatisé ne vaut pas preuve d'appareil physique.

**Statut :** PR #1000 DRAFT, NO-GO avant approbation, contrôle des droits au roman intégral, essais physiques et synchronisation interappareils autorisée. Score de maturité SINJIRA **66,5 % ±10 points**, inchangé.
