# SINJIRA™ V24.5.27 — Estimation fiscale indicative avant vente

## Principe

V24.5.27 prépare une estimation fiscale informative pour le Livre I sans ouvrir les ventes et sans transformer SINJIRA en moteur de facturation fiscale.

Une estimation fiscale est une aide à la compréhension du coût possible. Elle n’est jamais une facture, un avis fiscal, une déclaration de taxe, un consentement à payer ou une autorisation de débit.

## Aucune donnée inventée

Aucun profil fiscal ni aucun taux n’est créé automatiquement. L’administration doit saisir les taux seulement après vérification humaine.

Un profil ne peut être publié que si :

- il est actif;
- au moins un taux est défini;
- une référence/source de vérification est indiquée;
- une date d’effet est indiquée;
- l’administrateur est authentifié avec MFA/AAL2.

Toute modification d’un profil publié le remet en brouillon en supprimant `published_at`. Une nouvelle publication humaine est nécessaire.

Les longueurs sont aussi bornées côté serveur pour les libellés, subdivisions, références de source et notes publiques. Les paramètres `NULL` ou hors contrat sont refusés par la fonction d’estimation plutôt que d’être interprétés silencieusement.

## Précision

Les taux papier, numérique et livraison sont stockés en points de base décimaux `numeric(10,3)`. 100 points de base correspondent à 1 %. Cette précision permet notamment de représenter un taux de 14,975 % sans imposer un arrondi à 14,98 % ou 14,97 %.

Les taux peuvent différer entre papier, numérique et livraison parce que l’application fiscale peut dépendre du type de bien ou de service et de la juridiction. SINJIRA ne suppose pas qu’ils sont identiques.

## Confidentialité

L’estimation utilise un profil fiscal publié choisi par la personne. Elle ne demande ni n’enregistre une adresse exacte pour ce calcul.

La table `preorder_tax_estimate_profiles` est protégée par RLS et n’est pas directement accessible à `anon` ou `authenticated`. Les lectures publiques passent uniquement par des RPC limités aux profils actifs et publiés.

## Frontière de sécurité

Les implémentations privilégiées résident dans `preorder_tax_internal`. Les fonctions exposées dans `public` sont des wrappers `SECURITY INVOKER`.

Les opérations administratives exigent `private.require_sinjira_admin_aal2()` et ne sont pas exécutables par `anon`.

Les deux fonctions publiques d’estimation peuvent être utilisées sans compte, mais ne retournent que des profils publiés et les montants indicatifs qui en découlent.

## Contrat commercial

V24.5.27 conserve toutes les protections existantes :

- `sales_enabled = false`;
- `checkout_enabled = false`;
- `payment_enabled = false`;
- `external_fulfillment_enabled = false`;
- `auto_conversion_allowed = false`;
- livraison à la charge du client;
- ramassage sur place à 0 $ de frais de livraison;
- aucune conversion automatique de réservation en commande.

L’estimation fiscale n’est calculée que lorsque la fiche commerciale publiée et, lorsqu’elle est requise, la fourchette de livraison publiée sont disponibles. Si une donnée manque, aucun montant n’est inventé.

La checklist `admin_preorder_sale_readiness` exige désormais au moins un profil fiscal indicatif publié et vérifié avant de pouvoir afficher `ready_for_future_manual_opening = true`. Cela ne garantit pas qu’un taux donné s’applique à chaque acheteur : la vérification fiscale finale reste obligatoire au moment d’une future transaction.

## Pas de service externe payant

`external_tax_api_enabled = false` et `billing_authoritative = false` sont des invariants de cette version. Aucune API fiscale externe, aucun paiement, aucun checkout, aucune API transporteur et aucun service payant n’est activé.

La source administrative est une référence textuelle : SINJIRA ne télécharge pas automatiquement un document externe et ne contacte aucun fournisseur fiscal.

## Confirmation finale obligatoire

Toute estimation est `estimate_nonbinding = true` et `final_tax_confirmation_required = true`.

Avant une future transaction, le prix, la livraison, les taxes réellement applicables et le montant final devront être recalculés ou vérifiés selon les règles alors en vigueur, présentés clairement à la personne, puis acceptés dans une action de paiement distincte.

## État production

V24.5.27 correspond à trois migrations :

- `20260823195851 sinjira_v24_5_27_preorder_tax_estimate_preparation`;
- `20260823200303 sinjira_v24_5_27_tax_rate_precision_hardening`;
- `20260823201127 sinjira_v24_5_27_tax_input_and_readiness_hardening`.

Le ledger production contient **160 migrations**.

Au déploiement, aucun profil fiscal n’est créé ni publié automatiquement.
