# SINJIRA™ V25 — Feuille de revue humaine des migrations futures

Date de préparation : **2026-09-23 (America/Toronto)**  
PR de travail : **#435** — branche `a1/integration-rehearsal`

**Statut global : NON REVU / NON APPROUVÉ**

> Cette feuille prépare la revue humaine. Elle ne constitue ni une approbation du lot, ni une autorisation de fusion, ni une autorisation de prévol distant, ni une autorisation de production.
>
> **L’humain avant tout. Protéger sans surveiller.**

## Règles de décision

Aucune case cochée ne vaut à elle seule approbation production. L’approbation doit rester une décision humaine explicite et séparée, documentée après lecture du SQL, des dépendances, des preuves CI et des impacts sécurité/confidentialité.

Ne pas modifier automatiquement `supabase/production-reviewed-migration-batch.txt` ou `supabase/production-migration-ledger.txt` à partir de cette feuille.

Avant toute future promotion, le reviewer doit notamment vérifier :

- absence de DDL destructif ou de réécriture de données non comprise;
- RLS activée et anciennes policies permissives neutralisées lorsqu’elles pourraient se combiner avec `OR`;
- privilèges `anon`, `authenticated` et `service_role` strictement bornés;
- tout `SECURITY DEFINER` justifié avec `search_path` maîtrisé;
- wrappers navigateur self-only et absence d’oracle UUID arbitraire;
- transitions `child`, `child_pending`, `youth`, `youth_pending`, `adult` fail-closed;
- consentement, révocation, majorité, minimisation et rétention conformes;
- droits produit fondés sur un droit réel (`paid` / entitlement), jamais sur une commande en attente;
- dépendances entre migrations compatibles avec une reconstruction Supabase depuis zéro;
- seeds et `ADD COLUMN IF NOT EXISTS` idempotents;
- preuves pgTAP/CI correspondantes relues;
- issue #135 résolue et protection serveur de `main` vérifiée avant toute séquence de fusion;
- issue #240 traitée séparément seulement au moment autorisé de la production.

## Appui de triage statique

Le scan mécanique complémentaire est consigné dans `docs/SINJIRA_V25_PRODUCTION_MIGRATION_STATIC_RISK_SCAN_2026-09-23.md`. Il aide à prioriser la lecture, mais ne vaut aucune approbation.

## Checklist globale avant décision

- [ ] HEAD exact de revue gelé et consigné.
- [ ] Snapshot release vert sur ce HEAD exact.
- [ ] Reconstruction Supabase locale complète verte.
- [ ] Suites pgTAP métier/sécurité pertinentes vertes.
- [ ] Tous les rouges restants classés et expliqués.
- [ ] Protection serveur de `main` effectivement active.
- [ ] Reviewer humain identifié; date et décision consignées.
- [ ] Aucun secret de production copié dans Git, une issue ou un log.
- [ ] Prévol distant traité comme une étape distincte.
- [ ] Application production traitée comme une étape distincte.

## Revue migration par migration

Lire les migrations dans l’ordre chronologique canonique. Les colonnes de contrôle sont volontairement vides.

