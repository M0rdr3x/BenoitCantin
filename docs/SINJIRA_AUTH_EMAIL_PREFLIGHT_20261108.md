# SINJIRA — Prévol Auth et courriels en lecture seule (8 novembre 2026)

## État vérifié et procédure de clôture — 9 novembre 2026

**Périmètre : correctif inscription / confirmation / notifications Formspree /
Registre, et non l'intégralité du programme SINJIRA.**

**Avancement : 84 % estimés, 16 points non certifiés.** Les deux fonctions
Supabase actives en production sont `notify-account-confirmation` **v4**
et `submit-character-questionnaire` **v17**, toutes deux avec
`verify_jwt=true`. Les correctifs Formspree #918 et #920 ont été fusionnés
et redéployés ; le journal `sinjira_formspree_events` n'a **aucun événement**,
aucun facteur TOTP n'a le statut `verified` et aucun compte n'a le consentement
facultatif `formspree_receipt_opt_in=true`. Les **0 avis** enregistrés ne
prouvent donc pas à eux seuls une panne de transport. L'historique GitHub
Actions accessible ne comporte **aucun déclenchement manuel**
`workflow_dispatch` des prévols. Ce constat est une photographie du 9 novembre
et doit être revérifié au moment du sign-off.

### Ordre de travail pour atteindre réellement 100 %

