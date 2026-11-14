# SINJIRA™ V66 — Distinguer un balayage horizontal d'un défilement vertical

**12 novembre 2026 — PR candidate de fiabilité, non publiée.**

## Risque corrigé

Les modules tactiles V52 (pages PDF) et V53 (pages de texte adaptées aux téléphones) classifiaient les gestes avec leurs seules coordonnées de **début et de fin**. Un mouvement du doigt **d'abord vertical, puis horizontal, puis revenu à la hauteur initiale** pouvait passer pour un vrai balayage horizontal, entraînant involontairement le changement de la page PDF ou de l'écran de lecture. La même ambiguïté existait lorsqu'un défilement natif intervenait pendant le contact.

Une liseuse mobile doit laisser le défilement vertical, la sélection, les annotations et le zoom disponibles, sans tourner les pages accidentellement.

## Mesures implémentées

- Le classificateur commun `classifyReaderSwipe` accepte `maxVerticalTravel` (la plus grande excursion verticale pendant le contact) et `scrolledDuringGesture` (un défilement de la zone au-delà de 8 px). Ces paramètres sont optionnels, avec des valeurs compatibles avec les tests précédents.
- Les deux moteurs mémorisent une trajectoire **éphémère** pendant `touchstart/touchmove/touchend`, l'identifiant du doigt et le scroll initial.
- Si le geste revient à sa hauteur d'origine, l'excursion verticale maximale demeure prise en compte. Si le défilement a bougé puis est revenu, le geste reste refusé.
- Un défilement vertical intervenu pendant le toucher annule la commande de changement de page. Les vrais gestes horizontaux restent autorisés.
- Les gestes multi-touch, les menus interactifs et les sélections restent traités par les protections V52–V65.
- Aucun texte du livre, aucune coordonnée du doigt et aucune information d'identité ne sont conservés au-delà du geste, ni transmis au serveur.

## Couverture automatisée

1. **Sept tests Node supplémentaires** : classification avec excursion verticale, défilement pendant le contact, trajets gauche/droite complexes dans les deux moteurs, et maintien des vrais gestes.
2. La recette **V66 sur la vraie page** `compte/liseuse.html?edition=demo` (avec faux PDF et réseau Supabase bloqué), en **Chromium et WebKit**, à 390×844 et 320×568 px : trajet vertical→gauche, vertical→droite, scroll intermédiaire, vraie navigation horizontale en mode écran et PDF libre.
3. Réexécution des parcours V54/V57/V58 et du banc V65 `Input.dispatchTouchEvent` sur Chromium, pour s'assurer que la protection ne bloque pas les vrais événements du navigateur.
4. Le nouveau workflow ne fait que lire du code et exécuter des tests; il ne publie rien et n'accède pas aux romans privés.

La validation sera qualifiée de réussie **seulement après le succès des jobs sur le dernier SHA**. Les outils de navigateur ne remplacent pas des essais physiques iPhone Safari / Android Chrome, notamment les gestes natifs de défilement inertiel, VoiceOver et TalkBack.

## Séquencement et critères de publication

Cette PR V66 est empilée sur la [PR candidate d'intégration de liseuse #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) (V64 et V65). La branche principale `main` n'intègre pas encore le lecteur mobile candidate. La sécurité des progressions et les droits sur les livres intégraux restent un chantier indépendant dans la [PR V59 #986](https://github.com/M0rdr3x/BenoitCantin/pull/986).

Pour produire un GO, restent obligatoires les essais physiques, les vraies éditions intégrales avec droits vérifiés, les contrôles VoiceOver/TalkBack, les caches, la navigation retour et la synchronisation sur deux appareils.

**SINJIRA : 66,5 % ±10 points**, 13/13 portes globales de lancement ouvertes, date de fin inconnue. La maturité de Projet Nova (47 %), du programme Nova–Sinjira (non calculable), de la boussole (75 %) et du sondage (54,5 %) reste décrite dans le [bilan de référence fusionné dans main](https://github.com/M0rdr3x/BenoitCantin/blob/main/docs/AVANCEMENT_QUATRE_PROGRAMMES_2026-11-10.md).
