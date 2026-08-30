# SINJIRA V24.5.41 — Checklist de préparation à une future vente

## But

Exposer à l’administration une vue **strictement en lecture seule** du moteur `admin_preorder_sale_readiness` déjà présent en production.

Cette version ne crée aucun nouveau moteur de décision et n’ajoute aucune capacité d’ouverture de vente.

## Accès

La page `/admin/sinjira/precommandes-readiness.html` exige :

1. un compte authentifié;
2. le rôle administrateur SINJIRA;
3. MFA/AAL2;
4. le contrôle serveur déjà présent dans `preorder_readiness_internal.sale_readiness` via `private.require_sinjira_admin_aal2()`.

## Vérifications affichées

La checklist indique notamment :

- fiche commerciale publiée;
- prix papier et/ou numérique;
- date de sortie;
- résumé des conditions;
- disponibilité / production;
- réception du papier;
- estimation de livraison;
- point de ramassage;
- profil fiscal indicatif;
- nombre de zones, points et profils publiés.

## Verrous affichés

La page affiche explicitement que les éléments suivants doivent rester désactivés pendant la préparation :

- ventes;
- checkout;
- paiement;
- livraison externe;
- conversion automatique réservation → commande;
- API transporteur;
- achat externe de livraison.

Elle vérifie aussi :

- livraison à la charge du client;
- ramassage avec 0 $ de frais de livraison;
- taxes non calculées automatiquement par SINJIRA.

## Autorité humaine

Même si `ready_for_future_manual_opening` devient vrai, cela signifie uniquement que les informations préparatoires sont complètes. Une décision humaine séparée reste obligatoire avant toute future ouverture.

Aucun bouton « ouvrir les ventes », « checkout », « activer le paiement » ou « convertir les réservations » n’existe dans cette page.

## Données et services externes

La checklist n’affiche ni UUID, ni courriel, ni téléphone, ni adresse personnelle, ni carte bancaire.

Aucun Stripe, PayPal, transporteur, courriel, SMS ou autre fournisseur externe n’est ajouté ou activé.

## Base de données

V24.5.41 ne nécessite aucune migration Supabase. Le ledger reste à **172 migrations**, clôturé par :

`20260830035043 sinjira_v24_5_38_preorder_logistics_queue`
