# Installation — Compte SINJIRA universel v2

## 1. Choisir votre cas

### Nouveau projet Supabase
Dans Supabase > SQL Editor, exécutez :

`supabase/INSTALLATION_COMPLETE.sql`

### Système v1 déjà installé
Exécutez uniquement :

`supabase/migrations/20260809_sinjira_universal_platform.sql`

---

## 2. Authentication > URL Configuration

Site URL :

`https://www.benoitcantin.com`

Redirect URLs :

- `https://www.benoitcantin.com/compte/index.html`
- `https://www.benoitcantin.com/compte/reinitialiser-mot-de-passe.html`
- `https://www.benoitcantin.com/**`

Gardez la confirmation du courriel activée.

---

## 3. Relier le site à Supabase

Dans :

`assets/js/sinjira-supabase-config.js`

remplacez :

`https://VOTRE-PROJET.supabase.co`

et :

`VOTRE_CLE_PUBLIQUE_SUPABASE`

par votre **Project URL** et votre **Publishable Key**.

Ne mettez jamais de secret key / service_role key dans GitHub.

---

## 4. Déployer les Edge Functions

```bash
supabase login
supabase link --project-ref VOTRE_PROJECT_REF

supabase functions deploy send-game-report --no-verify-jwt
supabase functions deploy get-document-url --no-verify-jwt
supabase functions deploy submit-game-contribution
supabase functions deploy revoke-my-contributions
supabase functions deploy delete-player-account
supabase functions deploy admin-analytics
supabase functions deploy admin-console
```

---

## 5. Rapports par courriel

Conservez la configuration Resend :

Secrets Supabase :
- `RESEND_API_KEY`
- `REPORT_FROM_EMAIL`
- `REPORT_TEMPLATE_URL`

Ces secrets restent dans Supabase.

---

## 6. Activer votre compte administrateur

Créez d'abord votre Compte SINJIRA :

`https://www.benoitcantin.com/compte/inscription.html`

Confirmez le courriel.

Ensuite exécutez :

`supabase/ADMIN_ACTIVER_COMPTE.sql`

après avoir remplacé `VOTRE_COURRIEL_ADMIN`.

Administration :

`https://www.benoitcantin.com/admin/sinjira/`

---

## 7. Documents privés

Le SQL crée automatiquement le bucket privé :

`sinjira-private-documents`

Ne rendez jamais ce bucket public.

Depuis l'administration :
1. choisissez le projet;
2. entrez le titre et la version;
3. choisissez le niveau d'accès;
4. sélectionnez le fichier;
5. choisissez En révision ou Approuvé;
6. téléversez.

Le fichier n'est pas exposé dans GitHub Pages.

---

## 8. Niveaux d'accès

### Compte joueur
Tout utilisateur connecté voit les projets `visibility=account` et les documents `access_level=account`.

### Joueur approuvé
L'administration accorde `project_access=player`.

### Testeur
L'administration accorde `project_access=tester`, directement, après une demande, ou lors de l'approbation d'un playtest.

### Administration
Déterminée par `internal_admin_users`.

### Contributeur
Consentement volontaire séparé, géré par `research_consents`.

---

## 9. Test de sécurité recommandé

1. Créez un compte joueur normal.
2. Ajoutez un PDF privé avec accès `tester`.
3. Vérifiez qu'il n'apparaît pas pour ce compte.
4. Faites une demande testeur.
5. Approuvez-la dans l'administration.
6. Rechargez `/compte/documents.html`.
7. Vérifiez que le PDF devient visible.
8. Ouvrez-le et vérifiez que l'URL Supabase est temporaire.
9. Copiez cette URL, attendez l'expiration, puis vérifiez qu'elle ne fonctionne plus.

---

## 10. GitHub

Cette archive est un **overlay** pour le dépôt existant.

Décompressez-la à la racine de :

`M0rdr3x/BenoitCantin`

Téléversez tous les dossiers contenus dans l'archive et acceptez les remplacements.

Commit conseillé :

`Ajout du Compte SINJIRA universel et des documents protégés`

Le téléversement de cette archive ne doit pas supprimer Lumina, Futurax, Chroniques ou Projet Nova.
