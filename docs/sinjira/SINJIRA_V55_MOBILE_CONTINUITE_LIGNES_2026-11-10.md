# SINJIRA V55 — continuité des lignes du roman sur téléphone

**10 novembre 2026 — candidat à revue, non publié.**

## Défaut identifié

Sur la liseuse paginée [V53 #964](https://github.com/M0rdr3x/BenoitCantin/pull/964), le déplacement entre écrans utilisait surtout la **hauteur extérieure du lecteur**, sans retirer les marges intérieures (`padding-top`, `padding-bottom`) du texte. Cela pouvait rendre le saut de lecture trop grand sur un téléphone, en particulier à taille de police augmentée : une ligne partiellement masquée au pied d'un écran risquait de ne pas réapparaître à l'écran suivant. Ce risque était identifié par revue du calcul; aucun incident chez un utilisateur n'est affirmé.

## Correctif proposé

- La mesure du nombre de lignes visibles tient désormais compte de la **hauteur utilisable après retrait des marges** réellement calculées en CSS.
- Chaque changement d'écran conserve **une ligne de recouvrement**, pour qu'une ligne proche du bord inférieur reste visible au début de l'écran suivant.
- Les fonctions `measureReaderScreen`, `readerScreenState` et `planReaderScreenTurn` acceptent `paddingTop/paddingBottom` optionnels; les appels existants sans marges conservent leur comportement, afin de limiter les régressions.
- La liseuse continue d'utiliser les positions `scrollTop` et `scroll_ratio` déjà prévues, sans nouveau stockage ni accès Supabase. La navigation droite/gauche, le choix entre défilement libre et pages d'écran, le mode PDF et le clavier sont préservés.

## Réception

- **30 tests V53/V55** et **20 tests V52** (soit 50 tests Node) couvrent les positions, les marges et les cas limites.
- Le parcours Playwright V54 vérifie en plus, sur **Chromium et WebKit**, que le déplacement effectif n'excède pas la hauteur intérieure disponible moins une hauteur de ligne : mesure de la géométrie réelle `getComputedStyle` + `scrollTop`.
- Le workflow `.github/workflows/sinjira-liseuse-anti-saut-v55.yml` est en lecture seule, avec les deux moteurs et les contrôles de syntaxe; aucun service de livres privés et aucune migration.

## Limitations et autres étapes

Ce correctif réduit le risque de **lignes sautées**, mais n'est pas une preuve absolue d'une pagination de texte sémantique comparable à EPUB sur toutes les polices ou mises en page. Les sauts de paragraphes, les longues lignes et les images nécessitent une réception sur appareils physiques, y compris sous Zoom/VoiceOver/TalkBack.

V55 est une PR **empilée sur V54 #968**, elle-même sur V53 #964 et V52 #961. Elle doit rester en brouillon tant que ses CI ne sont pas vertes et que les validations physiques et la revue des droits privés [V51 #947](https://github.com/M0rdr3x/BenoitCantin/pull/947) ne sont pas achevées.

**Aucun relèvement de la maturité SINJIRA (66,5 % ±10 points), aucune fermeture des 13 portes de lancement, aucun déploiement.**
