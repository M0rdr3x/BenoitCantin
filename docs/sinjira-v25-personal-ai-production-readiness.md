# SINJIRA V25 — Exploitation production Mon IA

État post-déploiement vérifié le **2026-09-05**.  
Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`).

## Principe

**L’HUMAIN AVANT TOUT.** Mon IA V25 est en production comme **fondation privée seulement**. Aucun moteur conversationnel n’est activé.

Les invariants restent obligatoires :

- aucune mémoire conversationnelle;
- aucun fournisseur/modèle configuré;
- aucune récupération de contenu Histoire de vie ou Emploi;
- aucun accès au Registre personnel des consciences;
- aucun profil psychologique caché;
- aucune publicité fondée sur Mon IA;
- aucun clone posthume.

Le Registre personnel des consciences n’est jamais une source autorisable.

## Migrations production

Après la baseline Emploi :

`20260905133130_sinjira_v25_employment_foundation`

Mon IA a été appliqué dans cet ordre :

1. `20260905145448_sinjira_v25_personal_ai_foundation`;
2. `20260905145502_sinjira_v25_personal_ai_rls_hardening`;
3. `20260905150553_sinjira_v25_personal_ai_audit_user_index`.

La troisième migration corrige le finding performance de FK sur `private.personal_ai_audit.user_id` sans indexer de contenu intime.

## État structurel

Tables privées de production :

- `private.personal_ai_settings`;
- `private.personal_ai_source_permissions`;
- `private.personal_ai_audit`.

Contrat vérifié :

- RLS activée sur les trois tables;
- aucune policy client;
- aucun SELECT direct pour `anon`, `authenticated` ou `service_role`;
- RPC serveur `SECURITY DEFINER` avec `search_path` fixé;
- `runtime_status` borné à `not_configured`;
- sources autorisables bornées à `life_story` et `employment`;
- aucune source `conscience`/Registre personnel;
- index `private.personal_ai_audit_user_idx` présent sur `user_id`.

État immédiatement après rollout et correction performance :

- `personal_ai_settings` : 0 ligne;
- `personal_ai_source_permissions` : 0 ligne;
- `personal_ai_audit` : 0 ligne.

## Edge Function

`personal-ai` est déployée en production :

- statut `ACTIVE`;
- version `1`;
- `verify_jwt=true`;
- bundle SHA-256 `d3c700c6d9fb128a986cc61f4c9d70889f2e26358988a09495f13d77efc0bbc5`.

Le contrat de l’Edge reste :

- POST seulement;
- corps JSON borné à 16 KiB;
- réponses `private, no-store`;
- identité dérivée du JWT;
- rejet des identités cibles envoyées par le client;
- AAL2 obligatoire;
- scope risque serveur `ai_private`;
- continuité des challenges d’appareil fiable;
- aucun log du corps, d’un prompt ou du contenu des sources;
- aucune action `chat`, `memory`, `retrieve_source`, `complete` ou `generate`.

## Runtime volontairement désactivé

La fondation retourne explicitement :

- `conversation_enabled = false`;
- `memory_enabled = false`;
- `source_retrieval_enabled = false`;
- `provider_configured = false`.

Un consentement `life_story` ou `employment` est donc seulement préparatoire. Il n’autorise aucune récupération de contenu en V25.

## Tests

`supabase/tests/personal_ai_v25.test.sql` contient maintenant **36 assertions pgTAP**, dont l’index couvrant `personal_ai_audit.user_id`.

La CI vérifie aussi :

- le contrat statique Mon IA;
- l’inventaire Edge;
- la classification du schéma production;
- AAL2 et `ai_private`;
- `verify_jwt=true`;
- l’absence de runtime IA prématuré;
- la reconstruction complète de la base.

## Vérification production manuelle

Workflow :

`.github/workflows/sinjira-v25-personal-ai-production-readiness.yml`

Malgré son nom de fichier historique, il est désormais **strictement lecture seule**. Il exige `VERIFY-SINJIRA-V25-PERSONAL-AI`, vérifie le contrat local, lit l’historique distant et confirme l’ordre exact Emploi → fondation Mon IA → RLS → index, puis exécute les 36 pgTAP localement.

Il ne contient aucune voie de déploiement ou d’écriture production.

## Advisors

Après la migration d’index :

- le finding `unindexed_foreign_keys` sur `personal_ai_audit.user_id` a disparu;
- `personal_ai_audit_user_idx` apparaît seulement comme `unused_index` au niveau INFO parce que les tables sont neuves et vides; cet index doit être conservé;
- les INFO `RLS Enabled No Policy` sur les tables privées Mon IA sont cohérentes avec le modèle serveur-only sans accès direct;
- le WARN global **Leaked Password Protection Disabled** reste ouvert dans Supabase Auth et n’est pas un défaut spécifique à Mon IA.

Référence Supabase pour ce dernier réglage : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Smoke tests restant à faire

Les smoke tests authentifiés nécessitent un compte de test et une session AAL2. Ils ne doivent utiliser aucune donnée intime réelle.

À vérifier :

- AAL1 refusé;
- AAL2 + risque acceptable permet `get_state`;
- réglage factice modifiable;
- permission `employment` ou `life_story` accordable/révocable sans récupération de contenu;
- Registre personnel refusé comme source;
- suppression des données factices;
- aucune conversation ni mémoire créée.

## Incident / évolution future

Dès qu’une donnée réelle existe : ne pas supprimer automatiquement les tables, préserver les données privées et corriger par une nouvelle migration ciblée.

Toute activation future d’un véritable moteur IA doit être un **nouveau lot explicite, audité et consenti**. La présence de cette fondation en production ne constitue jamais un consentement à activer un modèle, une mémoire ou une récupération de sources.
