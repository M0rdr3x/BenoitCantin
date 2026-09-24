# SINJIRA™ V25 — Triage statique des 41 migrations futures

Date du scan : **2026-09-23 (America/Toronto)**  
PR : **#435** — branche `a1/integration-rehearsal`

**Statut : TRIAGE AUTOMATISÉ — AUCUNE APPROBATION PRODUCTION**

> Ce document aide la revue humaine. Il ne remplace pas la lecture SQL, les pgTAP, la reconstruction Supabase, la revue de confidentialité ni la décision humaine.
>
> **L’humain avant tout. Protéger sans surveiller.**

## Résultat global

Le scan a porté sur les **41 migrations futures non revues** figées par le snapshot release.

Constats mécaniques :

- **0** occurrence de `DROP TABLE`;
- **0** occurrence de `DROP COLUMN`;
- **0** occurrence de `TRUNCATE`;
- les migrations contenant des `SECURITY DEFINER` ont été contrôlées : aucune fonction privilégiée réelle détectée sans `search_path` explicite (`SET search_path = ...` ou `SET search_path TO ...`);
- plusieurs migrations contiennent volontairement des `INSERT`, `UPDATE` ou `DELETE`, des triggers, des changements RLS et des grants navigateur : elles demandent donc une lecture humaine attentive même si les suites locales sont vertes;
- les helpers internes exécutables depuis un rôle navigateur restent des zones de revue prioritaire : leur sûreté dépend de la frontière self-only/fail-closed, pas seulement du nom du schéma.

Ce scan ne conclut pas qu'une migration est sûre pour la production.

## Priorité de lecture 1 — surface de sécurité élevée

| Migration | Signaux statiques à relire |
|---|---|
| `20260916210000_sinjira_v25_child_guardian_signup.sql` | ~912 lignes; nombreux `SECURITY DEFINER`; policies créées/remplacées; écritures de données; 5 triggers; flux tuteur/enfant |
| `20260917223000_sinjira_v25_junior_community.sql` | ~671 lignes; RLS sur plusieurs tables; nombreux RPC privilégiés; grants/revokes; 3 triggers; surface sociale Junior |
| `20260922014000_sinjira_v25_creator_family_catalog_access.sql` | ~707 lignes; RLS; policies; `SECURITY DEFINER` + `SECURITY INVOKER`; nombreux grants; `service_role`; catalogue famille complet |
| `20260922033000_sinjira_v25_project_product_access.sql` | ~350 lignes; policies projet/documents; suppressions d’anciennes policies permissives; mutations de données; dépendance `projects.product_slug` |
| `20260919100000_sinjira_v25_private_profile_age_11.sql` | ~311 lignes; coffre privé; écritures profil/sécurité; fonctions privilégiées; règles 11+/tuteur |
| `20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql` | RLS + policy; écritures; fonctions privileged/invoker; grants navigateur; exposition Mode Voyage |
| `20260922031500_sinjira_v25_catalog_age_helper_boundary.sql` | 11 policies recréées et 11 anciennes retirées; frontière âge + commerce + helpers |
| `20260919123000_sinjira_v25_public_rpc_boundary.sql` | déplacement/wrapping de RPC; fonctions privilégiées/invoker; grants dynamiques selon rôles |
| `20260919130000_sinjira_v25_account_catalog_browser_privileges.sql` | convergence des privilèges navigateur; helpers RLS internes; grants/revokes explicites |
| `20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql` | helpers internes accessibles aux rôles navigateur; sécurité dépend du ciblage `auth.uid()` et du fail-closed |

## Priorité de lecture 2 — mutations de données / cycle de vie

Relire particulièrement les effets de bord, l'idempotence et la réexécution de :

- `20260913230000_sinjira_v25_travel_mode_retention_purge.sql` — purge par `DELETE`, fonction privilégiée;
- `20260919013000_sinjira_v25_child_pending_guardian_redeem.sql` — mise à jour du cycle de supervision;
- `20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql` — cascade de révocation via trigger;
- `20260919023000_sinjira_v25_guardian_invite_aal2.sql` — création/invalidation d’invitations;
- `20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql` — suppression de métadonnée via trigger;
- `20260919040000_sinjira_v25_junior_enable_aal2.sql` — consentement/activation;
- `20260919043000_sinjira_v25_guardian_revoke_aal2.sql` — révocation;
- `20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql` — changement privacy-by-default + trigger;
- `20260919090000_sinjira_v25_account_content_hub.sql` — seed/convergence de catalogue;
- `20260919093000_sinjira_v25_private_novel_catalog.sql` — registre privé + RLS;
- `20260919103000_sinjira_v25_livre_i_catalog_seed.sql` — seed Livre I;
- `20260919110000_sinjira_v25_social_public_pseudo_privacy.sql` — convergence pseudo public + trigger;
- `20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql` — réécriture/minimisation de réponses;
- `20260922030000_sinjira_v25_extension_product_access.sql` — `product_slug`, RLS et retrait d’anciennes policies;
- `20260922033000_sinjira_v25_project_product_access.sql` — convergence droits projet/documents.

## Grants navigateur à relire explicitement

La présence d'un grant n'est pas considérée comme une erreur par ce scan. Le reviewer doit confirmer que chaque fonction accordée à `anon` ou `authenticated` est soit un wrapper public minimal, soit un helper interne dont le comportement navigateur est strictement self-only/fail-closed.

Points particulièrement sensibles :

- `sinjira_my_age_band()`;
- `sinjira_child_project_available(uuid)` / `sinjira_child_document_available(uuid)`;
- `project_access_rank(uuid,uuid)`;
- RPC tuteur : émission/relecture/révocation, résumé Junior, métadonnées de contacts;
- RPC Communauté Junior;
- `sinjira_my_*_catalog()`;
- `has_sinjira_product(text,uuid)`;
- RPC Mode Voyage création/annulation.

Pour les helpers internes, vérifier à la fois :

1. privilège `USAGE` du schéma;
2. `EXECUTE` de la fonction;
3. branche `service_role`;
4. ciblage `auth.uid()` pour navigateur;
5. comportement `anon`;
6. absence d'oracle sur UUID arbitraire.

## RLS / policies à relire explicitement

La revue doit vérifier que les anciennes policies permissives ne restent pas combinables avec les nouvelles policies via le comportement `OR` de PostgreSQL.

Priorité :

- projets et documents;
- extensions;
- catalogue privé romans;
- relations tuteur/enfant;
- Communauté Junior;
- Mode Voyage.

Le scan a confirmé que plusieurs migrations retirent explicitement d'anciennes policies avant de créer la frontière canonique. La lecture humaine doit confirmer que les noms historiques couverts sont exhaustifs pour l'état réel de production.

## Ce que le scan ne prouve pas

Le scan statique ne prouve pas :

- l'état réel des policies déjà présentes en production;
- la volumétrie ou le coût d'une migration;
- les verrous et temps de blocage sur données réelles;
- les effets d'une donnée historique inattendue;
- l'absence de régression métier entre plusieurs migrations successives;
- la disponibilité des secrets ou l'autorisation de production;
- que `main` est protégé.

Ces éléments restent des étapes humaines ou de prévol séparées.

## Conclusion de triage

Aucun motif mécanique de type `DROP TABLE`, `DROP COLUMN`, `TRUNCATE` ou `SECURITY DEFINER` sans `search_path` n'a été détecté dans le lot figé de 41 migrations.

Cela réduit le champ de revue, mais **ne transforme aucune migration en migration revue production**.
