# Projet Nova — P53L : évaluation prudente des économies administratives

**22 octobre 2026 — étude candidate, sans économies démontrées ni décision d'application.**

## 1. Objet

Établir une chaîne de comparaison financière **distincte des opérations comptables interorganismes** de P53I–P53K, sans additionner les revenus et dépenses municipaux de 2024 au budget québécois 2026–2027. L'exercice 2027 est une **année hypothétique de projection**, et les montants 2024 ne fournissent pas automatiquement un coût de base pertinent pour une politique gouvernementale. Les hypothèses en dollars constants 2024 exigeraient une méthode explicite de conversion des prix avant utilisation réelle.

Un **gain comptable de consolidation** ne libère pas nécessairement de trésorerie. Une **économie de fonctionnement** ne devient crédible qu'avec une dépense effectivement évitée et durable, une base comparative propre, des coûts de mise en œuvre, des effets secondaires et les garanties de service.

## 2. Six pistes non chiffrées à instruire

- Achats groupés avec préservation de la qualité, de l'accès et de la concurrence.
- Simplification des formalités sans suppression d'assistance humaine.
- Efficacité énergétique et bâtiments sans report d'entretien.
- Entretien préventif et réduction des défaillances démontrée.
- Rationalisation de licences logicielles en préservant sécurité et accessibilité.
- Renouvellement transparent de contrats sans appauvrir les travailleurs et fournisseurs.

Ces pistes ne sont **ni des accusations de gaspillage**, ni des économies déjà constatées. Le programme crée un catalogue sans estimations financières fictives.

## 3. Formule et limites

Pour une mesure hypothétique dont la période, le périmètre, la monnaie et l'année de prix sont comparables :

- Écart brut annuel = coût annuel de référence − coût annuel projeté.
- Solde récurrent indicatif = écart brut − nouveaux coûts annuels − coûts déplacés vers citoyens, entreprises ou autres organismes.
- Solde indicatif du premier exercice = solde récurrent − dépenses initiales de transition.

Ces soldes **ne sont jamais certifiés par le logiciel** et ne sont pas publiés dans les bilans CI. Les coûts d'investissement initiaux sont imputés en entier au premier exercice dans le test conservateur ; toute analyse pluriannuelle ultérieure exigerait hypothèses de durée, actualisation, besoins de remplacement, risques, coûts administratifs et vérification des cash-flows. Une projection arithmétiquement positive ne justifie pas une baisse d'impôt, un budget adopté ou une décision de service.

## 4. Barrières contre les fausses économies

Refus de présenter un gain si la mesure provoque ou n'écarte pas : réduction de personnel ou d'heures contractuelles, détérioration salariale, baisse de qualité, délai accru, exclusion des personnes sans accès numérique, rupture de services essentiels, restriction de droits ou transfert de coûts. Une protection inconnue est explicitement insuffisante. Les indicateurs de satisfaction et de disponibilité, les références de contrats, les bases de dépenses et les données d'utilisation doivent être mesurés **avant** toute approbation.

Aucune addition de mesures touchant le même poste budgétaire et périmètre n'est permise automatiquement, afin d'éviter d'additionner deux fois le même gain projeté. Aucune élimination d'écriture interorganisme, réduction de transfert ou variation statistique ne compte pour une économie opérationnelle démontrée.

## 5. Méthode d'obtention de preuves

Pour chaque piste, obtenir les factures et contrats, les réalisations et crédits budgétaires, le coût complet du personnel sans suppression des effectifs, les dépenses de maintien et de transition, des indicateurs de service (attente, erreurs, accès humain), les coûts déplacés vers les autres administrations et usagers, ainsi que l'avis d'un auditeur indépendant. Dans un second temps, comparer **avant et après** la mesure sur des périmètres stables, avec méthode d'attribution des variations et examen des changements externes. Prévoir une consultation des salariés et usagers.

Références méthodologiques publiques :
- Secrétariat du Conseil du trésor : https://www.tresor.gouv.qc.ca/performance-de-letat/cadre-de-gestion-de-ladministration-gouvernementale/evaluation-de-programme
- Secrétariat du Conseil du trésor : https://www.tresor.gouv.qc.ca/performance-de-letat
- Commission municipale du Québec : https://www.cmq.gouv.qc.ca/fr/verification-municipale/questions-frequentes

## 6. Vérification technique

    python scripts/evaluer_hypotheses_economies_nova_p53l.py --rapport p53l_bilan.json --catalogue p53l_pistes.json
    python scripts/evaluer_hypotheses_economies_nova_p53l.py --exiger-economies-certifiees

Le mode normal retourne **0** pour un contrôle structurel réussi, **2** pour une entrée incompatible, **3** lorsque l'on exige une économie certifiée sans preuves. Les fiches de travail JSON fournies avec --mesure sont **seulement des hypothèses ou déclarations non authentifiées** ; aucun fichier de pièces ni montant par mesure n'est transmis dans les artéfacts CI. Les sorties existantes ne sont pas écrasées.

## 7. Conclusion

**NO_GO_AUTOMATIQUE**. Six pistes ouvertes, zéro pièce certifiée, zéro économie opérationnelle démontrée, aucune révision indépendante, F01–F20 toujours non validées, 1 320 montants Nova inconnus et aucun taux fiscal adopté. Aucun changement à l'emploi, aux services, à la fiscalité officielle, au site public, à main ou à SINJIRA. La PR #673 reste une étude en brouillon.
