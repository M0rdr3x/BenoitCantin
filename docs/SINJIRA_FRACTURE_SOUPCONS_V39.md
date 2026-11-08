# SINJIRA™ — Fracture V39 : dépouillement privé des soupçons

**Périmètre :** édition Déduction simplifiée, section 5 (« Discussion et soupçon ») et section 6 (départage par soupçons cumulés).

## Fonctionnalité préparée

Le module pur `assets/js/sinjira-fracture-soupcons-v39.mjs` vérifie la totalité des bulletins de soupçons pour les 10 rondes standard ou les 6 rondes Express et totalise les accusations/soupçons par numéro de siège. En Solo/Duo, un **humain** possède un emplacement de soupçon par ronde; les sièges invisibles ne votent jamais à sa place.

La saisie est fournie exclusivement par le futur backend sous la forme `roundBallots[ronde][humain]` avec un numéro de siège, ou `null` **uniquement** si l'abstention a été autorisée par une règle éditoriale explicite. Une valeur manquante, `undefined`, les votes en trop, cibles invalides et conversions numériques implicites sont rejetés. Aucun nom, identifiant de compte ni bulletin individuel ne figure dans le résultat, mais les cumuls chiffrés restent **privés** jusqu'au moment de révélation autorisé.

## Politique éditoriale : aucune décision imposée par le code

- `allowAbstention` **obligatoire, booléen** : choisir si un humain peut s'abstenir. Le manuel exige une saisie par humain; la page de suspension du jeu parle de « soupçon facultatif ». La différence demeure ouverte dans l'[issue #857](https://github.com/M0rdr3x/BenoitCantin/issues/857).
- `eligibleTargets` **obligatoire** : liste exacte des numéros de sièges autorisés. Cela permet de ne pas décider dans le code si les sièges invisibles ou le siège du joueur lui-même peuvent être soupçonnés. Le choix doit être **validé éditorialement et vérifié par le serveur** avant le jeu en ligne.
- Le module ne choisit pas les règles à la place de l'administrateur et **refuse les valeurs par défaut implicites** pour ces deux choix.
- Les numéros de sièges sont **une représentation technique**, pas une identité secrète. Aucun contrôle de l'appartenance réelle d'un compte à un siège n'est fourni.

## Sécurité et architecture de mise en réseau

1. **Jamais dans le navigateur avec les bulletins privés d'autrui.** L'API future doit collecter, authentifier et autoriser chaque bulletins côté serveur.
2. Vérifier systématiquement JWT et session active, droits de lecture/écriture, partie/siège contrôlé, ordre des rondes et délai; RLS et tests inter-comptes réels seront nécessaires.
3. Conserver le vote individuel chiffré dans un stockage privé et assurer une écriture **atomique et idempotente** : un seul bulletin par humain et par ronde.
4. Lire les bulletins d'un journal serveur fiable, au lieu d'accepter `roundBallots` transmis par un client. Vérifier la clôture complète des rondes avant dépouillement.
5. Le module ne protège pas à lui seul la confidentialité ni l'intégrité : il ne fait que valider des **entrées supposées authentiques**. Les comptes, noms, mains, identités, mots de passe, adresses et jetons ne doivent jamais figurer dans les logs ou résultats.
6. Une fois le dépouillement exécuté côté serveur, ses `totals` pourront alimenter la fonction V38 `suspicionTotals`, **après** validation de la politique éditoriale et de la frontière serveur. Il ne faut pas importer V38 dans le navigateur pour tester les bulletins de vrais comptes.
7. Les sorties agrégées peuvent elles-mêmes révéler un choix, surtout en Solo; ne jamais les exposer avant la fin du scrutin autorisée.

## Vérification et critères de fermeture

- `node --test tests/games/test_fracture_soupcons_v39.mjs` : cas Solo/Duo/Express 13–20, valeurs manquantes, abstentions interdites/autorisées, politique obligatoire, numéros hors limites, cumuls complets, confidentialité structurelle.
- La CI GitHub exécute aussi les tests V36 et son validateur de contrat.
- **Aucun changement à V35, V36, V37, V38, au lobby Web ni à Supabase dans cette PR.** Aucun déploiement ni donnée personnelle manipulée.
- Le responsable doit approuver le sens des soupçons, les cibles et le score final (**issue #857**) avant intégration à une partie multijoueur réelle.

Suivi global : [#826](https://github.com/M0rdr3x/BenoitCantin/issues/826). La maturité globale reste une **estimation de 67 %** jusqu'à la livraison et à la recette des fonctionnalités restantes.
