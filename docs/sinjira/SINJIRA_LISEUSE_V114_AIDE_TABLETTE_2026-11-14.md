# SINJIRA — V114 : aide tactile accessible aussi sur tablette

**14 novembre 2026, heure du Québec** — amélioration candidate de la PR #1000, sans déploiement.

## Régression d'ergonomie identifiée

La V113 avait remplacé l'immense paragraphe de consignes par un élément natif `details/summary`, replié au chargement. Mais la cible tactile de 44 px, le focus visible et les marges de l'aide avaient été placés dans `@media(max-width:760px)` uniquement, tandis que le mode « pages d'écran » et la barre de navigation tablette vont jusqu'à **980 px**. Les tablettes 768–980 px restaient donc avec un résumé natif moins facile à activer.

## Correction V114

Les styles `summary` (cible minimale 44 px, retour visuel du focus clavier, indicateur d'ouverture) et ceux du paragraphe déplié sont mutualisés dans `@media(max-width:980px)`. Les règles de fond de page pour le téléphone et la tablette restent inchangées. Le CSS est cache-busté à `53.11.14.114` dans le HTML.

**Contrôles :** test Node des règles responsives, maintien du `aria-describedby`; parcours Playwright Chromium et WebKit sur la vraie page avec livre synthétique, à 320, 390, 844 paysage, 768 et 820 px. Les deux tablettes testent la hauteur cible, l'ouverture/fermeture et l'absence de changement de page source. La navigation gauche/droite, la sélection de texte, le stockage et les droits privés ne sont pas modifiés.

**NO-GO publication** : PR toujours brouillon, pas de fusion dans `main` ni de mise en ligne. Essais physiques iPhone/Android, VoiceOver/TalkBack, Auth/RLS, livres privés, reprise réelle entre appareils et autorisation humaine restent obligatoires. Pas de changement aux pourcentages des programmes audités.
