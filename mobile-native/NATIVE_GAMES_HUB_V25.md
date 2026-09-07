# Hub Mes parties natif V25

## Objectif

`NativeGamesHub` est un sas React Native de navigation uniquement. Il permet d’atteindre les surfaces de jeu existantes sans copier les sauvegardes privées dans l’application native.

**L’HUMAIN AVANT TOUT.** Une sauvegarde de jeu peut contenir un historique détaillé, des décisions et des feuilles privées. Le natif n’en a pas besoin pour orienter la personne.

## Props minimales

Le composant reçoit seulement :

- `onOpenPath` pour ouvrir explicitement une destination existante;
- `onBack` pour revenir à l’Accueil natif.

Il ne reçoit aucun utilisateur, session, jeu, code de partie, statut, compteur, feuille, résultat, fichier ou historique.

## Aucune donnée de partie locale

Le hub ne lit et ne mémorise pas :

- les lignes `game_sessions`;
- le titre, le statut ou la date de mise à jour d’une partie;
- le jeu ou projet associé;
- le code de partie;
- le nombre de joueurs;
- le mode de jeu;
- la durée;
- les feuilles `player_sheets`;
- les feuilles `endgame_sheets`.

La Web et le serveur restent la source de vérité des sauvegardes.

## Exports privés

La surface Web peut produire volontairement une sauvegarde privée au format `SINJIRA_GAME_SAVE_V1`. Cette exportation peut contenir la session, les feuilles de joueur et les feuilles de fin de partie.

Le hub natif ne crée aucun Blob, ne fabrique aucun JSON de sauvegarde, ne déclenche aucun téléchargement, ne partage aucun fichier et ne met aucune sauvegarde en cache.

## Imports

L’import reste une action Web explicite. Le hub natif :

- ne sélectionne aucun fichier;
- ne lit aucun fichier JSON;
- ne décode aucun `SINJIRA_GAME_SAVE_V1`;
- ne crée ni ne clone aucune `game_sessions`;
- ne génère aucun code `IMP-*`;
- n’insère aucune `player_sheets` ou `endgame_sheets`.

Une sauvegarde ne transite donc pas par un stockage ou un picker natif ajouté par cette étape.

## Pas de profil de jeu

Le hub ne transforme pas l’historique, le temps de jeu, les modes choisis, le nombre de joueurs ou les résultats en score, profil implicite, recommandation ou mesure de valeur personnelle.

**Protéger sans surveiller.** Le minimum nécessaire ici est une intention de navigation, pas une copie de l’activité ludique.

## Destinations

Le hub peut ouvrir explicitement :

- `/compte/mes-parties.html?surface=web`;
- `/compte/bibliotheque.html?surface=web`;
- `/projets/sinjira/jeux/`;
- `/compte/securite.html`.

## Hors périmètre

Cette étape n’ajoute :

- aucun WebView au hub;
- aucun Supabase, Edge Function, RPC ou API réseau;
- aucun SecureStore, AsyncStorage ou stockage de sauvegarde;
- aucun DocumentPicker, FileSystem, presse-papiers ou partage de fichier;
- aucune modification de `App.tsx`;
- aucune migration SQL;
- aucune écriture Supabase ou production;
- aucune modification de `compte/mes-parties.html` ou `assets/js/sinjira-account.js`.
