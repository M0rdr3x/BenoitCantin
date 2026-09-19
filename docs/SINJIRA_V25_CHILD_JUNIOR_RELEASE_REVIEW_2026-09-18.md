# SINJIRA™ V25 — Dossier de revue release Enfant 11–12 / Communauté Junior

Date de préparation : **2026-09-18 (America/Toronto)**  
PR de travail : **#435** — branche `a1/integration-rehearsal`  
HEAD fonctionnel de référence : `8f3171215f9a2b9888fda6d8bd9d54c96330b89a`

> Ce document est un **dossier de revue non mutant**. Il ne constitue ni une approbation du lot de migrations, ni une autorisation de fusion, ni une autorisation d'écriture en production.  
> Principe : **L’humain avant tout. Protéger sans surveiller.**

## 1. État fonctionnel de référence

Sur le HEAD de référence, les Actions GitHub sont entièrement terminées :

- **100 workflows observés**;
- **50 succès**;
- **38 échecs**;
- **12 skipped**;
- **0 pending**.

Les 38 échecs ont été classés par leur première étape échouée. Ils se terminent sur la frontière de gouvernance **ledger / lot de migrations production revu**, ou sur un prévol qui atteint cette même frontière après avoir validé le dépôt. Aucun échec applicatif/fonctionnel restant n'a été identifié sur ce HEAD.

Preuves importantes :

- Communauté Junior #115 : local + reconstruction complète + pgTAP + navigateur **verts**;
- test compatibilité protection mineurs V25 : **8 assertions vertes**;
- inscription enfant 11 ans #147 : **success**;
- navigateur inscription 11 ans #127 : **success**;
- Validation sécurité mineurs V24.4.82 #599 : contrat sécurité **vert**, puis ledger rouge attendu;
- Validation conformité globale V24.4.83 #606 : convergence V25 **verte**, puis ledger rouge attendu;
- prévol Supabase production #1019 : dépôt/runtime/Edge/social-RLS **verts**, puis lot production non revu;
- garde Edge Functions publiques #397 : **success**;
- Tests navigateur SINJIRA #1681 : **success**;
- A1 convergence #175 et A1 Compte/Histoire de vie #191 : **success**;
- Mon IA #341 et production-readiness Mon IA #188 : **success**.

## 2. Correctif de défense en profondeur V25

La migration suivante est volontairement **forward-only** et ne réécrit pas la migration historique V24.4.82 :

`20260918023000_sinjira_v25_minor_content_policy_compat.sql`

Elle redéfinit `private.sinjira_content_policy_code(...)` afin que la garde renforcée de messagerie mineur soit fail-closed avec les bandes V25.

Les bandes suivantes restent protégées : `under11`, `child`, `child_pending`, `youth`, `youth_pending`, `unverified` et toute future bande non reconnue. Seules les bandes explicitement `adult` et `memorial` sortent de cette garde renforcée.

Les 8 assertions dédiées prouvent notamment :

- `child` bloque le contact hors plateforme;
- un destinataire `child` suffit à activer la garde;
- `child` bloque la sollicitation sexuelle;
- la révocation du tuteur produit `child_pending`;
- `child_pending` reste protégé contre la sollicitation financière;
- une bande non vérifiée échoue fermée;
- un adulte sans destinataire mineur n'est pas soumis à cette garde renforcée spécifique.

## 3. Lot local futur actuellement non revu

Le prévol et le garde historique détectent exactement **9 migrations locales futures non revues**.

### Mode Voyage

| Migration | Git blob SHA-1 |
|---|---|
| `20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql` | `7285d1e30ea288004d17c1dbfbf9f01662b36bb7` |
| `20260913230000_sinjira_v25_travel_mode_retention_purge.sql` | `41b8dc3d1b1e09c018e588755edb053e63e9904a` |
| `20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql` | `b08af7275d0d89b122505da413458fa9a24d2603` |

### Enfant 11–12 / Junior

| Migration | Git blob SHA-1 |
|---|---|
| `20260916210000_sinjira_v25_child_guardian_signup.sql` | `e4e16d20af50d9cd0c9672fda9b79cc3501aaedc` |
| `20260917223000_sinjira_v25_junior_community.sql` | `c56785a7b9f6e3ec8933d9782af5110a2ca22f4e` |
| `20260918010000_sinjira_v25_child_sensitive_boundary.sql` | `2c8758e1ada9993645cac661f5d7676a93a31cb1` |
| `20260918013000_sinjira_v25_child_content_rating.sql` | `5cc1d572f97f080bcc43ae3d20e85b441e62b9e0` |
| `20260918020000_sinjira_v25_account_capabilities.sql` | `0a16bfcc49e51ee2b96cb98742442ae3d00e5c76` |
| `20260918023000_sinjira_v25_minor_content_policy_compat.sql` | `c0556e3baa218f9529f185010455984a0bc1cd03` |

Ces empreintes sont fournies pour la **revue humaine**. Elles ne sont pas ajoutées automatiquement à `supabase/production-reviewed-migration-batch.txt`.

## 4. Périmètre enfant/Junior à maintenir coordonné

