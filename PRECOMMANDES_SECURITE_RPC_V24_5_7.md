# SINJIRA™ — Sécurité RPC des précommandes

**Version : V24.5.7**  
**Migration production : `20260822193403 sinjira_v24_5_7_preorder_rpc_and_index_hardening`**  
**Ledger production : 137 migrations**

## But

V24.5.7 durcit les lectures publiques des précommandes sans ouvrir l’accès direct aux tables commerciales et sans modifier les règles V24.5.3 à V24.5.6.

Les principes restent inchangés :

- réserver aujourd’hui ne signifie jamais consentir à payer demain;
- les frais de livraison d’un exemplaire expédié sont à la charge du client;
- le ramassage sur place comporte `0 $` de frais de livraison;
- une estimation de livraison est non contractuelle;
- aucune zone, aucun tarif ni aucune adresse de retrait ne sont inventés ou publiés automatiquement;
- aucune vente, aucun checkout, aucun paiement et aucune conversion automatique ne sont activés;
- aucune API de transporteur ou d’achat d’étiquette n’est activée.

## Frontière RPC publique

Les trois RPC publiques suivantes restent l’interface utilisée par le site :

- `public.product_preorder_commercial_info(text)`;
- `public.product_preorder_fulfillment_options(text)`;
- `public.product_preorder_shipping_estimate(text,text,integer)`.

Elles sont désormais `SECURITY INVOKER`.

La lecture privilégiée strictement nécessaire est isolée dans le schéma interne :

`preorder_public_internal`

Ce schéma n’est pas un schéma API public. Ses fonctions `SECURITY DEFINER` sont des lecteurs bornés : elles ne retournent que les champs explicitement destinés au public et respectent les états de publication.

Les tables sources restent scellées : aucun `SELECT`, `INSERT`, `UPDATE` ou `DELETE` direct n’est accordé à `anon` ou `authenticated` sur :

- `preorder_commercial_plans`;
- `preorder_fulfillment_settings`;
- `preorder_shipping_zones`;
- `preorder_pickup_points`.

## RLS des réservations

Les deux anciennes politiques SELECT permissives de `product_preorders` ont été remplacées par une politique unique :

`product_preorders_read`

Elle autorise la lecture uniquement lorsque l’utilisateur est propriétaire de la réservation ou qu’il satisfait au contrôle administrateur SINJIRA™.

Cette fusion ne donne aucun droit supplémentaire; elle évite simplement l’évaluation de deux politiques permissives concurrentes.

## Index de clés étrangères

V24.5.7 ajoute les index manquants signalés par l’advisor performance sur neuf clés étrangères existantes :

- modération : `reviewed_by`, `decided_by`, `reversed_by`;
- registre d’incidents de confidentialité : `created_by`, `updated_by`;
- gels juridiques de confidentialité : `created_by`, `user_id`;
- rencontres : `requested_by_profile_id`, `sender_profile_id`.

Après application, l’advisor ne signale plus de clé étrangère non indexée et ne signale plus de politiques SELECT permissives concurrentes sur `product_preorders`.

## Avertissements de sécurité restant à traiter séparément

L’advisor Supabase signale encore plusieurs RPC `SECURITY DEFINER` authentifiées dans d’autres modules historiques. Plusieurs sont intentionnellement des passerelles serveur qui vérifient l’identité, le rôle, la propriété, le MFA/AAL2 ou d’autres invariants. Elles ne doivent pas être converties ou révoquées en masse uniquement pour faire disparaître un avertissement de linter; chaque RPC exige un audit contractuel avant modification.

Les tables avec RLS activée et aucune politique peuvent également être volontairement scellées. Ajouter une politique permissive uniquement pour supprimer l’information du linter affaiblirait la sécurité.

La protection Supabase contre les mots de passe compromis est toujours signalée comme désactivée. Le connecteur actuellement disponible n’expose pas d’action de configuration Auth permettant de l’activer; cette limitation reste donc explicitement ouverte et ne doit pas être présentée comme corrigée.

## Gouvernance GitHub

Le workflow de gouvernance détecte les commits `main` sans PR, mais la protection serveur de la branche `main` n’est toujours pas activée par GitHub. Les outils disponibles ici ne fournissent pas d’action d’écriture pour les règles de branche. Cette limite reste distincte de V24.5.7.

## Services externes et domaine

V24.5.7 n’active aucun service payant, aucun transporteur, aucun paiement et ne modifie aucun DNS. Le domaine actif reste inchangé; `sinjira.com` demeure réservé pour une migration ultérieure explicitement autorisée.
