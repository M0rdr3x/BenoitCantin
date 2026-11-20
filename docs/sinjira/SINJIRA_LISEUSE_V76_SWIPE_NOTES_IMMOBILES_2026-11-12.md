# SINJIRA™ — V76 : glisser dans une note immobile peut tourner la page

**12 novembre 2026.** Correctif candidat sur la [PR unique #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), non publiée.

## Pourquoi améliorer V75

V75 réservait **tout** geste horizontal commencé dans une note verticalement défilable au navigateur, même si le panneau n'avait pas bougé et que la lectrice ou le lecteur souhaitait simplement tourner la page du livre. Cela pouvait priver la personne d'une zone importante de la liseuse sur petit écran.

## Comportement V76

- Pour toute note réellement défilable et *descendante du livre*, mémoriser sa position `scrollTop` au début du geste, sans récupérer de texte ni d'identité.
- Pendant `touchmove`, si la note se déplace de plus de 4 pixels CSS, mémoriser que le défilement a eu lieu **même si elle revient ensuite au point initial**; au `touchend`, contrôler aussi les positions finales.
- Si aucun défilement réel, aucun défilement du lecteur, aucune sélection, zoom ou rotation n'est constaté, un balayage horizontal volontaire continue de tourner l'écran ou la page PDF. Le rejet d'un trajet diagonal/vertical demeure pris en charge par le classificateur V66.
- Appliquer les mêmes règles dans les modes PDF V52 et texte paginé V53, sans modifier le stockage, les romans privés, Auth, les RLS ou la sauvegarde.
- Conserver les actions tactiles accessibles Précédent et Suivant et la protection du défilement horizontal V73/V74.

## Réception et CI

Quatre tests supplémentaires V76 vérifient les deux directions PDF et la page texte à l'intérieur d'une note immobile, la tolérance 4 pixels et le défilement transitoire qui annule le changement. Les deux tests V75 relatifs aux notes défilantes ont été mis à jour pour fournir un **vrai défilement** plutôt qu'une simple taille CSS.

Exécuter les suites Node V52/V53 et les workflows navigateur V64–V69 sur le SHA exact. Reproduire les essais physiques sur iPhone Safari et Android Chrome, portrait/paysage, zoom et grosses polices, en glissant dans une note immobile, dans une note réellement défilée et hors de la note. Tester VoiceOver/TalkBack, la continuité de position, les droits au roman privé et la synchronisation interappareils avant toute fusion.

**Décision : PR DRAFT / NO-GO**, pas de déploiement; maturité SINJIRA globale inchangée **66,5 % ±10 points** et conditions de lancement non fermées.
