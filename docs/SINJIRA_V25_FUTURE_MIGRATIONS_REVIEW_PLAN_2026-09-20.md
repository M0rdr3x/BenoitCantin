# SINJIRA V25 — Plan de revue des migrations futures

Date de préparation : 2026-09-20  
Branche : `a1/integration-rehearsal`  
PR : #435

> **Statut : préparation de revue uniquement.**
>
> Ce document ne constitue **aucune approbation** de migration, ne modifie pas le lot `reviewed_batch`, ne modifie pas le ledger production et n'autorise aucun déploiement Supabase production.

## Source de vérité du périmètre

Le prévol production a identifié initialement **34 migrations futures non revues**. La revue statique a ensuite ajouté une migration corrective forward-only pour fermer la réponse interne Mode Voyage, portant le delta à **35 migrations futures non revues**. La revue croisée B1/C a ensuite identifié des helpers navigateur pouvant sonder un autre UUID ou du contenu `account`; leur correctif forward-only porte le delta courant à **36 migrations futures non revues**. Elles sont regroupées ici pour permettre une revue humaine ordonnée par dépendances et surface de risque.

Répartition :
- **Lot A — Mode Voyage : 4 migrations**
- **Lot B — Enfant / Junior / Tuteur : 22 migrations**
- **Lot C — Compte / Catalogue / RPC : 9 migrations**
- **Lot D — Frontières helpers navigateur : 1 migration**

L'ordre ci-dessous est un **ordre de revue**, pas un ordre d'autorisation production.

## Critères communs avant toute approbation

Pour chaque migration :
- [ ] vérifier le diff SQL complet et les objets remplacés;
- [ ] vérifier les dépendances sur les migrations précédentes;
- [ ] vérifier `SECURITY DEFINER` / `SECURITY INVOKER`, `search_path`, ACL `GRANT/REVOKE` et exposition du schéma `public`;
- [ ] vérifier les policies RLS et leur comportement `anon` / `authenticated` / `service_role`;
- [ ] vérifier les effets de `DROP POLICY`, `DROP TRIGGER`, remplacement de fonctions et changements de privilèges;
- [ ] vérifier les chemins de révocation, désactivation et récupération fail-closed;
- [ ] vérifier **chaque état intermédiaire du batch** : aucune fonctionnalité ne doit être exposée avec une politique plus permissive avant qu'une migration ultérieure ne la durcisse;
- [ ] lorsqu'une migration ultérieure remplace une fonction/policy pour la rendre plus sûre, vérifier si cette protection doit être présente dès la migration d'introduction afin d'éviter une fenêtre transitoire pendant `db push`;
- [ ] vérifier les tests pgTAP / validateurs statiques / preuves navigateur associés;
- [ ] reconstruire une base locale propre et exécuter les tests concernés;
- [ ] confirmer qu'aucune donnée privée supplémentaire n'est exposée au navigateur;
- [ ] confirmer qu'aucune migration n'élargit implicitement les droits d'un enfant, d'un tuteur, d'un membre ou du créateur;
- [ ] seulement après revue humaine : décider séparément si la migration peut entrer dans un lot production revu.

---

## Lot A — Mode Voyage, noyau initial (3)

### A1 — Bornage du signal géographique

- [ ] `20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql`
  - Objet principal : `private.security_risk_score_v25`.
  - But déclaré : empêcher le Mode Voyage de diminuer des risques sans rapport avec la géographie.
  - Revue prioritaire : vérifier que seul le signal géographique attendu est neutralisé et qu'aucun appareil inconnu, récupération ou action sensible n'obtient un bonus global.

### A2 — Rétention

- [ ] `20260913230000_sinjira_v25_travel_mode_retention_purge.sql`
  - Objet principal : `private.security_purge_expired_travel_plans_v25`.
  - Fonction privilégiée de purge.
  - Revue prioritaire : vérifier l'autorité de `delete_after`, l'absence d'ordonnanceur implicite et la portée exacte des suppressions.

### A3 — Visibilité navigateur et RPC

- [ ] `20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql`
  - Objets principaux : `public.security_create_travel_plan`, `public.security_cancel_travel_plan`, policy de lecture propre.
  - Revue prioritaire : vérifier que le navigateur ne voit que ses propres plans actifs/non expirés et que les détails de rétention restent serveur.
  - Point sensible : ACL, RLS, `auth.uid()`, remplacement de frontière publique.

**Ordre de revue recommandé : A1 → A2 → A3, puis la réaffirmation forward-only `20260921005000`.**

