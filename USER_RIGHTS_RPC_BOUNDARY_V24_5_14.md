# SINJIRA V24.5.14 — Frontière RPC droits utilisateur

## Objectif

V24.5.14 retire du schéma API public les implémentations `SECURITY DEFINER` de 5 RPC utilisateur liées à la confidentialité et aux appels de modération, tout en conservant les noms, signatures, types de retour et droits d’usage existants.

L’objectif est de réduire la surface privilégiée exposée par `/rest/v1/rpc/*` sans modifier les droits de la personne ni le fonctionnement des appels humains.

## RPC concernées

Les **5 RPC** sont :

- `privacy_create_request`
- `privacy_export_my_extended_data`
- `privacy_my_requests`
- `moderation_my_decisions`
- `moderation_submit_appeal`

## Nouvelle frontière

Les implémentations privilégiées sont déplacées dans le schéma non public :

`sinjira_user_rights_internal`

Les fonctions de même nom conservées dans `public` sont uniquement des wrappers `SECURITY INVOKER`.

Contrat de production vérifié :

- **5/5** wrappers publics `SECURITY INVOKER`;
- **0/5** wrapper public `SECURITY DEFINER`;
- **0/5** fonction publique exécutable par `anon`;
- **5/5** fonctions publiques exécutables par `authenticated`;
- **5/5** fonctions publiques exécutables par `service_role`;
- **5/5** implémentations internes demeurent `SECURITY DEFINER`;
- **5/5** implémentations internes conservent leur contrôle `auth.uid()`.

## Droits humains et appels

Cette migration ne change pas les règles métier.

- Une personne conserve son droit de créer une demande de confidentialité.
- Une personne conserve son accès à ses propres demandes et à son export étendu autorisé.
- Une personne conserve l’accès aux décisions de modération qui la concernent.
- `moderation_submit_appeal` demeure le chemin d’appel utilisateur.
- L’appel demeure destiné à une **révision humaine**; aucune décision irréversible n’est transférée à une IA.
- Aucune nouvelle donnée personnelle n’est collectée.

Le principe reste : **L’humain avant tout.**

## ACL

Le schéma `sinjira_user_rights_internal` :

- retire l’accès à `public` et `anon`;
- accorde seulement `USAGE` à `authenticated` et `service_role`;
- n’accorde `EXECUTE` aux implémentations internes qu’à `authenticated` et `service_role`.

Les wrappers publics suivent les mêmes rôles autorisés.

## Production

Migration appliquée :

`20260823015621 sinjira_v24_5_14_user_rights_rpc_boundary`

Après ce jalon, le ledger canonique contient **145 migrations** de production.

## Hors périmètre

V24.5.14 ne modifie pas :

- `moderation_content_visible`, utilisé directement par des politiques RLS;
- les helpers sociaux ou de sécurité utilisés par RLS;
- les règles de suppression ou de conservation légale;
- les politiques de contenu;
- les règles de sécurité des mineurs;
- DNS, paiement, transport, courriel externe ou service payant.
