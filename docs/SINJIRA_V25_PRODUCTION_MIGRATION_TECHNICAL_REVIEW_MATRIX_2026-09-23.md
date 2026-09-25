# SINJIRA™ V25 — Matrice technique de revue des 43 migrations futures

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
| 4 | `20260916210000_sinjira_v25_child_guardian_signup.sql` | 920 lignes; 8 policies créées/24 retirées; 15 definer; 5 triggers; inserts/updates/delete; âge+tuteur+AAL2 | Revue prioritaire : inscription mineur, invitation tuteur, consentement, révocation, minimisation, ordre des triggers, privilèges et retrait des anciennes policies catalogue avant ouverture 11–12. |
| 5 | `20260917223000_sinjira_v25_junior_community.sql` | 671 lignes; 3 tables RLS; 20 definer; 3 triggers; nombreux grants/revokes; écritures sociales; âge+AAL2 | Revue prioritaire : communauté Junior, alias, consentement tuteur, modération, visibilité et impossibilité de contourner la supervision. |
| 6 | `20260918010000_sinjira_v25_child_sensitive_boundary.sql` | 194 lignes; 6 policies créées/20 retirées; 2 definer; 2 triggers; updates | Vérifier que toutes les écritures sensibles enfant restent fail-closed et que les anciennes policies ne se combinent plus par OR. |
| 7 | `20260918013000_sinjira_v25_child_content_rating.sql` | 122 lignes; projets/documents; 2 policies créées/10 retirées; 2 definer | Vérifier classement 11–12, masquage des contenus non approuvés et absence d'oracle UUID navigateur. |
| 8 | `20260918020000_sinjira_v25_account_capabilities.sql` | 58 lignes; 1 definer; grants/revokes; âge et `service_role` | Vérifier que les capacités retournées sont minimales, self-only et fail-closed si l'âge/supervision est incertain. |
| 9 | `20260918023000_sinjira_v25_minor_content_policy_compat.sql` | 87 lignes; 1 definer; compatibilité politique contenu mineur | Vérifier la compatibilité avec les catégories V25 sans réouvrir d'ancienne règle 13+ ou de comportement permissif. |
| 10 | `20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql` | 89 lignes; 2 definer; âge+tuteur | Vérifier qu'une révocation rend immédiatement les capacités dépendantes du tuteur indisponibles. |
| 11 | `20260919013000_sinjira_v25_child_pending_guardian_redeem.sql` | 88 lignes; 1 definer; 1 update | Vérifier transition `child_pending`, unicité/expiration, compatibilité stricte codes 10/16 caractères et absence d'élévation avant validation. |
| 12 | `20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql` | 54 lignes; 1 definer; 1 trigger; 2 updates | Vérifier la cascade de révocation, son ordre et son caractère borné aux consentements réellement dépendants. |
| 13 | `20260919023000_sinjira_v25_guardian_invite_aal2.sql` | 82 lignes; 1 definer; contrainte + insert + delete; AAL2 | Vérifier AAL2 obligatoire, rotation/invalidation, nouveau code 16 hex à 64 bits réels et compatibilité temporaire des codes 10 caractères. |
| 14 | `20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql` | 37 lignes; 1 definer; 1 trigger; update | Vérifier que les métadonnées sensibles sont supprimées/minimisées au bon moment sans casser la reprise légitime. |
| 15 | `20260919033000_sinjira_v25_guardian_invite_read_aal2.sql` | 32 lignes; 1 policy créée/2 retirées; AAL2 | Vérifier que la lecture d'invitation reste bornée au bon compte et au bon niveau AAL. |
| 16 | `20260919040000_sinjira_v25_junior_enable_aal2.sql` | 71 lignes; 1 definer; insert + update; AAL2 + verrou transactionnel | Vérifier qu'aucune activation Junior n'est possible sans tuteur valide, AAL2 effectif et sérialisation du lien tuteur avant consentement. |
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
| 42 | `20260924173000_sinjira_v25_junior_comment_author_visibility.sql` | 89 lignes; 1 `SECURITY DEFINER`; redéfinition du fil Junior interne; aucune mutation de données | Vérifier que publications **et commentaires** exigent encore une bande child active et un consentement Junior courant, sans recréer de DEFINER public ni supprimer l’historique. |
| 43 | `20260924191000_sinjira_v25_junior_hidden_post_comment_guard.sql` | correctif forward-only; redéfinition interne de création commentaire Junior; aucune mutation de données existantes | Vérifier qu’un post masqué par modération refuse immédiatement tout nouveau commentaire, que la réversion humaine restaure le comportement normal et qu’aucun DEFINER public n’est recréé. |

## Journal de relecture automatisée ciblée — 2026-09-24

