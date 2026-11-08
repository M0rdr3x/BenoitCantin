# SINJIRA — Fracture V43 : autorisation des sièges humains et invisibles

**But :** préparer la migration du moteur historique à contrôle automatique `bot` vers les règles humaines Solo/Duo V36, sans toucher à la base ni autoriser le jeu en réseau.

## Deux fonctions pures et leur périmètre

- `fractureAuthorizeSeatActionV43({humans, actorHumanSeat, targetSeat, round, express, duoFirst, action})` vérifie que **l'humain authentifié côté serveur** contrôle le siège cible pendant une ronde. Actions : `keep`, `pick`, `report`, `proof`.
- `fractureAuthorizeHumanBallotV43({humans, actorHumanSeat, ballotSeat, action})` vérifie que **seul un humain réel** dépose ses propres bulletins `suspicion` et `final-accusation`. Un siège invisible ne dépose aucun bulletin supplémentaire.

La validation des numéros refuse les conversions implicites, les dépassements et les actions inconnues. Les résultats figés ne comportent **aucune identité de compte, rôle secret, main, jeton ou carte**.

## Table de contrôle héritée strictement de V36

| Partie | Siège invisible | Humain autorisé |
|---|---|---|
| Solo, 1 humain, 3 sièges | 2 et 3 | Humain nº 1, chaque ronde |
| Duo, 2 humains, 3 sièges | 3 | Alternance à chaque ronde : `duoFirst` aux rondes impaires, l'autre humain aux rondes paires |
| 3–20 humains | Aucun | Chaque humain contrôle uniquement son propre siège |
| Express, 13–20 humains | Aucun | Même principe, mais 6 rondes au lieu de 10 |

**Les deux bulletins privés ne suivent pas cette délégation.** En Solo et Duo, un seul bulletin est déposé par chaque humain réel pour le type concerné. Les cibles du bulletin sont validées par V38/V39/V40; V43 vérifie seulement la propriété de l'auteur.

## Frontière de sécurité absolument indispensable

Cette bibliothèque est **une vérification métier et non une authentification/autorisation complète**. Le serveur devra extraire `actorHumanSeat` de sa propre table de membres, en liant l'identité vérifiée `auth.uid()` à une session **encore active**, à la bonne partie et à son siège réel. Ne jamais prendre `actorHumanSeat`, `humans`, `duoFirst`, `round` ou `targetSeat` du client sans les vérifier contre l'état autoritaire sous verrou transactionnel.

Avant chaque mutation, contrôler la phase (`choose_keep`, `pick`, `report` ou `final_vote`), le tour, la version de jeu, la propriété réelle des cartes, la Preuve unique et l'idempotence. Les résultats de V43 ne doivent pas être envoyés avec une main, une identité cachée ou un vote d'autrui à un navigateur.

Le moteur historique `_fracture_start_round`, `_fracture_auto_reports` et `_fracture_advance_turn` conserve des choix automatiques. V43 **ne les remplace pas côté serveur**; cela nécessite une migration autorisée, des tests multi-comptes sur une base isolée et un déploiement protégé.

## Validation

Le workflow GitHub V43 exécute les vrais modules V36 et V43 (Solo/Duo, inversion du premier joueur, 10/6 rondes, 3–20 joueurs, bulletins strictement humains, entrées malformées et non-divulgation). Les tests ne lisent aucun utilisateur ni schéma de production.

**Aucune activation du jeu, aucun bonus de score, aucune migration SQL.** Le blocage éditorial [#857](https://github.com/M0rdr3x/BenoitCantin/issues/857) et les critères de sortie serveur [#872](https://github.com/M0rdr3x/BenoitCantin/issues/872) demeurent ouverts.

La maturité globale SINJIRA est toujours **66,5 % ≈ 67 %** (±10 points), non augmentée sur une simple bibliothèque de garde.
