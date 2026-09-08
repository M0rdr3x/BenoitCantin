# SINJIRA™ — Lot de migrations Supabase production revu

## But

Le workflow générique de production ne doit jamais transmettre automatiquement une migration simplement parce que son timestamp est postérieur au dernier timestamp du ledger.

Le fichier canonique `supabase/production-reviewed-migration-batch.txt` constitue l'autorisation explicite du prochain lot de migrations transmissibles par le workspace protégé.

## Règle fail-closed

`scripts/build_supabase_production_workspace.py` compare avant toute construction :

1. le dernier timestamp de `supabase/production-migration-ledger.txt`;
2. toutes les migrations locales dont le timestamp est supérieur à ce cutoff;
3. la liste ordonnée du lot revu;
4. l'empreinte Git blob SHA-1 du contenu de chaque migration revue.

Le builder échoue si :

- une nouvelle migration locale n'est pas inscrite dans le lot revu;
- une migration inscrite a disparu;
- l'ordre ou un timestamp est invalide;
- une version du lot est déjà couverte par le ledger;
- le contenu d'une migration revue a changé après la revue.

Aucun workspace de production n'est alors construit. Le préflight canonique exécute le validateur du ledger avant toute étape de connexion distante; ce validateur construit lui-même un workspace temporaire et exerce donc ce garde.

## Lot actuellement revu

Baseline production connue : `20260906035442_sinjira_v25_device_challenge_continuity_hardening`.

Le lot revu contient actuellement neuf migrations, de :

- `20260907145100_sinjira_v25_security_push_receipt_queue.sql`
- à `20260908150000_sinjira_v25_live_social_share_codes.sql`

La liste complète et les empreintes sont volontairement conservées dans `supabase/production-reviewed-migration-batch.txt`, pas dupliquées ici.

## Ajouter une nouvelle migration

Une nouvelle migration postérieure au cutoff doit faire échouer la validation tant que le lot revu n'est pas mis à jour intentionnellement.

Pour l'autoriser :

1. faire relire la migration et ses tests;
2. ajouter sa ligne à la fin du fichier de lot, dans l'ordre des timestamps;
3. utiliser l'empreinte Git blob exacte du contenu revu;
4. repasser `python scripts/validate_production_migration_ledger.py` et toute la CI concernée;
5. ne jamais considérer cette revue comme une autorisation d'écrire en production.

L'écriture réelle reste soumise au workflow manuel canonique, à `apply=true`, aux secrets GitHub Actions requis et à toutes les vérifications distantes.

## Après une application production réussie

Après une application réellement vérifiée :

1. réconcilier `supabase/production-migration-ledger.txt` avec les versions distantes réellement enregistrées;
2. retirer du lot revu les migrations désormais couvertes par le ledger;
3. conserver uniquement les migrations locales encore futures;
4. repasser la validation avant toute nouvelle synchronisation.

Ne jamais contourner une divergence avec `db push --include-all`, `supabase migration repair`, `supabase db reset --linked`, un secret commité ou une voie d'écriture parallèle.

## Blocage actuel

Ce garde améliore la sûreté du futur déploiement, mais ne débloque pas la production à lui seul. Tant que le blocage opérationnel suivi par l'issue #240 n'est pas résolu, aucune application Supabase hébergée ne doit être effectuée.
