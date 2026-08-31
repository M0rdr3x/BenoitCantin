# SINJIRA™ V24.5.46 — Confidentialité des sorties UUID de précommande

## Objectif

Terminer le principe introduit en V24.5.32 : **l’UUID interne d’une précommande ne doit pas traverser la surface API utilisée par une personne ou par la console d’administration**.

La référence partageable reste la référence indépendante `PR-XXXXXXXXXXXXXXXX`. Elle n’est ni un UUID, ni un identifiant du compte, ni un numéro de commande.

## Correction utilisateur

`product_preorder_reserve_confirmed(...)` renvoyait historiquement l’UUID interne de la ligne créée/mise à jour, même si le JavaScript SINJIRA ignorait ce résultat et relisait ensuite l’état sécurisé.

V24.5.46 remplace ce retour par :

- `text`;
- la `reservation_reference` au format `PR-…`;
- aucun `user_id`;
- aucun UUID interne de précommande.

Les contrôles existants restent inchangés : authentification, accusé de compréhension V24.5.31, produit autorisé, format, quantité, `payment_status = not_collected` et `financial_commitment = false`.

## Correction administration

`admin_preorder_list(...)` ne renvoie plus `preorder_id uuid`. La première colonne devient `reservation_reference text`.

La console continue d’afficher uniquement des données nécessaires : libellé de compte, quantité, format, état, préférence d’avis et dates. Aucun courriel, téléphone, adresse de livraison, adresse de facturation ou donnée bancaire n’est ajouté.

L’accès reste administrateur + MFA/AAL2 via l’implémentation interne existante.

## ACL et frontière

- wrappers `public` : `SECURITY INVOKER`;
- `anon` : aucun `EXECUTE` sur les RPC de réservation confirmée et de liste admin;
- `authenticated` et `service_role` : droits conservés;
- implémentations privilégiées restent dans `preorder_user_internal` et `preorder_admin_internal`.

## Contrat commercial inchangé

- réservation ≠ commande;
- aucune vente active;
- aucun checkout actif;
- aucun paiement actif;
- aucune conversion automatique;
- aucun fournisseur de paiement ou transporteur externe;
- aucun service payant activé;
- frais de livraison à la charge du client si expédition physique;
- ramassage sur place : 0 $ de frais de livraison lorsqu’un point est disponible.

## Production

Migration appliquée :

`20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening`

Le ledger production passe à **174 migrations**.
