# SINJIRA V24.5.16 — Frontière RPC utilisateur Monde parallèle

## Objectif

V24.5.16 retire du schéma API public les implémentations `SECURITY DEFINER` de **4 RPC utilisateur du Monde parallèle**, sans modifier l’identité parallèle, les cycles, les réponses ou les protections d’identité.

RPC concernées :

- `parallel_my_context`
- `parallel_my_identity`
- `parallel_save_cycle_response`
- `parallel_set_my_identity`

Les implémentations privilégiées sont déplacées dans `sinjira_parallel_user_internal`. Les noms publics restent disponibles sous forme de wrappers `SECURITY INVOKER`.

## Contrat production

- **4/4** wrappers publics `SECURITY INVOKER`;
- **0/4** exécutable par `anon`;
- **4/4** exécutables par `authenticated` et `service_role`;
- **4/4** implémentations internes demeurent `SECURITY DEFINER`;
- **4/4** implémentations conservent `auth.uid()`;
- aucune des 4 RPC n’est référencée directement par une politique RLS.

## Continuité des appels internes

`parallel_my_context`, `parallel_save_cycle_response` et `parallel_set_my_identity` appellent historiquement `public.parallel_my_identity()`.

Ce nom public est conservé par le wrapper `SECURITY INVOKER`; les trois appels internes continuent donc d’utiliser le même contrat sans dupliquer ni contourner la logique d’identité.

## Pare-feu d’identité

Cette migration ne rapproche pas l’identité parallèle de l’identité réelle du compte.

- l’identité parallèle reste une identité distincte;
- aucun UUID interne n’est ajouté aux réponses publiques;
- aucun identifiant technique privé n’est publié;
- aucune donnée du Registre n’est fusionnée automatiquement avec l’identité parallèle;
- aucune relation privée entre personne réelle, personnage parallèle et personnage de roman n’est créée ou exposée;
- les règles d’âge, contenu, cycles et MFA déjà appelées par les implémentations restent inchangées.

La publication canonique du Monde parallèle demeure soumise à validation humaine. **L’humain avant tout.**

## Production

Migration appliquée :

`20260823021612 sinjira_v24_5_16_parallel_user_rpc_boundary`

Le ledger canonique passe à **147 migrations**.

Aucun DNS, paiement, fournisseur externe, service payant ou collecte supplémentaire n’est activé.
