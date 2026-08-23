# SINJIRA™ V24.5.25 — Résumé du coût avant achat

## Objectif

Donner une information utile avant toute future commande du Livre I sans ouvrir la vente ni activer de service payant.

## Règles utilisateur

- Les frais de livraison seront à la charge du client.
- Le prix du livre n’est affiché dans le résumé que s’il provient de `product_preorder_commercial_info` et a été publié officiellement.
- Une estimation de livraison n’est affichée que si une zone publiée retourne une fourchette valide via `product_preorder_shipping_estimate`.
- L’estimation est non contractuelle et le coût final doit être confirmé avant un futur achat.
- Le calculateur n’exige et ne conserve aucune adresse exacte; une zone publiée suffit.
- Le ramassage sur place ajoute **0 $ de frais de livraison**. S’il n’existe encore aucun point de retrait publié, le lieu reste explicitement à confirmer.
- Un total estimatif n’est calculé que lorsque toutes les données nécessaires sont présentes et dans la même monnaie.
- Une donnée SQL/JSON absente (`null`) n’est jamais convertie en faux prix ou faux tarif de 0 $.
- Une réservation reste distincte d’une vente et aucun paiement n’est prélevé maintenant.

## Architecture

V24.5.25 est **frontend-only**. Elle réutilise les RPC publiques déjà durcies :

- `product_preorder_commercial_info`
- `product_preorder_fulfillment_options`
- `product_preorder_shipping_estimate`

Le module `sinjira-preorder-cost-summary-v24-5-25.js` est chargé depuis le module de livraison déjà utilisé par la page publique du Livre I et par `compte/mes-achats.html`.

Aucune migration Supabase n’est ajoutée. Le ledger production reste à **156 migrations**, dernière migration `20260823044507 sinjira_v24_5_24_security_definer_reconstruction_convergence`.

## Services externes

Aucun Stripe, PayPal, API de transporteur, courriel/SMS payant ou autre fournisseur externe n’est activé. Le résumé est purement informatif et local au parcours SINJIRA™.
