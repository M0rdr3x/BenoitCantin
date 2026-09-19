# SINJIRA™ V25 — Dossier de revue release Enfant 11–12 / Communauté Junior

Date de préparation : **2026-09-18 (America/Toronto)**  
PR de travail : **#435** — branche `a1/integration-rehearsal`

> Dossier de revue **non mutant**. Il ne constitue ni une approbation du lot de migrations, ni une autorisation de fusion, ni une autorisation de production.  
> Principe : **L’humain avant tout. Protéger sans surveiller.**

## 1. État fonctionnel vérifié

Le périmètre enfant/Junior couvre notamment :

- création de compte dès 11 ans;
- parent/tuteur adulte vérifié obligatoire pour 11–13 ans;
- bande `child` à 11–12 ans, puis transition automatique vers `youth` à 13 ans;
- révocation du tuteur fail-closed;
- Communauté Junior séparée et pseudonymisée;
- aucune messagerie privée générale pour 11–12 ans;
- filtrage serveur des liens, coordonnées, rencontres, secrets, sexualité et commerce;
- classement de contenu 11–12 fail-closed;
- capacités de compte self-only;
- cohérence web, mobile et Edge Functions avec les bandes V25.

La vague CI associée au dossier précédent a confirmé que les parcours Communauté Junior et inscription enfant 11 ans passent. Les validations sécurité/conformité restantes atteignent la frontière ledger/lot production avant d’échouer, ce qui est attendu tant que la revue humaine de production n’a pas eu lieu.

## 2. Correctif forward-only issu de la revue technique

La revue a identifié un cas multi-tuteur : un lien `guardian_links` ayant `status='verified'` mais un `revoked_at` non nul pouvait encore contribuer à l’activation Junior ou rester visible dans la liste du tuteur si un autre tuteur valide maintenait la bande `child`.

La migration forward-only suivante corrige ce cas sans réécrire la migration Junior historique :

`20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql`

Elle exige explicitement `g.revoked_at is null` dans :

- `private.sinjira_junior_community_enabled(uuid)`;
- `public.guardian_junior_community_children()`.

Une preuve pgTAP dédiée reproduit le scénario avec deux tuteurs : le second tuteur maintient légitimement la bande `child`, mais le consentement Junior du tuteur révoqué ne reste pas actif, le tuteur révoqué ne voit plus l’enfant dans sa liste et ne peut pas réactiver Junior.

Cette dixième migration reste **non revue production**.

## 3. Lot local futur actuellement non revu

Le snapshot de revue attend exactement **10 migrations locales futures non revues**.

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
| `20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql` | `f60c6e7a6717f7b5818ff0b9a1ba7b055aa418ff` |

Ces empreintes servent uniquement à la **revue humaine**. Elles ne doivent pas être ajoutées automatiquement à `supabase/production-reviewed-migration-batch.txt`.

## 4. Garde automatisé de snapshot

`scripts/validate_v25_release_review_snapshot.py` vérifie notamment :

- l’ensemble exact des migrations futures non revues;
- les Git blob SHA-1 de chaque migration;
- l’intégrité du lot revu production;
- l’intégrité du ledger production;
- la présence de ce dossier et de ses empreintes;
- le maintien des gardes documentaires humaines.

Le workflow `.github/workflows/sinjira-v25-release-review-snapshot.yml` est en lecture seule et ne possède aucune capacité de déploiement production.

Le correctif multi-tuteur possède en plus :

- `supabase/tests/junior_guardian_revocation_v25.test.sql`;
- `scripts/validate_junior_guardian_revocation_v25.py`;
- `.github/workflows/sinjira-junior-guardian-revocation-v25.yml`.

## 5. Frontières humaines obligatoires

À ce stade :

- **lot production revu : non**
- **prévol distant : non exécuté dans ce dossier**
- **application production : non autorisée / non exécutée**
- **PR #435 : doit rester draft**
- issue #135 : protection serveur de `main` encore à traiter séparément
- issue #240 : secrets GitHub Actions Supabase production encore à traiter séparément

Ne pas, pour rendre la CI verte :

- modifier artificiellement le ledger;
- marquer les migrations comme revues sans lecture humaine;
- supprimer une migration future;
- utiliser `db push --include-all`, `migration repair` ou une autre voie parallèle;
- fusionner ou déployer implicitement.

## 6. Séquence de revue humaine

1. Geler le HEAD exact de revue.
2. Relire les **10 migrations** dans l’ordre.
3. Vérifier RLS, privilèges, `SECURITY DEFINER`, `search_path`, rétention, suppression et transitions d’âge.
4. Comparer les empreintes ci-dessus.
5. Relire les preuves CI et pgTAP, en particulier la révocation multi-tuteur.
6. Vérifier séparément les bloqueurs #135 et #240.
7. Seulement après approbation humaine explicite, mettre à jour le lot revu.
8. Garder le prévol distant et l’application production comme étapes distinctes.
9. Ne réconcilier le ledger qu’après une preuve distante réelle.

**L’humain avant tout. Protéger sans surveiller.**
