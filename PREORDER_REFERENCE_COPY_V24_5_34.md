# SINJIRA™ V24.5.34 — copie locale de la référence de précommande

## Objectif

Permettre à la personne de copier facilement sa référence de réservation `PR-…` pour la conserver dans ses propres notes ou la retrouver plus tard.

La référence reste une référence de réservation indépendante. Elle n’est ni un UUID, ni un identifiant technique du compte, ni un numéro de commande.

## Fonctionnement

Le bouton **« Copier la référence »** apparaît uniquement après le chargement de l’état de réservation.

L’action est déclenchée par un clic utilisateur :

- le navigateur utilise `navigator.clipboard.writeText()` lorsqu’il est disponible en contexte sécurisé;
- un repli local par champ temporaire est utilisé lorsque l’API Clipboard n’est pas disponible;
- seul le texte au format `PR-[0-9A-F]{16}` peut être copié;
- un message `aria-live` confirme l’action sans exposer d’autre donnée.

## Confidentialité

La copie n’envoie rien au serveur et n’écrit rien dans `localStorage`, `sessionStorage`, IndexedDB ou une base distante. Aucun événement de copie n’est journalisé par SINJIRA™.

Aucun UUID, courriel, adresse de livraison, adresse de facturation, donnée bancaire, identifiant de compte ou identifiant interne de produit n’est copié.

## Compatibilité

Le bouton fonctionne avec l’API Clipboard moderne et possède un repli local pour les navigateurs qui ne l’exposent pas. La confirmation imprimable V24.5.33 reste disponible séparément.

## Commerce

Cette amélioration ne transforme pas une réservation en commande. Aucun paiement, checkout, vente, fournisseur de courriel/SMS, stockage PDF, transporteur ou API fiscale n’est activé.

Les frais de livraison d’un livre physique restent à la charge du client et le ramassage sur place ajoute 0 $ de frais de livraison lorsqu’il est disponible.

## Base de données

V24.5.34 n’ajoute aucune migration Supabase. Le ledger production reste à **167 migrations**. La dernière migration de production reste `20260830001742 sinjira_v24_5_32_user_rights_redundant_boundary_cleanup`.
