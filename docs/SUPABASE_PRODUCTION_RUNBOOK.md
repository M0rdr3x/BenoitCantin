# SINJIRA™ — Runbook Supabase production

## Règle absolue

Ne jamais exécuter un `supabase db push --linked` directement depuis le dossier `supabase/migrations/` du dépôt contre la production SINJIRA™.

Le dépôt conserve deux réalités complémentaires :

- `supabase/migrations/` : historique **fonctionnel de reconstruction**, utilisé pour recréer/tester une base neuve;
- `supabase/production-migration-ledger.txt` : versions **réellement enregistrées** dans la production liée.

L’historique de reconstruction contient du SQL consolidé et des timestamps de travail qui ne correspondent pas tous au registre distant. Le workspace protégé `.prod-workspace/supabase` est donc obligatoire pour toute opération générique liée à la production.

## Voie générique unique — `Supabase production — prévol / synchronisation contrôlée`

Le seul workflow générique autorisé à préparer ou appliquer une synchronisation Supabase production est `.github/workflows/supabase-production-preflight.yml`.

L’ancien workflow `.github/workflows/supabase-production-safe.yml` est retiré et ne doit pas être recréé. Réduire la production à une seule voie générique évite des conditions d’écriture divergentes et rend l’audit du déploiement plus simple.

Son nom de run doit rendre l’intention visible :

- push ou pull request : `Supabase production — PRÉVOL`;
- lancement manuel avec `apply=false` : prévol seulement;
- lancement manuel avec `apply=true` : `Supabase production — APPLICATION DEMANDÉE`.

Le workflow canonique sépare désormais trois frontières dans le même fichier :

1. `local-preflight` — validations strictement locales, sans secret production et sans Supabase CLI;
2. `remote-preflight` — lancement manuel uniquement, avec lectures distantes, lint et `db push --dry-run`, sans écriture;
3. `apply-production` — seule zone générique autorisée à écrire, uniquement après le prévol local et distant, avec confirmation explicite et rattachement à l’Environment GitHub `production`.

Cette séparation est volontaire : un contrôle qui lit la production ne doit pas automatiquement posséder le droit de la modifier.

### Push et pull request

Un push ou une pull request ne doit jamais recevoir les secrets de connexion Supabase production, exécuter un contrôle distant authentifié ni modifier Supabase production.

Sur ces événements, le workflow reste **strictement local**. Il peut seulement :
- valider le dépôt, le ledger, le lot revu et les contrats de sécurité;
- construire le workspace protégé.

La Supabase CLI elle-même ne doit être ni installée ni vérifiée sur `pull_request` ou `push`; son installation et sa vérification sont réservées au lancement manuel `workflow_dispatch`.

Les étapes qui référencent `SUPABASE_ACCESS_TOKEN`, `SUPABASE_DB_PASSWORD` ou un autre secret production doivent être inaccessibles sur `pull_request` et `push`, même pour une branche interne au dépôt. Cette séparation reste obligatoire indépendamment des protections de branche GitHub.

Un run vert de PR ou de push signifie **prévol local réussi**, pas « production validée à distance » et pas « production synchronisée ».

### Lancement manuel `apply=false`

Le lancement manuel `workflow_dispatch` avec `apply=false` est la seule voie générique autorisée à utiliser les secrets de connexion pour un prévol distant en lecture/non destructif.

Il exige les secrets de connexion afin que les contrôles distants soient réellement exécutés. Il peut lier le workspace protégé, lire l’inventaire et l’historique, exécuter les lints et `db push --dry-run`, mais `apply=false` interdit toute écriture.

La valeur de confirmation par défaut est `PREFLIGHT_ONLY`. Elle doit rester non mutante.

Un run vert avec `apply=false` signifie **prévol distant réussi**, pas « production modifiée ».

### Lancement manuel `apply=true`

L’application réelle n’est autorisée que si toutes les conditions suivantes sont réunies :

1. événement `workflow_dispatch`;
2. `apply=true`;
3. le champ `confirmation` vaut exactement `APPLY-SUPABASE-PRODUCTION`;
4. le workflow est lancé depuis `main` (`refs/heads/main`), jamais depuis une branche de travail;
5. le prévol local et le prévol distant sont tous deux réussis;
6. les secrets de connexion sont détectés comme prêts;
7. le job d’écriture franchit l’Environment GitHub `production` avant toute mutation.

