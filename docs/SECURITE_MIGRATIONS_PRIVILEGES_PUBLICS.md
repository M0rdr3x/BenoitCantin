# Sécurité Supabase — privilèges futurs et migrations de l'API

## Observations réelles (lecture seule, 8 novembre 2026)

Le catalogue `pg_default_acl` du projet Supabase actif associe
encore des privilèges automatiques sur les futures **tables, fonctions
et séquences** du schéma `public`, créées notamment par `postgres`
ou `supabase_admin`, aux rôles `anon` et `authenticated`.

Vérification séparée du catalogue au moment de l'audit :
**135 tables publiques, aucune sans RLS**, aucune table du schéma privé
sans RLS et aucune vue publique dépourvue de
`security_invoker=true`. Les alertes `rls_enabled_no_policy`
sont des informations : une absence de politique peut exprimer une
stratégie légitime **deny by default**.

Les privilèges PostgreSQL et les politiques RLS constituent deux
barrières **indépendantes**. Un nouvel objet créé sans politique de
sécurité explicite peut élargir inutilement l'API, même si les tables
déjà déployées sont protégées.

Source : https://supabase.com/docs/guides/api/securing-your-api

## Garde préventif de migrations

`scripts/validate_new_supabase_api_privileges.py` vérifie les migrations
SQL **ajoutées ou modifiées** entre la base d'une PR et son SHA de tête,
ou entre les deux commits d'un push sur `main`.

- Toute nouvelle instruction `CREATE TABLE public.nom` doit être
  accompagnée, **dans le même fichier**, de
  `ALTER TABLE public.nom ENABLE ROW LEVEL SECURITY` et d'un
  `REVOKE ALL ... FROM PUBLIC, anon, authenticated`.
- Toute nouvelle instruction `CREATE FUNCTION public.nom(...)`
  doit comporter un `REVOKE ALL ON FUNCTION ... FROM PUBLIC, anon,
  authenticated`. Le service_role n'est pas révoqué globalement.
  Les fonctions autorisées à des clients doivent ensuite recevoir
  un `GRANT EXECUTE` explicite **après revue**.
- Les créations sans schéma explicite sont refusées. Les tests de
  mutation couvrent plusieurs omissions et privilèges incorrects.
- Le workflow GitHub Actions travaille sur l'historique de la PR
  uniquement : **aucun secret, accès réseau au projet ou changement de
  base n'est nécessaire**.
- Les anciennes migrations restent inchangées. Leur immutabilité
  est contrôlée par le garde historique du dépôt.

Ce contrôle est un filet préventif, **pas un analyseur SQL complet**.
Il ne détecte pas forcément les `CREATE` en SQL dynamique, les objets
renommés, les chemins de création indirects, ni la justesse d'une
politique RLS. Les vues, séquences, procédures et schémas internes
requièrent leurs contrôles propres.

## Limites opérationnelles et correction définitive

Ce garde ne modifie **pas** les privilèges par défaut déjà enregistrés
dans la base de production. La correction de fond reste dans
[l'issue #828](https://github.com/M0rdr3x/BenoitCantin/issues/828) :
préparer des `ALTER DEFAULT PRIVILEGES` par rôle créateur, et tester
en staging la création d'une table, d'une fonction et d'une séquence
sous chacun des propriétaires concernés.

La réussite GitHub Actions **ne bloque une mise en production que
si un ruleset actif impose les validations nécessaires**. La
protection effective de `main` doit être vérifiée par le propriétaire,
voir [l'issue #135](https://github.com/M0rdr3x/BenoitCantin/issues/135).

Aucune migration SQL, fonction ou privilège de la production n'a été
modifié lors de l'ajout du garde.