> **Information technique uniquement — toujours NON REVU / NON APPROUVÉ.**  
> Les observations ci-dessous documentent une lecture automatisée et la cohérence avec les preuves locales/CI. Elles ne remplissent aucune case de décision humaine et n'autorisent ni promotion, ni fusion, ni production.

### Migrations 11 et 13

- **#11 — rétablissement child_pending** : la consommation reste sérialisée par compte, à usage unique et limitée aux bandes pending admissibles. Le validateur exige exactement les formats historiques 10 caractères ou renforcés 16 caractères; aucun format plus large n'est accepté.
- **#13 — émission AAL2 du code parental** : l'émission reste adulte + AAL2, invalide les anciens codes ouverts du même tuteur et génère désormais 16 chiffres hexadécimaux en excluant les nibbles version/variant de l'UUID v4, soit 64 bits aléatoires effectifs. Les codes historiques 10 caractères restent consommables seulement jusqu'à leur expiration existante. Aucun suivi supplémentaire des tentatives n'est ajouté.

### Migration 16

- **#16 — activation Junior AAL2** : l'autorisation parent/tuteur est désormais sérialisée sur la ligne `guardian_links` active avec `FOR UPDATE` avant l'écriture du consentement. Cela ferme la course où une révocation pouvait auparavant tomber entre la vérification du lien et l'insert/upsert du consentement, puis laisser un consentement dormant susceptible de réapparaître après réactivation. Le pgTAP multi-tuteur compte désormais 26 assertions et vérifie la présence du verrou sur l'implémentation interne finale après la frontière RPC #33.

### Migrations 28 à 32

- **#28 — profil privé 11+** : lecture et écriture restent self-only sous MFA. Le minimum 11 ans est conservé, un tuteur vérifié et non révoqué reste obligatoire avant 14 ans, et un mineur ne peut pas déplacer sa date de naissance vers une date plus ancienne qui augmenterait son âge sans déclencher `BIRTH_DATE_PROTECTION_BOUNDARY_REQUIRES_REVIEW`. Les comptes jeunesse restent limités aux juridictions explicitement activées.
- **#29 — seed Livre I** : le seed publie seulement les métadonnées de catalogue et une démo publique; aucun chemin de stockage privé n'est écrit dans le catalogue navigateur. L'actif intégral est créé dans `private.sinjira_private_novel_assets` avec `enabled=false` et `on conflict(novel_id) do nothing`, ce qui préserve une configuration privée existante.
- **#30 — pseudo public / nom privé** : le trigger social dérive `social_profiles.pseudo` **et** `social_profiles.display_name` uniquement de `profiles.pseudo`; `profiles.display_name` n'est jamais copié dans le profil social. Le workflow Compte/catalogue surveille désormais cette migration et son pgTAP vérifie explicitement qu'un nom affiché privé différent ne fuit pas dans `social_profiles`.
- **#31 — assets romans privés** : RLS reste activée sans policy membre; `public`, `anon` et `authenticated` n'ont aucun accès direct. Seul `service_role` conserve SELECT/INSERT/UPDATE/DELETE pour les chemins serveur de livraison.
- **#32 — visibilité catalogue créateur** : la policy ajoute uniquement un droit de lecture au propriétaire canonique via `is_sinjira_owner(auth.uid())`. Elle ne crée ni achat, ni entitlement, ni ligne `project_access`; le pgTAP compte vérifie séparément que le catalogue complet du créateur ne fabrique aucun droit produit commercial.

### Migrations 33 et 34

- **#33 — frontière RPC publique V25** : 23 implémentations `SECURITY DEFINER` sont déplacées hors du schéma API public puis remplacées par des wrappers `SECURITY INVOKER`; les trois seuls wrappers anonymes attendus restent bornés aux helpers nécessaires aux RLS. Le pgTAP Communauté Junior vérifie désormais l'état **final reconstruit** et échoue si l'un de ces 23 noms redevient `SECURITY DEFINER` dans `public` après une migration ultérieure.
- **#34 — privilèges navigateur catalogue** : `project_access_rank()` privilégié est déplacé dans `sinjira_catalog_internal`, son wrapper public reste réservé au `service_role`, et les rôles navigateur ne reçoivent que les opérations de tables explicitement nécessaires. La preuve finale couvre en plus l'absence d'auto-attribution `project_access` et le retour `0` lors d'un sondage UUID non self.

### Migrations 35 et 36

