# SINJIRA — V49 : sauvegarde hors ordre sur deux appareils du même compte

**Date : 9 novembre 2026 · Analyse de risque technique, pas déploiement et pas homologation.**

## Résultat recherché

Les contrôles V47 et V48 du lecteur existent déjà sur `main`. V47 a révélé sur les **catalogues réels** : **7 PASS, 2 BLOCK, 1 REVIEW et NO_GO**. La colonne `scroll_ratio` et sa contrainte V32 manquent encore sur la base consultée au 9 novembre. V48 a appliqué la migration V32 originale **uniquement à une base PostgreSQL jetable**, puis vérifié la RLS, le ratio 0..1 et la séparation entre les **comptes fictifs A et B**. Ces essais sont utiles, mais **ils ne constituent pas un essai de deux appareils portant le même compte** et ne démontrent pas l'absence de conflits d'écriture.

La V49 ajoute le scénario manquant : **un même compte fictif** réalise deux lectures, depuis deux appareils indépendants; une requête ancienne arrive **après** la requête la plus récente.

## Pourquoi cette vérification est nécessaire

Le client de la liseuse `assets/js/sinjira-liseuse-v26.js` utilise `.upsert(payload,{onConflict:'user_id,novel_id'})` et transmet `updated_at` dans la charge utile. Cette opération peut remplacer la ligne existante **sans condition atomique sur la version ou l'horodatage déjà enregistré**. Le chemin de **rejeu après coupure** `retryCloudProgress()` vérifie bien le `updated_at` avant une réémission, mais cette protection ne couvre pas toutes les écritures normales `syncProgress()` envoyées presque simultanément par deux appareils d'un même compte.

La **mise à jour tardive** d'une requête plus ancienne peut ainsi écraser le dernier marque-page. Ce n'est **pas** la preuve qu'une perte de lecture s'est produite sur une vraie session en production; c'est une **classe de risque reproduite en laboratoire** à laquelle la logique actuelle paraît exposée, et qui bloque toute affirmation de cohérence multi-appareils.

## Procédure reproductible, sans accès aux utilisateurs

La CI `.github/workflows/sinjira-reader-v49-same-account-race.yml` se limite à un PostgreSQL 17.6 éphémère sur `127.0.0.1`, sans secret distant. Elle réutilise `tests/security/sql/setup_sinjira_reader_v48.sql` qui importe **la vraie migration V32 du dépôt** dans une base fictive, protégée par une politique RLS de propriétaire. Trois fichiers de test utilisent le **même UUID fictif** et des sessions `psql` distinctes.

| Étape | Requête / identité fictive | Résultat attendu dans le laboratoire |
| --- | --- | --- |
| Préparation A | Compte fictif propriétaire, page historique 4, ratio `NULL` | La sauvegarde A de 13 h est préparée, mais pas encore reçue par la base |
| Appareil B (récent) | Même propriétaire, page **31**, ratio **0.8123**, demande horodatée **13 h 05** | La position plus récente est persistée |
| Appareil A (en retard) | Même propriétaire, page **12**, ratio **0.2100**, demande horodatée **13 h 00**, arrivée APRÈS B | La logique `UPSERT` sans précondition remplace B par A : **risque reproduit** |
| Conclusion | Constat documentaire | **NO_GO**, problème non résolu et pas de date de fin attestée |

**Sémantique capitale des tests :** une CI verte signifie **« la reproduction de la défaillance attendue a réussi »**, **PAS** « la défaillance a été corrigée ». Le workflow se termine par `V49 NO_GO` précisément pour éviter cette confusion. Un correctif futur doit ajouter des **tests qui exigent l'absence d'écrasement** et réexaminer la pertinence de cette reproduction historique.

## Correction à concevoir et faire approuver

Une correction réellement sûre ne doit pas se limiter à une comparaison côté navigateur : deux appareils peuvent lire simultanément le même état et écrire ensuite dans un ordre différent. Le mécanisme envisagé doit garantir une **condition atomique du côté serveur**, évaluée dans la même transaction que la modification :

1. Introduire, après revue DBA, une **révision monotone ou une comparaison atomique explicite de version** par couple `user_id,novel_id`, sans faire reposer l'ordre des écritures sur l'horloge réglable de l'appareil.
2. Si une sauvegarde est rejetée comme périmée, **ne pas supprimer silencieusement la position locale**; informer le lecteur, récupérer la position autorisée du compte et prévoir une résolution compréhensible des conflits.
3. Vérifier la RLS du propriétaire et les exigences de `SELECT`, `INSERT`, `UPDATE`, ainsi que l'absence de contournement `service_role` depuis le navigateur. Aucune fonction `SECURITY DEFINER` ne doit être ajoutée pour contourner un problème de permission sans une revue approfondie.
4. Tester deux demandes avec la **même identité** en ordre inversé, sur une base fidèle, puis deux appareils/navigateurs réellement distincts avec un compte **consentant de test**; inclure déconnexion, session expirée, perte réseau et retraits de droits.
5. Appliquer V32 **uniquement après approbation explicite et runbook protégé**, puis recontrôler V47. Ni cette PR ni la CI V49 n'appliquent de DDL à la production.

## Interdictions et indicateurs

- **Aucune migration**, aucun `POST` de lecture vers Supabase, aucune consultation de compte, de PDF ou de roman intégral, aucune remise en route automatique du lecteur.
- **Pas de hausse de maturité globale** : SINJIRA complet reste **66,5 % (≈67 %), incertitude ±10 points**, **13/13 portes de lancement ouvertes** dans le relevé du 8 novembre.
- **Pas de promotion de `reader_v32_prod`, `reader_two_devices` ou `private_book_access`** tant que V32 n'est pas effectivement déployée de manière autorisée et que les scénarios multi-appareils/droits réels ne sont pas attestés.
- La cible de décembre 2027 concerne uniquement la planification du **Projet Nova politique**, pas SINJIRA.

**Sources du dépôt :** migration V32 `supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql`, tests RLS V48, prévol catalogue V47, code réel `assets/js/sinjira-liseuse-v26.js`, suivi [#826](https://github.com/M0rdr3x/BenoitCantin/issues/826). Le travail de cette V49 ne modifie aucun de ces fichiers sources.
