# Correctif SINJIRA™ — inscription, confirmation, Registre et notifications Formspree
Date : 2026-11-07

## Diagnostic du projet connecté

- Le point d'entrée `/compte/inscription.html` appelle Supabase Auth `signUp`.
- Des journaux Auth ont montré des réponses d'inscription 200, puis des vérifications `/verify` avec « One-time token not found » et « Email link is invalid or has expired ».
- Les systèmes de sécurité des messageries peuvent préouvrir les URL et consommer les liens à usage unique. C'est une **cause possible**, pas une certitude établie pour chaque visiteur.
- Le formulaire `/projets/sinjira/registre/` exige une session authentifiée; il vérifie en outre la protection AAL2/TOTP quand `sensitive_step_up` est activé (valeur par défaut).
- L'ancien transport Resend des copies et avis est désactivé. Le correctif propose un envoi distinct via Formspree uniquement après accord explicite du membre.

## Déploiement — ordre impératif

1. Fusionner puis déployer les fichiers de ce correctif. **Ne pas modifier le modèle de courriel avant que la page et son script soient effectivement disponibles en production.**
2. Vérifier que les deux URL publiques répondent :
   - `https://www.benoitcantin.com/compte/confirmer.html`
   - `https://www.benoitcantin.com/assets/js/sinjira-confirm-email.js`
3. Ouvrir Supabase Dashboard → Authentication → URL Configuration :
   - **Site URL** : `https://www.benoitcantin.com` (ne pas laisser localhost).
   - Ajouter dans les **Redirect URLs** : `https://www.benoitcantin.com/compte/confirmer.html`.
   - Conserver temporairement les anciennes routes de retour tant que les anciens courriels circulent.
