# SINJIRA™ V24.5.28 — Convergence de la frontière des droits utilisateur

## Objet

V24.5.28 rétablit la frontière canonique des cinq RPC utilisateur Confidentialité et appels de modération après détection d'une couche intermédiaire redondante créée alors que V24.5.14 avait déjà réalisé cette isolation.

La frontière canonique est :

```text
public.*
  SECURITY INVOKER
        ↓
sinjira_user_rights_internal.*
  SECURITY DEFINER
        ↓
contrôles auth.uid() et règles métier existantes
```

## RPC concernées

- `moderation_my_decisions(integer)`
- `moderation_submit_appeal(uuid,text)`
- `privacy_create_request(text,text)`
- `privacy_export_my_extended_data()`
- `privacy_my_requests(integer)`

## Garanties

- 5/5 wrappers publics restent `SECURITY INVOKER`;
- 0/5 wrapper public est exécutable par `anon`;
- 5/5 restent exécutables par `authenticated` et `service_role`;
- 5/5 implémentations privilégiées restent dans `sinjira_user_rights_internal` et `SECURITY DEFINER`;
- 5/5 implémentations conservent leur contrôle `auth.uid()`;
- signatures et types de retour sont inchangés;
- `privacy_my_requests` retrouve son contrat canonique `p_limit integer DEFAULT 20`;
- le schéma intermédiaire `sinjira_privacy_moderation_internal` est supprimé sans `CASCADE`;
- les droits d'appel humain et les demandes de confidentialité ne sont pas modifiés.

## Historique de réconciliation

La migration `20260823205908 sinjira_v24_5_14_privacy_moderation_user_rpc_boundary` est conservée dans le ledger parce qu'elle a été appliquée en production. Elle représente le pont redondant détecté. Elle est immédiatement neutralisée par :

`20260823210123 sinjira_v24_5_28_user_rights_boundary_convergence`.

Le ledger de production comporte alors **162 migrations**.

## Services externes

Cette convergence n'active aucun paiement, checkout, transporteur, API fiscale, courriel/SMS payant, IA distante payante, DNS, passkey ou autre service externe facturable.
