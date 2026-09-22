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


### Preuves techniques consolidées au HEAD applicatif `6ace8163c5a68d496d77e635c6b29132876a5b45`

- inscription/supervision enfant : **67/67** assertions, plus **11/11** coffre privé enfant et un vrai parcours Auth HTTP à exactement 11 ans;
- Communauté Junior : **51/51** assertions;
- frontière serveur 11–12 : **13/13**;
- classement contenu 11–12 : **23/23**;
- capacités compte self-only : **25/25**;
- compatibilité protection mineurs : **8/8**;
- révocation Junior multi-tuteur : **25/25**, avec auto-test du garde **10/10**;
- Compte/catalogue : suite actuelle **49 assertions** accès membre/créateur et **23/23** absence d'oracle/classement 11–12;
- Profil privé : **22/22** historique et **11/11** enfant;
- romans privés : **13/13**, avec auto-test statique courant **9/9**;
- Mode Voyage : rétention **11/11** et visibilité client **28/28**, les workflows consentement/self-only/minimisation restant également verts;
- snapshot release : **38 migrations futures non revues**, empreintes intactes, reviewed batch et ledger inchangés.

La classification exhaustive des workflows rouges de ce HEAD montre que leurs étapes métier/sécurité passent avant de s'arrêter sur le **ledger production volontairement bloqué** par les 38 migrations non revues. Le prévol Supabase suit la même logique : ses tests de sécurité passent, puis la vérification du dépôt s'arrête sur ce ledger.

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

Elle autorise un compte `child_pending` à consommer un **nouveau code parental adulte valide et à usage unique**. Le trigger canonique `sync_guardian_signup_invite_link` réactive/crée alors le lien `guardian_links` en `verified`, remet `revoked_at` à `null` et la classification repasse immédiatement à `child`. Un compte déjà supervisé ne reçoit pas un nouveau droit implicite. La consommation est maintenant sérialisée par un verrou transactionnel sur `account_safety_profiles` avant le recalcul de la bande : deux codes distincts présentés en parallèle pour le même compte pending ne peuvent plus créer deux liens implicites.

Le pgTAP d'inscription enfant couvre explicitement `child_pending → child`, la réactivation du lien, la consommation unique du code, la révocation asymétrique et la transition de majorité; il compte désormais **67 assertions**.

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

Le pgTAP enfant contient maintenant **67 assertions** au total; il prouve notamment le refus AAL1 à l’émission, la réussite AAL2, le format du code, la minimisation du secret et la fermeture de la relecture sous AAL1. Deux délimiteurs SQL `$$` endommagés dans la preuve précédente ont également été réparés et sont désormais verrouillés par le validateur statique.

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

La policy historique de lecture est retirée et remplacée par une policy **self-only + AAL2**. Le navigateur vérifie aussi le niveau d'assurance avant toute requête vers `guardian_signup_invites`; sous AAL1, les codes sont explicitement masqués et l'interface propose la vérification MFA ou la configuration du second facteur. La même policy conserve désormais immédiatement la borne de majorité : un code non consommé reste lisible au tuteur sous AAL2, mais une invitation déjà consommée n’est plus lisible dès que le `guardian_link` correspondant cesse d’être visible, évitant une réouverture transitoire avant `20260919053000`.

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

Le pgTAP enfant compte maintenant **67 assertions** et prouve notamment : tuteur AAL1 refusé, tuteur AAL2 accepté, puis enfant AAL1 capable de quitter immédiatement son propre lien avec retour fail-closed vers `child_pending`.

Cette dix-septième migration reste **non revue production**.

### Fin de visibilité de supervision à 18 ans

Le calcul des capacités cessait déjà la supervision à 18 ans, mais la policy historique `guardian_links` permettait encore à l'ancien tuteur de lire le lien après la majorité. Le pouvoir était donc coupé, mais la visibilité relationnelle persistait.

La migration forward-only suivante ferme cette rétention de visibilité :

`20260919050000_sinjira_v25_guardian_majority_visibility.sql`

La nouvelle policy utilise un helper self-only par ID de lien. La personne concernée conserve l'accès à son propre historique, tandis que l'ancien tuteur ne peut lire le lien que tant que le compte est dans une bande sous 18 ans (`child`, `child_pending`, `youth`, `youth_pending`). Un tiers obtient toujours `false` et ne peut pas sonder un lien arbitraire.