Une future release enfant/Junior ne doit pas être réduite à une seule page frontend.

Le périmètre coordonné comprend au minimum :

- création de compte supervisé dès 11 ans;
- code parental/tuteur obligatoire de 11 à 13 ans;
- bande `child` à 11–12 ans et transition automatique à `youth` à 13 ans;
- révocation du tuteur fail-closed;
- Communauté Junior séparée;
- absence de messages privés pour 11–12;
- alias Junior pseudonyme;
- filtrage des liens/contacts/rencontres/secrets/sexualité/commerce;
- classement contenu 11–12;
- capacités self-only du compte;
- matrice de routes fail-closed;
- frontière mobile enfant;
- accès Bibliothèque borné au contenu approuvé 11–12;
- protections Playtest et autres surfaces sensibles;
- compatibilité V25 du classifieur de contenu;
- Edge Functions qui utilisent `service_role` et doivent appliquer les mêmes bandes fail-closed.

Sources Edge actuellement concernées par cette cohérence :

- `get-document-url`;
- `personal-ai`;
- `redeem-license-code`;
- `get-private-book-url`;
- `get-private-book-reading-url`.

Aucune de ces fonctions ne doit être présentée comme déployée à partir de cette PR tant qu'un déploiement production distinct n'a pas été explicitement autorisé et vérifié.

## 5. Séquence de revue humaine recommandée

Cette séquence prépare une décision; elle ne prend pas la décision à la place du propriétaire.

1. **Geler un SHA de revue.** Relever le HEAD exact et refuser toute approbation basée sur un contenu qui a changé après lecture.
2. **Relire les 9 migrations dans leur ordre.** Vérifier portée, RLS, privilèges, fonctions SECURITY DEFINER, `search_path`, triggers, rétention, suppression et transitions d'âge.
3. **Comparer les blob SHA.** Toute différence avec les empreintes ci-dessus invalide cette revue et exige une nouvelle lecture.
4. **Décider du périmètre production.** Le builder canonique exige la cohérence entre toutes les migrations futures locales et le lot revu. Ne pas faire disparaître artificiellement les 3 migrations Mode Voyage pour faire passer un lot enfant.
5. **Relire les tests et preuves CI.** En particulier les parcours exacts 11 ans, révocation tuteur, Junior, contenu 11–12, capacités self-only, protection mineurs V25, routes/mobile, Edge et AAL2.
6. **Vérifier le blocage opérationnel #240.** L'issue est toujours ouverte : les secrets GitHub Actions de connexion production doivent être configurés hors dépôt par le propriétaire. Ne jamais copier leur valeur dans GitHub, un commit, un log ou ce document.
7. **Après approbation humaine explicite seulement**, mettre à jour le lot de migrations revu avec les empreintes exactes et repasser le prévol local.
8. **Ne pas confondre revue et application.** Un lot revu n'autorise pas une écriture distante.
9. **Prévol distant séparé**, lancé manuellement avec `apply=false`, seulement lorsque les secrets et la gouvernance sont prêts.
10. **Application réelle séparée**, depuis `main`, uniquement avec `workflow_dispatch`, `apply=true`, confirmation exacte `APPLY-SUPABASE-PRODUCTION`, prévols verts et frontière GitHub Environment `production`.
11. **Vérifications post-déploiement.** Rejouer les parcours enfant/Junior de test, contrôler les bandes d'âge, la révocation, les capacités, les routes, les accès documentaires et les Edge concernées.
12. **Réconcilier le ledger après preuve distante réelle.** Utiliser les versions réellement enregistrées; ne jamais présumer qu'un timestamp local est identique au timestamp distant.

## 6. Critères de blocage immédiat

Arrêter la préparation de release si l'un des points suivants survient :

- modification d'une migration après sa revue sans nouvelle empreinte;
- apparition d'un échec fonctionnel avant l'étape ledger;
- accès navigateur à `sinjira_age_band(uuid)`;
- accès enfant à une surface générale sociale/messagerie/commerce non explicitement autorisée;
- `child_pending` ou `unverified` traité comme compte standard;
- possibilité de contourner la révocation tuteur avec `status='verified'` mais `revoked_at` non nul;
- contenu 11–12 `unreviewed` rendu lisible;
- Edge Function `service_role` qui ne reproduit pas les restrictions de bande;
- secrets exposés à un run de PR/push;
- tentative de `db push --include-all`, `migration repair`, `db reset --linked` ou autre voie parallèle;
- tentative de fusion/déploiement implicite parce que les tests locaux sont verts.

## 7. État de décision

À la date de ce dossier :

- **fonctionnel branche : validé par CI**;
- **lot production revu : non**;
- **prévol distant : non exécuté dans ce dossier**;
- **application production : non autorisée / non exécutée**;
- **issue opérationnelle #240 : ouverte**;
- **PR #435 : doit rester draft tant que le propriétaire n'a pas décidé de franchir la prochaine frontière humaine**.

Le prochain changement autorisable dans le dépôt est une **mise à jour intentionnelle du lot revu après revue humaine**, pas une modification automatique du ledger et pas un déploiement.
