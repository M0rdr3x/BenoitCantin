# SINJIRA — confinement de l'identité dans les aides RLS privées

**Candidat de revue, non déployable.** Fichier associé :
`private_admin_project_access_identity.sql`. La transaction se termine
obligatoirement par `ROLLBACK` ; elle ne fait partie ni des migrations
canoniques ni d'un workflow Supabase de production.

## Observation réelle (catalogue PostgreSQL en lecture seule, 8 novembre 2026)

Les fonctions `private.is_sinjira_admin(uuid)` et
`private.project_access_rank(uuid,uuid)` sont `SECURITY DEFINER`,
appartiennent à `postgres` et sont exécutables par les rôles `anon`
et `authenticated` qui disposent également d'`USAGE` sur `private`.
Elles acceptent actuellement un `p_user_id` arbitraire. Leur paramètre
a `DEFAULT auth.uid()`, ce qui **n'empêche pas un appelant d'envoyer un
autre UUID explicitement**.

Ces aides sont utilisées par les règles RLS de `documents`, `projects`
et `playtests`. Les politiques examinées utilisent déjà
`auth.uid()` et la politique documentaire anonyme exige
`private.project_access_rank(project_id, NULL::uuid)`.
Ne **jamais** supprimer ces grants ni interdire l'identité nulle sans
revue, au risque de bloquer la lecture légitime de documents publics.

Le simple fait que des rôles SQL puissent exécuter une fonction dans
un schéma privé **ne prouve pas qu'il est exposé à PostgREST**.
Aucune exploitation HTTP, fuite de données ni usurpation n'a été constatée.

## Logique candidate

- `private.is_sinjira_admin` retourne `false` pour un UUID tiers,
  sauf appel authentifié avec rôle `service_role` dans le JWT validé.
- `private.project_access_rank` retourne `0` pour un UUID tiers,
  sauf `service_role`. L'identité `NULL` reste permise pour une
  requête anonyme et donne uniquement le rang prévu par la visibilité
  publique.
- Les signatures, les valeurs par défaut, les privilèges en place et
  les niveaux 100/30/20/10/1 sont conservés.
- Le `search_path` de chaque fonction est vide et les références
  de tables/fonctions sont entièrement qualifiées.
- Les exceptions privilégiées reposent sur le rôle d'un JWT serveur,
  **jamais sur un paramètre de rôle envoyé par le client**.

## Tests requis sur une base de staging **isolée**

Créer des utilisateurs et projets **fictifs** (propriétaire, second
utilisateur, admin, visiteur anonyme) dans un environnement local,
et vérifier séparément :

1. Un `authenticated` légitime obtient son propre rang projet ;
   un UUID d'un autre compte retourne `0`.
2. Le contrôle administrateur ne révèle pas le rôle d'un tiers :
   `false` pour un UUID différent et `true` seulement pour l'admin
   lui-même avec son propre JWT.
3. La politique `documents_anon_read` continue d'autoriser les
   documents publics approuvés sans session, mais pas les documents
   privés, et renvoie `0` ou `1` selon la visibilité.
4. Les politiques `documents_authenticated_read`,
   `projects_authenticated_read` et `playtests_read_authorized`
   continuent de permettre exactement les ressources de l'utilisateur
   fictif, jamais celles d'un second utilisateur.
5. Un vrai contexte `service_role` authentifié peut réaliser les
   opérations serveur légitimes pour un autre utilisateur ; un
   client normal qui passe `p_user_id` ne bénéficie pas de cette
   exception.
6. Vérifier l'absence de régression sur les fonctions qui utilisent
   ces helpers indirectement et sur l'historique de migrations.
7. Réexécuter les advisors et vérifier les GRANT au niveau catalogue ;
   les privilèges des fonctions restent identiques.

Le garde Python associé ne teste que la **structure SQL** et six
mutations artificielles. Il ne prouve aucune des assertions
d'intégration précédentes.

## Conditions avant tout déploiement

Un responsable doit confirmer les appels indirects sous contexte
`service_role`, approuver les essais RLS, créer ensuite une **nouvelle
migration canonique** avec le mécanisme du dépôt, résoudre l'écart de
registre des migrations (#438), obtenir la revue de sécurité, préparer
la restauration et appliquer individuellement. Ne pas exécuter ce
candidat sur la production (même s'il contient `ROLLBACK`, il ferait
des changements transitoires en cours de transaction).

Aucun `GRANT`, `REVOKE`, changement d'utilisateur, lecture de données
personnelles ou exécution SQL modificatrice n'a été effectué en
production lors de cette préparation.

Suivi : #722. Documentation : https://supabase.com/docs/guides/database/functions
