# SINJIRA V24.5.13 — Frontière RPC utilisateur Histoire de vie

## Objectif

V24.5.13 réduit la surface privilégiée exposée par l’API publique pour les opérations utilisateur de l’Histoire de vie et du signalement posthume, sans modifier les consentements, les destinataires, les règles de vérification du décès ni la séparation avec le Registre.

Les implémentations `SECURITY DEFINER` sont déplacées dans `sinjira_life_story_internal`. Le schéma `public` conserve les mêmes signatures au moyen de wrappers `SECURITY INVOKER`.

## RPC couvertes

Les **6 RPC** suivantes sont couvertes :

- `life_story_contest_death_verification(uuid,text)`
- `life_story_create_report_code(text)`
- `life_story_list_report_codes()`
- `life_story_my_posthumous_case()`
- `life_story_report_death_by_code(text,text,date)`
- `life_story_revoke_report_code(uuid)`

## Audit production

Après migration :

- 6/6 wrappers publics présents;
- 6/6 wrappers publics `SECURITY INVOKER`;
- 0/6 wrapper public `SECURITY DEFINER`;
- 0/6 exécutable par `anon`;
- 6/6 exécutables par `authenticated`;
- 6/6 exécutables par `service_role`;
- 6/6 implémentations internes `SECURITY DEFINER`;
- 6/6 signatures et types de retour conservés;
- 6/6 implémentations conservent `auth.uid()`;
- 5/6 conservent la barrière `sinjira_mfa_access_allowed` exactement comme avant la migration.

`life_story_report_death_by_code` ne possédait pas de barrière MFA directe avant V24.5.13 et V24.5.13 n’en invente pas une silencieusement. Le contrôle d’identité et toutes ses validations historiques sont conservés.

## Invariants humains et de confidentialité

Cette migration ne change pas le modèle de consentement de l’Histoire de vie :

- l’Histoire de vie reste distincte du Registre;
- aucune donnée du Registre n’est automatiquement copiée ou publiée;
- aucune extraction posthume automatique des secrets du Registre n’est créée;
- les destinataires ne gagnent aucun accès immédiat aux sources privées;
- la vérification du décès et la revue humaine restent requises par le pipeline existant;
- le clonage IA posthume reste interdit;
- la sortie autorisée demeure un PDF final selon les règles déjà établies;
- la contestation d’une vérification du décès reste possible;
- aucune nouvelle donnée n’est collectée par cette migration.

## Production

Migration appliquée :

`20260823013006 sinjira_v24_5_13_life_story_user_rpc_boundary`

Le ledger production compte **144 migrations** à ce jalon.
