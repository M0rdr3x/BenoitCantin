# SINJIRA V25 — État et exploitation production

> État vérifié le **2026-09-05**. Le backend du Registre personnel des consciences est désormais déployé en production. La preuve détaillée est conservée dans `docs/sinjira-v25-production-deployment-2026-09-05.md`.

## Principe

**L’HUMAIN AVANT TOUT.** Le Registre personnel des consciences concerne la personne réelle et reste strictement distinct du Registre narratif SINJIRA, de Histoire de vie et de l’héritage posthume.

Le contenu intime du coffre ne doit jamais être copié vers :

- Histoire de vie ou le PDF posthume;
- les analytics;
- la publicité;
- les recommandations;
- les journaux de sécurité.

## État production vérifié

Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`).

Baseline avant V25 :

`20260901002241_sinjira_v24_5_54_fracture_contribution_atomic_finalize`

Migrations V25 réellement présentes après cette baseline, dans l’ordre :

1. `20260905040230_sinjira_v25_0_security_risk_model_convergence`
2. `20260905040303_sinjira_v25_0_personal_consciousness_vault`
3. `20260905040330_sinjira_v25_0_conscience_vault_challenge_continuity`
4. `20260905040400_sinjira_v25_0_device_key_privacy_and_trust_hardening`

Le contenu SQL et l’Edge Function proviennent du lot gelé :

`fc8d9fe26c8f095a0e95dc6cadcbf43d7c61c9dd`

Aucune migration Emploi ou Mon IA n’a été incluse dans ce rollout ciblé.

## Objets DB confirmés

Les contrôles production confirment :

- `public.security_connection_events.risk_model_version` présent;
- `private.security_risk_score_v25(...)` présent;
- `private.conscience_entries` présent;
- `private.conscience_vault_sessions` présent;
- `private.conscience_vault_audit` présent;
- `public.service_conscience_evaluate_access(...)` présent.

Pour les trois tables `private.conscience_*` :

- RLS est activé;
- `anon` n’a aucun CRUD direct;
- `authenticated` n’a aucun CRUD direct;
- `service_role` n’a aucun CRUD direct;
- les fonctions serveur sensibles possèdent un `search_path` explicite.

Le coffre était vide immédiatement après rollout : `0` entrée, `0` session et `0` événement d’audit.

L’audit ne possède que des métadonnées (`id`, `user_id`, `session_id`, `entry_id`, `event_type`, `occurred_at`) et aucun champ de contenu intime, IP ou GPS.

## Edge Function production

`conscience-vault` est :

- `ACTIVE`;
- version `1`;
- `verify_jwt=true`;
- bundle SHA-256 `d2a61d32bf09e9278506e0682cf2bba87c0b5941b8acc607e64cd8a772998dfd`.

Le code du lot impose :

- JWT vérifié;
- AAL2 obligatoire à chaque appel;
- identité issue exclusivement du JWT;
- rejet de `user_id`, `target_user_id` et `subject_user_id` client;
- scope serveur `conscience_vault`;
- capacités courtes de 60 à 600 secondes;
- réponses sensibles `private, no-store`;
- aucune IP brute ni donnée GPS stockée;
- aucune journalisation du corps de requête ou du contenu du Registre.

## Durcissement des appareils

La migration V25 retire le `SELECT` direct de `public.security_devices` pour `authenticated`.

État vérifié :

- `authenticated` : aucun `SELECT` direct sur `security_devices`;
- `authenticated` : accès autorisé à `public.security_list_devices(text)`, réponse assainie;
- `anon` : aucun accès à cette liste assainie.

Avant le rollout, il existait un seul appareil enregistré et aucun appareil `is_trusted` ou `is_primary`. La remise à zéro de confiance n’a donc supprimé aucun statut fiable/principal existant au moment du déploiement.

## Historique Supabase : règle permanente

L’historique production SINJIRA utilise historiquement des timestamps distants qui peuvent différer de ceux des fichiers Git portant le même nom de migration.

Supabase CLI `migration list` compare les versions par timestamp. Pour éviter de réécrire artificiellement l’historique :

- ne pas utiliser `migration repair` en masse;
- ne pas utiliser `db reset --linked`;
- ne pas utiliser `db push --include-all` pour forcer la convergence;
- conserver le contrat par **nom et ordre** pour les migrations V25 appliquées via l’API de migrations Supabase.

La voie reproductible gardée dans le dépôt est `.github/workflows/sinjira-v25-production-deploy.yml`. Elle reste `workflow_dispatch` uniquement, avec confirmation `DEPLOY-SINJIRA-V25`, environnement GitHub `production`, SHA gelé et contrôle de l’historique distant.

Le rollout réel du 2026-09-05 a été appliqué via l’interface de gestion Supabase connectée après les mêmes contrôles de baseline et de périmètre. Aucun run GitHub fictif n’est revendiqué.

## CI validée avant rollout

La PR #172 a validé :

- le contrat statique du workflow de production;
- les garde-fous Edge du coffre;
- le démarrage d’une base Supabase locale;
- l’application locale des migrations;
- **31 assertions pgTAP** du coffre V25;
- les autres workflows déclenchés sans échec observé.

## Advisor sécurité après rollout

Supabase signale les tables `private.conscience_*` en `RLS Enabled No Policy` au niveau `INFO`. Pour ce coffre, ce résultat est cohérent avec le design : RLS est activé, aucun rôle applicatif n’a de CRUD direct et les opérations passent par les RPC `SECURITY DEFINER` étroites.

Un avertissement séparé reste ouvert : **Leaked Password Protection Disabled**.

Le dépôt fixe déjà `minimum_password_length = 12`, mais la protection contre les mots de passe compromis est un réglage Supabase Auth hébergé distinct. Elle n’est pas activée par une migration SQL et ne doit pas être déclarée résolue tant que le réglage hébergé n’a pas été modifié et revérifié.

Référence : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Validations d’expérience encore à faire

Le backend est déployé et structurellement vérifié. Les smoke tests authentifiés suivants restent à exécuter avec un **compte de test AAL2** et sans contenu intime réel :

1. une requête sans JWT est refusée;
2. une session AAL1 est refusée;
3. un identifiant utilisateur fourni par le client est refusé;
4. une ouverture AAL2 avec risque acceptable crée une capacité courte;
5. une capacité expirée ou révoquée ne permet plus de lecture;
6. le challenge d’un autre appareil fiable reste obligatoire lorsqu’il est requis;
7. Web et mobile utilisent le même contrat sans conserver de contenu intime hors du flux prévu.

Ces smoke tests ne doivent jamais utiliser de vraie confession, note intime ou donnée personnelle sensible.

## Manifeste production

À partir de ce rollout, `conscience_entries`, `conscience_vault_sessions` et `conscience_vault_audit` doivent rester dans `EXPECTED_TABLES` de `scripts/validate_production_schema_manifest.py`, et non dans `PLANNED_LOCAL_TABLES`.

Les fondations Emploi et Mon IA restent séparées de cette déclaration tant qu’elles n’ont pas été vérifiées comme déployées en production.

## Incident / rollback

Ne jamais faire de rollback destructif automatique du coffre si des entrées réelles existent.

En cas d’incident :

1. désactiver l’accès applicatif au Registre personnel;
2. révoquer les capacités actives;
3. conserver les données privées intactes;
4. analyser uniquement les métadonnées de sécurité nécessaires;
5. corriger par une nouvelle migration;
6. refaire les contrôles DB, Edge et AAL2 avant réouverture.

Le Registre personnel ne doit jamais être exporté vers Histoire de vie, le PDF posthume, les analytics, la publicité ou les recommandations, y compris pendant une procédure d’incident.
