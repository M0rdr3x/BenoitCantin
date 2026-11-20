# SINJIRA™ — V88 : garder le passage lu en activant la lecture plein écran

**Date : 14 novembre 2026. PR #1000 uniquement, DRAFT, sans déploiement.**

## Anomalie corrigée

Le mode « Lecture plein écran » modifie la classe `reader-focus-mode` et, par conséquent, la hauteur utile de la fenêtre du roman. Contrairement à une rotation, ce changement n'émet pas nécessairement d'événement `window.resize`. La liseuse paginée pouvait donc afficher un autre passage après l'entrée ou la sortie du mode de concentration, particulièrement avec des caractères agrandis.

## Modification V88

1. `assets/js/sinjira-liseuse-companion-v28.mjs` : notifier avant le changement de classe CSS par un événement de présentation local `sinjira:reader-layout-will-change`. Ni contenu ni position de lecture ne sortent de l'appareil.
2. `assets/js/sinjira-liseuse-reflow-v53.mjs` : capturer l'ancre de caractère et la proportion du texte dans **l'ancienne** géométrie; restituer après mise en page, avec les protections existantes de restitution obsolète, et libérer le listener à la fermeture.
3. `tests/e2e/test_sinjira_liseuse_responsive_v58.py` : sur la vraie page HTML à 320×568 et caractère agrandi, capturer une ancre effectivement lue, entrer en mode plein écran, vérifier qu'elle reste à moins de 35 px de la même position relative, en sortir et recommencer dans l'autre sens. Le test utilise un PDF fictif et interdit le réseau privé/Supabase.

## Critères de sortie

- CI spécifique du SHA V88 : `SINJIRA V69` et `SINJIRA V64` dans les moteurs Chromium et WebKit, sans exception ni dégradation des gestes gauche/droite.
- Vérifier sur iPhone/Android physiques les hauteurs dynamiques, les encoches, les barres système, les rotations et les annonces VoiceOver/TalkBack.
- Conserver le chantier de synchronisation sécurisée V51/V59, les contrôles d'accès au livre intégral et les **13 portes de lancement** ouverts.

**Décision : candidat technique, NO-GO production avant recettes matérielles, sécurité des comptes et approbation.** Aucun changement de Supabase, Auth, RLS, SQL, livre privé ou publication. Les taux de référence du 8 novembre sont inchangés : Nova 47 %, Nova–Sinjira sans pourcentage global, sondage 54,5 %, boussole 75 %, SINJIRA 66,5 % ±10 points.
