# P55L — Rapprochement externe des quotes-parts du RTC et de la Ville de Québec (2024)

**Étape documentaire du 4 novembre 2026.** Analyse de deux publications institutionnelles distinctes, sans acquisition et vérification des octets PDF originaux. Le but est d'identifier la contrepartie des **154 047 800 $** et **d'éviter de les comptabiliser à tort comme une économie politique**.

## Éléments établis par les publications

**Publication A — Ville de Québec.** [Rapport financier 2024](https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf), état sectoriel **S12, page imprimée 63**. La ligne « Quotes-parts », exercice 2024, fournit :
- Administration municipale : **47 353 223 $**.
- Organismes contrôlés et partenariats : **154 047 800 $**.
- Total consolidé : **47 353 223 $**.
- Différence arithmétique : **47 353 223 − 47 353 223 − 154 047 800 = −154 047 800 $**.

Le contrôle de cette page repose sur **l'extraction textuelle du PDF officiel** et sur le rapprochement P55K, et **non sur une nouvelle capture visuelle S12 ou sur un SHA-256 du PDF téléchargé**.

**Publication B — Réseau de transport de la Capitale (RTC).** [Rapport d'activité 2024, annexe financière consolidée](https://www-api.rtcquebec.ca/sites/default/files/2025-06/RTC_Rapport_Activite%202024_0.pdf), dépôt légal **juin 2025** :
- **État consolidé des résultats S7, exercice 2024** : ligne « Quotes-parts » **154 047 800 $ réalisés**, identiques au **budget 2024**; comparatif réalisé 2023 **143 131 000 $**.
- **Note 27, Revenus (S11, page 35 de l'annexe)** : « Quotes-parts — Contribution de l'agglomération » **154 047 800 $**.
- **Note 28, Opérations interentités (S11, page 39 de l'annexe)** : le RTC indique avoir reçu **154 047 800 $ de l'agglomération de Québec**, dont **environ 93 %** seraient assumés par la Ville de Québec. La note mentionne **143 100 000 $** pour 2023, chiffre moins précis que la ligne comparative S7 de **143 131 000 $**; ne pas forcer une identité stricte de ces deux références de 2023.
- **État S7 RTC** : revenus consolidés réalisés **428 758 065 $**, charges **358 727 303 $**, excédent des activités **70 030 762 $**. Ces montants sont ceux du **RTC**, pas des montants supplémentaires à additionner aux revenus consolidés de la Ville.

Le rapport RTC a été consulté **en texte indexé du PDF officiel**. La tentative de capture visuelle du PDF RTC par navigateur a échoué; il ne faut **pas** présenter cette étape comme une vérification visuelle, ni affirmer une signature authentifiée ou un hachage local actuel. Le rapport d'activité RTC 2024 est annoncé à **24,3 Mo** dans les [publications du RTC](https://www.rtcquebec.ca/propos/publications), au-dessus du plafond de **20 millions d'octets** du mécanisme P55H conçu pour les **deux autres PDF Ville/MAMH** : P55H ne doit **pas** être utilisé tel quel pour le télécharger.

## Résultats arithmétiques reproductibles

| Vérification | Calcul ou comparaison | Conclusion autorisée |
|---|---:|---|
| RTC S7 → RTC note 27 → RTC note 28 | **154 047 800 $ = 154 047 800 $ = 154 047 800 $** | Concordance des valeurs publiées dans le document RTC |
| RTC → Ville S12, colonne organismes | **154 047 800 $ = 154 047 800 $** | Correspondance exacte entre deux publications |
| Ville S12, écart des quotes-parts | **−154 047 800 $** | Différence de consolidation compatible avec la neutralisation d'une contrepartie |
| Variation du revenu RTC par rapport à 2023 | **+10 916 800 $**, soit **+7,6 %** | Comparatif de financement, **non une économie** |
| Part des quotes-parts dans les revenus RTC | **154 047 800 / 428 758 065 ≈ 35,9 %** | Poids d'une recette dans les comptes RTC, **non une marge disponible** |
| Résultat des activités RTC | **428 758 065 − 358 727 303 = 70 030 762 $** | Identité comptable, **pas une somme libre ni un gain Nova** |

### Lecture correcte

L'étape permet de dire que **les 154,05 M$ affichés en quotes-parts dans la colonne agrégée des organismes de la Ville correspondent au montant de contribution déclaré par le RTC en 2024**. La note RTC donne en outre **la nature du flux et sa provenance (agglomération)**.

Cela **renforce fortement l'interprétation** d'une contrepartie interentités neutralisée. Il reste cependant à confirmer par les **écritures comptables réciproques** et la feuille de consolidation où les comptes se compensent effectivement; le simple calcul du résidu **n'authentifie pas ces écritures**.

Le « **environ 93 %** » est **une approximation** contenue dans le rapport RTC. Il ne permet **pas** d'affirmer que la contribution municipale exacte de la Ville est égale à `154 047 800 × 0,93`, ni de calculer avec certitude celle des municipalités liées. Les règlements de quotes-parts d'agglomération et les contributions au RTC sont **des mécanismes distincts**. Pour 2024, consulter le [règlement R.A.V.Q. 1617](https://reglements.ville.quebec.qc.ca/fr/document/an/R.A.V.Q.1617); ne pas appliquer rétroactivement les dispositions d'une réforme adoptée en 2025.

**Aucune conclusion sur la SOMHAC** ne découle de ces correspondances, notamment sur ses autres revenus, ses coûts, ses soldes réciproques ou l'ensemble des résidus de consolidation. La confirmation des autres **22 394 371 $** de résidus sur le fonctionnement reste ouverte.

## Questions à résoudre sur pièces

1. Identifier dans le grand livre des deux parties les écritures d'agglomération → RTC, la contrepartie et l'écriture d'élimination du groupe Ville.
2. Obtenir la répartition **exacte** des versements 2024 par municipalité et par compétence, sans transformer le taux approximatif de 93 % en montant garanti.
3. Vérifier séparément le périmètre SOMHAC, ses transactions réciproques et les autres résidus du tableau S12.
4. Évaluer l'effet net et la récurrence des dépenses sous contrainte de **maintien des services de transport, des emplois et du pouvoir d'achat**. Ne jamais déduire une économie du seul fait que la recette d'un organisme est neutralisée à la consolidation.
5. Conserver les deux scénarios distincts : **Québec dans le Canada** et **Québec souverain hypothétique**. Ni l'un ni l'autre ne permet de réutiliser deux fois la même contribution.

Le logiciel P55L effectue ces contrôles sur les **valeurs recopiées des publications**, et non sur les bytes des originaux. Il ne réalise aucun accès réseau, ne publie aucune pièce privée, refuse toute tentative d'attestation automatique et retourne `NO_GO_AUTOMATIQUE`.

```bash
python scripts/recouper_quotes_parts_rtc_ville_nova_p55l.py \
  --bilan-public /hors_git/p55l_bilan.json \
  --table-public /hors_git/p55l_table.json
```

Les sorties publiques sont créées seulement si les chemins sont neufs. L'option `--exiger-certification` force un refus de code 3. Les tests synthétiques ne créent **aucune certification**.

**Toujours ouverts :** quatre dossiers P54E, date probable P54O, 40 tâches P54N, dix blocages P54O, 96 P54B et huit P54C non attestés, mandats comptable/juridique non signés, aucune économie certifiée. Pas de contact, dépense, réduction d'effectifs/services, modification SINJIRA ni fusion `main`.

**Décision : `NO_GO_AUTOMATIQUE`.**
