# SINJIRA™ Mobile Native — V25.0

Application iOS/iPadOS et Android de SINJIRA™.

> Référence normative : [`../CAHIER_MAITRE_SINJIRA.md`](../CAHIER_MAITRE_SINJIRA.md). L’application mobile respecte **L’humain avant tout** et la règle **protéger sans surveiller**.

## Principe d’architecture

Cette application ne crée **aucun second compte SINJIRA, aucune seconde base sociale et aucune copie indépendante des données**. Elle utilise le même Compte universel et la même plateforme Supabase que le Web.

Le conteneur Expo/React Native conserve immédiatement l’accès aux fonctions Web existantes tout en ajoutant progressivement les capacités natives nécessaires à la sécurité.

## Plateformes

Le socle utilise Expo SDK 57 / React Native 0.86.

- Android : Android 7 et versions ultérieures prises en charge par Expo SDK 57;
- iOS/iPadOS : iOS 16.4 et versions ultérieures prises en charge par Expo SDK 57;
- appareils non couverts : la PWA SINJIRA reste disponible depuis le navigateur.

## V24.4.98 — fondation sécurité native

### Identité d’appareil

- un identifiant aléatoire opaque est créé par l’application;
- il est conservé dans `expo-secure-store`;
- le même identifiant est transmis au WebView pour relier l’application au Centre **Ma sécurité**;
- il ne s’agit pas d’une empreinte publicitaire ou d’un fingerprint du téléphone;
- aucune adresse IP brute ni donnée GPS n’est utilisée pour produire cet identifiant.

### Protection biométrique locale

L’utilisateur peut choisir d’activer un verrou local avec Face ID, Touch ID ou l’authentification biométrique Android.

- activation volontaire seulement;
- la biométrie reste gérée par le système d’exploitation;
- SINJIRA ne reçoit ni visage ni empreinte;
- l’application se reverrouille lorsqu’elle passe en arrière-plan;
- si aucune biométrie utilisable ne reste configurée, le verrou local est désactivé afin de ne pas enfermer la personne hors de son propre compte.

### Notifications push de sécurité

L’utilisateur peut choisir d’activer les notifications natives de sécurité.

- permission demandée seulement après action explicite;
- jeton push conservé dans le stockage sécurisé local puis enregistré côté serveur;
- contenu volontairement générique sur l’écran verrouillé;
- aucune localisation précise, confidence, donnée de santé ou interprétation psychologique dans une alerte push;
- l’app ouvre la route SINJIRA fournie par une alerte lorsqu’elle est touchée;
- l’inscription push reste inactive tant que le projet n’est pas relié à un identifiant EAS réel.

## V24.4.99 — phase mobile 2

### Origine Web migrable

L’origine n’est plus une dépendance métier figée dans le code.

- valeur active : `expo.extra.webOrigin = https://www.benoitcantin.com`;
- hôtes autorisés par le runtime : `benoitcantin.com`, `www.benoitcantin.com`, `sinjira.com`, `www.sinjira.com`;
- HTTPS est obligatoire;
- toute origine configurée qui ne fait pas partie de cette liste retombe sur l’origine sûre actuelle;
- les liens `sinjira://` et les liens HTTPS des domaines autorisés sont normalisés vers l’origine active.

Cette préparation **ne change pas le DNS** et ne fait pas de `sinjira.com` le domaine actif.

### Universal Links et Android App Links

La configuration mobile déclare maintenant les futurs hôtes SINJIRA pour `/app`, `/compte` et `/projets/sinjira`.

Ils ne seront réellement vérifiés qu’après publication des fichiers d’association avec :

- le vrai Apple Team ID dans `apple-app-site-association`;
- le vrai SHA-256 du certificat Android de production dans `assetlinks.json`.

Aucun identifiant de signature ne doit être inventé.

### Récupération et téléphone perdu

La récupération V24.4.99 est renforcée côté Web/serveur :

- lorsqu’un TOTP vérifié existe, AAL2 est requis avant le changement de mot de passe;
- après récupération, les autres appareils SINJIRA sont révoqués;
- les push de sécurité sont désactivés et devront être réactivés volontairement;
- toutes les sessions Auth sont fermées;
- l’appareil courant doit regagner explicitement la confiance;
- un appareil déclaré perdu perd sa confiance et ses notifications, puis les autres sessions sont fermées.

## V25.0 — migration native progressive

La migration vers des surfaces React Native se fait **par frontière de risque**, sans recopier la logique métier ou les données privées déjà correctement protégées côté Web/serveur.

### Partage natif sûr

Le menu de partage du téléphone est maintenant réservé aux pages SINJIRA publiques :

