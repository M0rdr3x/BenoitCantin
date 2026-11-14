# SINJIRA™ — V77 : navigation par balayage dans les tableaux immobiles

**14 novembre 2026** — correctif de la liseuse mobile dans la [PR unique #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), **DRAFT / non déployée**.

## Incident corrigé

Les protections V73/V74 réservaient automatiquement un geste tactile à tout tableau ou encadré horizontalement défilable, même sans mouvement du tableau. Sur un écran de téléphone étroit, une grande zone de la page pouvait donc refuser un balayage pourtant intentionnel vers la page suivante ou précédente.

## Règle V77

- Capturer au `touchstart` la position `scrollLeft` des conteneurs internes défilables horizontalement, en s'arrêtant à la zone de lecture. Pas d'accès au texte ou aux données privées.
- Sur `touchmove` et `touchend`, refuser de tourner une page si une note ou un tableau s'est **réellement déplacé de plus de quatre pixels CSS**, même si sa position revient ensuite à l'origine.
- Si le tableau reste immobile, autoriser le **glissement gauche vers la page suivante** et le **glissement droite vers la précédente**, en PDF V52 et en texte paginé V53.
- Préserver la protection contre le panoramique natif du lecteur entier et le contenu texte lui-même; ne pas modifier les garde-fous V66–V76 (zoom, rotation, sélection, scroll vertical, gestes système, boutons et progression).

## Vérification et correction de tests

Cinq nouveaux tests Node V77 couvrent : les gestes dans les deux directions dans un tableau PDF immobile, le retour à la position `scrollLeft` après déplacement, la capture limitée aux vrais descendants du lecteur, le texte paginé immobile et la reprise du geste après un scroll transitoire. Les tests antérieurs V73/V74 ont été adaptés pour déclencher un **véritable changement `scrollLeft`**, plutôt que de considérer un dépassement de taille comme un déplacement.

Exécuter les deux suites Node V52/V53 et les workflows V64–V69 sur le SHA V77 exact.

## Conditions de mise en ligne

Vérifier physiquement sous iPhone Safari et Android Chrome (portrait/paysage) les balayages sur un tableau immobile, sur un tableau réellement déplacé puis relâché, en mode texte/PDF, avec VoiceOver/TalkBack, zoom et gros caractères. Confirmer les droits aux livres privés et la reprise de lecture entre deux appareils avant fusion/déploiement.

**Statut : DRAFT / NO-GO, aucun changement sur `main`, sans migration ou modification des droits privés.** La maturité globale SINJIRA demeure une estimation de **66,5 % ±10 points** avec les portes de lancement encore ouvertes.
