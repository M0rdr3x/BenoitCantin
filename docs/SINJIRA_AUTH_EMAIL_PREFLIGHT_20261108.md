# SINJIRA — Prévol Auth et courriels en lecture seule (8 novembre 2026)

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

Le diagnostic des paramètres **privés** demeure manuel et protégé : `Run workflow` → `main` → `PREFLIGHT-READ-ONLY` → approbation `production` si applicable. Il ne crée aucun utilisateur ni courriel et ne modifie pas les paramètres Auth. Il faut toujours confirmer séparément la réception Formspree et le parcours TOTP AAL2 réel.

## État opérationnel actualisé — 8 novembre 2026

Le score de suivi du correctif inscription/confirmation/Registre/Formspree est **84 % estimés** ; les 16 % non validés se décomposent en **Auth privée / SMTP (3 points)**, **configuration et réception réelle Formspree (3 points)** et **parcours complet avec compte fictif et TOTP AAL2 (10 points)**. La confirmation d'un compte dans `auth.users` ne prouve pas à elle seule la réception d'un courriel. Le Registre exige **toujours AAL2**, indépendamment de `sensitive_step_up`. Les versions actives sont `submit-character-questionnaire` v15 et `notify-account-confirmation` v2 avec JWT obligatoire.

Le workflow Auth exige l'entrée `PREFLIGHT-READ-ONLY`, une exécution sur `main`, le secret GitHub protégé `SUPABASE_ACCESS_TOKEN` et l'approbation de l'environnement de production. Ne pas lancer un contrôle utilisant des secrets privés hors de cet environnement, ni enregistrer ou afficher le jeton dans un rapport. La preuve de remise réelle doit provenir du fournisseur et de la boîte de test, pas d'un simple HTTP 200.

La [PR #891](https://github.com/M0rdr3x/BenoitCantin/pull/891) a corrigé la redirection de compte `next=//hôte`; le script public est maintenant observé avec `safeLocalNavigation`. La sécurité générale de l'hébergement reste un dossier distinct. Les données et preuves finales sont suivies dans [#850](https://github.com/M0rdr3x/BenoitCantin/issues/850). Aucun forfait payant ne doit être activé sans consentement du propriétaire.