Le pgTAP enfant compte désormais **67 assertions** et prouve la transition exacte vers `adult` à 18 ans, **0 lien visible pour l'ancien tuteur**, conservation de l'historique pour la personne devenue adulte, fermeture du helper aux tiers et disparition des invitations consommées côté ancien tuteur.

Cette dix-huitième migration reste **non revue production**.

### Fin de visibilité des invitations consommées à la majorité

La revue de cycle de vie a identifié une seconde trace relationnelle : même après disparition de `guardian_links` côté ancien tuteur, une invitation parentale déjà consommée restait lisible sous AAL2 dans `guardian_signup_invites` et conservait `minor_user_id`.

La migration forward-only suivante aligne cette table avec la fin de supervision :

`20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql`

Les codes non consommés du tuteur restent lisibles sous AAL2. En revanche, une invitation consommée n'est plus visible que si le `guardian_link` correspondant est lui-même encore visible. Le passage à `adult` masque donc automatiquement cette trace au tuteur sans supprimer l'historique interne.

Le pgTAP enfant compte désormais **67 assertions** et prouve qu'à 18 ans l'ancien tuteur voit **0 invitation consommée** liée au compte devenu adulte.

Cette dix-neuvième migration reste **non revue production**.

### Métadonnées de contacts jeunesse : consentement + AAL2

Le RPC historique `get_guardian_youth_contacts(uuid)` respectait la supervision active et se fermait à la majorité, mais il n'appliquait pas le drapeau `can_view_contact_metadata` du lien. Il permettait donc à un tuteur vérifié de consulter pseudos, réseaux et dates de dernier contact même lorsque cette permission était désactivée.

La migration forward-only suivante ferme cette incohérence :

`20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql`

Le RPC exige maintenant simultanément : supervision active, `can_view_contact_metadata=true` et session tuteur **AAL2**. Il continue à ne renvoyer aucun contenu de message.

Le pgTAP enfant compte désormais **67 assertions** et prouve les trois états : refus sans consentement explicite, refus en AAL1 malgré le consentement, puis accès aux seules métadonnées sous consentement + AAL2.

Cette vingtième migration reste **non revue production**.

### Métadonnées de contacts : privacy-by-default et choix du compte jeunesse

La revue suivante a confirmé que `can_view_contact_metadata` était historiquement initialisé à `true` lors de la création ou réactivation d'un lien. Il ne représentait donc pas un consentement explicite du compte jeunesse.

La migration forward-only :

`20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql`

passe la permission par défaut à `false`, neutralise les permissions actives héritées qui avaient été accordées implicitement et remet toute création/réactivation de lien à `false`. Le nouveau RPC `set_my_guardian_contact_metadata(uuid,boolean)` est self-only : seul le compte `child` ou `youth` concerné peut autoriser ou retirer cette visibilité.

L'écran Relations expose ce choix uniquement au compte enfant/jeunesse. Le parent voit l'état mais ne peut pas l'activer lui-même. Même après opt-in, `get_guardian_youth_contacts` exige toujours AAL2 et ne révèle jamais le contenu des messages.

Le pgTAP enfant compte désormais **67 assertions** et prouve le cycle complet : désactivé par défaut, refus parent, opt-in du jeune, step-up AAL2 du parent, retrait du jeune, puis retrait d'accès immédiat.

Cette vingt-et-unième migration reste **non revue production**.

### Minimisation du résumé parental de contacts

Même avec opt-in explicite du jeune et AAL2 du tuteur, le RPC historique renvoyait encore l'UUID interne du contact, son `display_name` et l'heure exacte de dernière interaction. Ces éléments dépassaient l'objectif de protection.

La migration forward-only :

`20260919070000_sinjira_v25_guardian_contacts_minimization.sql`

réduit la réponse à trois éléments : **pseudo**, **réseaux concernés** et **date UTC du dernier contact à la journée**. L'UUID, le `display_name`, le timestamp précis et le contenu des messages ne sont pas exposés.

