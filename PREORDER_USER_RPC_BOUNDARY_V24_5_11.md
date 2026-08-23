# SINJIRA V24.5.11 — Frontière RPC utilisateur des précommandes

## Objectif

V24.5.11 réduit la surface privilégiée exposée par l’API publique pour les opérations utilisateur de précommande, sans changer le comportement fonctionnel des réservations.

Le principe est identique aux frontières V24.5.8 à V24.5.10 : l’API conserve les mêmes noms de RPC et les mêmes signatures, mais les implémentations `SECURITY DEFINER` vivent dans un schéma interne non exposé directement.

## RPC couvertes

Les **5 RPC** suivantes sont couvertes :

- `product_preorder_cancel(text)`
- `product_preorder_fulfillment_status(text)`
- `product_preorder_my_status(text)`
- `product_preorder_reserve(text,text,integer,boolean)`
- `product_preorder_set_fulfillment_preference(text,text,text)`

## Frontière technique

Les implémentations privilégiées sont déplacées dans :

`preorder_user_internal`

Le schéma `public` conserve des wrappers `SECURITY INVOKER` avec les signatures historiques.

Audit production après migration :

- 5/5 wrappers publics présents;
- 5/5 wrappers publics `SECURITY INVOKER`;
- 0/5 wrapper public `SECURITY DEFINER`;
- 0/5 exécutable par `anon`;
- 5/5 exécutables par `authenticated`;
- 5/5 exécutables par `service_role`;
- 5/5 implémentations internes `SECURITY DEFINER`;
- 5/5 signatures et types de retour conservés;
- 5/5 implémentations conservent leur contrôle `auth.uid()`.

## Invariants fonctionnels

Cette migration ne change pas les règles de précommande :

- aucune réservation existante n’est transformée en achat;
- aucune obligation financière n’est ajoutée;
- aucun paiement ni checkout n’est activé;
- aucune conversion automatique en commande n’est activée;
- aucun tarif n’est publié;
- aucune zone de livraison ou point de ramassage n’est publié;
- aucun transporteur ou service externe payant n’est intégré.

Après la migration, l’audit production conserve les valeurs suivantes à zéro : ventes, checkout, paiement, conversion automatique, plans commerciaux publiés, zones de livraison publiées et points de ramassage publiés.

## Identité et confidentialité

Les RPC restent réservées aux comptes authentifiés. Le contrôle de l’utilisateur courant par `auth.uid()` reste présent dans les 5 implémentations privilégiées. `anon` ne reçoit aucun droit d’exécution.

La migration ne collecte aucune donnée supplémentaire et ne modifie aucune règle de conservation ou de confidentialité.

## Production

Migration appliquée :

`20260822202024 sinjira_v24_5_11_preorder_user_rpc_boundary`

Le ledger production compte **142 migrations** à ce jalon.
