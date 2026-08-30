# SINJIRA V24.5.39 — Feuille logistique imprimable locale

## But

Permettre à l’administration SINJIRA de préparer ou imprimer une feuille de travail pour le Livre I à partir de la file logistique V24.5.38, sans créer de commande, sans paiement et sans exporter de données personnelles supplémentaires.

## Fonctionnement local

La feuille est construite dans une fenêtre temporaire du navigateur à partir des données déjà chargées dans la console admin. Elle peut être imprimée ou enregistrée en PDF avec la fonction d’impression du navigateur.

Aucun fichier n’est téléversé vers SINJIRA, Supabase, un transporteur ou un fournisseur externe. Aucun nouvel objet de stockage serveur n’est créé.

## Données autorisées

La feuille peut contenir uniquement :

- référence publique de réservation `PR-…`;
- produit;
- quantité;
- format demandé;
- mode de réception;
- nom public et ville du point de retrait, lorsque le choix est le ramassage;
- état de suivi administratif;
- version et date de confirmation des conditions.

Elle ne contient ni UUID, ni nom réel, ni courriel, ni téléphone, ni adresse d’expédition ou de facturation, ni donnée bancaire.

## Résumé logistique

La feuille affiche aussi uniquement des agrégats non personnels :

- unités papier à prévoir;
- nombre de réservations avec livraison;
- nombre de réservations avec ramassage;
- nombre de réservations dont le mode reste à décider;
- portée du filtre utilisé (actives seulement ou toutes les réservations affichées);
- date/heure de génération locale.

## Rappels imprimés

La feuille indique explicitement qu’elle est un document interne préparatoire et non une commande ou une preuve de paiement.

- livraison : frais à la charge du client;
- ramassage : 0 $ de frais de livraison;
- aucun prix final ni paiement n’est déclenché;
- aucune API transporteur ni achat d’étiquette;
- aucune conversion automatique réservation → commande.

## Sécurité

La feuille dépend de la file V24.5.38, elle-même protégée par administration + MFA/AAL2 et une réponse de données minimales. Toutes les valeurs insérées dans le document imprimable sont échappées avant rendu.

La génération utilise uniquement les primitives locales du navigateur (`window.open`, DOM local et `window.print`). Elle ne doit utiliser ni `fetch`, ni `XMLHttpRequest`, ni `sendBeacon`, ni courriel, ni API externe.

## Base de données

V24.5.39 ne nécessite aucune migration Supabase. Le ledger reste à **172 migrations**, avec V24.5.38 comme dernière migration production :

`20260830035043 sinjira_v24_5_38_preorder_logistics_queue`
