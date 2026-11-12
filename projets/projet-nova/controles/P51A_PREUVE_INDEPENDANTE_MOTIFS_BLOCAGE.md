# Projet Nova — P51A : qualification de la cause du refus, pas seulement de l'état « bloqué »

**17 octobre 2026 · Contrôle de régression en lecture seule · Statut NO_GO**

## Défaut encore présent après P50Z

La PR [#668](https://github.com/M0rdr3x/BenoitCantin/pull/668) corrige l'identité des PR témoins : la bonne branche, le bon dépôt et les bons fichiers. Cependant, elle pouvait encore qualifier de « déclaration à contrôler » trois essais sans vérifier le **motif du blocage**. Une CI défaillante pouvait ainsi fausser l'essai « sans revue »; une approbation jamais obtenue pouvait fausser l'essai « approbation périmée »; une approbation manquante pouvait fausser l'essai « check défaillant ».

La [PR #670](https://github.com/M0rdr3x/BenoitCantin/pull/670), **enfant en brouillon de PR668**, renforce le validateur P50Y sans fusionner ces branches.

## Ce que doit désormais constater la lecture GitHub

| Scénario | Revues GitHub attendues | Checks obligatoires attendus |
| --- | --- | --- |
| `sans_revue` | 0 revue substantielle soumise | 3/3 réussis au SHA du HEAD |
| `approbation_perimee` | Au moins un avis antérieur APPROVED/DISMISSED d'un autre utilisateur sur un ancien SHA, et 0 APPROVED indépendant valable au HEAD | 3/3 réussis au SHA actuel |
| `check_non_satisfait` | Au moins 1 APPROVED indépendant valable au HEAD | Au moins 1 des 3 contrôles non réussi/manquant |

Les trois checks sont `no-committed-secrets`, `Contrat sécurité validation site` et `Contrat sécurité CI navigateur`, attribués à GitHub Actions, app `15368`. La présence de deux checks homonymes, une pagination incomplète, un mauvais SHA, un autre émetteur ou des revues/acteurs incomplets exige une **nouvelle vérification**. Les rapports sont non nominatifs et aucune permission d'écriture n'est utilisée.

**Limite :** « approbation périmée » ne devient pas juridiquement ou techniquement certain par la seule existence d'un avis sur un ancien SHA. L'administrateur doit vérifier la chronologie de l'essai, les règles réellement exigées et la raison de la fusion bloquée dans l'interface de GitHub. Un check manquant doit également être réellement requis par le serveur pour faire foi de l'essai.

## Comparaison indépendante (sans créer de PR témoin)

La proposition principale P51A récupère par SHA immuable :
- **avant** : PR668, `9e8d08b2a4d097e9609320cef5e9167ab3fe64bf`, 37 tests existants;
- **après** : PR670, `a39056723f21d7b50416e57b616558ecc0f3f585`, 52 tests (15 nouveaux).

Elle exerce six **sondes fictives** : absence de revue avec CI rouge, absence d'historique d'approbation, approbation encore actuelle, check défaillant sans approbation, check annoncé comme défaillant mais au vert, et absence de données d'API sur les revues. Le validateur initial doit qualifier ces déclarations de recevables; la version corrigée doit les classer en `RECETTE_REQUISE`.

Un scénario conforme fictif doit rester déclarativement recevable, **sans être qualifié de preuve serveur ni de GO**. L'outil ne remplace pas les trois essais administratifs réels. Les résultats techniques ne doivent être déclarés réussis qu'après exécution de la CI.

## Risques toujours ouverts

- La protection de la branche principale n'est pas attestée active; le suivi se fait dans [l'issue #135](https://github.com/M0rdr3x/BenoitCantin/issues/135).
- La désignation des réviseurs humains reste en attente dans [l'issue #662](https://github.com/M0rdr3x/BenoitCantin/issues/662).
- La correction [PR670](https://github.com/M0rdr3x/BenoitCantin/pull/670) n'est **pas fusionnée dans PR668**, et la correction PR668 n'est pas fusionnée dans PR667. Une future intégration devra renouveler les revues et tests sur chaque SHA modifié.
- La PR640 demeure **NE PAS FUSIONNER**. Aucun formulaire, don, adhésion, signature, paiement ni publication n'a été activé.

**Décision : NO_GO_AUTOMATIQUE, même avec la comparaison des sondes favorable.**
