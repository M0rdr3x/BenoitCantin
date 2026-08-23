# SINJIRA™ V24.5.26 — Garde de préparation à une future vente

## Principe

**L’humain avant tout.** V24.5.26 vérifie que les informations nécessaires sont suffisamment complètes avant d’envisager une future ouverture manuelle des ventes du Livre I. Cette version ne contient aucune action d’ouverture de vente, aucun checkout et aucun paiement.

Migration production : `20260823171121 sinjira_v24_5_26_preorder_sale_readiness_guard`.

Le ledger Supabase passe à **157 migrations**.

## Checklist administrateur

La RPC `admin_preorder_sale_readiness(text)` est un wrapper public `SECURITY INVOKER`. Elle délègue à `preorder_readiness_internal.sale_readiness(text)`, hors du schéma API public. L’implémentation interne exige `private.require_sinjira_admin_aal2()`.

La préparation n’est déclarée complète que si :

- une fiche commerciale a été publiée;
- au moins une édition réellement offerte possède un prix officiel;
- la date de sortie est publiée;
- les conditions sont suffisamment renseignées;
- l’information de disponibilité / production est renseignée;
- le nom de l’édition correspond au prix publié;
- si une édition papier est offerte, au moins une option de réception est effectivement publiée : estimation de livraison valide ou point de ramassage;
- les frais de livraison restent à la charge du client;
- le ramassage garde **0 $ de frais de livraison**;
- aucune API transporteur ni achat d’étiquette externe n’est activé;
- vente, checkout, paiement, livraison externe et conversion automatique restent désactivés pendant la préparation.

Un résultat `ready_for_future_manual_opening=true` signifie uniquement que la préparation informationnelle est complète. Il ne déclenche rien et ne constitue pas une autorisation d’ouvrir les ventes.

## Transparence des coûts et taxes

Le résumé public du coût continue d’utiliser exclusivement des prix et fourchettes officiellement publiés. Il affiche maintenant explicitement un **sous-total estimatif avant taxes**.

Les taxes applicables, le cas échéant, **ne sont pas calculées par SINJIRA dans cette version**. Aucun taux fiscal n’est inventé. Le montant final, incluant les taxes applicables s’il y en a, devra être déterminé et présenté à la personne avant tout futur paiement.

Cette précision ne constitue pas un avis fiscal ou juridique.

## Livraison et ramassage

- Les frais de livraison sont à la charge du client.
- Une estimation de livraison reste non contractuelle.
- Aucune adresse exacte n’est demandée pour l’estimation par zone.
- Le ramassage sur place conserve 0 $ de frais de livraison.
- Un point de ramassage ne peut être utilisé que s’il a été explicitement publié.

## Services externes

Aucun Stripe, PayPal, transporteur, service d’étiquettes, courriel/SMS payant, IA distante payante, DNS, passkey ou publication payante n’est activé par V24.5.26.

La protection serveur GitHub de `main` reste un prérequis externe tant que l’action de ruleset/branch protection n’est pas exposée par les outils disponibles.
