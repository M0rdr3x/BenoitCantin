# SINJIRA™ V24.5.44 — Convergence du cache public des précommandes

## Objectif

Forcer les deux surfaces utilisateur de précommande du Livre I à charger les versions courantes des styles et modules de précommande après les évolutions V24.5.30–V24.5.43.

Les surfaces concernées sont :

- `/compte/mes-achats.html`;
- `/projets/sinjira/romans/precommande.html`.

Les trois feuilles de style et les trois modules JavaScript de précommande utilisent désormais le cache-buster `?v=24.5.44` sur ces deux pages.

## Contrat utilisateur inchangé

Cette correction ne change aucune règle commerciale :

- une réservation n’est pas une commande;
- aucun paiement n’est prélevé pendant la phase de précommande;
- aucun checkout n’est actif;
- aucune conversion automatique réservation → commande n’est permise;
- les frais de livraison d’un livre physique expédié sont à la charge du client;
- le ramassage sur place, lorsqu’un point public confirmé est disponible, ajoute **0 $ de frais de livraison**;
- les estimations de livraison et de taxes restent indicatives et non contractuelles;
- le prix, la livraison, les taxes applicables et le total final devront être présentés puis acceptés séparément avant tout futur paiement;
- aucune donnée bancaire, adresse de facturation ou adresse de livraison n’est collectée dans cette phase de réservation.

## Services externes

V24.5.44 n’active aucun fournisseur externe : aucun paiement, transporteur, API fiscale, courriel/SMS externe ou service payant.

## Base de données

Aucune migration Supabase n’est nécessaire. Le ledger production reste à **172 migrations**.

V24.5.44 est uniquement une convergence de cache navigateur sur les surfaces utilisateur.