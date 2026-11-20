# SINJIRA — V69 : le geste volontaire du lecteur prime sur la restauration après rotation

**12 novembre 2026 — correctif de comportement candidat, non fusionné dans `main` ni déployé.**

## Anomalie révélée sur navigateur réel

Après fusion de V68 (hauteur de livre adaptée au paysage) dans la branche candidate #1000, la **suite complète V64 WebKit** a détecté un cas de course : pendant que `scheduleLayoutRestore` devait rétablir le passage à l'issue de deux trames d'animation, l'utilisateur pouvait déjà tourner la page par glissement. Le moteur tournait l'écran et mettait à jour l'affichage, puis l'ancien rappel de reflow pouvait réécrire la position de lecture, provoquant un retour perceptible au début de la portion.

Cette course est possible lorsque le navigateur met en page le livre de façon asynchrone. **Il ne faut pas déclarer la liseuse fiable uniquement parce qu'un swipe est consommé : sa position doit rester stable après l'événement.**

## Correction du moteur V53

- Chaque restitution différée obtient un identifiant de génération `layoutRestoreGeneration`.
- Lorsqu'un **vrai geste utilisateur** démarre dans la zone du livre, ou que les boutons/commandes de navigation déclenchent `turn`, la génération en attente est invalidée.
- Le rappel `requestAnimationFrame` double vérifie sa génération. Une restitution devenue obsolète ne peut plus ramener le lecteur à l'ancien ratio.
- Si le lecteur n'interagit pas, les restaurations V63/V64 de police et rotation continuent normalement et conservent le même caractère autant que possible.
- Les zones de geste système de 24 px V67, la sélection, le zoom, les droits PDF et les marque-pages V31/V51 sont inchangés. Aucun stockage supplémentaire.

## Preuves de réception

- Trois tests Node dédiés reproduisent une rotation différée suivie d'un **swipe**, d'un **clic suivant** et d'un **touchstart**, puis vidangent les trames différées : la position obtenue doit rester celle de l'utilisateur.
- Les anciens tests de rotation sans geste continuent de demander une restitution du ratio/du caractère.
- Une nouvelle CI V69 réexécute les suites Node et les parcours de la **vraie page** V54/V57/V58/V66 en **Chromium et WebKit**, et V65 CDP en Chromium, avec PDF entièrement synthétique et comptes Supabase bloqués.
- Le critère n'est pas assoupli : un geste doit **avancer le livre et y rester**. Les succès V68 antérieurs ne remplacent pas les contrôles V69 sur son SHA final.

## NO_GO production

Les essais sur de **véritables** iPhone Safari, Android Chrome, tablettes, VoiceOver/TalkBack, vrais romans intégrals autorisés, retrait des droits et synchronisation multiappareil restent nécessaires. [PR candidate de liseuse #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) non déployée; sécurité des livres [#986](https://github.com/M0rdr3x/BenoitCantin/pull/986) distincte.

Les chiffres du 8 novembre ne changent pas : Projet Nova politique **47 %**, Nova–Sinjira **pourcentage global non calculable** avec 14 dossiers identifiés, boussole **75 %**, sondage **54,5 %**, SINJIRA **66,5 % ±10 points** et 13 conditions globales de lancement ouvertes.