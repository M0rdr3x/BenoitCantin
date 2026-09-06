# SINJIRA V25 — État de sécurité Auth hébergée

Dernière vérification : 2026-09-06.

## État réel observé

- Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`).
- Organisation : `glaxqwyumblfqmzusqbt`.
- Plan observé le 2026-09-06 : **Free**.
- Security Advisor : `auth_leaked_password_protection` est encore présent au niveau **WARN**.
- La protection contre les mots de passe compromis n'est donc **pas activée** en production à cette date.
- La politique locale/reconstruction SINJIRA conserve une longueur minimale de **12 caractères** dans `supabase/config.toml`.

Cette page est un état daté, pas une hypothèse permanente sur le plan. Le workflow de production relit toujours le plan Supabase au moment de son exécution.

## Pourquoi le WARN n'est pas corrigé automatiquement aujourd'hui

Supabase réserve la protection contre les mots de passe compromis aux plans **Pro et supérieurs**. Le plan observé étant Free, tenter une activation n'est pas une correction valide.

Le réglage est un paramètre **Supabase Auth/GoTrue hébergé**, pas un paramètre PostgreSQL. Il ne doit jamais être modifié avec une migration SQL, `execute_sql`, une table `auth.*` ou une fonction improvisée.

La Management API officielle expose le réglage sous le champ :

`password_hibp_enabled`

sur :

`PATCH /v1/projects/{ref}/config/auth`

Référence Supabase : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Workflow prêt pour un futur passage Pro+

Le dépôt contient `.github/workflows/sinjira-v25-auth-password-hardening.yml`.

Ce workflow est volontairement manuel et :

1. exige la confirmation exacte `ENABLE-SINJIRA-V25-LEAKED-PASSWORD-PROTECTION` ;
2. exige l'environnement GitHub `production` et le secret `SUPABASE_ACCESS_TOKEN` ;
3. relit l'organisation et refuse **avant tout PATCH** un plan autre que Pro/Team/Enterprise ;
4. lit la configuration Auth distante et exige `password_min_length >= 12` ;
5. n'autorise qu'un unique PATCH avec `{"password_hibp_enabled":true}` ;
6. compare l'empreinte de toute la configuration Auth hors HIBP avant/après afin de détecter un changement concurrent ou inattendu ;
7. vérifie ensuite que le Security Advisor ne signale plus `auth_leaked_password_protection`.

Aucun rollback automatique de la configuration Auth n'est tenté si une différence concurrente est détectée : écraser une configuration Auth récente serait plus dangereux que d'arrêter l'opération.

## Condition de fermeture

Ce risque ne doit être marqué **corrigé** que lorsque les trois preuves suivantes existent en même temps :

- le plan courant est éligible à la fonction ;
- la configuration Auth distante retourne `password_hibp_enabled=true` ;
- le Security Advisor ne retourne plus `auth_leaked_password_protection`.

Tant que ces preuves ne sont pas réunies, la formulation correcte est : **workflow prêt, activation hébergée bloquée par le plan actuel**.

## Limites à ne pas confondre

Les avis `rls_enabled_no_policy` sur plusieurs tables privées serveur-only ne justifient pas l'ajout de politiques client permissives. Le modèle Coffre et Mon IA repose volontairement sur l'absence de politique client et des RPC serveur étroits ; ces INFO doivent être analysés selon le contrat de chaque table, pas supprimés en masse pour faire disparaître un Advisor.
