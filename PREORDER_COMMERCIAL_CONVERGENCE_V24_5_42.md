# SINJIRA™ V24.5.42 — Convergence de la préparation commerciale

## Objectif

Rendre cohérent le parcours de préparation du Livre I sans créer une nouvelle capacité commerciale.

La console des précommandes charge désormais explicitement l’éditeur fiscal indicatif V24.5.27 déjà existant et fournit un accès direct à la checklist V24.5.41 de préparation à une future vente.

## Parcours public déjà en place

Le module de livraison chargé par la page publique et par **Mes achats** importe déjà :

- `sinjira-preorder-cost-summary-v24-5-25.js` : prix officiel publié + estimation de livraison ou ramassage;
- `sinjira-preorder-tax-estimate-v24-5-27.js` : estimation fiscale indicative et total indicatif lorsqu’un profil fiscal vérifié est publié et choisi explicitement.

Aucune adresse exacte n’est requise pour une estimation de livraison. Une zone publiée suffit.

## Correction d’administration

`sinjira-admin-preorder-fulfillment-v24-5-6.js` charge maintenant :

- `sinjira-admin-preorder-tax-v24-5-27.js`;
- un lien visible vers `/admin/sinjira/precommandes-readiness.html`.

L’éditeur fiscal conserve son propre contrôle administrateur + MFA/AAL2. Les profils restent en brouillon tant qu’ils ne sont pas publiés séparément avec une source et une date d’effet vérifiées.

## Contrat financier inchangé

V24.5.42 n’ouvre aucune vente et n’ajoute aucun fournisseur externe.

Les invariants restent :

- réservation ≠ commande;
- aucun paiement prélevé;
- aucun checkout;
- aucune conversion automatique réservation → commande;
- frais de livraison à la charge du client;
- ramassage sur place : 0 $ de frais de livraison;
- estimations de livraison non contractuelles;
- estimations fiscales non contractuelles;
- `external_tax_api_enabled = false`;
- API transporteur externe désactivée;
- toute future transaction exige une nouvelle confirmation humaine et volontaire.

## Base de données

Aucune migration Supabase n’est nécessaire. Le ledger de production reste à **172 migrations**.

V24.5.42 ne crée ni prix, ni tarif de livraison, ni profil fiscal, ni point de ramassage. Elle rend seulement accessibles les outils préparatoires déjà existants.
