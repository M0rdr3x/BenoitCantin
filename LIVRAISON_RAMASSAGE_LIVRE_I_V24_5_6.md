# SINJIRA™ — Livraison et ramassage du Livre I

**Version : V24.5.6**  
**Produit : SINJIRA™ — Livre I : La Cendre du Jugement**

## Principe

La précommande reste une réservation sans paiement. Pour une future commande d’un exemplaire physique expédié, **les frais de livraison sont à la charge du client**.

Cette règle doit être annoncée avant l’achat, et non découverte après la confirmation de commande.

## Estimation des frais de livraison

SINJIRA peut publier des fourchettes par zone de destination. Une estimation utilise seulement :

- la zone choisie par la personne;
- la quantité d’exemplaires;
- une fourchette de base;
- une éventuelle fourchette par exemplaire additionnel.

Le calculateur ne stocke pas l’adresse de la personne ni la zone utilisée pour le calcul.

Une estimation reste indicative. Le prix réel pourra varier selon le poids final, l’emballage, la destination exacte, le transporteur et les tarifs en vigueur. Avant toute future commande payante, le coût réel de livraison devra être affiché et accepté séparément.

Aucune fourchette n’est préremplie par V24.5.6. L’administration doit utiliser des coûts raisonnablement vérifiés avant de publier une zone.

## Ramassage sur place

Une personne ayant réservé le Livre I peut indiquer :

```text
Livraison
Ramassage sur place
Je déciderai plus tard
```

Le ramassage sur place ne comporte **aucun frais de livraison**.

Un point de ramassage peut contenir :

- un nom public;
- une adresse publique;
- une ville et une région;
- une plage de disponibilité;
- des instructions de retrait.

Un point reste privé tant qu’un administrateur MFA/AAL2 ne le publie pas explicitement. Modifier un point publié le remet en brouillon afin d’éviter qu’une adresse ou une instruction change silencieusement.

L’administration doit éviter de publier une adresse personnelle si elle ne souhaite pas la rendre publique.

## Frontière avec une future vente

V24.5.6 ne crée aucune commande, aucun paiement, aucune étiquette d’expédition et aucune réservation de transporteur.

Les garde-fous sont :

```text
shipping_customer_pays = true
pickup_interest_enabled = true
external_carrier_api_enabled = false
external_shipping_purchase_enabled = false
pickup_shipping_charge_cents = 0
```

Les invariants commerciaux existants restent aussi actifs :

```text
sales_enabled = false
checkout_enabled = false
payment_enabled = false
auto_conversion_allowed = false
```

## Services externes

Aucune API Canada Post, UPS, FedEx, Purolator ou autre transporteur n’est activée par V24.5.6.

Une intégration future peut être préparée, mais son activation exige une décision distincte sur :

1. le fournisseur;
2. le coût;
3. les données transmises;
4. les limites de dépense;
5. la désactivation et le plan de repli.

## Données minimisées

La préférence de réception conserve seulement :

- `shipping`;
- `pickup`;
- `undecided`;
- éventuellement le point de ramassage public choisi.

Aucune adresse de livraison n’est collectée dans la précommande.

## Principe produit

**La personne doit savoir avant d’acheter qui paie la livraison et pouvoir éviter ces frais en choisissant un ramassage lorsque cette option est disponible.**
