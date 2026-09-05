# SINJIRA V25 — Préparation du déploiement production

> État vérifié le 2026-09-04. Ce document distingue volontairement **fusionné dans GitHub** et **appliqué sur Supabase production**.

## Principe de déploiement

**L’HUMAIN AVANT TOUT.** Le Registre personnel des consciences ne doit jamais être activé partiellement : le moteur de risque, le coffre privé, la continuité des challenges, le durcissement des appareils et l’Edge Function doivent former un lot cohérent.

Ce runbook ne constitue pas une preuve de déploiement. La production doit être vérifiée après chaque opération.

## État observé en production

Projet Supabase configuré par `supabase/config.toml` : `gpvivleexywljowcqkru`.

Au contrôle du 2026-09-04 :

- dernière migration appliquée observée : `20260901002241_sinjira_v24_5_54_fracture_contribution_atomic_finalize`;
- `public.security_connection_events.risk_model_version` : absent;
- `private.security_risk_score_v25(...)` : absent;
- `private.conscience_entries` : absent;
- `private.conscience_vault_sessions` : absent;
- `private.conscience_vault_audit` : absent;
- `public.service_conscience_evaluate_access(...)` : absent;
- Edge Function `conscience-vault` : absente de l’inventaire production;
- les trois tables du coffre restent donc correctement classées comme **planifiées** dans `scripts/validate_production_schema_manifest.py`.

Conclusion : le lot V25 est fusionné dans `main`, mais **n’est pas encore déployé sur Supabase production** tant que le workflow de production n’a pas été exécuté et que les contrôles post-déploiement n’ont pas réussi.

## Historique Supabase : règle importante

L’historique production SINJIRA existant n’utilise pas systématiquement les mêmes timestamps que les fichiers de `supabase/migrations/`. Par exemple, la production contient `20260809050252_sinjira_universal_platform` alors que le dépôt historique contient une migration locale portant le même nom avec un autre timestamp.

Supabase CLI `migration list` compare les migrations **par timestamp uniquement**. Un `supabase db push` depuis l’historique Git actuel considérerait donc des migrations anciennes comme divergentes, même lorsque leur changement de schéma est déjà présent en production.

Conséquences :

- **ne pas** utiliser `supabase db push`, `--include-all` ou `migration repair` pour forcer l’alignement de ce rollout;
- **ne pas** réécrire en masse l’historique ancien uniquement pour déployer le coffre;
- utiliser l’API officielle Supabase `POST /v1/projects/{ref}/database/migrations`, qui exécute la migration transactionnellement et crée l’entrée distante dans `supabase_migrations`;
- pour V25, le contrat de séquence repose sur les **noms des quatre migrations et leur ordre**, tandis que les versions/timestamps distants sont générérés par Supabase;
- conserver la baseline distante V24.5.54 comme frontière : aucune migration inattendue ne doit apparaître après elle avant ou pendant ce rollout.

## Voie de déploiement contrôlée

Le lot doit être déployé par `.github/workflows/sinjira-v25-production-deploy.yml` après fusion de ce workflow dans `main`.

Le workflow est volontairement manuel (`workflow_dispatch`) et impose :

- l’environnement GitHub `production`;
- la confirmation textuelle exacte `DEPLOY-SINJIRA-V25`;
- le secret `SUPABASE_ACCESS_TOKEN`;
- le projet Supabase explicite `gpvivleexywljowcqkru`;
- le checkout du SHA gelé `fc8d9fe26c8f095a0e95dc6cadcbf43d7c61c9dd`;
- une lecture préalable de `GET /v1/projects/{ref}/database/migrations`;
- la baseline exacte `20260901002241_sinjira_v24_5_54_fracture_contribution_atomic_finalize`;
- après cette baseline, uniquement un préfixe valide des quatre noms V25 attendus, ce qui permet une reprise sûre après une interruption partielle;
- l’application des migrations via `POST /v1/projects/{ref}/database/migrations` avec une `Idempotency-Key` stable;
- une nouvelle lecture de l’historique exigeant exactement les quatre noms V25 dans l’ordre avant le déploiement Edge;
- Supabase CLI `2.111.0` uniquement pour déployer la seule Edge Function `conscience-vault`, sans `--no-verify-jwt`.

### Pourquoi le SHA est gelé

