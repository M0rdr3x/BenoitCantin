# P55N — Baromètre de complétude du programme Nova et plan de fermeture des lacunes

**Évaluation indicative du 5 novembre 2026. Statut : analyse éditoriale interne candidate, non adoptée, non certifiée et non indépendante.**  
**Portée :** préparer un programme politique **complet, chiffré, cohérent et défendable**. Cette cible ne se confond ni avec la reconnaissance d'un parti politique ni avec la possibilité constitutionnelle et administrative d'appliquer immédiatement un programme de gouvernement.

## Réponse au citoyen

**Estimation actuelle : environ 53 %**, selon une grille pondérée de huit domaines, avec une **fourchette raisonnable de 45 à 60 %**. Ce chiffre **n'est pas une statistique officielle** : il reflète un jugement documentaire daté. Il ne mesure ni les bénéfices, ni l'efficacité de la politique, ni le soutien de la population. Le nombre de fichiers, commits et tests **n'entre pas** dans le calcul.

Un programme peut avoir beaucoup de textes et rester partiellement incomplet sur sa **capacité financière, juridique et opérationnelle**. Inversement, une section dont les propositions sont bien rédigées n'est pas une loi adoptée. Le fait que des tests automatiques passent ne prouve pas la crédibilité des hypothèses fiscales.

## Grille pondérée et preuves

| Domaine | Poids | Points estimés | Manque principal |
|---|---:|---:|---|
| Vision politique et principes | 10 | **10** | Dernière révision éditoriale et arbitrages cohérents |
| Institutions, élections, démocratie | 15 | **13** | Simulations régionales et revue contradictoire |
| Constitution, lois et concordance | 15 | **12** | Examen des compétences, recours et contradictions |
| Services publics, économie et secteurs | 15 | **9** | Coûts, indicateurs, priorités et garanties de continuité |
| Fiscalité, budget, deux régimes | 20 | **5** | Bases et taux, recettes effectives, incidence distributive, budgets à dix ans |
| Transition et déploiement | 10 | **4** | Coûts, étapes, responsables, risques et capacité réelle |
| Expertises indépendantes | 10 | **0** | Avis signés et contradictoires sur pièces |
| Consultations et adoption formelles | 5 | **0** | Décisions/consultations prouvées et procédure légale vérifiée |
| **Total** | **100** | **53** | **47 points estimés restent à atteindre** |

**Comment lire ces points :** ils ne signifient pas que chaque secteur a été audité ni qu'il existe une métrique universelle des programmes politiques. Ils sont accordés pour le niveau de rédaction et de démonstration **visible dans les sources examinées**. Une notation différente pourrait être raisonnable : les notes sont expressément approximatives et le modèle ne transforme jamais leur somme en attestation de complétude.

## Sources du Projet Nova inspectées

- `official/reference/programme.md` : **16 sections**, dernière consolidation publique **26 août 2026**, programme candidat et non adopté comme loi. Ce texte contient déjà les principes démocratiques, élections, justice, services, fiscalité, municipalités, économie et souveraineté.
- `official/reference/corpus.md` : architecture institutionnelle et hiérarchie normative **candidates**; constitution, lois et compétences sans effet juridique actuel.
- `official/reference/statuts.md` : statuts **proposés**, pas la preuve d'une autorisation ni d'une adoption d'un parti.
- `etudes/P52A_FAISABILITE_FISCALE_DEUX_REGIMES.md` et `P52B_METHODOLOGIE_SIMULATION_FISCALE.md` : étude des deux prélèvements et de **deux régimes constitutionnels**, sans taux adopté, avec **20 preuves P52A à obtenir** et **600 entrées financières inconnues P52B** dans les 60 exercices-scénarios. P52D comporte **720 montants d'incidence encore inconnus**.
- `etudes/P55M_NOTE_SOMHAC_RESERVES_CONVENTIONS_2024.md` : contrôle de réserves affectées et d'obligations non ventilées; aucune économie publique certifiée ni mandat professionnel signé.
- `DOCUMENT_CONTROL.md` : hiérarchie documentaire et modalités d'adoption.

**Important :** les études P52A–P55M constituent des travaux candidats dans la PR **et ne mettent pas automatiquement à jour le programme public de référence**. En particulier, la proposition de **deux prélèvements** reste une étude non adoptée : le programme public dit actuellement que la fiscalité devrait être fortement simplifiée, **pas** qu'un taux définitif et tous les prélèvements à supprimer ont été légalement arrêtés.

## Les dix portes nécessaires avant de parler de programme complet et défendable

Toutes sont **« NON DÉMONTRÉ »** dans le dossier de référence actuel :

