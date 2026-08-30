# SINJIRA™ V24.5.43 — Convergence du cache de la console des précommandes

## Objectif

Garantir que la console privée des précommandes charge bien les versions courantes de ses modules après les évolutions V24.5.36 à V24.5.42.

La page `/admin/sinjira/precommandes.html` utilisait encore d’anciens paramètres de cache sur quatre modules JavaScript alors que leurs fichiers avaient été enrichis ensuite, notamment avec le suivi opérationnel, la préparation logistique locale, l’éditeur fiscal indicatif et la checklist de préparation commerciale.

## Correction

Les quatre modules sont désormais chargés avec `?v=24.5.43` :

- `sinjira-admin-preorders-v24-5-4.js`;
- `sinjira-admin-preorder-workflow-v24-5-36.js`;
- `sinjira-admin-preorder-commercial-v24-5-5.js`;
- `sinjira-admin-preorder-fulfillment-v24-5-6.js`.

Le nom physique des fichiers reste inchangé afin de ne pas dupliquer leur logique. Seul le cache-buster est convergé.

## Invariants

V24.5.43 n’ajoute aucune capacité commerciale et n’applique aucune migration Supabase.

Les invariants restent :

- réservation ≠ commande;
- aucune vente activée;
- aucun checkout;
- aucun paiement;
- aucune conversion automatique;
- frais de livraison à la charge du client;
- ramassage sur place : 0 $ de frais de livraison;
- estimation de livraison non contractuelle;
- estimation fiscale non contractuelle;
- API transporteur externe désactivée;
- API fiscale externe désactivée;
- aucun courriel/SMS externe ajouté.

Le ledger production reste à **172 migrations**.
