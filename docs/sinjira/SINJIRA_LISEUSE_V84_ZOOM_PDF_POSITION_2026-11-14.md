# SINJIRA™ — V84 : zoom sur les pages illustrées PDF automatiques et position de lecture préservée

**14 novembre 2026.** Correctif candidat dans la [PR de liseuse #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), **DRAFT / non fusionnée, non déployée**.

## Problème réellement observé dans le code

Les pages illustrées ou non extractibles du roman sont affichées automatiquement comme PDF par V81/V82, alors que le choix enregistré reste **« texte adaptable »**. Jusqu'à V83, le menu **Zoom (affichage PDF)** appelait `renderPage()` uniquement lorsque `state.mode==='page'`. Le zoom ne changeait donc **rien** sur l'illustration temporaire. Par ailleurs, une rotation ou un zoom pouvait conserver une valeur de `scrollTop` absolue au lieu de la fraction de page lue : la lecture sautait verticalement après changement de taille.

## Comportement V84

- Identifier le canvas PDF réellement visible même si la préférence est « texte adaptable », sans forcer le mode PDF pour les autres pages.
- Le zoom de **80 % à 150 %** redessine cette illustration au bon facteur. Un zoom volontaire supérieur à la largeur disponible conserve son panoramique horizontal natif (le glissement pour changer de page ne doit pas le voler).
- Avant le zoom ou une rotation du PDF, mémoriser la **fraction de défilement de la page source** (ratio local) et la rétablir après le rendu. Conserver en priorité toute restauration déjà en attente, par exemple après un changement de page ou la reprise de lecture.
- Si le rendu courant échoue, libérer le verrou temporaire `restoringScroll` pour que la prochaine sauvegarde puisse fonctionner. Aucune exception contenant potentiellement du texte privé n'est journalisée.
- Ne pas modifier les données sauvegardées, les droits Auth/RLS, la synchronisation interappareils, les romans privés, ni les gestes tactiles des autres pages.

## Tests navigateur automatiques

L'essai E2E V81, lancé dans Chromium et WebKit par le workflow V69, effectue le parcours sur la vraie page HTML et un **PDF entièrement fictif** :

1. À **320 × 568**, l'illustration PDF automatique (page 4) s'affiche sans débordement horizontal.
2. Se placer à **45 % du défilement**, sélectionner le **zoom 150 %**, puis vérifier l'agrandissement et une position conservée à **±0,12** de la fraction initiale, sans modification du choix texte.
3. Revenir au **zoom 100 %**, vérifier la largeur initiale, la position préservée et l'absence de débordement.
4. Naviguer à gauche vers la page texte 5, revenir à la page illustrée, tourner le téléphone en **844 × 390**, puis naviguer à droite vers la page texte 3. Le choix PDF explicite continue d'être respecté.
5. Aucun roman privé, compte réel, réseau externe ou accès Supabase dans les tests.

Exiger la réussite des workflows sur le SHA exact. Les simulations ne constituent pas une recette physique iPhone/Android ou VoiceOver/TalkBack. Validation serveur des droits au roman intégral, RLS et reprise réelle entre deux appareils toujours bloquantes avant fusion/déploiement. **Maturité globale SINJIRA 66,5 % estimés ±10 points, 13 portes de lancement ouvertes.**
