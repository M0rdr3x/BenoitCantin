# P50T — Porte de revues effectives et dossier de décision responsable

**Projet Nova · 16 octobre 2026 · Décision institutionnelle : NO_GO**

## 1. Résultat d'inventaire à l'ouverture

La consultation en direct des API GitHub donne **0 revue soumise** et **0 demande de reviewer en attente** pour chacune des six PR 636, 638, 655, 657, 659 et 660. Toutes sont ouvertes en brouillon et non fusionnées. `main` reste au commit `9ed5f70cbe7022f25a679346a1288701f3b09067`. La PR 640 (`332afe7d9d73390feb41b0deb588692f3c73d48d`) reste **NE PAS FUSIONNER**.

Le contrôle P50S a confirmé ses 17 tests, les preuves CI P50Q et P50R au SHA, mais **n'a apporté aucune approbation humaine**. P50T transforme ce constat en **porte CI dédiée explicitement bloquée**, plutôt que de laisser un contrôle technique vert se confondre avec une autorisation de fusion.

## 2. Trois décisions à ne jamais confondre

| Niveau | Preuve possible | Que permet-elle? |
| --- | --- | --- |
| Reproductibilité technique | Tests sur SHA, validations de contenu, simulation locale de fusion | Conclure sur les scénarios testés, pas autoriser la publication |
| Revue de code GitHub | Revue formelle `APPROVED` déposée par une personne distincte de l'auteur, non Bot, sur le HEAD actuellement présenté | Confirmer qu'une approbation de code a été enregistrée; **ne prouve pas** le mandat, la compétence juridique ni l'indépendance institutionnelle |
| Autorisation réelle de publier | Mandat du porteur, décision du responsable habilité, conformité juridique applicable, plan de restauration, traitement des données et recette ciblée | Peut contribuer à une autorisation humaine distincte, jamais inférée du code ou de la CI |

**P50T ne donne jamais de GO** et ne soumet aucune demande de revue au nom d'une personne sans savoir qu'elle est autorisée à revoir cette PR. Les approbations requises doivent être obtenues par le mainteneur ou la gouvernance réellement habilitée.

## 3. Deux portes exécutables

### Porte prioritaire — correctif PR 657 et identité PR 638

- **PR 657** — correctif supplémentaire du validateur. HEAD attendu `f67abe43b7223d0f59ee1efb6cf883d558eddfb5`.
- **PR 638** — identité publique et projets de statuts non adoptés. HEAD attendu `e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e`.

Si une approbation de revue **au commit exact** est absente, le job `P50T - approbations indépendantes requises` doit **échouer** avec `P50T_REVIEW_GATE_BLOCKED`. Cet échec est **intentionnel et honnête** : il documente l'absence d'approbation, il ne signifie pas que les 40 tests de P50Q ont échoué.

### Porte complète — dépendances et simulation

La porte complète ajoute trois PR : **655 → 636**, plus **659** pour la revue de la simulation. Elle ne peut être franchie avec des approbations prises sur des SHA expirés. Les approbations de PR 657 et PR 638 demeurent aussi requises.

**Attention aux révisions après intégration** : une intégration future PR657 → PR655 et PR655 → PR636 produit de nouveaux commits et invalide les contrôles figés des anciennes versions; il faut actualiser les références, rejouer les suites de tests, réexaminer le diff et obtenir les revues nécessaires.

## 4. Commentaires et critères proposés aux réviseurs habilités

### Dossier de revue PR 657 — qualité du scanner de participation

**Périmètre** : `scripts/validate_nova_publication_p50b.py` et ses 40 tests. Vérifier :
1. Reconnaissance des destinations de formulaires et paiements, protocol-relative, pourcentages encodés et scripts inline.
2. Distinction des liens légitimes, faux positifs, liens de contact non visibles et attributs HTML spécifiques.
3. Couverture insuffisante des scripts externes, des routes serveur, des prestataires nouveaux et des chemins de collecte non répertoriés.
4. Préservation de l'interdiction des paiements, formulaires externes, signatures et adhésions; pas de collecte de preuves individuelles.
5. Tests au **HEAD final**, demandes de changements explicites en cas de défaut, puis avis traçable.

### Dossier de revue PR 638 — identité et normes institutionnelles

**Périmètre** : neuf fichiers de PR 638, identité active « Projet Nova », « Parti Nova » seulement futur/conditionnel. Vérifier :
1. Tous les libellés HTML, métadonnées, README et liens structurants.
2. Projet de statuts **non adopté**, manifeste SHA-256 de `official/reference/statuts.md`.
3. Absence d'affirmation d'enregistrement électoral ou d'autorité institutionnelle non démontrée.
4. Aucune confusion entre archives historiques SCQ et appellation du projet actif.
5. Workflow de validation de l'identité, faux positifs et limites du périmètre texte par rapport aux PDFs/illustrations.

### Dossiers secondaires — PR 655, 636 et 659

La chaîne de correction **657 → 655 → 636** doit être analysée dans cet ordre **uniquement par des personnes habilitées**, avec nouvel audit des SHA après tout changement. La simulation PR 659 donne une référence technique à 60 tests et 14 chemins, mais n'est pas une autorisation de merger. La PR 640 n'entre jamais dans cette chaîne.

## 5. Exécution et sens exact de la CI P50T

Le workflow P50T comporte :
- un **job d'observation en lecture seule** : récupère par son SHA le script P50S, consulte l'API GitHub, exécute **20 tests**, classe les approbations et stocke des rapports JSON **non nominatifs** pendant sept jours. La réussite de ce job démontre seulement un relevé correctement effectué;
- un **job bloquant** : échoue en l'absence de la revue de PR 657 ou PR 638; si elles sont observées, évalue ensuite les cinq PR. Son échec actuel est attendu et n'autorise pas de contournement.

Les revues GitHub restent contrôlées sur l'état exact observé lors de l'exécution. Le rapport ne stocke ni identité de réviseur, ni adresse de courriel, ni documents confidentiels. Les jetons GitHub ne sont pas envoyés dans les journaux.

**Un job P50T devenu vert ne peut jamais attester un mandat ou un GO de publication.** Ces décisions restent extérieures au pipeline.

## 6. Sécurité GitHub et obstacles non levés

La lecture de `/branches/main/protection` a renvoyé une erreur **403** pour la connexion utilisée. La liste accessible des rulesets était vide. Il est donc impossible de certifier, avec cet accès, que `main` impose effectivement une ou plusieurs approbations avant une fusion. La gouvernance doit faire confirmer les règles par un administrateur autorisé; aucune protection de branche n'est créée ni modifiée dans ce jalon.

Le traitement effectif des courriels de contact, les mandats, les obligations électorales applicables, les responsabilités de publication et un plan de restauration éprouvé ne sont pas attestés. Les statuts institutionnels V3.40 et toutes les portes W0/W1, E26, pouvoirs et financières demeurent inchangés. Aucun déploiement ou formulaire supplémentaire n'est autorisé.

## 7. Clôture du jalon et sortie

P50T est considéré **techniquement livré** après présence des deux jobs, réussite des 20 tests, constat GitHub réussi et **échec contrôlé de la porte humaine** en l'absence des approbations. Ce n'est pas une anomalie à masquer : c'est la distinction honnête entre automatisation et responsabilité.

La prochaine action qui améliore réellement la situation est la désignation par le responsable habilité de **deux relecteurs compétents pour PR 657 et PR 638**, puis le traitement formel de leurs avis, *sans aucun GO anticipé*. **PR 640 : NE PAS FUSIONNER.**
