# SINJIRA V24.5.21 — Frontière RPC joueur Fracture

## Objectif

Réduire la surface `SECURITY DEFINER` exposée aux joueurs de Fracture sans modifier le jeu, les sièges, les identités cachées, les cartes, les rapports, les accusations, les scores ni l’état brut réservé au serveur.

## Production

Migration appliquée :

`20260823033756 sinjira_v24_5_21_fracture_player_rpc_boundary`

Le ledger compte **152 migrations**.

## RPC isolées

Huit RPC joueur sont déplacées dans `sinjira_fracture_internal` :

- `create_fracture_party`
- `join_fracture_party`
- `fracture_engine_get_state`
- `fracture_engine_start`
- `fracture_engine_pick`
- `fracture_engine_submit_keep`
- `fracture_engine_submit_report`
- `fracture_engine_submit_accusation`

Les signatures publiques restent identiques avec des wrappers `SECURITY INVOKER`. `anon` ne peut pas les exécuter; `authenticated` et `service_role` conservent les droits existants.

Sept implémentations conservent leur vérification directe `auth.uid()`. `fracture_engine_get_state` continue de déléguer à `_fracture_engine_get_state_raw`, qui impose `AUTH_REQUIRED`, résout le siège du membre et refuse `NOT_A_MEMBER`.

## Helper RLS volontairement exclu

`public.is_fracture_party_member(uuid,uuid)` reste dans `public` et n’est pas déplacé par V24.5.21. Quatre politiques RLS l’utilisent directement pour autoriser la lecture de parties, membres, rapports de fin de partie et documents joueur. Le déplacer mécaniquement casserait l’évaluation RLS ou obligerait à ouvrir une permission indue.

## Confidentialité Fracture

- L’état brut `_fracture_engine_get_state_raw` reste non exécutable par `authenticated`.
- L’état joueur continue d’être assaini avant retour navigateur.
- Les identités cachées des autres sièges restent masquées avant la fin.
- Les rapports restent nettoyés pour ne pas révéler le suspect choisi par un autre joueur.
- Aucune règle de jeu ou distribution de rôle n’est modifiée.

## Coût

Aucun paiement, IA distante, courriel/SMS externe, service de transport, DNS ou autre service payant n’est activé.

Principe directeur : **L’humain avant tout.**
