# SINJIRA — Livre I — Release privée du maître 2026-10-05

## Objet

Préparer la diffusion privée de **SINJIRA — Livre I : La Cendre du Jugement** sans publier l’intégrale dans le dépôt public et sans contourner les portes de revue production.

Maître intégral reçu le 2026-10-05 :

- pages : **1027** ;
- taille : **7 325 502 octets** ;
- MIME : `application/pdf` ;
- SHA-256 : `9acc8f561962850158cb073b122ee038c2731ee3b165deae482260c0cc1ad2d8` ;
- dépôt Git public : **interdit** ;
- diffusion cible : **Storage privé + URL signée courte**.

La démo publique est un fichier distinct de 84 pages. Son blob Git public est binaire-identique au maître démo reçu.

## État production observé le 2026-10-05

Lecture seule effectuée sur le projet Supabase `gpvivleexywljowcqkru` :

- `public.sinjira_novels` existe ;
- `private.sinjira_private_novel_assets` n’est pas encore présent en production ;
- `public.sinjira_private_novel_asset_for_delivery(text)` n’est pas encore présent ;
- `public.sinjira_my_novel_catalog()` n’est pas encore présent ;
- aucun bucket `sinjira-private-novels` n’est actuellement créé ;
- les Edge Functions `get-private-novel-url` et `admin-private-novel-release` ne sont pas encore déployées.

Conséquence : **l’intégrale ne doit pas être activée maintenant**. Le site public peut annoncer l’intégrale privée et servir la démo, mais le fichier complet reste hors dépôt et hors diffusion tant que la chaîne serveur n’est pas déployée et vérifiée.

## Chaîne de release préparée

La release privée est volontairement découpée en étapes indépendantes :

1. appliquer les migrations V25 approuvées ;
2. créer/configurer un bucket privé autorisant `application/pdf` ;
3. configurer `delivery_mode='storage'`, `storage_bucket` et `storage_path` avec `enabled=false` ;
4. téléverser le PDF intégral dans le bucket privé ;
5. calculer localement le SHA-256 et la taille du fichier téléversé ;
6. enregistrer cette preuve via `admin-private-novel-release` avec l’action `record_integrity` ;
7. vérifier que `status.can_enable=true` ;
8. effectuer une décision humaine explicite ;
9. appeler `enable` avec `confirmation = "ACTIVER_LA_DIFFUSION_PRIVEE"` et le SHA-256 exact du maître ;
10. vérifier le parcours auteur, famille autorisée et membre possédant le droit produit ;
11. vérifier qu’un compte 11–12 ans et un compte sans droit restent refusés ;
12. conserver la désactivation `disable` comme voie fail-safe immédiate.

## Invariants

La migration de garde d’intégrité ne crée pas le PDF, ne téléverse rien, ne configure aucun chemin Storage, ne rend aucun bucket public et n’active aucun actif automatiquement. Elle exige un objet présent dans un bucket privé, la taille et le MIME attendus, une preuve d’intégrité enregistrée et réserve les RPC de release au `service_role`.

L’Edge Function d’administration exige une session administrateur avec MFA via `requiredAdmin()`, impose un corps JSON borné, ne reçoit jamais les octets du PDF, ne permet pas de remplacer le maître, ne peut activer sans la phrase de confirmation et le SHA-256 attendu, et permet la désactivation immédiate sans barrière supplémentaire.

## Rollback

En cas d’anomalie après activation :

1. appeler `admin-private-novel-release` avec `action="disable"` ;
2. confirmer que `enabled=false` dans la readiness ;
3. invalider/remplacer l’objet Storage si nécessaire ;
4. ne jamais déplacer l’intégrale vers le dépôt public comme solution de repli ;
5. conserver le journal de preuve et ouvrir un correctif forward-only.

## Frontière avec la revue production

Ce runbook ne vaut **pas** approbation de migration ni autorisation de déploiement. Les fichiers restent soumis au reviewed batch, au ledger de production et aux contrôles déjà présents dans la PR #435.