Le pgTAP enfant compte désormais **67 assertions** et utilise un vrai contact jeunesse de preuve pour verrouiller la forme JSON minimisée.

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

Le pgTAP enfant compte désormais **67 assertions** et prouve explicitement qu'un personnage nommé `Avatar Secret` n'est jamais remplacé par le pseudo réel `Contact Jeunesse`, même lorsque les deux appartiennent au même compte de test.

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

Le pgTAP `private_novel_catalog_v25.test.sql` contient désormais **13 assertions** sur les frontières membre/créateur, la non-divulgation des chemins de stockage, le fail-closed des comptes non vérifiés et l’activation RLS du registre privé.

Cette vingt-septième migration reste **non revue production**.

### Profil privé compatible avec les comptes 11 ans

La revue de la base active a révélé une incompatibilité restante : l'inscription V25 accepte les comptes à partir de 11 ans sous supervision, mais l'implémentation interne `private_profile_save` conservait encore l'ancienne erreur `SINJIRA_MINIMUM_AGE_13`. Un compte de 11 ou 12 ans pouvait donc être correctement créé puis être refusé au moment de modifier son coffre privé.

La migration forward-only :

`20260919100000_sinjira_v25_private_profile_age_11.sql`

conserve les barrières MFA, juridiction jeunesse et confidentialité du coffre, remplace la limite effective par **11 ans**, exige toujours un tuteur vérifié avant 14 ans et refuse explicitement un lien dont `revoked_at` n'est pas nul. La même supervision est maintenant imposée à `private_profile_get()` : après révocation ou en l’absence de tuteur valide, un compte de 11–13 ans ne peut plus relire le coffre privé.

Le navigateur affiche désormais un message cohérent avec la règle 11+, tout en reconnaissant une éventuelle erreur historique `SINJIRA_MINIMUM_AGE_13` comme un serveur non encore synchronisé.

Deux preuves SQL sont exécutées par le workflow Profil privé après reconstruction locale : le test historique de **22 assertions** et un nouveau pgTAP de **11 assertions** couvrant 11 ans avec tuteur actif, 11 ans sans tuteur, moins de 11 ans et lien tuteur révoqué.

Cette vingt-huitième migration reste **non revue production**.

### Catalogue canonique du Livre I

La reconstruction locale a montré que le schéma `public.sinjira_novels` pouvait exister sans contenir encore la ligne canonique du Livre I. Dans ce cas, la migration du registre privé exécutait un `INSERT ... SELECT` sans résultat et l'actif intégral n'était pas enregistré.

La migration forward-only :

`20260919103000_sinjira_v25_livre_i_catalog_seed.sql`

garantit que **La Cendre du Jugement** existe dans `public.sinjira_novels`, puis rattache son actif intégral au registre privé. Cet actif reste `enabled=false`, en mode `legacy_env`, sans chemin de stockage privé livré au navigateur et sans autorisation implicite de publication ou de déploiement.

Cette vingt-neuvième migration reste **non revue production**.

### Pseudonyme public séparé du nom affiché privé

La preuve enfant a révélé une fuite de confidentialité dans la synchronisation sociale : `social_profiles.pseudo` pouvait recevoir `profiles.display_name`. Comme `social_profiles` est une surface sociale lisible par les membres authentifiés, le nom affiché privé ne doit jamais y être copié.

La migration forward-only :

`20260919110000_sinjira_v25_social_public_pseudo_privacy.sql`

redéfinit la synchronisation pour dériver **uniquement** de `profiles.pseudo`. Pour compatibilité, `social_profiles.display_name` reste présent mais devient un miroir du pseudonyme public. Un backfill nettoie aussi les lignes existantes qui auraient conservé un nom affiché privé.

Le pgTAP enfant est ensuite passé à **67 assertions** : l’assertion réseau Compte prouve le pseudo public correct, le profil social nettoyé et l’absence de `Nom Affiché Privé`; deux preuves supplémentaires vérifient aussi que l’inscription ne préactive ni la publication mémorielle publique ni les souhaits d’anniversaire/usages privés optionnels.

Cette trentième migration reste **non revue production**.

### Défense RLS du registre privé des romans

