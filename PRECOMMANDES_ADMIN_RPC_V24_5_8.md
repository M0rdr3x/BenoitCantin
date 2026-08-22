# SINJIRA™ — Frontière RPC d’administration des précommandes

**Version : V24.5.8**  
**Migrations production :**
- `20260822195029 sinjira_v24_5_8_preorder_admin_rpc_boundary`
- `20260822195124 sinjira_v24_5_8_preorder_admin_rpc_acl_hardening`

**Ledger production : 139 migrations**

## Objectif

Réduire la surface privilégiée exposée par l’API sans modifier le comportement fonctionnel de l’administration des précommandes.

Les 15 fonctions `admin_preorder_*` conservent leurs noms, arguments, valeurs par défaut et types de retour dans `public`, mais les wrappers publics sont désormais `SECURITY INVOKER`.

Les implémentations historiques `SECURITY DEFINER` ont été déplacées dans :

`preorder_admin_internal`

Ce schéma n’est pas un schéma API public. Les implémentations internes conservent toutes l’appel à `private.require_sinjira_admin_aal2()`, donc l’accès reste soumis à l’identité administrateur et au MFA/AAL2.

## ACL

État production vérifié :

- wrappers publics : 15 fonctions, 0 `SECURITY DEFINER`;
- implémentations internes : 15 fonctions, 15 `SECURITY DEFINER`;
- contrôle MFA/AAL2 interne : 15/15;
- exécution `anon` des wrappers admin : 0/15;
- exécution `authenticated` des wrappers admin : 15/15;
- exécution par le rôle générique `PUBLIC` : 0/15;
- signatures/types de retour entre wrapper et implémentation : 0 divergence.

La seconde migration V24.5.8 retire explicitement `EXECUTE` à `anon`. Cette étape est obligatoire parce que des ACL explicites héritées existaient sur les RPC administratives historiques.

## Invariants commerciaux

V24.5.8 ne publie aucun tarif, aucune zone de livraison ni aucun point de ramassage. Elle n’active ni vente, ni checkout, ni paiement, ni conversion automatique, ni API transporteur, ni achat d’étiquette.

Les règles précédentes restent obligatoires :

- les frais de livraison d’un exemplaire expédié sont à la charge du client;
- le ramassage sur place est à 0 $ de frais de livraison;
- une estimation est non contractuelle;
- aucune adresse de retrait n’est rendue publique sans publication administrative explicite.

## Sécurité globale

Aucune fonction `SECURITY DEFINER` du schéma `public` n’est exécutable par `anon` après V24.5.7/V24.5.8.

D’autres RPC `SECURITY DEFINER` restent volontairement exécutables par `authenticated` dans d’autres modules. Elles seront auditées par famille fonctionnelle; aucune conversion ou révocation massive ne doit être faite sans vérifier les invariants de propriété, MFA, sécurité jeunesse, confidentialité ou moteur de jeu.

La protection Supabase intégrée contre les mots de passe compromis reste un avertissement accepté sous contrainte Free, car la fonction intégrée est réservée aux offres payantes. Aucun plan payant n’est activé.

## Limites inchangées

- aucun DNS modifié;
- aucun passkey activé avant la migration finale vers `sinjira.com`;
- aucun service externe payant activé;
- la branche GitHub `main` reste sans protection serveur faute d’action d’écriture disponible dans les outils actuels; le workflow de gouvernance reste un garde de détection seulement.
