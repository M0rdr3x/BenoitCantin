# P50R — Plan de simulation d’intégration avant revues institutionnelles

**16 octobre 2026 · Projet Nova · Preuve technique reproductible · NO_GO**

## Décision préparatoire

Les modifications de participation et d'identité du Projet Nova sont proposées dans des PR ouvertes, non fusionnées et sans approbations indépendantes attestées. Après 40 tests du correctif PR 657 et les comparaisons P50Q, le blocage technique restant pertinent est une **vérification sur un arbre commun** plutôt que sur des copies de branches séparées.

**P50R n'est ni une fusion ni une publication.** Les commandes de merge ne s'exécutent qu'à l'intérieur du conteneur temporaire GitHub Actions, sans identifiants de push, et laissent le dépôt `main` inchangé.

### Références immuables

| Étape | SHA de la version figée | Usage |
| --- | --- | --- |
| `main` | `9ed5f70cbe7022f25a679346a1288701f3b09067` | Base exacte |
| PR 636 | `6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb` | Corrections participation et avis légal |
| PR 655 | `8541f761be8dbabda0c3f024f8969562ab816bc7` | Premier renforcement du validateur |
| PR 657 | `f67abe43b7223d0f59ee1efb6cf883d558eddfb5` | Renforcement URL et vrai lien courriel |
| PR 638 | `e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e` | Identité, statuts et manifeste |
| PR 640 | `332afe7d9d73390feb41b0deb588692f3c73d48d` | **EXCLUE : ne pas fusionner** |

Les six PR restent soumises à leur propre revue. La présence d'un SHA dans le protocole ne constitue pas un mandat.

## Ordre et méthode de vérification

1. Lire `main` au commit exact dans un **espace jetable** sous Actions, avec `persist-credentials: false`.
2. Simuler localement les merges 636, 655, 657 puis 638 par quatre commandes `git merge --no-ff`. Aucun `git push`, aucune API de fusion et aucune branche distante n'est modifiée.
3. Faire échouer le workflow **sans contournement** en cas de conflit de merge; ne pas effectuer de résolution arbitraire.
4. Contrôler les **14 chemins exacts** attendus : 5 apportés par la PR 636 et 9 apportés par la PR 638; les PR 655/657 modifient les mêmes deux fichiers de scripts inclus dans ces cinq chemins.
5. Exiger les blobs Git des pages `participer.html`, `avis-legal.html` et `code-conduite.html` aux empreintes déjà contrôlées.
6. Vérifier la concordance SHA-256 entre `official/reference/statuts.md` et son manifeste `data/sources.json`.
7. Contrôler que le commit de la PR 640 **n'est pas un ancêtre** de la simulation, et que l'arbre local n'a aucun fichier modifié non engagé.
8. Lancer les **40 tests de participation**, le validateur des cinq pages candidates et les tests/contrôles d'identité directement dans l'arbre issu de la simulation.
9. Conserver un rapport JSON expurgé de toute donnée personnelle, avec la décision `NO_GO_AUTOMATIQUE`.
10. Une seconde vérification de l'état de `main` hors runner confirme qu'aucune opération réelle de publication ou fusion n'a été entreprise.

### Conditions de réussite technique

Un résultat CI vert signifie seulement :
- la simulation à ces SHA ne rencontre pas de conflit bloquant;
- les 14 chemins attendus forment le diff de la simulation;
- le manifeste documentaire et les trois pages de référence concordent;
- les suites de tests locales et les scanners réussissent.

**Il ne signifie jamais** : revue humaine, qualification juridique du porteur, autorisation électorale, confidentialité des courriels auditée, sauvegarde testée, approbation budgétaire ni site effectivement corrigé.

### Si un test échoue

L'échec est un fait technique à conserver dans les journaux. Noter le **stade** (conflit de merge, chemins supplémentaires, SHA invalide, code non compilable, tests, textes HTML, identité ou manifeste) et l'empreinte du commit fautif; résoudre le problème dans une **nouvelle proposition de code soumise à revue**, puis recommencer la simulation sur des SHA nouvellement figés. Aucune bascule automatique de NO_GO vers GO.

## Décisions humaines encore à obtenir

1. Une personne habilitée réalise la revue de sécurité du correctif PR 657 et décide de son éventuelle intégration vers PR 655.
2. Une revue indépendante examine l'intégration éventuelle PR 655 vers PR 636, après nouveau passage de CI.
3. Une revue juridique et éditoriale examine séparément la PR 638, les documents de statuts non adoptés et leur présentation.
4. Un responsable de confidentialité qualifie le régime du courriel de contact et les obligations applicables sans publier de données privées.
5. Le décideur compétent approuve ou refuse **par écrit** un périmètre de publication limité, avec plan de sauvegarde et restauration et identité des opérateurs.
6. Seulement après une modification autorisée : recette HTTP du site public, contrôles des liens, formulaires, paiements, redirections et transparence de l'état institutionnel.

**PR 640 — NE PAS FUSIONNER, même en cas de réussite de P50R.**

Le Projet Nova demeure l'identité active; « Parti Nova » est prospectif. Base maîtresse V3.40, P2-C0-49, W0/W1/W2–W4, E26, pouvoirs et preuves financières : non levés par cette étape. Aucune adhésion, sollicitation, signature électorale, contribution, paiement ou nouveau formulaire n'est activé.

*Ce dossier est un contrôle logiciel et ne se substitue pas aux professionnels habilités à engager le projet.*
