# SINJIRA V24.5.51 — Durcissement HTTP de la suppression de compte

## Objectif

Durcir la surface HTTP de `delete-player-account` sans modifier le droit à la suppression, les obligations de conservation, la protection MFA ni le comportement métier existant.

## Production

`delete-player-account` est déployée en production en version **4** avec `verify_jwt=true`.

V24.5.51 n’ajoute **aucune migration Supabase**. Au moment de cette livraison, le ledger reste à **174 migrations**.

## Requête

La fonction accepte uniquement :

- `POST` ;
- un corps `application/json` ;
- au maximum **1 024 octets**, vérifiés sur `Content-Length` lorsqu’il est présent et sur les octets réellement lus ;
- un objet JSON valide ;
- la confirmation exacte `SUPPRIMER MON COMPTE`.

La lecture directe `await req.json()` sans borne est interdite par le contrat CI V24.5.51.

## Réponses privées

Toutes les réponses applicatives portent notamment :

- `Cache-Control: private, no-store, max-age=0` ;
- `Pragma: no-cache` ;
- `X-Content-Type-Options: nosniff` ;
- `Referrer-Policy: no-referrer`.

Aucune réponse de suppression ne doit être mise en cache par un intermédiaire ou un navigateur.

## Garde-fous humains et juridiques conservés

V24.5.51 ne modifie pas les protections existantes :

- utilisateur authentifié obligatoire ;
- suppression self-service interdite pour le compte propriétaire/administrateur ;
- vérification d’une conservation légale avant toute opération destructive ;
- si un facteur MFA vérifié permet une session AAL2, AAL2 est exigé ;
- phrase de confirmation explicite obligatoire ;
- révocation des contributions liée uniquement à l’utilisateur authentifié ;
- suppression des fichiers personnels connus avant clôture du compte Auth.

La protection MFA reste progressive afin de ne pas transformer l’exercice du droit à l’effacement en obligation de souscrire ou d’enrôler un service externe.

## Coûts et services externes

Aucun paiement, checkout, vente, transporteur, IA distante payante, courriel/SMS payant ou autre fournisseur facturable n’est activé par V24.5.51.
