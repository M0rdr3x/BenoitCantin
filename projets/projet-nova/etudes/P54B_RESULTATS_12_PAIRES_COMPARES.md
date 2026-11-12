# P54B — Mesures numériques effectivement observées dans la CI

**24 octobre 2026.** Les 56 tests de P54B ont réussi dans GitHub Actions. Le même workflow a recapturé deux publications publiques de 2024, a recalculé leurs SHA-256 et a confirmé qu'elles correspondent exactement aux copies étudiées dans P53Z/P54A.

- Résultats : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40118178035
- Artefact du bilan : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40118178035/artifacts/12569352928
- Somme SHA-256 de l'archive de bilan : 79e3f3fb2031ce5a81db8709f487785f490e275fff3a966e91be18600b8f76fc

La comparaison porte **uniquement sur des jetons numériques extraits de pages textuellement candidates**, pas sur des écritures de grand livre ou des sommes qualifiées. Le MAMH publie des documents qui peuvent avoir des périmètres et des statuts d'audit distincts.

## Mesures des douze paires candidates

Indices de page PDF à partir de zéro. Recouvrement de Dice = deux fois les occurrences numériques communes divisé par le nombre total d'occurrences des deux pages.

| Ville → MAMH | Jetons Ville | Jetons MAMH | Communs | Recouvrement |
|---|---:|---:|---:|---:|
| 14 → 173 | 79 | 79 | 78 | 98,73 % |
| 51 → 30 | 99 | 99 | 98 | 98,99 % |
| 62 → 44 | 119 | 119 | 118 | 99,16 % |
| 75 → 57 | 86 | 86 | 85 | 98,84 % |
| 102 → 162 | 10 | 13 | 9 | 78,26 % |
| 104 → 164 | 66 | 66 | 65 | 98,48 % |
| 133 → 136 | 51 | 51 | 50 | 98,04 % |
| 139 → 140 | 55 | 55 | 54 | 98,18 % |
| 145 → 146 | 42 | 42 | 41 | 97,62 % |
| 146 → 147 | 42 | 42 | 41 | 97,62 % |
| 147 → 148 | 48 | 48 | 47 | 97,92 % |
| 170 → 155 | 39 | 39 | 38 | 97,44 % |

**Onze des douze paires ont un recouvrement lexical d'au moins 97 %.** La paire de pages 102 → 162 est prioritaire pour une vérification qualitative, parce que son recouvrement est le moins élevé, et **non parce qu'une anomalie serait constatée**.

Les chiffres ci-dessus ne désignent pas des montants : les jetons peuvent aussi représenter des années, dates, notes, codes ou pourcentages. La présence de nombreux jetons communs ne prouve pas des montants financiers équivalents. Les 96 contrôles de comparabilité restent NON_INSTRUIT, y compris l'exercice de chaque colonne, les mêmes périmètres consolidés, les unités et le caractère audité ou non de la section.

## Prochain travail humain et documentaire

Vérifier en premier lieu la page PDF index 102 du rapport municipal par rapport à la page PDF index 162 de la publication MAMH. Il faut identifier le type de section, l'unité, les notes, le périmètre, l'année, les éventuelles annexes et les colonnes comparables avant de confronter un seul montant.

Les états consolidés de la Ville incluent le RTC et la SOMHAC, selon le rapport municipal de 2024. Les opérations réciproques déjà éliminées ne doivent pas être transformées en économies supplémentaires. Les garanties d'emploi, les services essentiels, les coûts de transition et les validations comptables et juridiques originales signées restent bloquants.

Le fichier P54B_OBSERVATIONS_NUMERIQUES_2026_10_24.json archive les **résultats réellement obtenus**. Le script verifier_observations_numeriques_nova_p54b.py vérifie sa structure, sa référence au workflow, les douze paires, la cohérence mathématique de chaque recouvrement, la stabilité des empreintes et le maintien du statut non certifié.

**NO_GO_AUTOMATIQUE** : aucune économie certifiée, aucune irrégularité comptable démontrée, aucun poste monétaire authentifié, aucune décision de réduction de postes ou de services et aucune fusion dans main.
