# SINJIRA V25 — Preuve de déploiement production Emploi

Date de vérification : **2026-09-05**  
Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`)  
Lot Git historique gelé : `2077ca7ff3a0ec77a27a908a9379e92149a4e0a5`

## Portée

Cette preuve concerne uniquement la **fondation Emploi V25** : profil professionnel volontaire et suivi personnel de candidatures.

Elle ne revendique aucun déploiement Mon IA, aucun catalogue d’offres, aucune Edge Function et aucun couplage avec le Registre personnel, Rencontres, Histoire de vie, Mode Voyage ou la sécurité.

## Préflight observé

Avant écriture :

- dernière migration production : `20260905131659_sinjira_v25_conscience_vault_audit_session_index`;
- `public.employment_profiles` absente;
- `public.employment_applications` absente;
- migration distante `sinjira_v25_employment_foundation` absente.

Le SHA gelé `2077ca7f...` a été vérifié comme contenant la migration Emploi et comme précédant les deux migrations Mon IA connues.

## Validation GitHub avant rollout

La PR #176, `V25 Emploi: préparer le déploiement production ciblé`, a passé tous ses workflows observés sans échec.

Le workflow Emploi a validé :

- contrat Web/SQL;
- garde du lot production ciblé;
- classification du schéma;
- démarrage Supabase local;
- **31 assertions pgTAP**;
- nettoyage local.

Les navigateurs Chromium, Firefox et WebKit ainsi que Lighthouse mobile ont également réussi.

La PR #176 a été fusionnée par squash au commit :

`7103a6344ebfa61248b38cf82d59ac9252429142`

## Migration réellement appliquée

La migration locale :

`20260904225000_sinjira_v25_employment_foundation.sql`

a été appliquée seule via la connexion de gestion Supabase après revalidation de la baseline.

Version distante réellement générée :

`20260905133130_sinjira_v25_employment_foundation`

Aucune Edge Function n’a été déployée et aucune migration Mon IA n’a été appliquée avec ce lot.

## Contrôles DB post-déploiement

### `public.employment_profiles`

- table présente;
- RLS activé : `true`;
- RLS forcé : `true`;
- policies : `4`;
- `anon SELECT` : `false`;
- `anon INSERT` : `false`;
- `anon UPDATE` : `false`;
- `anon DELETE` : `false`.

### `public.employment_applications`

- table présente;
- RLS activé : `true`;
- RLS forcé : `true`;
- policies : `4`;
- `anon SELECT` : `false`;
- `anon INSERT` : `false`;
- `anon UPDATE` : `false`;
- `anon DELETE` : `false`.

Les seules clés étrangères de ces deux tables pointent vers `auth.users`.

`public.employment_job_listings` n’existe pas.

## État des données après rollout

- `employment_profiles` : `0` ligne;
- `employment_applications` : `0` ligne.

Aucune donnée utilisateur réelle n’a été créée pendant le déploiement ou ses contrôles structurels.

## Advisors Supabase

Aucun nouvel avertissement de sécurité spécifique à Emploi n’a été observé après DDL.

Les index :

- `employment_applications_user_created_idx`;
- `employment_applications_user_status_idx`

sont signalés `unused_index` au niveau `INFO`, ce qui est normal tant que la table contient zéro candidature.

Référence : https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index

L’avertissement global **Leaked Password Protection Disabled** demeure ouvert dans Supabase Auth hébergé.

Référence : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## État GitHub attendu après réconciliation

Après validation de cette preuve :

- `employment_profiles` et `employment_applications` sont classées dans `EXPECTED_TABLES`;
- les tables Mon IA restent dans `PLANNED_LOCAL_TABLES`;
- le workflow Emploi production devient un vérificateur `workflow_dispatch` strictement lecture seule;
- aucune voie GitHub dédiée ne doit pouvoir rejouer automatiquement le rollout historique.

## Smoke tests authentifiés

Ils restent à faire avec un compte de test et des données explicitement fictives. Aucun résultat A/B entre deux comptes n’est inventé dans cette preuve.

Le backend Emploi V25 est **déployé et structurellement vérifié**; les smoke tests d’expérience utilisateur authentifiée restent une étape distincte.