Le job `apply-production` reconstruit ensuite le workspace protégé et revalide le dépôt, le ledger, la cible liée, le lint SQL, l’historique distant et un nouveau `db push --dry-run` **après** la frontière de l’Environment. Aucune écriture ne doit précéder cette revalidation.

Les étapes capables de modifier la production conservent en plus leur garde locale `workflow_dispatch + apply=true + auth`. Ce verrou redondant est intentionnel : retirer la garde d’une étape ne doit pas suffire à la rendre exécutable ailleurs.

### Frontière humaine de l’Environment `production`

Le rattachement `environment: production` permet à GitHub d’appliquer les protections configurées pour cet Environment, notamment des reviewers requis lorsque le plan et les réglages du dépôt le permettent.

**Le YAML ne peut pas prouver à lui seul qu’un reviewer obligatoire est configuré dans les réglages GitHub.** Tant que ce réglage n’a pas été vérifié côté dépôt, ne pas présenter l’Environment comme une approbation humaine garantie. La confirmation textuelle `APPLY-SUPABASE-PRODUCTION` reste donc obligatoire même si une règle de reviewer est ensuite ajoutée.

Principe SINJIRA : l’humain garde la décision finale avant toute écriture sensible. Aucun automatisme, agent ou tâche récurrente ne doit transformer un prévol vert en application automatique.

La production n’est considérée synchronisée que lorsque le résumé final affiche exactement :

`✅ APPLIQUÉ ET VÉRIFIÉ`

Un run nommé `APPLICATION DEMANDÉE` n’est **pas** une preuve d’application réussie. En cas d’échec ou de synchronisation partielle, arrêter la procédure et diagnostiquer la première étape en échec.

## Rollout ciblé d’un module sensible

Un rollout ciblé validé (par exemple Coffre des consciences, Emploi ou Mon IA) peut être appliqué séparément si son contrat impose une migration précise et un périmètre plus étroit que le workflow générique.

Dans ce cas :

1. CI du lot entièrement verte;
2. fusion sur `main` avant écriture production;
3. baseline distante relue immédiatement avant l’application;
4. migration(s) appliquée(s) une par une avec nom et SQL exacts;
5. uniquement les Edge Functions explicitement autorisées sont déployées;
6. vérifications SQL/Edge/advisors post-déploiement;
7. **réconciliation immédiate du ledger** avec les versions distantes réellement générées avant toute future synchronisation générique.

Ne jamais substituer à cette procédure un `db push --include-all`, `supabase migration repair`, `supabase db reset --linked` ou un déploiement global d’Edge Functions non borné.

## Secrets GitHub Actions requis

À configurer hors dépôt dans :

`GitHub → Settings → Secrets and variables → Actions`

