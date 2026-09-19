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

Le pgTAP d'inscription enfant couvre explicitement `child_pending → child`, la réactivation du lien, la consommation unique du code, la révocation asymétrique et la transition de majorité; il compte désormais **62 assertions**.

Cette onzième migration reste **non revue production**.

### Révocation durable du consentement Junior

Une seconde revue de la chaîne de révocation a identifié qu'un ancien consentement `junior_community_guardian_consents` pouvait rester avec `revoked_at=null` lorsque le lien `guardian_links` était révoqué. Le garde d'accès empêchait bien Junior pendant la révocation, mais une réactivation ultérieure du lien pouvait alors ressusciter silencieusement cet ancien consentement.

La migration forward-only suivante ferme ce scénario :

`20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql`

Un trigger sur `guardian_links` révoque désormais durablement le consentement Junior associé lors d'une révocation **ou suppression** du lien. Après rétablissement de la supervision, Junior reste fermé jusqu'à une **nouvelle activation explicite** du parent/tuteur.

Le pgTAP de révocation Junior passe désormais à **25 assertions** et prouve la chaîne complète : révocation du lien, révocation du consentement, passage `child_pending`, nouveau code, retour à `child`, Junior toujours fermé, puis réactivation explicite seulement.

Cette douzième migration reste **non revue production**.

### AAL2 obligatoire pour émettre un code parental

La génération d’un code parental peut créer ou rétablir un lien de supervision d’un mineur. La revue a donc durci ce geste sensible indépendamment du réglage MFA global.

La migration forward-only suivante impose une session adulte **AAL2** :

`20260919023000_sinjira_v25_guardian_invite_aal2.sql`

Elle refuse explicitement AAL1 avec `MFA_AAL2_REQUIRED`, conserve les gardes MFA historiques additionnelles lorsqu’elles sont activées, invalide les anciens codes non consommés du même tuteur et maintient les ACL bornées à `authenticated`.

L’interface Relations vérifie le niveau d’assurance avant l’appel RPC. Si un facteur existe mais que la session est AAL1, elle utilise le parcours `/compte/mfa.html` puis revient vers Relations. Si aucun second facteur n’est configuré, elle renvoie vers le Centre de sécurité.

Le pgTAP enfant contient maintenant **62 assertions** au total; il prouve notamment le refus AAL1 à l’émission, la réussite AAL2, le format du code, la minimisation du secret et la fermeture de la relecture sous AAL1. Deux délimiteurs SQL `$$` endommagés dans la preuve précédente ont également été réparés et sont désormais verrouillés par le validateur statique.

Cette treizième migration reste **non revue production**.

### Minimisation du code parental après consommation

Le code parental est transmis à Supabase Auth comme métadonnée temporaire afin que le trigger d'inscription puisse le valider et le consommer. Comme le trigger canonique est `AFTER INSERT`, ce secret à usage unique restait auparavant dans `auth.users.raw_user_meta_data` après une inscription réussie.

La migration forward-only suivante supprime cette rétention inutile :

`20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql`

Un trigger `zz_sinjira_strip_guardian_signup_secret`, exécuté après `on_auth_user_created_sinjira`, retire `guardian_code` des métadonnées Auth uniquement après l'insertion réussie. Le code a donc le cycle minimal attendu : **transmis → validé → consommé → supprimé**.

Le pgTAP vérifie maintenant que le lien tuteur et la consommation du code existent toujours, tout en prouvant que `guardian_code` n'est plus conservé sur le compte enfant.

Cette quatorzième migration reste **non revue production**.

### Relecture des codes parentaux également protégée par AAL2

La revue du parcours a identifié qu'après avoir imposé AAL2 à l'émission, la table `guardian_signup_invites` restait lisible par le tuteur avec une simple session authentifiée grâce à l'ancienne policy RLS. Une session AAL1 pouvait donc relire un code déjà émis.

La migration forward-only suivante ferme cette asymétrie :

`20260919033000_sinjira_v25_guardian_invite_read_aal2.sql`

