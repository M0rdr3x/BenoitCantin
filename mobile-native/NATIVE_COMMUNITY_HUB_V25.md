# Hub Communauté natif V25

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

`NativeCommunityHub` est un sas de navigation uniquement. Il ne devient jamais un client social, une source d’identité, un outil de blocage ou un moteur de modération et d’appel.

## Données volontairement absentes du natif

Le hub ne reçoit, ne lit, ne calcule et ne stocke aucun :

- nom affiché, pseudo, avatar ou profil communautaire;
- publication, commentaire, réaction ou compteur social;
- relation entre identité de compte et identité de personnage;
- état d’acceptation des règles communautaires;
- liste de comptes bloqués, blocage, signalement, motif ou preuve;
- identifiant de décision de modération, règle appliquée ou exposé des motifs;
- durée de mesure, date de fin, date limite d’appel ou niveau d’urgence;
- texte d’appel, statut d’appel, date de soumission, motif de révision ou résultat de révision humaine;
- historique de consultation du fil, des membres ou des interactions.

## Deux identités séparées

La Communauté réelle et le Réseau personnage restent deux contextes distincts.

Le natif ne reçoit aucun identifiant permettant d’exposer ou de reconstruire le lien entre une personne réelle et sa représentation fictive. Une interaction de rôle-play ne devient jamais canonique par le seul fait d’exister dans le réseau social.

## Règles communautaires

Le hub ne sait pas si l’utilisateur a accepté la version courante des règles et ne peut pas enregistrer cette acceptation. `requireCommunityUser()` et la surface Web officielle restent responsables de la vérification avant publication ou messagerie.

## Blocages

Le chemin `/compte/blocages.html` peut ouvrir le sas Communauté, mais la liste des comptes bloqués n’est jamais chargée dans React Native. Ajouter, retirer ou inspecter un blocage reste une action Web/serveur explicite via `/compte/blocages.html?surface=web`.

Le hub ne permet donc pas de reconstruire un graphe de personnes bloquées, signalées ou consultées.

## Décisions de modération et appels

### Aucun dossier d’appel dans le natif

Le chemin `/compte/moderation.html` peut ouvrir le sas Communauté, mais le dossier réel reste exclusivement dans `/compte/moderation.html?surface=web` et ses contrôles serveur.

Le hub ne peut pas :

- appeler `moderation_my_decisions` ou `moderation_submit_appeal`;
- consulter une règle appliquée, un exposé des motifs, une durée, une échéance ou un niveau d’urgence;
- lire, préparer, conserver, envoyer ou retirer un texte d’appel;
- maintenir ou renverser une décision;
- déterminer l’issue d’un appel ou remplacer la révision humaine.

La protection historique V24.4.90 reste la source de vérité : décision humaine motivée, appel interne gratuit, délai d’appel serveur, masquage réversible et **révision humaine obligatoire**. Le natif et l’IA ne tranchent jamais un appel.

## Modération et sécurité

Le hub ne peut pas :

- publier, modifier ou supprimer un contenu;
- aimer ou retirer une réaction;
- commenter;
- signaler, bloquer ou débloquer un membre ou un personnage;
- reconstruire une preuve de signalement;
- consulter ou modifier un dossier de modération.

Les outils sociaux et de protection existants restent côté Web/serveur.

## Navigation autorisée

Le hub peut seulement ouvrir explicitement :

- `/compte/communaute.html?surface=web`;
- `/compte/mes-commentaires.html?surface=web`;
- `/compte/reseau-personnage.html?surface=web`;
- `/compte/regles-communaute.html?surface=web`;
- `/compte/blocages.html?surface=web`;
- `/compte/moderation.html?surface=web`;
- `/compte/securite.html`.

## Pas de graphe comportemental

Les relations, réactions, consultations, blocages et interactions ne doivent pas être transformés par le sas natif en profil implicite, classement ou recommandation. Une communauté sert les personnes; elle ne doit pas devenir un mécanisme de surveillance sociale.