Secrets de connexion indispensables :
- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_DB_PASSWORD`

Secrets optionnels :
- `RESEND_API_KEY` — courriels transactionnels;
- `OPENAI_API_KEY` — génération IA optionnelle dans les workflows qui l’autorisent explicitement.

Variable optionnelle :
- `OPENAI_CHARACTER_MODEL`

**Ne jamais écrire la valeur d’un secret dans le dépôt, une issue, un log, une PR, un message de documentation ou une sortie de commande.**

L’absence des secrets de connexion ne doit jamais être contournée par un token commité, un fichier `.env` ajouté au dépôt, une valeur collée dans une commande ou une autre voie d’écriture improvisée.

Le prévol distant utilise ces secrets sous forme d’`env` borné aux étapes qui en ont besoin. Le job d’application réévalue leur présence après la frontière `production`; aucun secret de connexion ne doit être promu au niveau global du workflow ou d’un job entier.

## Ledger de production

Le fichier `supabase/production-migration-ledger.txt` contient les versions déjà appliquées dans `gpvivleexywljowcqkru`.

État hébergé vérifié au **2026-09-07** :

- `186` versions distantes;
- première version : `20260809050252_sinjira_universal_platform`;
- dernière version : `20260906035442_sinjira_v25_device_challenge_continuity_hardening`.

Règles :
- ne jamais modifier rétroactivement une version déjà enregistrée;
- ne jamais supprimer une ancienne ligne du ledger;
- une future migration doit utiliser un timestamp supérieur au dernier timestamp du ledger;
- après une application réussie en production, ajouter la **version distante réellement créée** au ledger dans la PR/commit suivant avant toute nouvelle migration ou synchronisation générique;
- ne pas supposer que le timestamp d’un fichier local correspond au timestamp distant : pour les rollouts ciblés, Supabase peut enregistrer une autre version.

Le script `scripts/validate_production_migration_ledger.py` vérifie notamment :
- nombre attendu de versions;
- tri et unicité;
- première/dernière version connues;
- suffixe V24.5.54/V25 exact;
- exactitude du workspace protégé;
- absence de DDL dans les marqueurs déjà appliqués;
- transmission des migrations futures;
- contrat de la voie générique unique de production;
- absence de l’ancien workflow générique redondant;
- cohérence de ce runbook avec la baseline du ledger et les garde-fous d’application.

Le workflow `Validation du ledger Supabase production` doit être déclenché lorsqu’un changement touche le runbook, le workflow canonique, l’ancien chemin retiré ou le garde historique, afin qu’une seconde voie d’écriture ou une documentation obsolète ne puisse pas être fusionnée silencieusement.

## Reconstruction d’une base neuve

Pour une base neuve ou une branche de développement, utiliser l’historique fonctionnel complet de `supabase/migrations/`, pas les marqueurs du ledger.

`scripts/validate_production_schema_manifest.py` vérifie que l’historique local recrée toutes les tables actuellement attendues en production.

Les migrations V22 restaurées depuis le registre de production sont intentionnelles : elles fournissent les fondations sécurité/famille/Monde parallèle avant les migrations V24.4.12 qui les durcissent et les convergent vers l’architecture actuelle.

## Vérifications post-déploiement minimales

Après toute application réelle, vérifier :
- le ledger distant et le dry-run final depuis le workspace protégé;
- l’inventaire des Edge Functions attendu;
- `get_sinjira_server_version()` = version plateforme attendue;
- `get_sinjira_runtime_health().ok = true`;
- `fracture_engine_health().ok = true` et version moteur attendue;
- compte propriétaire AbyssTime;
- accès Fracture propriétaire;
- Registre : persistance avant courriel;
- Monde parallèle : adhésion personnage canonique;
- aucun FK public sans index couvrant;
- Performance Advisor sans WARN bloquant;
- Security Advisor : distinguer les frontières métier `SECURITY DEFINER` intentionnelles des vrais risques.

## Avertissement Auth actuel — mots de passe compromis

Au 2026-09-07, le Security Advisor peut encore signaler :

`auth_leaked_password_protection` — **Leaked Password Protection Disabled**.

Ce point reste ouvert tant que la protection n’est pas effectivement activée et vérifiée. La fonctionnalité Supabase correspondante peut nécessiter un plan payant; **ne jamais activer un plan payant sans autorisation explicite**.

Ce réglage est un paramètre du service Auth hébergé : ce n’est pas une migration PostgreSQL et il ne doit pas être simulé par du SQL, une policy RLS ou une modification de `auth.users`.

### Procédure d’activation autorisée après autorisation explicite

1. ouvrir le projet `gpvivleexywljowcqkru`;
2. ouvrir les réglages Authentication/Auth du fournisseur Email;
3. conserver ou renforcer les exigences de mot de passe existantes — ne pas abaisser la longueur minimale de `12` utilisée par SINJIRA;
4. activer la protection contre les mots de passe compromis si le plan et l’autorisation le permettent;
5. enregistrer le réglage;
6. rouvrir Security Advisor;
7. confirmer que `auth_leaked_password_protection` / `Leaked Password Protection Disabled` n’apparaît plus.

Ne pas contourner une limitation de plan par une implémentation maison non auditée dans le client.

### Critère de fermeture

Ce point n’est fermé que lorsque **les deux** conditions sont vraies :

- le Dashboard indique la protection activée;
- une nouvelle lecture du Security Advisor ne contient plus `auth_leaked_password_protection`.

Ne jamais consigner de mot de passe, token ou secret utilisé pendant la vérification.

## MFA globale

Ne pas imposer une MFA globale avant validation complète du parcours d’enrôlement/récupération, afin d’éviter de verrouiller des comptes légitimes. Les zones sensibles qui exigent AAL2 (Coffre des consciences, Mon IA, opérations privées correspondantes) conservent leurs propres exigences non désactivables.

## En cas de divergence de migrations

Ne pas utiliser `supabase migration repair`, `supabase db reset --linked`, `db push --include-all` ou modifier `supabase_migrations.schema_migrations` à l’aveugle.

Procédure :
1. arrêter toute application;
2. comparer `supabase migration list --linked` depuis le workspace protégé;
3. lire le registre distant;
4. récupérer les instructions exactes si nécessaire;
5. corriger le ledger ou l’historique de reconstruction dans une PR dédiée;
6. repasser toutes les validations avant toute écriture.
