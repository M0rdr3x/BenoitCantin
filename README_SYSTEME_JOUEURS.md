# SINJIRA — système de comptes joueurs v1

Cette archive construit le socle complet demandé pour **Fracture du Réseau-Mère** :

- mode invité sans sauvegarde serveur;
- compte joueur avec courriel + mot de passe;
- confirmation de courriel;
- récupération de mot de passe;
- profil joueur;
- sauvegardes volontaires de parties;
- reprise des parties;
- fiche joueur web reprenant les champs du PDF officiel;
- PDF direct toujours disponible;
- génération d’un PDF rempli à partir de la fiche web;
- téléchargement du rapport;
- envoi facultatif du rapport au courriel du joueur;
- Programme Contributeur SINJIRA;
- partage volontaire, par partie;
- exclusion des identifiants personnels des données d’analyse;
- possibilité de retirer les contributions reliées au compte;
- retour de fin de partie;
- données utilisables pour équilibrage et futures extensions;
- page d’analyse administrateur;
- export des données du joueur;
- suppression du compte.

## Important

Les fichiers sont construits, mais **les comptes ne pourront pas fonctionner tant que vous n’avez pas créé le projet Supabase et ajouté ses deux paramètres publics** dans :

`assets/js/sinjira-supabase-config.js`

Il faut aussi configurer Resend pour l’envoi de rapports par courriel.

Consultez `INSTALLATION_SUPABASE_ET_RESEND.md`.
