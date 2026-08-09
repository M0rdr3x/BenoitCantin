# Installation — comptes joueurs SINJIRA

## 1. Créer Supabase

1. Créez un projet Supabase : `SINJIRA Players`.
2. Ouvrez **SQL Editor**.
3. Exécutez :
   `supabase/migrations/20260808_sinjira_players.sql`

Le script crée les tables, les index, les triggers, les politiques RLS et les fonctions serveur nécessaires.

## 2. Configurer l’authentification Supabase

Dans **Authentication > URL Configuration** :

Site URL :
`https://www.benoitcantin.com`

Redirect URLs à autoriser :
- `https://www.benoitcantin.com/compte/index.html`
- `https://www.benoitcantin.com/compte/reinitialiser-mot-de-passe.html`
- `https://www.benoitcantin.com/**`

Gardez la confirmation de courriel activée.

## 3. Copier les deux paramètres publics

Dans Supabase, récupérez :
- Project URL
- Publishable key

Modifiez :
`assets/js/sinjira-supabase-config.js`

Remplacez :
- `https://VOTRE-PROJET.supabase.co`
- `VOTRE_CLE_PUBLIQUE_SUPABASE`

**Ne mettez jamais la service_role key dans GitHub.**

## 4. Configurer Resend pour les rapports par courriel

1. Créez un compte Resend.
2. Vérifiez un domaine d’envoi, idéalement `benoitcantin.com`.
3. Créez une API key.

Dans les secrets Supabase Edge Functions ajoutez :

`RESEND_API_KEY=...`

`REPORT_FROM_EMAIL=SINJIRA <no-reply@benoitcantin.com>`

`REPORT_TEMPLATE_URL=https://www.benoitcantin.com/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fracture_du_Reseau_Mere_Fiche_Joueur_Web.pdf`

Les secrets restent dans Supabase, jamais dans GitHub.

## 5. Déployer les Edge Functions

Avec Supabase CLI :

```bash
supabase login
supabase link --project-ref VOTRE_PROJECT_REF
supabase functions deploy send-game-report --no-verify-jwt
supabase functions deploy submit-game-contribution
supabase functions deploy revoke-my-contributions
supabase functions deploy delete-player-account
supabase functions deploy admin-analytics
```

Le dossier `supabase/config.toml` documente aussi les réglages JWT.

## 6. Créer votre compte joueur administrateur

Après avoir activé les pages sur le site :

`https://www.benoitcantin.com/compte/inscription.html`

Créez votre propre compte et confirmez votre courriel.

Dans Supabase SQL Editor, ouvrez :
`supabase/ADMIN_ACTIVER_COMPTE.sql`

Remplacez `VOTRE_COURRIEL_ADMIN` par votre adresse de compte puis exécutez.

La page d’administration devient :
`https://www.benoitcantin.com/admin/sinjira-analytics.html`

## 7. Envoyer les fichiers dans GitHub

Décompressez l’archive à la racine de `M0rdr3x/BenoitCantin`.

Téléversez :
- `assets/`
- `compte/`
- `admin/`
- `projets/`
- `supabase/`

Le dossier `supabase/` peut rester dans le dépôt; il ne contient aucun secret.

Commit conseillé :

`Ajout du système complet de comptes joueurs SINJIRA`

## 8. Tests recommandés

### Invité
1. Ouvrir `fiche-web.html`.
2. Remplir quelques champs.
3. Vérifier que rien n’apparaît dans les tables Supabase.
4. Générer le PDF.
5. Envoyer le rapport à une adresse de test.
6. Fermer la page : aucune sauvegarde ne doit exister.

### Compte
1. Créer un compte.
2. Confirmer le courriel.
3. Commencer une partie.
4. Cliquer `Sauvegarder dans mon compte`.
5. Quitter et reprendre la partie.
6. Terminer la partie.
7. Télécharger et envoyer le rapport.

### Contribution
1. Activer le Programme Contributeur.
2. Sauvegarder une partie.
3. Cliquer `Partager cette partie avec SINJIRA`.
4. Vérifier que la table `internal_gameplay_contributions` contient les métriques mais pas le courriel/pseudo/code partie/notes privées.
5. Ouvrir l’admin analytics.

## Sécurité

Le navigateur utilise uniquement la Publishable key.
La base protège les lignes privées avec RLS.
Les tables `internal_*` ont RLS activé sans politique utilisateur.
Les opérations privilégiées passent par Edge Functions et la service_role key stockée uniquement dans Supabase.
