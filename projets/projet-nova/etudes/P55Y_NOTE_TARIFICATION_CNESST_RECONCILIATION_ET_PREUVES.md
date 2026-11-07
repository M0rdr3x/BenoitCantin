# P55Y — CNESST 2026 : taux particuliers, salaires assurables et contrôle des preuves

**7 novembre 2026 · Étude candidate non adoptée.** Ce jalon prolonge P55W et P55X et cherche à établir une méthode de rapprochement des primes CNESST dans les coûts employeurs, sans inventer de prime d'entreprise, de réduction de dépense publique ou de rendement du système fiscal Nova.

## Références institutionnelles

- [CNESST — classification de l'employeur](https://www.cnesst.gouv.qc.ca/fr/demarches-formulaires/employeurs/assurance-sante-securite-travail/obligations-annuelles-prime-assurance/classification-employeur) : une ou plusieurs unités de classification par entreprise, avec taux propres et décision de classification.
- [CNESST — taux de prime](https://www.cnesst.gouv.qc.ca/fr/demarches-formulaires/employeurs/assurance-sante-securite-travail/tarification/taux-prime) : le taux dépend notamment de l'unité et du mode de tarification. Le taux moyen provincial n'est pas un taux universel applicable aux employeurs.
- [CNESST — taux moyen 2026](https://www.cnesst.gouv.qc.ca/fr/salle-presse/communiques/taux-moyen-cotisation-2026) : 1,54 $ par 100 $ de masse salariale, annoncé en mai 2025, **uniquement un taux moyen provincial**.
- [CNESST — maximum annuel assurable](https://www.cnesst.gouv.qc.ca/fr/demarches-formulaires/employeurs/assurance-sante-securite-travail/tarification/annexes-tableaux/salaire-maximum-annuel-assurable) : maximum de **103 000 $ pour 2026**, ou maximum hebdomadaire de **1 975,45 $**, sous réserve des règles applicables.
- [CNESST — taux de versement périodique](https://www.cnesst.gouv.qc.ca/fr/demarches-formulaires/employeurs/assurance-sante-securite-travail/obligations-annuelles-prime-assurance/versements-periodiques/taux-versement) : un employeur à plusieurs unités peut recevoir un taux de versement pondéré qui ne constitue pas nécessairement sa prime annuelle finale.
- [Revenu Québec — FSS 2026](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/employeur-principaux-changements-2026/) : le Fonds des services de santé est une contribution différente, avec son propre taux et son assiette.

Les décisions et informations d'employeurs potentiellement confidentielles restent hors du dépôt public; aucun numéro d'employeur ni dossier individuel n'est demandé ou conservé dans l'exemple.

## Calcul et avertissement

Le script P55Y se limite à une **opération arithmétique** : pour chaque unité, salaires assurables déclarés multipliés par le taux déclaré par 100 $ puis divisés par 100. Chaque résultat est arrondi au cent. Cela ne constitue pas une facture CNESST et ne reproduit pas la tarification personnalisée, rétrospective, les ajustements, le plafond hebdomadaire propre aux dossiers ni tous les mécanismes de versements.

| Unité fictive | Taux fictif par 100 $ | Salaires fictifs assurables | Résultat fictif |
|---|---:|---:|---:|
| UNIT-A | 1,50 $ | 300 000 $ | 4 500 $ |
| UNIT-B | 3,00 $ | 200 000 $ | 6 000 $ |
| Total illustratif | — | 500 000 $ | **10 500 $** |

Les taux de 1,50 $ et 3,00 $ sont **inventés uniquement pour tester le code**. Ils ne correspondent à aucune tarification attestée d'une PME et ne démontrent aucune économie. Ce total ne s'additionne pas automatiquement au P55X, lequel utilise lui aussi des hypothèses fictives différentes.

Une donnée absente demeure nulle et entraîne un total inconnu, jamais zéro. Le mode de saisie DECLARATION_NON_AUTHENTIFIEE ne prouve pas qu'une décision CNESST a été obtenue, signée ou auditée. Le mode FICTIF est obligatoire pour l'exemple inclus.

## Validation reproductible

Fichiers ajoutés :
- projets/projet-nova/etudes/P55Y_EXEMPLE_FICTIF_TARIFICATION_CNESST_2026.json
- scripts/rapprocher_tarification_cnesst_nova_p55y.py
- scripts/tests/test_rapprocher_tarification_cnesst_nova_p55y.py
- .github/workflows/validate-nova-p55y.yml
- cette note de méthode

Exemple d'exécution : python scripts/rapprocher_tarification_cnesst_nova_p55y.py --entree projets/projet-nova/etudes/P55Y_EXEMPLE_FICTIF_TARIFICATION_CNESST_2026.json

Le programme interdit l'écrasement des bilans existants et rejette toute requête --exiger-faisabilite avec le code 3. Les **27 tests synthétiques** vérifient le calcul, la distinction entre zéro et inconnu, la provenance déclarée, la non-transposition au Québec souverain et le refus de certification.

## Pièces non obtenues et conditions d'acceptation

| Identifiant | Preuve à obtenir | Condition de clôture |
|---|---|---|
| Y01 | Décision de classification 2026 | Version vérifiée, correspondance avec l'année et les unités |
| Y02 | Taux applicable par unité | Mode de tarification et décision authentifiés |
| Y03 | Salaires assurables anonymisés par unité | Bases, plafonds et ventilations contrôlés |
| Y04 | Ajustements, versements et associations | Réconciliation avec la prime réelle, sans double compte |
| Y05 | FSS et normes P55X | Assiettes, secteurs, exceptions et millésimes alignés |
| Y06 | Coût patronal complet de PME | Prestations, autres contributions et effets sur l'emploi inclus |
| Y07 | Financement des droits sociaux | Continuité indemnisations, prévention, rente et assurances étudiée |
| Y08 | Avis indépendants | Rapports professionnels réels, signés, contradictoires |

Une fois les pièces Y01–Y08 acquises légalement et examinées, un nouveau jalon pourra construire une comparaison avant/après réellement instruite. Même avec des chiffres complets, les effets prix, salaires, emplois, prestations et pouvoirs juridiques doivent être étudiés pour les deux statuts constitutionnels, **sans les fusionner**.

**P55N : 53 % estimatifs** (fourchette 45–60 %), sans revalorisation par l'ajout de fichiers. Les **600 entrées P52B** et les **720 incidences P52D** restent inconnues. Aucun taux Nova ni économie certifiée, aucun mandat signé, aucun contact ou dépense, aucune modification du programme public, de SINJIRA ni de main.

**Décision : NO_GO_AUTOMATIQUE.**