1. **FIN_BUDGET :** recettes, dépenses, dettes et équilibres des deux trajectoires décennales sourcés, sans gains inventés.
2. **FIN_INC :** protection du pouvoir d'achat démontrée par déciles et régions, y compris coûts transférés hors de l'impôt.
3. **FIN_MUNICIPAL :** collectivités, RTC, SOMHAC et autres organismes rapprochés sans double compte, y compris fonds affectés.
4. **SERVICES :** budgets des services et indicateurs de continuité avec protection des emplois et de l'accès.
5. **LEGAL :** compétences juridiques et constitutionnelles vérifiées; dans le Canada, un gouvernement provincial ne peut pas abolir seul des prélèvements fédéraux. Le scénario souverain est conditionnel et requiert une transition négociée et juridiquement validée.
6. **ELECTORAL :** réforme électorale simulée avec cartes régionales, cas extrêmes et contrôle indépendant.
7. **TRANSITION :** responsabilités et coût du transfert de fonctions, dette, actifs, contrats, systèmes et services.
8. **EXPERTS :** avis indépendants signés, réserves traitées et vérification contradictoire.
9. **CONSULTATIONS :** procédure accessible et transparente, sans biais ni exposition de données personnelles.
10. **ADOPTION :** décision formelle sur le texte maître, versions et statut réel du parti vérifié séparément.

Les portes ne sont pas « franchies » parce qu'un script a testé un scénario fictif. **Une seule porte critique encore ouverte empêche de qualifier le programme de prêt à être appliqué.**

## Douze actions concrètes, priorisées par l'effet sur la complétude

| Priorité | Livrable recherché | Critère minimal avant clôture |
|---|---|---|
| **N01** | Deux budgets complets sur 10 ans | Toutes les lignes sourcées et contraintes réconciliées; aucun zéro à la place d'un montant inconnu |
| **N02** | Étude détaillée des deux prélèvements | Compétences, recettes plausibles, exemples ménages/entreprises, effets distributifs et coûts non fiscaux |
| **N03** | Réconciliation municipale et organismes | Écritures, réserve SOMHAC, contribution RTC et fonds dédiés sans économie comptable fictive |
| **N04** | Passage Québec dans Canada → scénario souverain | Étapes, fonctions transférées, négociations, coûts, dette, droit et continuité |
| **N05** | Budgets sectoriels | Santé, éducation, logement, justice, sécurité, infrastructures : coûts, indicateurs et sauvegardes |
| **N06** | Examen de constitutionnalité et de concordance | Contradictions, compétences et recours soumis à avis juridique contradictoire |
| **N07** | Simulation de la réforme électorale | Distribution des sièges, régions et cas adversariaux validés |
| **N08** | Plan de déploiement cadencé | Dépendances, coûts de démarrage, plans de repli, emplois et services |
| **N09** | Avis d'experts indépendants | Mandats authentifiés, rapports et réserves, sans auto-certification |
| **N10** | Consultation citoyenne vérifiable | Accès, neutralité, traçabilité des propositions et gestion privée des réponses |
| **N11** | Statut légal du parti et adoption | Vérification officielle Élections Québec et décisions formelles, sans supposition d'autorisation |
| **N12** | Consolidation du programme maître | Décisions documentées sur chaque étude, statut des mesures et version publique cohérente |

**Ordre fonctionnel :** commencer par N01/N02/N03 et N04/N05; préparer parallèlement N06/N07/N08; aucun « GO » tant que N09/N10/N11 ne sont pas réellement documentés; terminer par N12 seulement après arbitrages et autorisations. Cela évite d'annoncer des taux ou de modifier le site public sur la base d'études non adoptées.

## Sources institutionnelles externes à revoir lors des décisions

- [Québec, Budget 2026–2027, plan budgétaire](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf) — cadre financier public de référence, **pas** un budget futur du Projet Nova.
- [Élections Québec — autorisation d'un parti politique provincial](https://www.electionsquebec.qc.ca/comprendre/comprendre-le-financement-politique/obtenir-le-droit-de-collecter-des-contributions-ou-de-faire-des-depenses/) — l'autorisation politique a ses propres exigences et **ne certifie pas** le programme.
- [Loi fédérale sur la clarté, art. 2 et 3](https://laws-lois.justice.gc.ca/fra/lois/C-31.8/section-2.html) — dispositions relatives à la majorité claire, aux négociations et aux modifications constitutionnelles. Le texte candidat Nova doit rester compatible avec les exigences juridiques applicables jusqu'à la survenance d'un changement de droit.

## Règle de mise à jour du score

**P55N est une photographie, pas un compteur automatique.** Ajouter un document, une répétition de tests, une simulation à entrées inconnues ou une nouvelle colonne de chiffres ne modifie pas le pointage. Une hausse ultérieure exige :
- une source vérifiable et la date de sa revue;
- un **critère précis** devenu satisfait, avec preuve d'acceptation;
- une réévaluation humaine des points avec motifs;
- la revue contradictoire des effets sur la protection de l'emploi, des services et du pouvoir d'achat.

En cas de contradiction de source, la mise à jour doit être refusée et documentée; la version précédente demeure conservée. La révision du score, si autorisée plus tard, doit passer par une **nouvelle version datée et de nouveaux tests**, plutôt que par une modification silencieuse de cette photographie P55N.

Le programme demeure **candidat**, non adopté et non exécutable; les deux scénarios de fiscalité ne sont pas fusionnés. Aucun taux n'est adopté, aucune économie certifiée, aucun mandat externe signé. **SINJIRA inchangé, aucun contact, aucune dépense, aucune fusion vers `main`.**

**Décision : `NO_GO_AUTOMATIQUE`.**
