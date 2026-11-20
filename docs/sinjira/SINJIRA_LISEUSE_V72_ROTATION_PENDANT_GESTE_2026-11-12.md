# SINJIRA — V72 : ne pas tourner une page lors d'une rotation ou d'un redimensionnement

**12 novembre 2026** — Correctif de la branche candidate [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), en lecture mobile, sans migration de données ni modification des droits privés.

## Anomalie prévenue

Un contact tactile commence à une certaine taille de livre. Pendant ce même contact, le téléphone peut pivoter, le navigateur peut redimensionner la zone ou les barres système peuvent modifier le viewport. Une fois la géométrie changée, les coordonnées du doigt ne représentent plus la même intention : une fin de geste horizontale ne doit pas déclencher un tournage du livre.

## Comportement retenu

- Capturer au premier doigt les dimensions du lecteur `clientWidth/clientHeight` et du viewport `innerWidth/innerHeight`.
- À `touchmove` et à `touchend`, refuser de tourner l'écran ou la page si une dimension détectable change de **plus de quatre pixels CSS**. Une variation transitoire capturée pendant le mouvement invalide définitivement le geste.
- Tolérer les fluctuations de 4 pixels ou moins pour ne pas supprimer les gestes légitimes sur des moteurs mobiles avec arrondis.
- Conserver les protections V66–V71 : défilement vertical, bords système, débordement horizontal, sélection et zoom natif. La reprise de lecture pendant rotation reste gérée par le moteur V63/V69.
- Une fois la rotation terminée, un **nouveau** glissement gauche/droite reste fonctionnel.

## Vérifications

Cinq tests Node additionnels couvrent les dimensions stables, la rotation en fin de contact PDF et texte, les fluctuations transitoires détectées à `touchmove` et le retour à une navigation normale. Les workflows CI V64–V69 doivent être rejoués sur le SHA final; les résultats antérieurs ne sont pas transférables automatiquement.

## Conditions de réception physique et publication

Faire tourner un **iPhone Safari** et un **Android Chrome** physiques pendant un geste horizontal (texte paginé et PDF). Vérifier l'absence de page changée et de saut de lecture; répéter après rotation, avec gros caractères, VoiceOver/TalkBack et zoom. Tester la reprise d'un livre autorisé entre deux appareils avant tout GO de publication.

**Statut : DRAFT / NO-GO** : pas de preuve d'appareils réels, pas de revue indépendante, pas de nouvelle certification des droits privés. Les scores Nova, Nova–Sinjira et SINJIRA restent inchangés.
