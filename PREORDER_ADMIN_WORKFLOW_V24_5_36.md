# SINJIRA™ V24.5.36 — suivi administratif non financier des précommandes

## Objectif

Permettre à l’administration SINJIRA™ d’organiser le traitement des réservations du Livre I sans transformer une réservation en commande et sans collecter de données personnelles supplémentaires.

Le suivi est exclusivement interne et opérationnel. Il utilise la référence publique de réservation `PR-…` comme repère de travail.

## États autorisés

Trois états seulement sont permis :

- `pending` — à traiter;
- `ready_for_future_contact` — prêt pour une étape future;
- `completed` — traitement administratif terminé.

Ces états sont réversibles. Ils ne modifient jamais l’état de la réservation elle-même.

## Minimisation des données

Le suivi est stocké dans `private.preorder_admin_workflow`, avec RLS activée et aucun accès direct pour `anon` ou `authenticated`.

Aucune note libre n’est prévue. Le suivi ne stocke ni courriel, ni adresse, ni numéro de téléphone, ni donnée bancaire, ni texte de profil. L’interface publique des RPC ne retourne aucun UUID ou identifiant technique de compte.

## Frontière d’administration

Les wrappers publics sont `SECURITY INVOKER`. Les implémentations privilégiées résident dans `preorder_admin_internal` et répètent `private.require_sinjira_admin_aal2()`.

`anon` n’a aucun droit d’exécution. Les comptes authentifiés ne peuvent donc utiliser ces opérations qu’après validation serveur du rôle administrateur et du niveau MFA/AAL2.

## Effets interdits

Changer un état de suivi :

- n’envoie aucun avis interne ou externe;
- ne crée aucune commande;
- n’active aucune vente;
- ne lance aucun checkout;
- ne collecte ni ne prélève aucun paiement;
- ne réserve aucun transporteur;
- ne crée aucune étiquette de livraison;
- ne convertit jamais automatiquement une réservation en achat.

La livraison d’un livre physique reste à la charge du client. Le ramassage sur place reste à 0 $ de frais de livraison lorsqu’il est offert et publié.

## Production

Migration : `20260830012533 sinjira_v24_5_36_preorder_admin_workflow`.

Le ledger Supabase compte **169 migrations** après V24.5.36.

La migration a été appliquée sans créer de ligne de suivi : l’état production initial vérifié est **0 ligne** dans `private.preorder_admin_workflow`, **0 vente/checkout/paiement activé**, **0 zone de livraison publiée** et **0 point de ramassage publié**.