# Alias secondaires vers les hubs natifs V25

## Objectif

Plusieurs pages du compte SINJIRA sont des vues secondaires d’un domaine déjà protégé par un hub React Native. Créer un nouveau hub pour chacune dupliquerait les frontières de sécurité et augmenterait inutilement la surface mobile.

Cette étape fait donc converger uniquement des **intentions de navigation** vers des hubs déjà validés. Elle ne charge aucune donnée de ces pages et ne change aucune règle serveur.

**L’HUMAIN AVANT TOUT.**

## Convergences fermées

### Messages

- `/compte/messages-reels.html` → `NativeMessagesHub`;
- `/compte/messages-personnage.html` → `NativeMessagesHub`.

Une entrée secondaire revient d’abord au sas Messages : le natif ne mémorise pas une identité de messagerie et ne déduit pas si la personne veut écrire avec son compte réel ou son personnage.

### Bibliothèque

- `/compte/mes-lectures.html` → `NativeLibraryHub`;
- `/compte/documents.html` → `NativeLibraryHub`;
- `/compte/playtests.html` → `NativeLibraryHub`.

Lectures et documents étaient déjà des destinations Web du hub Bibliothèque. Playtests y est ajouté comme destination explicite, sans importer candidatures, invitations, participations, niveau d’accès, âge, tuteur, cohorte jeunesse ou décision administrative.

### Jeux

- `/compte/contributions.html` → `NativeGamesHub`.

Le Programme Contributeur reste volontaire. Le hub ne lit ni le choix de participation, ni l’autorisation de texte libre, ni la demande de retrait des contributions précédentes. Il ne transmet aucune sauvegarde ou statistique de partie.

### Communauté et protections sociales

- `/compte/mes-commentaires.html` → `NativeCommunityHub`;
- `/compte/blocages.html` → `NativeCommunityHub`;
- `/compte/regles-communaute.html` → `NativeCommunityHub`;
- `/compte/moderation.html` → `NativeCommunityHub`.

Ces routes ne déplacent aucune action sociale dans React Native. Le hub ne lit ni contenu ou état de commentaire, ni liste de comptes bloqués, ni acceptation des règles, ni dossier de modération.

Pour les appels, le natif ne reçoit aucun identifiant de décision, règle appliquée, exposé des motifs, durée, date limite, texte d’appel, statut, motif de révision ou urgence. Il ne soumet et ne tranche aucun appel. La décision motivée, l’appel gratuit, l’échéance serveur et la **révision humaine obligatoire** restent dans la surface Web/serveur V24.4.90.

Les sorties explicites du hub utilisent :

- `/compte/mes-commentaires.html?surface=web`;
- `/compte/blocages.html?surface=web`;
- `/compte/regles-communaute.html?surface=web`;
- `/compte/moderation.html?surface=web`.

Messages et Rencontres utilisent aussi `?surface=web` pour Blocages et Règles afin qu’un choix volontaire d’action Web ne reboucle pas vers le sas Communauté.

### Personnage

- `/compte/mes-personnages.html` → `NativeCharacterHub`.

Cette ancienne page ne contient qu’une redirection vers `mon-personnage.html`. Le routeur converge donc vers le même sas natif sans créer une seconde identité personnage.

### Vie privée et paramètres

- `/compte/vie-privee.html` → `NativePrivacyHub`;
- `/compte/parametres.html` → `NativeSettingsHub`.

Ces hubs existaient déjà et conservent leurs frontières : aucune demande Vie privée, préférence, export ou suppression de compte n’est traitée localement.

## Pages volontairement hors alias

Les chemins suivants ne sont pas ajoutés à `NATIVE_MODULE_PATHS` :

- `/compte/registre-personnel.html` : garde biométrique/MFA/risque historique, contenu extrêmement sensible;
- `/compte/securite.html` et Mode Voyage : `NativeSecurityHub` et surface Web/serveur dédiés;
- `/compte/mfa.html` : étape d’authentification forte;
- `/compte/connexion.html`, `/compte/inscription.html`, `/compte/mot-de-passe-oublie.html`, `/compte/reinitialiser-mot-de-passe.html` : flux d’authentification;
- `/compte/signaler-deces.html` : procédure sensible de vérification du décès;
- `/compte/projet.html` : vue contextuelle/dynamique d’un projet, qui reste dans la navigation Web de la Bibliothèque;
- `/compte/confidentialite-joueur.html` : page d’information de confidentialité, lisible directement sur le Web.

## Frontière technique

`NativeModuleRouter` continue de recevoir uniquement :

- un chemin de la liste fermée `NATIVE_MODULE_PATHS`;
- `onOpenPath`;
- `onBack`.

Aucun alias n’ajoute de `user`, session, contenu, profil, rôle, consentement, candidature, invitation, progression, commentaire, statut de modération, décision, appel ou donnée jeunesse dans les props. Le routeur ne fait aucun appel réseau et n’utilise aucun stockage local.

Les sorties explicites des hubs vers les pages réelles utilisent `?surface=web` lorsque la destination est une surface privée Web. Ainsi, choisir une action Web ne reboucle pas automatiquement vers le sas natif.

## Principe

**PROTÉGER SANS SURVEILLER.** Une route secondaire sert seulement à choisir le bon sas. Elle ne devient jamais un raccourci pour copier l’état privé du module dans l’application native.
