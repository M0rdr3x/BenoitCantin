# SINJIRA — Fracture V46 : prévol de lancement SQL en lecture seule

**Date d'observation : 8 novembre 2026 · Statut réel : NO_GO.**  
Suivi des correctifs candidats [V42 (PR #877)](https://github.com/M0rdr3x/BenoitCantin/pull/877) et [V45 (PR #885)](https://github.com/M0rdr3x/BenoitCantin/pull/885), des bloqueurs [#872](https://github.com/M0rdr3x/BenoitCantin/issues/872) et [#857](https://github.com/M0rdr3x/BenoitCantin/issues/857).

## Objectif du prévol

Le fichier `scripts/audits/sinjira_fracture_v46_release_preflight_readonly.sql` est un **unique SELECT de catalogues PostgreSQL**, sans mutation ni connexion utilisateur. Il vérifie que les préconditions de sécurité **mesurables au niveau métadonnées** nécessaires à V42/V45 sont remplies.

La requête inspecte uniquement : `pg_proc`, `pg_namespace`, `pg_policies`, `pg_class` et les privilèges déclarés sur les routines. Elle n'accède à **aucune ligne de partie, de document, de compte ou de vote**. Elle n'a **pas** été placée dans `supabase/migrations/` et ne sera **jamais** lancée sur la base distante par GitHub Actions.

## Résultat sur la base SINJIRA au 8 novembre 2026

Le prévol a été exécuté effectivement sur **les métadonnées de production**, en lecture seule.

| Contrôle | Résultat | Interprétation |
|---|---|---|
| Inventaire des 10 signatures de mutation | PASS | Signatures présentes |
| Pas de surcharge de mutation non couverte | PASS | Aucune surcharge additionnelle détectée |
| Mutations refusées à `anon` | PASS | Rôle anonyme déjà exclu |
| Mutations refusées à `authenticated` | **BLOCK** | Les 10 mutations sont encore exécutables par des comptes connectés |
| Accès de maintenance `service_role` préservé | PASS | Privilèges actuellement présents |
| RLS des deux tables de documents | PASS | RLS activée sur les deux tables |
| `WITH CHECK` des rapports vers la partie cible | **BLOCK** | Politique actuelle sans contrainte de propriété de la partie cible |
| `WITH CHECK` des documents vers la partie cible | **BLOCK** | Politique actuelle sans contrainte de membre sur la partie cible |
| **Décision globale** | **NO_GO** | Trois blocages réels de préconditions; aucune autorisation automatique de déploiement |

**Bilan : 5 PASS, 3 BLOCK, décision NO_GO.**

Le contrôle de `WITH CHECK` est une **heuristique de catalogue** qui vérifie la présence de garde-fous nommés, mais ne prouve pas que les prédicats SQL, jointures et fonctions `SECURITY DEFINER` sont sémantiquement corrects. Les tests multi-comptes demeurent obligatoires, même si toutes les lignes passent à PASS. Lorsque aucun blocage de catalogue n'est présent, le résultat final ne devient **pas** GO, mais **REVIEW_REQUIRED**.

## Sécurité des validations

Le test `tests/security/test_fracture_release_preflight_v46.py` :

- refuse les commandes DDL, DML, `GRANT`, `REVOKE` et `EXECUTE` ;
- vérifie que la requête ne lit que les catalogues autorisés;
- compare exactement **les dix signatures** avec le fichier candidat V45;
- vérifie les noms des deux politiques **effectivement visées** par V42;
- impose les neuf contrôles et l'absence de feu vert automatique;
- interdit les identifiants du projet Supabase et toute connexion distante en CI.

Le workflow se contente de tester le SQL et ses contrats statiques, avec un jeton GitHub en lecture seule. Les validations réelles des politiques restent les recettes isolées livrées avec V42/V45.

## Plan de remédiation et conditions de sortie

1. **Garder le lobby Fracture Web suspendu**. Le garde V44 est déjà intégré et empêche sa réouverture accidentelle par changement de page.
2. Faire revoir les propositions V42/V45 avec les consommateurs actuels, les droits antérieurs, la non-perte des parties en cours et les opérations de maintenance. **Ne pas déployer ce SQL de prévol comme migration**.
3. Créer les migrations versionnées au moyen de la procédure Supabase prescrite, appliquer selon une **approbation de production spécifique**, puis re-exécuter le prévol en lecture seule.
4. Terminer l'intégration des règles V36–V43 côté serveur, arbitrer la formule du score final #857, valider la protection des sessions révoquées, la cohérence des tours et les transactions atomiques.
5. Mener une recette **multi-comptes sur une base isolée fidèle**, comprenant non-membres, mains et identités privées, soupçons, doubles votes, reprise de partie et charges concurrentes. Prévoir monitoring et retour arrière avant une réouverture contrôlée.

**Le prévol n'autorise jamais à lui seul la publication.** La maturité globale SINJIRA reste estimée à **66,5 % ≈ 67 %** (incertitude ±10 points), car la remédiation de production n'est pas encore appliquée et validée.
