# SINJIRA™ V24.5.48 — Confidentialité des réponses Edge

## Objectif

Durcir deux Edge Functions publiques/custom-auth sans modifier leur rôle métier ni activer de fournisseur externe :

- `get-document-url` ;
- `send-game-report`.

Le ledger Supabase reste volontairement à **174 migrations**. Cette version ne modifie pas le schéma de base de données.

## `get-document-url`

La fonction reste en `verify_jwt=false` parce qu’elle doit pouvoir servir un document explicitement public. L’accès protégé continue cependant à utiliser `optionalUser`, `project_access_rank` et les rangs d’accès.

Durcissements V24.5.48 :

- taille réelle du corps limitée à 8 KiB, même si `Content-Length` est absent ou mensonger ;
- `document_id` validé comme UUID avant la requête ;
- lecture SQL minimisée aux champs nécessaires ;
- document obligatoirement `approved` ;
- projet obligatoirement `active` ;
- URL relative autorisée seulement sous forme `/chemin` et jamais `//hôte` ;
- URL absolue autorisée seulement en HTTPS ;
- les URL signées Storage restent limitées à 600 secondes ;
- toutes les réponses JSON portent `Cache-Control: private, no-store, max-age=0`, `Pragma: no-cache`, `X-Content-Type-Options: nosniff` et `Referrer-Policy: no-referrer`.

Les 5 documents externes approuvés existants utilisent actuellement des chemins relatifs SINJIRA et restent compatibles.

## `send-game-report`

Le téléchargement PDF anonyme reste disponible comme auparavant. Le courriel externe reste préparé mais **désactivé** par :

```text
PAID_EXTERNAL_SERVICES_ENABLED=false
```

Durcissements V24.5.48 :

- la limite de 220 000 octets est vérifiée sur le corps réellement reçu, pas seulement sur `Content-Length` ;
- JSON invalide rejeté avant génération du PDF ;
- le PDF base64 et les erreurs associées sont toujours servis avec `private, no-store` ;
- `Referrer-Policy: no-referrer` et `nosniff` sont forcés ;
- la journalisation d’une session reste limitée à une session appartenant au compte authentifié ;
- l’intégration Resend demeure derrière le verrou payant à `false`.

## Coûts et services externes

V24.5.48 n’active :

- aucun paiement ;
- aucun checkout ;
- aucune vente ;
- aucun transporteur ;
- aucun courriel/SMS payant ;
- aucune IA distante payante ;
- aucun nouveau fournisseur externe facturable.

## Advisors

Les INFO `RLS Enabled No Policy` sur les tables volontairement scellées et les INFO `unused_index` ne sont pas « corrigés » artificiellement. `Leaked Password Protection` reste une fonctionnalité Supabase payante et n’est pas activée sans autorisation explicite.
