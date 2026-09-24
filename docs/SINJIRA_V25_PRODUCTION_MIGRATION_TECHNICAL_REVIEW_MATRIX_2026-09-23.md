# SINJIRA™ V25 — Matrice technique de revue des 41 migrations futures

Date de préparation : **2026-09-23 (America/Toronto)**  
PR : **#435** — branche `a1/integration-rehearsal`

**Statut : AIDE DE REVUE AUTOMATISÉE — NON REVU / NON APPROUVÉ**

> Cette matrice décrit des surfaces techniques observables dans les SQL. Elle ne constitue ni une approbation, ni une recommandation de promotion, ni une autorisation de fusion ou de production.
>
> **L’humain avant tout. Protéger sans surveiller.**

Utiliser cette matrice avec :
- `SINJIRA_V25_PRODUCTION_MIGRATION_REVIEW_WORKSHEET_2026-09-23.md` pour les Git blob SHA-1 et la décision humaine;
- `SINJIRA_V25_PRODUCTION_MIGRATION_STATIC_RISK_SCAN_2026-09-23.md` pour le triage transversal;
- les workflows/pgTAP associés pour les preuves comportementales.

Les compteurs ci-dessous sont **mécaniques** : ils aident à orienter la lecture et ne mesurent pas la sûreté d'une migration.

