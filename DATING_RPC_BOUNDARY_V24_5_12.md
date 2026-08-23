# SINJIRA V24.5.12 — Frontière RPC Rencontres

## Objectif

V24.5.12 retire les implémentations privilégiées des RPC Rencontres du schéma API public tout en conservant les noms, signatures et règles fonctionnelles déjà en production.

Le schéma public expose uniquement des wrappers `SECURITY INVOKER`. Les implémentations `SECURITY DEFINER` sont déplacées dans `sinjira_dating_internal`.

## RPC couvertes

Les **18 RPC** couvertes sont :

- `dating_block_connection`
- `dating_close_connection`
- `dating_compatibility_candidates`
- `dating_compatibility_detail`
- `dating_confirm_single_and_serious`
- `dating_connections_overview`
- `dating_conversation`
- `dating_import_registry_traits`
- `dating_pause_profile`
- `dating_report_connection`
- `dating_request_conversation`
- `dating_respond_connection`
- `dating_safe_meet_cancel`
- `dating_safe_meet_opt_in`
- `dating_safe_meet_status`
- `dating_self_status`
- `dating_send_message`
- `dating_set_photo_consent`

## Audit avant migration

Avant déplacement :

- 18/18 fonctions étaient `SECURITY DEFINER` dans `public`;
- 0/18 étaient exécutables par `anon`;
- 18/18 étaient exécutables par `authenticated`;
- 18/18 étaient exécutables par `service_role`;
- 18/18 contenaient un contrôle `auth.uid()`;
- aucune des 18 fonctions n’était référencée directement par une politique RLS.

Deux familles d’appels internes ont été identifiées et conservées comme un même lot :

- `dating_compatibility_detail` et `dating_request_conversation` utilisent `dating_compatibility_candidates`;
- `dating_safe_meet_opt_in` utilise `dating_safe_meet_status`.

Les wrappers publics conservent ces noms, de sorte que les appels historiques restent valides.

## Audit après migration

Production vérifiée :

- 18/18 wrappers publics présents;
- 18/18 wrappers publics `SECURITY INVOKER`;
- 0/18 wrapper public `SECURITY DEFINER`;
- 0/18 exécutable par `anon`;
- 18/18 exécutables par `authenticated`;
- 18/18 exécutables par `service_role`;
- 18/18 implémentations internes `SECURITY DEFINER`;
- 18/18 signatures et types de retour conservés;
- 18/18 implémentations conservent `auth.uid()`.

## Invariants Rencontres

Cette migration ne change pas les règles produit :

- Rencontres demeure réservé aux adultes selon les règles existantes;
- aucune identité n’est révélée plus tôt;
- aucun consentement photo n’est contourné;
- les règles de blocage, signalement et rencontre sécuritaire restent inchangées;
- l’usage facultatif de traits du Registre ne devient pas automatique;
- aucune nouvelle donnée n’est collectée;
- aucune décision humaine sensible n’est déléguée à l’IA.

## Production

Migration appliquée :

`20260823011647 sinjira_v24_5_12_dating_rpc_boundary`

Le ledger production compte **143 migrations** à ce jalon.
