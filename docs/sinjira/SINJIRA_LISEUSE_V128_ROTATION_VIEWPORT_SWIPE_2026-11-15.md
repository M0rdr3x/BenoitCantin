# SINJIRA V128 — annuler les gestes sur rotation ou changement visuel du téléphone

**15 novembre 2026**, PR #1000 en brouillon, sans fusion ni déploiement.

## Risque mobile

Les moteurs V52 (PDF/texte continu) et V53 (écrans) vérifient la géométrie en fin de swipe, mais Safari iOS et Chrome Android peuvent modifier les barres d'interface, la rotation ou le viewport, puis retrouver la même taille pendant que le doigt est encore posé. Une ancienne trajectoire peut alors tourner une mauvaise page.

## Correction

- V52 : les événements `window.resize`, `orientationchange` et `visualViewport.resize` invalident immédiatement les gestes tactiles et souris PDF en cours. Les écouteurs sont nettoyés au démontage, sans modifier la page, le stockage ni les préférences.
- V53 : `onResize` annule le contact avant la restauration de position; `visualViewport.resize` l'annule même en cours de pinch zoom, et `orientationchange` déclenche la même protection. Les ancrages de texte V63 restent actifs et les nouveaux swipes sont autorisés.
- Versions cache synchronisées : V52 `52.11.15.128` et V53 `53.11.15.128`, dans HTML, fixture, import et contrats.

## Tests

- Node PDF : resize, orientationchange, visualViewport resize, drag souris et nouveaux gestes gauche/droite, déconnexion complète.
- Node texte paginé : mêmes événements, zoom visuel temporaire, gestes suivants et nettoyage des listeners.
- Playwright V58 Chromium/WebKit : vraie page isolée, livre fictif, orientationchange entre touchstart et touchend sans nouvelle géométrie finale, aucun saut de page.

**Publication : NO-GO.** PR #1000 reste DRAFT, non fusionnée dans `main`, non déployée. iPhone et Android physiques, VoiceOver/TalkBack, droits Auth/RLS du roman privé, synchronisation interappareils et 13 conditions de lancement non homologuées. Aucun recalcul des pourcentages Nova/SINJIRA.
