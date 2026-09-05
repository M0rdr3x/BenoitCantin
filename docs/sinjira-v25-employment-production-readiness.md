# SINJIRA V25 — Readiness production Emploi

État préparatoire vérifié le **2026-09-05**.  
Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`).

## Principe

**L’HUMAIN AVANT TOUT.** Emploi est un espace volontaire de profil professionnel et de suivi personnel de candidatures. Il reste strictement séparé :

- du Registre personnel des consciences;
- de Rencontres;
- de Histoire de vie;
- du Mode Voyage et des signaux de sécurité;
- de Mon IA;
- de la publicité et du profilage inter-module.

Cette fondation **ne crée aucun catalogue d’offres** et ne prétend pas fournir des offres d’emploi vérifiées. Toute future place de marché devra faire l’objet d’un lot distinct avec organisations/employeurs vérifiés, offres réelles, signalement et anti-fraude.

## État production avant rollout

Contrôle en lecture seule du 2026-09-05 :

- `public.employment_profiles` : absent;
- `public.employment_applications` : absent;
- migration distante `sinjira_v25_employment_foundation` : absente.

La dernière migration production observée est :

`20260905131659_sinjira_v25_conscience_vault_audit_session_index`

Cette version constitue la baseline obligatoire du rollout Emploi ciblé.

## Lot Git gelé

SHA :

`2077ca7ff3a0ec77a27a908a9379e92149a4e0a5`

Ce SHA correspond à l’état après l’ajout d’Emploi à la navigation mobile et avant les migrations Mon IA.

Vérifications effectuées :

- `20260904225000_sinjira_v25_employment_foundation.sql` est présent;
- la migration Mon IA `20260905000500_sinjira_v25_personal_ai_foundation.sql` est absente à ce SHA;
- la migration Mon IA de durcissement `20260905001000_sinjira_v25_personal_ai_rls_hardening.sql` est absente à ce SHA.

## Migration autorisée

Une seule migration peut être appliquée :

`20260904225000_sinjira_v25_employment_foundation.sql`

Nom distant attendu :

`sinjira_v25_employment_foundation`

Elle crée uniquement :

- `public.employment_profiles`;
- `public.employment_applications`;
- deux index de suivi des candidatures;
- les politiques RLS propriétaire nécessaires.

Aucune Edge Function n’est requise pour cette fondation.

## Contrat SQL

### `employment_profiles`

- clé primaire `user_id` liée à `auth.users` avec suppression en cascade;
- données professionnelles volontairement saisies;
- états de recherche bornés;
- préférences de travail bornées;
- maximum 30 compétences;
- longueurs SQL bornées;
- RLS activé et forcé;
- quatre policies propriétaire `SELECT/INSERT/UPDATE/DELETE` basées sur `auth.uid()`.

### `employment_applications`

- identifiant UUID;
- propriétaire `user_id` lié à `auth.users`;
- organisation et poste obligatoires et bornés;
- URL source limitée à HTTP/HTTPS et 2048 caractères;
- états de candidature bornés;
- notes privées bornées;
- RLS activé et forcé;
- quatre policies propriétaire `SELECT/INSERT/UPDATE/DELETE` basées sur `auth.uid()`.

## Contrat Web/mobile

Le module Web :

- dérive l’identité de `supabase.auth.getUser()`;
- filtre les lectures et mutations sur l’utilisateur courant;
- ne persiste aucune donnée Emploi dans `localStorage` ou `sessionStorage`;
- rend les données utilisateur avec `textContent`, pas `innerHTML`;
- valide les URL HTTP/HTTPS avant affichage;
- ouvre les liens externes avec `noopener noreferrer`;
- ne lit aucune table Rencontres, Sécurité, Registre, Histoire de vie ou registre narratif.

L’application mobile utilise la route Web existante; elle ne crée pas un second stockage Emploi natif.

## Tests existants

`supabase/tests/employment_v25.test.sql` contient **31 assertions pgTAP** couvrant notamment :

- présence des deux tables;
- RLS activé et forcé;
- absence de lecture `anon`;
- CRUD `authenticated` borné par RLS;
- huit policies propriétaire;
- absence de table de fausses offres;
- absence de FK vers d’autres modules SINJIRA;
- bornes des états, compétences et URL.

Le workflow `.github/workflows/sinjira-employment-v25.yml` reconstruit la base locale et exécute ces tests.

## Voie de déploiement ciblée

Workflow :

`.github/workflows/sinjira-v25-employment-production.yml`

Garde-fous :

- `workflow_dispatch` uniquement;
- confirmation exacte `DEPLOY-SINJIRA-V25-EMPLOYMENT`;
- environnement GitHub `production`;
- `SUPABASE_ACCESS_TOKEN` requis;
- checkout du SHA gelé `2077ca7f...`;
- baseline distante exacte `20260905131659_sinjira_v25_conscience_vault_audit_session_index`;
- historique après baseline autorisé seulement vide ou contenant déjà l’unique migration Emploi;
- application par l’API de migrations Supabase;
- idempotence par nom de migration;
- aucune Edge Function;
- aucun `db push`;
- aucune migration Mon IA.

Si une migration inattendue apparaît après la baseline avant le rollout Emploi, **arrêter le déploiement** et refaire le readiness; ne pas forcer l’historique.

## Contrôles post-déploiement obligatoires

Après application, vérifier en lecture seule :

1. l’historique contient une seule migration après la baseline, nommée `sinjira_v25_employment_foundation`;
2. les deux tables existent;
3. RLS est activé et forcé sur les deux tables;
4. les 8 policies propriétaire existent;
5. `anon` n’a aucun CRUD utile sur les deux tables;
6. un utilisateur authentifié ne peut lire/modifier que ses propres lignes;
7. aucune table `employment_job_listings` n’existe;
8. les advisors Supabase ne révèlent aucun nouveau problème sécurité/performance directement causé par Emploi;
9. le manifeste GitHub n’est déplacé de `PLANNED_LOCAL_TABLES` vers `EXPECTED_TABLES` qu’après preuve réelle de production.

## Smoke tests

Utiliser un compte de test non sensible :

- créer/modifier/supprimer un profil professionnel factice;
- ajouter/modifier/supprimer une candidature fictive clairement identifiée comme test;
- vérifier qu’un autre compte ne peut pas lire ces données;
- vérifier qu’une URL non HTTP/HTTPS est refusée;
- vérifier que rien n’est écrit dans les stockages navigateur persistants.

Ne pas utiliser de vraie candidature, CV, employeur réel ou note personnelle pendant les smoke tests.

## Rollback / incident

Tant qu’aucune donnée utilisateur réelle n’existe, une correction de schéma peut être préparée de façon classique. Dès qu’une donnée Emploi réelle existe :

- ne pas supprimer automatiquement les tables;
- désactiver l’accès applicatif si nécessaire;
- préserver les données privées;
- corriger par une nouvelle migration;
- revalider RLS et séparation inter-module avant réouverture.

Emploi ne doit jamais être utilisé comme source automatique pour le Registre personnel, Rencontres, Histoire de vie, Mode Voyage, sécurité ou Mon IA.
