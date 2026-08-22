# SINJIRA™ Mobile Native — V24.4.98

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

## V24.4.98 — sécurité native mise en place

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
- l’app ouvre le Centre **Ma sécurité** lorsqu’une alerte correspondante est touchée;
- l’inscription push reste inactive tant que le projet n’est pas relié à un identifiant EAS réel.

### Accès rapide

La barre d’accès mobile inclut maintenant **Sécurité**, Registre, Personnage et Rencontres. Le Centre **Ma sécurité** permet la gestion des appareils, sessions, Mode Voyage, alertes et connexions à confirmer.

## Bouclier de connexion

Le moteur serveur V24.4.98 combine plusieurs signaux : appareil nouveau ou non fiable, changement de pays approximatif lorsqu’une infrastructure de confiance le fournit, déplacement temporellement improbable, Mode Voyage et sensibilité de l’action.

Un pays ou une région ne suffit jamais à conclure qu’une connexion est frauduleuse.

La géolocalisation de sécurité est **désactivée par défaut** dans l’Edge Function. Elle ne peut être activée que par une infrastructure SINJIRA contrôlée qui fournit une région approximative fiable. Le moteur ne lit ni ne stocke l’adresse IP brute et ne demande pas le GPS du téléphone.

## Passkeys — préparation, pas encore activation production

Le projet prévoit les passkeys, mais elles ne doivent pas être activées précipitamment sur l’ancien domaine.

WebAuthn lie les passkeys à un **RP ID**. Comme `sinjira.com` est réservé et destiné à devenir le domaine principal, l’activation production sera faite après le choix définitif du domaine et la configuration correspondante dans Supabase Auth. Cela évite de créer aujourd’hui des passkeys liées à `benoitcantin.com` qu’une migration ultérieure pourrait rendre inutilisables.

En attendant, TOTP/AAL2 et la biométrie locale assurent le step-up disponible dans la V24.4.98.

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
5. configurer le domaine final `sinjira.com` lorsque sa migration sera décidée;
6. activer et tester les passkeys seulement avec le RP ID final;
7. tester connexion, MFA, biométrie, push, Mode Voyage, récupération de session et réinstallation;
8. vérifier les politiques des stores au moment de la soumission.

## Prochaines migrations natives

- partage natif de liens SINJIRA;
- navigation profonde complète;
- écrans React Native natifs pour les parcours les plus utilisés;
- passkeys après activation du domaine/RP ID final;
- amélioration du parcours de récupération sans diminuer la protection du Registre.
