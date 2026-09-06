# Hub Monde parallèle natif V25

## Objectif

Le hub Monde parallèle React Native ajoute une surface de navigation minimale avant la continuité Monde parallèle SINJIRA existante. Il ne remplace ni l’identité de personnage, ni la Chronique personnelle, ni les cycles, ni les histoires publiées, ni les décisions canoniques Web/serveur.

**L’HUMAIN AVANT TOUT.** Le natif ne décide jamais du canon, d’un décès, d’un mémorial ou d’une modification irréversible du personnage.

## Frontière de données

Le composant `NativeParallelWorldHub` ne reçoit aucune donnée utilisateur. Il reçoit seulement :

- `onOpenPath`, pour ouvrir explicitement une destination existante;
- `onBack`, pour revenir à l’accueil natif.

Il ne lit ni identité de personnage, ni bio, ni adhésion, ni numéro de pionnier, ni réputation, ni lieu, ni faction, ni état de vie, ni résumé narratif privé, ni réponse de cycle, ni histoire personnelle ou collective.

Il n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau. Il n’utilise ni WebView, ni SecureStore, ni AsyncStorage comme source de vérité.

## Identités cloisonnées

Le nom public du personnage, le profil du compte et l’identifiant technique privé restent des couches séparées. Le hub natif ne reçoit aucune clé interne permettant de relier ces identités.

La résolution privée compte ↔ personnage reste dans les mécanismes serveur existants. Le natif ne reconstitue pas ce lien et ne conserve aucun identifiant technique de continuité.

## Continuité et écritures

Le hub ne crée, ne modifie et n’enregistre aucune réponse de cycle, aucun état narratif et aucune histoire. Les écritures de cycle restent dans la surface Web protégée et les RPC serveur existants.

Réputation, lieu, faction, résumé narratif privé, numéro de pionnier, état de vie et historique personnel ne sont pas copiés dans React Native.

## Canon et décisions humaines

**Le canon reste une décision humaine.** Le hub ne valide aucun canon, décès, mémorial ou changement irréversible du personnage. Il n’effectue aucune décision narrative et ne devient jamais la source de vérité de la continuité.

L’IA peut éventuellement assister des tâches ailleurs dans SINJIRA selon les règles du projet, mais ce hub ne délègue aucune décision canonique à une IA.

## Destinations permises

Le hub expose uniquement :

- `/compte/monde-parallele.html?surface=web` — espace privé Web;
- `/projets/sinjira/monde-parallele/` — portail public;
- `/compte/mon-personnage.html` — surface personnage existante;
- `/compte/securite.html` — Centre de sécurité.

## Principe de sécurité

**Protéger sans surveiller.** Ajouter une surface native ne justifie pas de dupliquer la mémoire narrative, les identités privées ou les clés techniques. Tant que ces fonctions ne disposent pas d’une frontière native équivalente, leur source de vérité reste Web/serveur.
