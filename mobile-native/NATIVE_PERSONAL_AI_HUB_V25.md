# Hub Mon IA natif V25

## Objectif

Le hub Mon IA React Native ajoute uniquement un sas de navigation avant la fondation privée Mon IA existante. Il ne remplace ni les réglages, ni les consentements, ni les contrôles AAL2, ni l’Edge Function privée.

**L’HUMAIN AVANT TOUT.** Mon IA reste sous contrôle explicite de la personne. Le natif n’active aucun modèle, ne déduit aucun consentement et ne transforme aucune donnée personnelle en décision cachée.

## Frontière de données

Le composant `NativePersonalAiHub` ne reçoit aucune donnée utilisateur. Il reçoit seulement :

- `onOpenPath`, pour ouvrir explicitement une destination existante;
- `onBack`, pour revenir à l’accueil natif.

Il ne lit aucun réglage Mon IA, état d’activation, nom d’affichage, langue, permission de source, audit, état MFA, décision de risque ou challenge d’appareil.

Il n’appelle ni Supabase, ni Edge Function, ni RPC, ni API réseau. Il n’utilise ni WebView, ni SecureStore, ni AsyncStorage comme source de vérité.

## AAL2 et ai_private

Le hub ne décide jamais si une personne est autorisée à ouvrir ou modifier Mon IA. L’exigence AAL2 et la ressource sensible `ai_private` restent appliquées par les mécanismes d’authentification, de risque et de challenge existants côté Web/serveur.

Aucun état MFA, code de challenge, clé d’appareil ou résultat de sécurité n’est copié dans le hub natif.

## Réglages, consentements et suppression

Le hub ne crée, ne modifie et ne supprime aucun réglage Mon IA. Il n’accorde et ne retire aucun consentement de source, ne modifie aucun nom ou langue et ne déclenche pas la suppression des données Mon IA.

Ces opérations restent dans la surface Web privée et l’Edge Function `personal-ai`, qui appliquent le contrat de sécurité existant.

## Runtime V25

Le runtime reste `not_configured`. Le hub ne lance aucun modèle et ne fournit :

- aucun chat;
- aucune mémoire;
- aucune récupération de source;
- aucun provider;
- aucun profil psychologique;
- aucun clone IA après décès.

## Sources explicitement séparées

Les seules catégories prévues par la fondation actuelle sont `life_story` et `employment`, et leur récupération de contenu reste désactivée dans V25. Ouvrir Histoire de vie ou Emploi depuis le hub natif ne vaut jamais consentement.

Le **Registre personnel des consciences n’est pas une source Mon IA**. Aucune donnée du Registre n’est importée dans le hub natif et il n’est jamais ajouté automatiquement.

## Destinations permises

Le hub expose uniquement :

- `/compte/mon-ia.html?surface=web` — fondation privée Web;
- `/compte/securite.html` — Centre de sécurité;
- `/compte/histoire-de-vie.html` — espace Histoire de vie séparé;
- `/compte/emploi.html?surface=web` — espace Emploi séparé.

## Principe de sécurité

**Protéger sans surveiller.** Le hub natif ne devient ni un second stockage des préférences IA, ni une copie du moteur de sécurité, ni une passerelle directe vers les données sources. La surface Web/serveur reste la source de vérité tant que le runtime IA n’existe pas et qu’une frontière native équivalente n’a pas été conçue.
