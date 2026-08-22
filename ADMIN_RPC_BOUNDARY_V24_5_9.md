# SINJIRA V24.5.9 — Frontière RPC administratives globale

## Principe

Les RPC administratives sensibles ne doivent pas exposer directement une implémentation `SECURITY DEFINER` dans le schéma API `public` lorsqu’une frontière invoker peut conserver exactement les mêmes contrôles.

V24.5.9 déplace **25 fonctions** dans `sinjira_admin_internal` et conserve les mêmes noms/signatures dans `public` sous forme de wrappers `SECURITY INVOKER`.

## Fonctions couvertes

- **13** RPC Histoire de vie `admin_life_story_*`;
- **7** RPC Monde parallèle `admin_parallel_*`;
- **4** RPC confidentialité `privacy_admin_*`;
- **1** RPC sécurité `safety_admin_escalation_cases`.

## Autorisations conservées

Audit production après migration :

- 25/25 wrappers publics `SECURITY INVOKER`;
- 0/25 wrapper public `SECURITY DEFINER`;
- 0/25 exécutable par `anon`;
- 25/25 exécutables par `authenticated`;
- 25/25 exécutables par `service_role`;
- 25/25 implémentations internes `SECURITY DEFINER`;
- 25/25 signatures et types de retour identiques entre wrapper et implémentation.

Les contrôles métier existants sont conservés :

- **20/25** implémentations conservent `private.require_sinjira_admin_aal2()`;
- **5/25** implémentations confidentialité/sécurité conservent leur vérification administrateur existante.

V24.5.9 ne transforme pas ces cinq fonctions en AAL2 automatiquement afin de ne pas modifier silencieusement un parcours fonctionnel; leur éventuel step-up doit être traité avec l’interface correspondante.

## RLS sans politique

Les informations `RLS Enabled No Policy` de l’advisor ne sont pas corrigées artificiellement sur les tables volontairement scellées. Ajouter une politique uniquement pour faire disparaître un lint pourrait ouvrir une surface de lecture/écriture qui n’existait pas.

## Commerce et services externes

Cette version ne modifie aucune règle commerciale : aucun tarif, zone, point de ramassage, checkout, paiement ou conversion automatique n’est activé. Aucun transporteur externe, DNS ou service payant n’est ajouté.

## Production

Migration appliquée :

`20260822200413 sinjira_v24_5_9_global_admin_rpc_boundary`

Le ledger production contient **140 migrations**.
