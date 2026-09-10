# SINJIRA / Benoit Cantin — Contrat de personnalité publique V25

## Intention

La personnalité du portail doit se ressentir comme une **direction de conception**, jamais comme une fiche biographique détaillée.

Le même noyau traverse les environnements :

- **L’humain avant tout** : l’outil, le système ou l’institution ne passe pas devant la personne.
- **Protéger sans surveiller** : minimiser ce qui doit être observé, conservé ou relié.
- **Capacité d’agir** : aider la personne à comprendre ce qu’elle peut réellement faire ensuite.
- **Autonomie** : éviter de créer une dépendance inutile lorsqu’un système peut rendre l’utilisateur plus capable.
- **Long terme** : montrer les coûts, dépendances et conséquences qui apparaissent après le bénéfice immédiat.
- **Réversibilité** : préserver une voie de correction lorsque l’irréversible n’est pas indispensable.
- **Liberté de choix** : proposer des chemins compréhensibles plutôt qu’imposer silencieusement une décision.
- **Transparence et responsabilité** : rendre les règles, limites, décisions et conséquences lisibles.

## Expression par environnement

### Portail Benoit Cantin

Le portail porte la synthèse : autonomie, capacité d’agir, conséquences à long terme et options ouvertes. Il doit donner l’impression d’entrer dans des projets construits pour durer plutôt que dans une simple vitrine.

### SINJIRA™

Signature : **« L’humain avant tout. Protéger sans surveiller. »**

La personnalité s’exprime par la séparation des identités, la minimisation des données, le choix humain et la prudence autour des décisions irréversibles. La protection ne doit jamais devenir une permission de surveiller davantage.

### Projet Nova

La personnalité s’exprime par un pouvoir compréhensible, traçable, encadré et corrigeable. Une proposition importante doit pouvoir exposer ses coûts, ses risques, ses responsables, ses critères de réussite et ses mécanismes de correction.

Ce contrat de personnalité n’ajoute ni ne remplace aucune position politique du corpus Nova. Il décrit seulement la manière dont l’environnement doit présenter ses décisions et ses mécanismes.

### Futurax

La technologie doit augmenter la capacité d’agir plutôt que créer une dépendance de plus. Les prototypes sont évalués au-delà de l’effet immédiat : durabilité, réparabilité, coûts futurs, dépendances et possibilité de remplacement comptent aussi.

### Lumina

La technologie reste au service de la personne. Une présence intelligente doit rester explicable sur ce qu’elle fait, ce qu’elle ne fait pas et où sont ses limites. Le choix libre ne doit pas être remplacé par la friction, la confusion ou une surveillance implicite.

### Chroniques des Mondes Fracturés

La personnalité devient narrative : les choix ont des conséquences, la liberté a un poids et une rupture peut encore devenir un nouveau départ. Quand le récit le permet, préserver une voie de reconstruction est plus fidèle au projet qu’un irréversible gratuit.

## Règles de confidentialité

Cette couche publique ne doit jamais devenir un mécanisme de profilage de son auteur ou de ses visiteurs.

Elle doit rester :

- statique et présentationnelle ;
- dérivée uniquement du chemin public courant ;
- sans lecture de compte, profil, identité, stockage local, géolocalisation, query-string ou fragment ;
- sans télémétrie, analytics, cookie, beacon ou appel d’API ;
- sans publication d’expériences personnelles privées, de préférences intimes ou d’informations qui n’ont pas été choisies comme principes publics du projet.

## Implantation

`/assets/js/site-personality-v25.js` choisit un environnement à partir de `window.location.pathname` uniquement et insère une section accessible juste avant le pied de page. Il construit le DOM avec `textContent`, sans HTML provenant d’une donnée externe.

`/assets/css/site-personality-v25.css` fournit un composant sobre, responsive et compatible avec `prefers-reduced-motion`.

Les deux points d’entrée historiques (`/assets/js/site.js` et `/projets/projet-nova/script.js`) chargent le même module partagé afin que les environnements ne développent pas des versions contradictoires de cette personnalité.

## Évolution

Toute nouvelle personnalité d’environnement doit rester une déclinaison de ces principes publics. Une nouvelle capacité dynamique, un accès à des données utilisateur ou une personnalisation comportementale exige une revue séparée : ce contrat ne l’autorise pas.
