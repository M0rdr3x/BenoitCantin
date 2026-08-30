# SINJIRA V24.5.38 — Préparation logistique interne des précommandes

## But

Préparer les exemplaires du Livre I avant toute ouverture transactionnelle, sans collecter davantage de données personnelles et sans transformer une réservation en commande.

## Frontière de données

La file logistique admin retourne uniquement : référence `PR-…`, produit, quantité, format souhaité, état de réservation, préférence de réception, nom et ville du point de retrait choisi, version/date des conditions confirmées et état de suivi interne.

Elle ne retourne ni UUID, ni nom réel, ni courriel, ni téléphone, ni adresse d’expédition/facturation, ni donnée bancaire.

## Accès

- administration SINJIRA seulement;
- MFA/AAL2 obligatoire via `private.require_sinjira_admin_aal2()`;
- wrapper public `SECURITY INVOKER`;
- implémentation privilégiée dans `preorder_admin_internal`;
- `anon` révoqué;
- `authenticated` et `service_role` conservent EXECUTE, avec le contrôle admin/AAL2 côté serveur.

## Export CSV

L’export CSV est généré localement par le navigateur à partir de la réponse minimale. Aucun fichier n’est envoyé au serveur, à un transporteur, à un service de courriel ou à un fournisseur externe.

Les réservations annulées sont exclues par défaut de la préparation; l’admin peut les afficher volontairement pour vérification.

## Contrat commercial inchangé

- frais de livraison à la charge du client;
- ramassage sur place : 0 $ de frais de livraison;
- aucune API transporteur;
- aucune étiquette achetée;
- aucune adresse collectée pendant la précommande;
- vente, checkout et paiement désactivés;
- aucune conversion automatique réservation → commande.

## Production

Migration : `20260830035043 sinjira_v24_5_38_preorder_logistics_queue`.

Le ledger production contient 172 migrations après V24.5.38.
