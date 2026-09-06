# SINJIRA V25 — Hub Mon personnage natif

## Principe

**L’HUMAIN AVANT TOUT.** Le hub React Native Mon personnage est un sas de navigation et d’explication. Il ne devient pas la source de vérité du personnage et ne reproduit aucune fiche narrative utilisateur.

**Protéger sans surveiller.** Le composant natif ne reçoit aucune donnée de personnage et n’appelle ni Supabase, ni RPC, ni Edge Function, ni API réseau. Il ne lit pas la WebView et ne conserve aucun cache local de nom, portrait, bible, psychologie, statut ou continuité.

## Frontière avec la personne réelle

La page Web Mon personnage peut afficher une représentation narrative validée liée au compte. Sa **fiche humaine source issue du Registre reste privée**.

Le natif ne reçoit notamment aucun :

- questionnaire ou réponse humaine source ;
- brouillon ou texte brut provenant du Registre ;
- nom public ou description du personnage ;
- portrait ou chemin d’image ;
- bible narrative ou synthèse psychologique ;
- statut de préparation, visibilité ou canon ;
- roman attribué ou note narrative ;
- soumission ou identifiant interne ;
- clé reliant le compte, la personne réelle et le personnage.

La représentation narrative ne doit jamais être confondue avec la personne réelle.

## Aucune création ni décision narrative locale

Le hub ne :

- crée aucun personnage ;
- ne remplit ni n’envoie le questionnaire du Registre ;
- n’approuve, ne refuse ou n’archive aucun personnage ;
- n’attribue aucun personnage à un roman ;
- ne choisit aucun statut de canon ;
- ne décide pas de la psychologie narrative ;
- ne change pas la visibilité d’une fiche.

La règle existante d’un personnage maximum par Compte SINJIRA reste portée par la surface et les mécanismes serveur actuels, pas par un nouvel état natif.

## Réparation propriétaire côté serveur

La réparation historique `ensure_sinjira_owner_character` reste une frontière serveur authentifiée, isolée par le contrat V24.5.20.

`NativeCharacterHub` ne l’appelle pas, ne reproduit pas sa logique et ne stocke aucun résultat de réparation. Le natif n’a aucune capacité propriétaire spéciale.

## Registre des Consciences

Le Registre peut participer au processus humain de création d’un personnage, mais il reste une source distincte et privée.

Le hub natif :

- ne lit aucun contenu du Registre ;
- ne donne aucun accès alternatif à la fiche humaine source ;
- ne contourne aucun contrôle du Registre personnel ;
- ne transforme aucune confidence ou réponse brute en donnée native ;
- ne crée aucune copie locale du questionnaire.

Le Registre personnel des consciences reste soumis à son propre gate sensible et n’est pas intégré à ce hub.

## Identités cloisonnées

Le compte humain, le personnage public/narratif et les identifiants techniques privés restent des couches distinctes.

Le hub ne reçoit aucune clé interne permettant de les corréler. Une navigation vers Monde parallèle ne copie pas l’identité, la Chronique ou la continuité dans le natif.

Le canon et les changements narratifs irréversibles restent des décisions humaines et serveur selon les contrats existants.

## Navigation

Le hub expose uniquement :

- `/compte/mon-personnage.html?surface=web` ;
- `/compte/monde-parallele.html?surface=web` ;
- `/compte/securite.html` ;
- `/compte/vie-privee.html?surface=web`.

L’Accueil natif et le routeur central peuvent ouvrir `NativeCharacterHub` sans donnée. La sortie `?surface=web` vers Mon personnage est volontairement explicite afin que la fiche réelle reste chargée par la surface Web authentifiée existante.

## Hors périmètre

Ce lot n’ajoute :

- aucune migration SQL ;
- aucune écriture Supabase ou production ;
- aucune table, RPC ou Edge Function ;
- aucun stockage natif de personnage ;
- aucun changement du questionnaire Registre ;
- aucune modification de `compte/mon-personnage.html` ou de son runtime ;
- aucune nouvelle capacité propriétaire.

Le natif sert uniquement à orienter la personne sans dupliquer sa représentation narrative ni sa fiche humaine source.
