# SINJIRA — V112 : accès mobile direct seulement si le roman est visible

**14 novembre 2026 (Québec)** — PR #1000 en revue, pas de publication.

## Constat et réparation

Le raccourci « Aller directement au livre » était accessible pendant que le livre demeurait masqué par le moteur V26 (chargement, session suspendue, droits invalides). La destination était alors une zone cachée.

- Désormais, `hidden` est présent sur le lien dans le HTML par défaut.
- `bindReaderQuickAccess` ne surveille que l'attribut `hidden` de `#reader-content` via `MutationObserver` : le lien apparaît si et seulement si le moteur V26 présente la zone de lecture.
- Une règle CSS explicite donne priorité à `[hidden]`, même quand le lien reçoit son style de bouton tactile sur mobile.
- Aucune autorisation n'est créée ou modifiée. Aucune donnée de compte, de texte privé ni de progression n'est consultée ni transmise ; PDF, swipe gauche/droite et réglages restent identiques.

## Contrôles de non-régression

Tests Node : état inaccessible initial, livre affiché, session suspendue, retour du livre et nettoyage de l'observateur. Playwright Chromium et WebKit sur page réelle avec livre synthétique et accès privé bloqué : masquage et réaffichage contrôlé du conteneur, synchronisation du lien après une trame. Versions CSS/JS V53 alignées à `53.11.14.112`.

**NO-GO** : PR non fusionnée, aucune validation sur appareils physiques iPhone et Android ou VoiceOver/TalkBack, droits privés et synchronisation multi-appareils encore à homologuer. Les taux globaux des programmes restent ceux des derniers audits.