### Notes de revue statique du lot A — non approbatives

Relecture technique effectuée sur la branche d'intégration, sans modifier le statut des cases ci-dessus :

- `security_risk_score_v25` ne contient plus aucun bonus global lié à `p_travel_match`; le paramètre est conservé uniquement pour compatibilité.
- `security_evaluate_context` neutralise `unexpected_region` uniquement lorsqu'un voyage actif correspond, tandis que `impossible_travel` reste indépendant et force un challenge.
- Le pgTAP `security_travel_scope_v25.test.sql` prouve qu'un voyage ne réduit ni appareil inconnu, ni action sensible, ni récupération récente, ni voyage impossible.
- La purge dédiée supprime uniquement les lignes dont `delete_after` est échu, ne reçoit aucun instant arbitraire et n'est exécutable que par `service_role`.
- La table `security_travel_plans` reste RLS; le navigateur authentifié ne reçoit que `SELECT`, self-only, statut `active`, non expiré; aucun DML direct n'est accordé.
- La revue a découvert que les fonctions `sinjira_security_internal` restaient directement exécutables par `authenticated`; laisser la minimisation uniquement à `20260921005000` créait donc une fenêtre transitoire pendant un `db push` séquentiel.
- `20260914223000` redéfinit désormais immédiatement ces fonctions internes avec la même réponse minimale que les wrappers publics. `20260921005000` reste une réaffirmation forward-only de cette frontière finale. Les tests de visibilité restent à 28 assertions et le validateur exige maintenant la minimisation à la fois à l’étape A3 et à l’état final.

**Portes encore ouvertes avant toute approbation du lot A :**
- exécution verte des workflows Mode Voyage sur le HEAD gelé;
- reconstruction Supabase locale complète avec la migration `20260921005000`;
- revue humaine du diff SQL final et des 28 assertions pgTAP;
- confirmation séparée qu'aucune promotion reviewed/ledger n'est effectuée par cette revue.

Aucune case n'est cochée ici : cette section documente une **préparation technique de revue**, pas une approbation.

---

## Lot B — Enfant / Junior / Tuteur (22)

### B1 — Fondation âge, supervision et Communauté Junior

- [ ] `20260916210000_sinjira_v25_child_guardian_signup.sql`
  - Minimum 11 ans, bandes d'âge, supervision et hook de création utilisateur.
  - **Très sensible** : Auth, `SECURITY DEFINER`, création de lien tuteur, transition automatique à 13 ans.
  - Point de revue transitoire : dès l'ouverture du parcours 11+, émission **et lecture** des codes parentaux sous AAL2, révocation tuteur sous AAL2 avec sortie immédiate du mineur, et `can_view_contact_metadata=false` sur création/réactivation.
  - Le trigger historique `sync_guardian_signup_invite_link_trigger` doit appeler une implémentation V25 qui ne peut jamais réactiver implicitement le partage des métadonnées.
  - `guardian_code` est une capacité à usage unique : son trigger de suppression et le nettoyage des résidus `auth.users.raw_user_meta_data` doivent exister dès cette migration, avant toute inscription 11+.
  - La visibilité du tuteur doit déjà s'arrêter au passage à `adult` pour `guardian_links` et pour les invitations consommées; le compte concerné conserve son propre historique.
  - Avant que `handle_new_sinjira_user()` puisse créer un compte 11–12, la frontière serveur child doit déjà refuser les mutations sensibles, maintenir la recherche/contribution à OFF et fermer playtests/contenus non classés indépendamment de la navigation.
  - Convergence transitoire : `20260916210000` et `20260918010000` gardent désormais les comptes `child` authentifiés hors de `projects/documents` jusqu’à l’introduction de `child_access_status`; l’accès 11–12 n’est rouvert qu’avec `approved_11_12` dans `20260918013000`.
  - Le classifieur serveur de contenu/messagerie doit reconnaître `child`, `child_pending` et toute bande inconnue en mode fail-closed dès cette même migration; aucun intervalle ne doit précéder `20260918023000`.
  - La même migration remplace désormais immédiatement `get_guardian_youth_contacts()` par la version consentement explicite + AAL2 + réponse minimisée (`contact_label`, réseau, date UTC seulement), afin que l’élargissement de `sinjira_parent_can_supervise()` aux 11–12 ans ne réactive jamais l’ancien RPC plus intrusif.