- les routes `/app`, `/compte`, `/admin`, `/auth` et `/api` ne peuvent pas être envoyées au menu de partage;
- les paramètres de requête et fragments ne sont pas transmis;
- le module de partage isolé ne reçoit jamais une URL privée de compte.

### Frontière de navigation externe

La WebView n’accepte que HTTPS. Les liens externes ne sont ouverts par le système que pour `https:`, `mailto:` et `tel:` après validation.

- HTTP et les schémas arbitraires sont bloqués;
- les URLs HTTPS externes contenant des éléments de session ou d’authentification sont refusées;
- les deep links `sinjira://` restent traités par React Native puis normalisés vers l’origine SINJIRA approuvée.

### Hub **Ma sécurité** natif

Le premier écran métier migré en React Native est un hub de sécurité volontairement minimal.

Il affiche uniquement l’état local déjà connu de l’application :

- verrou biométrique local activé ou non;
- notifications de sécurité activées ou non.

Il donne ensuite un accès direct à :

- Mes appareils;
- Connexions récentes;
- Mode Voyage;
- Connexions à confirmer;
- Préférences de sécurité.

Ces opérations continuent d’ouvrir le **Centre de sécurité Web existant**. Le hub natif :

- n’appelle pas Supabase directement;
- ne possède aucun RPC de sécurité;
- ne lit ni ne stocke les clés d’appareil;
- ne copie aucune liste d’appareils, connexion, voyage ou challenge;
- ne reçoit aucune donnée du Coffre ou de Mon IA;
- ne demande aucun GPS et n’affiche aucune adresse IP;
- conserve les contrôles AAL2 et serveur comme source de vérité unique.

Cette frontière évite de créer deux implémentations de sécurité qui pourraient diverger.

## Bouclier de connexion

Le moteur serveur combine plusieurs signaux : appareil nouveau ou non fiable, changement de pays approximatif lorsqu’une infrastructure de confiance le fournit, déplacement temporellement improbable, Mode Voyage et sensibilité de l’action.

Un pays ou une région ne suffit jamais à conclure qu’une connexion est frauduleuse.

La géolocalisation de sécurité est **désactivée par défaut** dans l’Edge Function. Elle ne peut être activée que par une infrastructure SINJIRA contrôlée qui fournit une région approximative fiable. Le moteur ne lit ni ne stocke l’adresse IP brute et ne demande pas le GPS du téléphone.

## Passkeys — préparées, pas activées

WebAuthn lie les passkeys à un **RP ID**. Le RP ID prévu est `sinjira.com`, mais il ne doit être utilisé qu’après la migration réelle du domaine.

V24.4.99 peut détecter la compatibilité du navigateur et afficher l’état de préparation, mais ne crée aucun identifiant WebAuthn sur le domaine actuel.

En attendant, TOTP/AAL2 et la biométrie locale assurent le step-up disponible.

Voir [`../DOMAIN_MIGRATION_SINJIRA.md`](../DOMAIN_MIGRATION_SINJIRA.md) pour le plan de cutover et de rollback.

## Vie privée

- HTTPS seulement;
- aucun secret Supabase embarqué dans l’application;
- aucune géolocalisation GPS ajoutée;
- aucune donnée de sécurité réutilisée pour publicité, Communauté, Rencontres ou Emploi;
- notifications sensibles discrètes;
- Registre et IA privée classés comme zones extrêmement sensibles;
- même Compte universel entre Web et application.

## Développement

```bash
cd mobile-native
npm install
npm run typecheck
npm run start
```

Pour un appareil ou simulateur :

```bash
npm run android
npm run ios
```

## Builds distribuables

Le fichier `eas.json` prépare les profils development, preview et production.

Avant publication réelle :

1. relier le projet à un compte Expo/EAS et obtenir le `projectId`;
2. configurer les certificats/signatures Apple et Google;
3. créer les fiches App Store Connect et Google Play Console;
4. finaliser Universal Links / Android App Links avec les signatures réelles;
5. effectuer le prévol de [`DOMAIN_MIGRATION_SINJIRA.md`](../DOMAIN_MIGRATION_SINJIRA.md);
6. migrer le domaine seulement lorsque tous les contrôles sont verts;
7. activer et tester les passkeys seulement avec le RP ID final;
8. tester connexion, MFA, biométrie, push, Mode Voyage, récupération, appareil perdu et réinstallation;
9. vérifier les politiques des stores au moment de la soumission.

## Prochaines migrations natives

- poursuivre les écrans React Native pour les parcours fréquents à faible risque, sans dupliquer les sources de vérité serveur;
- actions de sécurité enrichies depuis les notifications après stabilisation EAS;
- passkeys après activation du domaine/RP ID final.
