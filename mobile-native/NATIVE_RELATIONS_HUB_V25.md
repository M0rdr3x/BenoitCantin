# Hub Relations natif V25

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

`NativeRelationsHub` est un sas de navigation uniquement. Il ne devient jamais une source de vérité pour les relations privées, la tranche d’âge ou la supervision jeunesse.

## Données volontairement absentes du natif

Le hub ne reçoit, ne lit, ne calcule et ne stocke aucun :

- nom, pseudo, type de relation, date ou note privée;
- tranche d’âge ou statut adulte / jeunesse;
- code d’autorisation parentale à usage unique;
- identifiant ou statut d’un lien de supervision;
- rôle de parent ou tuteur;
- métadonnée de contact autorisée;
- contenu privé de message;
- compteur de relations, codes ou liens de supervision.

## Supervision jeunesse

Le serveur décide quels outils sont disponibles selon l’état du compte. Le hub natif ne connaît pas la tranche d’âge et ne déduit jamais qu’un utilisateur est adulte, mineur, en attente de supervision ou supervisé.

## Codes parentaux

Le hub ne peut pas :

- générer un code parental;
- afficher un code existant;
- lire ou saisir un code reçu;
- valider ou échanger un code;
- copier un code dans le presse-papiers;
- mémoriser un code, même temporairement.

Les codes restent dans la surface Web authentifiée et sont soumis aux règles serveur d’expiration et d’usage unique.

## Liens de supervision

Le hub ne crée, ne valide, ne révoque et ne liste aucun lien tuteur–mineur. Il ne reçoit pas le droit `can_view_contact_metadata` et ne doit jamais étendre ce droit au contenu privé des messages.

## Relations privées

Les relations déclaratives restent privées et distinctes des liens de supervision vérifiés. Le natif ne construit aucun graphe familial et n’utilise pas ces relations pour profiler l’utilisateur ou son entourage.

## Navigation autorisée

Le hub peut seulement ouvrir explicitement :

- `/compte/relations.html?surface=web`;
- `/compte/securite.html`;
- `/compte/vie-privee.html`.

Aucun `Supabase`, RPC, `fetch`, WebView, SecureStore, AsyncStorage, notification ou accès biométrique n’est ajouté au composant.