La validation transversale Supabase a détecté que le registre serveur `private.sinjira_private_novel_assets` avait ses privilèges directs révoqués mais n'avait pas encore RLS activée. La défense en profondeur du projet exige les deux barrières.

La migration forward-only :

`20260919113000_sinjira_v25_private_novel_asset_rls.sql`

active RLS sur cette table sans créer de policy membre. Les rôles `public`, `anon` et `authenticated` restent explicitement révoqués; le chemin de livraison privé continue de passer uniquement par les contrôles serveur dédiés et le rôle de service. Cette migration ne configure aucun actif privé et n'active aucune diffusion publique.

Cette trente-et-unième migration reste **non revue production**.

### Visibilité catalogue projets du créateur

La revue du portefeuille et de la bibliothèque a confirmé que les preuves V25 couvraient les romans et les produits, mais pas explicitement les lignes `public.projects` internes (jeux et autres créations). La migration forward-only :

`20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql`

ajoute une policy de lecture `authenticated` limitée à `is_sinjira_owner(auth.uid())`. Elle permet au créateur de voir les projets brouillons ou restreints dans son catalogue de gestion sans créer de faux achat, entitlement ou `project_access`. Aucun droit membre supplémentaire n'est accordé.

Le pgTAP `account_content_hub_v25.test.sql` prouve désormais que le membre standard ne voit pas le projet interne de test et que le créateur le voit.

Cette trente-deuxième migration reste **non revue production**.

### Reconvergence de la frontière RPC V25

Le contrat advisor V24.5.24 a révélé que plusieurs RPC Compte/Enfant/Junior redéfinies par V25 étaient redevenues des fonctions `SECURITY DEFINER` directement exposées dans le schéma API `public`. Les anciennes frontières V24.5.x avaient précisément supprimé cette exposition directe.

La migration forward-only :

`20260919123000_sinjira_v25_public_rpc_boundary.sql`

replace **23 implémentations privilégiées** dans le schéma interne `sinjira_v25_internal` et recrée leurs signatures publiques sous forme de wrappers `SECURITY INVOKER`. Elle conserve l'exécution `authenticated` des 23 RPC et l'accès `anon` uniquement aux trois helpers qui étaient déjà anonymes : `sinjira_my_age_band()`, `sinjira_child_project_available(uuid)` et `sinjira_child_document_available(uuid)`.

La migration échoue si le nombre de RPC, les privilèges anonymes ou les privilèges authentifiés ne correspondent pas exactement à l'état attendu. Elle vérifie désormais aussi l’unicité **par nom** : chacune des 23 cibles doit résoudre vers exactement une fonction `public SECURITY DEFINER`, et chacune des trois cibles anon vers exactement une fonction réellement exécutable par `anon`. Un overload inattendu ne peut donc pas compenser silencieusement une cible manquante. Elle n'élargit aucun droit métier, ne modifie aucune donnée utilisateur et ne change ni le reviewed batch ni le ledger production.

Le contrat pgTAP historique `security_advisor_contract_v24_5_24.test.sql` redevient ainsi applicable sans liste blanche : aucune fonction `SECURITY DEFINER` du schéma `public` ne doit être directement exécutable par `anon` ou `authenticated`.

Cette trente-troisième migration reste **non revue production**.

### Convergence des privilèges navigateur du catalogue Compte

Le pgTAP Compte a ensuite révélé une divergence de reconstruction locale : les tables du Compte universel avaient bien leurs policies RLS, mais les privilèges SQL navigateur explicites de la plateforme historique n’étaient pas convergés. Une policy seule ne donne pas le droit SQL de lire la table; `authenticated` recevait donc `permission denied for table projects` avant même l’évaluation RLS.

La migration forward-only :

`20260919130000_sinjira_v25_account_catalog_browser_privileges.sql`

révoque d’abord les privilèges navigateur implicites puis réaccorde uniquement le contrat utilisé par les clients actuels :

- `projects` et `documents` : `SELECT` pour `anon` / `authenticated`, toujours filtré par RLS;
- `project_access` : `SELECT` authentifié self-only via RLS;
- `access_requests` : `SELECT` + `INSERT` authentifié, sans `UPDATE` / `DELETE` client;
- `playtests` : `SELECT` authentifié;
- `playtest_participants` : `SELECT` + `INSERT` authentifié, sans décision client;
- `extensions` : `SELECT` uniquement pour les lignes rendues publiques par RLS.

