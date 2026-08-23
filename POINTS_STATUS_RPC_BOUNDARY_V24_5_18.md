# SINJIRA V24.5.18 — Frontière RPC statut Points

## Objectif

Réduire l’exposition privilégiée de `sinjira_points_status()` sans activer l’achat de Points ni modifier le solde, le ledger ou les règles du module Rencontres.

## Frontière

- wrapper public `public.sinjira_points_status()` : `SECURITY INVOKER`
- implémentation privilégiée : `sinjira_points_user_internal.sinjira_points_status()`
- `anon` : aucun `EXECUTE`
- `authenticated` et `service_role` : droits conservés
- `auth.uid()` : conservé dans l’implémentation interne
- signature et type de retour : inchangés

## Verrou commercial

L’implémentation conserve explicitement `purchases_enabled=false`. V24.5.18 ne crée aucun checkout, aucun paiement, aucune vente de Points et aucun fournisseur externe.

## Continuité

Le solde personnel reste obtenu via le moteur privé existant. Cette migration ne modifie pas les débits Safe Meet, le ledger universel ni les règles Rencontres.

## Production

Migration : `20260823030432 sinjira_v24_5_18_points_status_rpc_boundary`

Le registre de production contient **149 migrations** après V24.5.18.