| # | Migration | Git blob SHA-1 | Domaine | SQL / RLS | Vie privée / âge | Ordre / données | Preuves CI | Décision humaine |
|---:|---|---|---|:---:|:---:|:---:|:---:|:---:|
| 1 | `20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql` | `7285d1e30ea288004d17c1dbfbf9f01662b36bb7` | Mode Voyage | [ ] | [ ] | [ ] | [ ] | [ ] |
| 2 | `20260913230000_sinjira_v25_travel_mode_retention_purge.sql` | `41b8dc3d1b1e09c018e588755edb053e63e9904a` | Mode Voyage | [ ] | [ ] | [ ] | [ ] | [ ] |
| 3 | `20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql` | `2d7b8ccbfc79fed6a03208086a138618779d6e2d` | Mode Voyage | [ ] | [ ] | [ ] | [ ] | [ ] |
| 4 | `20260916210000_sinjira_v25_child_guardian_signup.sql` | `baa11566a920ee8ba9f08810f542d9ad78046d24` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 5 | `20260917223000_sinjira_v25_junior_community.sql` | `64e66dc8d9c45de9ecbb1174fdb842e4444b9b6b` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 6 | `20260918010000_sinjira_v25_child_sensitive_boundary.sql` | `ea0426172caba27fc3446c696575a19a1eae08d7` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 7 | `20260918013000_sinjira_v25_child_content_rating.sql` | `b0a2bfda90579830083d128035ee533d06dd2159` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 8 | `20260918020000_sinjira_v25_account_capabilities.sql` | `0a16bfcc49e51ee2b96cb98742442ae3d00e5c76` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 9 | `20260918023000_sinjira_v25_minor_content_policy_compat.sql` | `c0556e3baa218f9529f185010455984a0bc1cd03` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 10 | `20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql` | `efa9d6a29c4decfe0180e9262827022ff752f670` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 11 | `20260919013000_sinjira_v25_child_pending_guardian_redeem.sql` | `faaccf3cce0bf725d0f42a5cbecaecbba4b89aa2` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 12 | `20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql` | `e14c41364246929054282bccb0e4abc5641b8643` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 13 | `20260919023000_sinjira_v25_guardian_invite_aal2.sql` | `5700bfaa2b5a95d84d37ad475524960bdb78fc9b` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 14 | `20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql` | `f08102d4bc2485bc229e21076f361bf31552c928` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 15 | `20260919033000_sinjira_v25_guardian_invite_read_aal2.sql` | `b2439fbad69798db42c17a04887dff50d9f184cc` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 16 | `20260919040000_sinjira_v25_junior_enable_aal2.sql` | `df5475777abd5bb8fff26510a727d3d04cffce53` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 17 | `20260919043000_sinjira_v25_guardian_revoke_aal2.sql` | `7dada317202bdd1add1d4dc5113e3aca682459e4` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 18 | `20260919050000_sinjira_v25_guardian_majority_visibility.sql` | `d7a65f65e1a870620809f1a2e669ef031d6f6d8a` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 19 | `20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql` | `ac18154c958b707d94ddc557b1af6b2af01ba62f` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 20 | `20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql` | `d2ef613bfb372efe620e413d5e059b4d1b1e6c64` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 21 | `20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql` | `2d91c64a90f5c8bca506577ef359078fdf558fad` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 22 | `20260919070000_sinjira_v25_guardian_contacts_minimization.sql` | `e684227b322aa88dbd43376d8bd9aa19a6161f6e` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 23 | `20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql` | `07b1ea063e57d3dd4a31e689fac6f44fd1ca6d18` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 24 | `20260919080000_sinjira_v25_guardian_character_identity_isolation.sql` | `7c169564095bb440bde8a2a106c4e00aa2f307e4` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 25 | `20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql` | `8e0fd367bd0c30ed77f947ae0583408b370121a1` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 26 | `20260919090000_sinjira_v25_account_content_hub.sql` | `29358d27f8f505897b924062e208b8d5c740f8c5` | Compte / catalogue / romans privés | [ ] | [ ] | [ ] | [ ] | [ ] |
| 27 | `20260919093000_sinjira_v25_private_novel_catalog.sql` | `41fec69fe7b720a909558a8a1429a7c39cd4772c` | Compte / catalogue / romans privés | [ ] | [ ] | [ ] | [ ] | [ ] |
| 28 | `20260919100000_sinjira_v25_private_profile_age_11.sql` | `d51142e51ba109492b31c14216367287ef51fbc0` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 29 | `20260919103000_sinjira_v25_livre_i_catalog_seed.sql` | `2a5bb6ae5c25b92c8f963909e95d5949bb82df07` | Compte / catalogue / romans privés | [ ] | [ ] | [ ] | [ ] | [ ] |
| 30 | `20260919110000_sinjira_v25_social_public_pseudo_privacy.sql` | `ac4f11e8e1591c35f0be91f541a21763fdb3ec8d` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 31 | `20260919113000_sinjira_v25_private_novel_asset_rls.sql` | `745ae12098e538415dde16bac198d05610b99954` | Compte / catalogue / romans privés | [ ] | [ ] | [ ] | [ ] | [ ] |
| 32 | `20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql` | `5ed558a9426173fdb714479d28f170ada542803b` | Compte / catalogue / romans privés | [ ] | [ ] | [ ] | [ ] | [ ] |
| 33 | `20260919123000_sinjira_v25_public_rpc_boundary.sql` | `61377e409f769ed94646791acaf8f3c1f86328d0` | Compte / catalogue / romans privés | [ ] | [ ] | [ ] | [ ] | [ ] |
| 34 | `20260919130000_sinjira_v25_account_catalog_browser_privileges.sql` | `4436b3d183fa975f5eedeb0427d66da050dfa961` | Compte / catalogue / romans privés | [ ] | [ ] | [ ] | [ ] | [ ] |
| 35 | `20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql` | `1653597f4c9fe053a1b691fe810a3d1b8ca60955` | Mode Voyage | [ ] | [ ] | [ ] | [ ] | [ ] |
| 36 | `20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql` | `1a6f22628bf7dc944e7d3b77c2744c40e3204b03` | Compte / catalogue / romans privés | [ ] | [ ] | [ ] | [ ] | [ ] |
| 37 | `20260922014000_sinjira_v25_creator_family_catalog_access.sql` | `44f0e779fc667aaf6b39dbcb121b47a0f2e1054a` | Catalogue / droits produit | [ ] | [ ] | [ ] | [ ] | [ ] |
| 38 | `20260922023000_sinjira_v25_paid_order_product_access.sql` | `41643696fdfba9f1075e1388dcf9fab64132a09e` | Catalogue / droits produit | [ ] | [ ] | [ ] | [ ] | [ ] |
| 39 | `20260922030000_sinjira_v25_extension_product_access.sql` | `0bdc1677d4efe669b8ec1503ed41f745136c6680` | Catalogue / droits produit | [ ] | [ ] | [ ] | [ ] | [ ] |
| 40 | `20260922031500_sinjira_v25_catalog_age_helper_boundary.sql` | `b0b2495e24cc0a23c7d50f32f4caef24314cc85a` | Catalogue / droits produit | [ ] | [ ] | [ ] | [ ] | [ ] |
| 41 | `20260922033000_sinjira_v25_project_product_access.sql` | `a07f22b7801a6182e0c15dc05e2cf09df92e7dde` | Catalogue / droits produit | [ ] | [ ] | [ ] | [ ] | [ ] |
| 42 | `20260924173000_sinjira_v25_junior_comment_author_visibility.sql` | `3c80073c9bc027707d1f12a129cebd91a8d7ba4f` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |
| 43 | `20260924191000_sinjira_v25_junior_hidden_post_comment_guard.sql` | `5cdb8c576aae2ff7adcf75dd1270ba446b063e59` | Enfant 11–12 / Junior / confidentialité | [ ] | [ ] | [ ] | [ ] | [ ] |

