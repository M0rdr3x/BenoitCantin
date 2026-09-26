# SINJIRA V25 — Plan de revue des migrations futures

Date de préparation : 2026-09-20  
Branche : `a1/integration-rehearsal`  
PR : #435

> **Statut : préparation de revue uniquement.**
>
> Ce document ne constitue **aucune approbation** de migration, ne modifie pas le lot `reviewed_batch`, ne modifie pas le ledger production et n'autorise aucun déploiement Supabase production.

## Source de vérité du périmètre

Le prévol production a identifié initialement **34 migrations futures non revues**. La revue statique a ensuite ajouté une migration corrective forward-only pour fermer la réponse interne Mode Voyage, portant le delta à **35 migrations futures non revues**. La revue croisée B1/C a ensuite identifié des helpers navigateur pouvant sonder un autre UUID ou du contenu `account`; leur correctif forward-only a porté le delta à **36 migrations futures non revues**. La demande de catalogue complet pour le créateur et ses comptes familiaux, sans publier de courriel ni fabriquer de faux achat, ajoute maintenant une migration forward-only dédiée : les frontières self-only d’âge/catalogue et l’accès produit générique projets ajoutent ensuite deux migrations forward-only supplémentaires : le delta courant est désormais de **43 migrations futures non revues** après deux correctifs Junior forward-only supplémentaires (#42 visibilité auteur et #43 arrêt des commentaires sur publication masquée). Elles sont regroupées ici pour permettre une revue humaine ordonnée par dépendances et surface de risque.

Répartition :
- **Lot A — Mode Voyage : 4 migrations**
- **Lot B — Enfant / Junior / Tuteur : 22 migrations**
- **Lot C — Compte / Catalogue / RPC : 9 migrations**
- **Lot D — Frontières helpers navigateur : 1 migration**
- **Lot E — Catalogue famille créateur : 5 migrations**

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

**Preuves techniques maintenant satisfaites pour le lot A :**
- sur le HEAD applicatif `6ace8163c5a68d496d77e635c6b29132876a5b45`, les workflows Rétention, Consentement, Self-only, Vue éphémère, Visibilité client et Minimisation navigateur Mode Voyage sont verts;
- la reconstruction locale applique bien `20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql`;
- la suite rétention passe **11/11** assertions et la visibilité client passe **28/28** assertions, avec garde statique et auto-test verts;
- le HEAD documentaire ultérieur ne modifie aucun SQL du lot A.

**Restent ouverts avant toute approbation du lot A :**
- revue humaine du diff SQL final et des assertions pgTAP sur le SHA choisi;
- confirmation explicite du reviewer sur le périmètre du lot;
- confirmation séparée qu'aucune promotion reviewed/ledger n'est effectuée par cette revue.

Aucune case n'est cochée ici : cette section documente une **préparation technique de revue**, pas une approbation.

---

## Lot B — Enfant / Junior / Tuteur (22)

### B1 — Fondation âge, supervision et Communauté Junior

- [ ] `20260916210000_sinjira_v25_child_guardian_signup.sql`
  - Minimum 11 ans, bandes d'âge, supervision et hook de création utilisateur.
  - **Très sensible** : Auth, `SECURITY DEFINER`, création de lien tuteur, transition automatique à 13 ans.
  - Le cas créateur doit être résolu par l’autorité serveur `internal_admin_users.role='owner'`, jamais par une adresse courriel personnelle gravée dans la migration.
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


### Notes de revue statique du Lot B — non approbatives

Relecture technique effectuée sur le HEAD `6ace8163c5a68d496d77e635c6b29132876a5b45`, sans modifier le statut des cases B1–B5 :

- la migration d'introduction 11+ ferme dès B1 les fenêtres transitoires sensibles : code parental créé et relu sous AAL2, révocation tuteur AAL2 avec sortie immédiate du mineur, `guardian_code` supprimé des métadonnées Auth, visibilité tuteur coupée à la majorité, métadonnées de contacts remises à `false` par défaut et RPC contacts déjà minimisé;
- `handle_new_sinjira_user()` refuse <11 ans, exige un code parental valide avant 14 ans, limite le lancement jeunesse au Canada, neutralise le Programme Contributeur à 11–12 ans et crée un lien tuteur `verified` sans activer les métadonnées de contacts;
- la preuve locale d'inscription reconstruit la base puis passe **67/67** assertions `child_guardian_signup_v25.test.sql`, **11/11** assertions du coffre privé enfant et un vrai parcours Auth HTTP à exactement 11 ans; le navigateur 11 ans est également vert;
- B2 sérialise le rétablissement `child_pending` avec un verrou `FOR UPDATE` sur `account_safety_profiles`, verrouille aussi l'invitation consommée, interdit l'auto-tutelle et empêche deux codes concurrents de créer deux liens actifs depuis le même état pending;
- la révocation ou suppression d'un `guardian_link` révoque durablement le consentement Junior associé; une réactivation ultérieure de supervision ne réactive jamais implicitement Junior;
- la suite multi-tuteur est verte avec **25/25** assertions et l'auto-test du garde détecte **10/10** dérives critiques; un second tuteur valide ne maintient pas le consentement Junior du tuteur révoqué;
- les redéfinitions B3 conservent les protections de B1/B2 : émission AAL2, invalidation des codes ouverts précédents, minimisation du secret, lecture AAL2 self-only, activation Junior AAL2, désactivation fail-safe AAL1 et révocation immédiate par l'enfant;
- B4 conserve l'historique pour la personne concernée mais masque `guardian_links` et invitations consommées à l'ancien tuteur dès la bande `adult`; le pgTAP vérifie explicitement les deux vues à zéro pour le tuteur à 18 ans;
- B5 applique privacy-by-default : seul le compte `child/youth` lié peut activer ou retirer `can_view_contact_metadata`; le retrait est immédiat et une réactivation du lien remet la permission à `false`;
- `get_guardian_youth_contacts()` exige supervision active + opt-in + AAL2 et ne renvoie que `contact_label`, `network`, `last_contact_date`; les tests prouvent l'absence d'UUID de contact, `display_name`, timestamp précis et contenu, ainsi que l'isolation entre identité Compte et identité Personnage;
- `junior_guardian_summary()` exige AAL2, ne renvoie aucun contenu de publication/message et réduit la dernière activité à une date UTC; la liste parentale ne révèle jamais `junior_alias`;
- le workflow Communauté Junior est entièrement vert : **51/51** assertions Junior, **13/13** frontière serveur 11–12, **23/23** classement contenu, **25/25** capacités self-only et **8/8** compatibilité protection mineurs, plus la preuve navigateur locale;
- le snapshot release sur ce même HEAD reste vert et confirme **39 migrations futures non revues**, empreintes intactes, reviewed batch et ledger inchangés.

**Portes encore ouvertes avant toute approbation du Lot B :**
- relire humainement les 22 diffs B1→B5 dans l'ordre final, notamment les interactions entre policies RLS et fonctions `SECURITY DEFINER`;
- confirmer séparément que la portée juridictionnelle jeunesse reste volontairement limitée au Canada pour cette version;
- ne modifier ni `production-reviewed-migration-batch.txt` ni le ledger sans décision humaine explicite sur le SHA gelé;
- aucune promotion production ne doit être déduite des preuves vertes ci-dessus.

Aucune case B1–B5 n'est cochée : cette section documente une **préparation technique de revue**, pas une approbation.

---

## Lot C — Compte / Catalogue / RPC (9)

### C1 — Catalogue compte et romans privés

- [ ] `20260919090000_sinjira_v25_account_content_hub.sql`
  - Le repair historique du personnage propriétaire doit résoudre l’owner par rôle serveur et ne jamais fabriquer `user_entitlements`, `project_access` ou historique `reader_library` pour simuler l’accès créateur.
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


### Notes de revue statique du Lot C — non approbatives

Relecture technique effectuée sur le HEAD `1a54e110762a5249e99c70fc40e6667ce2858c54`, sans modifier le statut des cases C1/C2 :

- les policies `products_entitled_read`, `products_ordered_read`, `products_owner_read` et `projects_owner_catalog_read_v25` accordent uniquement de la lecture; le rôle créateur reste une visibilité de gestion et ne crée ni entitlement, ni commande, ni `project_access`;
- `private.sinjira_private_novel_assets` est sous RLS dès sa création, sans policy membre, avec privilèges navigateur révoqués; `service_role` reste le seul rôle SQL de livraison;
- `sinjira_my_novel_catalog()` ne renvoie ni bucket ni chemin Storage; `full_access` exige un actif privé activé et soit le rôle créateur, soit un entitlement du compte courant;
- l'Edge Function `get-private-novel-url` exige un JWT, réévalue côté serveur la bande d'âge, le rôle créateur ou l'entitlement, exige `enabled=true` et ne signe l'URL privée qu'après ces contrôles; la durée signée reste bornée à 300 secondes;
- le seed Livre I conserve l'actif privé désactivé et ne publie aucun chemin privé;
- `sync_social_profile_from_profile()` copie uniquement le pseudonyme public vers `social_profiles.pseudo` et `social_profiles.display_name`; le `profiles.display_name` privé n'est pas propagé;
- le workflow Profil privé `35677574965` a reconstruit la base locale puis validé **22/22** assertions historiques et **11/11** assertions enfant; son unique rouge est le ledger attendu parce que les 39 migrations restent non revues;
- la frontière RPC V25 exige exactement 23 cibles `public SECURITY DEFINER` et exactement 3 cibles anon avant déplacement, puis recrée uniquement des wrappers `public SECURITY INVOKER`;
- `sinjira_catalog_internal.project_access_rank(uuid,uuid)` conserve son OID pour les policies RLS mais retourne `0` à un navigateur qui tente de cibler un UUID différent de `auth.uid()`; `service_role` conserve le ciblage serveur explicite;
- les privilèges navigateur du catalogue restent limités à `SELECT` et aux deux insertions self-service nécessaires (`access_requests`, `playtest_participants`), toujours derrière RLS;
- sur le run Compte/catalogue `35677574948`, la validation statique, la reconstruction locale, la preuve membre/créateur et la preuve 11–12 / absence d'oracle ont terminé en succès avant le nettoyage de la pile.

**Preuves techniques maintenant satisfaites pour le Lot C :**
- la dernière preuve verte antérieure du workflow Compte/catalogue reste **45/45** assertions membre/créateur + **23/23** classement 11–12; la suite courante est portée à **49 assertions** et doit être relue sur le HEAD final après les durcissements famille/commande payée;
- la dernière preuve verte Catalogue romans privés reste pgTAP **13/13**; le validateur statique courant est porté à **9 dérives critiques** et doit être relu sur le HEAD final;
- l'Edge `get-private-novel-url` réévalue côté serveur identité, âge, rôle créateur/entitlement, actif `enabled` et stockage avant URL signée 300 s; la régression `Content-Length` doublement échappée est corrigée et gardée;
- les preuves négatives couvrent `anon/authenticated/service_role`, absence de lecture directe du registre privé, absence de chemin Storage dans le navigateur et sondage UUID self-only.

**Restent ouverts avant toute approbation du Lot C :**
- relire humainement les diffs SQL C1 puis C2 dans l'ordre et leurs interactions avec le Lot D;
- confirmer explicitement le périmètre et le SHA choisi;
- ne modifier ni `production-reviewed-migration-batch.txt` ni le ledger sans décision humaine séparée.

Aucune case C1/C2 n'est cochée : cette section documente une **préparation technique de revue**, pas une approbation.

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
  - Preuves attendues : pgTAP Compte à 49 assertions et classement 11–12 à 23 assertions.
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

**Preuves techniques maintenant satisfaites pour le Lot D :**
- les workflows Compte/catalogue et Communauté/accès enfant sont verts après reconstruction complète avec `20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql`;
- le pgTAP Compte courant contient **49 assertions**, dont le refus de sondage d'un autre UUID, le ciblage explicite `service_role`, l'entitlement durable, la commande `paid` et le refus d'une commande `pending`; validation CI finale encore requise sur le SHA gelé;
- le classement 11–12 passe **23/23** assertions, incluant l'absence d'oracle anon sur contenu `account` et le rang réel pour les documents;
- la reconstruction confirme que les policies RLS continuent de fonctionner après conservation de l'OID du helper interne.

**Restent ouverts avant toute approbation du Lot D :**
- revue humaine de la sémantique `service_role` pour les appels serveur avec UUID explicite;
- confirmation explicite du reviewer sur le SHA et l'interaction B/C;
- aucune promotion reviewed/ledger par cette revue.

Aucune case n'est cochée : cette section documente seulement la préparation technique.

---

## Lot E — Catalogue famille créateur (5)

- [ ] `20260922014000_sinjira_v25_creator_family_catalog_access.sql`
  - Ajoute un registre privé de comptes familiaux **par UUID uniquement**; aucun courriel n'est stocké dans la table ni inscrit en clair dans la migration publique.
  - Le provisionnement par courriel est réservé à `service_role` : le courriel est utilisé seulement pour résoudre `auth.users.id`, puis seul l'UUID est conservé.
  - Les implémentations privilégiées famille résident dans `sinjira_v25_internal`; les RPC publics restent `SECURITY INVOKER`, afin de ne pas rouvrir la frontière C2.
  - Le propriétaire conserve son accès complet existant; un compte famille 13+ obtient la visibilité catalogue complète sans création de commande, entitlement ou `project_access` artificiel.
  - Les membres ordinaires restent limités aux contenus publics/gratuits et à leurs achats, entitlements ou accès explicites.
  - Les extensions internes non publiques suivent le catalogue complet pour le créateur/famille `adult`/`youth`. Le membre standard ne voit que le public; un compte famille 11–12 reçoit seulement une fiche self-only minimisée (`protected`, sans contenu ouvrable) tant qu'aucune classification dédiée n'existe.
  - Pour un compte famille 11–12, la visibilité supplémentaire passe par des RPC self-only minimisés : titres/fiches visibles, mais projets non approuvés sans chemin ouvrable ni couverture non classée et romans privés sans `full_access`, `public_path`, `demo_path`, couverture privée ni nombre de pages.
  - `project_access_rank` n'accorde le rang famille `90` qu'aux bandes `adult` / `youth`; un compte `child` ne contourne donc jamais `child_access_status`.
  - `has_sinjira_product(text,uuid)` reconnaît le propriétaire ou la famille `adult/youth` sans créer d'entitlement; le garde anti-énumération self-only reste actif et `child` reste refusé.
  - L'Edge de roman privé reconnaît le rôle famille uniquement après la vérification d'âge déjà existante; les 11–12 restent refusés pour une intégrale non classée.
  - Preuve dédiée : `creator_family_catalog_access_v25.test.sql` porté à **54 assertions** et validateur statique de confidentialité, incluant l'interdiction d'une adresse courriel littérale, le scénario roman payé sans entitlement et la visibilité des extensions internes pour créateur/famille 13+ seulement.

- [ ] `20260922023000_sinjira_v25_paid_order_product_access.sql`
  - Aligne la RLS `products_ordered_read` et `has_sinjira_product(text,uuid)` sur un achat réellement payé.
  - Un entitlement reste un droit même si le produit n'est plus actif à la vente.
  - Une commande avec `status='paid'` conserve le droit produit même si le produit devient ensuite inactif.
  - Une commande `pending` ne rend plus le produit privé visible et ne satisfait jamais `has_sinjira_product()`.
  - Aucun faux entitlement n'est créé; le garde self-only reste inchangé et un navigateur ne peut pas sonder l'accès produit d'un autre UUID.
  - Cette migration doit être retestée à la fois par le workflow Compte/catalogue et par le workflow Romans privés.

- [ ] `20260922030000_sinjira_v25_extension_product_access.sql`
  - Ajoute `extensions.product_slug` comme lien commercial optionnel; aucune extension existante n'est transformée automatiquement en contenu payant.
  - Une extension publique `approved/released` reste gratuite et lisible selon la policy publique existante.
  - Une extension privée liée à un produit devient lisible pour un membre standard uniquement si `has_sinjira_product()` confirme un entitlement réel ou une commande `paid`.
  - Une commande `pending` ne suffit jamais, car la policy délègue au droit produit canonique.
  - Les rôles créateur/famille 13+ conservent le catalogue complet; les 11–12 famille restent limités à une fiche minimisée et non ouvrable.
  - Le RPC `sinjira_my_extension_catalog()` expose `access_source='product'` pour distinguer proprement un achat réel du gratuit/public.
  - Preuve dédiée dans `creator_family_catalog_access_v25.test.sql` : invisible avant achat en RLS + RPC, visible après commande `paid` en RLS + RPC, sans faux entitlement.


- [ ] `20260922031500_sinjira_v25_catalog_age_helper_boundary.sql`
  - Remplace les appels navigateur à `sinjira_age_band(uuid)` dans les policies catalogue par le helper self-only `sinjira_my_age_band()`.
  - Déplace l’implémentation privilégiée de `has_sinjira_product(text,uuid)` dans `sinjira_v25_internal`, avec wrapper public `SECURITY INVOKER`.
  - Conserve le ciblage UUID explicite uniquement pour `service_role`; un rôle navigateur reste borné à `auth.uid()`.
  - Réaffirme que les policies famille et achats d’extensions restent limitées à `adult/youth`; aucun droit produit ne rend le contenu ouvrable à 11–12 ans.
  - Revue prioritaire : ACL, `search_path`, ordre de remplacement des policies et absence d’oracle d’âge/droit par UUID arbitraire.

- [ ] `20260922033000_sinjira_v25_project_product_access.sql`
  - Ajoute `projects.product_slug` et généralise le droit produit aux jeux/autres projets sans créer de faux entitlement.
  - Un projet lié à un produit n’est lisible au membre standard qu’avec droit produit réel ou accès projet explicite; un achat ne révèle jamais un projet `draft`.
  - Les lignes complètes de projets publics payants restent fermées à `anon`; la fiche marketing publique peut rester séparée.
  - Les documents d’un projet payant répètent la frontière produit avant livraison; le helper 11–12 exclut tout projet payant même `approved_11_12`.
  - Le catalogue projet distingue `owner`, `family`, `product`, `access` et `free`, tout en minimisant les fiches 11–12 non ouvrables.
  - Revue prioritaire : interactions RLS projets/documents, états non-draft autorisés, Edge `get-document-url`, et preuve qu’un `project_access` technique ne contourne jamais la barrière d’âge.

### Notes de revue préparatoire du Lot E — non approbatives

Objectif fonctionnel : le créateur et les comptes familiaux explicitement autorisés voient toutes les créations SINJIRA dans leur compte, alors qu'un membre standard voit seulement le gratuit/public et ce qu'il a réellement acheté ou reçu comme droit.

Points à confirmer humainement avant toute approbation :
- le mécanisme de provisionnement production doit être exécuté séparément sous `service_role`, après déploiement de la migration, sans inscrire les adresses familiales dans Git;
- la commande dédiée `scripts/provision_creator_family_catalog.py` lit les comptes depuis `SINJIRA_CREATOR_FAMILY_EMAILS`, utilise `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY`, appelle uniquement le RPC serveur de provisionnement et n'affiche jamais les courriels dans ses sorties;
- la commande possède un `--self-test` exécuté par la CI; elle ne doit jamais être appelée automatiquement par un workflow PR ni avec des secrets production exposés;
- les UUID familiaux doivent être ceux des comptes voulus et aucun autre compte;
- la visibilité 11–12 doit rester strictement « catalogue », avec ouverture uniquement du contenu explicitement `approved_11_12`;
- aucune ligne de commande, entitlement ou `project_access` ne doit être créée pour simuler la propriété familiale;
- les comptes ordinaires doivent continuer à échouer sur les brouillons, produits internes, extensions privées et projets restreints sans droit;
- un produit commandé ne doit devenir ouvrable que lorsque la commande est réellement `paid`; une simple commande en attente ne suffit jamais.

Aucune case du Lot E n'est cochée : cette section documente une **préparation technique de revue**, pas une approbation.

## Lot F — Correctifs Junior forward-only récents (2)

- [ ] `20260924173000_sinjira_v25_junior_comment_author_visibility.sql`
  - Masque publications et commentaires lorsque leur auteur quitte la bande Junior ou perd son consentement courant, sans supprimer l’historique.
  - La preuve pgTAP couvre retrait puis réactivation explicite de l’auteur.

- [ ] `20260924191000_sinjira_v25_junior_hidden_post_comment_guard.sql`
  - Empêche la création d’un nouveau commentaire sur une publication actuellement masquée par une décision humaine de modération.
  - Redéfinit uniquement l’implémentation interne finale après la frontière RPC; aucun `SECURITY DEFINER` public n’est recréé.
  - La preuve pgTAP exige `JUNIOR_POST_UNAVAILABLE` pendant `hide_content`, puis conserve le commentaire normal après réversion humaine.

Aucune case du Lot F n’est cochée : ces migrations restent **NON REVUES / NON APPROUVÉES**.

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

- 43 / 43 migrations : **NON REVUES**
- 0 migration ajoutée au lot production par ce document
- 0 changement du ledger production
- 0 déploiement production
- PR #435 : répétition/intégration uniquement

Ce document sert de checklist de revue et de preuve de préparation; il ne doit jamais être interprété comme une autorisation de promotion.
