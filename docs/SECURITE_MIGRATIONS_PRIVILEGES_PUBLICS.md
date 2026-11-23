# Sécurité Supabase — garde des nouvelles migrations SQL publiques

**Candidat GitHub, non fusionné et non déployé.** Cette intervention protège le
processus de création des prochains objets. Elle ne révoque aucun privilège
existant et ne change aucune table, RPC ni session de production.

## Constat du 21 novembre 2026 : lecture seule du catalogue réel

- Schéma `public` : **136 tables, 136 avec RLS activée**, aucune table
  sans RLS dans ce relevé ; zéro vue publique dénombrée.
- Les privilèges par défaut `pg_default_acl` du schéma `public`, pour les
  créateurs `postgres` et `supabase_admin`, attribuent encore
  automatiquement des droits à **anon** et **authenticated** :
  - futures tables : SELECT, INSERT, UPDATE, DELETE et selon le propriétaire
    TRUNCATE, REFERENCES, TRIGGER, MAINTAIN ;
  - futures fonctions : EXECUTE ;
  - futures séquences : USAGE, SELECT, UPDATE.
- Le Security Advisor affiche **56 informations**
  `rls_enabled_no_policy` : l'absence de politique RLS constitue
  souvent un refus par défaut, pas une preuve de divulgation.
- L'avertissement Auth `auth_leaked_password_protection` reste présent,
  traité séparément dans [#437](https://github.com/M0rdr3x/BenoitCantin/issues/437).

**Portée :** des droits automatiques sur les *objets futurs*, pas une preuve
d'exploitation ni de fuite sur une table existante. Les futurs droits
de séquences et les fonctions sont indépendants de la RLS des tables.

## Nouvelle barrière GitHub Actions

Le script `scripts/validate_new_supabase_api_privileges.py` inspecte les
nouvelles migrations SQL ajoutées ou modifiées par rapport au commit de base.

| Objet créé dans `public` | Contrat requis dans la même migration |
|---|---|
| TABLE, y compris CREATE TABLE AS SELECT | `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` et `REVOKE ALL ON TABLE ... FROM PUBLIC, anon, authenticated` |
| FUNCTION | `REVOKE ALL ON FUNCTION ... FROM PUBLIC, anon, authenticated` |
| SEQUENCE | `REVOKE ALL ON SEQUENCE ... FROM PUBLIC, anon, authenticated` |
| VIEW | `WITH (security_invoker=true)` et `REVOKE ALL ON TABLE ... FROM PUBLIC, anon, authenticated` |
| MATERIALIZED VIEW publique | Refus par défaut : pas de RLS et revue SQL spéciale requise |

Les déclarations sans schéma explicite sont refusées pour ces créations.
Des GRANT explicites supplémentaires ne doivent être ajoutés **qu'après
revue de la justification métier et des politiques RLS**.

Le workflow `.github/workflows/sinjira-future-sql-api-privileges-security.yml`
lance des tests négatifs (syntaxe, vues invoker, tables AS, séquences,
fonction mal protégée, absence de rôle dans REVOKE, SQL commentaire)
et inspecte uniquement les fichiers de migration modifiés. Il est en
lecture seule, épingle ses actions sur des commits et ne reçoit pas de
secret Supabase. Les migrations historiques ne sont pas réécrites.

Ce garde n'est **pas un parseur PostgreSQL complet** : il ne détecte
pas toutes les créations via SQL dynamique, les renommages ou
les privilèges implicites hérités de rôles. Une revue de migration,
un test pgTAP/SQL sur base isolée et une vérification du catalogue
après déploiement sont indispensables.

## Correction structurelle future des privilèges par défaut (#828)

Une migration SQL séparée, **préparée et relue dans un environnement
isolé**, devra ajuster les `ALTER DEFAULT PRIVILEGES FOR ROLE ...`
pour les deux rôles créateurs concernés. Les droits par défaut
`PUBLIC` sur les nouvelles fonctions peuvent aussi provenir du
**niveau global** PostgreSQL : un simple `REVOKE` dans un schéma ne
garantit pas de neutraliser ces droits globaux.

Ne pas modifier directement le catalogue hébergé sans inventaire
des fonctions et GRANT attendus. Tester avec les rôles créateurs
la création réelle d'une table, d'une séquence, d'une fonction et
d'une vue ; vérifier les droits `anon`, `authenticated` et `service_role`,
puis exécuter des tests HTTP PostgREST de refus et des parcours légitimes.

**Portes de production :**
1. Réconcilier les migrations en attente (#438) et la revue des RPC (#701).
2. Revue de sécurité indépendante et tests staging incluant les usages
   normaux, opérations admin et éventuelles dépendances des RLS.
3. Activer un ruleset sur `main` pour rendre les tests obligatoires (#135).
4. Déployer seulement avec approbation, sauvegarde, plan de retour
   arrière et vérification du catalogue production.

Références :
- https://supabase.com/docs/guides/api/securing-your-api
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://www.postgresql.org/docs/current/sql-alterdefaultprivileges.html
- https://github.com/M0rdr3x/BenoitCantin/issues/828
- https://github.com/M0rdr3x/BenoitCantin/pull/844

**Aucune dépense, migration, DDL, modification d'Auth ou publication effectuée.**
