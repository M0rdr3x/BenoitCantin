# SINJIRA™ V24.5.33 — confirmation imprimable locale de précommande

## Objectif

Permettre à une personne qui possède une réservation du Livre I de conserver une copie lisible de son état de réservation sans créer un nouveau document serveur, sans transférer de données à un fournisseur externe et sans ajouter de collecte personnelle.

## Fonctionnement

Le bouton **« Imprimer / enregistrer en PDF »** apparaît dans l’état de précommande chargé depuis le Compte SINJIRA™.

Le navigateur ouvre une vue temporaire locale contenant seulement les données déjà autorisées par V24.5.32, puis ouvre le dialogue natif d’impression. La personne peut alors imprimer sur papier ou choisir la fonction « Enregistrer en PDF » fournie par son système.

SINJIRA™ ne génère, ne téléverse et ne conserve aucun PDF dans cette étape. Aucun service PDF externe n’est appelé.

## Données de la copie

La copie locale peut contenir :

- la référence de réservation indépendante `PR-…`;
- le nom du roman;
- le format et la quantité souhaités;
- la préférence de réception;
- l’état réservé ou annulé;
- l’état « aucun paiement / aucun engagement financier »;
- la version et la date des conditions réellement confirmées, lorsqu’elles existent;
- les dates de création et de dernière mise à jour;
- la date locale de génération de la copie.

Elle ne contient aucun UUID, courriel, adresse de livraison, adresse de facturation, donnée bancaire, identifiant de compte ou autre identifiant technique interne.

## Transparence commerciale

La copie dit explicitement qu’elle n’est :

- ni une facture;
- ni un reçu de paiement;
- ni une commande;
- ni une promesse de prix.

Pour une édition physique expédiée, les frais de livraison restent à la charge du client. Lorsqu’un ramassage sur place sera disponible, il ajoute 0 $ de frais de livraison. Les montants finaux devront toujours être présentés et acceptés séparément avant un futur paiement.

## Confidentialité

La fenêtre d’impression est générée depuis les données déjà présentes dans le navigateur. Elle ne charge aucune ressource distante et n’utilise aucun script inline. SINJIRA™ n’enregistre pas le fait qu’une personne a imprimé ou enregistré la copie.

## Services payants

V24.5.33 n’active aucun paiement, checkout, vente, stockage PDF, courriel, SMS, API transporteur, API fiscale ni fournisseur externe payant.

Aucune migration Supabase supplémentaire n’est nécessaire : le ledger production reste à **165 migrations**, avec V24.5.32 comme dernière migration de données de ce parcours.