Aucune création/modification de projet, décision de demande, approbation de candidature ou administration directe n’est ouverte au navigateur. Le pgTAP `account_content_hub_v25.test.sql` passe à **41 assertions** et prouve les privilèges positifs, les refus d’écriture sensibles, les `WITH CHECK` self-only des INSERT `access_requests` / `playtest_participants` (bande adulte/youth + statuts `pending` / `applied`) et la frontière de `project_access_rank` : implémentation `SECURITY DEFINER` déplacée vers `sinjira_catalog_internal`, policies RLS conservées par OID, wrapper public `SECURITY INVOKER` réservé au `service_role`. Le workflow Compte surveille explicitement cette migration, tandis que le workflow Sécurité En direct surveille déjà `supabase/migrations/**`.

La migration ferme désormais aussi la fenêtre transitoire immédiatement après le déplacement : l’implémentation interne conserve son OID mais retourne `0` lorsqu’un rôle navigateur fournit un `p_user_id` différent de `auth.uid()`. `service_role` conserve l’usage serveur arbitraire. Ainsi, le droit `EXECUTE` requis par les policies RLS ne devient jamais un oracle inter-compte avant `20260921010000`.

Cette trente-quatrième migration reste **non revue production**.

### Minimisation de la réponse interne du Mode Voyage

La revue statique du Mode Voyage a montré une asymétrie de confidentialité : les wrappers publics `SECURITY INVOKER` construisaient une réponse minimale, mais leurs implémentations `sinjira_security_internal` restaient directement exécutables par `authenticated` afin que les wrappers puissent fonctionner. La fonction interne de création renvoyait encore `to_jsonb(v_row)`, donc la ligne complète, incluant des métadonnées serveur comme `user_id` et `delete_after`.

La migration forward-only :

`20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql`

ne retire aucun garde métier. Elle conserve l'identité dérivée de `auth.uid()`, AAL2 lorsque disponible, validation ISO alpha-2, déduplication, limite de 1 à 12 pays, période maximale de 180 jours, self-only à l'annulation et rétention serveur. Elle réduit uniquement les réponses directes des fonctions internes :

- création : `id`, `status`, `starts_at`, `ends_at`, `destinations`;
- annulation : `id`, `status`.

Ainsi, un appel direct à l'implémentation interne ne peut plus contourner la minimisation du wrapper public pour obtenir `user_id`, `delete_after`, `cancelled_at`, timestamps techniques ou `multi_country`.

La même définition minimisée est désormais aussi installée dès `20260914223000`, au moment où les wrappers publics sont introduits. `20260921005000` demeure volontairement présent comme convergence finale, mais il n’existe plus de fenêtre intermédiaire où un appel direct interne peut renvoyer la ligne complète.

Le pgTAP `security_travel_client_visibility_v25.test.sql` passe à **28 assertions** et vérifie désormais aussi l'existence, les ACL et l'absence de retour `to_jsonb(v_row)` des implémentations internes effectives. Les garde-fous `validate_security_travel_client_visibility_v25.py` et `validate_security_travel_self_only_v25.py` lisent explicitement cette migration finale.

Cette trente-cinquième migration reste **non revue production**.

### Helpers catalogue self-only et absence d’oracle anonyme

La revue croisée du catalogue Compte et du classement 11–12 a identifié deux contournements par appels directs aux helpers internes nécessaires aux policies RLS :

- `sinjira_catalog_internal.project_access_rank(uuid,uuid)` restait exécutable par `anon/authenticated` et acceptait un `p_user_id` arbitraire, malgré un wrapper public réservé au `service_role`;
- les helpers de disponibilité 11–12 pouvaient confirmer par UUID l’existence d’un projet/document `account` à un visiteur anonyme.

La migration forward-only :

`20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql`

conserve les OID nécessaires aux policies et les droits d’exécution requis par la RLS, mais rend les réponses fail-closed :
- un rôle navigateur ne peut calculer `project_access_rank` que pour `auth.uid()` (ou `NULL` pour anon); toute tentative de cibler un autre UUID retourne `0`;
- `service_role` conserve les calculs serveur avec UUID explicite;
- un projet `account` n’est plus confirmable par anon via le helper 11–12;
- un document 11–12 exige désormais aussi le rang d’accès réel du compte courant.