- [ ] `20260917223000_sinjira_v25_junior_community.sql`
  - Crée les 3 tables Junior et les RPC de consentement, fil, publication, commentaire, signalement et résumé.
  - **Très sensible** : grande surface SQL, nombreux RPC privilégiés, tables isolées, pseudonymisation, signalement/blocage.
  - Point de revue transitoire : dès cette migration, activation Junior sous AAL2, révocation durable du consentement, exclusion des liens tuteur révoqués, aucun `junior_alias` dans la vue parent et résumé parental AAL2 réduit à une date UTC.

- [ ] `20260918010000_sinjira_v25_child_sensitive_boundary.sql`
  - Frontière serveur des modules non certifiés pour 11–12 ans.
  - **Très sensible** : policies projets/documents/playtests, triggers de refus de mutations child.

- [ ] `20260918013000_sinjira_v25_child_content_rating.sql`
  - Classement explicite projets/documents 11–12.
  - Revue prioritaire : défaut `unreviewed`, double approbation document + projet, absence d'élargissement implicite.
  - Fenêtre transitoire : dès cette migration d’introduction, `anon` ne doit jamais confirmer un projet `account` par UUID et le helper document doit déjà exiger le rang d’accès réel; `20260921010000` réaffirme ces invariants après déplacement des helpers.

- [ ] `20260918020000_sinjira_v25_account_capabilities.sql`
  - RPC self-only `public.sinjira_my_account_capabilities`.
  - Revue prioritaire : aucune date de naissance ni UUID arbitraire exposé; décisions fail-closed.

- [ ] `20260918023000_sinjira_v25_minor_content_policy_compat.sql`
  - Compatibilité du classifieur de contenu avec `child` / `child_pending`.
  - Revue prioritaire : toute bande mineure, pending ou inconnue reste protégée.

### B2 — Révocation, rétablissement et consentement durable

- [ ] `20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql`
  - Révocation tuteur fail-closed pour Junior.

- [ ] `20260919013000_sinjira_v25_child_pending_guardian_redeem.sql`
  - Rétablissement depuis `child_pending` via code parental.
  - Revue prioritaire : ne jamais ajouter implicitement un tuteur à un compte déjà supervisé.
  - Concurrence : sérialiser les consommations sur la ligne `account_safety_profiles` du compte avant de recalculer sa bande; deux codes distincts ne doivent jamais pouvoir créer deux liens `verified` à partir du même état pending observé en parallèle.

- [ ] `20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql`
  - Trigger de révocation durable du consentement Junior.
  - Revue prioritaire : un lien recréé ne doit jamais ressusciter un ancien consentement.

### B3 — AAL2 et agence de l'enfant

- [ ] `20260919023000_sinjira_v25_guardian_invite_aal2.sql`
  - AAL2 obligatoire pour créer un code parental.

- [ ] `20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql`
  - Nettoyage du `guardian_code` dans les métadonnées Auth après consommation.
  - Revue prioritaire : ordre du trigger `zz_`, aucune persistance du secret.

- [ ] `20260919033000_sinjira_v25_guardian_invite_read_aal2.sql`
  - Lecture des codes parentaux bornée self-only + AAL2.
  - Fenêtre transitoire fermée : la policy conserve aussi dès cette migration la borne de majorité des invitations consommées; `20260919053000` ne doit pas être nécessaire pour réparer une réouverture intermédiaire.

- [ ] `20260919040000_sinjira_v25_junior_enable_aal2.sql`
  - Activation Junior exige AAL2; désactivation reste possible sans step-up.
  - Revue prioritaire : préserver la voie de retrait immédiat.

- [ ] `20260919043000_sinjira_v25_guardian_revoke_aal2.sql`
  - Révocation par tuteur exige AAL2; l'enfant conserve une sortie immédiate.
  - Revue prioritaire : ne pas conditionner l'agence du mineur à un second facteur du tuteur.

### B4 — Fin de visibilité à la majorité

- [ ] `20260919050000_sinjira_v25_guardian_majority_visibility.sql`
  - RLS des `guardian_links` bornée à la minorité.

- [ ] `20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql`
  - Les invitations consommées cessent d'être visibles au tuteur à la majorité.

### B5 — Métadonnées parentales minimisées

- [ ] `20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql`
  - Lecture des métadonnées de contacts : consentement explicite + AAL2.

- [ ] `20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql`
  - Privacy-by-default; nouveaux liens et réactivations remettent la permission à `false`.
  - Seul le compte enfant/jeunesse concerné peut activer/retirer.