| # | Migration | Surface mécanique observée | Point de lecture humaine |
|---:|---|---|---|
| 1 | `20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql` | 104 lignes; 1 fonction privée; grants/revokes; branche `service_role` | Vérifier les entrées géographiques et le calcul de risque sans collecte excessive ni élargissement de portée. |
| 2 | `20260913230000_sinjira_v25_travel_mode_retention_purge.sql` | 33 lignes; 1 `SECURITY DEFINER`; 1 `DELETE` | Vérifier le prédicat de rétention, l'idempotence et l'absence de suppression hors données expirées. |
| 3 | `20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql` | 236 lignes; RLS; 1 policy créée/1 retirée; 2 definer + 5 invoker; inserts/updates; AAL2 | Relire la frontière navigateur, les grants, l'ownership des écritures et le fail-closed AAL2. |
| 4 | `20260916210000_sinjira_v25_child_guardian_signup.sql` | 912 lignes; 8 policies créées/16 retirées; 15 definer; 5 triggers; inserts/updates/delete; âge+tuteur+AAL2 | Revue prioritaire : inscription mineur, invitation tuteur, consentement, révocation, minimisation, ordre des triggers et privilèges. |
| 5 | `20260917223000_sinjira_v25_junior_community.sql` | 671 lignes; 3 tables RLS; 20 definer; 3 triggers; nombreux grants/revokes; écritures sociales; âge+AAL2 | Revue prioritaire : communauté Junior, alias, consentement tuteur, modération, visibilité et impossibilité de contourner la supervision. |
| 6 | `20260918010000_sinjira_v25_child_sensitive_boundary.sql` | 186 lignes; 6 policies créées/12 retirées; 2 definer; 2 triggers; updates | Vérifier que toutes les écritures sensibles enfant restent fail-closed et que les anciennes policies ne se combinent plus par OR. |
| 7 | `20260918013000_sinjira_v25_child_content_rating.sql` | 122 lignes; projets/documents; 2 policies créées/10 retirées; 2 definer | Vérifier classement 11–12, masquage des contenus non approuvés et absence d'oracle UUID navigateur. |
| 8 | `20260918020000_sinjira_v25_account_capabilities.sql` | 58 lignes; 1 definer; grants/revokes; âge et `service_role` | Vérifier que les capacités retournées sont minimales, self-only et fail-closed si l'âge/supervision est incertain. |
| 9 | `20260918023000_sinjira_v25_minor_content_policy_compat.sql` | 87 lignes; 1 definer; compatibilité politique contenu mineur | Vérifier la compatibilité avec les catégories V25 sans réouvrir d'ancienne règle 13+ ou de comportement permissif. |
| 10 | `20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql` | 89 lignes; 2 definer; âge+tuteur | Vérifier qu'une révocation rend immédiatement les capacités dépendantes du tuteur indisponibles. |
| 11 | `20260919013000_sinjira_v25_child_pending_guardian_redeem.sql` | 85 lignes; 1 definer; 1 update | Vérifier transition `child_pending`, unicité/expiration de l'invitation et absence d'élévation avant validation. |
| 12 | `20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql` | 54 lignes; 1 definer; 1 trigger; 2 updates | Vérifier la cascade de révocation, son ordre et son caractère borné aux consentements réellement dépendants. |
| 13 | `20260919023000_sinjira_v25_guardian_invite_aal2.sql` | 61 lignes; 1 definer; insert + delete; AAL2 | Vérifier AAL2 obligatoire, rotation/invalidation des invitations et minimisation des secrets. |
| 14 | `20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql` | 37 lignes; 1 definer; 1 trigger; update | Vérifier que les métadonnées sensibles sont supprimées/minimisées au bon moment sans casser la reprise légitime. |
| 15 | `20260919033000_sinjira_v25_guardian_invite_read_aal2.sql` | 32 lignes; 1 policy créée/2 retirées; AAL2 | Vérifier que la lecture d'invitation reste bornée au bon compte et au bon niveau AAL. |
| 16 | `20260919040000_sinjira_v25_junior_enable_aal2.sql` | 58 lignes; 1 definer; insert + update; AAL2 | Vérifier qu'aucune activation Junior n'est possible sans tuteur valide et AAL2 effectif. |
| 17 | `20260919043000_sinjira_v25_guardian_revoke_aal2.sql` | 54 lignes; 1 definer; update; AAL2 | Vérifier autorité du révocateur, idempotence et retrait immédiat des capacités dérivées. |
| 18 | `20260919050000_sinjira_v25_guardian_majority_visibility.sql` | 45 lignes; 1 policy créée/2 retirées; 1 definer; âge | Vérifier la transition de majorité et la fermeture des données de supervision devenues inutiles. |
| 19 | `20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql` | 30 lignes; 1 policy créée/1 retirée; AAL2 | Vérifier qu'une invitation de supervision ne reste pas visible/utilisable après majorité. |
| 20 | `20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql` | 107 lignes; 1 definer; AAL2 | Vérifier consentement explicite, minimisation des contacts et non-divulgation de l'identité réelle. |
| 21 | `20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql` | 102 lignes; `guardian_links`; 2 definer; 1 trigger; 3 updates | Vérifier privacy-by-default, opt-in explicite et absence de métadonnées activées implicitement. |
| 22 | `20260919070000_sinjira_v25_guardian_contacts_minimization.sql` | 107 lignes; 1 definer; AAL2 | Vérifier que le RPC ne retourne que les champs nécessaires et ne crée pas d'oracle entre comptes. |
| 23 | `20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql` | 72 lignes; 1 definer; âge+AAL2 | Vérifier que le résumé tuteur reste minimal et uniquement accessible au tuteur autorisé. |
| 24 | `20260919080000_sinjira_v25_guardian_character_identity_isolation.sql` | 106 lignes; 1 definer; AAL2 | Vérifier l'isolation identité réelle/personnage et l'absence de fuite via les contacts tuteur. |
| 25 | `20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql` | 53 lignes; 1 definer; âge | Vérifier que les alias Junior ne révèlent ni identité réelle ni identifiant sensible. |
| 26 | `20260919090000_sinjira_v25_account_content_hub.sql` | 79 lignes; 4 policies créées/4 retirées; insert + update | Vérifier seed/convergence du hub Compte, ownership des lignes et absence d'accès supplémentaire implicite. |
| 27 | `20260919093000_sinjira_v25_private_novel_catalog.sql` | 185 lignes; table privée + RLS; 2 definer; seed actif privé non mutant sur conflit; `service_role` | Vérifier séparation métadonnées/catalogue/asset privé, reprise partielle non destructive et délivrance seulement avec droit canonique. |
| 28 | `20260919100000_sinjira_v25_private_profile_age_11.sql` | 322 lignes; 2 definer; 2 inserts + 2 updates; âge; frontière anti-auto-vieillissement mineur | Vérifier coffre profil privé, âge minimum, champs permis, isolation totale entre comptes et refus d’une date plus ancienne qui augmenterait l’âge d’un mineur sans revue séparée. |
| 29 | `20260919103000_sinjira_v25_livre_i_catalog_seed.sql` | 53 lignes; 2 inserts; métadonnées roman convergées; actif privé non mutant sur conflit | Vérifier idempotence du seed, slugs stables et préservation d’une configuration privée déjà existante. |
| 30 | `20260919110000_sinjira_v25_social_public_pseudo_privacy.sql` | 66 lignes; 1 definer; 1 trigger; insert + updates | Vérifier que seul le pseudo public voulu est synchronisé et qu'aucune identité privée ne fuit. |
| 31 | `20260919113000_sinjira_v25_private_novel_asset_rls.sql` | 18 lignes; RLS table privée; grants/revokes; `service_role` | Vérifier que le navigateur n'obtient jamais un accès direct aux assets privés. |
| 32 | `20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql` | 20 lignes; RLS projets; 1 policy créée/1 retirée | Vérifier que le créateur voit son catalogue sans transformer ce rôle en droit commercial pour les autres comptes. |
| 33 | `20260919123000_sinjira_v25_public_rpc_boundary.sql` | 221 lignes; 4 definer + 3 invoker; grants/revokes; âge/`service_role` | Revue prioritaire des wrappers publics : paramètres, rôles autorisés, `search_path`, minimisation et self-only. |
| 34 | `20260919130000_sinjira_v25_account_catalog_browser_privileges.sql` | 145 lignes; 3 definer + 1 invoker; 10 grants + 10 revokes | Revue prioritaire des privilèges navigateur et des helpers internes accessibles aux rôles applicatifs. |
| 35 | `20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql` | 154 lignes; 2 definer; inserts + update; AAL2/`service_role` | Vérifier minimisation des réponses Mode Voyage et absence de détails internes dans les sorties navigateur. |
| 36 | `20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql` | 128 lignes; 3 definer; grants/revokes; `auth.uid()` | Revue prioritaire : chaque helper navigateur doit être self-only/fail-closed et inutilisable comme oracle UUID. |
| 37 | `20260922014000_sinjira_v25_creator_family_catalog_access.sql` | 707 lignes; table famille privée; RLS; 4 policies; 8 definer + 8 invoker; 17 grants/revokes; insert/update/delete; âge | Revue prioritaire : catalogue complet créateur/famille, provisionnement `service_role`, aucun courriel stocké, aucune création de faux entitlement, Junior minimisé. |
| 38 | `20260922023000_sinjira_v25_paid_order_product_access.sql` | 171 lignes; 1 policy; 1 definer + 3 invoker; âge/droits produit | Vérifier que seul `paid`/entitlement réel donne un droit, que pending ne donne rien et que le navigateur reste self-only. |
| 39 | `20260922030000_sinjira_v25_extension_product_access.sql` | 181 lignes; RLS extensions; 3 policies créées/7 retirées; 1 definer; update | Vérifier suppression exhaustive des anciennes policies permissives, parent non brouillon et extension approuvée avant accès produit. |
| 40 | `20260922031500_sinjira_v25_catalog_age_helper_boundary.sql` | 232 lignes; 11 policies créées/11 retirées; 1 definer + 2 invoker; âge/`service_role` | Revue prioritaire : frontière âge/commerce, helper produit self-only et non-réouverture des comptes 11–12. |
| 41 | `20260922033000_sinjira_v25_project_product_access.sql` | 350 lignes; projets; 3 policies créées/8 retirées; 2 definer; 2 updates | Revue prioritaire : projet payant, documents enfants du projet, parent brouillon, droits explicites distincts et suppression des anciennes policies SELECT permissives. |

