# SINJIRA V24.5.40 — Durcissement de la feuille logistique locale

## But

Durcir la feuille logistique imprimable introduite en V24.5.39 sans modifier les données, les précommandes, le suivi administratif ni le contrat commercial.

## Fenêtre locale isolée

La feuille reste générée uniquement dans une fenêtre temporaire du navigateur à partir des données minimales déjà chargées dans la console administration + MFA/AAL2.

V24.5.40 ajoute :

- une Content Security Policy locale restrictive avec `default-src 'none'`;
- `connect-src 'none'`, donc aucun appel réseau depuis la feuille;
- `object-src 'none'`, `frame-src 'none'` et `base-uri 'none'`;
- `form-action 'none'`;
- `Referrer-Policy: no-referrer`;
- aucun gestionnaire `onclick` ou autre script inline dans le document;
- le bouton d’impression est relié par `addEventListener` depuis le runtime déjà authentifié;
- `window.opener` est supprimé après la construction du document.

## Données inchangées

La feuille peut toujours contenir uniquement les données minimales V24.5.38–39 : référence `PR-…`, produit, quantité, format, mode de réception, point de retrait public/ville si applicable, état de suivi et version/date des conditions.

Elle ne contient ni UUID, ni nom réel, ni courriel, ni téléphone, ni adresse d’expédition/facturation, ni donnée bancaire.

## Contrat commercial inchangé

- livraison : frais à la charge du client;
- ramassage : 0 $ de frais de livraison;
- aucune vente;
- aucun checkout;
- aucun paiement;
- aucune conversion automatique réservation → commande;
- aucune API transporteur;
- aucun fournisseur externe payant.

## Base de données

V24.5.40 ne nécessite aucune migration Supabase. Le ledger reste à **172 migrations**, clôturé par :

`20260830035043 sinjira_v24_5_38_preorder_logistics_queue`

Les INFO `unused_index` ne justifient pas la suppression automatique d’index de clés étrangères ou d’index encore peu sollicités. Les tables volontairement scellées avec RLS sans politique directe restent fermées plutôt que d’être ouvertes artificiellement pour satisfaire un linter.
