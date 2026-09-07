# Hub Réseau personnage natif V25

## Objectif

`NativeCharacterNetworkHub` est un sas React Native de navigation seulement avant le Réseau personnage existant.

**L’HUMAIN AVANT TOUT.** Le passage au natif ne doit jamais rendre plus facile la corrélation entre une personne réelle et son personnage fictif.

**Protéger sans surveiller.** Ce hub ne construit aucun graphe social, historique de lecture ou profil relationnel local.

## Props minimales

Le composant reçoit uniquement :

- `onOpenPath` pour une sortie volontaire vers une surface existante;
- `onBack` pour revenir à l’Accueil natif.

Il ne reçoit aucun utilisateur, courriel, profil réel, identifiant de personnage, publication, commentaire, réaction, relation, groupe, blocage, signalement, rôle propriétaire ou jeton.

## Aucune donnée sociale locale

Le hub ne lit et ne stocke :

- aucun profil `character_social_profiles`;
- aucune publication `social_character_posts`;
- aucun commentaire `social_character_comments`;
- aucune réaction `social_character_likes`;
- aucun abonnement, abonné, groupe, membre ou relation mutuelle;
- aucun compteur ou historique d’interaction;
- aucun contenu de modération, blocage ou signalement.

Il n’appelle ni Supabase, ni RPC, ni Edge Function, ni API réseau et n’utilise ni WebView, SecureStore ou AsyncStorage.

## Identités séparées

Compte réel, profil communautaire et personnage restent des couches distinctes. Le hub ne reçoit aucune clé permettant de relier ces couches et ne contient aucune adresse courriel réelle.

La correction V25 qui délègue le rôle propriétaire à `is_sinjira_owner` reste entièrement côté Web/serveur. Le hub natif n’appelle ni `is_sinjira_owner` ni `ensure_sinjira_owner_character`.

## Rôle-play et canon

Le Réseau personnage reste un espace de rôle-play. Le natif ne rend aucune publication canonique et ne décide ni continuité, ni canon, ni changement irréversible d’un personnage.

## Mutations interdites

Le hub ne peut pas :

- publier, modifier ou supprimer un contenu;
- commenter ou réagir;
- suivre ou ne plus suivre;
- rejoindre ou quitter un groupe;
- bloquer, débloquer ou signaler;
- réparer un personnage ou déterminer un rôle propriétaire.

Toutes ces opérations restent dans les surfaces authentifiées Web/serveur existantes.

## Destinations

Le sas expose seulement :

- `/compte/reseau-personnage.html?surface=web`;
- `/compte/communaute.html?surface=web`;
- `/compte/mon-personnage.html?surface=web`;
- `/compte/securite.html`.

## Source de vérité

Le Web et le serveur restent la source de vérité des identités, contenus, relations et protections sociales. Le hub ne conserve aucun résumé local.

Ce lot ne modifie pas `App.tsx`, n’ajoute aucune migration SQL et n’effectue aucune écriture Supabase ou production.
