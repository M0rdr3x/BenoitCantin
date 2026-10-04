# Continuité ChatGPT — BenoitCantin / SINJIRA

Date de préparation : 2026-10-04  
Branche de transfert : `handoff/chat-continuity-2026-10-04-v1`  
Dépôt : `M0rdr3x/BenoitCantin`

## But du paquet

Ce fichier accompagne une copie complète du dépôt afin de reprendre le travail dans un autre chat sans perdre le contexte. Le prochain chat doit lire ce fichier en premier, puis vérifier l'état GitHub actuel avant toute mutation.

## Règles de gouvernance impératives

- Ne pas fusionner les PR #435 ou #436 sans instruction humaine explicite.
- Ne pas appliquer de migration Supabase en production.
- Ne pas modifier `supabase/production-reviewed-migration-batch.txt` ni `supabase/production-migration-ledger.txt` sans revue/approbation humaine explicite.
- Ne pas modifier DNS, hébergement de production ou forfait payant sans instruction humaine explicite.
- Une revue technique peut conclure « aucun bloqueur technique trouvé / prêt pour décision humaine », mais ne doit jamais marquer une migration approuvée.
- Ne pas inventer identifiants, approbations, permissions externes ou masters PDF.
- Mode de travail attendu : finir → prouver → fermer → suivant, avec critères explicites de « 100 % terminé ».
- Prudence avec les mutations d'état de PR. Une tentative antérieure sur #454 a fusionné la PR par erreur. Toute fermeture doit être vérifiée immédiatement avec `merged:false`.

## Point de convergence principal

Issue #455 : **Pilotage 100 % — convergence finale du projet, une composante à la fois**.

Définition de 100 % : code/configuration + tests + CI + preuve d'exécution réelle + décisions humaines/fournisseur nécessaires fermées. Cela n'autorise pas implicitement merge, déploiement, dépense, DNS, Supabase production ou approbation humaine.

Phases :
1. Hygiène Git / source de vérité.
2. Sécurité et publication web.
3. Backend / Supabase.
4. Canon.
5. Livre / PDF.
6. Fermeture globale.

## État de main

Main connu au moment de la préparation : `60cb8b60897fde126066bf359eccfe8747417760`.

Historique particulier :
- ancien main : `8c94b37e92e607088a4626ed0c1cc40ce1141a91`
- merge accidentel #454 : `498d5519ebe82465dc3630bb7c32f7e4f3d0cc29`
- revert immédiat : `60cb8b60897fde126066bf359eccfe8747417760`
- ancien main → main actuel : 2 commits, mais 0 différence nette de fichiers.

## PR #435 — backend / répétition d'intégration

Branche : `a1/integration-rehearsal`, draft.  
Head synchronisé : `193b686f34ba89fe7ec91022faf1651f14bf3e18`.  
Comparaison connue avec main : 1698 ahead / 0 behind.  
La synchronisation a réutilisé exactement l'arbre de l'ancien head, donc aucune modification de contenu.

Dernier état CI observé pendant la session :
- le connecteur n'affichait que les 100 premiers runs déclenchés par la PR ;
- 81 success / 12 skipped / 6 in_progress / 1 failure ;
- échec attendu : `SINJIRA - garde historique migrations production V25`, run `37188972483`, car 43 migrations futures ne sont pas dans le batch revu ;
- plusieurs workflows V25 étaient encore en cours. Re-vérifier avant d'annoncer la CI terminée.

**Ne pas fusionner #435.**

## Correctif âge / #453

Correctif appliqué dans `20260916210000_sinjira_v25_child_guardian_signup.sql` avec âge entier complété via `extract(year from age(...))::integer`.

Repères :
- commit correctif : `28c28409bcd610ad873c31e96cac9af46d240a7a`
- nouveau blob migration : `3231fc2720a28700be9d1be117e53a9a2448b08b`
- validator signup : commit `b065aa...`
- validator global safety : commit `fa8686...`
- workflow `SINJIRA V25 — Inscription enfant 11 ans`, run `37181885399`, SUCCESS
- pgTAP 75/75 + rebuild Supabase local + test profil privé enfant + Auth HTTP réel exactement 11 ans
- #453 fermé
- snapshot release rebaseliné, commit `5c39b513...`, explicitement NON REVUE / NON APPROUVÉE.

## #438 — revue humaine de 43 migrations futures

Ouvert. Revue technique A→F terminée.

