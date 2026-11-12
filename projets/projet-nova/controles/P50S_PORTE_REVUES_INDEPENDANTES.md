# Projet Nova — P50S : réception des revues et porte de décision humaine

**16 octobre 2026 · Jalon opérationnel de revue · Statut : NO_GO**

## Objet

P50R (PR 659) a démontré la compatibilité technique d'une simulation locale sans conflit pour PR636 → PR655 → PR657 → PR638 : 14 chemins, 10 tests d'inspection, 40 tests de participation, 10 tests d'identité; statut toujours **NO_GO**. P50S traite le **véritable blocage résiduel** : absence de réviseurs formellement demandés et d'avis humains déposés sur les PR concernées. Le script `scripts/inspect_nova_review_readiness_p50s.py` relève ces faits directement via l'API GitHub, sans écriture.

Il ne soumet pas de revue à la place d'un humain, ne choisit pas un réviseur sans mandat et ne délivre jamais de GO.

## Constat au départ de P50S

| PR | Rôle | SHA contrôlé | Revues formelles GitHub | Demandes en attente |
| --- | --- | --- | --- | --- |
| 657 | Second correctif du scanner | `f67abe43b7223d0f59ee1efb6cf883d558eddfb5` | 0 | 0 |
| 655 | Premier correctif | `8541f761be8dbabda0c3f024f8969562ab816bc7` | 0 | 0 |
| 636 | Pages participation et avis légal | `6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb` | 0 | 0 |
| 638 | Identité et statuts proposés | `e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e` | 0 | 0 |
| 659 | Simulation d'intégration P50R | `363bafc8f07cee1d72e785e51d48fbec121bb574` | 0 | 0 |

Source : requêtes GitHub `/pulls/{number}/reviews` et `/pulls/{number}/requested_reviewers` consultées le 16 octobre 2026. Les commentaires techniques des PR précédentes ne sont **pas** des revues GitHub formelles. Une révision a pu survenir après le constat; consulter le relevé live avant toute décision.

Le commit de `main` observé : `9ed5f70cbe7022f25a679346a1288701f3b09067`. Toute dérive exige de refaire la simulation et les examens. **PR 640 : NE PAS FUSIONNER**, même si un administrateur dispose de la capacité technique de le faire.

## Porte P50S — ce qui est vérifié automatiquement

1. État `open`, caractère `draft`, absence de fusion, base et **SHA exact** des cinq PR clés.
2. État de PR 640 exclue, absence de nouvelle évolution inconnue.
3. Existence de demandes de révision sur les PR clés, nombre de revues GitHub officiellement soumises.
4. Une approbation GitHub ne compte comme *observation de code review sur HEAD* que si elle est faite par une autre personne que l'auteur, non classée Bot, sur le SHA exact et non supplantée par une demande plus récente de modification.
5. Succès attesté des workflows **P50Q** et **P50R** aux SHA exacts.
6. Absence de tout glissement implicite de CI verte vers décision de publication, déploiement, autorisation juridique ou conformité des renseignements.
7. Aucun jeton n'est écrit dans les sorties; l'action GitHub utilise les permissions minimales **contents: read, pull-requests: read, actions: read**.

**La sortie du vérificateur demeure `NO_GO_AUTOMATIQUE`, même avec des approbations GitHub.** Les avis externes, les mandats et la conformité électorale ne se déduisent pas d'une identité GitHub ou d'une approbation technique.

## Séquence des décisions humaines requises

### Porte A — validation du correctif PR 657
Le responsable technique du dépôt, lorsqu'il est réellement habilité, choisit un relecteur **indépendant de l'auteur du correctif** et lui demande une revue GitHub formelle, aux octets du SHA actuel. Les exigences incluent : séquences URI encodées, scripts inline, faux positifs, limites sur les scripts externes et protection contre toute réactivation des paiements/formulaires.

**Sortie A :** avis traçable avec demandes de corrections, dates et SHA. Un `APPROVED` ne prouve pas, à lui seul, l'indépendance réelle ou un mandat de gouvernance.

### Porte B — PR 655 puis PR 636
Après une éventuelle approbation et **une décision du mainteneur habilité**, intégrer PR657 dans la branche PR655; revalider les **40 tests** au nouveau SHA. Ensuite, faire examiner l'intégration PR655 vers la branche PR636, vérifier les deux textes du site et relancer la CI au SHA final. **P50S ne procède lui-même à aucune fusion.**

### Porte C — revue autonome PR 638
Obtenir un avis distinct sur la dénomination actuelle **Projet Nova**, sur l'appellation éventuelle « Parti Nova » et sur les statuts **non adoptés**, leur manifeste SHA-256 et les mentions institutionnelles. Ne pas traiter la réussite technique du scanner d'identité comme une qualification juridique.

### Porte D — autorisation de publication
Faire établir **hors GitHub** la structure porteuse, le pouvoir de décision, les obligations de confidentialité du contact courriel, les règles électorales pertinentes et un plan de sauvegarde/retrait opérationnel. La décision humaine doit mentionner les SHA **finalement révisés**, un responsable habilité, le périmètre autorisé, la capacité de rollback et les critères d'arrêt. Une décision non documentée n'est pas un GO.

### Porte E — publication et recette éventuelles
Uniquement après autorisation explicite d'un responsable effectivement habilité : procédure de fusion limitée, contrôle HTTP du site réellement diffusé, absence de mécanismes de collecte/dons, vérification des redirections et de l'état public, rapport indépendant. Les éventuelles attestations restent hors dépôt public si elles contiennent des renseignements sensibles.

## États de sortie et traitement des écarts

| Scénario | Interprétation | Suite |
| --- | --- | --- |
| PR sans reviewer demandé | Processus humain non démarré | Sélectionner un relecteur réel et habilité |
| Demande de revue en attente | Révision non rendue | Maintenir NO_GO |
| `APPROVED` sur ancien SHA | Approbation périmée | Revoir au nouveau SHA |
| `CHANGES_REQUESTED` ultérieur | Avis négatif courant | Corriger puis soumettre de nouveau |
| PR, branche ou SHA changé | Simulation P50R historiquement périmée | Refaire test et revue |
| CI technique échouée | Preuve technique insuffisante | Reprendre la validation, sans passer outre |
| CI et reviews GitHub réussies mais mandats absents | **NO_GO institutionnel** | Compléter le dossier légal et la décision habilitée |
| PR 640 même techniquement propre | Interdiction spécifique persistante | **NE PAS FUSIONNER** |

## Sortie et prochain jalon

P50S peut livrer un état de préparation objectivement vérifiable : nombre de demandes de révision, statut des avis GitHub, conservation de la preuve CI et liste de blocages, **sans jamais fabriquer les approbations manquantes**.

Pour avancer réellement, la première prochaine action est la **demande de revue humaine des PR 657 et 638**, puis l'examen des dépendances 655/636. Sans personnes autorisées désignées par l'organisation, l'automatisation ne peut pas clôturer ce jalon de gouvernance.

**Base V3.40, P2-C0-49, W0/W1/W2–W4, E26, pouvoirs et finances inchangés. Aucun formulaire, don, signature ou collecte politique activé.**
