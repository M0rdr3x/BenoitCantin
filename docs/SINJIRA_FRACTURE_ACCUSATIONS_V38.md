# SINJIRA™ — Fracture V38 : accusations finales et départage

**Référence :** `projets/sinjira/jeux/fracture-du-reseau-mere/regles.html`, édition Déduction simplifiée.
**Statut :** brique de calcul privée seulement. **Aucun lobby, aucune migration ni changement de production.**

## Contrat métier implémenté

- Chaque **humain** remet exactement **un bulletin** et y désigne autant de **sièges distincts** que d'agents Réseau-Mère à la table. Aucun vote supplémentaire n'est ajouté pour les sièges invisibles Solo/Duo.
- Le joueur humain ne peut pas s'accuser lui-même. Les sièges invisibles restent des cibles possibles : sinon l'accusation Solo serait mathématiquement impossible.
- Les numéros de sièges doivent correspondre à la table officielle (3 à 20 sièges); les doublons, votes manquants, votes excédentaires et valeurs non entières sont refusés.
- Après clôture du scrutin, le calcul regroupe les voix par siège. Il prend les sièges les plus accusés, à concurrence du nombre d'agents à identifier.
- **En cas d'égalité au seuil**, les soupçons **cumulés** départagent; si l'égalité persiste, le résultat porte `draw-required` et liste les candidats ex æquo. Un serveur de confiance doit effectuer un tirage au sort cryptographiquement sûr et auditable. Aucune randomisation dans le navigateur.
- Les bulletins individuels ne figurent **pas** dans le résultat agrégé; seules les statistiques par siège sont retournées.

## Sécurité et confidentialité — conditions avant usage réseau

1. Les bulletins et soupçons sont **confidentiels** : les recevoir et les traiter dans une fonction serveur autorisée. Ne jamais transmettre les bulletins d'autrui au client ni les écrire dans des logs.
2. Authentifier chaque humain, vérifier la présence dans la partie, son numéro de siège, l'état clos des rondes, l'unicité de son bulletin et empêcher toute modification après clôture.
3. Rassembler les bulletins dans une transaction serveur atomique avec contrôle de version; bloquer les reprises de requête et les scrutins partiels. Les tableaux d'entrée du module ne sont **jamais** des données client fiables.
4. Lire le cumul des soupçons dans un stockage serveur protégé. Le paramètre `suspicionTotals=null` est utile aux tests, **pas** comme substitut à des soupçons historiques réels. Ne calculer l'agrégation qu'après validation de tous les bulletins.
5. Protéger et auditer le résultat de tirage aléatoire externe; `fractureApplyFinalDrawV38` vérifie uniquement l'appartenance des gagnants au groupe ex æquo, **pas** l'authenticité d'un tirage.
6. La liste des agents secrets doit rester côté serveur; le modèle V38 ne reçoit, ne conserve ni ne révèle les identités des factions. Aucune mise à jour Supabase ni activation Web n'est autorisée par cette PR.
7. Les résultats agrégés eux-mêmes sont potentiellement révélateurs; ne les publier qu'au moment approuvé par les règles, après clôture du scrutin.

## Points éditoriaux à valider AVANT une intégration des scores

Le manuel officiel décrit la désignation d'un nombre d'agents parmi les sièges les plus accusés et un départage au seuil. En revanche, la feuille de score V35 exige actuellement `correct + incorrect = humains × agents` (tous les choix individuels) pour attribuer les bonus de trois points. Il faut confirmer par une décision éditoriale si le bonus final s'applique **aux sièges désignés collectivement** ou **à chaque accusation individuelle**.

**V38 ne modifie donc ni le score V35 ni l'attribution du bonus final**, afin de ne pas figer une contradiction entre règles. Il constitue seulement un décompte technique des voix et égalités et n'est pas prêt à être activé.

## Validation

- 9 tests Node locaux ont réussi sur le module et une simulation des exports de V36 (1, 2, 3, 5 et 20 humains; exclusions, cumuls, égalités, tirage externe et confidentialité).
- La CI GitHub doit rejouer les tests sur le **véritable V36**, ainsi que la suite V36 de non-régression, au SHA exact de la PR. Aucun résultat CI ne doit être déduit des seuls tests locaux.
- Revue de sécurité, choix éditorial explicite et tests multi-comptes en environnement isolé restent obligatoires avant fusion fonctionnelle.

## Lien avec le programme complet

Suivi [#826](https://github.com/M0rdr3x/BenoitCantin/issues/826). Cette étape ne justifie **aucune hausse automatique** de la maturité globale estimée à 67 %.
