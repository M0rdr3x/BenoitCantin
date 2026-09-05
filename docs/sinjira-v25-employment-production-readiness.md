# SINJIRA V25 — État et exploitation production Emploi

État vérifié le **2026-09-05**.  
Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`).  
Preuve détaillée : `docs/sinjira-v25-employment-production-deployment-2026-09-05.md`.

## Principe

**L’HUMAIN AVANT TOUT.** Emploi est un espace volontaire de profil professionnel et de suivi personnel de candidatures. Il reste strictement séparé :

- du Registre personnel des consciences;
- de Rencontres;
- de Histoire de vie;
- du Mode Voyage et des signaux de sécurité;
- de Mon IA;
- de la publicité et du profilage inter-module.

Cette fondation ne crée aucun catalogue d’offres. Toute future place de marché devra faire l’objet d’un lot séparé avec organisations/employeurs vérifiés, offres réelles, signalement, anti-fraude et règles de confidentialité propres.

## État production vérifié

Baseline avant Emploi :

`20260905131659_sinjira_v25_conscience_vault_audit_session_index`

Migration Emploi réellement appliquée immédiatement après :

`20260905133130_sinjira_v25_employment_foundation`

Le lot historique gelé reste :

`2077ca7ff3a0ec77a27a908a9379e92149a4e0a5`

Ce SHA contient Emploi Web/mobile et précède volontairement les migrations Mon IA.

## Schéma production

`public.employment_profiles` et `public.employment_applications` existent en production.

Pour chacune :

- RLS activé;
- RLS forcé;
- quatre policies propriétaire;
- aucun CRUD `anon`;
- accès `authenticated` borné par `auth.uid()`.

Les seules clés étrangères du module pointent vers `auth.users`.

Aucune table `public.employment_job_listings` n’existe.

Au contrôle immédiatement après rollout :

- `employment_profiles` : `0` ligne;
- `employment_applications` : `0` ligne.

## Contrat applicatif

Le module Web :

- dérive l’identité avec `supabase.auth.getUser()`;
- filtre les lectures et mutations sur l’utilisateur courant;
- ne persiste aucune donnée Emploi dans `localStorage` ou `sessionStorage`;
- rend les données utilisateur avec `textContent`, pas `innerHTML`;
- limite les URL externes à HTTP/HTTPS et utilise `noopener noreferrer`;
- ne lit aucune table Rencontres, Sécurité, Registre, Histoire de vie ou registre narratif.

L’application mobile réutilise la route Web existante et ne crée pas un stockage Emploi natif parallèle.

## CI validée avant rollout

La PR #176 a passé sans échec :

- le contrat Emploi;
- le garde de production ciblé;
- la classification du schéma;
- les **31 assertions pgTAP** Emploi;
- les tests navigateur Chromium, Firefox et WebKit;
- Lighthouse mobile;
- la validation générale du site;
- les garde-fous secrets et advisor déclenchés.

La PR #176 a été fusionnée par squash sur `main` au commit :

`7103a6344ebfa61248b38cf82d59ac9252429142`

## Advisors après rollout

Aucun nouveau problème de sécurité spécifique à Emploi n’a été signalé.

Les deux index Emploi sont signalés `unused_index` au niveau `INFO`, ce qui est attendu avec zéro candidature et ne justifie pas leur suppression.

Référence performance : https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index

L’avertissement global **Leaked Password Protection Disabled** reste ouvert côté Supabase Auth hébergé.

Référence : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Vérification post-déploiement

`.github/workflows/sinjira-v25-employment-production.yml` est désormais destiné à être un **vérificateur lecture seule** :

- `workflow_dispatch` uniquement;
- confirmation exacte `VERIFY-SINJIRA-V25-EMPLOYMENT`;
- environnement GitHub `production`;
- lecture de l’historique des migrations via l’API de gestion;
- vérification que `20260905133130_sinjira_v25_employment_foundation` suit immédiatement la baseline du coffre;
- aucune migration appliquée;
- aucune Edge Function déployée;
- aucun secret modifié.

## Smoke tests encore à faire

Les tests authentifiés nécessitent un compte de test non sensible. Ils ne sont pas déclarés réussis tant qu’ils n’ont pas été réellement exécutés.

À vérifier :

1. créer/modifier/supprimer un profil professionnel factice;
2. ajouter/modifier/supprimer une candidature fictive clairement identifiée comme test;
3. confirmer qu’un autre compte ne peut pas lire ces données;
4. confirmer qu’une URL non HTTP/HTTPS est refusée;
5. confirmer qu’aucune donnée Emploi n’est écrite dans les stockages persistants du navigateur.

Ne pas utiliser de vraie candidature, CV, employeur réel ou note personnelle pendant ces smoke tests.

## Manifeste production

`employment_profiles` et `employment_applications` doivent désormais rester dans `EXPECTED_TABLES` de `scripts/validate_production_schema_manifest.py`.

Les tables Mon IA restent dans `PLANNED_LOCAL_TABLES` tant que leur propre lot n’a pas été audité et déployé séparément.

## Incident / rollback

Dès qu’une donnée Emploi réelle existe :

1. ne pas supprimer automatiquement les tables;
2. désactiver l’accès applicatif si nécessaire;
3. préserver les données privées;
4. corriger par une nouvelle migration;
5. revalider RLS, isolation propriétaire et séparation inter-module avant réouverture.

Emploi ne doit jamais devenir une source automatique pour le Registre personnel, Rencontres, Histoire de vie, Mode Voyage, sécurité ou Mon IA.
