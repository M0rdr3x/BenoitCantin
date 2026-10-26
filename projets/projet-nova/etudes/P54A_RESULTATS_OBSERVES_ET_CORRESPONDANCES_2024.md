# P54A — Résultats observés dans GitHub Actions : douze pages candidates

**24 octobre 2026, seconde acquisition réelle à 17 h 26 min UTC.** Le workflow P54A a réussi. Les 48 tests passent; deux PDF institutionnels ont été récupérés de nouveau par HTTPS. Leurs empreintes SHA-256 sont **identiques aux captures P53Z** observées plus tôt le même jour. Cela documente la stabilité des copies lors de deux captures rapprochées, et **ne constitue pas une signature numérique de l'émetteur**.

- Workflow et logs : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40116065853
- Artefact de synthèse : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40116065853/artifacts/12568158622
- Première acquisition : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40113700739
- Archive P54A SHA-256 : c973b8558bc05ec4f4d572da66a700548b7ba835e88cd4208c2c96f6fbea86dc

## Correspondances approximatives identifiées

La méthode P53X n'a trouvé aucune page au **texte normalisé strictement identique** entre les deux publications. La méthode P54A (séquences de quatre mots, score de Jaccard) a identifié **12 candidats retenus, plafonnés à 12**. Ces paires ne sont pas douze attestations indépendantes ni la liste exhaustive des pages semblables.

| Page PDF Ville (index 0) | Page PDF MAMH (index 0) | Score de Jaccard |
|---:|---:|---:|
| 14 | 173 | 0,9511 |
| 51 | 30 | 0,9250 |
| 62 | 44 | 0,9106 |
| 75 | 57 | 0,9219 |
| 102 | 162 | 0,9156 |
| 104 | 164 | 0,9128 |
| 133 | 136 | 0,9200 |
| 139 | 140 | 0,9083 |
| 145 | 146 | 0,9366 |
| 146 | 147 | 0,9256 |
| 147 | 148 | 0,9172 |
| 170 | 155 | 0,9167 |

**Les numéros sont des indices de pages PDF commençant à zéro, non les numéros de page imprimés.** Les scores sont des estimations de similarité de groupes de mots; ils ne prouvent ni la concordance des montants, ni le périmètre d'audit, ni la validité comptable.

Le résultat est important pour la qualité des travaux : « zéro page strictement identique » n'impliquait pas « zéro contenu en commun ». Il y a du contenu fortement similaire malgré des présentations distinctes.

## Questions restantes et doctrine

La Ville de Québec déclare le RTC et la SOMHAC dans son périmètre consolidé et l'élimination des écritures réciproques dans son rapport 2024 (page imprimée 35). L'analyse des douze correspondances ne remplace pas les factures, les journaux comptables des deux parties, les feuilles de consolidation, l'analyse des coûts évitables, les garanties emplois/services, ni des avis indépendants et signés.

**NO_GO_AUTOMATIQUE** : 0 économie certifiée, 0 anomalie financière démontrée, 0 version juridiquement authentifiée par le seul algorithme, aucune réduction d'effectifs, de service ou fusion dans main.

Le JSON P54A_RESULTATS_REANALYSE_2026_10_24.json conserve les résultats observés. Le script verifier_resultats_observes_nova_p54a.py en vérifie les valeurs et restrictions. Ce contrôle est un test de cohérence de la transcription par rapport aux données du workflow et non une signature probante d'un auditeur indépendant.
