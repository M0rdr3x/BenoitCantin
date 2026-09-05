# SINJIRA V25 — Durcissement Auth contre les mots de passe compromis

## Principe

**L’HUMAIN AVANT TOUT.** Ce changement protège les comptes contre la réutilisation de mots de passe déjà compromis sans collecter de nouvelle donnée personnelle dans SINJIRA et sans lire, journaliser ni modifier les mots de passe des utilisateurs.

## État observé avant activation

Le 2026-09-05, le Security Advisor Supabase production signale encore :

- `auth_leaked_password_protection`
- niveau `WARN`
- titre `Leaked Password Protection Disabled`

Les garde-fous RLS V25 sont déjà verrouillés séparément en CI et le Performance Advisor ne signale plus de clé étrangère non indexée. Ce réglage Auth hébergé est donc le dernier WARN de sécurité identifié dans cette phase.

Le même jour, la lecture connectée de l’organisation Supabase `glaxqwyumblfqmzusqbt` confirme :

- projet `gpvivleexywljowcqkru` : `ACTIVE_HEALTHY` ;
- région : `ca-central-1` ;
- plan de l’organisation : **`free`**.

La protection HIBP ne peut donc pas être activée dans l’état actuel du plan. Ce document et le workflow ne doivent jamais présenter l’activation comme terminée tant que l’organisation reste `free`.

## Référence Supabase

Supabase Auth permet de refuser les mots de passe connus comme compromis via l’API Pwned Passwords de HaveIBeenPwned.

Références :

- https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection
- Management API organisation : `GET /v1/organizations/{slug}`
- Management API Auth GET : `/v1/projects/{ref}/config/auth`
- Management API Auth PATCH : `/v1/projects/{ref}/config/auth`
- champ exact : `password_hibp_enabled`

Supabase indique que la protection contre les mots de passe compromis est disponible sur le plan **Pro et supérieur**. Les plans actuels correspondants sont Pro, Team et Enterprise.

Le workflow n’achète, ne change ni ne contourne aucun plan. Il lit seulement le plan courant et s’arrête avant toute opération Auth si le plan n’est pas explicitement éligible.

## Workflow de production

Fichier : `.github/workflows/sinjira-v25-auth-password-hardening.yml`

Le workflow est exclusivement `workflow_dispatch`, utilise l’environnement GitHub `production` et exige la confirmation exacte :

`ENABLE-SINJIRA-V25-LEAKED-PASSWORD-PROTECTION`

Le secret utilisé est uniquement `SUPABASE_ACCESS_TOKEN`, déjà réservé aux appels Management API du projet production `gpvivleexywljowcqkru`.

### Préflight 0 — éligibilité du plan

Avant même de lire `/config/auth`, le workflow :

1. lit `GET /v1/organizations/glaxqwyumblfqmzusqbt` ;
2. extrait uniquement le champ `plan` ;
3. autorise uniquement `pro`, `team` ou `enterprise` ;
4. échoue immédiatement pour `free`, valeur absente ou valeur inconnue ;
5. n’exécute alors aucun PATCH Auth.

**État actuel : cette étape doit échouer sur `plan='free'`.** Il n’est donc pas pertinent de déclencher le workflow tant que le plan reste inchangé.

### Préflight Auth

Seulement après éligibilité du plan, le workflow :

1. lit `/config/auth` sans afficher le document complet ;
2. exige `password_min_length >= 12` ;
3. exige que `password_hibp_enabled` soit un booléen ;
4. calcule une empreinte SHA-256 de toute la configuration Auth **hors** `password_hibp_enabled` ;
5. devient idempotent si HIBP est déjà activé.

Aucun secret Auth contenu dans la réponse n’est imprimé dans les logs.

### Écriture autorisée

Une seule écriture est autorisée :

```json
{"password_hibp_enabled":true}
```

Aucun autre champ Auth n’est envoyé. Le workflow ne modifie notamment pas :

- le plan ou la facturation Supabase ;
- la longueur minimale des mots de passe ;
- les caractères obligatoires ;
- les fournisseurs OAuth ;
- MFA ;
- CAPTCHA ;
- SMTP/SMS ;
- les secrets ou clés API ;
- les mots de passe ou enregistrements d’utilisateurs.

Il n’exécute aucune migration, requête SQL de production ou Edge Function.

### Postflight

Après le PATCH, le workflow :

1. relit `/config/auth` ;
2. exige `password_hibp_enabled=true` ;
3. confirme que `password_min_length` reste au moins 12 ;
4. recalcule l’empreinte de tous les autres paramètres et exige qu’elle soit identique au préflight ;
5. interroge le Security Advisor jusqu’à six fois, avec un intervalle de 10 secondes, et exige la disparition de `auth_leaked_password_protection`.

Si un autre paramètre Auth change pendant l’opération, le workflow échoue et **ne tente pas de rollback automatique**, afin de ne pas écraser une modification concurrente légitime.

## Effet attendu pour les utilisateurs

L’activation ne révèle pas les mots de passe à SINJIRA. Supabase utilise le mécanisme Pwned Passwords pour identifier les mots de passe compromis et appliquer sa politique Auth.

D’après la documentation Supabase, le renforcement des exigences peut affecter la création de compte, les changements de mot de passe et certains flux d’authentification lorsqu’un mot de passe est considéré faible ou compromis. Pour cette raison, l’activation reste une action production explicite et manuelle plutôt qu’un effet automatique d’une PR.

## Incident et retour arrière

Un retour arrière ne doit être envisagé qu’en cas d’incident de connexion réellement constaté et documenté.

Le retour arrière technique correspondant serait un PATCH borné de `password_hibp_enabled` vers `false`, après lecture préalable de la configuration actuelle. Il ne faut jamais restaurer un ancien document Auth complet : cela risquerait d’écraser des changements concurrents.

Aucun rollback de base de données n’est pertinent, car ce réglage n’est pas une migration SQL.

## Vérification après activation

Une activation n’est considérée terminée que lorsque :

- le plan de l’organisation est Pro, Team ou Enterprise ;
- `/config/auth` renvoie `password_hibp_enabled=true` ;
- `password_min_length >= 12` ;
- les autres paramètres Auth n’ont pas changé durant l’opération ;
- le Security Advisor ne contient plus `auth_leaked_password_protection`.

Tant que le plan reste `free`, le WARN est un **blocage de capacité hébergée connu et documenté**, pas une permission de contourner la sécurité ou de modifier d’autres réglages.
