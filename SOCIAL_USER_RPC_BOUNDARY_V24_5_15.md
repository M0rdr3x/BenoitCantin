# SINJIRA V24.5.15 — Frontière RPC sociales utilisateur

## Objectif

V24.5.15 retire du schéma API public les implémentations `SECURITY DEFINER` de **4 RPC sociales propres à l’utilisateur**, sans modifier les règles de blocage, de signalement, de sécurité des mineurs ou de modération humaine.

RPC concernées :

- `social_my_blocks`
- `social_my_reports`
- `social_report_content`
- `social_unblock_user`

Les implémentations privilégiées vivent désormais dans `sinjira_social_user_internal`. Les fonctions de même nom conservées dans `public` sont des wrappers `SECURITY INVOKER`.

## Contrat production

Audit après migration :

- **4/4** wrappers publics `SECURITY INVOKER`;
- **0/4** wrapper public `SECURITY DEFINER`;
- **0/4** exécutable par `anon`;
- **4/4** exécutables par `authenticated` et `service_role`;
- **4/4** implémentations internes demeurent `SECURITY DEFINER`;
- **4/4** conservent leur contrôle `auth.uid()`.

## Helpers RLS explicitement exclus

V24.5.15 ne déplace pas :

- `social_is_blocked`, référencé par 8 politiques RLS;
- `social_is_suspended`, référencé par 12 politiques RLS.

Ces helpers restent dans `public` afin de ne pas casser les politiques de ligne existantes.

## Garanties conservées

Le signalement communautaire conserve :

- l’écriture dans le registre canonique `social_reports`;
- la résolution serveur des contenus signalés;
- le snapshot marqué serveur;
- l’anti-spam horaire;
- le blocage des doublons ouverts;
- le marquage `priority_safety` pour les motifs de sécurité;
- la possibilité de signaler un risque sans exiger l’acceptation préalable des règles;
- les protections renforcées pour les mineurs.

Les listes de blocages et de signalements restent limitées à `auth.uid()`.

La modération et les recours restent humains et réversibles selon les règles SINJIRA™. **L’humain avant tout.**

## Production

Migration appliquée :

`20260823020820 sinjira_v24_5_15_social_user_rpc_boundary`

Le ledger canonique passe à **146 migrations**.

Aucun DNS, paiement, service payant, fournisseur externe ou collecte supplémentaire n’est activé par cette migration.
