# SINJIRA V25 — Hub Paramètres natif

## But

Ajouter une surface React Native de navigation pour **Paramètres** sans déplacer les préférences ni les opérations sensibles hors de leur source de vérité Web/serveur.

Le hub natif ne reçoit aucune donnée utilisateur et ne réalise aucune modification de compte.

## Frontière de sécurité

Le hub Paramètres natif :

- ne lit ni préférence de confidentialité, ni préférence de notification, ni état d’export ou de suppression;
- n’appelle ni Supabase, ni Edge Function, ni RPC;
- n’utilise ni `SecureStore`, ni `AsyncStorage`, ni stockage de fichier local pour les données du compte;
- ne prépare, ne télécharge et ne conserve aucun export JSON;
- ne déclenche jamais la suppression du compte;
- ne modifie aucun profil public, choix de visibilité ou préférence de messagerie;
- ne reçoit aucun secret, jeton, contenu du Registre personnel, de l’Histoire de vie ou de Mon IA.

Les actions réelles restent dans les surfaces existantes :

- Paramètres complets : `/compte/parametres.html?surface=web`;
- Centre Vie privée : `/compte/vie-privee.html?surface=web`;
- Ma sécurité : `/compte/securite.html`;
- Profil complet : `/compte/profil.html?surface=web`.

Le paramètre `surface=web` transporte uniquement une intention de navigation. Il ne contient aucune donnée utilisateur.

## Intégration

`NativeProfileHub` et `NativePrivacyHub` conservent leurs deux seules capacités : `onOpenPath` et `onBack`.

Ils ouvrent `NativeSettingsHub` par un état local d’interface lorsque la destination canonique est `/compte/parametres.html`. Toutes les sorties du hub Paramètres réutilisent `onOpenPath`, donc la navigation et les gardes historiques du shell mobile.

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

Une surface native ne doit pas obtenir plus de pouvoir que nécessaire. Tant que l’export, la suppression et les préférences n’ont pas une frontière native équivalente, testée et justifiée, elles restent dans les contrôles Web/serveur existants.
