# SINJIRA V25 — Preuve de déploiement production du Registre personnel

Date de vérification : **2026-09-05**  
Projet Supabase : `gpvivleexywljowcqkru` (`ca-central-1`)  
Lot Git gelé : `fc8d9fe26c8f095a0e95dc6cadcbf43d7c61c9dd`

## Portée

Cette preuve concerne uniquement le **Registre personnel des consciences** et son moteur de risque V25. Elle ne revendique pas le déploiement des fondations Emploi ni Mon IA.

Le principe reste **L’HUMAIN AVANT TOUT** : le contenu intime du Registre personnel est séparé du Registre narratif, de Histoire de vie, de l’héritage posthume, des analytics, de la publicité et des recommandations.

## Préflight observé avant écriture

- projet Supabase : `ACTIVE_HEALTHY`;
- dernière migration distante avant V25 : `20260901002241_sinjira_v24_5_54_fracture_contribution_atomic_finalize`;
- aucune migration V25 déjà présente;
- appareils enregistrés : `1`;
- appareils fiables : `0`;
- appareils principaux : `0`.

La remise à zéro V25 de confiance appareil n’a donc retiré aucun statut fiable/principal existant au moment du rollout.

## Migrations réellement appliquées

Les migrations ont été appliquées transactionnellement via l’interface de gestion Supabase connectée, après validation du SHA gelé et de l’historique distant. Le workflow GitHub manuel reste la voie reproductible gardée, mais **aucun run GitHub fictif n’est revendiqué ici**.

Ordre distant réellement créé :

1. `20260905040230_sinjira_v25_0_security_risk_model_convergence`
2. `20260905040303_sinjira_v25_0_personal_consciousness_vault`
3. `20260905040330_sinjira_v25_0_conscience_vault_challenge_continuity`
4. `20260905040400_sinjira_v25_0_device_key_privacy_and_trust_hardening`

Aucune migration Emploi ou Mon IA n’a été incluse dans ce lot.

## Vérification structurelle DB

Les six contrôles post-déploiement ont retourné `true` :

- `private.conscience_entries` existe;
- `private.conscience_vault_sessions` existe;
- `private.conscience_vault_audit` existe;
- `public.service_conscience_evaluate_access(...)` existe;
- `public.security_connection_events.risk_model_version` existe;
- `private.security_risk_score_v25(...)` existe.

## Contrat de privilèges vérifié

Pour les trois tables privées du coffre :

- RLS activé;
- aucun CRUD direct pour `anon`;
- aucun CRUD direct pour `authenticated`;
- aucun CRUD direct pour `service_role`;
- accès applicatif uniquement via les RPC `SECURITY DEFINER` étroites prévues.

Les fonctions sensibles vérifiées possèdent un `search_path` explicite.

Le durcissement appareil est actif :

- `authenticated` n’a plus de `SELECT` direct sur `public.security_devices`;
- `authenticated` peut appeler `public.security_list_devices(text)`, qui renvoie une vue assainie;
- `anon` ne peut pas appeler cette liste assainie.

## État initial du coffre après rollout

Au contrôle immédiatement après déploiement :

- `private.conscience_entries` : `0` ligne;
- `private.conscience_vault_sessions` : `0` ligne;
- `private.conscience_vault_audit` : `0` ligne.

Le schéma d’audit contient uniquement :

- `id`;
- `user_id`;
- `session_id`;
- `entry_id`;
- `event_type`;
- `occurred_at`.

Il ne contient aucun champ de contenu intime, IP ou GPS.

## Edge Function production

`conscience-vault` a été déployée depuis le SHA gelé avec ses dépendances `_shared/auth.ts` et `_shared/cors.ts`.

État observé :

- statut : `ACTIVE`;
- version : `1`;
- `verify_jwt=true`;
- SHA bundle : `d2a61d32bf09e9278506e0682cf2bba87c0b5941b8acc607e64cd8a772998dfd`.

Le contrat de code validé en CI et dans le bundle impose notamment :

- AAL2 à chaque appel du coffre;
- identité dérivée du JWT vérifié;
- rejet de `user_id`, `target_user_id` et `subject_user_id` fournis par le client;
- réponses sensibles `Cache-Control: private, no-store`;
- aucune IP brute ni donnée GPS stockée;
- aucune journalisation du corps de requête ou du contenu intime;
- scope de risque fixé serveur à `conscience_vault`.

## Validation CI avant production

La PR de correction de la voie de déploiement (#172) a passé :

- le validateur statique du contrat de déploiement;
- le démarrage Supabase local et l’application des migrations;
- **31 assertions pgTAP** du coffre V25;
- les autres workflows déclenchés, sans échec observé.

## Advisor sécurité après déploiement

Le conseiller Supabase classe les trois tables `private.conscience_*` en `RLS Enabled No Policy` au niveau `INFO`. Dans ce design, cette situation est volontaire : aucun rôle applicatif ne dispose de CRUD direct et les accès passent par les RPC serveur étroites. Les privilèges ont été vérifiés explicitement après le rollout.

Un avertissement distinct reste ouvert : **Leaked Password Protection Disabled** dans Supabase Auth. Il s’agit d’un réglage Auth hébergé et non d’une migration SQL. Cette preuve ne le marque pas comme résolu.

## État de validation

Le backend V25 du Registre personnel est **déployé et structurellement vérifié en production**.

Restent comme validations d’expérience authentifiée : smoke tests Web/mobile avec un compte de test AAL2, sans contenu intime réel, notamment ouverture de capacité courte, expiration/révocation et parcours de challenge appareil lorsque applicable.
