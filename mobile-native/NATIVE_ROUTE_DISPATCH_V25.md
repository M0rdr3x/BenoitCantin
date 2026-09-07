# Routage uniforme des hubs natifs V25

## Objectif

La migration native de SINJIRA comporte maintenant plusieurs hubs React Native qui servent de sas sans données avant les surfaces Web privées. Les entrées persistantes et les chemins reconnus doivent converger vers ces sas sans dupliquer les données de leurs modules.

Cette étape unifie uniquement le **routage de l’interface mobile**. Elle ne migre aucune donnée et ne change aucune règle serveur.

**L’HUMAIN AVANT TOUT.** Une navigation plus cohérente ne doit jamais devenir un prétexte pour copier des données privées ou contourner une protection existante.

## Routeur central

`NativeModuleRouter` reçoit seulement :

- un chemin appartenant à une liste fermée de modules natifs;
- `onOpenPath`, pour quitter explicitement le sas vers une destination existante;
- `onBack`, pour revenir à l’Accueil natif.

Le routeur ne reçoit aucune donnée utilisateur et ne possède aucune source de vérité. Il n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau et n’utilise ni WebView, ni SecureStore, ni AsyncStorage.

## Modules routés nativement

La liste fermée couvre maintenant tous les hubs de navigation déjà fusionnés ou ajoutés avec leur garde dédié :

- `/compte/messages.html` → `NativeMessagesHub`;
- `/compte/rencontres.html` → `NativeDatingHub`;
- `/compte/emploi.html` → `NativeEmploymentHub`;
- `/compte/bibliotheque.html` → `NativeLibraryHub`;
- `/compte/mes-parties.html` → `NativeGamesHub`;
- `/compte/communaute.html` → `NativeCommunityHub`;
- `/compte/reseau-personnage.html` → `NativeCharacterNetworkHub`;
- `/compte/relations.html` → `NativeRelationsHub`;
- `/compte/mes-achats.html` → `NativeCommerceHub`;
- `/compte/monde-parallele.html` → `NativeParallelWorldHub`;
- `/compte/mon-ia.html` → `NativePersonalAiHub`;
- `/compte/histoire-de-vie.html` → `NativeLifeStoryHub`;
- `/compte/mon-personnage.html` → `NativeCharacterHub`;
- `/compte/notifications.html` → `NativeAlertsHub`;
- `/compte/profil.html` → `NativeProfileHub`.

Les onglets persistants et raccourcis du shell qui passent explicitement par `openNativeModule` utilisent cette liste fermée avant toute sortie Web.

## Mes parties

`/compte/mes-parties.html` transporte uniquement une intention de navigation vers `NativeGamesHub`. Le routeur ne reçoit aucune sauvegarde, session, code de partie, compteur, durée, mode de jeu, `player_sheets`, `endgame_sheets` ou fichier `SINJIRA_GAME_SAVE_V1`.

Les exports et imports privés restent des actions Web explicites. Le routeur ne sélectionne, ne lit, ne parse, ne copie et ne partage aucun fichier de sauvegarde.

## Réseau personnage

`/compte/reseau-personnage.html` transporte uniquement une intention de navigation vers `NativeCharacterNetworkHub`.

Le routeur et le hub natif ne reçoivent ni identité réelle, ni identifiant de compte ou de personnage, ni profil social, publication, commentaire, réaction, relation, groupe, blocage, signalement, état de modération ou historique de consultation. Ils ne calculent aucun graphe social et ne relient jamais publiquement l’identité du compte à l’identité fictive.

Les décisions de rôle propriétaire restent côté serveur. Les RPC `is_sinjira_owner` et `ensure_sinjira_owner_character` ne font pas partie du hub natif et ne sont pas reproduites dans React Native. Les publications et interactions rôle-play restent dans la surface Web protégée et ne deviennent jamais canoniques par l’effet du routage natif.

## Alias Commerce

Le Commerce possède une seule frontière native. Les chemins directs suivants sont donc aussi des alias vers `NativeCommerceHub` lorsqu’un appel du shell passe par `openNativeModule` :

- `/compte/marche.html`;
- `/compte/jetons.html`;
- `/compte/licences.html`.

Ces alias transportent uniquement une **intention de navigation**. Ils ne transportent aucun solde de Jetons, mouvement de grand livre, brouillon d’annonce, prix, localisation approximative, précommande, préférence commerciale, licence ou droit numérique. Le même composant de sas est utilisé pour éviter de créer une logique native commerciale parallèle.

Cette étape ne réécrit pas les liens profonds reçus par `Linking` ni les navigations internes déjà actives dans la WebView : ces chemins continuent de passer par `navigateToUrl` ou la navigation Web historique. Les sorties explicites des hubs avec `?surface=web` restent elles aussi des sorties Web volontaires.

## Chemins volontairement exclus

### Registre personnel

`/compte/registre-personnel.html` **n’est pas** une route du `NativeModuleRouter`. Son ouverture continue de passer par `navigate()` et le gate existant : biométrie locale ponctuelle lorsqu’elle est disponible, fenêtre courte, verrouillage en arrière-plan, puis MFA et moteur de risque côté SINJIRA.

Le routeur ne reçoit, ne stocke et n’exporte aucun contenu du Registre.

### Sécurité

Le raccourci Sécurité continue d’ouvrir directement `NativeSecurityHub`, qui possède déjà sa frontière native spécifique. Il n’est pas dupliqué dans le routeur de modules.

### Mode Voyage

Mode Voyage reste une fonctionnalité Web/serveur. Le routeur ne reçoit ni destination, ni période, ni plan de voyage et ne stocke aucune donnée de déplacement.

## Sortie explicite vers le Web

Quand une personne choisit une action Web depuis un hub natif, `App.tsx` efface d’abord l’intention de module natif, puis utilise la navigation historique. Le Web redevient alors la surface active avec ses protections existantes.

Les liens profonds, notifications et autres navigations historiques restent gérés par `navigateToUrl`; cette étape n’intercepte pas arbitrairement des URLs externes ou des états Web précis.

## Retour et partage

Le bouton Retour Android ou le retour du hub ferme le routeur et revient à l’Accueil natif. Les boutons Partager/Recharger restent masqués tant qu’un hub natif est affiché, comme pour l’Accueil et la Sécurité.

## CI exhaustive

Le garde central exige la présence de chaque route et de chaque composant actuellement routé. Son workflow revalide également les garde-fous dédiés des hubs Messages, Rencontres, Emploi, Bibliothèque, Mes parties, Communauté, Réseau personnage, Relations, Commerce, Monde parallèle, Mon IA, Histoire de vie, Mon personnage, Alertes et Profil, ainsi que les frontières Paramètres, Vie privée, Sécurité, navigation, partage, challenge, secrets, coffre et TypeScript.

L’ajout futur d’un hub au routeur doit donc être accompagné de son garde dédié et de son rechaînage dans cette validation centrale.

## Principe de sécurité

**Protéger sans surveiller.** Ce routeur transporte uniquement une intention de navigation parmi une liste fermée. Il ne transporte ni profil, ni message, ni candidature, ni compatibilité, ni sauvegarde de jeu, ni relation familiale, ni achat, ni solde, ni identité réelle, ni identité de personnage, ni graphe social, ni histoire de vie, ni réglage IA, ni état de sécurité.
