# Projet Nova–Sinjira — G0.17e : admissibilité des dépenses TECQ et continuité du financement municipal

**Date : 8 novembre 2026 · Document de travail technique · Audit interne Nova : 47/100, 53 points à obtenir.**

**Décision :** les règles officielles d'aide à l'investissement sont mieux établies, mais ni les dépenses de fonctionnement municipal, ni les dix années budgétaires du Projet Nova, ni les encaissements de subventions ne sont financièrement certifiés. Le Projet Nova n'est pas une loi en vigueur ni un programme politique officiellement adopté.

## 1. La question financière que G0.17e résout

Une réforme qui ramène la fiscalité à **deux prélèvements proposés** ne peut pas financer durablement les services d'eau potable, l'assainissement et la voirie en comptabilisant comme recette générale les montants annoncés pour des projets d'infrastructures. Les aides à l'investissement sont soumises à des critères de dépense, de programmation, de cumul et d'audit. Elles **ne couvrent pas automatiquement le fonctionnement courant**.

La référence principale est le [Guide TECQ 2024–2028, 4e version, **juillet 2026**](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/infrastructures/tecq/GUI_tecq_2024_2028_juillet_2026.pdf), que le [portail officiel du Gouvernement du Québec](https://www.quebec.ca/habitation-territoire/infrastructures-municipales/programmes/eau-potable-eaux-usees/programme-transfert-infrastructures-eau-collectives-quebec-tecq-2024-2028) affiche comme guide en vigueur. Les pages 5 à 8, 12 et 14 du PDF ont été consultées et leur rendu visuel contrôlé.

## 2. Ce que le programme TECQ met à disposition

Le guide indique **près de 3,316 G$** pour la période 2024–2028 : **près de 2,226 G$ du gouvernement fédéral et près de 1,090 G$ du Québec**. La part québécoise **inclut 90 M$ supplémentaires** pour les bâtiments municipaux de base : **il serait incorrect de compter ces 90 M$ une seconde fois**.

Ces montants sont des **enveloppes annoncées à l'échelle du programme**, **pas** des paiements vérifiés à une municipalité, et **pas** des revenus nets supplémentaires du Projet Nova. Les catégories d'infrastructures visées comprennent notamment l'eau, l'assainissement, la voirie locale, la résilience et d'autres ouvrages collectifs; le total ne peut être affecté intégralement à l'eau.

### Conditions d'allocation : données et exemples de formule, pas subventions reçues

La population utilisée est celle du décret au **1er janvier 2024**. Sous réserve de conditions particulières et de clauses de neutralité :

- **Moins de 6 500 habitants** : montant forfaitaire de **500 000 $** plus **215,27 $ par habitant**;
- **6 500 habitants ou plus** : **291,33 $ par habitant**.

D'autres règles s'appliquent notamment aux regroupements municipaux, territoires non organisés, bonifications écoresponsables et bâtiments municipaux de base. Sans population officiellement vérifiée, décision municipale et programmation acceptée, il est interdit d'appeler une estimation issue de cette formule **une aide acquise ou encaissée**.

## 3. Calendrier de versement ≠ trésorerie

Le guide prévoit **cinq tranches de 20 %** :

| Période gouvernementale visée | Quote-part théorique |
| --- | ---: |
| 1er janvier 2024 – 31 mars 2025 | 20 % |
| 1er avril 2025 – 31 mars 2026 | 20 % |
| 1er avril 2026 – 31 mars 2027 | 20 % |
| 1er avril 2027 – 31 mars 2028 | 20 % |
| 1er avril 2028 – 31 décembre 2028 | 20 % |

Les versements nécessitent des **programmations approuvées** ou leurs mises à jour annuelles. La part québécoise demeure conditionnelle aux crédits votés. Les sommes non versées peuvent être reportées, et une retenue correspondant notamment au financement accessible en 2028–2029 peut dépendre de l'acceptation de la reddition de comptes finale **avec audit indépendant**.

**Une tranche programmée ne prouve ni la date ni le montant d'un crédit à la banque municipale.** Le registre G0.17e garde les montants approuvés, retenus, versés et encaissés à `null` pour chacune des cinq périodes. Il ne confond pas `null` (preuve manquante) avec `0` (preuve d'absence de versement).

## 4. Admissibilité : protéger les coûts non couverts

Le guide TECQ (sections 3.1.1 et 3.1.2) décrit des travaux et études admissibles, dont les ouvrages d'eau et d'assainissement, le renouvellement des conduites et certaines études de gestion des actifs. **Le classement demeure conditionnel à l'admissibilité précise du projet, aux plafonds et aux pièces**.

Il exclut notamment :
- **les travaux usuels d'entretien**;
- les **salaires réguliers des employés municipaux**, à l'exception spécifiée de certaines activités et études de gestion des actifs;
- des frais juridiques, les coûts de l'audit de reddition, les taxes récupérables et les travaux hors de la période admissible.

Le guide précise aussi des cas et contraintes supplémentaires; **la présente matrice ne remplace pas une décision juridique d'admissibilité du MAMH**.

Cela signifie que le Projet Nova doit financer explicitement une enveloppe distincte pour **l'exploitation, le personnel, l'entretien, l'énergie, les réparations, la dette et les pensions**, même lorsque la construction d'une nouvelle infrastructure est soutenue par TECQ ou PRIMEAU.

## 5. Empêcher le double financement et les doubles comptes

Le guide (section 3.6) demande de **déduire les dépenses déjà financées par un autre programme et les contributions privées** pour établir la base résiduelle des dépenses admissibles. Les plafonds de cumul d'aides doivent être respectés.

Pour chaque projet, la chaîne documentaire à produire est :

