# Hub Messages natif V25

## Objectif

Le hub Messages React Native ajoute une surface de navigation minimale avant la messagerie SINJIRA existante. Il ne remplace pas la messagerie Web protégée et ne devient jamais une source de vérité pour les conversations.

**L’HUMAIN AVANT TOUT.** Le choix de l’identité utilisée pour écrire appartient toujours à la personne.

**Protéger sans surveiller.** Le natif facilite l’accès sans recopier ni observer l’activité privée de messagerie.

## Frontière de données

Le composant `NativeMessagesHub` ne reçoit aucune donnée utilisateur. Ses seules capacités sont `onOpenPath` et `onBack`.

Il n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau. Il n’utilise ni WebView, ni stockage local, ni SecureStore, ni AsyncStorage pour conserver des messages ou un choix d’identité.

Il ne lit ni message privé, ni conversation, ni participant, ni avatar, ni texte, ni date, ni compteur non lu, ni état lu/non lu. Il ne construit aucun aperçu ou résumé local de conversation.

Il n’envoie, ne modifie, ne supprime et ne marque aucun message. Toutes les mutations et règles d’accès restent dans la messagerie Web protégée existante.

## Séparation des identités

SINJIRA conserve volontairement deux contextes distincts :

- le **compte réel**, qui écrit avec le pseudo et l’avatar du compte;
- le **personnage**, qui écrit sous l’identité du personnage SINJIRA™.

Le hub natif ne choisit jamais une identité à la place de l’utilisateur, ne fusionne pas ces deux contextes et ne mémorise pas le dernier choix. La personne peut soit ouvrir le sélecteur Web existant, soit choisir explicitement l’une des deux surfaces depuis le hub.

## Destinations

- `/compte/messages.html?surface=web` — sélecteur d’identité existant;
- `/compte/messages-reels.html?surface=web` — messagerie du compte réel;
- `/compte/messages-personnage.html?surface=web` — messagerie du personnage;
- `/compte/blocages.html` — gestion des comptes bloqués;
- `/compte/regles-communaute.html` — règles de la communauté.

## Intégration native

Le hub est ouvert localement depuis `NativeHomeHub` et `NativeAlertsHub` lorsque la destination exacte `/compte/messages.html` est choisie. Les sorties du hub continuent d’utiliser `onOpenPath`, donc la navigation historique et ses protections restent la seule voie vers les surfaces Web.

Aucune modification de `App.tsx`, aucune migration SQL et aucune écriture Supabase ne sont nécessaires pour cette étape.
