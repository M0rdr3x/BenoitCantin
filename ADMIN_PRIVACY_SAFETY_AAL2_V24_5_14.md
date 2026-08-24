# SINJIRA — Durcissement AAL2 confidentialité/sécurité

## Migration production

`20260824013042 sinjira_v24_5_14_admin_privacy_safety_aal2_hardening`

Production contient maintenant **163 migrations**.

## Correction

Les cinq implémentations administratives suivantes utilisent désormais `private.require_sinjira_admin_aal2()` :

- `privacy_admin_incidents`
- `privacy_admin_record_incident`
- `privacy_admin_requests`
- `privacy_admin_update_request`
- `safety_admin_escalation_cases`

Le rôle `service_role` reste compatible avec ce garde-fou. Les wrappers publics restent `SECURITY INVOKER`, `anon` conserve zéro droit d'exécution et les signatures publiques ne changent pas.

## Règle de sécurité

Un compte administrateur humain doit être en AAL2/MFA pour ces opérations. Le contrôle `service_role` reste possible pour les traitements serveur de confiance.

Aucun paiement, transporteur externe, checkout, DNS ou service payant n'est activé par cette migration.