- **#35 — minimisation Mode Voyage** : l'implémentation interne dérive toujours le propriétaire de `auth.uid()`, conserve le step-up MFA, normalise/déduplique les codes pays et impose 1 à 12 destinations. `multi_country` est recalculé côté serveur à partir des destinations réelles plutôt que cru depuis le client. Les réponses internes ne retournent ni `user_id`, ni `delete_after`; l'annulation filtre simultanément `id + user_id + status='active'`, ce qui évite un oracle plan tiers / plan inexistant.
- **#36 — helpers navigateur self-only** : `project_access_rank` retourne `0` lorsqu'un appel non-`service_role` cible un UUID différent de `auth.uid()`. Les helpers projet/document 11–12 restent bornés à l'état approuvé, au rang réel du compte courant et à la visibilité compatible; anon ne peut pas confirmer l'existence d'un contenu `account` ou `restricted`.

### Migrations 37 à 43
- **#37 — catalogue famille créateur** : registre familial privé borné au `user_id`, aucun courriel stocké dans la table, provisionnement réservé au `service_role`, catalogue complet distinct des entitlements commerciaux. Les comptes 11–12 famille ne reçoivent que des fiches minimisées; l'accès intégral reste fermé. Le script de provisionnement est en plus borné au host Supabase canonique dérivé de `supabase/config.toml`.
- **#38 — droits produits issus des commandes** : le droit canonique exige explicitement `o.status='paid'` ou un entitlement réel; une commande `pending` ne donne aucun droit. Le RPC des droits effectifs est self-only et ne retourne ni numéro de commande, ni montant, ni devise, ni courriel.
- **#39 — extensions produit** : les anciennes policies SELECT connues sont retirées avant recréation. Une extension achetée doit être `approved` ou `released`, et son projet parent ne doit pas être `draft`. Une extension interne en conception reste invisible au membre standard même avec un produit associé.
- **#40 — frontière âge/catalogue** : les policies navigateur utilisent le helper âge self-only; le wrapper public `has_sinjira_product` retourne `false` aux comptes 11–12 et aux UUID non self. Les lignes de commandes, order items, entitlements et métadonnées produits commerciales restent masquées aux comptes child.
- **#41 — projets/documents produit** : toutes les anciennes policies SELECT de `public.documents` sont supprimées dynamiquement avant la policy canonique. Les projets payants exigent un droit produit réel pour adult/youth. Pour 11–12, le helper interne final exige `product_slug is null`; les wrappers publics déplacés par #33 délèguent vers ces helpers internes, ce qui ferme aussi les documents d'un projet payant même avec un rang `player`. Un accès explicite `player/tester` peut toujours ouvrir un brouillon pour adult/youth : ce comportement est distinct d'un achat et doit rester un point de décision humaine. La relecture automatisée confirme que le navigateur n'a que `SELECT` sur `public.project_access`, sans `INSERT`, et que `sinjira_catalog_internal.project_access_rank()` retourne `0` si un appel non-`service_role` cible un UUID différent de `auth.uid()`; le pgTAP compte V25 porte désormais une assertion explicite anti-auto-attribution.
- **#42 — visibilité auteur Junior** : le fil interne exige pour les publications **et** les commentaires que l'auteur soit encore dans la bande Junior et conserve un consentement Junior actif. La révocation masque le contenu sans supprimer l'historique et aucun nouveau `SECURITY DEFINER` public n'est créé.
- **#43 — arrêt d’interaction sur post masqué** : la création de commentaire interne exige désormais `moderation_content_visible('real','post',p.id)`. Un `hide_content` humain doit produire `JUNIOR_POST_UNAVAILABLE`; la migration ne supprime aucun contenu existant et ne recrée aucun `SECURITY DEFINER` public.

### Preuves CI associées observées sur le HEAD fonctionnel `aac9aa92ef4b6ab14eff53c8fcd230b3a5f17729`

- **Refonte compte et catalogue** : succès, incluant la preuve `plan(50)` que le propriétaire voit le catalogue complet sans fabriquer de droit produit commercial;
- **Communauté Junior 11–12** : dernière preuve verte avant #43 avec `plan(59)`; le nouveau `plan(60)` ajoute le refus de commentaire pendant un `hide_content` et doit être confirmé par la nouvelle vague CI;
- **Catalogue romans privés** : succès, avec frontière de livraison privée toujours bornée à l'âge et au droit canonique;
- **Snapshot revue release enfant Junior** : le lot est désormais porté à 43 migrations, toutes non revues et non approuvées; le snapshot doit être recalculé avec l’empreinte #43.

## Ordre conseillé de lecture technique

Sans constituer un classement de sûreté, un ordre efficace pour la **lecture humaine** est :

1. commencer par les frontières qui ont la plus grande surface de privilèges/RLS : 4, 5, 33, 34, 37, 39, 40, 41, puis relire 42 avec la révocation Junior et 43 avec la modération des commentaires;
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
- les 43 migrations restent non revues;
- le reviewed batch reste inchangé;
- le ledger reste inchangé;
- aucun prévol distant ni déploiement production n'est autorisé;
- la PR reste draft.
