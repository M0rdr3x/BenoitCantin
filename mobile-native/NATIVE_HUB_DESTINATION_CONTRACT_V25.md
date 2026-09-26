# Contrat des destinations des hubs natifs V25

## Objectif

Les hubs React Native SINJIRA restent des sas de navigation sans copie de données métier. Après la classification exhaustive des **44 pages** `compte/*.html` et le routage central des **31 routes natives**, leurs boutons doivent eux aussi respecter une frontière vérifiable.

**L’HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.**

Ce contrat ne déplace aucune donnée et ne crée aucune nouvelle autorisation. Il vérifie seulement les chemins déclarés dans les composants `Native*Hub.tsx`.

## Route native ou sortie Web explicite

Pour une page appartenant aux 31 routes natives :

- le chemin nu, par exemple `/compte/messages.html`, signifie **ouvrir le sas natif**;
- `?surface=web` signifie **ouvrir explicitement la surface Web existante**;
- aucun autre paramètre de requête n’est accepté dans un tableau de destinations natif;
- aucun fragment n’est ajouté à une route de sas natif.

Ainsi un futur bouton ne peut pas changer silencieusement de surface par une variante d’URL non documentée.

## Sécurité dédiée

`/compte/securite.html` reste une exception dédiée hors `NATIVE_MODULE_PATHS` :

- le chemin nu ouvre le hub Sécurité natif;
- les **cinq ancres Sécurité** approuvées restent Web : `devices-title`, `recent-title`, `travel-title`, `quick-title` et `preferences-title`;
- aucune autre ancre ni aucun paramètre de requête n’est accepté depuis un hub.

Le Mode Voyage reste donc une fonction de sécurité existante, sans GPS brut ni nouvelle collecte native.

## Accueil compte Web fail-closed

`/compte/index.html` reste une destination Web spéciale utilisée uniquement par `NativeHomeHub.tsx` lorsque l’état du compte est encore `unknown`.

- le chemin doit rester exact, sans paramètre ni fragment dans le tableau de destinations;
- il sert à laisser la surface Web authentifiée établir les capacités du compte;
- il ne doit pas être ajouté comme route native générale;
- il ne transmet aucune identité au shell : seul l’état coarse `unknown | child | nonchild` revient ensuite au mobile.

Cette destination évite d’exposer des hubs adultes avant que le compte ait été vérifié.

## Communauté Junior Web dédiée

Les surfaces `/compte/communaute-junior.html` et `/compte/regles-communaute-junior.html` restent volontairement **Web-only** et hors des 31 routes natives générales.

- elles peuvent être déclarées comme destinations uniquement depuis `NativeHomeHub.tsx`;
- elles doivent rester des chemins exacts, sans paramètre ni fragment dans les tableaux de destinations;
- elles ne deviennent jamais une permission : le serveur, les RPC Junior et la supervision parentale restent l’autorité;
- le hub Communauté natif général ne peut pas être utilisé comme substitut à la Communauté Junior.

Cette exception évite qu’un compte 11–12 ans soit redirigé vers une surface sociale générale simplement parce qu’elle existe déjà dans le routeur mobile.

## Registre personnel

Le **Registre personnel** reste hors routeur natif et extrêmement sensible. Une seule destination est admise : `/compte/registre-personnel.html`, **uniquement depuis l’accueil** `NativeHomeHub.tsx`.

Cette exception n’est valide que tant que `App.tsx` conserve le gate local du Registre avant l’ouverture Web. Le lien ne peut porter ni paramètre ni fragment. Aucun autre hub ne peut déclarer une destination vers le Registre.

Le contenu du Registre n’est jamais lu, résumé ou copié par ce garde ni par un hub natif.

## Surfaces interdites dans les tableaux de destinations

Les pages d’**authentification et MFA**, de récupération/réinitialisation de mot de passe et de **signalement de décès** ne sont pas des raccourcis de hub natif. Toute introduction de ces routes dans un `Native*Hub.tsx` doit faire échouer la CI et nécessiter une décision de sécurité explicite.

La procédure de décès reste Web/serveur avec ses validations humaines. Aucun hub ne décide d’un décès, d’une remise posthume ou d’une autre action irréversible.

## Destinations publiques internes

Les hubs peuvent pointer vers une page publique interne du site, comme un portail de projet ou la politique de confidentialité. Le chemin doit rester absolu au site, commencer par `/`, ne jamais utiliser `//` et ne contenir aucun schéma externe.

Il n’y a donc **aucune destination externe** déclarée directement dans le graphe des hubs.

## Validation automatique

`scripts/validate_mobile_native_hub_destinations_v25.py` :

- découvre dynamiquement tous les fichiers `Native*Hub.tsx`;
- extrait leurs chemins internes littéraux;
- compare les pages `compte/*.html` aux fichiers réels;
- lit `NATIVE_MODULE_PATHS` au lieu de maintenir une seconde liste de routes natives;
- exige `?surface=web` comme seule sortie Web explicite pour une route native;
- borne les cinq ancres Sécurité;
- autorise le Registre uniquement depuis l’accueil et vérifie le gate local dans `App.tsx`;
- interdit auth/MFA et signalement de décès dans les destinations natives;
- borne l’accueil compte Web fail-closed à `NativeHomeHub.tsx`;
- borne les surfaces Communauté Junior Web-only à l’accueil natif enfant;
- refuse les chemins protocol-relative, antislash et destinations externes;
- se rechaîne aux gardes de classification, routage d’intentions, navigation, secrets, coffre et TypeScript.

Aucune migration SQL, aucun secret de production et aucune écriture Supabase ne sont nécessaires pour ce contrat.
