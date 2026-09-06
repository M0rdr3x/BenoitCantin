# Hub Rencontres natif V25

## Objectif

Le hub Rencontres React Native ajoute une surface de navigation minimale avant le parcours Rencontres SINJIRA existant. Il ne remplace ni le profil Rencontres, ni le moteur de compatibilité, ni les conversations, ni les mécanismes de consentement et de sécurité Web.

**L’HUMAIN AVANT TOUT.** Le natif ne décide jamais qui une personne devrait rencontrer, ne pousse aucune relation et ne transforme jamais un score en décision humaine.

**Protéger sans surveiller.** Le natif facilite l’accès sans recopier, observer ou synthétiser l’activité relationnelle privée.

## Frontière de données

Le composant `NativeDatingHub` ne reçoit aucune donnée utilisateur. Ses seules capacités sont `onOpenPath` et `onBack`.

Il n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau. Il n’utilise ni WebView, ni stockage local, ni SecureStore, ni AsyncStorage pour conserver un profil, une préférence, un candidat, une conversation ou un consentement.

Il ne lit notamment aucune identité de genre, tranche d’âge recherchée, région, valeur, intérêt, objectif, limite personnelle, statut relationnel, admissibilité, score de compatibilité, raison de compatibilité, proposition, connexion, compteur de messages, message privé, état de dévoilement ou identité révélée.

## Aucune décision relationnelle native

Le hub ne calcule, ne classe et ne recommande aucune personne. Il ne charge aucune liste de candidats et ne produit aucun score ou motif de compatibilité.

Les contrôles 18+, le statut célibataire, la confirmation périodique et l’admissibilité restent appliqués par la surface Web et le serveur. Le hub natif ne vérifie pas ces états et ne doit jamais être considéré comme une preuve d’admissibilité.

## Dévoilement et consentement

Le seuil de 10 messages envoyés par chaque personne est uniquement une condition Web/serveur permettant de rendre le dévoilement possible. Il ne déclenche jamais un dévoilement automatique.

Le hub natif ne lit aucun compteur et n’enregistre aucun consentement de dévoilement. Le pseudo et la photo ne sont révélés que lorsque les mécanismes Web/serveur existants constatent le consentement mutuel requis.

## Registre personnel

Aucune donnée du Registre personnel n’est importée dans le hub natif. L’option volontaire existante dans Rencontres reste contrôlée dans la surface Web et ne donne jamais au hub accès aux réponses brutes du Registre.

## Signalement, blocage et première rencontre

Le hub n’envoie aucun signalement, ne bloque ou débloque aucun compte et ne conserve aucune preuve de modération. Ces actions restent dans leurs surfaces Web protégées.

Le hub ne lit ni zone de rencontre, ni préférences de sortie, ni solde de Points SINJIRA. Il ne crée, n’accepte, n’annule et ne génère aucune proposition de première rencontre. Le consentement des deux personnes et les protections de lieu public restent dans le mécanisme Web/serveur existant.

## Navigation

Les seules destinations du hub sont :

- `/compte/rencontres.html?surface=web` pour le parcours Rencontres protégé;
- `/compte/blocages.html` pour la gestion des blocages;
- `/compte/regles-communaute.html` pour les règles de respect, consentement et modération;
- `/compte/securite.html` pour la sécurité générale du compte.

Depuis `NativeHomeHub`, la destination exacte `/compte/rencontres.html` ouvre le hub Rencontres natif. Toute sortie repasse ensuite par la fonction de navigation historique fournie par le shell.

## Hors périmètre

Cette étape ne modifie pas `App.tsx`, ne crée aucune migration SQL, n’écrit rien dans Supabase et ne change aucun schéma ou RPC Rencontres. Elle ne migre aucun formulaire, score, conversation, signalement, blocage, consentement ou préparation de rencontre dans React Native.