**Projet → dépense admissible → facture et coût réel → engagements/autorisation TECQ → autres aides appliquées au même coût → retenues → virement de chaque gouvernement → crédit effectivement reçu par la municipalité → neutralisation des transferts internes en consolidation.**

Un projet soutenu aussi par PRIMEAU n'autorise pas à attribuer **deux fois la même facture** à deux subventions; il faut examiner les conventions et les règles de chaque programme.

La neutralisation comptable d'un transfert interne entre le gouvernement provincial et une municipalité ne supprime **ni la facture, ni l'actif à entretenir, ni le salaire d'un opérateur d'eau**.

## 6. Délais officiels de contrôle

Le guide fixe notamment :

- **1er janvier 2024 – 31 décembre 2028** : période admissible des travaux;
- **1er octobre – 15 février** : fenêtre annuelle indiquée pour les mises à jour de la programmation;
- **31 décembre 2026** : échéance associée à une étape donnant accès à une bonification écoresponsable allant jusqu'à **5 %**, sous conditions;
- une bonification totale pouvant atteindre **10 %** selon les démarches de gestion des actifs;
- **30 juin 2029** : limite pour déposer la reddition de comptes finale;
- **six mois après son approbation par le ministère** : délai indiqué pour le rapport de l'auditeur indépendant.

Les retenues et remboursements éventuels dépendent des décisions documentées. Aucun versement écoresponsable effectif n'a été confirmé dans notre dossier.

## 7. Mesure normative proposée pour Nova, sans création de troisième taxe

**Proposition de travail non adoptée : « Garantie de continuité opérationnelle des services municipaux ».**

La transition fiscale envisagée par Nova ne pourrait réduire ou retirer une taxe, un droit ou une recette municipale **qu'après** vérification des coûts permanents et du remplacement légal et effectif des recettes correspondantes. La garantie comprendrait :

1. **Financement d'exploitation** : budget annuel des services d'eau, d'assainissement, de voirie et des autres missions locales, séparé de l'aide affectée aux immobilisations.
2. **Maintien de la main-d'œuvre et des obligations** : aucun équilibre supposé obtenu par une suppression fictive des salaires, conventions de travail, pensions ou services rendus.
3. **Maintien des actifs** : coût de cycle de vie, entretien courant, interventions d'urgence, renouvellement et dette.
4. **Financement des investissements** : aides admissibles, contribuables et recettes légalement utilisables, prêts et montants réellement encaissés, sans comptage multiple.
5. **Dispositif de contrôle** : registre de dépenses par projet, reçu de paiement, retenues, audit externe, possibilité de correction et information publique caviardée.
6. **Respect du cadre constitutionnel** : Québec dans le Canada et Québec souverain font l'objet de budgets et d'analyses juridiques **distincts**. Aucune aide fédérale après une éventuelle souveraineté n'est présumée garantie.

Ce mécanisme aurait pour mission de **préserver les services et le pouvoir d'achat**, mais sa viabilité reste à démontrer. Il n'est pas financé parce qu'on lui a donné un nom.

## 8. Modèle inspectable et blocages encore réels

Le dossier G0.17e livre :

- `data/g017e-tecq-guide-2026-depenses-admissibles-et-paiements.json` : enveloppe, cinq périodes, admissibilités, coûts exclus, échéances, rapprochement de projets et montants inconnus;
- `assets/g017e-tecq-legal-cost-cash-core.mjs` : contrôles stricts de provenance, d'éligibilité, de dépenses récurrentes et d'affirmations de paiement non prouvées;
- `tests/g017e-tecq-legal-cost-cash.test.mjs` : **65 tests sur 65 réussis par rejeu JavaScript/V8 isolé**, y compris le contrôle de provenance CI. Une **exécution native GitHub Actions antérieure a réussi**, au commit de la version à 57 tests ([rapport d'exécution no 42536049965](https://github.com/M0rdr3x/BenoitCantin/actions/runs/42536049965), commit `01bb9b2de54918b9b1ac0e0622db719f322eb439`, tâche Node.js « Vérifier les calculs et la provenance »). La **nouvelle version à 65 tests** a également été validée par [l'exécution native GitHub Actions no 42536695704](https://github.com/M0rdr3x/BenoitCantin/actions/runs/42536695704), **terminée avec succès** au commit `96e14eb51a57925a9d96eaac80774155ceb03d90`; la tâche de vérification des calculs et de la provenance a obtenu le statut **success**. Même un succès natif complet ne vaut **pas audit financier indépendant du Projet Nova**.

Le projet ne possède toujours pas, pour chaque municipalité :

- des preuves de **virements TECQ/PRIMEAU et de leur réception**;
- des coûts d'exploitation, de personnel et de renouvellement **homogènes sur les dix exercices**;
- une assiette de taxation Nova vérifiée, le rendement net du mécanisme contre les paradis fiscaux et une simulation du revenu disponible;
- deux budgets constitutionnels équilibrés, juridiquement défendables et **audités indépendamment**.

Les fichiers officiels municipaux 2024–2025 et le classeur de l'eau potable 2024 identifiés en G0.17b–d doivent encore être téléchargés et traités. Le délai de la publication des données ne doit pas être converti en valeur imputée.

**Décision G0.17e :** guide de juillet 2026 et limites du financement TECQ consolidés; contrôle logiciel reproduit; **aucun paiement de subvention ni revenu Nova nouvellement confirmé**; **score de complétude inchangé à 47/100, avec 53 points à valider**.

**Suite G0.17f :** construire, à partir de preuves réelles reçues ou de sources publiques vérifiables, un premier **état municipal d'exploitation et d'investissement** séparant recettes fiscales, tarifs, transferts internes, amortissement, dette, travaux admissibles, paiements et provisions; le reproduire ensuite dans les deux modèles de dix ans avant une réévaluation indépendante du score.
