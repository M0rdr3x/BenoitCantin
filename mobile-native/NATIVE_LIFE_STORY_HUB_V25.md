# SINJIRA V25 — Hub Histoire de vie natif

## Principe

**L’HUMAIN AVANT TOUT.** Le hub React Native Histoire de vie est un sas de navigation et d’explication. Il ne devient pas une nouvelle source de vérité et ne reproduit aucune donnée privée du module Histoire de vie.

**Protéger sans surveiller.** Le natif ne reçoit aucune donnée utilisateur Histoire de vie et n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau. Il ne lit pas le contenu de la WebView et ne maintient aucun cache local de souvenirs, versions, proches ou état posthume.

## Données volontairement absentes du natif

Le hub ne reçoit, ne lit et ne stocke notamment aucun :

- souvenir, titre, récit, date ou classification personnelle ;
- état d’autorisation d’un élément ;
- association à une version famille, personnelle ou générale ;
- titre ou instruction d’une version ;
- nom, description ou courriel d’un destinataire ;
- directive posthume ou état d’un dossier de vérification de décès ;
- code privé de signalement de décès, sous forme brute ou dérivée ;
- aperçu privé ou contenu d’un futur PDF.

Ses seules capacités sont `onOpenPath` et `onBack`.

## Consentement : trois décisions distinctes

Le hub ne crée, ne modifie et ne supprime aucun élément Histoire de vie.

Les opérations suivantes restent séparées dans la surface privée Web :

1. enregistrer un élément, qui reste privé par défaut ;
2. autoriser explicitement cet élément pour une œuvre ;
3. choisir explicitement les versions dans lesquelles cet élément peut apparaître.

Ouvrir le hub natif ne réalise aucune de ces décisions et ne vaut jamais consentement.

## AAL2 reste sur la surface privée

Le hub ne décide jamais si une personne est autorisée à lire ou modifier Histoire de vie. La surface Web existante conserve son exigence AAL2 avant l’accès aux données et opérations privées.

Le natif n’évalue pas MFA, appareil, risque ou challenge et ne reproduit aucune logique d’autorisation serveur.

## Procédure posthume

Le hub natif ne :

- signale pas un décès ;
- ne valide pas un décès ;
- ne choisit aucun destinataire ;
- ne crée ou révoque aucun code privé de signalement ;
- ne conteste pas une vérification ;
- ne prépare, génère ou remet aucun PDF.

La procédure existante reste inchangée : décès vérifié humainement, délai de sécurité de **30 jours** sans contestation, puis **deuxième validation humaine** avant toute préparation. Une contestation suspend la suite du processus jusqu’à révision humaine.

Aucune génération n’est déclenchée par l’ouverture du hub natif.

## Registre personnel : frontière absolue

Le **Registre personnel des consciences** reste séparé de Histoire de vie.

- il n’est pas lu par `NativeLifeStoryHub` ;
- il n’est pas transmis au hub ;
- il n’est jamais ajouté automatiquement à Histoire de vie ;
- il n’est jamais inclus automatiquement dans une œuvre ou un PDF posthume ;
- le hub ne fournit aucun chemin alternatif autour du gate Registre existant.

Seuls les éléments que la personne choisit volontairement d’enregistrer dans Histoire de vie peuvent suivre le contrat Histoire de vie.

## Mon IA reste séparée

Le hub ne crée aucun clone IA après décès et ne rend aucune mémoire interrogeable par un proche.

Ouvrir Mon IA depuis le hub ne vaut jamais consentement pour utiliser Histoire de vie comme source. Les consentements Mon IA restent explicites et séparés.

## Navigation

Le hub expose uniquement des liens vers :

- `/compte/histoire-de-vie.html?surface=web` ;
- `/compte/securite.html` ;
- `/compte/vie-privee.html?surface=web` ;
- `/compte/mon-ia.html?surface=web`.

L’Accueil natif peut ouvrir `NativeLifeStoryHub` sans données. Le routeur natif central connaît `/compte/histoire-de-vie.html`, mais la sortie `?surface=web` reste volontairement une ouverture explicite de la surface Web privée.

## Hors périmètre

Ce lot n’ajoute :

- aucune migration SQL ;
- aucune écriture en production ;
- aucune nouvelle table ou RPC ;
- aucun stockage natif Histoire de vie ;
- aucune génération PDF ;
- aucune nouvelle procédure de décès ;
- aucune capacité de remise posthume.

Le rôle du natif est uniquement d’orienter clairement la personne avant l’ouverture de la zone privée.
