# Routage uniforme des hubs natifs V25

## Objectif

La migration native de SINJIRA comporte maintenant plusieurs hubs React Native qui servent de sas sans données avant les surfaces Web privées. L’Accueil natif ouvrait déjà ces hubs, mais les onglets persistants et certains raccourcis du shell mobile pouvaient encore ouvrir directement les pages Web correspondantes.

Cette étape unifie uniquement le **routage de l’interface mobile**. Elle ne migre aucune donnée et ne change aucune règle serveur.

**L’HUMAIN AVANT TOUT.** Une navigation plus cohérente ne doit jamais devenir un prétexte pour copier des données privées ou contourner une protection existante.

## Routeur central

`NativeModuleRouter` reçoit seulement :

- un chemin appartenant à une liste fermée de modules natifs;
- `onOpenPath`, pour quitter explicitement le sas vers une destination existante;
- `onBack`, pour revenir à l’Accueil natif.

Le routeur ne reçoit aucune donnée utilisateur et ne possède aucune source de vérité. Il n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau et n’utilise ni WebView, ni SecureStore, ni AsyncStorage.

## Modules routés nativement

La liste fermée contient uniquement :

- `/compte/messages.html` → `NativeMessagesHub`;
- `/compte/rencontres.html` → `NativeDatingHub`;
- `/compte/emploi.html` → `NativeEmploymentHub`;
- `/compte/monde-parallele.html` → `NativeParallelWorldHub`;
- `/compte/mon-ia.html` → `NativePersonalAiHub`;
- `/compte/notifications.html` → `NativeAlertsHub`;
- `/compte/profil.html` → `NativeProfileHub`.

Les onglets persistants Messages, Rencontres, Emploi, Monde et Mon IA passent maintenant par ce routeur. Les raccourcis Alertes et Profil utilisent le même mécanisme.

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

## Principe de sécurité

**Protéger sans surveiller.** Ce routeur transporte uniquement une intention de navigation parmi une liste fermée. Il ne transporte ni profil, ni message, ni candidature, ni compatibilité, ni identité narrative, ni réglage IA, ni état de sécurité.
