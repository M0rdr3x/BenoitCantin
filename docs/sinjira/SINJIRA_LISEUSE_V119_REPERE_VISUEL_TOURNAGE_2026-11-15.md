# SINJIRA V119 — retour visuel discret lors d'un changement de page

**15 novembre 2026** — code candidat PR #1000, pas de publication.

## Amélioration de l'expérience liseuse

Les vrais lecteurs de livre fournissent un retour perceptible lorsqu'on tourne la page. V119 ajoute un **liseré lumineux de 180 ms** sur le côté correspondant au sens du passage : bord droit pour écran/page suivante, bord gauche pour écran/page précédente. Le contenu reste strictement immobile : pas de changement de typographie, pas de déplacement de lignes, pas de transition entre deux textes, pas d'écriture de progression ni de données privées. Le mouvement du doigt continue à commander les changements d'écran ou de page comme auparavant.

L'effet utilise l'API Web Animations si disponible, et ne change aucun élément DOM. Il est **automatiquement supprimé** si la préférence système `prefers-reduced-motion: reduce` est active, ainsi que sur navigateurs dépourvus de l'API. Aucun comportement de lecture ne dépend de la disponibilité de l'animation.

Le module V52 l'active uniquement sur les boutons canoniques PDF, qui sont également actionnés par les swipes et les tapotements de marge; le texte paginé V53 l'active sur les passages réels d'écran et de page source. Les gestes ignorés, les pages limites, le zoom et la sélection ne doivent pas produire d'effet. Les écouteurs du PDF sont retirés lors du nettoyage.

## Recette

- Tests Node : gauche/droite distincts, durée de 180 ms, préférence d'animation réduite, API d'animation manquante ou défaillante, swipe ignoré sans animation et nettoyage des écouteurs.
- Playwright Chromium/WebKit, cinq résolutions : instrumentation de `viewer.animate` pour deux vrais swipes successifs gauche/droite, puis activation `prefers-reduced-motion: reduce` et confirmation que les nouveaux swipes fonctionnent **sans** animation.
- Cache busting cohérent : V52 `52.11.15.119`; V53 `53.11.15.119`.

**NO-GO de publication** : PR #1000 toujours brouillon et non fusionnée; tests sur vrais iPhone/Android, VoiceOver/TalkBack, autorisations privées, synchronisation et les 13 conditions de lancement encore indispensables. Les taux de maturité Nova/SINJIRA restent ceux du dernier audit interne.