Le pgTAP Compte passe à **49 assertions** et le pgTAP classement 11–12 à **23 assertions**.

Cette trente-sixième migration reste **non revue production**.

### Catalogue complet pour la famille du créateur, sans faux achat

La demande fonctionnelle est de conserver trois comportements distincts :

- le propriétaire SINJIRA voit toutes ses créations;
- les comptes familiaux explicitement autorisés voient eux aussi le catalogue complet, sans créer de fausse commande, entitlement ou ligne `project_access`;
- les autres membres restent limités au contenu public/gratuit et à leurs achats ou droits réels.

La migration forward-only :

`20260922014000_sinjira_v25_creator_family_catalog_access.sql`

ajoute un registre privé par UUID et un provisionnement réservé à `service_role`. Les implémentations privilégiées famille restent dans `sinjira_v25_internal`; les RPC publics correspondants sont uniquement des wrappers `SECURITY INVOKER`, conformément à la frontière C2. Le courriel fourni au moment du provisionnement sert uniquement à résoudre `auth.users.id`; il n'est ni stocké dans le registre familial ni écrit dans cette migration publique.

Pour 13+ (`youth` / `adult`), un compte familial peut relire les projets, romans et produits internes sans faux achat. `has_sinjira_product()` reconnaît aussi ce rôle pour lancer un jeu/licence appartenant à l'univers, tout en conservant l'anti-énumération et sans créer d'entitlement. Pour 11–12 ans, l'accès supplémentaire est limité à des RPC de catalogue minimisés : la fiche d'une création peut être visible, mais un projet non approuvé ne contient ni chemin ouvrable ni couverture non classée; un roman privé ne reçoit jamais `full_access`, `public_path`, `demo_path`, couverture privée ou nombre de pages, et le droit produit reste faux. `project_access_rank` n'accorde le rang famille qu'à `youth/adult`.

Les adresses réelles des comptes familiaux ne sont volontairement pas inscrites dans Git. Leur association production devra être exécutée séparément sous `service_role`, après revue et déploiement de la migration.

Le pgTAP famille est maintenant porté à **44 assertions**. Il couvre notamment le gratuit visible au membre standard, le privé refusé sans droit, puis un roman privé rendu accessible par une commande `paid` sans créer d'entitlement artificiel.

Cette trente-septième migration reste **non revue production**.

### Accès produit après achat réellement payé

La revue du parcours catalogue a identifié une divergence : la RLS `products` permettait déjà à un membre de relire un produit lié à une commande enregistrée, mais `has_sinjira_product(text,uuid)` ne reconnaissait que les entitlements. Un membre pouvait donc voir un produit acheté tout en étant refusé à l'ouverture.

La migration forward-only :

`20260922023000_sinjira_v25_paid_order_product_access.sql`

aligne le droit produit sur les droits réels :
- un entitlement durable reste valide même si le produit devient ensuite inactif à la vente;
- une commande `status='paid'` donne également le droit produit;
- une commande non payée ne donne aucun accès;
- aucun faux entitlement n'est créé;
- le garde self-only par UUID est conservé.

Le pgTAP Compte est maintenant porté à **49 assertions** : entitlement durable, commande `paid`, produit d'une commande `pending` invisible comme achat et `has_sinjira_product()` faux pour cette commande non payée. La preuve CI doit être relue sur le HEAD final gelé.

Cette trente-huitième migration reste **non revue production**.

### Revue réouverte après durcissements du 21 septembre 2026

Le snapshot a volontairement détecté que plusieurs migrations non revues avaient changé depuis leurs empreintes précédentes. Elles ont été relues avant mise à jour de ce dossier; les changements sont des **resserrements**, pas des élargissements de droits :