- [ ] **Jalon A — 3 points : paramètres SMTP privés et courriel Auth reçu.**
  Depuis [GitHub Actions — prévol Auth](https://github.com/M0rdr3x/BenoitCantin/actions/workflows/sinjira-auth-email-production-preflight.yml),
  sélectionner `Run workflow`, la branche `main`, entrer exactement
  `PREFLIGHT-READ-ONLY`, puis approuver l'environnement `production` selon
  les règles du dépôt. **Avant le lancement**, s'assurer que cet environnement
  dispose du secret `SUPABASE_ACCESS_TOKEN` autorisé en lecture de la
  configuration Auth. L'existence de ce secret n'a pas pu être certifiée avec
  l'accès de lecture disponible. Aucun token ne doit figurer dans les rapports.
  Exiger **13 contrôles PASS, 0 ÉCHEC** ; les avertissements sans secret/SMTP
  sont attendus. Le prévol exige aussi **un seul usage du jeton de confirmation
  dans le modèle HTML**, exclusivement dans le lien HTTPS prévu : un second
  jeton dans une image, un autre lien, un commentaire ou un texte crée un
  échec, même si le bon lien existe. Les liens de pied de page sans jeton
  restent acceptés. Le prévol rejette aussi un lien de confirmation placé
  dans un élément HTML masqué (`hidden`, `inert`, `aria-hidden`,
  `display:none`, `visibility:hidden` ou `<template>`). Un lien visible
  après un bloc masqué demeure acceptable. Le prévol refuse également un
  `<a href>` vide ou dont le seul libellé est masqué : le lien doit avoir
  du texte visible, y compris dans un élément enfant, ou une image porteuse
  d'un attribut `src` et d'un `alt` non vide. Un commentaire HTML et une
  image décorative ne suffisent pas. Ce contrôle statique ne peut pas
  analyser toutes les feuilles de style et **n'atteste pas la livraison**.
  Puis confirmer **dans une boîte de test contrôlée** qu'un
  courriel Auth de confirmation a effectivement été reçu et qu'un clic
  volontaire sur le bouton réussit. Le prévol seul **ne suffit pas**.

- [ ] **Jalon B — 3 points : réception Formspree avec consentement.**
  Vérifier depuis le tableau de bord privé des formulaires
  `xzeeqynp` (confirmation de compte) et `mrppvrwa` (Registre) que le
  Workflow est activé et que son destinataire vérifié est bien
  `sinjiraofficiel@gmail.com`. Utiliser un compte de test volontairement
  consentant ; confirmer son adresse via le courriel Auth, puis contrôler
  **un** événement `sent` dans `sinjira_formspree_events` **et l'arrivée
  réelle du message dans la boîte officielle**. Un HTTP 2xx ou une ligne
  `sent` seuls n'attestent pas cette réception. Un autre compte de test,
  **sans opt-in**, ne doit provoquer ni avis ni ligne dans le journal.
  Ne jamais forcer un consentement pour obtenir un résultat vert.

- [ ] **Jalon C — 10 points : parcours authentifié complet.** Avec les mêmes
  comptes fictifs et des réponses de questionnaire fictives, vérifier
  inscription → réception Auth → clic de confirmation → connexion → inscription
  TOTP dans `/compte/securite.html` → **vérification réelle du facteur et
  `currentLevel=aal2`** → Registre → sauvegarde observable dans
  `character_submissions` → comportement idempotent et absence de doublon.
  Le module `v24-security.js?v=24.4.70` ne doit annoncer « TOTP activée »
  que si `challengeAndVerify()` retourne une session avec `access_token`
  et que `getAuthenticatorAssuranceLevel()` confirme `currentLevel=aal2`.
  Un résultat ambigu, `aal1` ou une erreur d'assurance restent **non certifiés**.
  Ces tests hors ligne ne remplacent pas la vérification AAL2 réelle.
  Ne pas désactiver AAL2, le JWT ni les contrôles de consentement. Prévoir une
  suppression documentée des données de test selon les droits autorisés.

- [ ] **Contrôle supplémentaire de publication.** Sur `main`, exécuter
  [le prévol public en lecture seule](https://github.com/M0rdr3x/BenoitCantin/actions/workflows/sinjira-public-release-parity.yml)
  avec `PUBLIC-GET-ONLY`. Les pages de confirmation et d'inscription chargent
  désormais respectivement `sinjira-confirm-email.js?v=4` et
  `v24-signup.js?v=24.5.6`, pour contourner les anciens caches après
  les correctifs de sécurité. Le renvoi d'un courriel de confirmation est
  désormais protégé contre les requêtes concurrentes même au clavier.
  Cette révision utilise un accusé d'inscription
  **neutre** : le SDK Auth peut retourner un utilisateur masqué si l'adresse
  existe déjà, donc même un `user.id` n'atteste pas qu'un nouveau compte
  a été créé ni qu'un courriel SMTP a été reçu. Le contrat CI refuse le retour aux anciennes
  révisions ; seule une inspection du site publié confirme la livraison.
  Le prévol public vérifie également la présence d'une **unique vraie
  balise `<script>`** pour chaque module critique, avec `src` local exact
  et `type=module` ; un commentaire, un texte, un script externe ou un
  doublon ne peuvent pas faire réussir artificiellement ce contrôle.
  Les quatre scripts JS publics ont déjà été comparés
  sans divergence à GitHub `main` le 9 novembre ; ce workflow permet de
  recontrôler la version publiée après un déploiement. À partir de la PR de
  contrôle TOTP, un **cinquième script** (`assets/js/v24-security.js`) est
  comparé octet par octet, pour déceler une ancienne version de la vérification
  MFA. Le contrôle porte alors sur **5 JS + 3 pages = 8 GET anonymes**. Le
  script privé de la page sécurité ne nécessite aucune connexion pour ce
  contrôle de parité, et la page HTML protégée n'est pas consultée.
  **Cette parité ne prouve ni la réception SMTP, ni un facteur TOTP réellement
  vérifié, ni une session AAL2.**

**Décision de fin :** ne déclarer le correctif **100 % terminé** que si les
jalons A, B et C ont des résultats datés et vérifiables, sans publier les
adresses de test, les codes TOTP, les jetons, les réponses privées du Registre
ou le contenu des courriels. Si un jalon échoue, relever uniquement le nom de
son contrôle, son état PASS/ÉCHEC et un lien vers l'exécution protégée.
Une date de fin ne peut pas être annoncée avant ces preuves.

**Source de suivi :** [issue #850](https://github.com/M0rdr3x/BenoitCantin/issues/850).
Les sections ci-dessous documentent l'évolution historique depuis le 8 novembre ;
leurs références `v15` et `v2` ne sont pas les versions actuellement déployées.


Objectif : réduire les 16 % restants du correctif SINJIRA en vérifiant la
configuration Auth hébergée sans envoyer de message ni changer les réglages.

## Utilisation

Ouvrir GitHub Actions :
https://github.com/M0rdr3x/BenoitCantin/actions/workflows/sinjira-auth-email-production-preflight.yml

Sélectionner Run workflow puis main. Saisir PREFLIGHT-READ-ONLY exactement.
L'environnement GitHub production doit posséder SUPABASE_ACCESS_TOKEN avec
un accès restreint à auth_config_read (Management API Supabase). Ne jamais
copier ce secret ni les modèles HTML Auth dans le chat ou les logs.

La lecture GET /v1/projects/{ref}/config/auth contrôle le Site URL,
le fournisseur Email, le refus de confirmation automatique, la redirection
permise, le modèle utilisant le fragment #token_hash et {{ .TokenHash }},
le sujet de confirmation, la disponibilité TOTP et 12 caractères minimum.
Les sorties ne révèlent que les noms des contrôles et PASS ou ÉCHEC.

## Limites

Ce workflow est exclusivement READ-ONLY. Il ne change aucun paramètre de
Supabase Auth, ne crée aucun utilisateur et n'envoie aucun email.
Il ne prouve pas la réception des notifications à sinjiraofficiel@gmail.com.
Cette preuve doit être vérifiée depuis Formspree avec un compte fictif,
un consentement explicite et un contrôle de l'accusé de réception.

Le forfait Supabase Free a été confirmé le 8 novembre 2026. La protection
contre les mots de passe compromis reste indisponible sur cette offre;
un workflow sécurisé distinct existe pour une future offre Pro+ :
.github/workflows/sinjira-v25-auth-password-hardening.yml.
Ne pas déclencher de paiement sans autorisation.

Références :
https://supabase.com/docs/reference/api/v1-get-auth-service-config
https://supabase.com/docs/guides/auth/auth-email-templates

Le correctif global reste estimé à 84 % tant que les résultats de ce
prévol et les courriels réellement reçus ne sont pas constatés.

## Fiabilisation du contrôle Auth — 8 novembre 2026

Le prévol GitHub Actions ne télécharge plus Python 3.12.14 auprès de `actions/python-versions` : cette distribution externe générait des erreurs réseau 504 dans plusieurs jobs de production. Les deux jobs utilisent le Python 3.12 déjà présent sur `ubuntu-24.04` et **échouent** s'il n'est pas en version 3.12. Les assertions de sécurité de `scripts/preflight_sinjira_auth_email.py --self-test` exigent les deux contrôles Python, l'environnement `production`, la branche `main`, l'événement manuel et le secret déjà présent, sans jamais imprimer sa valeur. Aucune règle de validation Auth n'a été désactivée.

## Vérification SMTP personnalisée — révision du 8 novembre 2026

Le prévol en lecture seule vérifie maintenant **13 contrats Auth** (au lieu de 9), dont quatre exigences explicitement SMTP fondées sur les champs présents dans le `GET /v1/projects/{ref}/config/auth` de Supabase :

- Un `smtp_host` non vide et différent d'une cible de développement locale.
- Un `smtp_port` numérique valide (1 à 65535), accepté comme entier ou texte.
- Une `smtp_admin_email` syntaxiquement plausible, sans exposer son adresse dans le résultat du workflow.
- Un `smtp_user` renseigné, sans afficher sa valeur.

**Frontière de vérification :** la présence de ces champs **ne prouve pas** l'exactitude du mot de passe SMTP, la validation du domaine émetteur, les quotas, l'acceptation par le serveur externe ou l'arrivée d'un courriel. Le workflow ne lit pas `smtp_pass` comme preuve de succès, ne produit aucune valeur privée et n'envoie aucun message. Il ajoute un avertissement permanent de validation par véritable réception dans une boîte de test. Un contrôle SMTP échoué garde le jalon « SMTP Auth : 3 % » **non certifié** ; un contrôle réussi ne le clôture pas sans preuve de délivrabilité.

Les autocontrôles du script couvrent les valeurs absentes, le port invalide et les noms d'hôte locaux. Aucun fournisseur payant, accès Production ou secret n'est ajouté par cette modification.

Le diagnostic des paramètres **privés** demeure manuel et protégé : `Run workflow` → `main` → `PREFLIGHT-READ-ONLY` → approbation `production` si applicable. Il ne crée aucun utilisateur ni courriel et ne modifie pas les paramètres Auth. Il faut toujours confirmer séparément la réception Formspree et le parcours TOTP AAL2 réel.

## État opérationnel actualisé — 8 novembre 2026

Le score de suivi du correctif inscription/confirmation/Registre/Formspree est **84 % estimés** ; les 16 % non validés se décomposent en **Auth privée / SMTP (3 points)**, **configuration et réception réelle Formspree (3 points)** et **parcours complet avec compte fictif et TOTP AAL2 (10 points)**. La confirmation d'un compte dans `auth.users` ne prouve pas à elle seule la réception d'un courriel. Le Registre exige **toujours AAL2**, indépendamment de `sensitive_step_up`. Les versions actives sont `submit-character-questionnaire` v15 et `notify-account-confirmation` v2 avec JWT obligatoire.

Le workflow Auth exige l'entrée `PREFLIGHT-READ-ONLY`, une exécution sur `main`, le secret GitHub protégé `SUPABASE_ACCESS_TOKEN` et l'approbation de l'environnement de production. Ne pas lancer un contrôle utilisant des secrets privés hors de cet environnement, ni enregistrer ou afficher le jeton dans un rapport. La preuve de remise réelle doit provenir du fournisseur et de la boîte de test, pas d'un simple HTTP 200.

La [PR #891](https://github.com/M0rdr3x/BenoitCantin/pull/891) a corrigé la redirection de compte `next=//hôte`; le script public est maintenant observé avec `safeLocalNavigation`. La sécurité générale de l'hébergement reste un dossier distinct. Les données et preuves finales sont suivies dans [#850](https://github.com/M0rdr3x/BenoitCantin/issues/850). Aucun forfait payant ne doit être activé sans consentement du propriétaire.
