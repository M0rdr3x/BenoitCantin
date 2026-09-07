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

La liste fermée couvre maintenant tous les hubs de navigation déjà fusionnés :

- `/compte/messages.html` → `NativeMessagesHub`;
- `/compte/rencontres.html` → `NativeDatingHub`;
- `/compte/emploi.html` → `NativeEmploymentHub`;
- `/compte/bibliotheque.html` → `NativeLibraryHub`;
- `/compte/communaute.html` → `NativeCommunityHub`;
- `/compte/relations.html` → `NativeRelationsHub`;
- `/compte/mes-achats.html` → `NativeCommerceHub`;
- `/compte/monde-parallele.html` → `NativeParallelWorldHub`;
- `/compte/mon-ia.html` → `NativePersonalAiHub`;
- `/compte/histoire-de-vie.html` → `NativeLifeStoryHub`;
- `/compte/mon-personnage.html` → `NativeCharacterHub`;
- `/compte/notifications.html` → `NativeAlertsHub`;
- `/compte/profil.html` → `NativeProfileHub`.

Les onglets persistants et raccourcis dont le chemin appartient à cette liste passent par le routeur avant toute sortie Web.

## Alias Commerce

Le Commerce possède une seule frontière native. Les chemins directs suivants sont donc aussi des alias vers `NativeCommerceHub` :

- `/compte/marche.html`;
- `/compte/jetons.html`;
- `/compte/licences.html`.

Ces alias transportent uniquement une **intention de navigation**. Ils ne transportent aucun solde de Jetons, mouvement de grand livre, brouillon d’annonce, prix, localisation approximative, précommande, préférence commerciale, licence ou droit numérique. Le même composant de sas est utilisé pour éviter qu’une entrée directe contourne la frontière Commerce.

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

Un lien ou raccourci dont le chemin exact appartient à `NATIVE_MODULE_PATHS` est intercepté par le routeur natif. Les autres liens profonds, notifications et états Web précis restent gérés par `navigateToUrl`; le routeur n’intercepte pas arbitrairement des URLs externes ou des variantes non autorisées.

## Retour et partage

Le bouton Retour Android ou le retour du hub ferme le routeur et revient à l’Accueil natif. Les boutons Partager/Recharger restent masqués tant qu’un hub natif est affiché, comme pour l’Accueil et la Sécurité.

## CI exhaustive

Le garde central exige la présence de chaque route et de chaque composant actuellement routé. Son workflow revalide également les garde-fous dédiés des hubs Messages, Rencontres, Emploi, Bibliothèque, Communauté, Relations, Commerce, Monde parallèle, Mon IA, Histoire de vie, Mon personnage, Alertes et Profil, ainsi que les frontières Paramètres, Vie privée, Sécurité, navigation, partage, challenge, secrets, coffre et TypeScript.

L’ajout futur d’un hub au routeur doit donc être accompagné de son garde dédié et de son rechaînage dans cette validation centrale.

## Principe de sécurité

**Protéger sans surveiller.** Ce routeur transporte uniquement une intention de navigation parmi une liste fermée. Il ne transporte ni profil, ni message, ni candidature, ni compatibilité, ni relation familiale, ni achat, ni solde, ni identité narrative, ni histoire de vie, ni réglage IA, ni état de sécurité.