- 42/43 blobs futurs sont byte-identical aux paquets de revue historiques.
- seul blob changé : migration signup enfant de #453, blob `3231fc...`, revalidé techniquement.
- preuves connues : child 75/75 ; private child profile 13/13 ; Junior Community 61/61 ; sensitive boundary 13/13 ; content rating 26/26 ; account capabilities 25/25 ; minor content policy 8/8 ; multi-guardian 26/26 ; account/catalog 56/56 ; private profile historical 22/22 ; snapshot 43 migrations.
- docs : commits `a0caa5...`, `e82077...`, `1215cdf...`.

Décisions humaines encore requises : Mode Voyage, seuils âge/supervision, AAL2, retrait immédiat, majorité à 18 ans, métadonnées parentales, sémantique owner/service_role/player/tester, accès famille, droits commerciaux, comportement correctif Junior.

Le batch revu et le ledger sont inchangés.

## Supabase production

Projet : `gpvivleexywljowcqkru`  
Organisation : `glaxqwyumblfqmzusqbt`  
État connu : ACTIVE_HEALTHY, forfait Free.

Security Advisor :
- `auth_leaked_password_protection` WARN / désactivé ;
- la protection mots de passe compromis exige un forfait éligible ; aucune mise à niveau ou PATCH n'a été faite.

Historique migrations production :
- s'arrête à `20260906035442_sinjira_v25_device_challenge_continuity_hardening`
- ledger production s'arrête au même point
- 14 migrations revues mais non appliquées ensuite
- #438 couvre 43 migrations supplémentaires non revues
- séquence future totale = 57 = 14 revues/non appliquées + 43 non revues
- aucun preflight distant ni apply production.

RLS Advisor : 49 tables RLS sans policy, mais la classification SQL a montré aucune permission SELECT/INSERT/UPDATE/DELETE pour anon/authenticated ; surfaces deny-all explicites, pas une exposition navigateur. Aucun changement SQL requis sur cette seule base.

## #135 — protection de main

Dernière revalidation :
- `main` : `protected:false`
- aucun required status check actif
- endpoint détaillé protection : 403 `Resource not accessible by integration`
- preuve commentée dans #135

Bloqueur administrateur réel. Le connecteur ne peut pas activer la protection/ruleset.

## #240 — secrets Supabase production

Workflow `.github/workflows/supabase-production-preflight.yml` :
- frontière distante uniquement `workflow_dispatch`
- apply seulement si `inputs.apply == true`
- confirmation exacte `APPLY-SUPABASE-PRODUCTION`
- branche exacte `refs/heads/main`
- absence de `SUPABASE_ACCESS_TOKEN` / `SUPABASE_DB_PASSWORD` = fail closed.

Les API secrets ne sont pas exposées ; ne pas affirmer leur présence. Aucun run distant/apply.

## #437 — HIBP

Projet Supabase Free ; warning advisor encore présent.  
Workflow `.github/workflows/sinjira-v25-auth-password-hardening.yml` gated :
- workflow_dispatch seulement
- main
- environment production
- confirmation exacte `ENABLE-SINJIRA-V25-LEAKED-PASSWORD-PROTECTION`
- vérifie forfait éligible avant PATCH
- seul changement prévu : `password_hibp_enabled=true`.

Bloqué par le forfait Free. Pas de dépense/upgrade/PATCH. #136 fermé comme doublon.

## #439 — reviewers d'environnement GitHub

API environment/pages non exposée par l'intégration. Impossible de vérifier/muter les reviewers dans Settings → Environments. Bloqueur admin externe.

## Web — PR canonique #449

PR #449, branche `a1/web-release-transparency`, draft.  
Head synchronisé : `2ddad2fd11cb689b5236154f9b7a6e39a058f9fa`.  
Comparaison connue : 135 ahead / 0 behind main.  
La synchro a réutilisé exactement l'arbre précédent : aucun changement de fichier.

Dernière CI connue : **29 success / 9 skipped / 0 failure / 0 active**.

#446 et #448 ont été fermées sans merge comme superseded par #449.

#445 est maintenant : **Release web — publier le candidat web-only #449 de façon explicite et vérifiée**.  
Le prochain gate web est #450, hébergement/cutover, pas le code #449.

#449 contient notamment :
- `vercel.json`
- `.github/workflows/validate-vercel-preview.yml`
- durcissement du builder
- correction de faux positif `scripts/validate_site.py`
- allowlist exacte `vercel.json` + workflow dans `scripts/validate_web_release_scope.py`.

