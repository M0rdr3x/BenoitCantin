# SINJIRA V25 — Plan de revue des 34 migrations futures

Date de préparation : 2026-09-20  
Branche : `a1/integration-rehearsal`  
PR : #435

> **Statut : préparation de revue uniquement.**
>
> Ce document ne constitue **aucune approbation** de migration, ne modifie pas le lot `reviewed_batch`, ne modifie pas le ledger production et n'autorise aucun déploiement Supabase production.

## Source de vérité du périmètre

Le prévol production a identifié exactement **34 migrations futures non revues**. Elles sont regroupées ici pour permettre une revue humaine ordonnée par dépendances et surface de risque.

Répartition :
- **Lot A — Mode Voyage : 3 migrations**
- **Lot B — Enfant / Junior / Tuteur : 22 migrations**
- **Lot C — Compte / Catalogue / RPC : 9 migrations**

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

## Lot A — Mode Voyage (3)

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

**Ordre de revue recommandé : A1 → A2 → A3.**

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

- [ ] `20260919130000_sinjira_v25_account_catalog_browser_privileges.sql`
  - Réaccorde uniquement les privilèges navigateur nécessaires pour rendre les RLS atteignables.
  - **Très sensible** : vérifier chaque `GRANT` / `REVOKE`; aucun `UPDATE/DELETE` ou privilège administratif supplémentaire.

**Ordre de revue recommandé : C1 → C2.**  
La migration RPC `20260919123000` doit être revue avant `20260919130000`, car les privilèges navigateur ne doivent être validés qu'une fois les frontières publiques finalisées.

---

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

- 34 / 34 migrations : **NON REVUES**
- 0 migration ajoutée au lot production par ce document
- 0 changement du ledger production
- 0 déploiement production
- PR #435 : répétition/intégration uniquement

Ce document sert de checklist de revue et de preuve de préparation; il ne doit jamais être interprété comme une autorisation de promotion.
