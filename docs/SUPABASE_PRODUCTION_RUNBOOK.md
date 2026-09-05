# SINJIRA™ — Runbook Supabase production

## Règle absolue

Ne jamais exécuter un `supabase db push --linked` directement depuis le dossier `supabase/migrations/` du dépôt contre la production SINJIRA™.

Le dépôt conserve deux réalités complémentaires :

- `supabase/migrations/` : historique **fonctionnel de reconstruction**, utilisé pour recréer/tester une base neuve;
- `supabase/production-migration-ledger.txt` : versions **réellement enregistrées** dans la production liée.

L’historique de reconstruction contient du SQL consolidé et des timestamps de travail qui ne correspondent pas tous au registre distant. Le workspace protégé est donc obligatoire pour toute opération générique liée à la production.

## Workflows autorisés

### 1. `Prévol Supabase production — lecture seule`

Usage : audit seulement.

Ce workflow peut :
- valider le dépôt;
- construire le workspace protégé;
- lier la copie temporaire à Supabase;
- exécuter `db lint`;
- comparer le ledger;
- exécuter `db push --dry-run`.

Il **ne doit jamais** :
- exécuter un `db push` réel;
- modifier les secrets;
- déployer les Edge Functions;
- modifier les données ou le schéma de production.

### 2. `Synchroniser Supabase production — sécurisé`

Usage : voie GitHub Actions générique autorisée pour appliquer de nouvelles migrations ou redéployer les Edge Functions lorsqu’un rollout ciblé dédié n’est pas utilisé.

Avant application, ce workflow :
1. valide le schéma reconstructible;
2. valide **toutes** les versions déjà enregistrées dans le ledger;
3. construit `.prod-workspace/supabase`;
4. remplace les migrations déjà appliquées par des marqueurs no-op aux timestamps exacts de production;
5. copie uniquement les migrations futures dont la version est supérieure au dernier timestamp du ledger;
6. effectue lint + `migration list` + dry-run;
7. n’écrit que si `apply=true`;
8. refait lint + ledger + dry-run après application.

Un workflow vert avec `apply=false` signifie **prévol réussi**, pas « production modifiée ».

La production n’est considérée synchronisée par ce workflow que s’il a été lancé avec `apply=true` et que sa vérification finale est verte.

### 3. Rollout ciblé d’un module sensible

Un rollout ciblé validé (par exemple Coffre des consciences, Emploi ou Mon IA) peut être appliqué séparément si son contrat impose une migration précise et un périmètre plus étroit que le workflow générique.

Dans ce cas :

1. CI du lot entièrement verte;
2. fusion sur `main` avant écriture production;
3. baseline distante relue immédiatement avant l’application;
4. migration(s) appliquée(s) une par une avec nom et SQL exacts;
5. uniquement les Edge Functions explicitement autorisées sont déployées;
6. vérifications SQL/Edge/advisors post-déploiement;
7. **réconciliation immédiate du ledger** avec les versions distantes réellement générées avant toute future synchronisation générique.

Ne jamais substituer à cette procédure un `db push --include-all`, `migration repair`, `db reset --linked` ou un déploiement global d’Edge Functions.

## Secrets GitHub Actions requis

À configurer dans :

`GitHub → Settings → Secrets and variables → Actions`