## Ordre conseillé de lecture technique

Sans constituer un classement de sûreté, un ordre efficace pour la **lecture humaine** est :

1. commencer par les frontières qui ont la plus grande surface de privilèges/RLS : 4, 5, 33, 34, 37, 39, 40, 41;
2. relire ensuite les transitions de supervision et AAL2 : 10 à 25;
3. relire les écritures/retentions/seeds : 2, 3, 26 à 30, 35;
4. terminer par les migrations plus courtes dont l'effet dépend surtout des migrations précédentes.

## Questions transversales à poser pendant la revue

Pour chaque migration concernée :

- une ancienne policy permissive peut-elle encore être active et s'additionner par `OR` ?
- un `SECURITY DEFINER` fixe-t-il explicitement son `search_path` et valide-t-il l'appelant ?
- un rôle `authenticated` peut-il passer un UUID arbitraire au lieu d'être borné à `auth.uid()` ?
- le rôle `service_role` est-il utilisé uniquement pour une opération serveur réellement nécessaire ?
- une transition d'âge ou de supervision échoue-t-elle fermée si l'état est incomplet ou révoqué ?
- les opérations `INSERT`/`UPDATE`/`DELETE` sont-elles idempotentes ou explicitement non réexécutables ?
- un achat `pending` pourrait-il être confondu avec un droit `paid` ?
- un projet/roman/extension brouillon pourrait-il redevenir visible par une ancienne policy ?
- les champs retournés au navigateur sont-ils minimisés ?
- la reconstruction depuis zéro et les pgTAP associés couvrent-ils bien la branche modifiée ?

## Frontière de décision

Cette matrice peut réduire le coût de lecture, mais **elle ne doit jamais remplir automatiquement la colonne « Décision humaine »** de la feuille de revue.

Tant qu'une décision humaine explicite n'existe pas :
- les 41 migrations restent non revues;
- le reviewed batch reste inchangé;
- le ledger reste inchangé;
- aucun prévol distant ni déploiement production n'est autorisé;
- la PR reste draft.
