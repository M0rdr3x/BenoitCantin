# SINJIRA™ Mobile Native — V24.4.97

Application iOS/iPadOS et Android de SINJIRA™.

> Référence normative : [`../CAHIER_MAITRE_SINJIRA.md`](../CAHIER_MAITRE_SINJIRA.md). L’application mobile doit respecter le principe **L’humain avant tout** et la règle **protéger sans surveiller**.

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
- aucune nouvelle collecte de données;
- les futures données de localisation de sécurité doivent rester approximatives, minimisées et séparées des usages commerciaux, sociaux, Rencontres et Emploi;
- le Registre des Consciences et l’IA personnelle sont classés comme zones extrêmement sensibles;
- les notifications sur écran verrouillé ne doivent pas révéler de contenu extrêmement privé.

## Centre de sécurité mobile visé

L’application doit progressivement offrir un accès direct à :

- Mes appareils;
- Connexions récentes;
- Mode Voyage;
- Passkeys et authentification;
- approbation ou refus d’une nouvelle connexion;
- Téléphone perdu;
- Compte compromis;
- Récupération du compte.

Le téléphone peut devenir l’appareil principal de confiance de l’utilisateur, sans devenir un outil de suivi permanent de sa localisation.

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

1. notifications push natives, avec contenu discret pour les alertes sensibles;
2. partage natif de liens SINJIRA;
3. biométrie locale pour protéger la reprise de session et les zones extrêmement sensibles;
4. passkeys et approbation de connexion depuis l’appareil de confiance;
5. navigation profonde complète;
6. accès rapide au Centre de sécurité;
7. intégration côté serveur du Bouclier de connexion contextuel et du Mode Voyage;
8. migration progressive des écrans les plus utilisés vers React Native sans dupliquer les comptes ni les données.
