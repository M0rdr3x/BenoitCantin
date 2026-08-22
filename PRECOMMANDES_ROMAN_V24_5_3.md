# SINJIRA™ — Précommandes du Livre I

**Version : V24.5.3**  
**Statut : canon produit et architecture**  
**Produit initial : SINJIRA™ — Livre I : La Cendre du Jugement**

## 1. Objet

SINJIRA possède un emplacement officiel permettant à une personne de **réserver une précommande** du Livre I avant l’ouverture de la boutique transactionnelle.

Cette phase sert à enregistrer l’intention d’achat et à mesurer la demande. Elle ne doit pas être présentée techniquement comme une vente déjà conclue.

## 2. Règle financière absolue de cette phase

En V24.5.3 :

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

Ces deux valeurs sont des invariants serveur de la V24.5.3.

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
7. réactiver ultérieurement la même réservation si la phase reste ouverte.

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
- les horodatages nécessaires au fonctionnement.

Aucune donnée bancaire ou adresse postale n’appartient à `product_preorders`.

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

Aucun prix n’est défini par cette migration.

## 8. Frontière avec les commandes payantes

`product_preorders` est distinct de `orders` et `order_items`.

Une future ouverture des ventes doit être une nouvelle phase explicite. Une réservation peut alors permettre d’inviter la personne à commander, mais la création d’une commande payante doit exiger une nouvelle action volontaire et l’acceptation des conditions alors en vigueur.

La séquence autorisée est :

```text
Réservation de précommande
        ↓
Annonce des prix et conditions réels
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

## 9. Services externes

Cette fonctionnalité respecte `SERVICES_EXTERNES_PAYANTS.md` : le système de paiement futur peut être préparé en code, mais il reste désactivé tant qu’une autorisation séparée n’a pas été donnée.

## 10. Principe d’arbitrage

La précommande doit réduire la friction pour la personne sans lui retirer son choix.

**Réserver aujourd’hui ne signifie jamais consentir à payer demain.**
