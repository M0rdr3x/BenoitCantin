# Routage des intentions natives V25

## Objectif

Les 44 pages `compte/*.html` sont maintenant classées et 31 chemins appartiennent à `NATIVE_MODULE_PATHS`. Le shell mobile doit appliquer cette classification de façon cohérente lorsqu’une navigation provient de l’application, d’un lien profond SINJIRA ou d’une notification.

**L’HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.**

Cette étape ne copie aucune donnée privée et ne change aucune autorisation serveur. Elle décide seulement si une intention de navigation ouvre d’abord un sas React Native sans données ou continue vers la surface Web existante.

## Règle principale

Dans `navigateToUrl` :

- une URL interne HTTPS vers un chemin de `NATIVE_MODULE_PATHS`, sans fragment et sans `surface=web`, n’ouvre le hub correspondant via `openNativeModule` que lorsque le shell a reçu l’état coarse `nonchild` depuis une page `/compte/` authentifiée;
- `?surface=web` indique une sortie Web explicite et conserve la surface Web existante;
- un fragment n’est pas absorbé par le routeur natif, afin de ne pas perdre une destination précise d’une surface Web;
- une URL externe ou un hôte non autorisé ne devient jamais une intention native;
- l’état `unknown` est fail-closed : les hubs généraux ne s’ouvrent pas et la navigation retombe sur la surface Web autoritative;
- l’état `child` utilise une navigation Junior distincte et ne peut pas ouvrir un hub natif général.

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

Pour les comptes `nonchild`, `shouldStart` conserve le comportement général historique et le traitement spécial du Registre.

Pour un compte déjà identifié `child`, le shell applique toutefois une frontière supplémentaire **avant chargement** : les liens internes vers Messages, Rencontres, Emploi, playtests, Mon IA, Monde parallèle, commerce, licences et autres routes explicitement restreintes sont réécrits vers `/compte/communaute-junior.html?from=restricted&module=...`. La Communauté générale et ses règles sont réécrites vers leurs versions Junior.

Les routes autorisées 11–12 ans, par exemple Profil ou la Bibliothèque filtrée, restent dans la WebView. Cette interception ne décide jamais qu’un contenu est convenable : RLS, RPC et classement humain `approved_11_12` restent l’autorité.

## Pages volontairement Web

La classification précédente reste inchangée :

- `/compte/index.html` : accueil Web de repli;
- auth/MFA : connexion, inscription, récupération, réinitialisation et MFA;
- `/compte/signaler-deces.html` : procédure sensible Web/serveur;
- `/compte/projet.html` et `/compte/confidentialite-joueur.html` : pages contextuelles/informatives;
- `/compte/communaute-junior.html` et `/compte/regles-communaute-junior.html` : surfaces Web Junior dédiées, hors du routeur natif général;
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
- le refus d’ouvrir un hub général lorsque l’état du compte est `unknown` ou `child`;
- les redirections préchargement des routes restreintes lorsqu’un compte `child` est déjà connu;
- la preuve exécutable qu’un lien Messages est réécrit vers Junior tandis qu’un lien Profil reste autorisé;
- la présence des cinq fragments Web du hub Sécurité;
- le rechaînage des gardes de classification, routeur, navigation, challenge, secrets, coffre et TypeScript.

## Principe de sécurité

Le routeur reçoit une intention d’URL, pas des données métier. Il ne reçoit ni message, profil, historique, candidature, compatibilité, sauvegarde, commentaire, relation, achat, solde, identité de personnage, souvenir, réglage IA, décision de modération, donnée de voyage ou contenu du Registre.

Le choix du sas protège la cohérence de l’application; il ne remplace jamais une décision humaine, une **révision humaine** obligatoire, ni les contrôles serveur qui protègent les personnes. Il ne décide ni d’un appel de modération, ni d’un décès, ni du canon, ni d’un autre changement irréversible.

## Normalisation du schéma mobile `sinjira:`

Les intentions natives acceptent les formes URI usuelles à **une, deux ou trois barres** (`sinjira:/compte/...`, `sinjira://compte/...`, `sinjira:///compte/...`). Elles sont toutes ramenées à un seul chemin interne `/compte/...` avant la décision de routage. Cela évite qu’une URI triple-slash devienne accidentellement `//compte/...` et contourne le sas natif.

Le garde dédié couvre explicitement les trois formes afin qu’une régression de normalisation échoue en CI avant fusion.

Cette normalisation ne rend aucune nouvelle route admissible : les mêmes listes fermées, exclusions sensibles et règles `?surface=web` continuent de s’appliquer après normalisation.
