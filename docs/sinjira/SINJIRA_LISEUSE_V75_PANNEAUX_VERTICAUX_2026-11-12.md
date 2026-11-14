# SINJIRA — liseuse mobile V75 : priorité au défilement des notes intégrées

**12 novembre 2026.** Correctif soumis dans la [PR unique d'intégration #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), toujours **DRAFT / non fusionnée**.

## Scénario

Des passages de roman peuvent contenir une note, un encadré ou une référence détaillée avec sa propre hauteur et `overflow-y:auto` ou `scroll`. Un geste diagonal ou horizontal commencé sur ce panneau ne doit pas quitter la page du roman alors que la personne consulte la note. Les mesures verticales du **conteneur principal** ne prouvent pas que l'utilisateur n'a pas défilé à l'intérieur de la note.

## Correctif

- V75 détecte la capacité réelle d'un conteneur **descendant** à défiler verticalement : `scrollHeight > clientHeight + 4` et `overflow-y` autorisant le défilement.
- Depuis la cible tactile, la recherche s'arrête **avant** l'élément de lecture parent : le lecteur général n'est pas considéré comme une note imbriquée.
- Lorsque le contact commence dans un panneau vertical défilable, la navigation par balayage **ne tourne pas** la page, ni dans le PDF V52, ni dans le texte reflow V53; les événements restent au navigateur.
- `overflow-y:hidden/clip/visible` ne bloque pas le geste de pagination; les boutons Précédent/Suivant restent accessibles.
- Si le style calculé est indisponible, privilégier la prudence vis-à-vis d'un possible scroll natif.
- Aucune modification des comptes, RLS, Supabase, sauvegarde, roman privé ni sélection de texte.

## Vérification

Six régressions Node ciblent les styles, les dimensions, les éléments hors du lecteur, les deux directions PDF et les deux états (défilable/masqué) en lecture écran. Exécuter `node --test tests/sinjira-liseuse-touch-v52.test.mjs tests/sinjira-liseuse-reflow-v53.test.mjs` puis les workflows Chromium/WebKit V64–V69 sur le **SHA exact**.

## Réception avant publication

Sur iPhone Safari et Android Chrome physiques, ouvrir un livre de démonstration autorisé contenant un encadré `overflow-y:auto`. Faire défiler la note, balayer gauche et droite dans la note, puis hors de la note et avec les boutons tactiles. Vérifier le zoom, la rotation, VoiceOver/TalkBack et la reprise de lecture interappareils. Une simulation automatisée n'est pas une preuve d'appareil physique.

**Statut : NO-GO tant que les essais physiques, les droits au contenu intégral et la revue indépendante n'ont pas été approuvés.** Score SINJIRA complet inchangé : 66,5 % ±10 points, 13 portes de lancement ouvertes.
