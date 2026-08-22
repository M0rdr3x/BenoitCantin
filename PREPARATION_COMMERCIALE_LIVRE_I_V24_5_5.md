# SINJIRA™ — Préparation commerciale du Livre I — V24.5.5

## Objet

La V24.5.5 prépare la publication des informations commerciales de **SINJIRA™ — Livre I : La Cendre du Jugement** sans ouvrir la boutique et sans transformer une réservation en vente.

Le système distingue trois objets :

1. la **réservation de précommande** V24.5.3;
2. l’**information commerciale publiée** V24.5.5;
3. une future **commande payante**, qui n’existe pas encore dans ce parcours.

## Principe de consentement

Une réservation exprime un intérêt. Elle ne constitue ni une promesse d’achat ni une autorisation de prélèvement.

Même lorsque le prix, l’édition et la date de sortie sont publiés, la réservation conserve :

```text
payment_status = not_collected
financial_commitment = false
```

Une future vente devra présenter à nouveau les éléments pertinents et demander une confirmation volontaire séparée avant tout checkout.

## Fiche commerciale versionnée

La table `preorder_commercial_plans` conserve des révisions. Les états sont :

```text
draft → ready → published → superseded
```

Une révision publiée est immuable. Lorsqu’une nouvelle version doit remplacer une information publiée, une nouvelle révision est préparée puis publiée; l’ancienne devient `superseded`.

La fiche peut contenir :

- devise;
- prix papier;
- prix numérique;
- libellé de l’édition papier;
- libellé de l’édition numérique;
- date de sortie annoncée;
- fin éventuelle de la période de réservation;
- note de disponibilité;
- résumé des conditions.

Aucune de ces valeurs n’est initialisée avec un prix, une édition ou une date fictive.

## Conditions minimales avant publication

Pour passer de `draft` à `ready`, la fiche doit posséder :

- une date de sortie;
- un résumé des conditions;
- au moins une édition avec son prix correspondant.

L’action `ready` ne publie encore rien.

L’action `publish` rend uniquement la fiche informative visible sur la page publique et dans le Compte SINJIRA™.

## Verrous de non-vente

La table et son trigger imposent toujours :

```text
sales_enabled = false
checkout_enabled = false
payment_enabled = false
external_fulfillment_enabled = false
auto_conversion_allowed = false
```

La lecture publique vérifie également ces cinq valeurs avant d’afficher la fiche.

## Administration

Les opérations administratives exigent le rôle SINJIRA et **MFA/AAL2** :

- `admin_preorder_commercial_plan_get`;
- `admin_preorder_commercial_plan_save`;
- `admin_preorder_commercial_plan_mark_ready`;
- `admin_preorder_commercial_plan_publish`.

La table n’est pas directement lisible ni modifiable par `anon` ou `authenticated`.

## Lecture utilisateur

La RPC `product_preorder_commercial_info` ne retourne que la révision `published`.

Avant publication, l’interface indique simplement que le prix, les éditions et la date ne sont pas encore annoncés.

Après publication, l’interface peut afficher les informations confirmées, mais rappelle explicitement que :

- la vente reste fermée;
- le checkout reste désactivé;
- aucun paiement n’est possible;
- la réservation ne devient pas automatiquement une commande.

## Notifications

Publier une fiche commerciale ne crée **aucune notification**.

Le mécanisme d’avis interne V24.5.4 demeure séparé et nécessite ses propres étapes `draft → ready → send`.

Cette séparation évite qu’une correction ou une mise à jour de la fiche commerciale contacte automatiquement les personnes.

## Services externes

La V24.5.5 n’active :

- aucun fournisseur de paiement;
- aucun courriel ou SMS externe;
- aucun fournisseur d’impression ou de livraison;
- aucun abonnement ou service payant.

Toute activation commerciale réelle reste soumise à une décision explicite séparée conformément à `SERVICES_EXTERNES_PAYANTS.md`.
