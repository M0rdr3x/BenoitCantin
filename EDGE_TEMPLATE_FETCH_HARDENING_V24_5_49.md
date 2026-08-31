# SINJIRA™ V24.5.49 — Verrouillage du modèle PDF Fracture

## Objectif

Durcir le chargement du modèle PDF utilisé par `send-game-report` sans modifier les droits métier, le contenu de la fiche, le parcours de téléchargement ni la politique de services externes.

## Frontière réseau du modèle

Le modèle PDF ne peut être chargé que depuis :

- origine HTTPS exacte : `https://www.benoitcantin.com`;
- préfixe de chemin : `/projets/sinjira/jeux/fracture-du-reseau-mere/documents/`;
- extension `.pdf`;
- aucun identifiant/mot de passe dans l’URL;
- aucun paramètre de requête;
- aucun fragment.

Même si `REPORT_TEMPLATE_URL` est défini côté serveur, une valeur qui sort de cette frontière est refusée.

## Redirections et taille

Le chargement utilise `redirect: 'error'` : une redirection HTTP n’est jamais suivie automatiquement.

Le modèle est limité à **15 MiB** :

- la taille déclarée est contrôlée lorsqu’elle existe;
- la taille réellement reçue est contrôlée après téléchargement;
- un corps vide est refusé;
- les cinq premiers octets doivent être `%PDF-`.

Ces contrôles évitent qu’une mauvaise configuration du modèle ne transforme cette fonction en passerelle réseau arbitraire ou en téléchargement mémoire non borné.

## Confidentialité existante conservée

V24.5.48 reste applicable :

- corps de requête `send-game-report` limité à 220 000 octets réels;
- réponses contenant le PDF base64 en `private, no-store`;
- `nosniff` et `no-referrer`;
- journalisation d’une session uniquement si elle appartient au compte authentifié;
- le téléchargement direct reste disponible selon le contrat existant.

## Services externes payants

`PAID_EXTERNAL_SERVICES_ENABLED=false` demeure obligatoire.

Le code d’intégration courriel peut rester préparé, mais il ne peut pas contacter le fournisseur tant que le verrou serveur reste à `false`. V24.5.49 n’active aucun paiement, checkout, vente, transporteur, IA distante, courriel/SMS payant ou autre fournisseur facturable.

## Base de données

V24.5.49 n’ajoute **aucune migration Supabase**.

Le ledger production demeure à **174 migrations**, dont la dernière est :

`20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening`

## Production Edge

`send-game-report` est déployée en production en **version 6** avec cette frontière de modèle. `verify_jwt=false` reste intentionnel pour le contrat custom-auth/public existant; aucune élévation de droit n’est ajoutée.
