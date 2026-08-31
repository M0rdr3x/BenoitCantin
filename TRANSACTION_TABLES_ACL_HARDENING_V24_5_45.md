# SINJIRA™ V24.5.45 — Durcissement ACL des tables transactionnelles dormantes

## Objectif

Réduire la surface SQL historique de `public.orders` et `public.order_items` pendant que les ventes, le checkout et les paiements restent désactivés.

## État observé avant correction

- `orders` et `order_items` contenaient **0 ligne** en production;
- RLS était déjà activée;
- les seules politiques existantes autorisaient la lecture `SELECT` d’une commande appartenant au compte authentifié;
- aucun code applicatif courant n’écrit directement dans ces tables;
- malgré cela, les rôles `anon` et `authenticated` conservaient encore des privilèges SQL hérités plus larges que les politiques RLS.

## Correction

V24.5.45 applique une défense en profondeur :

- `anon` perd tout privilège direct sur `orders` et `order_items`;
- `authenticated` conserve uniquement `SELECT`;
- `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `REFERENCES` et `TRIGGER` sont révoqués à `authenticated`;
- les politiques RLS self-only existantes restent inchangées;
- les écritures futures devront passer par un chemin serveur explicitement conçu et autorisé.

## Contrat commercial inchangé

Cette migration **n’active aucune vente**. Les invariants restent :

- réservation ≠ commande;
- `sales_enabled = false`;
- `checkout_enabled = false`;
- `payment_enabled = false`;
- aucune conversion automatique réservation → commande;
- aucun Stripe, PayPal ou fournisseur de paiement;
- aucun transporteur externe;
- aucun service payant activé.

Les frais de livraison d’un livre physique expédié restent à la charge du client. Le ramassage sur place, lorsqu’un point public est disponible, ajoute **0 $ de frais de livraison**.

## Production

Migration appliquée :

`20260831002808 sinjira_v24_5_45_transaction_tables_acl_hardening`

Le ledger production passe à **173 migrations**.
