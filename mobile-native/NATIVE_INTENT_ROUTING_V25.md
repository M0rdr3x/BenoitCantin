# Routage des intentions natives V25

## Objectif

Les 42 pages `compte/*.html` sont maintenant classées et 31 chemins appartiennent à `NATIVE_MODULE_PATHS`. Le shell mobile doit appliquer cette classification de façon cohérente lorsqu’une navigation provient de l’application, d’un lien profond SINJIRA ou d’une notification.

**L’HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.**

Cette étape ne copie aucune donnée privée et ne change aucune autorisation serveur. Elle décide seulement si une intention de navigation ouvre d’abord un sas React Native sans données ou continue vers la surface Web existante.

## Règle principale

Dans `navigateToUrl` :

- une URL interne HTTPS vers un chemin de `NATIVE_MODULE_PATHS`, sans fragment et sans `surface=web`, ouvre le hub correspondant via `openNativeModule`;
- `?surface=web` indique une sortie Web explicite et conserve la surface Web existante;
- un fragment n’est pas absorbé par le routeur natif, afin de ne pas perdre une destination précise d’une surface Web;
- une URL externe ou un hôte non autorisé ne devient jamais une intention native.

Le paramètre `surface=web` n’accorde aucun droit. Il choisit uniquement la surface d’interface. Authentification, RLS, AAL2, moteur de risque, RPC et autres protections restent appliqués par les mécanismes existants.

## Sécurité dédiée

`/compte/securite.html` reste hors de `NativeModuleRouter`.

L’URL interne exacte, sans recherche ni fragment, ouvre `NativeSecurityHub`. Les destinations précises du hub Sécurité, par exemple :

- `#devices-title`;
- `#recent-title`;
- `#travel-title`;
- `#quick-title`;
- `#preferences-title`;

restent Web. Ainsi Mode Voyage, les appareils, les connexions récentes et les confirmations continuent d’utiliser leur source de vérité Web/serveur et ne sont pas reconstruits dans React Native.

## Registre personnel

`/compte/registre-personnel.html` n’appartient pas aux routes natives. Son traitement reste après le résolveur d’intention et conserve le gate local ponctuel existant avant l’ouverture Web, puis les protections renforcées côté SINJIRA.

Cette étape n’affaiblit ni le verrouillage en arrière-plan, ni le MFA, ni le moteur de risque, et ne donne jamais au routeur accès au contenu du Registre.

## Liens profonds

`Linking.getInitialURL()` et l’écouteur `Linking.addEventListener('url', ...)` normalisent toujours l’URL vers un hôte SINJIRA autorisé, puis passent par `navigateToUrl`.

Conséquence : un lien profond vers une route native sans fragment ni sortie Web explicite ouvre maintenant le sas natif correspondant au lieu de contourner silencieusement la classification par une WebView directe.

## Notifications

Le gestionnaire de réponse aux notifications continue d’accepter uniquement un chemin interne commençant par `/` et refusant `//`. Il appelle `navigate`, qui converge vers `navigateToUrl`.

Une notification ciblant une route classée native utilise donc le même sas que le reste du shell. Le routage ne lit aucun contenu de notification supplémentaire et n’ajoute aucune donnée au natif.

## Sorties depuis les hubs

Les hubs utilisent déjà deux formes distinctes :

- chemin nu vers un autre module lorsque l’intention est d’ouvrir un sas natif;
- `?surface=web` lorsque la personne choisit explicitement une action ou une vue qui reste Web.

Les hubs sensibles audités conservent cette règle pour Messages, Rencontres, Emploi, Bibliothèque, Mes parties, Communauté, Réseau personnage, Relations, Commerce, Monde parallèle, Mon IA, Histoire de vie, Personnage, Alertes, Profil, Vie privée et Paramètres.

## Navigation interne de la WebView

Cette étape **n’intercepte pas** les clics internes déjà actifs dans la WebView. `shouldStart` conserve son comportement historique et son traitement spécial du Registre.

Cette limite est volontaire : changer en même temps les navigations internes d’une surface Web pourrait casser un flux contextuel ou un état déjà ouvert. Le présent lot ferme uniquement l’écart des intentions qui passent par le shell mobile, les hubs, les liens profonds et les notifications.

## Pages volontairement Web

La classification précédente reste inchangée :

- `/compte/index.html` : accueil Web de repli;
- auth/MFA : connexion, inscription, récupération, réinitialisation et MFA;
- `/compte/signaler-deces.html` : procédure sensible Web/serveur;
- `/compte/projet.html` et `/compte/confidentialite-joueur.html` : pages contextuelles/informatives;
- Registre : Web gardé;
- fragments Sécurité : Web.

Aucune de ces routes n’est ajoutée à `NATIVE_MODULE_PATHS` par ce changement.

## Invariants CI

`validate_mobile_native_intent_routing_v25.py` exige notamment :

- la normalisation des intentions internes sur les hôtes autorisés;
- l’ouverture native exacte de Sécurité sans recherche ni fragment;
- le test `surface=web` avant l’ouverture d’un module natif;
- l’exclusion des fragments du routage des modules;
- l’utilisation de `isNativeModulePath` puis `openNativeModule`;
- le maintien du gate Registre après la décision de routage;
- le passage des liens profonds par `navigateToUrl`;
- le passage des notifications par `navigate`;
- l’absence d’interception `openNativeModule` dans `shouldStart`;
- la présence des cinq fragments Web du hub Sécurité;
- le rechaînage des gardes de classification, routeur, navigation, challenge, secrets, coffre et TypeScript.

## Principe de sécurité

Le routeur reçoit une intention d’URL, pas des données métier. Il ne reçoit ni message, profil, historique, candidature, compatibilité, sauvegarde, commentaire, relation, achat, solde, identité de personnage, souvenir, réglage IA, décision de modération, donnée de voyage ou contenu du Registre.

Le choix du sas protège la cohérence de l’application; il ne remplace jamais les décisions et contrôles humains ou serveur qui protègent les personnes.
