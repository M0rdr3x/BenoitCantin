# SINJIRA™ V24.5.50 — Remise Histoire de vie sans jeton dans l’URL

## Principe humain

La remise posthume reste une conséquence d’un choix explicite de la personne dans son **Histoire de vie**. Elle ne donne aucun accès au Registre des Consciences, ne révèle aucun secret non autorisé et ne crée aucun clone IA posthume.

La vérification du décès, la période de sécurité, la contestation, la deuxième validation humaine et les destinataires autorisés restent inchangés.

## Problème corrigé

L’ancien lien de remise plaçait le jeton opaque dans une query string (`?token=...`). Même avec `Referrer-Policy: no-referrer`, un secret placé dans une URL peut être conservé dans l’historique ou certains journaux techniques.

V24.5.50 retire le secret de l’URL transmise au serveur.

## Nouveau protocole

1. `life-story-export` génère un jeton aléatoire de **256 bits**.
2. Seul son hash SHA-256 est conservé en base.
3. Le lien remis au destinataire prend la forme :
   `https://www.benoitcantin.com/histoire-de-vie/remise.html#<jeton>`
4. Le fragment `#...` n’est pas transmis au serveur HTTP lors du chargement de la page.
5. Le JavaScript local lit le fragment puis appelle immédiatement `history.replaceState()` pour le retirer de la barre d’adresse.
6. Le jeton est ensuite envoyé uniquement dans un petit corps JSON par **POST** vers `life-story-delivery`.
7. La fonction Edge refuse les requêtes GET, toute query string, les origines non approuvées, les contenus non JSON et les corps trop volumineux.

## Validation du PDF

Avant de consommer un téléchargement, `life-story-delivery` vérifie :

- lien présent et hash correct;
- non révoqué;
- non expiré;
- limite de téléchargements non atteinte;
- export à l’état `generated` ou `delivered`;
- bucket privé exact `sinjira-life-story-exports`;
- fichier non vide;
- taille maximale **15 MiB**;
- signature `%PDF-`.

Le compteur est ensuite enregistré par `service_life_story_register_download`, qui revalide atomiquement révocation, expiration et limite avant l’incrément.

## Confidentialité navigateur

La page `/histoire-de-vie/remise.html` :

- est `noindex,nofollow,noarchive,nosnippet`;
- applique `no-referrer`;
- utilise une CSP restrictive;
- ne charge aucun analytique, pixel ou fournisseur externe;
- ne stocke pas le jeton dans `localStorage`, `sessionStorage` ou un cookie;
- ne transmet le jeton qu’à la fonction Supabase officielle;
- vérifie aussi type PDF, taille et signature côté navigateur avant le téléchargement.

## Réponses Edge

Les réponses utilisent notamment :

- `Cache-Control: private, no-store, max-age=0`;
- `Pragma: no-cache`;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: no-referrer`;
- `X-Frame-Options: DENY`;
- une CSP fermée sur la réponse.

Les erreurs restent génériques et ne journalisent jamais le jeton.

## État production au moment du changement

Avant le changement de protocole :

- 0 lien de remise existant;
- 0 lien actif;
- 0 export téléchargeable;
- 0 dossier posthume ouvert.

Il n’y avait donc aucun lien utilisateur existant à invalider.

## Déploiement

- `life-story-delivery` : version 2, `verify_jwt=false` volontairement, authentification custom par jeton opaque.
- `life-story-export` : version 3, `verify_jwt=true`, administration + MFA selon le contrat existant.

V24.5.50 ne modifie pas le schéma SQL. Le ledger Supabase reste à **174 migrations**, dernière migration `20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening`.

## Coûts et services externes

Aucun paiement, checkout, vente, courriel/SMS payant, IA distante, transporteur, stockage externe ou fournisseur facturable n’est activé par V24.5.50.
