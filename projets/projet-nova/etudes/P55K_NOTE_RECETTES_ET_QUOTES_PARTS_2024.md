# P55K — Analyse détaillée des écarts de revenus consolidés 2024

**4 novembre 2026 — analyse du rapport financier officiel de la Ville de Québec, sans certification des octets ni des écritures.**

## Décision visée

Identifier le **premier poste à examiner humainement** dans les différences de consolidation relevées par P55J, pour ne pas attribuer à tort des « économies » au regroupement des organismes publics. Il faut distinguer le budget de la Ville, les comptes des organismes contrôlés, les flux entre entités et les résultats consolidés.

## Preuves documentaires et niveaux de confiance

- [Rapport financier 2024 de la Ville de Québec](https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf), **page imprimée 35 / index PDF 34**, note « Principales méthodes comptables », consultée **visuellement**. Le périmètre contrôlé comprend le Réseau de transport de la Capitale (**RTC**) et la Société municipale d’habitation Champlain (**SOMHAC**). L'administration municipale désigne la Ville **sans** ces organismes; l'expression « Ville », dans le rapport sectoriel, désigne l'ensemble consolidé. Les opérations et soldes interorganismes sont éliminés.
- Même rapport, **page imprimée 63 / index PDF 62**, tableau **S12, « Résultats détaillés par organismes »**. **Les lignes chiffrées sont prises dans l'extraction textuelle du PDF officiel.** Plusieurs tentatives de capture visuelle de cette page n'ont pas abouti dans le lecteur Web; il ne faut **pas** prétendre qu'elle a été relue visuellement. Aucune copie locale intégrale n'a été acquise et vérifiée avec une empreinte courante.
- Même rapport, **page imprimée 197 / index PDF 196**, note « Périmètre comptable », consultée **visuellement**. Le rapprochement des budgets fait lui aussi intervenir l'agglomération, les compétences locales et les organismes; ces périmètres sont à distinguer, et le tableau S12 ne fournit **pas** un détail séparé des revenus du RTC et de la SOMHAC.

## Les dix postes de revenus de fonctionnement 2024

Formule : `résidu = total consolidé − administration municipale − organismes contrôlés et partenariats`, tous les montants en dollars canadiens.

| Catégorie | Administration | Organismes groupés | Consolidé | Résidu |
|---|---:|---:|---:|---:|
| Taxes | 1 296 686 206 | 0 | 1 295 208 647 | −1 477 559 |
| Compensations tenant lieu de taxes | 134 445 067 | 0 | 132 702 160 | −1 742 907 |
| **Quotes-parts** | **47 353 223** | **154 047 800** | **47 353 223** | **−154 047 800** |
| Transferts | 228 223 969 | 100 926 706 | 319 764 739 | −9 385 936 |
| Services rendus | 96 508 463 | 95 138 908 | 188 160 353 | −3 487 018 |
| Imposition de droits | 97 261 483 | 0 | 97 261 483 | 0 |
| Amendes et pénalités | 19 294 230 | 0 | 19 294 230 | 0 |
| Revenus de placements | 46 576 373 | 350 943 | 46 927 316 | 0 |
| Autres revenus d'intérêts | 21 438 065 | 3 754 116 | 23 941 951 | −1 250 230 |
| Autres revenus | 20 569 227 | 475 246 | 15 993 752 | −5 050 721 |
| **Total** | **2 008 356 306** | **354 693 719** | **2 186 607 854** | **−176 442 171** |

Les lignes bouclent exactement : l'administration, le bloc organismes, le total consolidé et le résidu de **−176 442 171 $** correspondent tous au rapprochement P55J.

## Une concentration significative, mais non monétisable

La différence de **−154 047 800 $** sur les quotes-parts représente :

[
\frac{154\,047\,800}{176\,442\,171}\times 100 = 87,3\%
]

de la **valeur absolue du résidu total des revenus de fonctionnement**. La différence restante est de **−22 394 371 $**.

C'est **compatible avec une neutralisation importante de flux entre entités**, mais le tableau seul ne permet pas d'identifier toutes les contreparties, leurs comptes, le chemin exact des écritures, ni la part respective du RTC et de la SOMHAC. Cette différence n'est **ni une charge économisable, ni un paiement compté deux fois dans le total consolidé, ni une preuve de gaspillage**. Elle doit au contraire attirer l'attention sur un risque de **faux gain de 154 M$** si quelqu'un additionne directement les organismes à la Ville.

Les résidus des taxes et des compensations apparaissent alors même qu'aucun revenu correspondant des organismes n'est affiché sur ces lignes. Ils doivent donc **rester sans explication définitive** jusqu'à l'examen des ajustements et reclassements, plutôt que d'être automatiquement qualifiés d'opérations interorganismes. À l'inverse, un résidu arithmétique nul n'établit pas qu'aucune transaction n'a été éliminée en amont.

## Priorités d'investigation

1. **K01 — Quotes-parts :** demander, dans le cadre d'un futur mandat comptable autorisé, les écritures et notes expliquant les 154 047 800 $, leur contrepartie et la méthode de neutralisation.
2. **K02 — Séparation RTC/SOMHAC :** obtenir les états et grands livres propres à chacun. Le tableau S12 agrège les organismes et ne permet pas de calculer leurs parts respectives.
3. **K03 — Résidu restant :** justifier sur pièces les **22 394 371 $** restants, notamment les postes de transferts, de services et les résidus sur revenus sans colonne d'organisme.
4. **K04 — Périmètre juridique et budgétaire :** documenter les compétences locales et d'agglomération, les résolutions de 2024 et la cohérence des fonds affectés.
5. **K05 — Éventuelle politique d'économie :** examiner séparément l'effet net et récurrent, les services, les emplois, les obligations et le pouvoir d'achat. **Aucun gain ne peut être conclu avec le seul tableau S12.**

Ces actions ne constituent **pas** une prise de contact, un mandat ni une demande de données réellement effectuée.

## Contrôles logiciels et suites

Le référentiel `P55K_DETAIL_REVENUS_RECIPROQUES_2024.json` verrouille les dix lignes, les formules, les niveaux de preuve et les cinq questions humaines. Le script `scripts/ventiler_revenus_reciproques_nova_p55k.py` vérifie les trois totaux, le résidu P55J, la différence sur les quotes-parts, la concentration à une décimale et le résidu restant. Il produit des **sorties publiques neutres**, sans empreintes actuelles ni données privées :

```bash
python scripts/ventiler_revenus_reciproques_nova_p55k.py \
  --bilan-public /hors_git/p55k_bilan.json \
  --table-public /hors_git/p55k_tableau.json
```

L'option `--exiger-certification` retourne volontairement un refus. Les tests GitHub Actions ne téléchargent **aucun PDF réel**; les calculs sont faits à partir des montants textuels du rapport public, sous réserve de relecture visuelle future de S12 et de l'acquisition réelle P55H/P55G.

**Verrous permanents :** quatre dossiers P54E et une date probable toujours ouverts; 40 P54N, dix P54O, 96 P54B et huit P54C non attestés; deux mandats comptable/juridique non signés; zéro économie certifiée. Pas de suppression d'effectifs ou de services publics justifiée par ces différences; préservation du pouvoir d'achat; deux régimes (Québec au Canada et Québec souverain hypothétique) non confondus; SINJIRA non modifié, aucune fusion dans `main`.

**Décision : `NO_GO_AUTOMATIQUE`.**
