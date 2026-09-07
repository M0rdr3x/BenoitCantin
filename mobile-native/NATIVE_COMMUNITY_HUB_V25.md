# Hub Communauté natif V25

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

`NativeCommunityHub` est un sas de navigation uniquement. Il ne devient jamais un client social, une source d’identité ou un outil de modération.

## Données volontairement absentes du natif

Le hub ne reçoit, ne lit, ne calcule et ne stocke aucun :

- nom affiché, pseudo, avatar ou profil communautaire;
- publication, commentaire, réaction ou compteur social;
- relation entre identité de compte et identité de personnage;
- état d’acceptation des règles communautaires;
- blocage, signalement, motif, preuve ou statut de modération;
- historique de consultation du fil, des membres ou des interactions.

## Deux identités séparées

La Communauté réelle et le Réseau personnage restent deux contextes distincts.

Le natif ne reçoit aucun identifiant permettant d’exposer ou de reconstruire le lien entre une personne réelle et sa représentation fictive. Une interaction de rôle-play ne devient jamais canonique par le seul fait d’exister dans le réseau social.

## Règles communautaires

Le hub ne sait pas si l’utilisateur a accepté la version courante des règles et ne peut pas enregistrer cette acceptation. `requireCommunityUser()` et la surface Web officielle restent responsables de la vérification avant publication ou messagerie.

## Modération et sécurité

Le hub ne peut pas :

- publier, modifier ou supprimer un contenu;
- aimer ou retirer une réaction;
- commenter;
- signaler ou bloquer un membre ou un personnage;
- reconstruire une preuve de signalement;
- consulter ou modifier un dossier de modération.

Les outils sociaux et de protection existants restent côté Web/serveur.

## Navigation autorisée

Le hub peut seulement ouvrir explicitement :

- `/compte/communaute.html?surface=web`;
- `/compte/reseau-personnage.html?surface=web`;
- `/compte/regles-communaute.html?surface=web`;
- `/compte/securite.html`.

## Pas de graphe comportemental

Les relations, réactions, consultations et interactions ne doivent pas être transformées par le sas natif en profil implicite, classement ou recommandation. Une communauté sert les personnes; elle ne doit pas devenir un mécanisme de surveillance sociale.