- `20260916210000_sinjira_v25_child_guardian_signup.sql` : privacy-by-default dès la première supervision, purge immédiate de `guardian_code`, visibilité tuteur bornée à la minorité; le RPC historique de contacts est remplacé dès cette étape par la version consentement explicite + AAL2 + réponse minimisée; publication mémorielle publique et souhait d’anniversaire restent à `false` par défaut; avant le classement explicite, le compte `child` authentifié reste aussi fermé aux projets/documents non classés;
- `20260917223000_sinjira_v25_junior_community.sql` : révocation durable du consentement Junior, AAL2 à l’activation, retrait de l’alias Junior du résumé tuteur;
- `20260918010000_sinjira_v25_child_sensitive_boundary.sql` : conserve la fermeture complète `projects/documents` pour `child` jusqu’à la migration de classement explicite `approved_11_12`, évitant une réouverture intermédiaire;
- `20260918013000_sinjira_v25_child_content_rating.sql` : fermeture de l’oracle `anon` sur les projets `account` dès l’introduction du helper et exigence immédiate du rang d’accès réel pour les documents;
- `20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql` : retrait de `junior_alias` du résultat parental;
- `20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql` : métadonnées parentales minimisées dès la première exposition et identités Compte/Personnage cloisonnées;
- `20260919070000_sinjira_v25_guardian_contacts_minimization.sql` : maintien du cloisonnement sans UUID, `display_name` ni heure précise;
- `20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql` : la réponse des implémentations internes est maintenant minimisée dès A3, supprimant la fenêtre transitoire avant `20260921005000`;
- `20260919093000_sinjira_v25_private_novel_catalog.sql` : RLS activée dès la création du registre privé et rôle propriétaire résolu par la frontière serveur canonique.

Cette réouverture de revue **ne transforme aucune migration en migration production revue**. Les 38 migrations restent non revues au sens du `production-reviewed-migration-batch.txt`.

## 3. Lot local futur actuellement non revu

Le snapshot de revue attend exactement **38 migrations locales futures non revues**.

### Mode Voyage

| Migration | Git blob SHA-1 |
|---|---|
| `20260913030500_sinjira_v25_travel_mode_geo_scope_hardening.sql` | `7285d1e30ea288004d17c1dbfbf9f01662b36bb7` |
| `20260913230000_sinjira_v25_travel_mode_retention_purge.sql` | `41b8dc3d1b1e09c018e588755edb053e63e9904a` |
| `20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql` | `2d7b8ccbfc79fed6a03208086a138618779d6e2d` |
| `20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql` | `1653597f4c9fe053a1b691fe810a3d1b8ca60955` |

### Frontières helpers navigateur

| Migration | Git blob SHA-1 |
|---|---|
| `20260921010000_sinjira_v25_browser_helper_self_only_hardening.sql` | `1a6f22628bf7dc944e7d3b77c2744c40e3204b03` |

### Catalogue famille créateur

| Migration | Git blob SHA-1 |
|---|---|
| `20260922014000_sinjira_v25_creator_family_catalog_access.sql` | `5b3ee72a1e5fab921e2aeb87782bb88ef6d61aa0` |
| `20260922023000_sinjira_v25_paid_order_product_access.sql` | `edb262781911679ff740573cc3830b9dddfabf94` |

### Enfant 11–12 / Junior

