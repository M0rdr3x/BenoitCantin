# SINJIRA™ — Runbook Supabase production

## Règle absolue

Ne jamais exécuter un `supabase db push --linked` directement depuis le dossier `supabase/migrations/` du dépôt contre la production SINJIRA™.

Le dépôt conserve deux réalités complémentaires :

- `supabase/migrations/` : historique **fonctionnel de reconstruction**, utilisé pour recréer/tester une base neuve;
- `supabase/production-migration-ledger.txt` : versions **réellement enregistrées** dans la production liée.

L’historique de reconstruction contient du SQL consolidé et des timestamps de travail qui ne correspondent pas tous au registre distant. Le workspace protégé est donc obligatoire pour toute opération liée à la production.

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

Usage : seule voie GitHub Actions autorisée pour appliquer de nouvelles migrations ou redéployer les Edge Functions.

Avant application, ce workflow :
1. valide le schéma reconstructible;
2. valide les 62 versions déjà enregistrées dans le ledger;
3. construit `.prod-workspace/supabase`;
4. remplace les migrations déjà appliquées par des marqueurs no-op aux timestamps exacts de production;
5. copie uniquement les migrations futures dont la version est supérieure au dernier timestamp du ledger;
6. effectue lint + `migration list` + dry-run;
7. n’écrit que si `apply=true`;
8. refait lint + ledger + dry-run après application.

Un workflow vert avec `apply=false` signifie **prévol réussi**, pas « production modifiée ».

La production n’est considérée synchronisée par GitHub Actions que si le workflow sécurisé a été lancé avec `apply=true` et que sa vérification finale est verte.

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

Règles :
- ne jamais modifier rétroactivement une version déjà enregistrée;
- ne jamais supprimer une ancienne ligne du ledger;
- une future migration doit utiliser un timestamp supérieur au dernier timestamp du ledger;
- après une application réussie en production, ajouter la nouvelle version réelle au ledger dans la PR/commit suivant avant toute nouvelle migration.

Le script `scripts/validate_production_migration_ledger.py` vérifie notamment :
- nombre attendu de versions;
- tri et unicité;
- première/dernière version connues;
- exactitude du workspace protégé;
- absence de DDL dans les marqueurs déjà appliqués;
- transmission des migrations futures.

## Reconstruction d’une base neuve

Pour une base neuve ou une branche de développement, utiliser l’historique fonctionnel complet de `supabase/migrations/`, pas les marqueurs du ledger.

`scripts/validate_production_schema_manifest.py` vérifie que l’historique local recrée toutes les tables publiques actuellement attendues en production.

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

## Avertissement Auth actuel

La protection Supabase contre les **mots de passe compromis** doit être activée dès qu’un canal de configuration Auth vérifiable est disponible. Ne pas prétendre qu’elle est active tant que le Security Advisor signale `Leaked Password Protection Disabled`.

Ne pas imposer une MFA globale avant validation complète du parcours d’enrôlement/récupération, afin d’éviter de verrouiller des comptes légitimes.

## En cas de divergence de migrations

Ne pas utiliser `migration repair` ou modifier `supabase_migrations.schema_migrations` à l’aveugle.

Procédure :
1. arrêter toute application;
2. comparer `supabase migration list --linked` depuis le workspace protégé;
3. lire le registre distant;
4. récupérer les instructions exactes si nécessaire;
5. corriger le ledger ou l’historique de reconstruction dans une PR dédiée;
6. repasser toutes les validations avant toute écriture.
