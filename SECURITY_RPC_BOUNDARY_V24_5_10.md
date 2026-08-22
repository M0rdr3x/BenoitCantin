# SINJIRA V24.5.10 — Frontière RPC du centre de sécurité

## Objectif

Les opérations du centre de sécurité doivent conserver leurs contrôles de propriété et d’authentification sans exposer directement une implémentation `SECURITY DEFINER` dans le schéma API `public`.

V24.5.10 déplace exactement **17 RPC `security_*`** dans `sinjira_security_internal` et recrée les mêmes signatures publiques sous forme de wrappers `SECURITY INVOKER`.

## Invariants vérifiés en production

- 17/17 wrappers publics `SECURITY INVOKER`;
- 0/17 wrapper public `SECURITY DEFINER`;
- 0/17 exécutable par `anon`;
- 17/17 exécutables par `authenticated`;
- 17/17 exécutables par `service_role`;
- 17/17 implémentations internes `SECURITY DEFINER`;
- 17/17 signatures et types de retour conservés;
- 17/17 implémentations conservent une vérification liée à `auth.uid()`;
- 2/17 contiennent un contrôle AAL2 direct, exactement comme avant la migration.

La migration ne rajoute pas artificiellement un contrôle AAL2 aux autres opérations : les règles fonctionnelles existantes sont préservées. Les parcours qui imposent déjà une étape MFA côté serveur ou interface continuent de le faire.

## RPC couvertes

- `security_after_password_recovery`
- `security_cancel_travel_plan`
- `security_compromise_account`
- `security_create_travel_plan`
- `security_disable_push_for_device`
- `security_get_settings`
- `security_list_sessions`
- `security_push_status`
- `security_register_device`
- `security_register_push_endpoint`
- `security_report_lost_device`
- `security_resolve_connection_challenge`
- `security_resolve_connection_challenge_mfa`
- `security_revoke_device`
- `security_sensitive_access_status`
- `security_set_device_trust`
- `security_update_settings`

## Confidentialité

Cette frontière ne change pas le principe de sécurité contextuelle : pas de GPS brut, pas de culpabilité fondée uniquement sur la localisation, Mode Voyage limité aux informations approximatives nécessaires à la protection du compte.

## Production

Migration appliquée :

`20260822201257 sinjira_v24_5_10_security_rpc_boundary`

Le ledger production contient **141 migrations**.

L’advisor Supabase ne signale plus ces 17 RPC comme fonctions `SECURITY DEFINER` publiques exécutables par les comptes connectés.
