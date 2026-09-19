# SINJIRA™ V25 — Dossier de revue release Enfant 11–12 / Communauté Junior

Date de préparation : **2026-09-18 (America/Toronto)**  
PR de travail : **#435** — branche `a1/integration-rehearsal`

> Dossier de revue **non mutant**. Il ne constitue ni une approbation du lot de migrations, ni une autorisation de fusion, ni une autorisation de production.  
> Principe : **L’humain avant tout. Protéger sans surveiller.**

## 1. État fonctionnel vérifié

Le périmètre enfant/Junior couvre notamment :

- création de compte dès 11 ans;
- parent/tuteur adulte vérifié obligatoire pour 11–13 ans;
- génération d’un code parental réservée à une session adulte AAL2;
- bande `child` à 11–12 ans, puis transition automatique vers `youth` à 13 ans;
- révocation du tuteur fail-closed;
- Communauté Junior séparée et pseudonymisée;
- aucune messagerie privée générale pour 11–12 ans;
- filtrage serveur des liens, coordonnées, rencontres, secrets, sexualité et commerce;
- classement de contenu 11–12 fail-closed;
- décisions de classement 11–12 réservées à l’admin avec second facteur configuré et session `aal2` active;
- capacités de compte self-only;
- cohérence web, mobile et Edge Functions avec les bandes V25.

La vague CI associée au dossier précédent a confirmé que les parcours Communauté Junior et inscription enfant 11 ans passent. Les validations sécurité/conformité restantes atteignent la frontière ledger/lot production avant d’échouer, ce qui est attendu tant que la revue humaine de production n’a pas eu lieu.

## 2. Correctifs forward-only issus de la revue technique

La revue a identifié un cas multi-tuteur : un lien `guardian_links` ayant `status='verified'` mais un `revoked_at` non nul pouvait encore contribuer à l’activation Junior ou rester visible dans la liste du tuteur si un autre tuteur valide maintenait la bande `child`.

La migration forward-only suivante corrige ce cas sans réécrire la migration Junior historique :

`20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql`

Elle exige explicitement `g.revoked_at is null` dans :

- `private.sinjira_junior_community_enabled(uuid)`;
- `public.guardian_junior_community_children()`.

Une preuve pgTAP dédiée reproduit le scénario avec deux tuteurs : le second tuteur maintient légitimement la bande `child`, mais le consentement Junior du tuteur révoqué ne reste pas actif, le tuteur révoqué ne voit plus l’enfant dans sa liste et ne peut pas réactiver Junior.

Cette dixième migration reste **non revue production**.

### Rétablissement de supervision 11–12 après révocation

La revue du parcours Relations a identifié une incohérence serveur/client : l'interface reconnaissait `child_pending` et proposait un nouveau code parental, alors que `public.redeem_guardian_signup_invite(text)` refusait cette bande et n'acceptait que le contrat jeunesse historique.

La migration forward-only suivante aligne le serveur avec la bande V25 :

`20260919013000_sinjira_v25_child_pending_guardian_redeem.sql`

Elle autorise un compte `child_pending` à consommer un **nouveau code parental adulte valide et à usage unique**. Le trigger canonique `sync_guardian_signup_invite_link` réactive/crée alors le lien `guardian_links` en `verified`, remet `revoked_at` à `null` et la classification repasse immédiatement à `child`. Un compte déjà supervisé ne reçoit pas un nouveau droit implicite.

Le pgTAP d'inscription enfant passe de **26 à 34 assertions** et couvre explicitement `child_pending → child`, la réactivation du lien et la consommation unique du nouveau code.

Cette onzième migration reste **non revue production**.

### Révocation durable du consentement Junior

Une seconde revue de la chaîne de révocation a identifié qu'un ancien consentement `junior_community_guardian_consents` pouvait rester avec `revoked_at=null` lorsque le lien `guardian_links` était révoqué. Le garde d'accès empêchait bien Junior pendant la révocation, mais une réactivation ultérieure du lien pouvait alors ressusciter silencieusement cet ancien consentement.

La migration forward-only suivante ferme ce scénario :

`20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql`

Un trigger sur `guardian_links` révoque désormais durablement le consentement Junior associé lors d'une révocation **ou suppression** du lien. Après rétablissement de la supervision, Junior reste fermé jusqu'à une **nouvelle activation explicite** du parent/tuteur.

Le pgTAP de révocation Junior passe de **9 à 17 assertions** et prouve la chaîne complète : révocation du lien, révocation du consentement, passage `child_pending`, nouveau code, retour à `child`, Junior toujours fermé, puis réactivation explicite seulement.

Cette douzième migration reste **non revue production**.

### AAL2 obligatoire pour émettre un code parental

La génération d’un code parental peut créer ou rétablir un lien de supervision d’un mineur. La revue a donc durci ce geste sensible indépendamment du réglage MFA global.

La migration forward-only suivante impose une session adulte **AAL2** :

`20260919023000_sinjira_v25_guardian_invite_aal2.sql`

Elle refuse explicitement AAL1 avec `MFA_AAL2_REQUIRED`, conserve les gardes MFA historiques additionnelles lorsqu’elles sont activées, invalide les anciens codes non consommés du même tuteur et maintient les ACL bornées à `authenticated`.

L’interface Relations vérifie le niveau d’assurance avant l’appel RPC. Si un facteur existe mais que la session est AAL1, elle utilise le parcours `/compte/mfa.html` puis revient vers Relations. Si aucun second facteur n’est configuré, elle renvoie vers le Centre de sécurité.

Le pgTAP enfant contient maintenant **34 assertions** et prouve le refus AAL1, la réussite AAL2 et le format du code généré. Deux délimiteurs SQL `$$` endommagés dans la preuve précédente ont également été réparés et sont désormais verrouillés par le validateur statique.

Cette treizième migration reste **non revue production**.

## 3. Lot local futur actuellement non revu

Le snapshot de revue attend exactement **13 migrations locales futures non revues**.

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
| `20260919013000_sinjira_v25_child_pending_guardian_redeem.sql` | `983ac4b48f25f29c0c62becb692b9203cdec80a1` |
| `20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql` | `e14c41364246929054282bccb0e4abc5641b8643` |
| `20260919023000_sinjira_v25_guardian_invite_aal2.sql` | `5700bfaa2b5a95d84d37ad475524960bdb78fc9b` |

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
2. Relire les **13 migrations** dans l’ordre.
3. Vérifier RLS, privilèges, `SECURITY DEFINER`, `search_path`, rétention, suppression et transitions d’âge.
4. Comparer les empreintes ci-dessus.
5. Relire les preuves CI et pgTAP, en particulier la révocation multi-tuteur.
6. Vérifier séparément les bloqueurs #135 et #240.
7. Seulement après approbation humaine explicite, mettre à jour le lot revu.
8. Garder le prévol distant et l’application production comme étapes distinctes.
9. Ne réconcilier le ledger qu’après une preuve distante réelle.

**L’humain avant tout. Protéger sans surveiller.**
