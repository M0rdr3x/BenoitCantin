# SINJIRA™ — V91 : annuler les balayages interrompus par une suspension mobile

**14 novembre 2026 — PR #1000 en brouillon, aucun déploiement.**

## Problème

Un téléphone peut perdre le focus de son navigateur pendant que le doigt se déplace sur le livre : changement d'application, mise en veille, verrouillage, appel ou onglet masqué. La plateforme peut ne pas émettre `touchcancel` pour le geste. Sans invalidation du geste en mémoire, un `touchend` tardif pourrait être interprété comme « page suivante » ou « page précédente », provoquant un saut de lecture involontaire.

## Correction V91

- **Texte paginé V53 et PDF V52** : annuler la reconnaissance d'un toucher en cours sur `window.blur`, `window.pagehide` et `document.visibilitychange` lorsque `document.hidden` devient vrai.
- Lorsqu'un onglet reste visible, un événement de visibilité non masquante ne doit pas bloquer les prochains gestes normaux.
- Tous ces écouteurs sont déconnectés avec le moteur de lecture ; aucun changement d'authentification, de livre privé ou de données de progression.
- Les gestes horizontaux en premier plan conservent leur sens : gauche = avance, droite = retour ; le défilement vertical, le pinch-zoom et les gestes système restent prioritaires.

## Contrôles

1. Tests Node V52 et V53 : un `touchstart` valide, puis chacune des trois interruptions, puis `touchend` **ne provoque aucun tournage de page** ; le balayage suivant en premier plan fonctionne ; les écouteurs sont nettoyés.
2. Test navigateur `test_sinjira_liseuse_mobile_v54.py` sur le vrai moteur de pagination en Chromium et WebKit : `blur` et `visibilitychange(hidden)` synthétiques intercalés pendant le geste, sans navigation du livre.
3. Tous les autres tests de pagination, zoom, retour arrière, navigateur paysage, sauvegarde et frontière privée restent obligatoires. Le PDF de test est fictif et Supabase n'est pas sollicité.

**Limites et statut : NO-GO production.** Les signaux sont simulés : les suspend/reprise physiques, appels entrants, VoiceOver/TalkBack et navigateur sur appareil réel doivent encore être reçus. La synchronisation sûre entre appareils, les droits de roman intégral et les 13 portes de lancement ne sont pas homologués.

**Progression de référence du 8 novembre inchangée :** Nova 47 %, Nova–Sinjira non chiffrable, sondage 54,5 %, boussole 75 %, SINJIRA 66,5 % ±10 points. La date conditionnelle du 31 décembre 2027 concerne uniquement le programme Nova.