La policy historique de lecture est retirée et remplacée par une policy **self-only + AAL2**. Le navigateur vérifie aussi le niveau d'assurance avant toute requête vers `guardian_signup_invites`; sous AAL1, les codes sont explicitement masqués et l'interface propose la vérification MFA ou la configuration du second facteur.

Le pgTAP ajoute deux preuves exécutées avec le rôle API `authenticated` : **0 ligne visible en AAL1**, puis **le propre code visible en AAL2**.

Cette quinzième migration reste **non revue production**.

### AAL2 pour activer la Communauté Junior

L'activation de la Communauté Junior augmente les capacités sociales d'un compte 11–12 ans. La revue a constaté qu'un tuteur authentifié pouvait encore l'activer sans step-up.

La migration forward-only suivante impose AAL2 uniquement à l'activation :

`20260919040000_sinjira_v25_junior_enable_aal2.sql`

Le serveur exige désormais une session parent/tuteur **AAL2** lorsque `p_enabled=true`. La désactivation reste volontairement disponible en AAL1 afin de conserver une voie fail-safe immédiate de retrait d'accès.

L'interface Relations applique la même règle et réutilise le parcours MFA existant. Le pgTAP Junior compte maintenant **25 assertions** : activation refusée en AAL1, activation permise en AAL2, révocation durable, réactivation explicite et désactivation fail-safe en AAL1. La preuve a aussi réparé un délimiteur SQL `$$` cassé et le workflow corrige son nettoyage local `command -v supabase`.

Cette seizième migration reste **non revue production**.

### Révocation de supervision : AAL2 tuteur, sortie immédiate du mineur

Le RPC historique `revoke_guardian_link(uuid)` autorisait les deux parties à couper le lien sans step-up. Exiger AAL2 pour tout le monde aurait toutefois retiré au mineur une voie de protection.

La migration forward-only suivante applique donc une règle asymétrique :

`20260919043000_sinjira_v25_guardian_revoke_aal2.sql`

- lorsqu'un **tuteur** initie la révocation, sa session doit être AAL2;
- lorsque le **mineur lié** quitte son propre lien, aucune MFA n'est exigée;
- un lien déjà révoqué reste idempotent;
- l'interface distingue les deux parcours et ne présente plus un lien avec `revoked_at` comme actif.

Le pgTAP enfant compte maintenant **62 assertions** et prouve notamment : tuteur AAL1 refusé, tuteur AAL2 accepté, puis enfant AAL1 capable de quitter immédiatement son propre lien avec retour fail-closed vers `child_pending`.

Cette dix-septième migration reste **non revue production**.

### Fin de visibilité de supervision à 18 ans

Le calcul des capacités cessait déjà la supervision à 18 ans, mais la policy historique `guardian_links` permettait encore à l'ancien tuteur de lire le lien après la majorité. Le pouvoir était donc coupé, mais la visibilité relationnelle persistait.

La migration forward-only suivante ferme cette rétention de visibilité :

`20260919050000_sinjira_v25_guardian_majority_visibility.sql`

La nouvelle policy utilise un helper self-only par ID de lien. La personne concernée conserve l'accès à son propre historique, tandis que l'ancien tuteur ne peut lire le lien que tant que le compte est dans une bande sous 18 ans (`child`, `child_pending`, `youth`, `youth_pending`). Un tiers obtient toujours `false` et ne peut pas sonder un lien arbitraire.

Le pgTAP enfant compte désormais **62 assertions** et prouve la transition exacte vers `adult` à 18 ans, **0 lien visible pour l'ancien tuteur**, conservation de l'historique pour la personne devenue adulte, fermeture du helper aux tiers et disparition des invitations consommées côté ancien tuteur.

Cette dix-huitième migration reste **non revue production**.

### Fin de visibilité des invitations consommées à la majorité

La revue de cycle de vie a identifié une seconde trace relationnelle : même après disparition de `guardian_links` côté ancien tuteur, une invitation parentale déjà consommée restait lisible sous AAL2 dans `guardian_signup_invites` et conservait `minor_user_id`.

