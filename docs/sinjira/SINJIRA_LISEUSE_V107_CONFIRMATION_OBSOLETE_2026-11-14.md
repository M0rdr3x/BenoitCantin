# SINJIRA — V107 : annulation d'une confirmation tactile devenue obsolète

**14 novembre 2026 — PR #1000, brouillon, non publiée.**

## Anomalie évitée

Avec V106, déplacer le curseur « Aller à l'écran » émet des événements `input` et son relâchement un `change`. Si une **rotation, un changement de page PDF, un défilement natif ou un vrai swipe** intervenait entre les deux, un événement `change` retardé pouvait encore exécuter une navigation vers l'ancienne sélection, au détriment du passage réellement lu.

## Mesure V107

- Marquer la sélection en attente comme **annulée** lorsqu'une action plus récente intervient (rotation, défilement, changement de mode/page ou swipe dans le texte).
- Ignorer une confirmation tardive une seule fois, réafficher l'écran réel et ne pas émettre `sinjira:reader-screen-turn` ni une sauvegarde non sollicitée.
- Une nouvelle action `input` du curseur reprend normalement le contrôle. La validation volontaire `change` reste unique comme en V106.
- Aucun nouveau stockage, texte privé, changement Auth, RLS ou migration SQL.

## Régression automatisée

`tests/sinjira-liseuse-reflow-v53.test.mjs` couvre le `change` différé après rotation, nouvelle page et swipe, puis la reprise volontaire d'une sélection. Les versions des imports du module V53 sont synchronisées dans la page réelle, la fixture et les tests responsive. Les workflows de la PR doivent être contrôlés **sur le SHA du commit V107**, sans assimiler les succès antérieurs à une nouvelle validation.

## Conditions de réception

Essais sur appareils physiques iPhone Safari, Android Chrome, écran tactile et lecteur d'écran VoiceOver/TalkBack; confirmation des droits du livre privé et de la sauvegarde interappareils autorisée. Sans ces preuves, **NO-GO de fusion vers `main` / production**. L'estimation globale SINJIRA du dernier registre reste **66,5 % ±10 points**, avec 13 portes ouvertes; aucune date de fin certifiée.
