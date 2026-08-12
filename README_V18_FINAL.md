# SINJIRA V18 — Pack final

## Architecture publique
- Accueil : SINJIRA Romans, SINJIRA Jeux, Projet Nova.
- SINJIRA : trois portails distincts — Romans, Jeux, Personnages des fans.
- Les anciens univers restent dans le dépôt mais ne sont plus mis en avant.

## Compte SINJIRA
Un seul compte sert maintenant comme :
- compte lecteur;
- compte joueur;
- compte de commentaire;
- compte de participant au Registre;
- compte de suivi des personnages.

Pages ajoutées :
- `/compte/mes-lectures.html`
- `/compte/mes-commentaires.html`
- `/compte/mes-personnages.html`

## Commentaires lecteurs
Les commentaires sont liés au compte et publiés uniquement après modération administrateur.

## Personnages des fans
Le questionnaire est lié automatiquement au `user_id`, au pseudo et au courriel du Compte SINJIRA.
Le futur personnage apparaît ensuite dans `Mes personnages`, avec :
- statut;
- description officielle;
- roman attribué;
- ou mention d’attente pour un futur roman.

## IA
L’IA est conçue comme générateur de BROUILLON uniquement.
Elle ne peut pas rendre un personnage canonique sans validation de Benoit Cantin.

Les Edge Functions utilisent `OPENAI_API_KEY` uniquement côté serveur.
Aucune clé OpenAI ne doit apparaître dans GitHub ou le JavaScript du navigateur.

Les données personnelles directes (nom légal, courriel, téléphone, date de naissance, coordonnées parentales) sont filtrées avant l’appel OpenAI.
Le paramètre `store:false` est utilisé.

## Bible des personnages
L’administration peut :
- générer/régénérer un brouillon IA;
- modifier le nom et la description;
- éditer la Bible JSON;
- attribuer un roman;
- marquer le personnage comme futur, approuvé ou publié;
- choisir ce que le fan voit dans son compte;
- supprimer définitivement les réponses sources personnelles une fois devenues inutiles.

## Administration
La console existante conserve Jeux, Documents, Joueurs, Testeurs, Playtests, Rapports et Statistiques.
V18 ajoute :
- Commentaires romans;
- Personnages fans;
- Bible personnages.

L’administrateur propriétaire reste `kingtyrano@gmail.com / AbyssTime`.


## Bible maîtresse CANON v1.0

La V18 a été alignée sur la Bible maîtresse CANON v1.0 fournie par l’auteur.

Important :
- le document maître complet n’est PAS placé dans le dépôt GitHub public;
- seuls des garde-fous de continuité non secrets sont utilisés par la fonction IA;
- les éléments `SECRET AUTEUR` restent hors du code public;
- `PROVISOIRE` est le statut par défaut d’un personnage issu d’un questionnaire;
- `CANON` doit être attribué uniquement lorsque Benoit Cantin confirme que le personnage est établi par un manuscrit officiel finalisé.


## Alignement sur les documents CANON fournis le 12 août 2026

La V18 finale utilise désormais deux sources internes officielles :
- **SINJIRA — Bible maîtresse de l’univers — CANON v1.0**;
- **Roman 1 — La Cendre du Jugement — Dossier narratif — CANON v1.0**.

Le moteur de brouillon de personnage respecte notamment :
- la hiérarchie de préséance du canon;
- le statut PROVISOIRE par défaut pour tout personnage issu d’un questionnaire;
- le verrouillage du Roman 1;
- la liste des personnages déjà établis, afin d’éviter les doublons;
- les règles du monde (aucune magie/superpouvoir établi, Réseau-Mère non omnipotent, autorité contestable);
- les mystères SECRET AUTEUR, qui ne doivent jamais être résolus ou révélés automatiquement;
- les alertes À ARBITRER, que l’IA ne peut pas trancher.

### Confidentialité du canon
Les textes complets des deux documents internes ne sont **pas** inclus dans le ZIP GitHub public.
Le contexte sensible est stocké dans une table Supabase privée sans accès `anon` ni `authenticated`.
La console administrateur peut le consulter, mais les joueurs et lecteurs ne peuvent pas y accéder.

### Protection contre les erreurs de continuité
- Un personnage généré reste `PROVISOIRE`.
- Le passage à `CANON` exige une confirmation explicite de l’auteur dans l’administration.
- L’attribution rétroactive au Roman 1 exige une confirmation explicite de décision auteur / retcon.
