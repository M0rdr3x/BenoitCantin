# SINJIRA™ V24.5.33 — Convergence des droits utilisateur

## Principe

Cette version ne crée aucun nouveau droit métier. Elle corrige une frontière RPC redondante créée alors que les cinq RPC Confidentialité / Appels utilisateur étaient déjà protégées par la frontière canonique `sinjira_user_rights_internal`.

## État final attendu

Les RPC publiques suivantes restent des wrappers `SECURITY INVOKER` :

- `privacy_create_request`
- `privacy_export_my_extended_data`
- `privacy_my_requests`
- `moderation_my_decisions`
- `moderation_submit_appeal`

Elles appellent directement `sinjira_user_rights_internal`.

Les implémentations canoniques internes restent `SECURITY DEFINER`, conservent `auth.uid()`, et restent exécutables uniquement par `authenticated` et `service_role`. `anon` ne reçoit aucun droit d’exécution.

Le schéma temporaire `sinjira_privacy_moderation_internal` doit être absent après convergence.

## Traçabilité production

Deux migrations ont réellement été appliquées et sont donc conservées dans le ledger :

- `20260830001642 sinjira_v24_5_14_privacy_moderation_user_rpc_boundary`
- `20260830001742 sinjira_v24_5_32_user_rights_redundant_boundary_cleanup`

La production compte **167 migrations** après cette convergence.

## Invariants

- aucun changement des droits de confidentialité de l’utilisateur ;
- aucun changement du droit d’appel en modération ;
- aucun accès `anon` ajouté ;
- aucune politique RLS ouverte artificiellement ;
- aucun paiement, service externe ou fournisseur payant activé ;
- aucun changement DNS, passkey ou transporteur.
