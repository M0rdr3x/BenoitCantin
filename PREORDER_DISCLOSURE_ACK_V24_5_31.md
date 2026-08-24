# SINJIRA™ V24.5.31 — Accusé de compréhension des précommandes

## Principe

La transparence affichée avant la précommande doit aussi être comprise explicitement au moment où la réservation est créée, modifiée ou réactivée.

**Réserver aujourd’hui ne signifie jamais consentir à payer demain.**

L’accusé V24.5.31 n’est pas un consentement financier. Il confirme uniquement que la personne a compris les limites de la phase de réservation.

## Texte que la personne doit comprendre

Avant d’enregistrer une réservation ou une mise à jour, la personne confirme explicitement que :

- aucun paiement n’est prélevé aujourd’hui;
- une réservation n’est pas une commande;
- pour une édition physique expédiée, les frais de livraison seront à la charge du client;
- le ramassage sur place, lorsqu’un point public sera disponible, ajoute **0 $ de frais de livraison**;
- les estimations de livraison et de taxes sont indicatives et non contractuelles;
- le prix, la livraison, les taxes réellement applicables et le total final devront être présentés puis acceptés séparément avant tout futur paiement.

La case n’est jamais précochée. Une nouvelle réservation, une modification ou une réactivation exige une confirmation actuelle.

## Verrou serveur

La nouvelle passerelle `product_preorder_reserve_confirmed(...)` exige :

- `p_disclosure_version = 'preorder-disclosure-v24.5.31'`;
- `p_disclosure_acknowledged = true`;
- un compte authentifié;
- les validations historiques de produit, format et quantité.

L’ancien `product_preorder_reserve(...)` reste présent uniquement pour échouer de façon sûre avec `PREORDER_DISCLOSURE_REQUIRED`. Il ne peut plus créer ou mettre à jour une réservation sans l’accusé V24.5.31.

Le wrapper public du nouveau RPC est `SECURITY INVOKER`; l’implémentation privilégiée reste dans `preorder_user_internal`. `anon` n’a aucun droit `EXECUTE`.

## Minimisation

La table `product_preorders` conserve seulement :

- `disclosure_version`;
- `disclosure_acknowledged_at`.

Les réservations historiques antérieures à V24.5.31 restent `NULL/NULL`; elles ne sont jamais rétroactivement marquées comme ayant accepté un texte qu’elles n’ont pas vu.

Aucun historique détaillé supplémentaire, aucune adresse, aucune donnée bancaire et aucune donnée de facturation n’est ajouté.

## Garde-fous commerciaux inchangés

V24.5.31 n’active pas :

- les ventes;
- le checkout;
- les paiements;
- la conversion automatique d’une réservation en commande;
- une API transporteur;
- une API fiscale;
- un service externe payant.

Les estimations déjà préparées restent non contractuelles et le ramassage reste à 0 $ de frais de livraison.

## Production

Migration appliquée :

`20260824215053 sinjira_v24_5_31_preorder_disclosure_acknowledgement`

Le ledger Supabase passe à **164 migrations**.
