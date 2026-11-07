# Projet Nova — P52W : préqualification d'une expertise indépendante F09

**20 octobre 2026 · Proposition non adoptée · Aucune invitation, candidature, consultation, dépense ou nomination engagée.**

## Objet précis

P52V a préparé 39 positions documentaires F09, 12 contrôles contradictoires et huit livrables. P52W définit désormais des conditions d'admissibilité et un protocole de réception confidentielle. Le contrôle est prêt à recevoir ultérieurement une décision humaine, mais **aucun expert réel n'a été mandaté**.

## Qualification légale du mandant

Avant de fixer un budget, contacter un prestataire ou imposer un mécanisme public de soumissions, un juriste ou une personne habilitée doit qualifier le mandant. La Loi sur les contrats des organismes publics (C-65.1) s'applique selon les organismes et contrats visés, non automatiquement à un projet politique. Aucun seuil réglementaire ni appel d'offres obligatoire n'est présumé.

Texte officiel : https://www.legisquebec.gouv.qc.ca/fr/document/lc/c-65.1

## Vérifications sans prospection automatisée

Un professionnel pourrait démontrer sa compétence sur les finances publiques québécoises, la distinction entre prévisions et réalisations, la vérification des comptes, les transferts fédéraux, les limites institutionnelles et les droits d'accès. Le tableau public de l'Ordre des CPA aide à vérifier le statut et les limitations d'une personne déjà identifiée; il ne constitue ni une preuve de compétence financière F09 ni une source de listes de prospection.

Tableau CPA : https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/intro/

## 12 conditions G01–G12 et cinq axes S01–S05

Les douze conditions d'admissibilité couvrent l'autorité et les fonds, la portée, le droit d'exercice, l'expérience, les conflits, l'interdiction de s'auto-évaluer, la confidentialité, les coûts, l'avis défavorable et la séparation des décideurs. Un **conflit bloquant ne se compense pas par une note élevée**.

Les poids **uniquement proposés** sont 30/100 (expérience), 25 (méthode), 20 (contradiction), 15 (livrables) et 10 (coût et échéance). Aucun seuil, nombre légal minimal d'offres, budget ou système de notation n'a été adopté. Tout comparatif éventuel doit être traité comme une aide à une décision réellement humaine, non une attribution automatique.

## Réception des offres et protection de la vie privée

Le registre de réception P52W est **strictement vide**; noms, courriels, CV, devis, déclarations détaillées et documents personnels ne doivent jamais être déposés dans les fichiers ou les artefacts CI. Avant une sollicitation, déterminer la base légale, la finalité, l'accès, la conservation, le retrait et la sécurité de la réception. Le droit québécois du secteur privé et les règles applicables aux partis peuvent différer selon l'organisme.

Sources : https://www.legisquebec.gouv.qc.ca/fr/document/lc/p-39.1 et https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25

## Conséquences et commandes

Le validateur P52W contrôle la correspondance exacte avec P52A, P52N, P52Q, P52U et P52V; ses simulations ne portent que sur des candidats fictifs. Un CSV exporté reste un gabarit vide. Il refuse toute approbation inventée.

    python scripts/preparer_selection_expert_nova_p52w.py --rapport /tmp/p52w_bilan.json
    python scripts/preparer_selection_expert_nova_p52w.py --export-csv /tmp/p52w_grille_vierge.csv
    python scripts/preparer_selection_expert_nova_p52w.py --exiger-mandat

Code 0 = dossier cohérent et NO_GO; code 2 = anomalie documentaire; code 3 = mandat humain manquant. La publication, les dépenses et la fusion ne sont jamais autorisées. Les étapes d'expertise restent externes : identité juridique, budget, candidature, vérification indépendante, contrat, relecture, avis signé et réserves.

**Situation : 20 preuves F01–F20 non validées, 1 320 montants Nova inconnus, PR #673 en brouillon, main sans protection obligatoire (#135), revues humaines non engagées (#662).**
