# SINJIRA V24.5.17 — Frontière RPC famille, tuteurs et playtest

## Principe

**L’humain avant tout.** Cette version réduit l’exposition technique de sept RPC sensibles sans modifier les protections des mineurs, les liens tuteur/enfant, les invitations, les consentements ni les contrôles humains existants.

## Frontière technique

Les 7 RPC concernées sont :

- `accept_sinjira_playtest_invitation`
- `create_family_link_invite`
- `create_guardian_signup_invite`
- `get_guardian_youth_contacts`
- `invite_sinjira_playtest_participant`
- `redeem_guardian_signup_invite`
- `revoke_guardian_link`

Leurs implémentations privilégiées résident dans `sinjira_family_playtest_internal`.

Les signatures publiques restent identiques, mais les fonctions du schéma `public` sont maintenant des wrappers `SECURITY INVOKER` seulement. Les implémentations internes conservent `SECURITY DEFINER`, leurs contrôles `auth.uid()` et leurs validations historiques.

## ACL

Audit production V24.5.17 :

- 7/7 wrappers publics `SECURITY INVOKER`
- 0/7 wrapper public `SECURITY DEFINER`
- 0/7 exécutable par `anon`
- 7/7 exécutables par `authenticated`
- 7/7 exécutables par `service_role`
- 7/7 implémentations internes `SECURITY DEFINER`
- 7/7 contrôles `auth.uid()` conservés
- 7/7 signatures et types de retour conservés

## Mineurs et tuteurs

Cette migration ne modifie aucune règle d’âge, aucun consentement parental, aucun droit du tuteur et aucun lien familial. Elle ne crée aucun accès additionnel aux données d’un jeune. Les gardes existantes demeurent dans les implémentations internes.

## Playtest

Les invitations de playtest restent soumises à leurs contrôles historiques. Le simple fait d’être authentifié ne confère aucun privilège administrateur : les contrôles internes existants restent exécutés.

## Exclusions volontaires

`redeem_family_link_invite` n’est pas déplacée dans V24.5.17 parce qu’une autre fonction dépend directement de son contrat public. Les helpers directement utilisés par RLS restent également hors de ce lot.

## Coûts externes

Aucun service payant, fournisseur externe, paiement, courriel/SMS payant ou API tierce n’est activé par V24.5.17.

## Production

Migration : `20260823025628 sinjira_v24_5_17_family_playtest_rpc_boundary`

Le registre de production contient **148 migrations** après V24.5.17.