| Migration | Git blob SHA-1 |
|---|---|
| `20260916210000_sinjira_v25_child_guardian_signup.sql` | `51544dee4322d809a8116fb5614962de78691b31` |
| `20260917223000_sinjira_v25_junior_community.sql` | `64e66dc8d9c45de9ecbb1174fdb842e4444b9b6b` |
| `20260918010000_sinjira_v25_child_sensitive_boundary.sql` | `d526702c0c32bda7628a37134b9f64e9c66d6351` |
| `20260918013000_sinjira_v25_child_content_rating.sql` | `b0a2bfda90579830083d128035ee533d06dd2159` |
| `20260918020000_sinjira_v25_account_capabilities.sql` | `0a16bfcc49e51ee2b96cb98742442ae3d00e5c76` |
| `20260918023000_sinjira_v25_minor_content_policy_compat.sql` | `c0556e3baa218f9529f185010455984a0bc1cd03` |
| `20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql` | `efa9d6a29c4decfe0180e9262827022ff752f670` |
| `20260919013000_sinjira_v25_child_pending_guardian_redeem.sql` | `faaccf3cce0bf725d0f42a5cbecaecbba4b89aa2` |
| `20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql` | `e14c41364246929054282bccb0e4abc5641b8643` |
| `20260919023000_sinjira_v25_guardian_invite_aal2.sql` | `5700bfaa2b5a95d84d37ad475524960bdb78fc9b` |
| `20260919030000_sinjira_v25_guardian_code_metadata_minimization.sql` | `f08102d4bc2485bc229e21076f361bf31552c928` |
| `20260919033000_sinjira_v25_guardian_invite_read_aal2.sql` | `b2439fbad69798db42c17a04887dff50d9f184cc` |
| `20260919040000_sinjira_v25_junior_enable_aal2.sql` | `df5475777abd5bb8fff26510a727d3d04cffce53` |
| `20260919043000_sinjira_v25_guardian_revoke_aal2.sql` | `7dada317202bdd1add1d4dc5113e3aca682459e4` |
| `20260919050000_sinjira_v25_guardian_majority_visibility.sql` | `d7a65f65e1a870620809f1a2e669ef031d6f6d8a` |
| `20260919053000_sinjira_v25_guardian_invite_majority_visibility.sql` | `ac18154c958b707d94ddc557b1af6b2af01ba62f` |
| `20260919060000_sinjira_v25_guardian_contacts_consent_aal2.sql` | `d2ef613bfb372efe620e413d5e059b4d1b1e6c64` |
| `20260919063000_sinjira_v25_guardian_contact_metadata_opt_in.sql` | `2d91c64a90f5c8bca506577ef359078fdf558fad` |
| `20260919070000_sinjira_v25_guardian_contacts_minimization.sql` | `e684227b322aa88dbd43376d8bd9aa19a6161f6e` |
| `20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql` | `07b1ea063e57d3dd4a31e689fac6f44fd1ca6d18` |
| `20260919080000_sinjira_v25_guardian_character_identity_isolation.sql` | `7c169564095bb440bde8a2a106c4e00aa2f307e4` |
| `20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql` | `8e0fd367bd0c30ed77f947ae0583408b370121a1` |
| `20260919090000_sinjira_v25_account_content_hub.sql` | `29358d27f8f505897b924062e208b8d5c740f8c5` |
| `20260919093000_sinjira_v25_private_novel_catalog.sql` | `7ca3cf47f5f67205cb2a36310513273faacb7dea` |
| `20260919100000_sinjira_v25_private_profile_age_11.sql` | `db4d0c04f4fba2a6044e12b28d882382ed077086` |
| `20260919103000_sinjira_v25_livre_i_catalog_seed.sql` | `04929202946a0cda629c1f8005dbf51e4bfb2d68` |
| `20260919110000_sinjira_v25_social_public_pseudo_privacy.sql` | `ac4f11e8e1591c35f0be91f541a21763fdb3ec8d` |
| `20260919113000_sinjira_v25_private_novel_asset_rls.sql` | `745ae12098e538415dde16bac198d05610b99954` |
| `20260919120000_sinjira_v25_projects_owner_catalog_visibility.sql` | `5ed558a9426173fdb714479d28f170ada542803b` |
| `20260919123000_sinjira_v25_public_rpc_boundary.sql` | `61377e409f769ed94646791acaf8f3c1f86328d0` |
| `20260919130000_sinjira_v25_account_catalog_browser_privileges.sql` | `4436b3d183fa975f5eedeb0427d66da050dfa961` |

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
2. Relire les **38 migrations** dans l’ordre chronologique canonique; la migration `20260921005000` appartient fonctionnellement au lot Mode Voyage mais reste la dernière par timestamp.
3. Vérifier RLS, privilèges, `SECURITY DEFINER`, `search_path`, rétention, suppression et transitions d’âge.
4. Comparer les empreintes ci-dessus.
5. Relire les preuves CI et pgTAP, en particulier la révocation multi-tuteur.
6. Vérifier séparément les bloqueurs #135 et #240.
7. Seulement après approbation humaine explicite, mettre à jour le lot revu.
8. Garder le prévol distant et l’application production comme étapes distinctes.
9. Ne réconcilier le ledger qu’après une preuve distante réelle.

**L’humain avant tout. Protéger sans surveiller.**
