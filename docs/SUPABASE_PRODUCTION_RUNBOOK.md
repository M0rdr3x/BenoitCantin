# SINJIRA™ — Runbook Supabase production

## Règle absolue

Ne jamais exécuter un `supabase db push --linked` directement depuis le dossier `supabase/migrations/` du dépôt contre la production SINJIRA™.

Le dépôt conserve deux réalités complémentaires :

- `supabase/migrations/` : historique **fonctionnel de reconstruction**, utilisé pour recréer/tester une base neuve;
- `supabase/production-migration-ledger.txt` : versions **réellement enregistrées** dans la production liée.

L’historique de reconstruction contient du SQL consolidé et des timestamps de travail qui ne correspondent pas tous au registre distant. Le workspace protégé `.prod-workspace/supabase` est donc obligatoire pour toute opération générique liée à la production.

## Voie canonique — `Supabase production — prévol / synchronisation contrôlée`

Le workflow canonique est `.github/workflows/supabase-production-preflight.yml`.

Son nom de run doit rendre l’intention visible :

- push ou pull request : `Supabase production — PRÉVOL`;
- lancement manuel avec `apply=false` : prévol seulement;
- lancement manuel avec `apply=true` : `Supabase production — APPLICATION DEMANDÉE`.

### Push et pull request

Un push ou une pull request ne doit jamais modifier Supabase production.

Le workflow peut :
- valider le dépôt;
- construire le workspace protégé;
- effectuer les vérifications distantes si les secrets GitHub Actions requis sont disponibles;
- exécuter lint, inventaire, comparaison du ledger et `db push --dry-run` depuis le workspace protégé.

Si les secrets de connexion sont absents sur un push ou une pull request, les étapes distantes sont ignorées et le run reste un prévol local non destructif. Cet état signifie **NON SYNCHRONISÉ**, pas « production validée à distance ».

### Lancement manuel `apply=false`

Un lancement manuel de prévol exige les secrets de connexion afin que les contrôles distants soient réellement exécutés. `apply=false` interdit toute écriture.

Un run vert avec `apply=false` signifie **prévol réussi**, pas « production modifiée ».

### Lancement manuel `apply=true`

L’application réelle n’est autorisée que si les trois conditions sont réunies :

1. événement `workflow_dispatch`;
2. `apply=true`;
3. secrets de connexion détectés comme prêts.

Les étapes capables de modifier la production doivent conserver ce triple verrou. La production n’est considérée synchronisée que lorsque le résumé final affiche exactement :

`✅ APPLIQUÉ ET VÉRIFIÉ`

Un run nommé `APPLICATION DEMANDÉE` n’est **pas** une preuve d’application réussie. En cas d’échec ou de synchronisation partielle, arrêter la procédure et diagnostiquer la première étape en échec.

## Voie secondaire manuelle — `Synchroniser Supabase production — sécurisé`

Le workflow `.github/workflows/supabase-production-safe.yml` reste une voie manuelle secondaire. Il ne doit pas devenir une voie automatique ni contourner le workflow canonique.

Contraintes minimales :
- déclenchement `workflow_dispatch` uniquement;
- `SUPABASE_ACCESS_TOKEN` et `SUPABASE_DB_PASSWORD` obligatoires avant toute liaison distante;
- `apply=false` = prévol uniquement;
- `apply=true` = migrations futures et Edge Functions depuis le workspace protégé;
- aucune primitive de réparation destructive ou de réécriture d’historique.

Par défaut, préférer le workflow canonique `Supabase production — prévol / synchronisation contrôlée`, car son état `PRÉVOL` / `APPLICATION DEMANDÉE` et son verdict final sont explicitement verrouillés par le validateur du ledger.

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
- contrat des workflows génériques de production;
- cohérence de ce runbook avec la baseline du ledger et les garde-fous d’application.

Le workflow `Validation du ledger Supabase production` doit être déclenché lorsqu’un changement touche ce runbook, afin qu’une documentation obsolète ne puisse pas être fusionnée silencieusement.

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