`fc8d9fe26c8f095a0e95dc6cadcbf43d7c61c9dd` correspond à l’état du dépôt après le runbook #162 et avant les fondations applicatives ajoutant d’autres migrations.

La chronologie vérifiée est la suivante :

- #155 introduit `20260902211500_sinjira_v25_0_security_risk_model_convergence.sql`;
- #156 introduit les trois autres migrations SQL du coffre ainsi que `conscience-vault`;
- #157, #158, #159, #161 et #162 n’ajoutent aucune migration SQL;
- #164 ne contient aucune migration;
- #165 introduit ensuite `20260904225000_sinjira_v25_employment_foundation.sql`;
- #167 introduit ensuite les migrations `20260905000500_sinjira_v25_personal_ai_foundation.sql` et `20260905001000_sinjira_v25_personal_ai_rls_hardening.sql`.

**Ne pas exécuter `supabase db push` depuis le `main` actuel pour ce déploiement du coffre.** Cela pourrait embarquer des migrations de modules qui ne font pas partie de ce lot et se heurterait en plus à la dérive historique de timestamps déjà présente.

Le SHA gelé sert à garantir le contenu exact du SQL et de l’Edge Function. La production reste protégée par un second contrat indépendant : la baseline distante et la suite ordonnée des noms de migrations lue directement depuis l’API Supabase.

## Lot SQL V25 à appliquer — ordre obligatoire

1. `20260902211500_sinjira_v25_0_security_risk_model_convergence.sql` → `sinjira_v25_0_security_risk_model_convergence`
2. `20260902223000_sinjira_v25_0_personal_consciousness_vault.sql` → `sinjira_v25_0_personal_consciousness_vault`
3. `20260902231500_sinjira_v25_0_conscience_vault_challenge_continuity.sql` → `sinjira_v25_0_conscience_vault_challenge_continuity`
4. `20260903213000_sinjira_v25_0_device_key_privacy_and_trust_hardening.sql` → `sinjira_v25_0_device_key_privacy_and_trust_hardening`

Ne pas sauter la première migration : le coffre exige explicitement le modèle de risque `v25.0` et le scope sensible `conscience_vault`.

Ne pas utiliser `migration repair`, `db reset --linked`, `db push`, `--include-all` ou un SQL copié manuellement pour forcer le passage. Si une migration inattendue apparaît après la baseline V24.5.54, arrêter le déploiement et diagnostiquer avant toute nouvelle écriture.

## Effet utilisateur important avant production

La migration `20260903213000_sinjira_v25_0_device_key_privacy_and_trust_hardening.sql` retire le `SELECT` direct de `security_devices` et **réinitialise volontairement tous les statuts historiques `is_trusted` / `is_primary`**.

Cette remise à zéro est une mesure de sécurité parce que les anciennes `device_key` avaient déjà été exposées au navigateur. Elle implique toutefois que les utilisateurs devront réamorcer la confiance de leurs appareils selon le nouveau contrat AAL2 / autre appareil fiable.

Le contrôle production du 2026-09-04 a trouvé un seul appareil enregistré, aucun appareil `is_trusted`, aucun appareil `is_primary` et donc aucun utilisateur affecté par cette remise à zéro au moment du préflight. Ce constat doit être revérifié si le déploiement est reporté.

Le déploiement doit donc être traité comme un changement utilisateur réel, pas comme une simple migration invisible.

## Edge Function à déployer après les migrations

Déployer `supabase/functions/conscience-vault/index.ts` avec :

- `verify_jwt = true`;
- les mêmes dépendances partagées que le SHA gelé;
- aucune exposition directe du schéma `private` au navigateur;
- aucune journalisation du contenu du Registre.

Le workflow déploie explicitement seulement `conscience-vault` après confirmation de l’historique SQL. Il ne doit jamais utiliser `--no-verify-jwt`.

Ne pas rendre l’interface du Registre personnel opérationnelle tant que cette fonction et les quatre migrations ne sont pas présentes en production.

## Préflight obligatoire

Avant toute écriture production :

