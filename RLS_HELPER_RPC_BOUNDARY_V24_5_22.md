# SINJIRA V24.5.22 — Frontière des helpers RLS

## Objectif

Retirer du schéma API public les neuf implémentations `SECURITY DEFINER` encore appelables par les comptes connectés, sans casser les politiques RLS qui en dépendent et sans élargir leurs permissions.

## Production

Migration appliquée :

`20260823034619 sinjira_v24_5_22_rls_helper_rpc_boundary`

Le ledger compte **153 migrations**.

## Helpers isolés

- `is_fracture_party_member`
- `moderation_content_visible`
- `sinjira_can_social_interact`
- `sinjira_content_allowed`
- `sinjira_cycle_allowed`
- `sinjira_mfa_access_allowed`
- `sinjira_my_age_band`
- `social_is_blocked`
- `social_is_suspended`

Les implémentations privilégiées sont déplacées dans `sinjira_rls_internal`. Les signatures publiques restent disponibles sous forme de wrappers `SECURITY INVOKER`, `STABLE`, avec les mêmes arguments, valeurs par défaut et types de retour.

`anon` n’obtient aucun `EXECUTE`. `authenticated` et `service_role` conservent les droits existants sur les wrappers et sur le schéma interne nécessaire aux politiques.

## Continuité RLS

`ALTER FUNCTION ... SET SCHEMA` conserve l’OID de chaque implémentation. Les politiques déjà liées à ces OID continuent donc d’appeler directement l’implémentation privilégiée, maintenant hors du schéma API exposé.

Audit production après migration : **81/81 références de politiques RLS** pointent vers `sinjira_rls_internal`, réparties ainsi :

- 4 `is_fracture_party_member`
- 8 `moderation_content_visible`
- 19 `sinjira_can_social_interact`
- 1 `sinjira_content_allowed`
- 1 `sinjira_cycle_allowed`
- 19 `sinjira_mfa_access_allowed`
- 9 `sinjira_my_age_band`
- 8 `social_is_blocked`
- 12 `social_is_suspended`

Aucune politique ne pointe vers un nouveau wrapper public à la place de son implémentation historique.

## Sécurité

Après V24.5.22, l’advisor Supabase ne signale plus aucun warning `Signed-In Users Can Execute SECURITY DEFINER Function`.

Les INFO `RLS Enabled No Policy` correspondent encore à des tables volontairement scellées et seront traitées séparément par des politiques explicites de refus, sans ouvrir de lecture ni d’écriture.

La protection Supabase contre les mots de passe compromis reste un avertissement distinct lié au plan Pro+; aucun achat n’est autorisé par cette version.

Aucun paiement, checkout, fournisseur de courriel/SMS, transporteur, IA distante ou changement DNS n’est activé.

Principe directeur : **L’humain avant tout.**