Mise à jour du **2026-09-24** : les migrations #4 et #6 ont aussi été durcies pour retirer les anciennes policies SELECT projets/documents avant d’installer les gardes `child`, fermant une combinaison permissive par `OR`. Elles restent **NON REVUES / NON APPROUVÉES**.

Mise à jour du **2026-09-24** : la migration #42 corrige forward-only la visibilité des commentaires Junior après révocation de l’accès de leur auteur. Elle reste **NON REVUE / NON APPROUVÉE** et n’autorise aucune promotion.

Mise à jour du **2026-09-24** : la migration #43 ferme la possibilité de commenter une publication Junior pendant un masquage humain `hide_content`. Elle reste **NON REVUE / NON APPROUVÉE**; aucune case de revue n’est cochée automatiquement.

Mise à jour du **2026-09-24** : une relecture automatisée ciblée des migrations #37 à #42 a été consignée dans la matrice technique. Elle confirme la cohérence des gardes famille/achat/âge/projet/Junior avec les preuves CI vertes du HEAD fonctionnel `aac9aa92ef4b6ab14eff53c8fcd230b3a5f17729`. **Aucune case de cette feuille n’est cochée par cette relecture automatisée**; le comportement `project_access` explicite `player/tester` pour adult/youth reste notamment un point de décision humaine distinct d’un achat.

## Signification des colonnes

- **SQL / RLS** : DDL, policies, grants, fonctions, triggers, `SECURITY DEFINER`, `search_path`.
- **Vie privée / âge** : minimisation, consentement, révocation, majorité, bandes d’âge, anti-oracle.
- **Ordre / données** : dépendances antérieures, reconstruction depuis zéro, seed, migration de données, idempotence.
- **Preuves CI** : workflow, pgTAP, navigateur ou autre preuve correspondante effectivement relue.
- **Décision humaine** : à cocher uniquement après les quatre revues précédentes; cette case ne modifie aucun statut production automatiquement.

## Conditions d’arrêt immédiat

Suspendre la promotion si une seule des conditions suivantes apparaît :

- empreinte différente de celle figée dans le snapshot;
- migration nouvelle ou absente du lot de 43;
- élargissement de droits non expliqué;
- policy permissive historique encore active et combinable avec une nouvelle policy;
- accès navigateur à un helper prévu pour `service_role`;
- régression 11–12 / Junior ou réouverture commerciale;
- dépendance de migration qui casse `supabase db reset`;
- changement du reviewed batch ou du ledger sans décision humaine explicite;
- `main` toujours non protégé au moment envisagé de la fusion.

## Sortie de revue

La sortie correcte de cette feuille est soit :

1. **NON APPROUVÉ** avec les points à corriger; ou
2. une **approbation humaine explicite**, séparée de cette feuille, qui précise le HEAD, les 43 blobs relus et la prochaine étape autorisée.

Même après approbation du SQL, la fusion, le prévol distant, la configuration des secrets, l’application Supabase et la réconciliation du ledger restent des décisions séparées.
