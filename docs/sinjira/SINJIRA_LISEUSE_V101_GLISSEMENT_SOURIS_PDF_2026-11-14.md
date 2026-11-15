# SINJIRA™ — V101 : tourner une page PDF à la souris sur ordinateur

**14 novembre 2026 — PR #1000 en brouillon (NO-GO production).**

## Nouvelle fonction

La liseuse SINJIRA V97–V100 possède déjà les balayages tactiles de gauche à droite et de droite à gauche, les tapotements des marges et la lecture par pages d'écran sur mobile. La V101 complète l'interaction **sur ordinateur** : faire glisser horizontalement **le canvas du PDF** avec le bouton principal de la souris tourne une seule page.

- Glisser vers la **gauche** : page PDF suivante.
- Glisser vers la **droite** : page PDF précédente.
- Les mouvements trop courts, obliques ou au-delà des seuils temporels habituels ne naviguent pas.
- Un curseur « prendre / glisser » apparaît uniquement sur les appareils munis d'une souris/pointeur précis et uniquement sur le canvas du PDF visible.
- L'aide intégrée explique le geste. La page de lecture charge les versions fraîches `52.11.14.101`, `53.11.14.101` et le CSS `53.11.14.101`.

## Conception défensive

L'implémentation se trouve dans `assets/js/sinjira-liseuse-touch-v52.mjs` à côté du gestionnaire tactile existant. Elle utilise `pointerdown/move/up/cancel` **avec `pointerType === 'mouse'` seulement** ; les pointeurs `touch` et `pen` restent aux modules tactiles et au système. Elle ne démarre qu'après appui principal directement sur `#reader-canvas`, lorsque `#reader-text` est masqué, le livre affiché et le mode écran inactif.

Les critères existants sont réutilisés (`classifyReaderSwipe`, géométrie, sélection, débordement horizontal, mouvement vertical, zoom, durée, boutons désactivés). Tout changement de mode, fermeture ou suspension annule le geste. La navigation se fait exclusivement par les **boutons officiels** `reader-next/previous`, afin de préserver la sauvegarde de progression et les limites de page sans modifier le stockage ou l'authentification.

## Vérifications

- `tests/sinjira-liseuse-touch-v52.test.mjs` : glisser dans les deux directions, refus du texte continu, clic simple, sélection, zoom, scroll, diagonale, contact trop long, changement de mode et non-duplication des gestes tactiles.
- `tests/e2e/test_sinjira_liseuse_real_page_v57.py` : ouvrir le **véritable canvas PDF** sur `compte/liseuse.html` avec document fictif isolé, puis `page.mouse.down/move/up` pour contrôler le passage exact 4 → 5 → 4 et les compteurs officiels. Chromium et WebKit sont testés dans des environnements émulés.
- Synchroniser les imports et versions cache V52/V53 dans la vraie page, les fixtures, les tests Node et les tests responsives.

**Certification manquante :** essais sur matériel physique iPhone/Android, VoiceOver/TalkBack, comptes et droits réels RLS/CAS, synchronisation multi-appareils. La PR n'est ni fusionnée ni déployée ; les **13 conditions de lancement SINJIRA** restent ouvertes. Aucun lancement n'est autorisé par cette V101.

## Référentiel d'avancement inchangé, au 8 novembre 2026

- Projet Nova — programme politique : **47 %**, cible du **31 décembre 2027** conditionnelle (report 2028 ou plus tard possible).
- Projet Nova–Sinjira — 14 secteurs de services publics : **pas de pourcentage global mesurable** ni de date fiable.
- Sondage citoyen : **54,5 %** (6 critères sur 11) ; collecte non ouverte.
- Boussole électorale : **75 %** (9 critères sur 12) ; date non établie.
- SINJIRA complet : **66,5 % ±10 points** ; 13 portes de lancement ouvertes ; date non établie.

Ces pourcentages ne sont pas modifiés automatiquement par une correction de liseuse.