## Artefact web isolé

Preuve historique sur l'ancien head de contenu identique :
- workflow `Web release — artefact public isolé`, run `37186821003`
- artefact `sinjira-web-release-a1133035360e8e01cee82072c10cf39b0a46f223`
- artifact id `11296854857`
- taille archive 43 253 807 octets
- digest `e2bae94272d0b92aa1796a8579bfaef6cfcd2ad6b1ff12e728a7892b1b32732d`
- 487 entrées
- 0 entrée sous supabase/scripts/docs/.github/tests/mobile-native
- 404 forcées pour ces six zones
- CSP/HSTS/nosniff/permissions/private no-store présents.

Le head #449 actuel a le même arbre, mais ne pas supposer qu'un nouvel artefact aurait le même ID/digest/source_sha sans vérification.

## Site live / #450

Dernière observation connue :
- `https://www.benoitcantin.com/` servait encore l'ancien site avec navigation « Registre » et « Contact »
- `https://www.benoitcantin.com/supabase/config.toml` était publiquement lisible

Cela prouvait que l'ancien hébergement n'était pas encore cut over. Revalider avant toute affirmation actuelle.

Vercel :
- team id `team_PXR1PkxpEzOEfkZplC0CSFJD`
- tentative de création projet `benoitcantin-web-preview` avec deploy=false → 403 permission
- 0 projet lié observé
- aucun projet/déploiement/domaine/DNS créé.

Ne pas faire de cutover DNS/hébergement sans instruction humaine explicite.

## #454 — incident Vercel

PR `a1/vercel-preview-safe-bootstrap` accidentellement fusionnée lors d'une tentative de changement d'état :
- merge `498d5519...`
- ajoutait seulement `vercel.json`
- revert immédiat `60cb8b...`
- différence nette de fichiers avec l'ancien main : zéro.

Ne pas utiliser des mutations d'état de PR sans vérification immédiate.

## #444 — BubblaV

État fournisseur connu :
- site `www.benoitcantin.com`
- ready
- allow_all_domains=false
- allowed_domains=[`www.benoitcantin.com`]
- yolo_mode=false
- auto_apply_learning=false
- plan free.

Dans #449 `assets/js/ai-transparency.js` :
- publicAssistantFormsMinimized=true
- publicAssistantDomainsRestricted=true
- publicAssistantNetworkValidated=false
- widget ne charge que si les trois sont vrais
- widget URL `https://www.bubblav.com/widget.js`
- site id public `ca77cd98-bd32-459c-ad55-fdad4fb85316`.

Preuve contrôlée encore requise :
1. fonctionne sur www.benoitcantin.com
2. échoue preview/local/tiers.

Ne pas élargir CSP ni mettre networkValidated=true avant preuve.

## #451 — Formspree

Aucun connecteur Formspree authentifié. Impossible de créer proprement un endpoint personnel. Ne pas inventer d'endpoint.

## #363 — masters PDF

Fichiers trouvés :
- `La_Cendre_du_Jugement_DEMO.pdf` — 1 140 091 octets — vieille démo promo, incorrecte
- `SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf` — 20 206 667 — full récent, pas le master historique
- `SINJIRA_Livre_01_La_Cendre_du_Jugement_MAITRE_OFFICIEL.pdf` — 9 890 250 — ne correspond pas au master historique attendu

Masters attendus :
- démo : 6 530 033 octets, SHA-256 `aad491ce...`
- full : 10 371 834 octets, SHA-256 `9862a110...`

Aucun match exact. Ne pas remplacer la démo publique par une mauvaise version ni exposer le livre complet. Bloqué jusqu'au master exact ou rebaseline humaine.

## Canon — #436 / #441 / #442

#436 : branche `sinjira-univers-etendu-registre-v25`, head connu avant dernier changement main `7e306f98e64b7d05ecf906cd3e2a5c57481a126a`, draft/open/mergeable au dernier contrôle. Re-vérifier le behind count. **Ne pas fusionner.**

#441 correctifs forward-only :
- `20260926212000_sinjira_v25_canon_source_locator_guard.sql` blob `ae7f3c3f9b274ab815ec950cdaf1f9583d7f7da2`
- `20260926214500_sinjira_v25_extended_canon_rpc_acl_hardening.sql` blob `6a38d112958acd47e1b0a763ed2dee3ab0ee1460`
- workflow run `36288349454` SUCCESS.

