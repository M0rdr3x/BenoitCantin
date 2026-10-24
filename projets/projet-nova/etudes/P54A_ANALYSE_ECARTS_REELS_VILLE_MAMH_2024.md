# P54A — Analyse de l'écart entre deux publications officielles 2024

**Dossier documentaire vérifiable au 24 octobre 2026 : Ville de Québec 23027 / RTC T0088.** L'analyse de publications n'est pas un audit des grands livres et ne démontre aucun montant d'économie.

## 1. Résultat matériel confirmé par le workflow P53Z

Le workflow P53Z s'est terminé avec succès (52 tests) et a réalisé une capture HTTPS de **deux PDF publics officiels**, puis une comparaison de fichiers. Les résultats ne sont plus hypothétiques.

Source du résultat : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40113700739

Source de l'artefact vérifié : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40113700739/artifacts/12567252796

| Indicateur | PDF Ville de Québec | PDF MAMH |
|---|---|---|
| Date de capture UTC | 2026-10-24 16:58:03 | 2026-10-24 16:58:05 |
| Taille (octets) | 8 984 919 | 10 818 312 |
| Pages PDF | 230 | 177 |
| Pages sans texte exploitable par P53X | 27 | 3 |
| SHA-256 de la copie | b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399 | 4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00 |

**Deux fichiers binaires distincts ont été obtenus.** Leur longueur, leur nombre de pages et leur empreinte sont différents. Le programme P53X n'a retrouvé **aucune correspondance de texte normalisé strictement identique entre pages**; cela ne veut pas dire que les pages sont toutes conceptuellement différentes ou que les comptes divergent.

Ces empreintes attestent les octets réellement capturés par le programme lors de l'exécution P53Z. Elles ne sont pas des signatures de l'émetteur officiel, et ne prouvent pas quelle version est la version finale juridiquement autorisée. L'artefact de la CI contient un bilan, pas les PDF.

## 2. Pourquoi un second niveau de comparaison est nécessaire

Le MAMH explique qu'il peut assembler les documents transmis par les organismes municipaux et publier des mises à jour, tandis que le PDF de la Ville contient sa propre présentation éditoriale.

Référence : https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier

Un algorithme de pages identiques ne suffit pas. P54A ajoute des correspondances **approximatives** entre pages par séquences normalisées de quatre mots, comptage de chevauchements et score de Jaccard. La méthode ignore les pages au texte trop faible, les en-têtes trop fréquents et les candidats dont le recouvrement est inférieur au seuil. Les candidats retenus sont des **points d'examen**, jamais une expertise signée ni un jugement d'irrégularité.

Les sorties comportent seulement des numéros de page, des scores arrondis et le statut explicitement NON CERTIFIÉ. Aucun extrait de page ni pièce de personnel, journal ou facture confidentielle n'est archivé. Les fichiers téléchargés pour une nouvelle relecture restent en mémoire et ne sont pas commis dans GitHub.

## 3. Sept questions professionnelles à examiner

1. **Édition et composition** : les PDF assemblés présentent-ils les mêmes sections dans des mises en page différentes ?
2. **Périmètre audité** : bien distinguer les renseignements financiers audités des sections budgétaires explicitement NON AUDITÉES.
3. **États et périmètre** : ne comparer des valeurs qu'à base, période, convention comptable et périmètre de consolidation identiques.
4. **Ville–RTC** : rechercher les opérations bilatérales dans les grands livres et pièces justificatives.
5. **Éliminations** : ne jamais transformer une opération réciproque déjà éliminée en économie future.
6. **Main-d'œuvre et services** : sauvegarder les effectifs, conditions de travail, accessibilité et continuité des services essentiels.
7. **Expertise** : faire revoir les véritables différences chiffrées par des professionnels indépendants, avec mandat, droits d'accès et avis originaux signés.

Les notes du rapport municipal 2024 confirment la consolidation du RTC et de la SOMHAC, ainsi que l'élimination des opérations réciproques (page imprimée 35). La page 197 est située dans une partie indiquée NON AUDITÉE; cette mention ne doit pas être attribuée sans distinction à tous les états du rapport.

## 4. Exécution

Consulter les résultats P53Z confirmés, sans téléchargement :

    python scripts/analyser_ecarts_publications_nova_p54a.py --bilan p54a_bilan_reference.json

Reproduire la capture et chercher des candidats de pages :

    python scripts/analyser_ecarts_publications_nova_p54a.py --reanalyser-publications --bilan p54a_rapprochements.json

Refuser une conclusion comptable certifiée :

    python scripts/analyser_ecarts_publications_nova_p54a.py --exiger-anomalie-certifiee

Code 0 : exécution correcte du dossier ou relecture de deux fichiers. Code 2 : configuration invalide ou sortie existante. Code 3 : refus d'une certification inventée. Code 4 : nouvelle acquisition/extraction incomplète; les mesures originales de P53Z restent une preuve documentaire distincte.

Les nouvelles captures pourront présenter des SHA différents si les organismes ont publié d'autres versions. Elles ne remplacent pas rétrospectivement les observations P53Z du 24 octobre 2026.

**Décision : NO_GO_AUTOMATIQUE.** Aucune anomalie financière attestée; aucune économie, diminution d'emploi, dégradation de service, fusion main ou fiscalité définitivement adoptée.
