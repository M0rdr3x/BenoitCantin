# SINJIRA V24.5.53 — Transmission de contribution sans UUID exposé

## Objectif

Durcir `submit-game-contribution` sans modifier le consentement du Programme Contributeur ni les données de fin de partie réellement utilisées pour l’équilibrage.

## Production

`submit-game-contribution` est déployée en production en version **4** avec `verify_jwt=true`.

V24.5.53 n’ajoute **aucune migration Supabase**. Le ledger reste à **174 migrations**.

## Confidentialité UUID

La RPC serveur `record_sinjira_contribution(...)` retourne un UUID interne et reste exécutable uniquement par `service_role`.

Depuis V24.5.53 :

- cet UUID n’est plus retourné au navigateur ;
- la réponse publique confirme seulement `submitted: true` ;
- aucun identifiant de contribution interne n’est nécessaire au parcours utilisateur.

## Surface HTTP

- `POST` uniquement ;
- JWT et utilisateur authentifié obligatoires ;
- `application/json` obligatoire ;
- corps limité à **2 048 octets**, sur taille déclarée et taille réellement lue ;
- `session_id` doit être un UUID valide ;
- JSON invalide et session invalide sont rejetés avant toute requête métier.

## Minimisation SQL

La session de jeu n’est plus lue avec `select('*')`. Seuls les champs nécessaires au calcul des métriques sont sélectionnés.

La session doit appartenir à l’utilisateur authentifié et le consentement contributeur doit toujours être actif.

## Réponses privées

Toutes les réponses applicatives portent :

- `Cache-Control: private, no-store, max-age=0` ;
- `Pragma: no-cache` ;
- `X-Content-Type-Options: nosniff` ;
- `Referrer-Policy: no-referrer`.

## Coûts

Aucun paiement, checkout, vente, transporteur, courriel/SMS payant, IA distante payante ou autre fournisseur facturable n’est activé par V24.5.53.
