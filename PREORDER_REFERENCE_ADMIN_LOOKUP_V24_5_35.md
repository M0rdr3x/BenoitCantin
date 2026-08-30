# SINJIRA™ V24.5.35 — recherche admin par référence de précommande

## Objectif

Donner une utilité opérationnelle à la référence `PR-…` que la personne peut copier depuis V24.5.34, sans transformer cette référence en identifiant de compte et sans rechercher une personne par courriel, UUID ou adresse.

## Accès

La recherche est disponible uniquement dans la console privée des précommandes. Le navigateur vérifie déjà le rôle administrateur et le niveau MFA/AAL2. Le serveur répète obligatoirement cette barrière avec `private.require_sinjira_admin_aal2()`.

`anon` n’a aucun droit d’exécution. Le wrapper `public.admin_preorder_find_by_reference(text)` est `SECURITY INVOKER`; l’implémentation privilégiée reste dans `preorder_admin_internal`.

## Entrée

Une seule donnée de recherche est acceptée : une référence normalisée au format `PR-[0-9A-F]{16}`.

Aucune recherche par nom, courriel, UUID, adresse postale, numéro de téléphone ou identifiant interne n’est introduite.

## Résultat minimal

La réponse contient seulement :

- la référence `PR-…`;
- le nom/pseudo de profil déjà utilisé par la console admin;
- le nom du produit;
- quantité et format souhaités;
- état active/annulée;
- opt-in d’avis interne;
- préférence livraison/ramassage;
- version et date d’acceptation des conditions;
- dates de création et de mise à jour.

Elle ne retourne aucun UUID, courriel, adresse de livraison, adresse de facturation, donnée bancaire, identifiant de point de retrait ou identifiant interne de produit.

## Livraison et paiement

La recherche ne change aucune réservation et n’ouvre aucune vente. Les frais de livraison d’un livre physique restent à la charge du client. Le ramassage sur place reste à 0 $ de frais de livraison lorsqu’il est disponible.

Aucun paiement, checkout, transporteur externe, courriel/SMS ou fournisseur externe payant n’est activé.

## Production

Migration : `20260830004410 sinjira_v24_5_35_preorder_reference_admin_lookup`.

Le ledger Supabase compte **168 migrations** après V24.5.35.
