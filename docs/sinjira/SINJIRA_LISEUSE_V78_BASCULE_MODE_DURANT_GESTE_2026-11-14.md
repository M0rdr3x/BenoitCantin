# SINJIRA™ — liseuse mobile V78 : changement de mode pendant un balayage

**14 novembre 2026.** Correctif candidat dans la [PR unique #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), **DRAFT, non fusionnée ni déployée**.

## Défaut

Le gestionnaire tactile PDF V52 prend connaissance de `dataset.readerLayout` en fin de contact seulement. Si le toucher commence pendant l'affichage de texte paginé puis que l'interface bascule vers le PDF/continu avant `touchend`, le gestionnaire PDF pouvait provoquer un changement de page involontaire à partir d'un toucher commencé sous un **autre mode**.

Le moteur V53 utilisait `isPaged` en fin de geste, mais une bascule rapide du mode pages vers continu et retour vers pages durant un même toucher pouvait rendre la direction du geste ambiguë.

## Modification V78

- Le geste PDF enregistre le **mode initial** au premier toucher; le gestionnaire l'annule si le mode diffère à `touchmove` ou `touchend`, y compris si le mode a déjà changé plusieurs fois.
- La bascule réelle du contrôle texte paginé/continu dans V53 invalide **immédiatement** le geste en cours. Les `touchmove` et `touchend` refusent aussi les changements détectables de `readerLayout` et un mode pages désactivé.
- Un nouveau geste, après stabilisation dans le mode choisi, fonctionne normalement gauche vers suivant et droite vers précédent.
- Aucune modification de l'authentification, des droits aux romans, de la sauvegarde de position, du schéma Supabase ni du contenu des livres.

## Contrôle

**Quatre tests Node** simulent la bascule pendant un contact : écran vers PDF sans tourner une fausse page, bascule temporaire puis rétablissement du PDF sur `touchmove`, bascule et réactivation des pages V53 et perturbation temporaire du mode V53. Vérifier aussi les suites Chromium/WebKit de la vraie page avec PDF fictif, sans compte réel, sur le SHA V78 exact.

### Barrières de publication

Essais physiques obligatoires iPhone Safari et Android Chrome, portrait/paysage, sélection de mode pendant le contact, zoom, boutons tactiles, grandes polices, VoiceOver et TalkBack. Revue des autorisations sur romans privés et de la synchronisation autorisée interappareils avant la fusion.

**Statut : NO-GO production ; score SINJIRA programme complet 66,5 % ±10 points inchangé.**
