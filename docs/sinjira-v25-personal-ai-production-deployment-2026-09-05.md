# SINJIRA V25 — Preuve de déploiement production Mon IA — 2026-09-05

## Portée

Cette preuve documente uniquement la **fondation privée Mon IA V25**. Elle ne documente ni n’autorise un moteur conversationnel, une mémoire IA, un fournisseur de modèle ou une récupération de contenu.

Principe : **L’HUMAIN AVANT TOUT.**

Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`).

## État avant rollout

La baseline production confirmée était :

`20260905133130_sinjira_v25_employment_foundation`

Avant application :

- `private.personal_ai_settings` absent;
- `private.personal_ai_source_permissions` absent;
- `private.personal_ai_audit` absent;
- migrations Mon IA absentes;
- Edge `personal-ai` absente.

## Lot Git gelé

SHA historique utilisé pour les deux migrations de fondation et l’Edge :

`e2e99ec63730559c440ccd90b10a9c18747c5f45`

Ce SHA contient `verify_jwt=true` pour `personal-ai` et ne contient aucun endpoint de chat, mémoire, récupération de source ou génération.

## Migrations réellement appliquées

1. `20260905145448_sinjira_v25_personal_ai_foundation`
2. `20260905145502_sinjira_v25_personal_ai_rls_hardening`
3. `20260905150553_sinjira_v25_personal_ai_audit_user_index`

La troisième migration a été ajoutée après observation de l’advisor performance et validation de la PR #179. Elle crée uniquement :

`private.personal_ai_audit_user_idx` sur `private.personal_ai_audit(user_id)`.

## Vérifications SQL

Après les deux premières migrations :

- les trois tables existaient;
- RLS était activée sur les trois tables;
- aucune policy client n’existait;
- `anon` n’avait aucun SELECT direct;
- `authenticated` n’avait aucun SELECT direct;
- `service_role` n’avait aucun SELECT direct;
- `authenticated` ne pouvait pas appeler directement `service_personal_ai_get_state`;
- `service_role` pouvait appeler la RPC serveur;
- la contrainte `runtime_status = not_configured` était présente;
- les sources étaient bornées à `life_story` et `employment`;
- aucune source `conscience` n’était autorisable.

Comptes immédiatement après rollout :

- `personal_ai_settings` : `0`;
- `personal_ai_source_permissions` : `0`;
- `personal_ai_audit` : `0`.

Après la correction performance, l’index a été confirmé avec la définition :

`CREATE INDEX personal_ai_audit_user_idx ON private.personal_ai_audit USING btree (user_id)`

## Edge Function réellement déployée

`personal-ai` :

- statut `ACTIVE`;
- version `1`;
- `verify_jwt=true`;
- id `431ebe9c-99e5-4e5a-971c-4101f28b90b4`;
- bundle `ezbr_sha256` `d3c700c6056bbaa03aa80a7788a9f61825987044fbecd95b8fb7a91c32dadc9a`.

Ces métadonnées ont été revalidées directement dans l’inventaire Supabase après la fusion de la PR #180. Cette correction documentaire n’a entraîné **aucun redéploiement** de l’Edge Function.

Fichiers déployés depuis le SHA gelé :

- `supabase/functions/personal-ai/index.ts`;
- `supabase/functions/_shared/auth.ts`;
- `supabase/functions/_shared/cors.ts`.

## Contrat de sécurité confirmé

- JWT obligatoire;
- AAL2 obligatoire indépendamment de la préférence `sensitive_step_up`;
- scope risque serveur `ai_private`;
- identité dérivée du JWT;
- `user_id`, `target_user_id`, `subject_user_id` envoyés par le client refusés;
- réponses `private, no-store`;
- corps JSON borné;
- aucune lecture directe du Registre personnel, Histoire de vie ou Emploi dans l’Edge;
- aucun endpoint `chat`, `memory`, `retrieve_source`, `complete` ou `generate`;
- aucun prompt/réponse/source intime dans les logs.

## Runtime confirmé désactivé

Le backend de fondation expose explicitement :

- `conversation_enabled=false`;
- `memory_enabled=false`;
- `source_retrieval_enabled=false`;
- `provider_configured=false`.

La présence de la fondation en production ne signifie donc pas qu’une IA conversationnelle est active.

## CI

PR #178 — readiness production : tous les workflows verts, dont **35/35** pgTAP Mon IA avant la correction d’index.

PR #179 — index audit : tous les workflows verts, dont :

- Mon IA **36/36**;
- moteur de risque V25 **20/20**;
- coffre des consciences **32/32**;
- reconstruction Supabase depuis zéro;
- contrats pgTAP globaux;
- politique Auth locale de 12 caractères;
- navigateurs Chromium, Firefox et WebKit;
- Lighthouse;
- garde secrets;
- validation du ledger production.

PR #179 a été fusionnée sur `main` au commit :

`c75be5b7a72d7ade12d440c456702188a20d5540`

PR #180 — réconciliation production : Mon IA, Emploi, Coffre, site, navigateurs, ledger et gardes déclenchés sont tous passés au vert après correction des deux assertions de classification. Elle a été fusionnée sur `main` au commit :

`0e5e9b9e95ec65c25cdd3b1ccb64f0a97195e0d6`

## Revalidation production après PR #180

Les trois dernières migrations production restent, dans cet ordre :

1. `20260905145448_sinjira_v25_personal_ai_foundation`;
2. `20260905145502_sinjira_v25_personal_ai_rls_hardening`;
3. `20260905150553_sinjira_v25_personal_ai_audit_user_index`.

Les trois tables privées Mon IA sont toujours vides. Elles conservent :

- RLS activée;
- `0` policy client;
- aucun SELECT direct pour `anon`, `authenticated` ou `service_role`;
- aucun INSERT direct pour `anon`, `authenticated` ou `service_role`;
- l’index `personal_ai_audit_user_idx` présent.

## Advisors après correction

Le finding performance `unindexed_foreign_keys` visant `personal_ai_audit_user_id_fkey` a disparu après `20260905150553`.

`personal_ai_audit_user_idx` apparaît désormais seulement comme `unused_index` INFO, ce qui est attendu tant que la table est vide. Il ne doit pas être supprimé pour cette raison.

Les INFO `RLS Enabled No Policy` sont cohérentes avec les tables privées server-only sans accès direct.

Le WARN global **Leaked Password Protection Disabled** reste ouvert dans Supabase Auth. Il n’a pas été modifié par ce rollout.

Référence : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Limites restantes

Les smoke tests authentifiés AAL1/AAL2 n’ont pas été exécutés faute de compte/session de test disponible. Aucun contenu réel ou intime n’a été créé pour compenser cette absence.

Toute activation future d’un moteur IA, d’une mémoire, d’un fournisseur ou d’une récupération de sources exige un lot séparé et un consentement explicite.