Secrets de connexion indispensables :
- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_DB_PASSWORD`

Secrets optionnels :
- `RESEND_API_KEY` — courriels transactionnels;
- `OPENAI_API_KEY` — génération IA optionnelle;

Variable optionnelle :
- `OPENAI_CHARACTER_MODEL`

**Ne jamais écrire la valeur d’un secret dans le dépôt, une issue, un log, une PR ou un message de documentation.**

## Ledger de production

Le fichier `supabase/production-migration-ledger.txt` contient les versions déjà appliquées dans `gpvivleexywljowcqkru`.

État réconcilié au 2026-09-05 :

- `185` versions distantes;
- première version : `20260809050252_sinjira_universal_platform`;
- dernière version : `20260905150553_sinjira_v25_personal_ai_audit_user_index`.

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
- transmission des migrations futures.

## Reconstruction d’une base neuve

Pour une base neuve ou une branche de développement, utiliser l’historique fonctionnel complet de `supabase/migrations/`, pas les marqueurs du ledger.

`scripts/validate_production_schema_manifest.py` vérifie que l’historique local recrée toutes les tables actuellement attendues en production.

Les migrations V22 restaurées depuis le registre de production sont intentionnelles : elles fournissent les fondations sécurité/famille/Monde parallèle avant les migrations V24.4.12 qui les durcissent et les convergent vers l’architecture actuelle.

## Vérifications post-déploiement minimales

Après toute application réelle, vérifier :
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

Au 2026-09-05, le Security Advisor signale encore :

`auth_leaked_password_protection` — **Leaked Password Protection Disabled**.

Ce WARN est **ouvert**. Ne jamais écrire qu’il est corrigé tant que le Security Advisor le retourne.

### Ce que fait le réglage

Supabase Auth peut refuser les mots de passe connus comme compromis en les vérifiant contre le service Pwned Passwords de HaveIBeenPwned. Selon la documentation Supabase actuelle, cette protection est disponible sur le **plan Pro et supérieur**.

Ce réglage est un paramètre du service Auth hébergé : ce n’est pas une migration PostgreSQL et il ne doit pas être simulé par du SQL, une policy RLS ou une modification de `auth.users`.

### Procédure d’activation autorisée

La connexion Supabase utilisée par l’assistant n’expose actuellement aucune mutation de configuration Auth pour ce réglage. L’activation doit donc être faite dans le Dashboard Supabase par un opérateur autorisé :

1. ouvrir le projet `gpvivleexywljowcqkru`;
2. ouvrir **Authentication / Auth settings**, section du fournisseur **Email**;
3. conserver ou renforcer les exigences de mot de passe existantes — ne pas abaisser la longueur minimale de `12` utilisée par la configuration SINJIRA;
4. activer **Prevent the use of leaked passwords / Leaked password protection**;
5. enregistrer le réglage;
6. rouvrir **Security Advisor**;
7. confirmer que `auth_leaked_password_protection` / `Leaked Password Protection Disabled` n’apparaît plus.

Si l’option n’est pas disponible, vérifier d’abord le niveau de plan du projet. Ne pas contourner la limitation par une implémentation maison non auditée dans le client.

### Critère de fermeture

Ce point n’est fermé que lorsque **les deux** conditions sont vraies :

- le Dashboard indique la protection activée;
- une nouvelle lecture du Security Advisor ne contient plus `auth_leaked_password_protection`.

Après fermeture, consigner la date et le résultat du Security Advisor dans une PR documentaire dédiée. Ne jamais consigner de mot de passe, token ou secret utilisé pendant la vérification.

### Effet sur les utilisateurs existants

Renforcer la politique ne nécessite pas de modifier directement les hashes de mot de passe. Ne pas forcer une réinitialisation massive depuis SQL. Toute expérience de récupération/changement de mot de passe doit continuer à préserver l’accès des utilisateurs légitimes et les mécanismes de récupération sécurisés.

Référence officielle : `https://supabase.com/docs/guides/auth/password-security`.

## MFA globale

Ne pas imposer une MFA globale avant validation complète du parcours d’enrôlement/récupération, afin d’éviter de verrouiller des comptes légitimes. Les zones sensibles qui exigent AAL2 (Coffre des consciences, Mon IA, opérations privées correspondantes) conservent leurs propres exigences non désactivables.

## En cas de divergence de migrations

Ne pas utiliser `migration repair` ou modifier `supabase_migrations.schema_migrations` à l’aveugle.

Procédure :
1. arrêter toute application;
2. comparer `supabase migration list --linked` depuis le workspace protégé;
3. lire le registre distant;
4. récupérer les instructions exactes si nécessaire;
5. corriger le ledger ou l’historique de reconstruction dans une PR dédiée;
6. repasser toutes les validations avant toute écriture.
