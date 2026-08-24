# SINJIRA™ V24.5.30 — Contrat de transparence complète des précommandes

## Objectif

Verrouiller le parcours existant du Livre I afin qu’une personne puisse comprendre le coût potentiel avant toute future vente sans transformer une réservation en commande ni activer un service payant.

## Chaîne frontend canonique

Les pages de précommande chargent `sinjira-preorder-fulfillment-v24-5-6.js`. Ce module importe obligatoirement :

- `sinjira-preorder-cost-summary-v24-5-25.js` — prix publié, quantité, livraison ou ramassage, sous-total avant taxes;
- `sinjira-preorder-tax-estimate-v24-5-27.js` — profil fiscal choisi explicitement, taxes estimatives et total indicatif après taxes.

Ces imports évitent de dupliquer les balises `<script>` et garantissent une seule chaîne de calcul.

## Informations qui doivent rester visibles

- Les frais de livraison sont à la charge du client.
- Une fourchette de livraison n’est utilisée que si une zone a été explicitement publiée.
- Aucune adresse exacte n’est demandée ou enregistrée pour une estimation.
- Le ramassage sur place ajoute 0 $ de frais de livraison.
- Un prix n’est utilisé que lorsqu’il est officiellement publié.
- Une valeur absente (`null`) ne peut jamais être interprétée comme 0 $.
- Le sous-total avant taxes reste distinct des taxes estimatives.
- SINJIRA™ ne choisit jamais automatiquement une zone fiscale pour la personne.
- Une estimation fiscale exige un profil publié et choisi explicitement.
- L’estimation fiscale est non contractuelle et non autoritative pour la facturation.
- Le prix, la livraison, les taxes réellement applicables et le total final devront être présentés puis acceptés séparément avant tout futur paiement.

## Verrous commerciaux

La réservation reste distincte d’une vente. Le contrat interdit qu’une évolution de ce parcours active implicitement :

- une vente;
- un checkout;
- un paiement;
- une conversion automatique d’une réservation en commande;
- une API transporteur ou un achat externe d’étiquette;
- une API fiscale externe.

## État de production au moment du contrat

- 0 fiche commerciale publiée;
- 0 zone de livraison publiée;
- 0 point de ramassage publié;
- 0 profil fiscal publié;
- 0 avis d’ouverture envoyé;
- vente, checkout, paiement et conversion automatique désactivés;
- API transporteur et achat externe d’étiquette désactivés;
- livraison toujours à la charge du client;
- ramassage toujours à 0 $ de frais de livraison.

Aucune migration Supabase n’est ajoutée par V24.5.30. Le ledger demeure à **163 migrations**.
