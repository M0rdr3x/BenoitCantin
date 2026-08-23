# SINJIRA V24.5.19 — Frontière RPC rachat de lien familial

## Principe

**L’humain avant tout.** Cette version déplace l’implémentation privilégiée de `redeem_family_link_invite` derrière la frontière famille existante, sans modifier les consentements ni les règles relationnelles.

## Frontière

- wrapper public `public.redeem_family_link_invite(...)` : `SECURITY INVOKER`
- implémentation privilégiée : `sinjira_family_playtest_internal.redeem_family_link_invite(...)`
- `anon` : aucun `EXECUTE`
- `authenticated` et `service_role` : droits conservés
- `auth.uid()` : conservé
- signature, paramètres par défaut et type de retour : inchangés

## Invariants familiaux

L’implémentation interne conserve :

- compte appelant adulte obligatoire;
- compte source adulte obligatoire;
- impossibilité de relier un compte à lui-même;
- code d’invitation valide, non utilisé et non expiré;
- `adult_child → child`;
- `family → other`;
- statut du lien `confirmed`;
- consentements des deux comptes;
- `mirror_to_fiction=false` au moment de la création, même si un ancien paramètre de compatibilité existe.

## Health-check

`sinjira_family_link_health()` reste réservé au `service_role` et inspecte maintenant l’implémentation interne plutôt que le wrapper public. Son résultat de production est `ok=true`, avec les mappings historiques et le miroir fiction privé vérifiés.

## Coûts externes

Aucun service payant, courriel/SMS externe, paiement ou fournisseur tiers n’est activé.

## Production

Migration : `20260823031150 sinjira_v24_5_19_family_redeem_rpc_boundary`

Le registre de production contient **150 migrations** après V24.5.19.
