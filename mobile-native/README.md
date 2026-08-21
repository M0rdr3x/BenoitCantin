# SINJIRA™ Mobile Native — V24.4.96

Application iOS/iPadOS et Android de SINJIRA™.

## Principe d’architecture

Cette application ne crée **aucun second compte SINJIRA, aucune seconde base sociale et aucune copie des données**. Elle utilise le site mobile-first existant comme surface fonctionnelle commune dans un conteneur natif Expo/React Native.

Cette stratégie donne immédiatement une application installable depuis les stores tout en conservant les fonctions existantes :

- Fil de la Communauté;
- Monde parallèle;
- Messages;
- Notifications;
- Profil;
- Registre des Consciences;
- Réseau personnage;
- Rencontres 18+;
- Compte, sécurité, modération et autres écrans déjà disponibles sur le Web.

Les écrans pourront ensuite être migrés progressivement vers des composants React Native natifs sans changer les comptes ni Supabase.

## Plateformes

Le socle utilise Expo SDK 57 / React Native 0.86.

- Android : Android 7 et versions ultérieures prises en charge par Expo SDK 57;
- iOS/iPadOS : iOS 16.4 et versions ultérieures prises en charge par Expo SDK 57;
- appareils non couverts : la PWA SINJIRA reste disponible depuis le navigateur.

## Sécurité et vie privée

- HTTPS seulement pour le domaine SINJIRA;
- aucun secret Supabase embarqué dans ce shell;
- cookies et stockage WebView persistants pour conserver la session de l’utilisateur;
- liens externes ouverts hors du conteneur SINJIRA;
- aucune permission appareil ajoutée par défaut;
- aucune géolocalisation ajoutée par cette version;
- aucune nouvelle collecte de données.

## Développement

Prérequis : Node.js compatible avec Expo SDK 57.

```bash
cd mobile-native
npm install
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

1. relier le projet à un compte Expo/EAS;
2. configurer les certificats/signatures Apple et Google;
3. créer les fiches App Store Connect et Google Play Console;
4. finaliser les fichiers d’association de domaine pour Universal Links / Android App Links avec les identifiants de signature réels;
5. tester connexion, récupération de session, retour arrière Android, ouverture des liens et réinstallation;
6. vérifier les politiques des stores au moment de la soumission.

## Étapes natives suivantes

Priorité recommandée après ce socle :

1. notifications push natives;
2. partage natif de liens SINJIRA;
3. biométrie locale pour protéger la reprise de session;
4. navigation profonde complète;
5. migration progressive des écrans les plus utilisés vers React Native;
6. intégration de la sécurité de connexion contextuelle et du mode voyage côté serveur, sans surveillance inutile.
