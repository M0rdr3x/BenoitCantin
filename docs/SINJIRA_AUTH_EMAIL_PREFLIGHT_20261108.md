# SINJIRA — Prévol Auth et courriels en lecture seule (8 novembre 2026)

Objectif : réduire les 20 % restants du correctif SINJIRA en vérifiant la
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

Le correctif global reste estimé à 80 % tant que les résultats de ce
prévol et les courriels réellement reçus ne sont pas constatés.