1. vérifier que le projet Supabase est `ACTIVE_HEALTHY`;
2. lire l’historique Supabase et confirmer la baseline `20260901002241_sinjira_v24_5_54_fracture_contribution_atomic_finalize`;
3. confirmer qu’après cette baseline il n’existe aucune migration inattendue : seulement zéro à quatre noms V25, dans l’ordre prévu;
4. confirmer que les workflows V25 de `main` sont verts;
5. confirmer que `conscience-vault` reste `verify_jwt=true` dans le SHA gelé;
6. revérifier l’impact de la remise à zéro de confiance des appareils;
7. confirmer que l’environnement GitHub `production` et `SUPABASE_ACCESS_TOKEN` sont configurés;
8. déclencher uniquement `.github/workflows/sinjira-v25-production-deploy.yml` avec la confirmation exacte;
9. arrêter immédiatement si l’API de migrations refuse l’accès ou si l’historique ne correspond plus au préfixe attendu;
10. ne pas confondre le Registre personnel avec le Registre narratif ni avec Histoire de vie.

## Vérifications post-déploiement DB

Exécuter en lecture seule :

```sql
select
  to_regclass('private.conscience_entries') is not null as conscience_entries_exists,
  to_regclass('private.conscience_vault_sessions') is not null as conscience_vault_sessions_exists,
  to_regclass('private.conscience_vault_audit') is not null as conscience_vault_audit_exists,
  exists (
    select 1
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public'
      and p.proname = 'service_conscience_evaluate_access'
  ) as conscience_access_rpc_exists,
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'security_connection_events'
      and column_name = 'risk_model_version'
  ) as risk_model_version_column_exists,
  exists (
    select 1
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'private'
      and p.proname = 'security_risk_score_v25'
  ) as security_risk_score_v25_exists;
```

Toutes les valeurs doivent être `true`.

Puis vérifier les privilèges :

- aucun CRUD direct `anon` / `authenticated` sur `private.conscience_*`;
- aucun accès direct au contenu du coffre par le navigateur/mobile;
- RPC serveur avec `search_path` fixé;
- AAL2 obligatoire;
- Mode Voyage/appareil fiable ne contourne jamais le step-up du Registre personnel;
- l’audit du coffre ne contient que des métadonnées;
- Histoire de vie / héritage n’a aucune voie vers `private.conscience_*`.

## Vérifications post-déploiement Edge

1. `conscience-vault` apparaît `ACTIVE` dans l’inventaire Supabase;
2. `verify_jwt=true`;
3. une requête sans JWT est refusée;
4. une session AAL1 est refusée;
5. un `user_id` / `target_user_id` fourni par le client est refusé;
6. une ouverture AAL2 avec risque acceptable crée une capacité courte;
7. une capacité expirée ou révoquée ne lit plus aucune entrée;
8. un challenge d’appareil fiable reste obligatoire lorsqu’il est requis;
9. les réponses sensibles sont `private, no-store`;
10. aucun contenu intime n’apparaît dans les logs.

Le succès du workflow n’est pas, à lui seul, une preuve suffisante de ces dix propriétés : les contrôles production doivent être exécutés après le déploiement.

## Vérification Auth séparée

Le conseiller sécurité Supabase observé le 2026-09-04 signale **Leaked Password Protection Disabled**.

Le dépôt fixe déjà `minimum_password_length = 12` pour la reconstruction locale, mais la protection contre les mots de passe compromis est un réglage Auth hébergé distinct. Il doit être activé et revérifié séparément dans la configuration production; ne pas prétendre qu’un changement GitHub ou le workflow SQL suffit à l’activer.

Référence Supabase : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Après validation production

Seulement après vérification réelle du backend :

- mettre à jour `scripts/validate_production_schema_manifest.py` pour déplacer `conscience_entries`, `conscience_vault_sessions` et `conscience_vault_audit` de `PLANNED_LOCAL_TABLES` vers `EXPECTED_TABLES`;
- conserver les tests/guards V25 actifs;
- effectuer un smoke test Web et mobile sans contenu intime réel;
- noter la date, le SHA gelé et les versions distantes générées par Supabase dans le journal de release.

## Rollback / incident

Ne pas tenter un rollback destructif automatique du coffre si des entrées réelles ont été créées. En cas d’incident :

1. désactiver l’accès applicatif au Registre personnel;
2. révoquer les capacités actives;
3. conserver les données privées intactes;
4. analyser les logs de métadonnées seulement;
5. corriger en migration avant de rouvrir l’accès.

Le Registre personnel ne doit jamais être exporté vers Histoire de vie, le PDF posthume, les analytics, la publicité ou les recommandations, y compris pendant une procédure d’incident.
