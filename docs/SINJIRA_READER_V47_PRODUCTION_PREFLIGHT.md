# SINJIRA — V47 : prévol de mise en service de la liseuse V32

**Référence : 8 novembre 2026 · État de la production : NO_GO pour le défilement synchronisé.**

## Résultat réel, en lecture seule

La requête `scripts/audits/sinjira_reader_v47_preflight_readonly.sql` a été **exécutée sur les seuls catalogues PostgreSQL de la base SINJIRA** le 8 novembre 2026. Elle ne lit aucune ligne de `sinjira_reader_library`, aucun lecteur, aucun livre ni aucun PDF. Elle n'applique aucune migration.

| Vérification | Résultat | Portée |
|---|---|---|
| Table de progression présente | PASS | `public.sinjira_reader_library` existe |
| RLS activée | PASS | RLS `relrowsecurity` vraie |
| Politique propriétaire unique | PASS | Politique `ALL` pour `authenticated` avec `auth.uid()` en `USING` et `WITH CHECK` |
| Clé composite lecteur/roman | PASS | `PRIMARY KEY(user_id, novel_id)` |
| Contraintes historiques page/progression | PASS | Les deux bornes précédentes restent définies |
| Colonnes et types de base | PASS | UUID du lecteur/roman, entier page et pourcentage |
| Droits de lecture et mise à jour du compte | PASS | Rôle `authenticated` autorisé par GRANT, puis restreint par RLS |
| GRANT directs au rôle `anon` | **REVIEW** | `anon` possède toujours des privilèges de table, mais **aucune politique RLS ne l'autorise à lire les lignes**. Vérifier le moindre privilège, ne pas interpréter comme une fuite confirmée |
| Colonne `scroll_ratio` V32 | **BLOCK** | Colonne absente de la base liée |
| Contrainte de défilement 0..1 | **BLOCK** | Contrainte non encore installée |
| **Décision** | **NO_GO** | La reprise intrapage entre appareils n'est pas activée |

**Bilan : 7 PASS, 2 BLOCK, 1 REVIEW, décision NO_GO.**

La documentation Supabase précise que les privilèges GRANT et les politiques RLS sont deux contrôles complémentaires. Une autorisation SQL accordée à `anon` sans politique permissive ne certifie **pas** l'existence d'un accès aux données. Voir la [documentation officielle RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).

## Mise en service contrôlée requise

La migration V32 `supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql` existe déjà sur `main` et ajoute `scroll_ratio numeric(5,4) NULL` avec contrainte de valeur entre 0 et 1. **Cette PR V47 ne modifie pas la migration et ne l'applique pas.**

Respecter strictement [`docs/SUPABASE_PRODUCTION_RUNBOOK.md`](SUPABASE_PRODUCTION_RUNBOOK.md) : le registre de migrations effectives, le workspace protégé, le prévol local puis distant, la confirmation explicite sur `main` et la protection de l'Environment GitHub `production`. **Ne jamais utiliser un `supabase db push --linked` depuis l'historique de reconstruction du dépôt.**

Avant et après application autorisée, vérifier les différences de schéma attendues, la compatibilité avec les progressions anciennes (position `NULL`), les politiques RLS, l'absence d'accès inter-comptes et le droit de lecture aux romans réellement autorisés. Le correctif de schéma ne vaut pas recette de lecture.

## Critères d'acceptation opérationnelle

1. **Prévol V47 avant déploiement** : présente `NO_GO` et les deux manquements V32; les droits `anon` doivent être examinés selon la politique de moindre privilège.
2. **Déploiement manuel approuvé** : migration ciblée, vérification des colonnes et de la contrainte (et absence de dérive du RLS), sans écraser l'historique distant.
3. **Prévol V47 après déploiement** : les deux critères V32 doivent devenir PASS; la conclusion ne peut devenir que **REVIEW_REQUIRED**, jamais GO automatique.
4. **Tests avec deux vrais appareils pour un compte de test autorisé** : reprendre page + position dans un roman privé, changer d'appareil et de compte, vérifier les accès et les comportements hors ligne, en cas d'échec de réseau et sur ancienne sauvegarde `NULL`.
5. **Décision de sortie explicite** : seulement après preuves d'appels et de reprise réels, validations de sécurité et approbation du responsable.

## Garanties de cette livraison V47

Le validateur `scripts/validate_sinjira_reader_v47_preflight.py` et ses tests interdisent d'introduire du DDL/DML dans ce prévol, de consulter les tables de lecteurs, d'utiliser une connexion de production, de changer les onze critères de revue ou de laisser dériver la migration de référence. Le workflow CI n'exécute que Python, **sans secrets, sans session Supabase ni réseau distant**.

La V47 améliore la mesure des blocages P0, mais **ne ferme pas** le jalon `reader_v32_prod` du programme SINJIRA ni celui des deux appareils. Le pourcentage général reste **66,5 % ≈ 67 %**, incertitude ±10 points, sans date de fin fiable.
