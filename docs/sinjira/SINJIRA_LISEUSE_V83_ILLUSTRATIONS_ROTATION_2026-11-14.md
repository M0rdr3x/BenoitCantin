# SINJIRA™ — V83 : couverture et illustration PDF ajustées aux petits téléphones et à la rotation

**14 novembre 2026** — correction candidate de la [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), **DRAFT, non fusionnée, non déployée**.

## Défaut confirmé dans le moteur

V81 et V82 montrent automatiquement une page PDF lorsque le texte de cette page n'est pas extractible. Toutefois, la préférence de lecture demeure « texte adaptable ». Jusqu'à V82, le gestionnaire `resize` de `assets/js/sinjira-liseuse-v26.js` ne recalculait que les pages en **mode PDF explicitement sélectionné**. Une image de fallback créée en mode texte conservait donc sa largeur après une rotation ou un redimensionnement. En outre, la largeur minimale forcée de 280 pixels CSS pouvait dépasser la largeur réellement disponible sur de très petits écrans et interdire le geste gauche/droite pour protéger le défilement horizontal.

## Correctif V83

- Calculer le rendu PDF depuis `viewer.clientWidth - paddingLeft - paddingRight - 8`, sans largeur minimale de 280 px. Garder le zoom PDF manuel et son panoramique intentionnel lorsque nécessaire, et limiter la taille maximale à 1 150 px.
- Au `resize`, recalculer également **l'image PDF provisoire** lorsque la préférence générale est « texte adaptable » mais que le contenu actuellement affiché est le canvas PDF. Conserver le délai de 250 ms contre les rafales de rotation et `renderVersion` contre les anciens rendus.
- Ne pas transformer une illustration en texte; retourner au mode paginé dès que la page source suivante contient du texte extractible. Préserver les boutons, la navigation gauche/suivante et droite/précédente, les notes, le zoom, la position, les droits et les préférences.

## Tests sur la vraie page

Le scénario V81 est étendu dans le workflow V69, sous Chromium et WebKit, avec une page 4 du **PDF fictif** dépourvue de texte :

1. à 390 px : fallback PDF visible et préférence « texte » inchangée;
2. redimensionnement à **320 × 568** : canevas recalculé plus petit, sans défilement horizontal du lecteur ni document débordant, avant de tourner à gauche vers page 5 texte;
3. retour à page 4 puis rotation **844 × 390** : canevas élargi à la place disponible, pas de défilement horizontal et geste droite vers page 3 texte;
4. le choix PDF explicite reste une préférence séparée et n'est pas remplacé automatiquement; aucune requête Supabase, roman privé ni ressource externe.

**Le passage des tests sur le SHA exact est indispensable avant de déclarer ce correctif reçu en CI.** Les simulations Chromium/WebKit ne remplacent pas une réception physique iPhone Safari/Android Chrome, VoiceOver/TalkBack, les droits au roman intégral et la reprise interappareils. **PR DRAFT / NO-GO production.** La maturité totale SINJIRA reste **66,5 % estimés ±10 points**, 13 portes de lancement ouvertes.