La migration forward-only suivante aligne cette table avec la fin de supervision :

`20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql`

Les codes non consommés du tuteur restent lisibles sous AAL2. En revanche, une invitation consommée n'est plus visible que si le `guardian_link` correspondant est lui-même encore visible. Le passage à `adult` masque donc automatiquement cette trace au tuteur sans supprimer l'historique interne.

Le pgTAP enfant compte désormais **62 assertions** et prouve qu'à 18 ans l'ancien tuteur voit **0 invitation consommée** liée au compte devenu adulte.

Cette dix-neuvième migration reste **non revue production**.

### Métadonnées de contacts jeunesse : consentement + AAL2

Le RPC historique `get_guardian_youth_contacts(uuid)` respectait la supervision active et se fermait à la majorité, mais il n'appliquait pas le drapeau `can_view_contact_metadata` du lien. Il permettait donc à un tuteur vérifié de consulter pseudos, réseaux et dates de dernier contact même lorsque cette permission était désactivée.

La migration forward-only suivante ferme cette incohérence :

`20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql`

Le RPC exige maintenant simultanément : supervision active, `can_view_contact_metadata=true` et session tuteur **AAL2**. Il continue à ne renvoyer aucun contenu de message.

Le pgTAP enfant compte désormais **62 assertions** et prouve les trois états : refus sans consentement explicite, refus en AAL1 malgré le consentement, puis accès aux seules métadonnées sous consentement + AAL2.

Cette vingtième migration reste **non revue production**.

### Métadonnées de contacts : privacy-by-default et choix du compte jeunesse

La revue suivante a confirmé que `can_view_contact_metadata` était historiquement initialisé à `true` lors de la création ou réactivation d'un lien. Il ne représentait donc pas un consentement explicite du compte jeunesse.

La migration forward-only :

`20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql`

passe la permission par défaut à `false`, neutralise les permissions actives héritées qui avaient été accordées implicitement et remet toute création/réactivation de lien à `false`. Le nouveau RPC `set_my_guardian_contact_metadata(uuid,boolean)` est self-only : seul le compte `child` ou `youth` concerné peut autoriser ou retirer cette visibilité.

L'écran Relations expose ce choix uniquement au compte enfant/jeunesse. Le parent voit l'état mais ne peut pas l'activer lui-même. Même après opt-in, `get_guardian_youth_contacts` exige toujours AAL2 et ne révèle jamais le contenu des messages.

Le pgTAP enfant compte désormais **62 assertions** et prouve le cycle complet : désactivé par défaut, refus parent, opt-in du jeune, step-up AAL2 du parent, retrait du jeune, puis retrait d'accès immédiat.

Cette vingt-et-unième migration reste **non revue production**.

### Minimisation du résumé parental de contacts

Même avec opt-in explicite du jeune et AAL2 du tuteur, le RPC historique renvoyait encore l'UUID interne du contact, son `display_name` et l'heure exacte de dernière interaction. Ces éléments dépassaient l'objectif de protection.

La migration forward-only :

`20260919070000_sinjira_v25_guardian_contacts_minimization.sql`

réduit la réponse à trois éléments : **pseudo**, **réseaux concernés** et **date UTC du dernier contact à la journée**. L'UUID, le `display_name`, le timestamp précis et le contenu des messages ne sont pas exposés.

Le pgTAP enfant compte désormais **62 assertions** et utilise un vrai contact jeunesse de preuve pour verrouiller la forme JSON minimisée.

Cette vingt-deuxième migration reste **non revue production**.

### Résumé parental Junior : AAL2 et date seulement

Le résumé `junior_guardian_summary(uuid)` ne révélait aucun contenu, mais restait consultable en AAL1 et exposait l'heure exacte de dernière activité. Cette précision n'est pas nécessaire à l'objectif de protection.

La migration forward-only :

`20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql`

exige désormais AAL2 pour lire le résumé et remplace `last_activity_at` par `last_activity_date` en UTC. Les comptes de publications/commentaires restent disponibles, tandis que le contenu et les messages privés restent explicitement invisibles au tuteur. La désactivation de Junior demeure disponible en AAL1 comme voie fail-safe.

