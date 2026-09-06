# SINJIRA V25 — Hub Alertes natif

## But

Ajouter une surface React Native de navigation pour **Alertes** sans copier les notifications privées, leurs compteurs ni leur état lu/non lu hors de la source de vérité Web/serveur.

Le hub natif ne reçoit aucune donnée utilisateur et ne réalise aucune mutation d’avis.

## Frontière de sécurité

Le hub Alertes natif :

- ne lit aucun avis privé, aperçu, nombre non lu, date, catégorie, lien ou événement de compte;
- n’appelle ni Supabase, ni Edge Function, ni RPC;
- n’utilise ni `SecureStore`, ni `AsyncStorage`, ni stockage local pour les avis;
- ne marque aucun avis comme lu ou non lu;
- ne crée et ne supprime aucune notification;
- ne reçoit aucun contenu de Messages, Rencontres, Registre personnel, Histoire de vie ou Mon IA;
- ne construit aucun résumé local de l’activité du compte.

Les actions réelles restent dans les surfaces existantes :

- avis privés complets : `/compte/notifications.html?surface=web`;
- Centre de sécurité : `/compte/securite.html`;
- Messages : `/compte/messages.html`;
- préférences internes : `/compte/parametres.html?surface=web`.

Le paramètre `surface=web` transporte uniquement une intention de navigation. Il ne contient aucune donnée utilisateur.

## Intégration

`NativeHomeHub` conserve exactement ses capacités historiques : `onOpenPath` et `onOpenSecurity`.

L’ouverture de `/compte/notifications.html` active `NativeAlertsHub` par un état local d’interface. Toutes les sorties du hub réutilisent `onOpenPath`, donc la navigation historique et ses gardes restent la frontière d’accès aux modules réels.

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

Le natif améliore l’orientation sans devenir une seconde copie du centre d’avis. Tant qu’une lecture native des notifications n’a pas une frontière RLS, une minimisation et des tests équivalents, le contenu privé reste côté Web/serveur.
