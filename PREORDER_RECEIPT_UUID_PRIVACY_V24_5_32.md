# SINJIRA™ V24.5.32 — preuve de réservation et confidentialité des identifiants

## Principe

Une précommande reste une réservation sans paiement. V24.5.32 ajoute une preuve lisible dans le Compte SINJIRA™ sans exposer l’UUID interne de la ligne de base de données.

La référence visible suit le format `PR-XXXXXXXXXXXXXXXX`, où les 16 caractères hexadécimaux sont générés aléatoirement. Elle sert uniquement à reconnaître une réservation; elle n’est ni un numéro de commande ni un identifiant du compte.

## Données visibles

`product_preorder_my_status(text)` peut retourner uniquement les données nécessaires à la personne :

- référence de réservation indépendante;
- produit et nom du roman;
- quantité;
- format souhaité;
- préférence livraison / ramassage / plus tard;
- état réservé ou annulé;
- préférence d’avis interne;
- état financier `not_collected` et `financial_commitment=false`;
- version et date du texte de transparence réellement confirmé;
- dates de création, mise à jour et annulation éventuelle.

Le résultat public ne retourne plus `preorder_id`, `user_id`, `product_id`, `pickup_point_id` ni aucun UUID interne.

## Anciennes réservations

Toutes les réservations existantes reçoivent une référence indépendante. En revanche, une ancienne réservation dont `disclosure_version` et `disclosure_acknowledged_at` sont absents n’est jamais présentée comme ayant accepté rétroactivement V24.5.31. L’interface indique que la confirmation n’est pas enregistrée pour cette ancienne réservation.

## Livraison et ramassage

Les règles précédentes restent inchangées :

- les frais de livraison d’un livre physique sont à la charge du client;
- l’estimation de livraison est indicative et non contractuelle;
- aucune adresse exacte n’est collectée pour l’estimation;
- le ramassage sur place ajoute 0 $ de frais de livraison lorsqu’un point public est disponible;
- le coût final doit être présenté et accepté avant toute future transaction.

## Sécurité RPC

- `public.product_preorder_my_status(text)` reste `SECURITY INVOKER`;
- `anon` n’a pas `EXECUTE`;
- `authenticated` et `service_role` conservent `EXECUTE`;
- l’implémentation interne reste dans `preorder_user_internal` et vérifie `auth.uid()`.

## Commerce

V24.5.32 n’active aucun paiement, checkout, vente, conversion automatique, API transporteur, API fiscale, courriel/SMS payant ou autre fournisseur externe payant.

Migration production : `20260829233536 sinjira_v24_5_32_preorder_receipt_and_uuid_privacy`.

Le ledger production contient **165 migrations** après ce jalon.
