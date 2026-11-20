# SINJIRA V125 — ne pas tourner la page après une bascule PDF synchronisée

**15 novembre 2026** — modification candidate PR #1000, non fusionnée et non déployée.

## Risque résiduel

V123 annule les gestes PDF/texte quand un MutationObserver détecte un changement d'attribut `hidden`. Or, MutationObserver est livré de façon asynchrone à la fin de la tâche JavaScript : si une application bascule de PDF à texte puis de texte à PDF et envoie `touchend` ou `pointerup` sans relâcher la tâche JS, le rappel n'est pas encore exécuté. Le code pouvait alors interpréter la fin d'un ancien geste comme une nouvelle page, même si la représentation était revenue à son état initial.

## Correction

- V52 interroge `MutationObserver.takeRecords()` **avant** `touchmove`, `touchend`, `pointermove` et `pointerup`. Une mutation `hidden` dans l'historique depuis le début du contact entraîne l'annulation du geste en cours. Les transitions PDF→texte→PDF, le masquage/réaffichage du contenu intégral et la souris PDF sont couverts.
- Avant chaque nouveau `touchstart` ou `pointerdown`, les anciens records sont purgés : un changement survenu avant le geste n'invalide jamais un nouveau swipe légitime.
- Le callback normal de V123 est conservé. Les événements étrangers à `hidden` ne bloquent pas la navigation; aucune copie de texte, identité de lecteur ou écriture de progression n'est effectuée.
- V52 mis en cache avec le suffixe `52.11.15.125` dans la page, l'import V53, la fixture de recette et les tests. V53 reste à `53.11.15.124`.

## Vérifications

- Node : observer factice avec `takeRecords`, changement PDF→texte→PDF dans la même tâche, masquage/réaffichage, purge des mutations anciennes, changements non pertinents, glissement souris PDF et nouveaux gestes gauche/droite.
- Playwright V58 Chromium/WebKit : véritable HTML local isolé et roman fictif, deux attributs `hidden` modifiés pendant un geste, `touchend` SYNCHRONE avant le rappel de MutationObserver, contrôle de l'absence de page fantôme et restauration de la pagination par écrans.

**Statut de publication : NO-GO.** PR #1000 DRAFT, non fusionnée dans `main` ni déployée. Essais physiques iPhone/Android, VoiceOver/TalkBack, droits Auth/RLS des livres privés, synchronisation entre appareils et les 13 conditions de lancement restent à homologuer. Les pourcentages des programmes Nova et SINJIRA ne changent pas.
