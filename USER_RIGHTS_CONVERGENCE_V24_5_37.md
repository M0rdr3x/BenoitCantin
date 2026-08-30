# SINJIRA™ V24.5.37 — convergence de la frontière des droits utilisateur

## Objet

Cette version réconcilie l’état réel de production avec la frontière canonique déjà mise en place pour les demandes de confidentialité et les appels de modération utilisateur.

Une tentative de durcissement a détecté tardivement que les cinq RPC ciblées étaient déjà des wrappers `SECURITY INVOKER` vers `sinjira_user_rights_internal`. La migration de production `20260830015838` a donc ajouté une couche intermédiaire redondante. La migration corrective `20260830015937` la supprime immédiatement et restaure l’architecture canonique.

## État final obligatoire

Les cinq RPC publiques concernées sont :

- `moderation_my_decisions(integer)`;
- `moderation_submit_appeal(uuid,text)`;
- `privacy_create_request(text,text)`;
- `privacy_export_my_extended_data()`;
- `privacy_my_requests(integer)`.

L’état final est :

`public SECURITY INVOKER → sinjira_user_rights_internal SECURITY DEFINER`

`anon` n’a aucun droit `EXECUTE`. Les rôles `authenticated` et `service_role` conservent les droits historiques. Les implémentations canoniques conservent leur contrôle `auth.uid()`.

## Compatibilité restaurée

Les valeurs par défaut historiques sont explicitement restaurées :

- `moderation_my_decisions(p_limit integer DEFAULT 50)`;
- `privacy_create_request(p_request_type text, p_details text DEFAULT NULL)`;
- `privacy_my_requests(p_limit integer DEFAULT 20)`.

Le schéma transitoire `sinjira_privacy_moderation_internal` doit être absent dans l’état final.

## Invariants humains et de confidentialité

Cette convergence ne change pas les droits de la personne :

- aucune demande de confidentialité n’est supprimée ou convertie;
- aucun appel de modération n’est annulé ou rendu irréversible;
- aucune donnée supplémentaire n’est collectée;
- aucune décision automatisée souveraine n’est introduite;
- aucune fonction payante ou fournisseur externe n’est activé.

## Production

Les migrations réellement appliquées et conservées dans l’historique sont :

- `20260830015838 sinjira_v24_5_14_privacy_moderation_user_rpc_boundary`;
- `20260830015937 sinjira_v24_5_15_user_rights_wrapper_cleanup`.

Le ledger Supabase compte **171 migrations** après cette convergence.
