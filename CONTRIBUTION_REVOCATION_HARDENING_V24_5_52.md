# SINJIRA V24.5.52 — Révocation explicite et bornée des contributions

## Objectif

Durcir `revoke-my-contributions` sans réduire le droit de retrait d’une personne ni modifier la propriété des contributions.

## Production

`revoke-my-contributions` est déployée en production en version **2** avec `verify_jwt=true`.

V24.5.52 n’ajoute **aucune migration Supabase**. Le ledger reste à **174 migrations**.

## Correction d’un risque de portée

L’ancienne surface transformait implicitement l’absence de `session_id` en `p_session_id = null`, ce qui correspond au mode « toutes les contributions ».

Depuis V24.5.52 :

- révoquer toutes les contributions exige explicitement `all: true` ;
- sinon un `session_id` UUID valide est obligatoire ;
- `all: true` et `session_id` ensemble sont refusés comme portée ambiguë ;
- un corps vide ne peut plus déclencher une révocation globale.

## Surface HTTP

- `POST` uniquement ;
- `application/json` obligatoire ;
- corps limité à **2 048 octets**, sur taille déclarée et taille réellement lue ;
- JSON invalide rejeté ;
- lecture directe `await req.json()` sans borne interdite par le CI.

## Réponses privées

Les réponses applicatives utilisent :

- `Cache-Control: private, no-store, max-age=0` ;
- `Pragma: no-cache` ;
- `X-Content-Type-Options: nosniff` ;
- `Referrer-Policy: no-referrer`.

## Autorisation

- JWT obligatoire ;
- utilisateur authentifié obligatoire ;
- l’identifiant utilisateur transmis à la RPC est toujours celui de la session authentifiée ;
- `revoke_sinjira_contributions(uuid, uuid)` demeure exécutable uniquement par `service_role` côté base ;
- aucune possibilité de choisir l’UUID d’un autre utilisateur n’est exposée au client.

## Coûts

Aucun paiement, checkout, vente, transporteur, courriel/SMS payant, IA distante payante ou autre fournisseur facturable n’est activé par V24.5.52.
