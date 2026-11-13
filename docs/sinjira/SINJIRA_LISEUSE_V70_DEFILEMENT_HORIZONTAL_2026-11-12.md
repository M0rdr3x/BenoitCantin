# SINJIRA™ — V70 : protéger le défilement horizontal sur mobile

**Périmètre :** liseuse mobile candidate, branche d'intégration de la PR #1000. Aucun changement des identités, des droits d'accès aux romans privés, du moteur de persistance, ni des migrations Supabase.

## Comportement attendu

- **Glisser à gauche** dans le texte ajusté à l'écran : écran de lecture suivant, puis page du PDF suivante lorsque le texte de la page source est terminé.
- **Glisser à droite** : écran précédent, puis page PDF précédente au début du texte source.
- **Contenu plus large que l'écran** : laisser le navigateur gérer le défilement horizontal, sans `preventDefault()` et sans tournage de page. Les boutons tactiles Précédente et Suivante restent accessibles.
- **Tolérance :** 4 pixels CSS pour éviter les faux débordements subpixels, borders et arrondis.
- **Gestes non horizontaux** : conserver le défilement vertical, sélection de texte, pinch-to-zoom et les zones de navigation système iOS/Android héritées des versions V66/V67.

## Régressions automatiques ajoutées

1. `viewer.scrollWidth > viewer.clientWidth + 4` : aucun changement de page au swipe, mais bouton Suivante fonctionnel.
2. `text.scrollWidth > text.clientWidth + 4` : aucun retour tactile accidentel.
3. Débordement de 4 pixels exactement : balayage normal toujours accepté.

Exécuter `node --test tests/sinjira-liseuse-touch-v52.test.mjs tests/sinjira-liseuse-reflow-v53.test.mjs` et les workflows Chromium/WebKit V64–V69 de la PR. Les chiffres de CI doivent être consignés **après** exécution sur le SHA final, jamais anticipés.

## Réception physique et décision

Réaliser le parcours sur iPhone Safari et Android Chrome réels, portrait et paysage, caractères de 34 px, avec les modes **pages d'écran** et **PDF**, VoiceOver/TalkBack, ainsi que du texte PDF volontairement trop large. Vérifier que l'extrémité du texte reste accessible, que le geste ne déclenche pas de double page, et que le livre autorisé reprend à la bonne position sans exposer son contenu dans le stockage local.

**Statut : PR DRAFT / NO_GO production** tant que la revue indépendante et les essais sur appareils physiques et comptes autorisés ne sont pas documentés. Ce correctif ne modifie pas le score de maturité SINJIRA (66,5 % ±10 points) ni les portes de lancement.