Le pgTAP Junior compte désormais **25 assertions** et prouve le refus AAL1, la lecture AAL2, l'absence du timestamp précis et la conservation du seul compte d'activité utile.

Cette vingt-troisième migration reste **non revue production**.

### Cloisonnement identité Compte / Personnage dans le résumé parental

La revue de minimisation a identifié un risque de recoupement : les messages du réseau Personnage étaient regroupés par `user_id`, puis associés au pseudo du compte réel. Un tuteur autorisé pouvait ainsi relier un personnage public au compte qui le contrôle.

La migration forward-only :

`20260919080000_sinjira_v25_guardian_character_identity_isolation.sql`

sépare désormais les deux espaces. Le réseau **Compte** utilise uniquement le pseudo public du compte; le réseau **Personnage** utilise uniquement le `public_name` du personnage résolu par `character_id`. Les deux identités restent dans des entrées distinctes et aucun identifiant interne n'est retourné.

Le pgTAP enfant compte désormais **62 assertions** et prouve explicitement qu'un personnage nommé `Avatar Secret` n'est jamais remplacé par le pseudo réel `Contact Jeunesse`, même lorsque les deux appartiennent au même compte de test.

Cette vingt-quatrième migration reste **non revue production**.

### Alias Junior privé vis-à-vis du tuteur

La liste parentale `guardian_junior_community_children()` renvoyait encore `junior_alias`, alors que cet alias sert précisément à pseudonymiser l'enfant dans la Communauté Junior. Le tuteur n'en a pas besoin pour activer/désactiver Junior ni pour consulter le résumé de sécurité.

La migration forward-only :

`20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql`

retire donc l'alias Junior de la réponse parentale. L'interface Relations affiche seulement le libellé du compte enfant et précise que l'alias Junior n'est pas montré au tuteur.

Le pgTAP Junior compte désormais **25 assertions** et prouve qu'aucun objet de la liste tuteur ne contient `junior_alias`.

Cette vingt-cinquième migration reste **non revue production**.

### Refonte compte, acquisitions et catalogue créateur

La revue visuelle du compte a identifié plusieurs incohérences : navigation trop chargée, page Achats sans historique réel, bibliothèque mélangeant jeux et projets, page Littérature centrée sur un seul roman, et ancien client commentaires encore branché sur `novel_comments.contains_spoilers` alors que le modèle canonique utilise `sinjira_novel_comments.spoiler`.

La migration forward-only :

`20260919090000_sinjira_v25_account_content_hub.sql`

ajoute trois garanties de lecture sans créer de faux achats : un membre peut relire un produit inactif s'il est lié à son propre entitlement ou à sa propre commande; le compte créateur peut lire les romans brouillons et produits internes; les autres membres ne voient pas ces éléments privés. Le Livre II `Le Sang du Sauveur` est aussi convergé vers `sinjira_novels` afin que le catalogue canonique reflète les romans déjà annoncés sur le site.

La refonte front-end regroupe la navigation du compte en familles, sépare Bibliothèque en **Jeux / Romans / Autres créations**, ajoute un historique réel **Achats / Droits / Créations**, rend pseudo et courriel modifiables par le propriétaire du compte, convertit les commentaires vers les tables/RPC `sinjira_*`, et transforme Littérature en catalogue multi-romans piloté par les droits du compte.

Le pgTAP `account_content_hub_v25.test.sql` contient **9 assertions** dédiées aux frontières membre/créateur.

Cette vingt-sixième migration reste **non revue production**.

### Catalogue générique des romans privés

La première refonte révélait encore une limitation historique : la lecture intégrale privée était codée spécifiquement pour le Livre I. Cela ne pouvait pas supporter proprement les futurs romans ni distinguer un catalogue créateur complet d'un manuscrit réellement chargé dans le coffre privé.

La migration forward-only :

`20260919093000_sinjira_v25_private_novel_catalog.sql`