- [ ] `20260919070000_sinjira_v25_guardian_contacts_minimization.sql`
  - Retire UUID, `display_name` et heure précise du résumé parental.

- [ ] `20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql`
  - Résumé Junior minimisé sous AAL2; aucun contenu des messages/publications.

- [ ] `20260919080000_sinjira_v25_guardian_character_identity_isolation.sql`
  - Cloisonnement entre réseau Compte et réseau Personnage.

- [ ] `20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql`
  - L'alias Junior n'est pas révélé au tuteur.

**Ordre de revue recommandé : B1 → B2 → B3 → B4 → B5.**  
Ne pas revoir B3/B4/B5 isolément sans avoir validé les invariants de B1/B2 qu'ils remplacent ou resserrent.

---

## Lot C — Compte / Catalogue / RPC (9)

### C1 — Catalogue compte et romans privés

- [ ] `20260919090000_sinjira_v25_account_content_hub.sql`
  - Policies catalogue membres/créateur.
  - Revue prioritaire : accès créateur complet sans faux achat/entitlement.

- [ ] `20260919093000_sinjira_v25_private_novel_catalog.sql`
  - Table privée `private.sinjira_private_novel_assets`; catalogue self-only.
  - **Très sensible** : aucun chemin de stockage privé ne doit sortir au navigateur.

- [ ] `20260919100000_sinjira_v25_private_profile_age_11.sql`
  - Compatibilité du coffre Profil privé avec 11+.
  - Revue prioritaire : 11–13 conditionnés à une supervision valide.
  - La garde est désormais symétrique : `private_profile_get()` et `private_profile_save(...)` refusent tous deux un compte avant 14 ans sans lien tuteur `verified` non révoqué; le MFA historique reste requis.

- [ ] `20260919103000_sinjira_v25_livre_i_catalog_seed.sql`
  - Ancrage canonique du Livre I.
  - Revue prioritaire : données de catalogue uniquement, aucun PDF intégral ni chemin privé.

- [ ] `20260919110000_sinjira_v25_social_public_pseudo_privacy.sql`
  - Le profil social ne reçoit plus le `display_name` privé; miroir du pseudonyme public uniquement.

- [ ] `20260919113000_sinjira_v25_private_novel_asset_rls.sql`
  - RLS sur le registre privé de romans, sans policy membre.
  - Revue prioritaire : table effectivement fail-closed pour les rôles navigateur.

### C2 — Visibilité créateur, frontière RPC et privilèges navigateur

- [ ] `20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql`
  - Visibilité catalogue projets pour le créateur uniquement; aucun faux entitlement.

- [ ] `20260919123000_sinjira_v25_public_rpc_boundary.sql`
  - Reconvergence des RPC privilégiés hors de `public`; wrappers publics `SECURITY INVOKER`.
  - **Très sensible** : vérifier chaque signature, ACL, résolution de fonction et absence de contournement par `search_path`.
  - Précondition fail-closed renforcée : les 23 noms doivent chacun résoudre vers exactement une RPC `public SECURITY DEFINER`; les 3 cibles anon doivent chacune exister exactement une fois avec `EXECUTE` anon avant déplacement. Un overload inattendu ne peut plus masquer une cible absente.

- [ ] `20260919130000_sinjira_v25_account_catalog_browser_privileges.sql`
  - Réaccorde uniquement les privilèges navigateur nécessaires pour rendre les RLS atteignables.
  - **Très sensible** : vérifier chaque `GRANT` / `REVOKE`; aucun `UPDATE/DELETE` ou privilège administratif supplémentaire.
  - Convergence transitoire : dès le déplacement de `project_access_rank(uuid,uuid)`, l’implémentation interne devient self-only pour `anon/authenticated`; `service_role` seul conserve le ciblage d’un UUID explicite. `20260921010000` réaffirme ensuite la même frontière.

**Ordre de revue recommandé : C1 → C2.**  
La migration RPC `20260919123000` doit être revue avant `20260919130000`, car les privilèges navigateur ne doivent être validés qu'une fois les frontières publiques finalisées.

---

## Lot A — correctif forward-only découvert pendant la revue

Cette migration appartient fonctionnellement au **Lot A — Mode Voyage**, mais son timestamp est postérieur aux lots B/C. Elle reste donc listée ici afin que la checklist conserve l'ordre chronologique canonique exigé par le garde automatique.

