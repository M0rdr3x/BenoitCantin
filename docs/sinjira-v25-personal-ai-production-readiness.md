# SINJIRA V25 — Readiness production Mon IA

État préparatoire vérifié le **2026-09-05**.  
Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`).

## Principe

**L’HUMAIN AVANT TOUT.** Mon IA V25 est une fondation privée de réglages et de consentements. Ce lot ne prétend pas fournir un moteur conversationnel.

Il reste strictement séparé :

- du Registre personnel des consciences;
- de Rencontres;
- du Mode Voyage et des signaux de sécurité autres que le contrôle d’accès `ai_private`;
- de la publicité et du profilage caché;
- de toute mémoire psychologique ou inférence silencieuse;
- de tout clone posthume.

Le Registre personnel des consciences n’est jamais une source autorisable.

## État production avant rollout

Contrôle en lecture seule du 2026-09-05 :

- `private.personal_ai_settings` : absent;
- `private.personal_ai_source_permissions` : absent;
- `private.personal_ai_audit` : absent;
- migration `sinjira_v25_personal_ai_foundation` : absente;
- migration `sinjira_v25_personal_ai_rls_hardening` : absente;
- Edge Function `personal-ai` : absente.

La dernière migration production observée est :

`20260905133130_sinjira_v25_employment_foundation`

Cette version constitue la baseline obligatoire du lot Mon IA.

## Lot Git gelé

SHA :

`e2e99ec63730559c440ccd90b10a9c18747c5f45`

Ce SHA contient :

- `20260905000500_sinjira_v25_personal_ai_foundation.sql`;
- `20260905001000_sinjira_v25_personal_ai_rls_hardening.sql`;
- `supabase/functions/personal-ai/index.ts`;
- les helpers partagés d’authentification et CORS;
- `[functions.personal-ai] verify_jwt = true`;
- la navigation Web/mobile Mon IA.

## Périmètre SQL autorisé

Deux migrations seulement, dans cet ordre :

1. `sinjira_v25_personal_ai_foundation`;
2. `sinjira_v25_personal_ai_rls_hardening`.

Elles créent trois tables privées :

- `private.personal_ai_settings`;
- `private.personal_ai_source_permissions`;
- `private.personal_ai_audit`.

### Réglages

`personal_ai_settings` conserve seulement des réglages de fondation : activation volontaire, nom d’affichage, langue et `runtime_status`.

Le runtime est borné par contrainte SQL à :

`not_configured`

### Permissions de sources

Les seules sources préparatoires autorisables sont :

- `life_story`;
- `employment`.

Ces consentements ne donnent pas accès au contenu dans V25. Le runtime retourne explicitement :

- `conversation_enabled = false`;
- `memory_enabled = false`;
- `source_retrieval_enabled = false`;
- `provider_configured = false`.

### Audit

L’audit stocke uniquement des métadonnées minimales : action, utilisateur, type de source éventuel et date.

Il ne stocke aucun prompt, réponse, résumé intime, IP brute, GPS ou identifiant publicitaire.

## Accès et sécurité

Les privilèges directs sont révoqués pour `anon`, `authenticated` et `service_role` sur les trois tables.

RLS est activée comme défense supplémentaire, sans policy client. Les RPC serveur `SECURITY DEFINER` constituent la seule voie prévue.

Le contrôle d’accès exige :

- identité dérivée du JWT;
- rejet des champs client `user_id`, `target_user_id` et `subject_user_id`;
- AAL2 obligatoire;
- moteur de risque V25 avec scope serveur `ai_private`;
- blocage à risque critique;
- continuité des challenges d’appareil fiable;
- refus d’un retry comme approbation implicite;
- anti-fatigue MFA après un refus récent.

## Edge Function autorisée

Une seule Edge Function fait partie du lot :

`personal-ai`

Contraintes :

- `verify_jwt = true` obligatoire;
- méthode POST seulement;
- corps JSON borné à 16 KiB;
- réponses `private, no-store`;
- aucun log du corps, d’un prompt ou du contenu des sources;
- aucune lecture directe de `life_story_entries`, `employment_profiles`, `employment_applications` ou du Registre personnel;
- aucune action `chat`, `memory`, `retrieve_source`, `complete` ou `generate`.

Les seules opérations de fondation sont :

- lire l’état privé;
- modifier les réglages;
- accorder/révoquer un consentement de source préparatoire;
- supprimer les données Mon IA de fondation.

## Tests

`supabase/tests/personal_ai_v25.test.sql` contient **35 assertions pgTAP** couvrant notamment :

- présence des trois tables privées;
- RLS activée;
- absence de lecture directe pour `anon`, `authenticated` et `service_role`;
- RPC serveur présentes;
- privilèges d’exécution réservés au `service_role`;
- sources bornées à Histoire de vie / Emploi;
- exclusion du Registre personnel;
- runtime `not_configured`;
- absence de mémoire conversationnelle documentée;
- `SECURITY DEFINER` avec `search_path` fixé.

Le validateur statique `scripts/validate_personal_ai_v25.py` vérifie aussi l’Edge, l’AAL2, `verify_jwt=true`, l’absence d’accès inter-module et l’absence de runtime IA prématuré.

## Workflow readiness

Workflow :

`.github/workflows/sinjira-v25-personal-ai-production-readiness.yml`

Il est volontairement **sans écriture production**. Il :

- s’exécute uniquement manuellement;
- exige la confirmation `VERIFY-SINJIRA-V25-PERSONAL-AI`;
- checkout le SHA gelé;
- valide les invariants du lot;
- démarre une base Supabase locale;
- exécute les 35 pgTAP;
- rappelle la baseline production attendue.

Le déploiement réel ne doit être effectué qu’après :

1. CI de la PR entièrement verte;
2. fusion sur `main`;
3. nouveau contrôle production confirmant que la baseline est toujours `20260905133130_sinjira_v25_employment_foundation` et que les objets Mon IA sont encore absents;
4. application séquentielle des deux migrations seulement;
5. déploiement de l’unique Edge `personal-ai` avec JWT obligatoire.

## Contrôles post-déploiement obligatoires

Après le rollout, vérifier en lecture seule :

1. les deux migrations distantes Mon IA apparaissent immédiatement après la baseline Emploi et dans l’ordre prévu;
2. les trois tables existent;
3. RLS est activée sur les trois tables;
4. aucun rôle client ne possède de CRUD direct;
5. aucune policy client n’existe;
6. les RPC serveur sont présentes et conservent leur `search_path` fixé;
7. `runtime_status` reste borné à `not_configured`;
8. aucune source `conscience`/Registre personnel n’est autorisable;
9. l’Edge `personal-ai` est `ACTIVE` avec `verify_jwt=true`;
10. aucun endpoint de chat/mémoire/génération n’existe;
11. les trois tables sont vides immédiatement après rollout;
12. les advisors Supabase ne montrent pas de nouveau problème directement causé par Mon IA.

## Smoke tests

Les smoke tests authentifiés restent séparés du rollout structurel. Utiliser uniquement un compte de test et des données factices :

- AAL1 doit être refusé;
- AAL2 valide + risque acceptable permet `get_state`;
- modifier un nom d’affichage factice;
- accorder puis révoquer `employment` ou `life_story` sans récupération de contenu;
- vérifier que le Registre personnel est refusé comme source;
- supprimer les données Mon IA de test;
- vérifier qu’aucune conversation ni mémoire n’est créée.

Ne jamais utiliser de contenu intime réel pour ces tests.

## Incident / rollback

Tant que les tables sont vides, une correction peut être apportée par une nouvelle migration ciblée. Dès qu’une donnée réelle existe :

- ne pas supprimer automatiquement les tables;
- désactiver l’accès applicatif si nécessaire;
- préserver les données privées;
- corriger par une nouvelle migration;
- revalider AAL2, risque, RLS et séparation inter-module avant réouverture.

L’activation future d’un véritable moteur IA devra être un **nouveau lot explicitement conçu, audité et consenti**. La fondation V25 ne l’autorise pas implicitement.
