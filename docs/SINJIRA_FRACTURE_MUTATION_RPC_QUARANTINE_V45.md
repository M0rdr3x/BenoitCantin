# SINJIRA — Fracture V45 : mise en quarantaine des RPC d'action historiques

**Statut : PROPOSITION NON APPLIQUÉE — NO_GO production.** Travaux liés : [#872](https://github.com/M0rdr3x/BenoitCantin/issues/872), [#857](https://github.com/M0rdr3x/BenoitCantin/issues/857) et [#826](https://github.com/M0rdr3x/BenoitCantin/issues/826).

## Pourquoi le NO_GO du navigateur ne suffit pas

L'audit **en lecture seule des métadonnées PostgreSQL de SINJIRA**, réalisé le 8 novembre 2026, confirme que le rôle `authenticated` possède encore `EXECUTE` sur les cinq actions de partie historiques `fracture_engine_start`, `fracture_engine_pick`, `fracture_engine_submit_keep`, `fracture_engine_submit_report` et `fracture_engine_submit_accusation`, **dans les schémas `public` et `sinjira_fracture_internal`**. `anon` n'a pas cet accès. Les versions internes sont `SECURITY DEFINER`.

Le lobby Web demeure suspendu, mais une page inactive **n'est pas une barrière d'autorisation serveur**. Les fonctions contiennent par ailleurs plusieurs vérifications de membre, de tour et de phase : leur présence **ne prouve pas qu'une personne puisse les exploiter**, mais n'annule pas le risque d'exposer le moteur historique qui n'est pas réconcilié avec l'édition officielle.

Pour les bonnes pratiques de privilèges RPC et `SECURITY DEFINER`, voir la [documentation Supabase : Securing your API](https://supabase.com/docs/guides/api/securing-your-api) et l'[avis sur les fonctions privilégiées exécutables par un utilisateur connecté](https://supabase.com/docs/guides/observability/advisors?queryGroups=lint&lint=0029_authenticated_security_definer_function_executable).

## Contenu limité du candidat V45

Le script **`scripts/proposals/sinjira_fracture_v45_mutation_rpc_quarantine_candidate.sql`** propose de révoquer `EXECUTE` à `PUBLIC`, `anon` et `authenticated` **uniquement pour les dix signatures précises** (cinq actions, deux schémas) et de préserver explicitement l'accès technique `service_role`.

Il ne touche **pas** aux fonctions de lecture `fracture_engine_get_state` / `fracture_engine_get_state_safe`, aux fonctions `fracture_engine_health` et `fracture_engine_privacy_health`, aux documents de jeu ni aux tables, données, identités, politiques RLS ou scores. Il est enregistré **hors du répertoire de migrations** pour empêcher un déploiement implicite.

Ce confinement n'empêche pas des opérations réalisées par un rôle privilégié, des anciennes transactions déjà ouvertes ou des interfaces alternatives. Il s'agit d'une frontière de permission supplémentaire, **et non d'une preuve de sécurité complète**.

## Test en base éphémère, sans utilisateur réel

`tests/security/sql/test_fracture_rpc_quarantine_v45.sql` crée des fonctions purement fictives de même signature dans PostgreSQL 17.6 éphémère, puis vérifie :

- les 10 permissions présentes pour `authenticated` **avant** l'application du candidat;
- les 10 permissions **retirées** pour `authenticated` et `anon` après l'application;
- l'exécution maintenue pour `service_role` (maintenance autorisée);
- les fonctions de consultation et de santé **inchangées**;
- des appels directs de test qui doivent échouer avec `insufficient_privilege`.

La suite Python exige exactement les dix signatures prévues, interdit l'ajout de commandes de modification de données ou de schéma et garantit l'absence de secrets et de migration implicite. La CI ne reçoit aucun accès aux environnements distants.

## Effets à examiner AVANT toute migration réelle

1. **Compatibilité** : confirmer qu'aucune partie réellement en cours ou aucun service autorisé n'a besoin de ces RPC durant la quarantaine; sinon, planifier une interruption contrôlée et informer les utilisateurs. Conserver les fonctionnalités de documents privés et de comptes.
2. **Accès par rôles** : mesurer les permissions exactes, le chemin indirect via les wrappers, la portée du schéma Data API et les dépendances `SECURITY DEFINER` sur une copie isolée.
3. **Opérations** : préparer un plan réversible avec les privilèges préalables enregistrés, vérifier la conservation de `service_role`, l'impact sur les connexions existantes, les conséquences pour l'observabilité et le retrait ultérieur de la quarantaine.
4. **Migration de production** : seulement après revue, approbation explicite, création d'une migration versionnée par la procédure Supabase prescrite, prévol en lecture seule et tests multi-comptes; ne jamais appliquer le fichier de proposition directement sur la base liée.
5. **Réouverture** : même après quarantaine, ne pas lever le NO_GO multijoueur avant l'alignement réel du moteur sur V36–V43, l'arbitrage #857, la revue de révocation des sessions et la recette multi-comptes de #872.

**Important :** la fusion éventuelle de cette proposition dans GitHub ne change pas les droits de production. La maturité globale SINJIRA reste à **66,5 % ≈ 67 %**, avec incertitude d'environ ±10 points, tant que le serveur n'est pas réellement remédié et testé.