- [ ] `20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql`
  - Réduit la réponse directe des implémentations `sinjira_security_internal.security_create_travel_plan` et `security_cancel_travel_plan`.
  - Motif : les fonctions internes restent exécutables par `authenticated` pour permettre aux wrappers publics `SECURITY INVOKER` de fonctionner; elles ne doivent donc jamais retourner davantage de données que les wrappers publics.
  - Revue prioritaire : confirmer que les gardes AAL2, validation ISO, durée <= 180 jours, self-only et rétention restent inchangées.
  - Vérifier que création directe interne retourne uniquement `id`, `status`, `starts_at`, `ends_at`, `destinations`.
  - Vérifier que l'annulation directe interne retourne uniquement `id` et `status`.
  - Vérifier l'absence de `user_id`, `delete_after`, `cancelled_at`, timestamps techniques et `multi_country` dans les réponses.
  - Preuve associée : `security_travel_client_visibility_v25.test.sql` étendu à 28 assertions.

## Lot D — Frontières helpers navigateur (1)

- [ ] `20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql`
  - Conserve l’OID de `sinjira_catalog_internal.project_access_rank(uuid,uuid)` utilisé par les policies RLS, mais retourne `0` lorsqu’un rôle navigateur fournit un `p_user_id` différent de `auth.uid()`; `service_role` conserve l’usage serveur arbitraire.
  - Ferme l’oracle anonyme de `sinjira_child_project_available(uuid)` : un projet `visibility='account'` exige désormais une session authentifiée.
  - Aligne `sinjira_child_document_available(uuid)` sur le rang réel du compte courant via `project_access_rank >= document_access_rank`.
  - Preuves attendues : pgTAP Compte à 45 assertions et classement 11–12 à 23 assertions.
  - Migration transversale B/C : revue conjointe avec la frontière RPC V25 et les policies projets/documents.

### Notes de revue statique du Lot D — non approbatives

La revue croisée des définitions et des preuves runtime confirme actuellement :

- `sinjira_catalog_internal.project_access_rank(uuid,uuid)` conserve son OID, nécessaire aux policies RLS existantes;
- pour `anon` / `authenticated`, un `p_user_id` différent de `auth.uid()` retourne `0` avant toute lecture de rang;
- le pgTAP Compte exécute réellement ce cas avec un membre authentifié ciblant l'UUID d'un autre compte et attend `0`;
- `service_role` conserve explicitement `EXECUTE` sur le helper interne et un test runtime prouve qu'il peut calculer le rang d'un UUID explicite différent du compte JWT, afin de préserver les traitements serveur légitimes;
- la migration d’introduction `20260918013000` applique désormais la même fermeture pour éviter toute fenêtre intermédiaire pendant le batch;
- `anon` ne peut plus obtenir `true` sur un projet `visibility='account'` approuvé 11–12;
- le pgTAP classement 11–12 exécute ce cas sur projet **et** document;
- les contenus `restricted` restent fermés sans rang d'accès réel;
- les wrappers publics V25 restent `SECURITY INVOKER` et délèguent aux implémentations internes durcies;
- le workflow Compte et le workflow Communauté/accès enfant surveillent explicitement `20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql`.

**Portes encore ouvertes avant toute approbation du Lot D :**
- exécution verte des deux workflows sur un HEAD gelé;
- reconstruction Supabase locale complète avec la migration `20260921010000`;
- revue humaine de la sémantique `service_role` pour les appels serveur avec UUID explicite;
- vérification que les policies RLS dépendantes continuent d'appeler le même OID après reconstruction;
- aucune promotion reviewed/ledger par cette revue.

Aucune case n'est cochée : cette section documente seulement la préparation technique.

## Portes de sortie de revue

Une famille ne peut être proposée comme « revue » que si :
1. toutes ses migrations sont comprises individuellement;
2. leurs interactions sont relues dans l'ordre;
3. les tests locaux associés passent sur une reconstruction propre;
4. les preuves négatives (accès refusés, révocations, AAL1, child, tiers) sont couvertes;
5. les données exposées au navigateur ont été comparées avant/après;
6. le reviewer confirme explicitement le périmètre et le SHA;
7. le lot `reviewed_batch` et le ledger production restent inchangés jusqu'à cette décision explicite.

## État au moment de la création de ce document

- 36 / 36 migrations : **NON REVUES**
- 0 migration ajoutée au lot production par ce document
- 0 changement du ledger production
- 0 déploiement production
- PR #435 : répétition/intégration uniquement

Ce document sert de checklist de revue et de preuve de préparation; il ne doit jamais être interprété comme une autorisation de promotion.
