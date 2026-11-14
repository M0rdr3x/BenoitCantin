# SINJIRA™ — V80 : essai natif Chromium des glissements lents sur la vraie liseuse

**14 novembre 2026** — [PR unique de la liseuse mobile #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), **DRAFT et non fusionnée**.

## Risque réduit

La V79 ouvre la navigation tactile aux gestes plus lents, pour améliorer l'accessibilité des lecteurs à mobilité réduite. Les tests de classificateur Node ne prouvent pas à eux seuls que le navigateur délivre un geste de 1,2–1,55 seconde de manière exploitable : un moteur peut aussi déclencher de la sélection native, des gestes de défilement ou perdre `touchend`.

## Recette V80 (véritables événements tactiles moteur, téléphone simulé)

Le scénario préexistant `tests/e2e/test_sinjira_liseuse_native_touch_v65.py` utilise `Input.dispatchTouchEvent` via le protocole Chromium, dont les événements vérifiés possèdent `isTrusted=true` dans la page. V80 ajoute un paramètre de **durée écoulée réelle** lors des étapes `touchMove`, et contrôle :

1. **Texte paginé, 390 px** : glisser à gauche pendant 1 200 ms avance un écran sans changer de page source; glisser à droite pendant 1 500 ms revient au premier écran.
2. **Affichage PDF, 320 px** : depuis la page fictive 4, glisser à droite pendant 1 250 ms revient à la page 3, puis glisser à gauche pendant 1 550 ms avance à nouveau à la page 4, sans double saut.
3. **Refus de geste très long** : un mouvement horizontal de 1 900 ms en mode PDF ne doit pas changer de page.
4. Les parcours rapides, gestes verticaux, adaptation aux 320 px, absence d'accès Supabase et `isTrusted` restent dans le même scénario.

Le workflow V65 exécute ce scénario sous Chromium dans un environnement mobile simulé (PDF **entièrement fictif**, comptes et services privés bloqués). Son titre de phase Node est corrigé pour ne plus prétendre que la suite contient seulement « 68 tests » alors que la suite est plus vaste.

**Important :** un navigateur Chromium automatisé, même avec `isTrusted=true`, ne remplace **pas** une réception sur téléphone physique ni un test de VoiceOver ou TalkBack.

## Critères de publication toujours bloquants

Tester physiquement Safari iPhone et Chrome Android avec les gestes lents, la rotation, la sélection, le zoom, les zones défilantes et la progression de lecture; obtenir la revue indépendante des droits sur les romans privés et la synchronisation entre appareils avant toute fusion/déploiement.

**Statut : PR DRAFT / NO-GO.** Estimation du programme SINJIRA complet : **66,5 % ±10 points**, inchangée; 13 portes de lancement non closes.
