# SINJIRA V126 — garder la page d'écran stable si le texte change pendant un geste

**15 novembre 2026.** Correctif candidat dans PR #1000 (brouillon), non déployé.

## Défaut

V123 et V125 annulent un toucher PDF devenu périmé grâce aux observations du module tactile V52. Toutefois, sur les écrans de texte V53 intercepte `touchend` *en phase de capture* avant V52. Une bascule cachée PDF → texte → PDF dans la même tâche JavaScript, ou un remplacement du texte par le moteur de lecture, peut revenir au même état avant que le `MutationObserver` du V53 ait exécuté son callback. La V53 peut alors tourner un écran avec une trajectoire ayant commencé sur une autre représentation.

## Correctif

- Le moteur d'écrans V53 lit `observer.takeRecords()` avant `touchstart`, `touchmove` et `touchend` et annule le geste si la zone texte a subi une mutation `hidden`, `childList` ou `characterData`.
- Toute mutation consommée est synchronisée explicitement par `afterTextChanged()`, afin de ne pas perdre le réagencement que le callback différé aurait assuré. Une mutation sans rapport n'interrompt pas le geste.
- Le module tactile PDF V52 garde son correctif V125 et les protections précédentes. Aucun changement de texte, stockage privé, sauvegarde, compte ou requête réseau.
- Cache V53 synchronisé à `53.11.15.126` dans `compte/liseuse.html`, fixture et tests. Le moteur V52 reste à `52.11.15.125`.

## Couverture

- Node : texte caché puis réaffiché pendant un swipe, mutation de contenu pendant la même tâche, mutation non pertinente, rechargement en attente avant `touchstart`, nouveau geste gauche/droite possible après annulation.
- Playwright V58 : vraie fixture mobile de liseuse sous Chromium et WebKit, `touchstart`, double mutation `hidden`, `touchend` synchrone avant le callback différé et contrôle strict de la page/position/layout inchangés.
- Les tests de navigation précédents restent actifs.

**NO-GO** : la PR n'est pas fusionnée ni déployée. Les essais physiques iOS/Android, VoiceOver/TalkBack, Auth/RLS du roman privé, synchronisation interappareils et 13 conditions de lancement requièrent toujours une homologation. Les pourcentages Nova/SINJIRA restent ceux du dernier bilan documenté.