#442 : des blobs historiques avaient reçu une approbation explicite, mais les trois blobs finaux de #436 ont ensuite changé. Blobs finaux connus :
- Chroniques `38ef1e8a...`
- Calendar/Atlas `69d1b503...`
- Provenance `62362dee...`

Les commits ultérieurs n'étaient que des mises à jour d'empreinte, pas de nouvelles approbations explicites. Approbation humaine des trois blobs actuels insuffisante. Batch revu inchangé.

## Nettoyage des anciennes PR A1

Phase 1 de #455 commencée en auditant chaque PR sémantiquement contre le head canonique #435, pas seulement par ancestry Git.

Déjà auditées et fermées **sans merge** :
- #401 : protections delete account préservées/renforcées dans #435
- #402 : frontière export Histoire de vie préservée/renforcée
- #403 : frontière remise Histoire de vie préservée/renforcée

Pour chacune : commentaire de convergence ajouté puis fermeture vérifiée avec `merged:false`.

### Prochaine action exacte

Continuer avec **#404**, puis #405, #406, etc., une par une :
1. récupérer metadata + patch de la PR ;
2. inspecter les fichiers actuels au head #435 `193b686f34ba89fe7ec91022faf1651f14bf3e18` ;
3. prouver que chaque protection/changement existe encore ou identifier un comportement unique manquant ;
4. si totalement convergée : commenter la preuve, fermer sans merge, vérifier `merged:false` ;
5. sinon : ne pas fermer ; porter/corriger le changement manquant sur la branche canonique avec tests/CI.

Heads historiques utiles :
- #404 `290c7632831323b1ba6915db0e0fb32f4d5dafb8`
- #405 `e38a5d17d0dcbee34b12eec9da202e575ad4bc09`
- #406 `c7b01bf64c3230de1a41f46ba08378a668510ca2`
- #407 `825f60c97e417cc0f772fd44a0f67c7e02add0e4`
- #408 `8da11f5632f970aca504558721441f7f8d7ef357`
- #409 `d3fd602a8c65db661de9819947936906b8d4e0d2`
- #410 `4aa2956e5c807719e64dd425b09935207a4d089c`
- #411 `7e4ab37d7a89a6deda0ebf93bb10392725bd31e3`
- #412 `ff6946dbb866adfb992ff5f64866652202171a3b`
- #415 `5aa2e33794785ecdda4b3f00afa7ba46a20ecb9a`
- #416 `047d158e19e5551c510eb23a3adcf2c352c9956f`
- #417 `579eda93747f2cdb7efda27b895225b9a8d8b371`

Récupérer l'état frais de #418–#434 avant d'agir.

## Recherche approfondie

Une session Deep Research a été démarrée avec l'objectif d'auditer exhaustivement le projet :
1. indexer/inventorier repos et tickets ;
2. vérifier CI, migrations et blobs critiques ;
3. auditer secrets, workflows et protection de branche ;
4. prioriser la résolution de tous les tickets ouverts ;
5. produire un plan d'action séquencé détaillé.

Session : `6ac20694-7cb8-83ea-b1c4-f357cf937249`.

Dernier état connu dans ce chat : `waiting_for_user_response_on_plan`. Aucun rapport final Deep Research n'a été récupéré dans la session de continuité. Le prochain chat ne doit pas prétendre que le rapport est terminé sans vérifier l'outil/session.

## Ordre logique après le nettoyage A1

Après #404→#434 :
- terminer le gate hébergement #450 et les preuves web (#445/#450/#451/#444/#135) ;
- traiter les décisions backend/Supabase (#438/#439/#240/#437) sans production non autorisée ;
- terminer Canon (#436/#441/#442) avec approbations humaines exactes ;
- résoudre le master PDF #363 ;
- fermer globalement #455 seulement quand toutes les preuves et décisions sont réellement closes.

## Message conseillé au prochain chat

« Lis d'abord `CHATGPT_CONTINUITY_2026-10-04.md`. Vérifie ensuite l'état GitHub actuel avant toute mutation. Continue la convergence #455 à partir de la PR #404, une PR à la fois, en suivant finir → prouver → fermer → suivant. Ne merge pas #435/#436, ne touche pas aux migrations Supabase production, au batch/ledger revu, au DNS/hébergement de production ni à un forfait payant sans mon autorisation explicite. Vérifie aussi si la session Deep Research `6ac20694-7cb8-83ea-b1c4-f357cf937249` peut être reprise ou si son rapport est disponible. »
