# Rapport d’audit professionnel — BenoitCantin PRO V14

## Résultat général

Le site fourni a été audité comme un site statique GitHub Pages avec intégration Supabase.

### Contrôles statiques
- 86 pages HTML analysées.
- 2 666 références HTML internes vérifiées.
- 0 lien ou ressource HTML interne manquant après correction.
- 0 ressource CSS manquante.
- 16 fichiers JavaScript vérifiés syntaxiquement : 0 erreur.
- 0 page avec problème de base détecté sur `lang`, `viewport`, `title`, `alt` d’image, liens `_blank` non sécurisés ou IDs dupliqués.
- 0 référence active à l’ancienne marque « L’Ère des consciences » dans le HTML/CSS/JS du portail principal.
- CNAME vérifié : `www.benoitcantin.com`.

## Corrections importantes apportées

### 1. Administration SINJIRA — erreur 404
Le dossier du site était `Admin/` avec une majuscule alors que les liens utilisent `/admin/sinjira/`. GitHub Pages est sensible à la casse.

Correction :
- création du chemin réel `admin/sinjira/index.html`;
- maintien de `Admin/` comme redirection de compatibilité;
- la page d’administration n’est plus censée tomber sur la 404.

### 2. Page 404 non stylée
Les ressources de `404.html` utilisaient des chemins relatifs. Lorsqu’une 404 se produisait dans un sous-dossier, le navigateur cherchait donc le CSS et les images dans le mauvais dossier.

Correction : CSS, images, navigation et JavaScript utilisent maintenant des chemins absolus à partir de la racine.

### 3. Pages parasites dans Projet Nova
Deux copies anciennes du portail principal étaient présentes dans :
- `projets/projet-nova/a-propos.html`
- `projets/projet-nova/univers.html`

Elles contenaient des chemins cassés et une ancienne structure. Elles ont été remplacées par des redirections propres vers les pages officielles du portail principal.

### 4. Continuer une partie Fracture
Le Compte SINJIRA utilisait encore l’ancien chemin de fiche pour reprendre une partie.

Correction : le bouton « Continuer » utilise maintenant le `party_code` et ouvre directement `partie.html?code=FRM-...`.

### 5. Photos de profil
Ajout d’une photo de profil pour tous les comptes SINJIRA, y compris le compte propriétaire.

Fonctionnement :
- JPG, PNG ou WebP;
- maximum 8 Mo avant traitement;
- minimum 160 × 160 px;
- recadrage carré automatique;
- optimisation à 512 × 512 px en WebP;
- affichage modéré : environ 168 px dans le profil, 112 px sur le tableau de bord et 64 px dans l’administration;
- possibilité de remplacer ou retirer la photo.

Le backend Supabase a déjà été configuré :
- colonne `profiles.avatar_path`;
- bucket `sinjira-avatars`;
- politiques d’écriture/suppression limitées au propriétaire du fichier;
- fonction privée `admin-users` déployée pour l’affichage administratif.

### 6. Administration unique
Vérification backend :
- 1 seul compte administrateur;
- `kingtyrano@gmail.com`;
- pseudo `AbyssTime`.

Le verrouillage administrateur existant reste en place.

### 7. SEO et confidentialité technique
- `robots.txt` bloque maintenant `/admin/`, `/Admin/` et `/compte/`;
- sitemap actualisé avec les principales pages publiques;
- les pages de compte et d’administration restent hors indexation.

## Limite de l’audit

Les contrôles statiques et backend ont été réalisés avant publication. Après téléversement sur GitHub Pages, un dernier contrôle visuel sur le domaine public est recommandé pour confirmer le cache navigateur/CDN, l’affichage mobile et les appels Supabase depuis le domaine réel.

Aucune anomalie statique bloquante n’est restante dans le package V14.