introduit un registre privé `private.sinjira_private_novel_assets` inaccessible au navigateur, un RPC self-only `sinjira_my_novel_catalog()` et un RPC de livraison strictement `service_role`. Le catalogue navigateur ne reçoit jamais le bucket ni le chemin de stockage.

Le nouveau service `get-private-novel-url` utilise un `novel_slug`, vérifie l'état d'âge du compte, puis le rôle créateur ou un entitlement réel avant de signer temporairement un actif privé. Le Livre I est enregistré dans ce registre mais reste **désactivé par défaut** tant qu'un véritable actif privé n'a pas été configuré et revu. Le lecteur intégral devient générique via `?novel=<slug>`.

Pour le compte créateur, la distinction est maintenant explicite :
- **catalogue complet** : l'œuvre et son état sont visibles;
- **intégrale privée** : le bouton de lecture apparaît seulement lorsqu'un actif privé est configuré;
- un manuscrit non chargé n'est jamais présenté comme disponible.

À l'état constaté lors de cette revue, aucun actif privé identifiable du Livre II n'est présent dans le stockage actif. La refonte ne fabrique donc aucun fichier ni accès fictif pour `Le Sang du Sauveur`.

Le pgTAP `private_novel_catalog_v25.test.sql` contient **12 assertions** sur les frontières membre/créateur, la non-divulgation des chemins de stockage et le fail-closed des comptes non vérifiés.

Cette vingt-septième migration reste **non revue production**.

## 3. Lot local futur actuellement non revu

Le snapshot de revue attend exactement **27 migrations locales futures non revues**.

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
| `20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql` | `f08102d4bc2485bc229e21076f361bf31552c928` |
| `20260919033000_sinjira_v25_guardian_invite_read_aal2.sql` | `9b56b0e422f91fbb93939e03709d9afbcce0c7cf` |
| `20260919040000_sinjira_v25_junior_enable_aal2.sql` | `df5475777abd5bb8fff26510a727d3d04cffce53` |
| `20260919043000_sinjira_v25_guardian_revoke_aal2.sql` | `7dada317202bdd1add1d4dc5113e3aca682459e4` |
| `20260919050000_sinjira_v25_guardian_majority_visibility.sql` | `d7a65f65e1a870620809f1a2e669ef031d6f6d8a` |
| `20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql` | `ac18154c958b707d94ddc557b1af6b2af01ba62f` |
| `20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql` | `f889da5d2c78eade2da8ef5a557cc5d77ae8e1e1` |
| `20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql` | `2d91c64a90f5c8bca506577ef359078fdf558fad` |
| `20260919070000_sinjira_v25_guardian_contacts_minimization.sql` | `300b934766f3f1e8298f459ab3e8897df63b4959` |
| `20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql` | `07b1ea063e57d3dd4a31e689fac6f44fd1ca6d18` |
| `20260919080000_sinjira_v25_guardian_character_identity_isolation.sql` | `7c169564095bb440bde8a2a106c4e00aa2f307e4` |
| `20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql` | `8e0fd367bd0c30ed77f947ae0583408b370121a1` |
| `20260919090000_sinjira_v25_account_content_hub.sql` | `29358d27f8f505897b924062e208b8d5c740f8c5` |
| `20260919093000_sinjira_v25_private_novel_catalog.sql` | `be721fa72387de258fb488293f973febd9f9c8e7` |

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
2. Relire les **27 migrations** dans l’ordre.
3. Vérifier RLS, privilèges, `SECURITY DEFINER`, `search_path`, rétention, suppression et transitions d’âge.
4. Comparer les empreintes ci-dessus.
5. Relire les preuves CI et pgTAP, en particulier la révocation multi-tuteur.
6. Vérifier séparément les bloqueurs #135 et #240.
7. Seulement après approbation humaine explicite, mettre à jour le lot revu.
8. Garder le prévol distant et l’application production comme étapes distinctes.
9. Ne réconcilier le ledger qu’après une preuve distante réelle.

**L’humain avant tout. Protéger sans surveiller.**
