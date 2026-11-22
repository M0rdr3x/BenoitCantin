# Sécurité SINJIRA — fonctions privées SECURITY DEFINER et identités de tiers

**Statut : candidat en revue, jamais une migration de production.**
Référence : [issue #701](https://github.com/M0rdr3x/BenoitCantin/issues/701).

## Constat du 21 novembre 2026 (catalogue Supabase, lecture seule)

Les fonctions de schéma `private` suivantes sont `SECURITY DEFINER`
(propriétaire : `postgres`) et possèdent `EXECUTE` pour
`anon` et `authenticated`. Les deux rôles ont `USAGE` sur `private` :

| Fonction | Empreinte SHA-256 de `btrim(pg_get_functiondef)` |
|---|---|
| `private.is_sinjira_admin(uuid)` | `5e3df1425976db0252e8c3b544929f60038d02581f4226d684819c7c4a347c06` |
| `private.project_access_rank(uuid,uuid)` | `efc5da4d75817740e4e3ab12d84124fd4638c32d0d4df75b8496d07bfa08d4a3` |

La première effectue une lecture privilégiée de `internal_admin_users` à
partir d'un identifiant libre. La seconde retourne le rang d'accès d'un
`p_user_id` fourni et appelle la première. Si l'API expose une voie
permettant l'invocation, cela peut constituer une **sonde de droits d'un
tiers** : le test de permissions SQL seul ne prouve pas qu'un appel est
exploitable depuis le navigateur. Vérifier les schémas réellement exposés
et les wrappers PostgREST avant toute conclusion d'exploitabilité.

**Dépendances RLS identifiées :** `documents_anon_read`,
`documents_authenticated_read`, `playtests_read_authorized`,
`projects_authenticated_read` et
`playtest_participants_apply` appellent `project_access_rank`.
La fonction privée conserve donc son retour `1` pour
un visiteur anonyme sur projet public et le contrat `10/20/30/100`
pour les droits authentifiés habituels.

## Candidat sécurisé (NON déployé)

Fichier `security/candidates/sinjira_private_definer_identity_staging.sql` :

- **Admin :** la fonction ne peut révéler l'appartenance administrateur
  qu'au même `auth.uid()`, sauf lorsque le JWT validé par Supabase
  porte réellement `role=service_role`. L'égalité
  `IS NOT DISTINCT FROM` empêche qu'une identité de JWT absente
  renvoie `NULL` pour un administrateur réel et `false` pour un autre
  compte (oracle d'appartenance); valeur nulle = faux.
- **Rang projet :** si `p_user_id` diffère de `auth.uid()` et le
  demandeur ne détient pas un JWT `service_role`, retourne `0`
  avant les requêtes sur `project_access` ou `internal_admin_users`.
  L'anonyme avec `p_user_id NULL` conserve les projets publics.
- Signatures, `STABLE SECURITY DEFINER`, rangs historiques et noms de
  tables sont conservés ; `search_path` restreint à `pg_catalog`,
  tous les schémas applicatifs et d'authentification qualifiés.
- **Aucun changement de GRANT/REVOKE :** les autres fonctions, triggers,
  politiques RLS et éventuels services backend peuvent dépendre des
  droits actuels. Préparer séparément la réduction des `EXECUTE`
  directs sur `private.is_sinjira_admin` après inventaire complet.
- Fichier toujours **`BEGIN; ... ROLLBACK;`**. Ne pas l'exécuter
  en production ou le déplacer dans `supabase/migrations/`.

## Preuves nécessaires

`scripts/validate_private_definer_identity_candidate.py` refuse les
modifications non autorisées du contrat et teste seize mutations négatives
(identité, service_role, rangs, règles de projet, recherche SQL, transaction).

Le workflow `sinjira-private-definer-identity-security.yml` construit
une base Supabase **locale** et injecte des utilisateurs fictifs via une
transaction annulée : **22 assertions pgTAP** avec les rôles `anon`,
`authenticated` et `service_role`, sur des projets publics,
restreints et accessibles aux comptes. La réussite locale ne prouve
pas la compatibilité de tous les chemins en production.

### Portes de promotion et vérification après

1. Vérifier les empreintes exactes des deux fonctions en production
   et l'absence de dérive depuis cet audit. Si dérive, **arrêter**.
2. Vérifier l'exposition Data API effective de `private`, les wrappers,
   les usages dans les fonctions/Edge et les politiques RLS.
3. Exécuter les tests pgTAP et des essais HTTP sur **staging hébergé**,
   avec des JWT réels de deux comptes fictifs, un admin, et un compte
   propriétaire. Tester les autres services utilisant `service_role`.
4. Réconcilier les migrations Supabase existantes (issue #438), préparer
   une migration canonique nouvelle, la faire revoir indépendamment
   et garder un plan de retour arrière.
5. Après approbation humaine et déploiement contrôlé, valider les
   fonctions actives, les permissions, les accès RLS et les requêtes
   de consultation d'un tiers **refusées**. Vérifier ensuite la
   suppression justifiée des `EXECUTE` inutiles du schéma privé.

**Autres risques indépendants :** protection GitHub `main` #135,
publication GitHub Pages #450, documents privés #1108, sessions
révoquées côté serveur #725. Le correctif du navigateur ne suffit
jamais à remplacer l'autorisation côté serveur.

Documentation : https://supabase.com/docs/guides/api/securing-your-api

**Aucune session ni donnée utilisateur réelle n'a été lue ; aucun
DDL, migration, GRANT, secret ou déploiement Supabase réalisé.**