4. Ouvrir Supabase Dashboard → Authentication → Email Templates → **Confirm sign up**.
5. Remplacer uniquement le modèle **Confirm sign up** par ce modèle (ne pas changer les modèles de récupération et de changement d'adresse) :

```html
<!doctype html>
<html lang="fr">
  <body>
    <h2>Confirmez votre adresse courriel SINJIRA™</h2>
    <p>Pour activer votre compte, ouvrez la page suivante et cliquez ensuite sur « Confirmer mon compte » :</p>
    <p>
      <a href="https://www.benoitcantin.com/compte/confirmer.html#token_hash={{ .TokenHash }}&amp;type=email">
        Ouvrir la confirmation SINJIRA™
      </a>
    </p>
    <p>Si vous n'avez pas demandé de compte SINJIRA™, ignorez ce message.</p>
  </body>
</html>
```

Le `#token_hash=` fait voyager le jeton dans le fragment URL (non envoyé au serveur de pages statiques). La page **n'appelle pas** `verifyOtp` pendant le chargement; elle l'appelle seulement après un clic explicite. Ne pas inclure de jeton dans une capture d'écran, un ticket, un journal ou un message.

6. Si un prestataire de courriel réécrit les liens pour le suivi de clic, **désactiver le suivi des liens** pour les messages d'authentification.
7. Faire un test avec un compte de test et une boîte de réception administrée par vous : inscription → courriel → page SINJIRA → clic explicite → authentification → ouverture Compte ou Registre. Vérifier la récupération quand un lien est expiré au moyen de « Renvoyer un lien ».
8. Pour transmettre le questionnaire, le visiteur doit être connecté. Lorsque la protection sensible est activée, il doit configurer la 2FA dans `/compte/securite.html` et valider la session AAL2. **Ce correctif ne diminue pas les contrôles de sécurité des dossiers privés.**
9. Tester un questionnaire de test avec consentement et vérifier le nouvel enregistrement dans l'administration. L'envoi par Formspree doit être configuré dans Workflow, séparément de la sauvegarde Supabase. Les accusés de réception automatiques Formspree exigent Professional ou Business.

## Tests de non-régression suggérés

- Le lien du modèle ne vise **pas** `/auth/v1/verify` directement.
- Consulter la page sans cliquer n'active pas le compte.
- Un lien à jeton invalide affiche un message et le renvoi, sans consommer d'autres jetons.
- Le renvoi d'une confirmation n'expose pas l'existence d'un compte (message générique).
- L'option « questionnaire » dirige vers le Registre après validation.
- Le Registre ne transmet pas sans session valide et conserve son contrôle MFA/AAL2.
- Aucun secret serveur, clé de service ou donnée personnelle n'est ajouté au dépôt.
- Vérifier les tests CI et l'allowlist de publication Web avant fusion.

Documentation officielle :
- https://supabase.com/docs/guides/auth/auth-email-templates
- https://supabase.com/docs/guides/auth/redirect-urls
- https://supabase.com/docs/reference/javascript/auth-verifyotp

## Intégration Formspree (accusés et copie des réponses créatives)

Deux formulaires ont été créés dans Formspree :

- **Créer votre compte** : `https://formspree.io/f/xzeeqynp`. La notification n'est faite qu'après confirmation réelle du courriel dans Supabase.
- **Registre des Consciences** : `https://formspree.io/f/mrppvrwa`. La notification n'est faite qu'après écriture confirmée dans `character_submissions`.

Les deux avis sont déclenchés **côté serveur** par un helper unique `supabase/functions/_shared/sinjira-formspree.ts`.
Après un consentement facultatif enregistré dans SINJIRA, chaque avis contient le champ `email` du compte Supabase, `event`, `reference` (UUID aléatoire distinct du compte et du dossier), `message`, et `date`. Pour le Registre, le champ `questionnaire` contient **les réponses créatives** de la liste blanche du formulaire (y compris les notes libres). **Aucun mot de passe, nom légal, date de naissance, téléphone, photo, code parental ou information familiale n'est transféré.** Les données originales et complètes restent dans Supabase; une copie des réponses créatives et l'adresse courriel transitent par Formspree et peuvent être archivées par ce prestataire et reçues par courriel.

Un registre dédié `public.sinjira_formspree_events`, fermé aux rôles `anon`/`authenticated` par RLS et privilèges SQL, assure une seule notification réservée par `(event_type, source_id)`. Un échec Formspree n'annule jamais la sauvegarde du questionnaire ni l'activation du compte. Contrôler aussi l'onglet Spam : Formshield est activé.

### Mise en production dans cet ordre

1. Examiner et tester les modifications de la PR unifiée (remplaçant la PR de confirmation initiale).
2. Vérifier que la migration `supabase/migrations/20261108054703_sinjira_formspree_notification_ledger.sql` est déjà enregistrée en production (installée le 8 novembre 2026). **Ne pas l'exécuter une deuxième fois.** Pour un nouvel environnement vierge, l'appliquer avant le déploiement des fonctions.
3. Déployer `submit-character-questionnaire` (avec l'import partagé) et `notify-account-confirmation` sur le projet `gpvivleexywljowcqkru`. Conserver **verify_jwt=true** pour les deux.
4. Déployer les fichiers Web depuis GitHub/Netlify et vérifier que `/compte/confirmer.html`, `/assets/js/sinjira-confirm-email.js` et les deux formulaires sont accessibles.
5. Configurer **Supabase Authentication → URL Configuration → Site URL** à `https://www.benoitcantin.com` et autoriser `https://www.benoitcantin.com/compte/confirmer.html` dans Redirect URLs.
6. Dans **Supabase Authentication → Email Templates → Confirm sign up**, installer le modèle avec le fragment `#token_hash={{ .TokenHash }}&amp;type=email` ci-dessus. **Ne jamais activer ce modèle avant que la page `confirmer.html` soit déployée.**
7. Vérifier que la confirmation ne s'effectue pas simplement à l'ouverture du courriel. Seul le clic `Confirmer mon compte` doit échanger le jeton.
8. Faire un essai avec **une adresse de test contrôlée**, puis confirmer que la notification apparaît dans le Formspree **Créer votre compte** une seule fois. Ne jamais soumettre directement à Formspree le formulaire d'inscription contenant les mots de passe.
9. Avec ce compte, configurer le second facteur via `/compte/securite.html`, se reconnecter en AAL2, envoyer une participation factice consentie du Registre, puis vérifier qu'un **seul dossier** est sauvegardé dans Supabase et qu'une **seule soumission avec courriel et réponses créatives** apparaît dans Formspree, et que sa notification à sinjiraofficiel@gmail.com contient le champ questionnaire.
10. Vérifier les erreurs, les délais de courriel, les journaux Auth Supabase et les alertes du Registre. Le transport Resend historique demeure désactivé (`PAID_EXTERNAL_SERVICES_ENABLED=false`). Cette valeur n'empêche pas le nouveau transport Formspree, mais la configuration Formspree est nécessaire et sa capacité de réponse automatique dépend du forfait.

### Limites et échecs possibles

- Les anciens courriels utilisant un lien Supabase direct peuvent déjà être expirés ou consommés; l'utilisateur doit demander un **nouveau** lien depuis `/compte/confirmer.html`.
- L'envoi d'avis Formspree est un service **secondaire** et dépend de ses protections anti-spam, quotas et disponibilité.
- Un avis en échec est marqué `delivery_status='failed'` dans le registre interne. Par défaut, aucune répétition automatique n'est lancée, afin de privilégier l'absence de doublons; une reprise contrôlée devra être développée si nécessaire.
- Si JavaScript ne charge pas, les boutons d'envoi restent désactivés. Aucune inscription ou participation ne doit être présentée comme enregistrée.
- La configuration des **modèles de courriel Supabase hébergés** n'est pas modifiée par un commit GitHub : c'est une étape manuelle impérative.

### Vérifications statiques prévues

```sh
python3 scripts/validate_auth.py
python3 scripts/validate_character_questionnaire_security.py
python3 scripts/validate_edge_function_inventory.py
python3 scripts/validate_public_edge_auth.py
python3 scripts/validate_production_schema_manifest.py
python3 scripts/validate_sinjira_signup_registry_delivery.py
```


## Réglages obligatoires dans le tableau de bord Formspree

**Aucun commit GitHub ne peut modifier les réglages du tableau de bord Formspree.** Ne pas confondre le bouton « formulaire créé » et l'activation d'un envoi de courriel.

### Formspree — Registre des Consciences (mrppvrwa)

1. Ouvrir le tableau de bord Formspree, sélectionner **Registre des Consciences**, puis **Workflow**.
2. Vérifier la présence d'une action **Email** (création avec « + Add New », si absente), et la diriger vers **sinjiraofficiel@gmail.com**. Cette adresse doit préalablement avoir été ajoutée et **vérifiée** dans la section **Account → Email addresses** de Formspree.
3. Vérifier que la notification Email inclut les champs de la soumission : `email` (pour Reply-To), `reference`, `event`, `questionnaire`, `date`. Le champ `questionnaire` est une copie lisible, avec une entrée par question du formulaire.
4. Si vous avez **Professional ou Business**, dans **Workflow → Actions → + Add New → Auto Response**, configurer : 
   - Nom de l'expéditeur : **SINJIRA™ — Registre des Consciences**
   - Objet : **SINJIRA™ — Votre questionnaire a bien été reçu**
   - Message : **Bonjour, votre questionnaire du Registre des Consciences a été enregistré dans SINJIRA™. Merci pour votre participation. Les réponses restent soumises à vérification avant toute utilisation dans l'univers SINJIRA™.**
5. Pour tester sans vraies données : utiliser un compte de test, approuver l'envoi Formspree, envoyer des réponses fictives et vérifier une seule soumission, la réception dans **sinjiraofficiel@gmail.com** et l'accusé dans la boîte de test. Le statut HTTP 2xx de Formspree ne prouve **pas** la livraison d'un courriel.
6. Si vous avez l'offre gratuite, l'action Auto Response peut être indisponible : conserver la confirmation **sur le site** et un accès au dossier Supabase, sans affirmer qu'un accusé courriel Formspree a été envoyé.

### Formspree — Créer votre compte (xzeeqynp)

1. Dans Formspree, ouvrir **Créer votre compte** puis **Workflow**.
2. L'avis Formspree ne se déclenche qu'après confirmation réelle du compte dans Supabase et seulement si l'utilisateur a choisi le consentement facultatif. Aucun mot de passe n'est envoyé.
3. Sous **Professional ou Business**, ajouter une action **Auto Response** :
   - Nom de l'expéditeur : **SINJIRA™ — Comptes**
   - Objet : **SINJIRA™ — Votre compte a été confirmé**
   - Message : **Bonjour, votre adresse courriel est confirmée et votre Compte SINJIRA™ est prêt. Vous pouvez maintenant vous connecter et accéder au Registre des Consciences. Si vous n'êtes pas à l'origine de cette démarche, contactez SINJIRA™.**
4. La confirmation indispensable à la création du compte **continue d'être envoyée par Supabase Auth**. Formspree n'active pas un compte, il envoie simplement un accusé supplémentaire si l'action Auto Response est disponible et activée.
5. Test : un courriel de confirmation Supabase, un seul avis Formspree et un seul accusé Formspree pour le même compte; aucune duplication de comptes.

### Respect de la vie privée

- Les cases d'accord Formspree sont **facultatives** et non précochées. Un refus ne bloque pas le compte ni la sauvegarde Supabase du questionnaire.
- Le consentement au transfert du Registre couvre le **courriel et les réponses créatives**, notamment les notes facultatives. Éviter toute donnée très privée dans les champs libres si on choisit ce transfert.
- Ne pas transmettre des photos ou des justificatifs à Formspree. Le canal n'est pas le coffre privé des pièces jointes.
- Formspree peut conserver les soumissions dans son archive si l'option **Submission Archive** est activée. Réviser ses durées de conservation et sa politique de confidentialité avant lancement.
- L'envoi est **au mieux une fois** par événement source : aucun doublon automatique. Si Formspree échoue, la soumission officielle est intacte et une reprise contrôlée doit être décidée manuellement.

Documentation Formspree (février 2026) :
- https://help.formspree.io/articles/plugins/sending-a-confirmation-or-response-email
- https://help.formspree.io/fr/articles/form-and-project-settings/changing-a-form-email-address
- https://help.formspree.io/fr/articles/building-your-form/special-fields

## Alignement de l'historique de migration — 8 novembre 2026

La migration a été appliquée en production avec la version distante **`20261108054703`** et le nom **`sinjira_formspree_notification_ledger`**. Le fichier local et son inventaire revu utilisent désormais cette même version. Son contenu SQL et son blob Git restent **strictement inchangés** (`0bd4e7cb92ae73b8897d91f0fd67fbdff895919c`).

- **Production existante :** aucun second `db push` de cette migration; contrôler `supabase_migrations.schema_migrations` et la table `public.sinjira_formspree_events` (RLS activée, accès `anon`/`authenticated` refusé) avant d'activer les Edge Functions.
- **Environnement vierge :** appliquer cette version une fois dans l'ordre des migrations autorisées, après revue du manifeste, avant de déployer les fonctions.
- Ne pas réécrire l'historique `supabase_migrations` et ne pas ajouter de migration « réparatrice » duplicative.
- En date de cette vérification, GitHub #834 reste en brouillon; les fonctions et la page Web sont encore à publier. Un statut CI historique ne vaut pas réussite des tests du nouveau commit.

## Résilience aux accusés réseau perdus et transparence des notifications

La page du Registre conserve désormais la photo privée après un appel de soumission commencé dont le résultat serveur est inconnu. Elle n'efface le fichier temporaire que si **aucun appel de soumission serveur n'a été tenté**. En effet, un délai réseau peut masquer une sauvegarde déjà réussie; supprimer la photo dans ce cas créerait une référence cassée dans le dossier. Lorsqu'un envoi échoue sans réponse sûre, le participant doit recharger le Registre pour vérifier si sa participation est apparue avant de retenter un envoi.

Le message de réussite distingue aussi explicitement le résultat `admin_notification_created` renvoyé par le serveur : un avis interne non confirmé ne doit pas être annoncé comme créé. Le succès du dossier Supabase ne constitue toujours pas une preuve de livraison de courriel Formspree. Ces gardes sont vérifiées dans `scripts/validate_sinjira_signup_registry_delivery.py`; le script client utilise désormais `sinjira-character-registry.js?v=24.5.5` pour éviter les caches de l'ancienne version.

**Limite résiduelle à revoir avant publication :** un fichier privé orphelin peut subsister lorsqu'un envoi échoue définitivement après avoir été tenté; un mécanisme de maintenance sécurisé et borné est préférable à une suppression immédiate risquant de perdre une photo référencée. Aucun nettoyage automatique global ni suppression de données réelles ne sont activés par ce correctif.

## Anti-doublon côté navigateur après résultat réseau indéterminé

Lorsque l'appel `submit-character-questionnaire` a commencé, une erreur de réseau ou une réponse d'API non confirmée est traitée comme un **résultat indéterminé** : SINJIRA conserve la photo privée qui peut déjà être liée à une participation, désactive tout nouvel envoi sur cette page, garde les réponses affichées et fournit un lien « Vérifier mon dossier (nouvel onglet) » vers `/compte/mon-personnage.html`. Cela évite de recréer inutilement un dossier ou de générer de nouveaux fichiers dans le navigateur avant une consultation de l'état serveur. Le participant peut ouvrir le dossier dans un autre onglet, puis recharger le Registre après vérification si aucun dossier n'existe.

Les erreurs **avant** toute invocation serveur (ex. photo refusée ou préparation locale) conservent le droit de réessayer et peuvent entraîner le nettoyage du fichier temporaire si présent. Ce comportement est gardé par le contrat `scripts/validate_sinjira_signup_registry_delivery.py` et la version de script `sinjira-character-registry.js?v=24.5.6`.

**Limite connue :** la vérification de l'état dans un autre onglet repose sur la connexion du même participant; elle ne constitue pas une reprise transactionnelle automatique du POST. Les tests réels de perte d'accusé HTTP avant production restent obligatoires.

## Sauvegarde serveur confirmée et stockage local facultatif

Une fois la sauvegarde Supabase confirmée, l'effacement du brouillon local (`registre-consciences-draft-v1`) est désormais **best effort**. Un `SecurityError` du navigateur, une restriction des cookies ou un `localStorage` inaccessible ne peut plus faire basculer l'interface sur un faux message « Transmission impossible » ni réactiver le bouton de soumission. La réussite du dossier n'est déterminée que par la réponse du serveur; les problèmes locaux sont consignés sans exposition de réponses. Le contrat automatisé protège le comportement et le script est versionné `sinjira-character-registry.js?v=24.5.7`.


## Protection AAL2 obligatoire du questionnaire du Registre — 8 novembre 2026

Renforcement indépendant de la livraison Formspree : le point d’entrée serveur `submit-character-questionnaire` n’utilise plus la politique de vérification sensible pouvant être désactivée via `security_user_settings.sensitive_step_up`. Il appelle désormais `requiredVaultUser(req)`, qui vérifie le JWT réel puis les niveaux AAL `currentLevel`/`nextLevel` du facteur Auth Supabase; **AAL2 est obligatoire pour tous les participants, même si la préférence de vérification renforcée générale est désactivée**. Les sessions AAL1 et les comptes sans facteur validé sont refusés avant la lecture du questionnaire; les états de sécurité indisponibles entraînent un échec fermé. Le contrôle de propriété de la photo et l’unicité du personnage restent inchangés.

Côté navigateur, le Registre vérifie explicitement `auth.mfa.getAuthenticatorAssuranceLevel()` avant d’afficher le formulaire comme transmissible : vers `/compte/securite.html` si le facteur manque; vers `/compte/mfa.html` pour valider une session déjà équipée; échec sans transmission si le contrôle est indisponible. Le script public est versionné `sinjira-character-registry.js?v=24.5.8`. Des mutations négatives du validateur doivent faire échouer les tests si la garde serveur obligatoire est remplacée par `requiredUser(req)`.

Ce renforcement peut **bloquer les anciennes sessions AAL1** jusqu’à leur montée en AAL2; il ne supprime aucun dossier et ne publie aucune donnée. Déployer serveur et Web de façon coordonnée, après réussite de la CI de la PR de sécurité, sans diminuer l’exigence MFA pour une validation fictive.
## Condition bloquante supplémentaire : transport SMTP Supabase Auth en production (audit du 8 novembre 2026)

**IMPORTANT :** une page de confirmation publiée et un modèle `Confirm sign up` corrects ne prouvent pas que les nouveaux membres peuvent recevoir les courriels. Le transport de **Supabase Auth** est indépendant de **Formspree**. Formspree reçoit les avis facultatifs **après** validation du compte; il ne peut pas remplacer l’envoi initial du courriel d’activation.

Selon la documentation officielle Supabase du 31 octobre 2026, le SMTP intégré de Supabase est réservé aux adresses autorisées de l’équipe du projet, limité et non destiné à l’exploitation publique. La livraison d’un courriel de confirmation vers un utilisateur externe exige donc la **vérification d’un SMTP personnalisé déjà opérationnel** (ou sa mise en place avec accord explicite sur tout coût).

**Procédure de contrôle — à effectuer dans le tableau de bord Supabase, sans exposer de secret dans GitHub :**

1. Ouvrir **Authentication → SMTP Settings** (ou les paramètres d’envoi des courriels de la version actuelle du tableau de bord) et constater si **Custom SMTP** est activé. Ne jamais copier son mot de passe ni ses identifiants dans une issue, un commit ou un rapport de test.
2. Vérifier le nom d’hôte et le port du service, son domaine d’expédition vérifié, les protections SPF/DKIM/DMARC et le volume prévu. Ne pas supposer qu’un SMTP de test fonctionne pour des utilisateurs externes.
3. Confirmer séparément **Site URL**, **Redirect URLs** et le modèle **Confirm sign up**, qui dirige vers `/compte/confirmer.html#token_hash=…&type=email`. Tester que l’ouverture du courriel ne consomme pas le jeton : seul le clic volontaire sur le bouton de la page doit confirmer.
4. Créer un **compte fictif inédit avec une adresse de test contrôlée, non membre de l’équipe Supabase**, puis confirmer la réception effective du message, l’ouverture de la page et l’activation du compte. Conserver uniquement des résultats anonymisés : succès/échec, étape, horodatage, code d’erreur technique sans adresse ni jeton.
5. Tester le renvoi, un lien expiré, une connexion AAL1 puis la transition obligatoire AAL2 du Registre. Ne pas désactiver la MFA pour faire réussir l’essai.
6. Configurer indépendamment les deux workflows **Formspree**, vérifier `sinjiraofficiel@gmail.com` comme destination et utiliser une adresse de test pour prouver la **réception** du message. Un `2xx` ou une ligne `delivery_status='sent'` signifie seulement que Formspree a accepté l’envoi, pas que la boîte l’a reçu.
7. L’option **Auto Response** de Formspree demande **Professional ou Business**. Si aucun abonnement correspondant n’a été approuvé, ne pas activer de dépense; documenter clairement que l’accusé externe n’est pas disponible et que l’accusé **à l’écran** reste assuré seulement après sauvegarde confirmée.

**Seuil de mise en service :** maintenir l’état **NON CERTIFIÉ / 80 % estimés** tant que l’existence du SMTP opérationnel, les paramètres Auth, les workflows Formspree, le parcours d’un compte de test extérieur, l’authentification AAL2 et la livraison réelle des courriels ne sont pas constatés. Ne jamais transformer un test de l’interface en preuve de délivrabilité.

**Sources officielles :**
- Supabase Auth — SMTP de production : https://supabase.com/docs/guides/auth/auth-smtp
- Supabase Auth — modèles de courriel : https://supabase.com/docs/guides/auth/auth-email-templates
- Formspree — Auto Response : https://help.formspree.io/articles/plugins/sending-a-confirmation-or-response-email
- Formspree — forfaits et fonctionnalités : https://formspree.io/plans

**État lors de cet audit :** PR GitHub #834 déjà fusionnée; `notify-account-confirmation` v1 et `submit-character-questionnaire` v13 actives avec `verify_jwt=true`; aucun événement dans `public.sinjira_formspree_events`. La présence d’un SMTP personnalisé et la réception des courriels **n’ont pas pu être vérifiées** depuis les accès de cet audit. Aucune mise à jour des paramètres hébergés, aucun test d’envoi, aucun achat, aucune donnée réelle modifiée.

