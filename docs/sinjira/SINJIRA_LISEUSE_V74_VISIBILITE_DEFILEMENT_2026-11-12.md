# SINJIRA™ — V74 : débordement masqué ≠ geste de défilement disponible

**12 novembre 2026.** Correctif de la liseuse tactile candidate [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), non fusionnée en production.

## Défaut évité

Le mode texte « pages d'écran » impose `overflow-x:hidden` à la zone du livre, pour une expérience de liseuse. Il peut néanmoins exister une différence positive entre `scrollWidth` et `clientWidth` (mot très long, image ou tableau trop large). Depuis V70/V73, une telle différence seule pouvait réserver le balayage horizontal au navigateur, **alors que ce débordement masqué ne peut pas défiler au doigt**. Résultat potentiel : glisser à gauche ne tourne plus la page, sans possibilité de déplacement horizontal.

## Correctif V74

- Contrôler le **style calculé CSS `overflow-x`**, en plus de `scrollWidth > clientWidth + 4` : réserver le geste au défilement horizontal seulement si `overflow-x` est défilable (`auto`, `scroll` ou valeur analogue).
- Ne pas réserver un geste à `overflow-x: hidden`, `clip` ou `visible` même si la largeur du contenu excède celle du conteneur.
- Déployer le même critère en mode PDF V52, en mode pages d'écran V53 et sur les éléments imbriqués V73.
- Lorsque le style calculé est indisponible, **préserver prudemment le défilement possible** plutôt que voler un mouvement destiné au navigateur.
- Les boutons tactiles Précédente/Suivante, la reconnaissance gauche/droite, la sélection du texte, les protections de zoom/rotation et la persistance de lecture ne sont pas modifiés.

## Tests Node ajoutés

Cinq nouveaux tests vérifient les trois styles non défilables, les styles défilables, la tolérance de quatre pixels, le geste dans le PDF, le reflow malgré un débordement masqué et le respect d'une annotation réellement défilable. Les workflows Chromium et WebKit V64–V69 doivent être réussis **sur le dernier commit**, sans reprendre automatiquement les résultats antérieurs.

## Barrières de publication

Tests physiques nécessaires sur Safari iOS et Chrome Android : téléphone portrait/paysage, texte très long avec débordement caché, encadré `overflow-x:auto`, tailles de police, zoom natif et reprise d'une vraie page de livre. Vérifier les droits du roman intégral et la synchronisation autorisée entre deux appareils, et obtenir la revue indépendante avant de fusionner cette PR.

**Statut : PR DRAFT / NO-GO production; SINJIRA global 66,5 % ±10 points inchangé.**
