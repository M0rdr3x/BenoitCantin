# SINJIRA™ — Précommandes du Livre I

**Version : V24.5.6**  
**Statut : canon produit et architecture**  
**Produit initial : SINJIRA™ — Livre I : La Cendre du Jugement**

## 1. Objet

SINJIRA possède un emplacement officiel permettant à une personne de **réserver une précommande** du Livre I avant l’ouverture de la boutique transactionnelle.

Cette phase sert à enregistrer l’intention d’achat et à mesurer la demande. Elle ne doit pas être présentée techniquement comme une vente déjà conclue.

## 2. Règle financière absolue de cette phase

En V24.5.3 et versions préparatoires suivantes :

- aucun paiement n’est prélevé;
- aucune carte bancaire n’est demandée;
- aucune adresse de facturation n’est demandée;
- aucune adresse de livraison n’est demandée;
- aucun fournisseur de paiement n’est appelé;
- aucun abonnement ou service externe payant n’est requis;
- aucune réservation ne peut devenir automatiquement une commande payante;
- aucun montant n’est dû simplement parce qu’une réservation existe.

La base de données impose :

```text
payment_status = not_collected
financial_commitment = false
```

Ces deux valeurs restent des invariants serveur tant que la réservation n’a pas été remplacée par un futur parcours d’achat explicitement consenti.

## 3. Parcours utilisateur

La précommande est accessible depuis :

- la section Littérature du portail SINJIRA;
- la page dédiée du Livre I;
- `Mes achats et précommandes` dans le Compte SINJIRA.

Une personne connectée peut :

1. choisir un **format souhaité**;
2. indiquer une quantité de 1 à 5;
3. choisir si elle souhaite être avertie **dans SINJIRA** lorsque les conditions de vente seront disponibles;
4. réserver;
5. modifier sa réservation;
6. annuler sa réservation;
7. réactiver ultérieurement la même réservation si la phase reste ouverte;
8. indiquer une préférence de réception : livraison, ramassage sur place ou décision ultérieure.

## 4. Formats

Les choix actuels sont des préférences et non des promesses commerciales :

- papier;
- numérique;
- papier + numérique;
- indécis.

La présence d’un choix ne garantit pas qu’une édition finale particulière sera commercialisée.

## 5. Données minimisées

La réservation conserve uniquement :

- l’identifiant interne du Compte SINJIRA;
- le produit réservé;
- la quantité;
- le format souhaité;
- l’état réservé/annulé;
- la préférence d’avertissement interne;
- la préférence `shipping`, `pickup` ou `undecided`;
- éventuellement le point de ramassage public choisi;
- les horodatages nécessaires au fonctionnement.

Aucune donnée bancaire ou adresse de livraison n’appartient à `product_preorders`. La zone choisie dans le calculateur de livraison n’est pas enregistrée.

## 6. Identité et confidentialité

La réservation est liée au Compte SINJIRA afin d’éviter de redemander l’identité ou les coordonnées de la personne.

Un utilisateur authentifié ne peut lire que sa propre réservation. L’administration SINJIRA peut consulter les réservations pour gérer la demande. Les données ne doivent pas être revendues, profilées pour la publicité ou réutilisées dans Rencontres, Emploi ou le Registre des Consciences.

## 7. Produit canonique initial

Le catalogue contient le produit :

```text
slug: sinjira-livre-01-la-cendre-du-jugement
name: SINJIRA™ — Livre I : La Cendre du Jugement
product_type: novel
```

Aucun prix n’est défini automatiquement.

## 8. Information commerciale V24.5.5

La V24.5.5 ajoute une fiche commerciale versionnée distincte de la réservation. Elle peut contenir, une fois les décisions humaines prises :

- la devise;
- le prix et le libellé d’une édition papier;
- le prix et le libellé d’une édition numérique;
- la date de sortie annoncée;
- la fin éventuelle des réservations;
- une note de disponibilité;
- un résumé des conditions.

Aucune de ces valeurs n’est inventée ni préremplie par la migration.

Le parcours de publication est :

```text
brouillon privé
      ↓
prêt après vérification de complétude
      ↓
publication informative
```

Une publication informative ne constitue pas une ouverture des ventes. Elle ne crée ni commande, ni notification, ni paiement.

Les cinq verrous serveur demeurent :

```text
sales_enabled = false
checkout_enabled = false
payment_enabled = false
external_fulfillment_enabled = false
auto_conversion_allowed = false
```

Une révision publiée est immuable. Une future correction ou modification passe par une nouvelle révision afin de préserver ce qui avait été présenté aux personnes.

Le protocole détaillé est défini dans `PREPARATION_COMMERCIALE_LIVRE_I_V24_5_5.md`.

## 9. Livraison et ramassage V24.5.6

Pour un exemplaire physique expédié, **les frais de livraison sont à la charge du client**. Cette règle est affichée avant l’achat.

SINJIRA peut publier des fourchettes de frais par zone et quantité afin que la personne puisse se faire une idée du coût possible. Ces fourchettes ne sont pas des devis : le coût final doit être affiché et accepté dans le futur parcours d’achat.

Le ramassage sur place peut être choisi comme préférence. Il comporte `0 $` de frais de livraison. Un lieu de retrait n’est affiché qu’après publication explicite par l’administration MFA/AAL2.

Aucune API transporteur ni achat d’étiquette externe n’est activé par V24.5.6.

Le protocole détaillé est défini dans `LIVRAISON_RAMASSAGE_LIVRE_I_V24_5_6.md`.

## 10. Frontière avec les commandes payantes

`product_preorders`, `preorder_commercial_plans` et les données de préparation de livraison sont distincts de `orders` et `order_items`.

Une future ouverture des ventes doit être une nouvelle phase explicite. Une réservation peut alors permettre d’inviter la personne à commander, mais la création d’une commande payante doit exiger une nouvelle action volontaire et l’acceptation des conditions alors en vigueur.

La séquence autorisée est :

```text
Réservation de précommande
        ↓
Annonce des prix, livraison et conditions réels
        ↓
Nouvelle confirmation volontaire
        ↓
Checkout payant seulement si ce service a été explicitement activé
        ↓
Commande
```

La séquence interdite est :

```text
Réservation de précommande
        ↓
Débit automatique / commande automatique
```

## 11. Services externes

Cette fonctionnalité respecte `SERVICES_EXTERNES_PAYANTS.md` : le système de paiement futur et les intégrations transporteur peuvent être préparés en code, mais ils restent désactivés tant qu’une autorisation séparée n’a pas été donnée.

## 12. Principe d’arbitrage

La précommande doit réduire la friction pour la personne sans lui retirer son choix.

**Réserver aujourd’hui ne signifie jamais consentir à payer demain, et les frais de livraison ne doivent jamais être une surprise après l’achat.**
