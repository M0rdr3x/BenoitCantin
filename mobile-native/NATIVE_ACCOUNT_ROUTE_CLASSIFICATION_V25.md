# Classification exhaustive des routes du compte V25

## Objectif

Le dossier `compte/` contient les surfaces privées, sensibles, contextuelles et historiques de SINJIRA. Une page ne doit jamais devenir implicitement « native » ou implicitement « Web » simplement parce qu’elle a été ajoutée au dépôt.

Cette classification impose donc qu’**every `compte/*.html` appartienne à une catégorie explicite et unique**. Le garde CI compare les fichiers réels du dépôt à cette classification et échoue dès qu’une page apparaît sans décision architecturale.

**L’HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.**

Cette étape ne migre aucune donnée, ne change aucune règle serveur et ne rend aucune nouvelle surface accessible nativement.

## État de référence

Le dépôt contient actuellement **42 pages HTML** directement sous `compte/`.

Elles sont réparties dans sept catégories disjointes :

1. 31 routes de sas dans `NativeModuleRouter`;
2. 1 accueil Web de repli du compte;
3. 1 surface Sécurité avec hub natif dédié hors `NativeModuleRouter`;
4. 1 Registre personnel Web avec garde local ponctuel puis protections serveur;
5. 5 flux Web d’authentification/MFA;
6. 1 procédure Web sensible de signalement de décès;
7. 2 pages Web contextuelles ou informatives.

Aucune page n’est laissée « non classée ».

## 1. Routes de sas `NativeModuleRouter` — 31

Ces chemins transportent uniquement une intention de navigation vers un hub natif déjà borné. Les données et actions réelles restent dans leurs surfaces Web/serveur lorsqu’elles sont nécessaires.

### Messages

- `/compte/messages.html`;
- `/compte/messages-reels.html`;
- `/compte/messages-personnage.html`.

### Rencontres et emploi

- `/compte/rencontres.html`;
- `/compte/emploi.html`.

### Bibliothèque et jeu

- `/compte/bibliotheque.html`;
- `/compte/mes-lectures.html`;
- `/compte/documents.html`;
- `/compte/playtests.html`;
- `/compte/mes-parties.html`;
- `/compte/contributions.html`.

### Communauté et protections sociales

- `/compte/communaute.html`;
- `/compte/mes-commentaires.html`;
- `/compte/blocages.html`;
- `/compte/regles-communaute.html`;
- `/compte/moderation.html`.

`moderation.html` reste uniquement une entrée vers le sas Communauté : les décisions motivées, échéances, textes d’appel et résultats de révision restent Web/serveur avec **révision humaine obligatoire**.

### Personnage, relations et Monde

- `/compte/reseau-personnage.html`;
- `/compte/relations.html`;
- `/compte/monde-parallele.html`;
- `/compte/mon-personnage.html`;
- `/compte/mes-personnages.html`.

### Commerce

- `/compte/mes-achats.html`;
- `/compte/marche.html`;
- `/compte/jetons.html`;
- `/compte/licences.html`.

### Vie privée, profil et outils personnels

- `/compte/mon-ia.html`;
- `/compte/histoire-de-vie.html`;
- `/compte/notifications.html`;
- `/compte/profil.html`;
- `/compte/vie-privee.html`;
- `/compte/parametres.html`.

## 2. Accueil Web de repli — 1

- `/compte/index.html`.

L’Accueil natif réel de l’application est `/app/` et rend `NativeHomeHub`. `compte/index.html` reste une surface Web du compte et un point de retour sûr utilisé notamment quand une surface sensible est fermée en arrière-plan. Il **n’est pas** ajouté à `NativeModuleRouter`.

## 3. Sécurité dédiée hors routeur — 1

- `/compte/securite.html`.

Le raccourci Sécurité du shell ouvre `NativeSecurityHub` directement. La page Web `securite.html` reste la surface canonique pour les opérations Web/serveur qui ne sont pas reproduites dans le natif, notamment Mode Voyage.

Cette route ne doit pas être dupliquée dans `NativeModuleRouter`.

## 4. Registre personnel Web gardé — 1

- `/compte/registre-personnel.html`.

Le Registre reste volontairement hors `NativeModuleRouter`. Son ouverture passe par le garde local ponctuel déjà présent dans `App.tsx`, puis par les protections renforcées côté SINJIRA.

Le natif ne reçoit, ne met en cache et n’exporte aucun contenu du Registre. Cette classification ne réduit ni la fenêtre locale courte, ni le verrouillage en arrière-plan, ni le MFA, ni le moteur de risque.

## 5. Authentification et MFA Web — 5

- `/compte/connexion.html`;
- `/compte/inscription.html`;
- `/compte/mot-de-passe-oublie.html`;
- `/compte/reinitialiser-mot-de-passe.html`;
- `/compte/mfa.html`.

Ces pages sont des étapes d’établissement, de récupération ou de renforcement de l’identité de session. Elles restent hors du routeur de modules métier.

## 6. Procédure décès Web sensible — 1

- `/compte/signaler-deces.html`.

Le signalement d’un décès reste une procédure Web/serveur distincte. Aucun hub natif générique ne doit pouvoir valider un décès, déclencher une remise posthume ou prendre une décision irréversible à partir d’une simple intention de navigation.

## 7. Pages Web contextuelles ou informatives — 2

- `/compte/projet.html` : vue dynamique d’un projet sélectionné dans la Bibliothèque;
- `/compte/confidentialite-joueur.html` : page d’information qui renvoie vers le Centre Vie privée pour les actions réelles.

Ces pages restent Web parce que leur rôle n’est pas celui d’un module natif autonome.

## Invariant CI

`validate_mobile_native_account_route_classification_v25.py` doit vérifier :

- que les 42 fichiers réels sont exactement couverts par les catégories ci-dessus;
- que les catégories sont disjointes;
- que les 31 routes natives sont exactement celles déclarées dans `NATIVE_MODULE_PATHS`;
- qu’aucune route Web sensible ou spéciale n’est présente dans `NativeModuleRouter`;
- que `App.tsx` conserve les marqueurs du hub Sécurité, du Registre gardé et de l’Accueil natif `/app/`;
- que toute route documentée existe réellement sur disque;
- que la CI centrale revalide ce garde.

Une nouvelle page `compte/*.html` doit donc provoquer un choix explicite : sas natif existant/nouveau, sécurité dédiée, Web sensible, Web contextuel ou autre catégorie documentée. Elle ne peut pas passer silencieusement.

## Principe de sécurité

La classification n’est pas un mécanisme de collecte. Elle ne lit aucune donnée utilisateur et ne modifie aucun comportement serveur. Elle sert uniquement à empêcher qu’une future évolution de navigation contourne par accident une frontière déjà décidée.
