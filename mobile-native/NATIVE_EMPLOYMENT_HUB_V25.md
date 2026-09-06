# Hub Emploi natif V25

## Objectif

Le hub Emploi React Native ajoute une surface de navigation minimale avant l’espace Emploi SINJIRA existant. Il ne remplace ni le profil professionnel privé ni le suivi de candidatures Web, qui restent les seules sources de vérité.

**L’HUMAIN AVANT TOUT.** Les renseignements professionnels appartiennent à la personne et ne sont utilisés que lorsqu’elle choisit explicitement de les saisir ou de les consulter.

**Protéger sans surveiller.** Le natif facilite l’accès sans copier ni observer l’activité professionnelle privée.

## Frontière de données

Le composant `NativeEmploymentHub` ne reçoit aucune donnée utilisateur. Ses seules capacités sont `onOpenPath` et `onBack`.

Il n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau. Il n’utilise ni WebView, ni stockage local, ni SecureStore, ni AsyncStorage pour conserver un profil, une candidature ou une préférence professionnelle.

Il ne lit ni titre professionnel, ni résumé, ni compétence, ni préférence de travail, ni employeur, ni poste, ni lien source, ni statut, ni date, ni prochaine étape, ni note privée.

Il ne crée, ne modifie, ne supprime et ne classe aucune candidature. Il ne reproduit aucun formulaire Emploi dans le natif.

## Séparation des usages

Le hub ne récupère automatiquement aucune donnée depuis :

- le Registre personnel;
- Histoire de vie;
- Rencontres;
- les relations;
- les renseignements de sécurité;
- la localisation de sécurité;
- le Mode Voyage.

Les renseignements de sécurité servent à protéger le compte, jamais à classer une candidature.

## Navigation

La destination principale ouvre `/compte/emploi.html?surface=web`, donc la surface Web privée existante et ses règles d’accès. Les raccourcis Vie privée, Sécurité et Paramètres restent eux aussi des navigations vers les surfaces protégées existantes.

Depuis `NativeHomeHub`, la destination exacte `/compte/emploi.html` ouvre le hub Emploi natif. Toute sortie du hub repasse ensuite par la fonction de navigation historique fournie par le shell.

## Hors périmètre

Cette étape ne modifie pas `App.tsx`, ne crée aucune migration SQL, n’écrit rien dans Supabase et ne change aucun schéma de données. Elle ne transforme pas SINJIRA en moteur d’offres d’emploi et n’ajoute aucun classement ou recommandation d’emploi.
